"""地标相关工具 (4个工具，无需X-User-ID)"""
from typing import Dict, Any, Optional
from app.tools.base import LandmarkTool


class GetLandmarksTool(LandmarkTool):
    """获取地标列表"""

    @property
    def name(self) -> str:
        return "get_landmarks"

    @property
    def description(self) -> str:
        return "获取地标列表，支持按类别和区域筛选。类别包括：地铁站、商场、医院、学校等。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "地标类别，如：地铁站、商场、医院、学校"
                },
                "district": {
                    "type": "string",
                    "description": "行政区，如海淀、朝阳"
                }
            }
        }

    async def execute(self, category: Optional[str] = None, district: Optional[str] = None) -> Dict[str, Any]:
        params = {}
        if category:
            params["category"] = category
        if district:
            params["district"] = district
        return await self._get("/api/landmarks", params)


class GetLandmarkByNameTool(LandmarkTool):
    """按名称精确查询地标"""

    @property
    def name(self) -> str:
        return "get_landmark_by_name"

    @property
    def description(self) -> str:
        return "按名称精确查询地标信息，返回地标详情包括位置、类别等。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "地标名称，如西二旗地铁站、中关村"
                }
            },
            "required": ["name"]
        }

    async def execute(self, name: str) -> Dict[str, Any]:
        return await self._get(f"/api/landmarks/name/{name}")


class SearchLandmarksTool(LandmarkTool):
    """关键词模糊搜索地标"""

    @property
    def name(self) -> str:
        return "search_landmarks"

    @property
    def description(self) -> str:
        return "关键词模糊搜索地标，支持部分名称匹配。可同时按类别和区域筛选。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "搜索关键词，必填"
                },
                "category": {
                    "type": "string",
                    "description": "可选，限定类别：subway(地铁)/company(公司)/landmark(商圈等)"
                },
                "district": {
                    "type": "string",
                    "description": "可选，限定行政区，如海淀、朝阳"
                }
            },
            "required": ["q"]
        }

    async def execute(self, q: str, category: Optional[str] = None, district: Optional[str] = None) -> Dict[str, Any]:
        params = {"q": q}
        if category:
            params["category"] = category
        if district:
            params["district"] = district
        return await self._get("/api/landmarks/search", params)


class GetLandmarkByIdTool(LandmarkTool):
    """按ID查询地标详情"""

    @property
    def name(self) -> str:
        return "get_landmark_by_id"

    @property
    def description(self) -> str:
        return "按ID查询地标详情，返回地标完整信息。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "landmark_id": {
                    "type": "string",
                    "description": "地标ID"
                }
            },
            "required": ["landmark_id"]
        }

    async def execute(self, landmark_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/landmarks/{landmark_id}")


# 导出所有地标工具
LANDMARK_TOOLS = [
    GetLandmarksTool,
    GetLandmarkByNameTool,
    SearchLandmarksTool,
    GetLandmarkByIdTool
]