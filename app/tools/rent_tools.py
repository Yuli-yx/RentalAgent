"""租房操作工具 (4个工具，需要X-User-ID)"""
from typing import Dict, Any
from app.tools.base import RentTool


class RentHouseTool(RentTool):
    """租房"""

    @property
    def name(self) -> str:
        return "rent_house"

    @property
    def description(self) -> str:
        return "租下指定房源，执行后房源状态变为已租。需要确认用户确实想要租该房源。必须指定挂牌平台。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "house_id": {
                    "type": "string",
                    "description": "要租的房源ID"
                },
                "listing_platform": {
                    "type": "string",
                    "description": "挂牌平台：链家/安居客/58同城（必填）"
                }
            },
            "required": ["house_id", "listing_platform"]
        }

    async def execute(self, house_id: str, listing_platform: str) -> Dict[str, Any]:
        return await self._post(f"/api/houses/{house_id}/rent?listing_platform={listing_platform}")


class TerminateRentalTool(RentTool):
    """退租"""

    @property
    def name(self) -> str:
        return "terminate_rental"

    @property
    def description(self) -> str:
        return "退租指定房源，执行后房源状态变为可租。需要确认用户确实想要退租。必须指定挂牌平台。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "house_id": {
                    "type": "string",
                    "description": "要退租的房源ID"
                },
                "listing_platform": {
                    "type": "string",
                    "description": "挂牌平台：链家/安居客/58同城（必填）"
                }
            },
            "required": ["house_id", "listing_platform"]
        }

    async def execute(self, house_id: str, listing_platform: str) -> Dict[str, Any]:
        return await self._post(f"/api/houses/{house_id}/terminate?listing_platform={listing_platform}")


class TakeOfflineTool(RentTool):
    """下架房源"""

    @property
    def name(self) -> str:
        return "take_offline"

    @property
    def description(self) -> str:
        return "下架指定房源，执行后房源不再显示在列表中。需要确认用户确实想要下架。必须指定挂牌平台。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "house_id": {
                    "type": "string",
                    "description": "要下架的房源ID"
                },
                "listing_platform": {
                    "type": "string",
                    "description": "挂牌平台：链家/安居客/58同城（必填）"
                }
            },
            "required": ["house_id", "listing_platform"]
        }

    async def execute(self, house_id: str, listing_platform: str) -> Dict[str, Any]:
        return await self._post(f"/api/houses/{house_id}/offline?listing_platform={listing_platform}")


class ResetHousesTool(RentTool):
    """重置房源数据"""

    @property
    def name(self) -> str:
        return "reset_houses"

    @property
    def description(self) -> str:
        return "重置所有房源数据到初始状态。每个新会话开始时应调用此工具以确保数据干净。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }

    async def execute(self) -> Dict[str, Any]:
        return await self._post("/api/houses/init")


# 导出所有租房操作工具
RENT_TOOLS = [
    RentHouseTool,
    TerminateRentalTool,
    TakeOfflineTool,
    ResetHousesTool
]