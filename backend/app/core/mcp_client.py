"""
MCP (Model Context Protocol) Client for connecting to external MCP servers.
This client connects to MCP servers over HTTP/SSE and provides tools for agents.

Supports:
1. Connecting to remote MCP servers (like AMAP MCP server)
2. Automatic tool discovery and registration
3. Tool abstraction with extensible Tool classes
4. Multiple server registration and management
"""
import json
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from pydantic import BaseModel, Field
import httpx

class MCPMessageType(Enum):
    """MCP message types"""
    INITIALIZE = "initialize"
    INITIALIZE_RESULT = "initialize_result"
    TOOLS_LIST = "tools/list"
    TOOLS_LIST_RESULT = "tools/list_result"
    TOOLS_CALL = "tools/call"
    TOOLS_CALL_RESULT = "tools/call_result"
    ERROR = "error"

class MCPMessage(BaseModel):
    """Base MCP message model"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class ToolParameter(BaseModel):
    """Tool parameter schema"""
    type: str
    description: Optional[str] = None
    required: bool = True

class ToolSchema(BaseModel):
    """Tool schema from MCP server"""
    name: str
    description: Optional[str] = None
    inputSchema: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, ToolParameter]] = None


class Tool(ABC):
    """Abstract base class for all tools"""
    
    def __init__(self, name: str, description: str = "", metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.metadata = metadata or {}
    
    @abstractmethod
    def call(self, **kwargs) -> Any:
        """Call the tool with given arguments"""
        pass
    
    def __call__(self, **kwargs) -> Any:
        """Make the tool callable like a function"""
        return self.call(**kwargs)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get tool metadata"""
        return {
            "name": self.name,
            "description": self.description,
            **self.metadata
        }


class MCPTool(Tool):
    """Tool implementation for MCP server tools"""
    
    def __init__(self, name: str, description: str, mcp_client: 'MCPClient', 
                 schema: Optional[ToolSchema] = None):
        super().__init__(name, description, metadata={"type": "mcp", "schema": schema})
        self.mcp_client = mcp_client
        self.schema = schema
        # 完整名称（包含服务器前缀），用于在 Registry 中唯一标识
        # 会在 MCPClientRegistry._update_tools_cache() 中被设置
        self._full_name: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """
        获取完整的工具名称（包含服务器前缀）
        如果没有设置前缀，则返回原始名称
        """
        return self._full_name if self._full_name else self.name
    
    @full_name.setter
    def full_name(self, value: str) -> None:
        """设置完整的工具名称"""
        self._full_name = value
    
    def call(self, **kwargs) -> Any:
        """Call the tool on the MCP server"""
        return self.mcp_client.call_tool(self.name, **kwargs)
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters from schema"""
        if self.schema and self.schema.parameters:
            return {name: param.dict() for name, param in self.schema.parameters.items()}
        return {}
    
    def to_openai_function_schema(self) -> Dict[str, Any]:
        """
        将工具转换为 OpenAI Function Calling 格式
        
        注意：这里使用 full_name（带服务器前缀）作为工具名称，
        确保模型返回的工具名称与 tools 字典中的 key 一致。
        
        返回格式示例:
        {
            "type": "function",
            "function": {
                "name": "amap.maps_weather",  # 带前缀的完整名称
                "description": "查询天气信息",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        }
        """
        # 从 inputSchema 获取参数定义
        parameters = {"type": "object", "properties": {}, "required": []}
        
        if self.schema and self.schema.inputSchema:
            input_schema = self.schema.inputSchema
            # inputSchema 通常已经是标准的 JSON Schema 格式
            parameters = {
                "type": input_schema.get("type", "object"),
                "properties": input_schema.get("properties", {}),
                "required": input_schema.get("required", [])
            }
            # 保留其他 JSON Schema 字段（如 additionalProperties）
            if "additionalProperties" in input_schema:
                parameters["additionalProperties"] = input_schema["additionalProperties"]
        
        # 使用 full_name 确保与 tools 字典的 key 一致
        return {
            "type": "function",
            "function": {
                "name": self.full_name,
                "description": self.description or "",
                "parameters": parameters
            }
        }
    
    def to_prompt_string(self) -> str:
        """
        将工具转换为适合放入提示词的字符串格式
        
        返回人类可读的工具描述，便于在 prompt 中使用
        """
        schema = self.to_openai_function_schema()
        func = schema["function"]
        
        lines = [
            f"工具名称: {func['name']}",
            f"功能描述: {func['description']}",
            "参数:"
        ]
        
        properties = func["parameters"].get("properties", {})
        required = func["parameters"].get("required", [])
        
        if properties:
            for param_name, param_info in properties.items():
                is_required = "必填" if param_name in required else "可选"
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "无描述")
                lines.append(f"  - {param_name} ({param_type}, {is_required}): {param_desc}")
                
                # 如果有枚举值，显示出来
                if "enum" in param_info:
                    lines.append(f"    可选值: {param_info['enum']}")
        else:
            lines.append("  无参数")
        
        return "\n".join(lines)


class MCPClient:
    """
    MCP Client for connecting to external MCP servers.
    
    This client connects to MCP servers (like AMAP MCP server) and provides
    a unified interface for agents to call remote tools.
    """
    
    def __init__(self, server_url: str, api_key: Optional[str] = None, 
                 timeout: int = 30, transport_type: str = "http"):
        """
        Initialize MCP client and connect to server.
        
        Args:
            server_url: URL of the MCP server (e.g., "https://mcp.amap.com/mcp")
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            transport_type: Transport type - "http" or "sse"
        """
        self.server_url = server_url
        self.api_key = api_key
        self.timeout = timeout
        self.transport_type = transport_type
        self._tools: Dict[str, ToolSchema] = {}
        self._initialized = False
        
        # HTTP client for making requests
        self._client = httpx.Client(timeout=timeout)
        
        # Initialize connection
        self.initialize()
    
    def initialize(self) -> None:
        """
        Initialize connection to MCP server and fetch available tools.
        """
        if self._initialized:
            return
        
        try:
            # Send initialize request
            init_msg = MCPMessage(
                id=str(uuid.uuid4()),
                method=MCPMessageType.INITIALIZE.value,
                params={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "travel-assistant-agent",
                        "version": "1.0.0"
                    }
                }
            )
            
            response = self._send_message(init_msg)
            
            if response.error:
                raise Exception(f"MCP initialization error: {response.error}")
            
            # After initialization, fetch tools list
            self._fetch_tools()
            self._initialized = True
            
            # print(f"✅ MCP client connected to {self.server_url}")
            # print(f"✅ Discovered {len(self._tools)} tools")
            
        except Exception as e:
            print(f"❌ Failed to initialize MCP client: {e}")
            raise
    
    def _send_message(self, message: MCPMessage) -> MCPMessage:
        """
        Send MCP message to server and get response.
        
        Args:
            message: MCP message to send
            
        Returns:
            Response message from server
        """
        # MCP Streamable HTTP requires specific Accept header
        # See: https://modelcontextprotocol.io/specification/2024-11-05/basic/transports
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Add API key to URL if it's in query params (like AMAP)
        url = self.server_url
        
        try:
            response = self._client.post(
                url,
                headers=headers,
                content=message.model_dump_json(exclude_none=True)
            )
            response.raise_for_status()
            
            # Handle both JSON and SSE responses
            content_type = response.headers.get("content-type", "")
            
            if "text/event-stream" in content_type:
                # Parse SSE response - extract JSON from event stream
                return self._parse_sse_response(response.text)
            else:
                # Standard JSON response
                response_data = response.json()
                return MCPMessage(**response_data)
            
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error communicating with MCP server: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from MCP server: {e}")
    
    def _parse_sse_response(self, sse_text: str) -> MCPMessage:
        """
        Parse Server-Sent Events (SSE) response and extract JSON-RPC message.
        
        Args:
            sse_text: Raw SSE response text
            
        Returns:
            Parsed MCPMessage
        """
        # SSE format: 
        # event: message
        # data: {"jsonrpc": "2.0", ...}
        
        lines = sse_text.strip().split('\n')
        json_data = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('data:'):
                # Extract JSON after "data:" prefix
                data_content = line[5:].strip()
                if data_content:
                    try:
                        json_data = json.loads(data_content)
                        # Return the last valid JSON message (result)
                    except json.JSONDecodeError:
                        continue
        
        if json_data:
            return MCPMessage(**json_data)
        
        raise Exception("No valid JSON data found in SSE response")
    
    def _fetch_tools(self) -> None:
        """
        Fetch list of available tools from MCP server.
        """
        try:
            tools_msg = MCPMessage(
                id=str(uuid.uuid4()),
                method=MCPMessageType.TOOLS_LIST.value,
                params={}
            )
            
            response = self._send_message(tools_msg)
            
            if response.error:
                raise Exception(f"Failed to fetch tools: {response.error}")
            
            # Parse tools from response
            tools_data = response.result.get("tools", []) if response.result else []
            
            for tool_data in tools_data:
                try:
                    tool = ToolSchema(**tool_data)
                    self._tools[tool.name] = tool
                except Exception as e:
                    print(f"Warning: Failed to parse tool {tool_data.get('name')}: {e}")
            
        except Exception as e:
            print(f"Warning: Failed to fetch tools from MCP server: {e}")
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result from the tool execution
            
        Raises:
            KeyError: If tool not found
            Exception: If tool call fails
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not found. Available tools: {list(self._tools.keys())}")
        
        try:
            call_msg = MCPMessage(
                id=str(uuid.uuid4()),
                method=MCPMessageType.TOOLS_CALL.value,
                params={
                    "name": tool_name,
                    "arguments": kwargs
                }
            )
            
            response = self._send_message(call_msg)
            
            if response.error:
                error_msg = response.error.get("message", "Unknown error")
                raise Exception(f"Tool call failed: {error_msg}")
            
            return response.result
            
        except Exception as e:
            raise Exception(f"Failed to call tool '{tool_name}': {e}")
    
    def get_tools(self) -> Dict[str, MCPTool]:
        """
        Get all discovered tools as MCPTool instances.
        
        Returns:
            Dictionary mapping tool names to MCPTool instances
        """
        tools_dict = {}
        
        for tool_name, tool_schema in self._tools.items():
            tool = MCPTool(
                name=tool_name,
                description=tool_schema.description or "",
                mcp_client=self,
                schema=tool_schema
            )
            tools_dict[tool_name] = tool
        
        return tools_dict
    
    def get_tool_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata for all discovered tools.
        
        Returns:
            Dictionary mapping tool names to tool metadata
        """
        metadata = {}
        
        for tool_name, tool_schema in self._tools.items():
            metadata[tool_name] = {
                "name": tool_schema.name,
                "description": tool_schema.description,
                "parameters": tool_schema.parameters,
                "inputSchema": tool_schema.inputSchema,
            }
        
        return metadata
    
    def list_tools(self) -> List[str]:
        """
        List names of all available tools.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())
    
    def close(self):
        """Close the HTTP client connection."""
        self._client.close()


# Factory function for creating MCP clients
def create_mcp_client(server_name: str = "amap", api_key: Optional[str] = None) -> MCPClient:
    """
    Create an MCP client for a specific server.
    
    Args:
        server_name: Name of the server ("amap" or custom URL)
        api_key: Optional API key
        
    Returns:
        MCPClient instance
    """
    # Map server names to URLs
    server_urls = {
        "amap": "https://mcp.amap.com/mcp",
        "utest": "http://utest.mcpserver.woa.com/mcp",
    }
    
    if server_name in server_urls:
        url = server_urls[server_name]
    else:
        # Assume it's a custom URL
        url = server_name
    
    # Add API key to URL if provided (for AMAP style)
    if api_key and "amap" in url:
        url = f"{url}?key={api_key}"
    
    return MCPClient(server_url=url, api_key=api_key)


# Global MCP client instances
_mcp_clients: Dict[str, MCPClient] = {}


def get_mcp_client(server_name: str = "amap", api_key: Optional[str] = None) -> MCPClient:
    """
    Get or create a singleton MCP client for a specific server.
    
    Args:
        server_name: Name of the server ("amap" or custom URL)
        api_key: Optional API key
        
    Returns:
        MCPClient instance
    """
    global _mcp_clients
    
    cache_key = f"{server_name}:{api_key or 'no-key'}"
    
    if cache_key not in _mcp_clients:
        _mcp_clients[cache_key] = create_mcp_client(server_name, api_key)
    
    return _mcp_clients[cache_key]


class MCPClientRegistry:
    """
    Registry for managing multiple MCP servers and their tools.
    
    This class provides a centralized way to register, discover, and use
    tools from multiple MCP servers.
    """
    
    def __init__(self):
        self._servers: Dict[str, MCPClient] = {}
        self._tools: Dict[str, MCPTool] = {}
    
    def register_server(self, name: str, server_url: str, api_key: Optional[str] = None) -> MCPClient:
        """
        Register an MCP server with the registry.
        
        Args:
            name: Unique name for the server (e.g., "amap")
            server_url: URL of the MCP server
            api_key: Optional API key for authentication
            
        Returns:
            MCPClient instance for the registered server
        """
        if name in self._servers:
            print(f"Warning: Server '{name}' already registered, replacing")
        
        client = MCPClient(server_url=server_url, api_key=api_key)
        self._servers[name] = client
        
        # Update tools cache
        self._update_tools_cache()
        
        return client
    
    def register_predefined_server(self, name: str, api_key: Optional[str] = None) -> MCPClient:
        """
        Register a predefined MCP server.
        
        Args:
            name: Server name ("amap", "utest", etc.)
            api_key: Optional API key
            
        Returns:
            MCPClient instance
        """
        server_urls = {
            "amap": "https://mcp.amap.com/mcp",
            "utest": "http://utest.mcpserver.woa.com/mcp",
        }
        
        if name not in server_urls:
            raise ValueError(f"Unknown server name: {name}. Available: {list(server_urls.keys())}")
        
        url = server_urls[name]
        if api_key and "amap" in url:
            url = f"{url}?key={api_key}"
        
        return self.register_server(name, url, api_key)
    
    def get_server(self, name: str) -> Optional[MCPClient]:
        """Get a registered server by name."""
        return self._servers.get(name)
    
    def get_all_servers(self) -> Dict[str, MCPClient]:
        """Get all registered servers."""
        return self._servers.copy()
    
    def get_tools(self) -> Dict[str, MCPTool]:
        """Get all tools from all registered servers."""
        return self._tools.copy()
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Get a specific tool by name."""
        return self._tools.get(tool_name)
    
    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool by name.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result from tool execution
            
        Raises:
            KeyError: If tool not found
        """
        tool = self.get_tool(tool_name)
        if not tool:
            available = list(self._tools.keys())
            raise KeyError(f"Tool '{tool_name}' not found. Available tools: {available}")
        
        return tool.call(**kwargs)
    
    def list_tools(self) -> List[str]:
        """List names of all available tools."""
        return list(self._tools.keys())
    
    def _update_tools_cache(self):
        """Update the tools cache from all registered servers."""
        self._tools.clear()
        
        for server_name, client in self._servers.items():
            try:
                server_tools = client.get_tools()
                for tool_name, tool in server_tools.items():
                    # Add server name prefix to avoid name conflicts
                    full_name = f"{server_name}.{tool_name}"
                    tool.metadata["server"] = server_name
                    tool.metadata["original_name"] = tool_name
                    # 设置完整名称，确保 to_openai_function_schema() 返回带前缀的名称
                    tool.full_name = full_name
                    self._tools[full_name] = tool
            except Exception as e:
                print(f"Warning: Failed to get tools from server '{server_name}': {e}")
    
    def close_all(self):
        """Close all server connections."""
        for client in self._servers.values():
            try:
                client.close()
            except Exception as e:
                print(f"Warning: Failed to close client: {e}")
        
        self._servers.clear()
        self._tools.clear()


# Global registry instance
_mcp_registry: Optional[MCPClientRegistry] = None


def get_mcp_registry() -> MCPClientRegistry:
    """Get or create the global MCP client registry."""
    global _mcp_registry
    if _mcp_registry is None:
        _mcp_registry = MCPClientRegistry()
    return _mcp_registry


# Backward compatibility decorator (for existing code)
def tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Decorator for local tools (for backward compatibility).
    
    Note: This is for local tools, not MCP server tools.
    Use this for tools that should be implemented locally.
    """
    import functools
    from typing import Callable
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        wrapper._tool_name = name or func.__name__
        wrapper._tool_description = description or func.__doc__ or ""
        return wrapper
    
    return decorator


