"""模型调用服务"""
import httpx
from typing import Dict, Any, List, Optional
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger()


class ModelService:
    """模型调用服务，支持 OpenAI 兼容格式"""

    def __init__(self, model_ip: str, session_id: Optional[str] = None):
        self.model_ip = model_ip
        self.session_id = session_id
        self.base_url = f"http://{model_ip}:{settings.MODEL_PORT}"
        logger.debug(f"ModelService初始化 | base_url: {self.base_url}")

    def _get_api_path(self) -> str:
        """获取 API 路径，根据调试模式选择 V1 或 V2"""
        if settings.DEBUG_MODE:
            return "/v2/chat/completions"
        return "/v1/chat/completions"

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        # 只有正式模式才需要 Session-ID
        if not settings.DEBUG_MODE and self.session_id:
            headers["Session-ID"] = self.session_id
        return headers

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        调用模型进行对话

        Args:
            messages: 对话消息列表
            tools: 工具定义列表
            tool_choice: 工具选择策略 (auto/none/required)

        Returns:
            模型响应
        """
        url = f"{self.base_url}{self._get_api_path()}"

        payload = {
            "model": "default",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        headers = self._get_headers()

        logger.info(f"调用模型API | URL: {url}")
        logger.debug(f"请求头: {headers}")
        logger.debug(f"消息数: {len(messages)} | 工具数: {len(tools) if tools else 0}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers
                )

                logger.debug(f"响应状态码: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"模型调用成功")
                    return result
                else:
                    error_text = response.text
                    logger.error(f"模型调用失败 | 状态码: {response.status_code} | 响应: {error_text}")
                    return {
                        "error": True,
                        "status_code": response.status_code,
                        "message": error_text
                    }
            except httpx.TimeoutException:
                logger.error(f"模型调用超时")
                return {
                    "error": True,
                    "message": "请求超时"
                }
            except Exception as e:
                logger.error(f"模型调用异常: {str(e)}", exc_info=True)
                return {
                    "error": True,
                    "message": str(e)
                }

    def get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个专业的租房助手，帮助用户找到合适的房源。

## 你的职责
1. 理解用户的租房需求（区域、价格、户型、装修、通勤等）
2. 使用工具查询和筛选房源
3. 为用户推荐最合适的房源（最多5套）
4. 协助用户完成租房相关操作

## 工具使用指南
- search_houses: 最常用的房源查询工具，支持多条件筛选
- get_houses_nearby: 查询地标附近的房源
- get_house_by_id: 获取房源详情
- get_landmarks/search_landmarks: 查询地标信息
- rent_house: 租房操作
- reset_houses: 重置房源数据（新会话开始时自动调用）

## 重要规则
1. 每次查询最多返回5套房源
2. 房源查询结果必须以JSON格式返回，格式如下：
   {"message": "为您找到以下房源", "houses": ["HF_1", "HF_2", ...]}
3. 近地铁标准：地铁距离800米以内
4. 在推荐房源前，先获取房源详情了解完整信息
5. 主动询问用户需求细节，如预算、区域偏好、户型要求等

## 回复要求
- 简洁明了，避免冗余
- 突出房源的核心优势
- 提供实用的建议
- 房源查询最终结果必须是JSON格式的房源ID列表"""


__all__ = ["ModelService"]