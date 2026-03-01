"""配置文件"""
from typing import Optional


# Agent服务配置
AGENT_HOST: str = "0.0.0.0"
AGENT_PORT: int = 8191

# 房源仿真服务
RENTAL_API_BASE: str = "http://7.225.29.223:8080"

# 模型服务
MODEL_PORT: int = 8888
DEBUG_MODEL_IP: str = "7.225.29.223"  # 调试模式默认使用仿真服务IP

# 默认用户工号（可在请求中覆盖）
DEFAULT_USER_ID: str = "z00931220"

# 会话配置
MAX_HISTORY_TURNS: int = 8

# 调试模式
DEBUG_MODE: bool = False  # 通过命令行 --debug 设置

# 日志配置
LOG_LEVEL: str = "INFO"
LOG_DIR: str = "logs"
LOG_FILE_PREFIX: str = "rental_agent"


class Settings:
    """配置类"""

    def __init__(self):
        self.AGENT_HOST = AGENT_HOST
        self.AGENT_PORT = AGENT_PORT
        self.RENTAL_API_BASE = RENTAL_API_BASE
        self.MODEL_PORT = MODEL_PORT
        self.DEBUG_MODEL_IP = DEBUG_MODEL_IP
        self.DEFAULT_USER_ID = DEFAULT_USER_ID
        self.MAX_HISTORY_TURNS = MAX_HISTORY_TURNS
        self.DEBUG_MODE = DEBUG_MODE
        self.LOG_LEVEL = LOG_LEVEL
        self.LOG_DIR = LOG_DIR
        self.LOG_FILE_PREFIX = LOG_FILE_PREFIX

    def update_debug_mode(self, debug: bool):
        """更新调试模式"""
        self.DEBUG_MODE = debug
        if debug:
            self.LOG_LEVEL = "DEBUG"

    def get_log_file(self) -> Optional[str]:
        """获取日志文件名"""
        if not self.LOG_FILE_PREFIX:
            return None
        from datetime import datetime
        return f"{self.LOG_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d')}.log"


settings = Settings()