"""Agent核心服务"""
import json
import time
from typing import Dict, Any, List, Optional
from app.services.model_service import ModelService
from app.tools import get_tool_by_name, get_all_tool_definitions
from app.utils.session_manager import session_manager
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger()


class AgentService:
    """Agent核心服务，处理对话和工具调用"""

    # 最大工具调用迭代次数，防止无限循环
    MAX_ITERATIONS = 10

    def __init__(self, model_ip: str, session_id: str, user_id: Optional[str] = None):
        self.model_ip = model_ip
        self.session_id = session_id
        self.user_id = user_id or settings.DEFAULT_USER_ID
        self.model_service = ModelService(model_ip, session_id)
        logger.debug(f"AgentService初始化 | session_id: {session_id} | user_id: {self.user_id}")

    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        处理用户消息

        Args:
            message: 用户消息

        Returns:
            处理结果
        """
        start_time = time.time()
        logger.info(f"开始处理消息 | session_id: {self.session_id}")
        logger.debug(f"用户消息内容: {message}")

        # 检查是否需要重置房源数据（新会话第一次调用）
        if not session_manager.is_reset_done(self.session_id):
            logger.info(f"新会话，重置房源数据 | session_id: {self.session_id}")
            await self._reset_houses()
            session_manager.set_reset_done(self.session_id)

        # 添加用户消息到历史
        session_manager.add_message(self.session_id, "user", message)

        # 获取对话历史
        messages = self._build_messages()
        logger.debug(f"构建消息列表 | 消息数: {len(messages)}")

        # 获取工具定义
        tools = get_all_tool_definitions(self.user_id)
        logger.debug(f"加载工具定义 | 工具数: {len(tools)}")

        # 调用模型
        logger.info(f"调用模型服务 | model_ip: {self.model_ip}")
        response = await self.model_service.chat(messages, tools)

        if response.get("error"):
            logger.error(f"模型调用失败: {response}")
            return self._build_error_response(response, start_time)

        # 处理模型响应（可能包含多轮工具调用）
        result = await self._handle_model_response(response, start_time)

        return result

    async def _handle_model_response(self, response: Dict[str, Any], start_time: float, iteration: int = 0) -> Dict[str, Any]:
        """处理模型响应"""
        # 检查迭代次数
        if iteration >= self.MAX_ITERATIONS:
            logger.warning(f"达到最大迭代次数: {self.MAX_ITERATIONS}")
            return self._build_error_response(
                {"message": "超过最大工具调用次数"},
                start_time
            )

        choice = response.get("choices", [{}])[0]
        message = choice.get("message", {})

        # 检查是否有工具调用
        tool_calls = message.get("tool_calls")

        if tool_calls:
            logger.info(f"模型请求工具调用 | 迭代: {iteration + 1} | 工具数: {len(tool_calls)}")

            # 添加助手消息到历史（包含tool_calls）
            assistant_message = {
                "role": "assistant",
                "content": message.get("content"),
                "tool_calls": tool_calls
            }
            session_manager.add_message(self.session_id, "assistant", json.dumps(assistant_message, ensure_ascii=False))

            # 执行所有工具调用并添加结果到历史
            for tool_call in tool_calls:
                result = await self._execute_tool_call(tool_call)

            # 重新调用模型获取最终响应
            messages = self._build_messages()
            tools = get_all_tool_definitions(self.user_id)

            logger.info(f"重新调用模型 | 迭代: {iteration + 1}")
            new_response = await self.model_service.chat(messages, tools)

            if new_response.get("error"):
                logger.error(f"模型调用失败: {new_response}")
                return self._build_error_response(new_response, start_time)

            return await self._handle_model_response(new_response, start_time, iteration + 1)
        else:
            # 直接回复
            content = message.get("content", "")
            logger.info(f"模型返回最终回复 | 内容长度: {len(content)}")
            session_manager.add_message(self.session_id, "assistant", content)

            return self._build_success_response(content, start_time)

    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        function = tool_call.get("function", {})
        tool_name = function.get("name")
        arguments_str = function.get("arguments", "{}")
        tool_id = tool_call.get("id")

        logger.info(f"执行工具: {tool_name}")
        logger.debug(f"工具参数: {arguments_str}")

        try:
            arguments = json.loads(arguments_str)
        except json.JSONDecodeError:
            logger.warning(f"工具参数解析失败，使用空参数")
            arguments = {}

        # 获取工具实例
        tool = get_tool_by_name(tool_name, self.user_id)

        if not tool:
            error_msg = f"未找到工具: {tool_name}"
            logger.error(error_msg)
            result = {"error": True, "message": error_msg}
        else:
            try:
                result = await tool.execute(**arguments)
                logger.info(f"工具执行成功: {tool_name}")
                logger.debug(f"工具返回结果: {json.dumps(result, ensure_ascii=False)[:500]}...")
            except Exception as e:
                error_msg = str(e)
                logger.error(f"工具执行异常: {tool_name} | 错误: {error_msg}", exc_info=True)
                result = {"error": True, "message": error_msg}

        # 添加工具结果到历史（OpenAI 格式）
        tool_message = {
            "role": "tool",
            "tool_call_id": tool_id,
            "content": json.dumps(result, ensure_ascii=False)
        }
        session_manager.add_message(self.session_id, "tool", json.dumps(tool_message, ensure_ascii=False))

        return {
            "tool_call_id": tool_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result
        }

    def _build_messages(self) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = [
            {"role": "system", "content": self.model_service.get_default_system_prompt()}
        ]

        # 添加历史消息
        history = session_manager.get_messages(self.session_id)
        for msg in history:
            # 如果是字符串，尝试解析为JSON
            if isinstance(msg, dict):
                messages.append(msg)
            elif isinstance(msg, str):
                try:
                    parsed = json.loads(msg)
                    messages.append(parsed)
                except json.JSONDecodeError:
                    # 如果无法解析，假设是简单文本消息
                    messages.append({"role": "user", "content": msg})

        return messages

    async def _reset_houses(self):
        """重置房源数据"""
        from app.tools import ResetHousesTool
        reset_tool = ResetHousesTool(self.user_id)
        try:
            result = await reset_tool.execute()
            logger.info(f"房源数据重置成功")
        except Exception as e:
            logger.warning(f"房源数据重置失败: {e}")

    def _build_success_response(self, content: str, start_time: float) -> Dict[str, Any]:
        """构建成功响应"""
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(f"请求处理完成 | 耗时: {duration_ms}ms")

        return {
            "session_id": self.session_id,
            "response": content,
            "status": "success",
            "tool_results": [],
            "timestamp": int(time.time()),
            "duration_ms": duration_ms
        }

    def _build_error_response(self, error: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """构建错误响应"""
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(f"请求处理失败 | 耗时: {duration_ms}ms | 错误: {error}")

        return {
            "session_id": self.session_id,
            "response": f"发生错误: {error.get('message', '未知错误')}",
            "status": "error",
            "tool_results": [],
            "timestamp": int(time.time()),
            "duration_ms": duration_ms,
            "error": error
        }


__all__ = ["AgentService"]