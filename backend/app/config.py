import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 加载环境变量
load_dotenv()

class Settings(BaseSettings):
    # 应用基本配置
    app_name: str = "智能旅行助手"
    app_version: str = "1.0.0"

    host: str = ""
    port: int = 8000

    # CORS配置(从环境变量读取) - 使用字符串,在代码中分割
    cors_origins: str = ""

    # 高德地图API配置(从环境变量读取)
    amap_api_key: str = ""

    # Unsplash API配置(从环境变量读取)
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    # LLM配置 (从环境变量读取)
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = ""

    # 日志配置
    log_level: str = ""

    class ConfigDict:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # 忽略额外的环境变量

    def get_cors_origins_list(self) -> list[str]:
        """获取CORS origins列表"""
        return [origin.strip() for origin in self.cors_origins.split(',')]

# 创建全局配置实例
settings = Settings()

def get_settings() -> Settings:
    """获取配置实例"""
    return settings

# 打印配置信息(用于调试)
def print_config():
    """打印当前配置(隐藏敏感信息)"""
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")
    print(f"服务器: {settings.host}:{settings.port}")
    print(f"高德地图API Key: {'已配置' if settings.amap_api_key else '未配置'}")

    # 检查LLM配置
    llm_api_key = os.getenv("LLM_API_KEY") or settings.openai_api_key
    llm_base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
    llm_model = os.getenv("LLM_MODEL_ID") or settings.openai_model

    print(f"LLM API Key: {'已配置' if llm_api_key else '未配置'}")
    print(f"LLM Base URL: {llm_base_url}")
    print(f"LLM Model: {llm_model}")
    print(f"日志级别: {settings.log_level}")

if __name__ == '__main__':
    print_config()