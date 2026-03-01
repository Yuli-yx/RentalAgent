"""工具基类"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import httpx
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()


class BaseTool(ABC):
    """工具基类"""

    def __init__(self, user_id: Optional[str] = None):
        self.user_id = user_id or settings.DEFAULT_USER_ID
        self.base_url = settings.RENTAL_API_BASE

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """工具参数定义 (OpenAI Function Calling 格式)"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""
        pass

    def get_openai_tool_definition(self) -> Dict[str, Any]:
        """获取 OpenAI Function Calling 格式的工具定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    def _get_headers(self, need_user_id: bool = True) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if need_user_id:
            headers["X-User-ID"] = self.user_id
        return headers

    async def _get(self, endpoint: str, params: Optional[Dict] = None, need_user_id: bool = True) -> Dict[str, Any]:
        """发送 GET 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(need_user_id)

        logger.debug(f"GET请求 | URL: {url} | 参数: {params}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                return self._handle_response(response, url)
            except httpx.TimeoutException:
                logger.error(f"GET请求超时 | URL: {url}")
                return {"error": True, "message": "请求超时"}
            except Exception as e:
                logger.error(f"GET请求异常 | URL: {url} | 错误: {str(e)}")
                return {"error": True, "message": str(e)}

    async def _post(self, endpoint: str, data: Optional[Dict] = None, need_user_id: bool = True) -> Dict[str, Any]:
        """发送 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(need_user_id)

        logger.debug(f"POST请求 | URL: {url} | 数据: {data}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=data, headers=headers)
                return self._handle_response(response, url)
            except httpx.TimeoutException:
                logger.error(f"POST请求超时 | URL: {url}")
                return {"error": True, "message": "请求超时"}
            except Exception as e:
                logger.error(f"POST请求异常 | URL: {url} | 错误: {str(e)}")
                return {"error": True, "message": str(e)}

    def _handle_response(self, response: httpx.Response, url: str) -> Dict[str, Any]:
        """处理响应"""
        logger.debug(f"响应状态码: {response.status_code} | URL: {url}")

        if response.status_code == 200:
            try:
                result = response.json()
                logger.debug(f"响应成功 | 数据长度: {len(str(result))}")
                return result
            except Exception as e:
                logger.error(f"JSON解析失败 | URL: {url}")
                return {"error": True, "message": f"JSON解析失败: {str(e)}"}
        else:
            error_text = response.text
            logger.error(f"请求失败 | URL: {url} | 状态码: {response.status_code} | 响应: {error_text}")
            return {
                "error": True,
                "status_code": response.status_code,
                "message": error_text
            }


class LandmarkTool(BaseTool):
    """地标工具基类 - 不需要 X-User-ID"""

    def __init__(self, user_id: Optional[str] = None):
        super().__init__(user_id)

    async def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """发送 GET 请求（不需要 X-User-ID）"""
        return await super()._get(endpoint, params, need_user_id=False)


class HouseTool(BaseTool):
    """房源工具基类 - 需要 X-User-ID"""
    pass


class RentTool(BaseTool):
    """租房操作工具基类 - 需要 X-User-ID"""
    pass