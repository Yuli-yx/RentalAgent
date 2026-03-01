"""对话接口路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from app.services.agent_service import AgentService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger()


class ChatRequest(BaseModel):
    """对话请求模型"""
    model_ip: str = Field(..., description="模型服务IP地址")
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="用户消息")
    user_id: Optional[str] = Field(None, description="用户工号（可选）")


class ChatResponse(BaseModel):
    """对话响应模型"""
    session_id: str
    response: str
    status: str
    tool_results: List[Any] = []
    timestamp: int
    duration_ms: int


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    处理对话请求

    - model_ip: 模型服务IP地址
    - session_id: 会话ID，用于多轮对话
    - message: 用户消息
    - user_id: 用户工号（可选，不传则使用配置文件中的默认值）
    """
    logger.info(f"收到对话请求 | session_id: {request.session_id} | model_ip: {request.model_ip}")
    logger.debug(f"用户消息: {request.message}")
    logger.debug(f"用户ID: {request.user_id or '使用默认值'}")

    try:
        agent = AgentService(
            model_ip=request.model_ip,
            session_id=request.session_id,
            user_id=request.user_id
        )

        result = await agent.process_message(request.message)

        logger.info(
            f"对话完成 | session_id: {request.session_id} | "
            f"状态: {result['status']} | 耗时: {result['duration_ms']}ms"
        )
        logger.debug(f"响应内容: {result['response'][:200]}..." if len(result['response']) > 200 else f"响应内容: {result['response']}")

        return ChatResponse(**result)

    except Exception as e:
        logger.error(f"对话处理异常 | session_id: {request.session_id} | 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))