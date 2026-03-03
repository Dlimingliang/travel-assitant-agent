from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import trip
from ..config import get_settings,print_config,validate_config
from ..agents.react_agent import ReActAgent
from ..core import memory
from ..core.mcp_client import get_mcp_registry

# 获取配置
settings = get_settings()

# 注册启动和关闭监听
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    """应用启动事件"""
    print("\n" + "=" * 60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("=" * 60)
    # 打印配置信息
    print_config()
    # 验证配置
    try:
        validate_config()
        print("\n✅ 配置验证通过")
        
        # 1. 注册MCP服务器
        print("\n🔧 注册MCP服务器...")
        registry = get_mcp_registry()
        
        # 注册高德地图MCP服务器（使用配置中的API密钥）
        if settings.amap_api_key and settings.amap_api_key != "your_amap_api_key_here":
            try:
                client = registry.register_predefined_server("amap", settings.amap_api_key)
                print(f"✅ MCP服务器注册成功，发现 {len(client.list_tools())} 个工具")
            except Exception as e:
                print(f"⚠️  MCP服务器注册失败: {e}")
                print("   继续启动，但部分功能可能不可用")
        else:
            print("⚠️  未配置高德地图API密钥，跳过MCP服务器注册")
        
        # 2. 创建Agent并注入工具
        print("\n🤖 创建Agent...")
        agent = ReActAgent(
            name=settings.app_name, 
            role=settings.app_name, 
            memory=memory.Memory(),
            tools=registry.get_tools()  # 直接注入所有工具
        )
        print(f"✅ Agent创建完成，加载了 {len(agent.tools)} 个工具")
        
        # 3. 测试工具调用（可选，演示如何使用）
        # if agent.tools:
        #     print("\n🔍 可用工具列表:")
        #     for tool_name, tool in agent.tools.items():
        #         print(f"   - {tool_name}:{tool.schema} {tool.description[:50]}..." if tool.description else f"   - {tool_name}")
            
            #示例：调用一个工具（如果有地理编码工具）
            #注意：实际调用需要参数，这里仅演示调用方式
            # try:
            #     result = agent.tools["amap.maps_weather"].call(city="北京市")
            #     print(f"示例调用结果: {result}")
            # except Exception as e:
            #     print(f"示例调用失败: {e}")

        # 4. 测试agent感知（原有逻辑）
        # agent.perceiving("123123","帮我规划一个北京的旅游计划")
        # 4. 测试agent规划
        agent.planning("123123", "帮我查询北京天气")
        
    except ValueError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        print("\n请检查.env文件并确保所有必要的配置项都已设置")
        raise
    except Exception as e:
        print(f"\n❌ 启动过程中发生错误:\n{e}")
        raise
    
    print("\n" + "=" * 60)
    print("📚 API文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("=" * 60 + "\n")

    yield  # 应用运行期间

    # 关闭时执行
    print("👋 应用关闭")
    """应用关闭事件"""
    print("\n" + "=" * 60)
    print("👋 应用正在关闭...")
    print("=" * 60 + "\n")
    
    # 关闭MCP连接
    try:
        registry.close_all()
        print("✅ MCP连接已关闭")
    except Exception as e:
        print(f"⚠️  关闭MCP连接时出错: {e}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    description="智能履行规划助手APP",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trip.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "name":settings.app_name,
        "version":settings.app_version,
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }