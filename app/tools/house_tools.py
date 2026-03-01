"""房源查询工具 (8个工具，需要X-User-ID)"""
from typing import Dict, Any, Optional
from app.tools.base import HouseTool


class GetHouseByIdTool(HouseTool):
    """根据ID获取房源详情"""

    @property
    def name(self) -> str:
        return "get_house_by_id"

    @property
    def description(self) -> str:
        return "根据房源ID获取房源详细信息，包括价格、面积、户型、位置、装修等完整信息。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "house_id": {
                    "type": "string",
                    "description": "房源ID，如 HF_1, HF_2, HF_2001"
                }
            },
            "required": ["house_id"]
        }

    async def execute(self, house_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/houses/{house_id}")


class GetHouseListingsTool(HouseTool):
    """获取房源在各平台的挂牌记录"""

    @property
    def name(self) -> str:
        return "get_house_listings"

    @property
    def description(self) -> str:
        return "获取房源在各平台（链家、安居客、58同城）的挂牌记录，包括价格变动历史。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "house_id": {
                    "type": "string",
                    "description": "房源ID"
                }
            },
            "required": ["house_id"]
        }

    async def execute(self, house_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/houses/listings/{house_id}")


class GetHousesByCommunityTool(HouseTool):
    """按小区名查询房源"""

    @property
    def name(self) -> str:
        return "get_houses_by_community"

    @property
    def description(self) -> str:
        return "按小区名称查询该小区下可租房源列表。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "community": {
                    "type": "string",
                    "description": "小区名，如建清园(南区)、保利锦上(二期)"
                },
                "listing_platform": {
                    "type": "string",
                    "description": "挂牌平台：链家/安居客/58同城，不传则默认安居客"
                },
                "page": {
                    "type": "integer",
                    "description": "页码，默认1"
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页条数，默认10，最大10000"
                }
            },
            "required": ["community"]
        }

    async def execute(self, community: str, listing_platform: Optional[str] = None,
                      page: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        params = {"community": community}
        if listing_platform:
            params["listing_platform"] = listing_platform
        if page:
            params["page"] = page
        if page_size:
            params["page_size"] = page_size
        return await self._get("/api/houses/by_community", params)


class SearchHousesTool(HouseTool):
    """多条件筛选房源（核心查询工具）"""

    @property
    def name(self) -> str:
        return "search_houses"

    @property
    def description(self) -> str:
        return """多条件筛选房源，这是最常用的房源查询工具。
支持筛选条件：
- district: 行政区（海淀、朝阳、东城、西城、丰台、石景山等），可逗号分隔多个
- area: 商圈，可逗号分隔多个
- min_price/max_price: 价格范围（月租金，单位元）
- bedrooms: 卧室数（可逗号分隔，如1,2,3）
- rental_type: 租赁类型（整租/合租）
- decoration: 装修（精装/简装/豪华/毛坯/空房）
- orientation: 朝向（朝南/朝北/朝东/朝西/南北/东西）
- elevator: 是否有电梯（true/false）
- min_area/max_area: 面积范围（平方米）
- subway_line: 地铁线路，如13号线
- subway_station: 地铁站名
- max_subway_dist: 最大地铁距离（米），近地铁建议设为800
- commute_to_xierqi_max: 到西二旗通勤时间上限（分钟）
- listing_platform: 挂牌平台（链家/安居客/58同城）
- utilities_type: 水电类型（民水民电等）
- available_from_before: 可入住日期上限（YYYY-MM-DD）
- sort_by: 排序字段（price/area/subway）
- sort_order: 排序方向（asc/desc）"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "listing_platform": {
                    "type": "string",
                    "description": "挂牌平台：链家/安居客/58同城，不传则默认安居客"
                },
                "district": {
                    "type": "string",
                    "description": "行政区，逗号分隔，如海淀,朝阳"
                },
                "area": {
                    "type": "string",
                    "description": "商圈，逗号分隔，如西二旗,上地"
                },
                "min_price": {
                    "type": "integer",
                    "description": "最低月租金（元）"
                },
                "max_price": {
                    "type": "integer",
                    "description": "最高月租金（元）"
                },
                "bedrooms": {
                    "type": "string",
                    "description": "卧室数，逗号分隔，如1,2"
                },
                "rental_type": {
                    "type": "string",
                    "description": "租赁类型：整租或合租"
                },
                "decoration": {
                    "type": "string",
                    "description": "装修情况：精装/简装/豪华/毛坯/空房"
                },
                "orientation": {
                    "type": "string",
                    "description": "朝向：朝南/朝北/朝东/朝西/南北/东西"
                },
                "elevator": {
                    "type": "string",
                    "description": "是否有电梯：true或false"
                },
                "min_area": {
                    "type": "integer",
                    "description": "最小面积（平方米）"
                },
                "max_area": {
                    "type": "integer",
                    "description": "最大面积（平方米）"
                },
                "property_type": {
                    "type": "string",
                    "description": "物业类型，如住宅"
                },
                "subway_line": {
                    "type": "string",
                    "description": "地铁线路，如13号线"
                },
                "subway_station": {
                    "type": "string",
                    "description": "地铁站名，如车公庄站"
                },
                "max_subway_dist": {
                    "type": "integer",
                    "description": "最大地铁距离（米），近地铁建议800"
                },
                "utilities_type": {
                    "type": "string",
                    "description": "水电类型，如民水民电"
                },
                "available_from_before": {
                    "type": "string",
                    "description": "可入住日期上限，YYYY-MM-DD格式"
                },
                "commute_to_xierqi_max": {
                    "type": "integer",
                    "description": "到西二旗通勤时间上限（分钟）"
                },
                "sort_by": {
                    "type": "string",
                    "description": "排序字段：price/area/subway"
                },
                "sort_order": {
                    "type": "string",
                    "description": "排序方向：asc或desc"
                },
                "page": {
                    "type": "integer",
                    "description": "页码，默认1"
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页条数，默认10，最大10000"
                }
            }
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        # 过滤掉 None 值
        params = {k: v for k, v in kwargs.items() if v is not None}
        return await self._get("/api/houses/by_platform", params)


class GetHousesNearbyTool(HouseTool):
    """查询地标附近房源"""

    @property
    def name(self) -> str:
        return "get_houses_nearby"

    @property
    def description(self) -> str:
        return "以地标为圆心，查询指定距离内的可租房源，返回带直线距离、步行距离、步行时间。需先通过地标接口获得landmark_id。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "landmark_id": {
                    "type": "string",
                    "description": "地标ID或地标名称（支持按名称查找）"
                },
                "max_distance": {
                    "type": "integer",
                    "description": "最大直线距离（米），默认2000"
                },
                "listing_platform": {
                    "type": "string",
                    "description": "挂牌平台：链家/安居客/58同城，不传则默认安居客"
                },
                "page": {
                    "type": "integer",
                    "description": "页码，默认1"
                },
                "page_size": {
                    "type": "integer",
                    "description": "每页条数，默认10，最大10000"
                }
            },
            "required": ["landmark_id"]
        }

    async def execute(self, landmark_id: str, max_distance: Optional[int] = None,
                      listing_platform: Optional[str] = None,
                      page: Optional[int] = None, page_size: Optional[int] = None) -> Dict[str, Any]:
        params = {"landmark_id": landmark_id}
        if max_distance is not None:
            params["max_distance"] = max_distance
        if listing_platform:
            params["listing_platform"] = listing_platform
        if page:
            params["page"] = page
        if page_size:
            params["page_size"] = page_size
        return await self._get("/api/houses/nearby", params)


class GetNearbyLandmarksTool(HouseTool):
    """查询小区周边地标"""

    @property
    def name(self) -> str:
        return "get_nearby_landmarks"

    @property
    def description(self) -> str:
        return "查询某小区周边某类地标（商超/公园），按距离排序。用于回答「附近有没有商场/公园」。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "community": {
                    "type": "string",
                    "description": "小区名，用于定位基准点"
                },
                "type": {
                    "type": "string",
                    "description": "地标类型：shopping(商超)或park(公园)，不传则不过滤"
                },
                "max_distance_m": {
                    "type": "integer",
                    "description": "最大距离（米），默认3000"
                }
            },
            "required": ["community"]
        }

    async def execute(self, community: str, type: Optional[str] = None,
                      max_distance_m: Optional[int] = None) -> Dict[str, Any]:
        params = {"community": community}
        if type:
            params["type"] = type
        if max_distance_m is not None:
            params["max_distance_m"] = max_distance_m
        return await self._get("/api/houses/nearby_landmarks", params)


class GetHouseStatsTool(HouseTool):
    """获取房源统计信息"""

    @property
    def name(self) -> str:
        return "get_house_stats"

    @property
    def description(self) -> str:
        return "获取房源统计信息，包括总套数、按状态/行政区/户型分布、价格区间等，按当前用户视角统计。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }

    async def execute(self) -> Dict[str, Any]:
        return await self._get("/api/houses/stats")


class GetLandmarkStatsTool(HouseTool):
    """获取地标统计信息"""

    @property
    def name(self) -> str:
        return "get_landmark_stats"

    @property
    def description(self) -> str:
        return "获取地标统计信息，包括总数、按类别分布等。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }

    async def execute(self) -> Dict[str, Any]:
        return await self._get("/api/landmarks/stats")


# 导出所有房源工具
HOUSE_TOOLS = [
    GetHouseByIdTool,
    GetHouseListingsTool,
    GetHousesByCommunityTool,
    SearchHousesTool,
    GetHousesNearbyTool,
    GetNearbyLandmarksTool,
    GetHouseStatsTool,
    GetLandmarkStatsTool
]