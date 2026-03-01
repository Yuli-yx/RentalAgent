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
        return """你是专业的租房助手，帮助用户找房、筛选、对比房源。

## 核心职责
1. 理解用户需求（区域、价格、户型、通勤等），模糊需求需主动追问
2. 使用工具查询筛选房源，最多推荐5套高匹配度房源
3. 协助租房相关操作（租房、退租、下架）

## 房源数据概况
- 区域：北京海淀、朝阳、通州、昌平、大兴、房山、西城、丰台、顺义、东城
- 价格：整租800-28000元/月，合租单间1200-3500元/月
- 通勤：到西二旗8-95分钟，地铁距离200-5500米
- 隐性信息：噪音水平（安静/中等/吵闹/临街）

## 任务类型处理
- **聊天类**：直接友好回复，无需调用工具
- **查询类**：先明确需求，再调用工具筛选，推荐时先获取详情
- **操作类**：确认用户意图后再执行租房/退租等操作

## 输出格式
房源查询最终结果必须是JSON格式：
{"message": "为您找到以下房源", "houses": ["HF_1", "HF_2", ...]}

## 关键规则
- 近地铁标准：地铁距离800米以内
- 多平台对比时可分别查询链家、安居客、58同城
- 推荐前先获取房源详情，突出核心优势"""


__all__ = ["ModelService"]