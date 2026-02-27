from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routes import trip
from ..config import get_settings,print_config,validate_config
from ..agents.react_agent import ReActAgent
from ..core import memory, llm_message

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
        agent = ReActAgent(name=settings.app_name, role=settings.app_name, memory=memory.Memory())
        message = llm_message.LlmMessage(role=llm_message.MessageRole.user,content="介绍你自己")
        messages = [message.to_dict()]
        agent.call_llm(messages=messages)
    except ValueError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        print("\n请检查.env文件并确保所有必要的配置项都已设置")
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