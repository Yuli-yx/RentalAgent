"""工具模块初始化，导出所有工具"""
from typing import Dict, Any, Optional, List, Type
from app.tools.base import BaseTool
from app.tools.landmark_tools import (
    GetLandmarksTool,
    GetLandmarkByNameTool,
    SearchLandmarksTool,
    GetLandmarkByIdTool,
    LANDMARK_TOOLS
)
from app.tools.house_tools import (
    GetHouseByIdTool,
    GetHouseListingsTool,
    GetHousesByCommunityTool,
    SearchHousesTool,
    GetHousesNearbyTool,
    GetNearbyLandmarksTool,
    GetHouseStatsTool,
    GetLandmarkStatsTool,
    HOUSE_TOOLS
)
from app.tools.rent_tools import (
    RentHouseTool,
    TerminateRentalTool,
    TakeOfflineTool,
    ResetHousesTool,
    RENT_TOOLS
)

# 所有工具类
ALL_TOOLS: List[Type[BaseTool]] = LANDMARK_TOOLS + HOUSE_TOOLS + RENT_TOOLS


def get_tool_by_name(name: str, user_id: Optional[str] = None) -> Optional[BaseTool]:
    """根据工具名获取工具实例"""
    for tool_class in ALL_TOOLS:
        if tool_class(user_id).name == name:
            return tool_class(user_id)
    return None


def get_all_tool_definitions(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取所有工具的 OpenAI Function Calling 定义"""
    definitions = []
    for tool_class in ALL_TOOLS:
        tool = tool_class(user_id)
        definitions.append(tool.get_openai_tool_definition())
    return definitions


__all__ = [
    # 地标工具
    "GetLandmarksTool",
    "GetLandmarkByNameTool",
    "SearchLandmarksTool",
    "GetLandmarkByIdTool",
    # 房源工具
    "GetHouseByIdTool",
    "GetHouseListingsTool",
    "GetHousesByCommunityTool",
    "SearchHousesTool",
    "GetHousesNearbyTool",
    "GetNearbyLandmarksTool",
    "GetHouseStatsTool",
    "GetLandmarkStatsTool",
    # 租房工具
    "RentHouseTool",
    "TerminateRentalTool",
    "TakeOfflineTool",
    "ResetHousesTool",
    # 辅助函数
    "get_tool_by_name",
    "get_all_tool_definitions",
    "ALL_TOOLS"
]