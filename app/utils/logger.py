"""日志配置模块"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs"
) -> logging.Logger:
    """
    配置日志系统

    Args:
        log_level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_file: 日志文件名，None则只输出到控制台
        log_dir: 日志目录

    Returns:
        配置好的logger
    """
    # 创建logger
    logger = logging.getLogger("RentalAgent")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 清除已有的handlers
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件handler（如果指定了日志文件）
    if log_file:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        file_path = log_path / log_file
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 全局logger实例（延迟初始化）
_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """获取logger实例"""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def init_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """初始化日志系统"""
    global _logger
    _logger = setup_logging(log_level, log_file)