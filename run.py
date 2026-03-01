"""租房 AI Agent 启动脚本"""
import argparse
import uvicorn
from datetime import datetime
from app.config import settings
from app.utils.logger import setup_logging
import os


def main():
    parser = argparse.ArgumentParser(description="租房 AI Agent 服务")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启动调试模式（使用V2接口，无需Session-ID）"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="服务绑定地址（默认：0.0.0.0）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="服务端口（默认：8191）"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="日志级别（默认：INFO，调试模式下为DEBUG）"
    )

    args = parser.parse_args()

    # 更新调试模式
    if args.debug:
        settings.update_debug_mode(True)

    # 更新日志级别
    if args.log_level:
        settings.LOG_LEVEL = args.log_level

    # 创建日志目录
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    # 初始化日志
    log_file = settings.get_log_file()
    logger = setup_logging(
        log_level=settings.LOG_LEVEL,
        log_file=log_file,
        log_dir=settings.LOG_DIR
    )

    # 打印启动信息
    logger.info("=" * 60)
    logger.info("租房 AI Agent 服务启动中...")
    logger.info("=" * 60)

    if args.debug:
        logger.info("调试模式已启用")
        logger.info("- 使用 V2 接口（无需 Session-ID）")
        logger.info(f"- 默认模型 IP: {settings.DEBUG_MODEL_IP}:{settings.MODEL_PORT}")

    # 确定服务配置
    host = args.host or settings.AGENT_HOST
    port = args.port or settings.AGENT_PORT

    logger.info(f"服务地址: http://{host}:{port}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    logger.info(f"日志文件: {settings.LOG_DIR}/{log_file}")
    logger.info(f"房源API: {settings.RENTAL_API_BASE}")
    logger.info("=" * 60)

    # 启动服务
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()