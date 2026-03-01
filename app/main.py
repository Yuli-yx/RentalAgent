"""FastAPI 应用入口"""
import time
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat
from app.config import settings
from app.utils.logger import setup_logging, get_logger

# 创建日志目录
import os
os.makedirs(settings.LOG_DIR, exist_ok=True)

# 初始化日志
log_file = settings.get_log_file()
logger = setup_logging(
    log_level=settings.LOG_LEVEL,
    log_file=log_file,
    log_dir=settings.LOG_DIR
)

# 创建 FastAPI 应用
app = FastAPI(
    title="租房 AI Agent",
    description="智能租房助手 API，支持房源查询、筛选、推荐等功能",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "debug_mode": settings.DEBUG_MODE,
        "timestamp": datetime.now().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("=" * 60)
    logger.info("租房 AI Agent 服务启动")
    logger.info(f"调试模式: {settings.DEBUG_MODE}")
    logger.info(f"服务地址: http://{settings.AGENT_HOST}:{settings.AGENT_PORT}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    logger.info(f"日志目录: {settings.LOG_DIR}")
    logger.info(f"房源API: {settings.RENTAL_API_BASE}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("租房 AI Agent 服务关闭")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()

    # 记录请求
    logger.info(f"请求开始: {request.method} {request.url.path}")

    # 处理请求
    response: Response = await call_next(request)

    # 计算耗时
    duration = time.time() - start_time
    duration_ms = int(duration * 1000)

    # 记录响应
    logger.info(
        f"请求完成: {request.method} {request.url.path} | "
        f"状态码: {response.status_code} | 耗时: {duration_ms}ms"
    )

    return response