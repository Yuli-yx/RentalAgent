# 租房 AI Agent 设计说明书

## 文档信息

| 项目名称 | 租房 AI Agent |
|---------|--------------|
| 版本号 | V1.0 |
| 编写日期 | 2026-03-01 |
| 文档状态 | 正式发布 |

---

## 目录

1. [概述](#1-概述)
2. [系统架构设计](#2-系统架构设计)
3. [核心模块设计](#3-核心模块设计)
4. [工具系统设计](#4-工具系统设计)
5. [对话流程设计](#5-对话流程设计)
6. [会话管理设计](#6-会话管理设计)
7. [日志系统设计](#7-日志系统设计)
8. [接口设计](#8-接口设计)
9. [数据结构设计](#9-数据结构设计)
10. [错误处理设计](#10-错误处理设计)
11. [性能优化设计](#11-性能优化设计)
12. [部署设计](#12-部署设计)

---

## 1. 概述

### 1.1 项目背景

本项目是一个租房 AI Agent 开发挑战赛项目，目标是开发一个智能租房助手，能够：
- 精准识别用户租房多元需求
- 自动完成房源信息搜集、筛选、核验
- 多维度分析候选房源
- 输出最多5套高匹配度候选房源

### 1.2 设计目标

1. **高可用性**：服务稳定运行，支持多用户并发访问
2. **可扩展性**：模块化设计，便于功能扩展
3. **可维护性**：完善的日志系统，便于问题排查
4. **高性能**：响应快速，处理高效

### 1.3 技术选型

| 技术领域 | 选型 | 说明 |
|---------|------|------|
| Web框架 | FastAPI | 高性能异步框架，自动API文档 |
| HTTP客户端 | httpx | 支持异步请求 |
| 数据验证 | Pydantic | 请求数据验证 |
| 模型接口 | OpenAI兼容格式 | 支持 Function Calling |
| 日志系统 | logging | Python标准库 |

---

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        判题系统 / 用户                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Agent API (FastAPI:8191)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Router    │  │ Middleware  │  │     Exception Handler   │  │
│  │  (chat.py)  │  │  (logging)  │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Service                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Message   │  │    Tool     │  │     Session Manager     │  │
│  │  Processing │  │  Execution  │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
┌───────────────────────────┐  ┌───────────────────────────────────┐
│      Model Service        │  │           Tool System             │
│  ┌─────────────────────┐  │  │  ┌─────────┐ ┌─────────┐        │
│  │  OpenAI Compatible  │  │  │  │ Landmark│ │  House  │        │
│  │       API           │  │  │  │  Tools  │ │  Tools  │        │
│  └─────────────────────┘  │  │  └─────────┘ └─────────┘        │
└───────────────────────────┘  │  ┌─────────┐ ┌─────────┐        │
            │                  │  │  Rent   │ │  Stats  │        │
            ▼                  │  │  Tools  │ │  Tools  │        │
┌───────────────────────────┐  │  └─────────┘ └─────────┘        │
│   模型服务 (model_ip:8888) │  └───────────────────────────────────┘
│   - V1接口 (正式模式)      │                  │
│   - V2接口 (调试模式)      │                  ▼
└───────────────────────────┘  ┌───────────────────────────────────┐
                                           │  房源API (7.225.29.223:8080)  │
                                           │  - 地标服务                     │
                                           │  - 房源服务                     │
                                           │  - 租房操作服务                 │
                                           └───────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 关键文件 |
|------|------|---------|
| API层 | 接收请求、返回响应、路由分发 | main.py, chat.py |
| Service层 | 核心业务逻辑、工具调用编排 | agent_service.py, model_service.py |
| Tool层 | 封装外部API调用 | landmark_tools.py, house_tools.py, rent_tools.py |
| Utils层 | 会话管理、日志记录 | session_manager.py, logger.py |

### 2.3 请求处理流程

```
Request → Router → AgentService → SessionManager
                              ↓
                         ModelService ←→ Model API
                              ↓
                         Tool Execution ←→ Rental API
                              ↓
                         Response Builder → Response
```

---

## 3. 核心模块设计

### 3.1 Agent Service

**文件**: `app/services/agent_service.py`

**职责**: 核心业务逻辑处理，包括消息处理、工具调用编排、响应构建

**关键方法**:

```python
class AgentService:
    async def process_message(message: str) -> Dict[str, Any]:
        """处理用户消息的主入口"""

    async def _handle_model_response(response, start_time, iteration) -> Dict[str, Any]:
        """处理模型响应，支持多轮工具调用"""

    async def _execute_tool_call(tool_call) -> Dict[str, Any]:
        """执行单个工具调用"""

    def _build_messages() -> List[Dict]:
        """构建发送给模型的消息列表"""
```

**设计要点**:

1. **迭代处理**: 支持多轮工具调用，设置最大迭代次数(10次)防止无限循环
2. **会话隔离**: 通过 session_id 隔离不同用户的会话
3. **数据重置**: 新会话自动调用 reset_houses 确保数据干净

### 3.2 Model Service

**文件**: `app/services/model_service.py`

**职责**: 封装模型API调用，支持OpenAI兼容格式

**关键方法**:

```python
class ModelService:
    async def chat(messages, tools, tool_choice) -> Dict[str, Any]:
        """调用模型进行对话"""

    def get_default_system_prompt() -> str:
        """获取系统提示词"""
```

**设计要点**:

1. **双接口支持**: V1接口(正式)需要Session-ID，V2接口(调试)不需要
2. **超时处理**: 设置60秒超时，防止长时间等待
3. **错误处理**: 捕获网络异常，返回友好错误信息

### 3.3 Session Manager

**文件**: `app/utils/session_manager.py`

**职责**: 管理多轮对话上下文

**数据结构**:

```python
session = {
    "session_id_1": {
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."},
            {"role": "tool", "content": "..."}
        ],
        "context": {},  # 预留上下文存储
        "reset_done": True  # 标记是否已重置房源数据
    }
}
```

**关键方法**:

```python
class SessionManager:
    def get_or_create_session(session_id) -> Dict:
        """获取或创建会话"""

    def add_message(session_id, role, content):
        """添加消息到历史"""

    def get_messages(session_id) -> List[Dict]:
        """获取会话历史消息"""
```

**设计要点**:

1. **内存存储**: 使用字典存储会话，适合单机部署
2. **历史限制**: 限制最大历史消息数(40条，即20轮对话)
3. **会话状态**: 跟踪房源数据重置状态

---

## 4. 工具系统设计

### 4.1 工具基类设计

**文件**: `app/tools/base.py`

```python
class BaseTool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """工具参数定义 (OpenAI Function Calling 格式)"""

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具"""

    def get_openai_tool_definition(self) -> Dict[str, Any]:
        """获取 OpenAI Function Calling 格式的工具定义"""
```

**继承关系**:

```
BaseTool (抽象基类)
    ├── LandmarkTool (地标工具，不需要X-User-ID)
    ├── HouseTool (房源工具，需要X-User-ID)
    └── RentTool (租房操作工具，需要X-User-ID)
```

### 4.2 工具分类

#### 4.2.1 地标工具 (4个)

| 工具类 | 工具名 | API路径 | 需要认证 |
|--------|--------|---------|---------|
| GetLandmarksTool | get_landmarks | GET /api/landmarks | 否 |
| GetLandmarkByNameTool | get_landmark_by_name | GET /api/landmarks/name/{name} | 否 |
| SearchLandmarksTool | search_landmarks | GET /api/landmarks/search | 否 |
| GetLandmarkByIdTool | get_landmark_by_id | GET /api/landmarks/{id} | 否 |

#### 4.2.2 房源工具 (8个)

| 工具类 | 工具名 | API路径 | 需要认证 |
|--------|--------|---------|---------|
| GetHouseByIdTool | get_house_by_id | GET /api/houses/{house_id} | 是 |
| GetHouseListingsTool | get_house_listings | GET /api/houses/listings/{house_id} | 是 |
| GetHousesByCommunityTool | get_houses_by_community | GET /api/houses/by_community | 是 |
| SearchHousesTool | search_houses | GET /api/houses/by_platform | 是 |
| GetHousesNearbyTool | get_houses_nearby | GET /api/houses/nearby | 是 |
| GetNearbyLandmarksTool | get_nearby_landmarks | GET /api/houses/nearby_landmarks | 是 |
| GetHouseStatsTool | get_house_stats | GET /api/houses/stats | 是 |
| GetLandmarkStatsTool | get_landmark_stats | GET /api/landmarks/stats | 是 |

#### 4.2.3 租房操作工具 (4个)

| 工具类 | 工具名 | API路径 | 需要认证 |
|--------|--------|---------|---------|
| RentHouseTool | rent_house | POST /api/houses/{house_id}/rent | 是 |
| TerminateRentalTool | terminate_rental | POST /api/houses/{house_id}/terminate | 是 |
| TakeOfflineTool | take_offline | POST /api/houses/{house_id}/offline | 是 |
| ResetHousesTool | reset_houses | POST /api/houses/init | 是 |

### 4.3 核心工具详解: search_houses

这是最常用的房源查询工具，支持多条件筛选：

**参数设计**:

```json
{
  "type": "object",
  "properties": {
    "district": {"type": "string", "description": "行政区，逗号分隔"},
    "area": {"type": "string", "description": "商圈，逗号分隔"},
    "min_price": {"type": "integer", "description": "最低月租金(元)"},
    "max_price": {"type": "integer", "description": "最高月租金(元)"},
    "bedrooms": {"type": "string", "description": "卧室数，逗号分隔"},
    "rental_type": {"type": "string", "description": "整租/合租"},
    "decoration": {"type": "string", "description": "装修情况"},
    "orientation": {"type": "string", "description": "朝向"},
    "elevator": {"type": "string", "description": "是否有电梯"},
    "min_area": {"type": "integer", "description": "最小面积"},
    "max_area": {"type": "integer", "description": "最大面积"},
    "max_subway_dist": {"type": "integer", "description": "最大地铁距离(米)"},
    "commute_to_xierqi_max": {"type": "integer", "description": "到西二旗通勤时间上限(分钟)"},
    "listing_platform": {"type": "string", "description": "挂牌平台"},
    "sort_by": {"type": "string", "description": "排序字段"},
    "sort_order": {"type": "string", "description": "排序方向"}
  }
}
```

---

## 5. 对话流程设计

### 5.1 完整对话流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. 接收请求                                                      │
│    - 解析请求参数 (model_ip, session_id, message, user_id)       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. 会话初始化                                                    │
│    - 获取或创建会话                                              │
│    - 首次访问时重置房源数据                                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. 构建消息列表                                                  │
│    - 添加系统提示词                                              │
│    - 添加历史对话                                                │
│    - 添加当前用户消息                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. 调用模型                                                      │
│    - 发送消息和工具定义                                          │
│    - 等待模型响应                                                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. 处理模型响应                                                  │
│    ├─ 有工具调用 → 执行步骤6                                     │
│    └─ 无工具调用 → 执行步骤7                                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
┌───────────────────────────┐  ┌───────────────────────────────────┐
│ 6. 执行工具调用            │  │ 7. 构建最终响应                   │
│    - 解析工具名和参数      │  │    - 提取回复内容                 │
│    - 执行工具              │  │    - 保存到会话历史               │
│    - 返回步骤4重新调用模型 │  │    - 返回响应                     │
└───────────────────────────┘  └───────────────────────────────────┘
```

### 5.2 工具调用流程

```
Tool Call Received
        │
        ▼
┌───────────────────┐
│ 解析工具调用参数   │
│ - tool_name       │
│ - arguments       │
│ - tool_call_id    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 获取工具实例       │
│ get_tool_by_name()│
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 执行工具          │
│ tool.execute()    │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 构建工具结果消息   │
│ {                 │
│   role: "tool",   │
│   tool_call_id,   │
│   content: result │
│ }                 │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ 添加到会话历史     │
└───────────────────┘
```

---

## 6. 会话管理设计

### 6.1 会话数据结构

```python
{
    "session_id_xxx": {
        "messages": [
            # 用户消息
            {"role": "user", "content": "查询海淀区房源"},

            # 助手消息（含工具调用）
            {"role": "assistant", "content": null, "tool_calls": [...]},

            # 工具结果
            {"role": "tool", "tool_call_id": "xxx", "content": "{...}"},

            # 最终回复
            {"role": "assistant", "content": "为您找到以下房源..."}
        ],
        "context": {
            # 预留：存储用户偏好等上下文
            "preferred_district": "海淀",
            "budget_range": [3000, 5000]
        },
        "reset_done": True
    }
}
```

### 6.2 消息历史管理

```python
# 消息添加
def add_message(session_id, role, content):
    session["messages"].append({
        "role": role,
        "content": content
    })

    # 限制历史长度
    if len(session["messages"]) > MAX_HISTORY_TURNS * 2:
        session["messages"] = session["messages"][-MAX_HISTORY_TURNS * 2:]
```

### 6.3 会话生命周期

```
创建会话 → 添加消息 → 工具调用 → 生成回复 → 添加消息 → ...
     │
     └── 首次创建时调用 reset_houses()
```

---

## 7. 日志系统设计

### 7.1 日志架构

```python
Logger (RentalAgent)
    │
    ├── ConsoleHandler (stdout)
    │   └── 输出到控制台
    │
    └── FileHandler (logs/rental_agent_YYYYMMDD.log)
        └── 输出到文件
```

### 7.2 日志级别使用规范

| 级别 | 使用场景 | 示例 |
|------|---------|------|
| DEBUG | 详细调试信息 | 请求参数、响应内容、工具参数 |
| INFO | 关键操作信息 | 请求开始/结束、工具调用、模型调用 |
| WARNING | 警告信息 | 重试、降级、非预期情况 |
| ERROR | 错误信息 | 异常、失败、超时 |

### 7.3 关键日志点

| 环节 | 日志级别 | 日志内容 |
|------|---------|---------|
| 服务启动 | INFO | 配置信息、服务地址 |
| 请求接收 | INFO | session_id, model_ip |
| 会话管理 | INFO | 新会话创建、数据重置 |
| 模型调用 | INFO | 调用开始/结束 |
| 工具执行 | INFO | 工具名、执行结果 |
| 响应返回 | INFO | 状态、耗时 |

### 7.4 日志格式

```
%(asctime)s | %(levelname)-8s | %(name)s | %(message)s

示例:
2026-03-01 14:30:15 | INFO     | RentalAgent | 收到对话请求 | session_id: test123
```

---

## 8. 接口设计

### 8.1 对话接口

**POST /api/v1/chat**

**请求模型**:

```python
class ChatRequest(BaseModel):
    model_ip: str      # 模型服务IP
    session_id: str    # 会话ID
    message: str       # 用户消息
    user_id: Optional[str] = None  # 用户工号(可选)
```

**响应模型**:

```python
class ChatResponse(BaseModel):
    session_id: str           # 会话ID
    response: str             # 回复内容
    status: str               # 状态: success/error
    tool_results: List[Any]   # 工具调用结果
    timestamp: int            # 时间戳
    duration_ms: int          # 处理耗时(毫秒)
```

### 8.2 健康检查接口

**GET /health**

**响应**:

```json
{
    "status": "healthy",
    "debug_mode": false,
    "timestamp": "2026-03-01T14:30:00"
}
```

---

## 9. 数据结构设计

### 9.1 OpenAI 工具定义格式

```json
{
    "type": "function",
    "function": {
        "name": "search_houses",
        "description": "多条件筛选房源...",
        "parameters": {
            "type": "object",
            "properties": {
                "district": {
                    "type": "string",
                    "description": "行政区"
                }
            }
        }
    }
}
```

### 9.2 模型响应格式

**带工具调用的响应**:

```json
{
    "choices": [{
        "message": {
            "role": "assistant",
            "content": null,
            "tool_calls": [{
                "id": "call_xxx",
                "function": {
                    "name": "search_houses",
                    "arguments": "{\"district\": \"海淀\"}"
                }
            }]
        }
    }]
}
```

**最终回复的响应**:

```json
{
    "choices": [{
        "message": {
            "role": "assistant",
            "content": "为您找到以下房源..."
        }
    }]
}
```

---

## 10. 错误处理设计

### 10.1 错误类型

| 错误类型 | 场景 | 处理方式 |
|---------|------|---------|
| 网络错误 | API调用失败 | 记录日志，返回错误响应 |
| 超时错误 | 请求超时 | 记录日志，返回超时提示 |
| 参数错误 | 参数验证失败 | 返回400错误 |
| 工具错误 | 工具执行失败 | 记录日志，返回错误信息 |

### 10.2 错误响应格式

```json
{
    "session_id": "xxx",
    "response": "发生错误: 具体错误信息",
    "status": "error",
    "tool_results": [],
    "timestamp": 1709251200,
    "duration_ms": 100,
    "error": {
        "message": "详细错误信息"
    }
}
```

### 10.3 异常处理策略

```python
try:
    # 执行操作
    result = await tool.execute(**arguments)
except httpx.TimeoutException:
    logger.error(f"请求超时")
    result = {"error": True, "message": "请求超时"}
except Exception as e:
    logger.error(f"执行异常: {str(e)}", exc_info=True)
    result = {"error": True, "message": str(e)}
```

---

## 11. 性能优化设计

### 11.1 异步处理

- 使用 `async/await` 实现异步处理
- 使用 `httpx.AsyncClient` 进行异步HTTP请求
- FastAPI 原生支持异步

### 11.2 会话管理优化

- 内存存储，避免数据库IO
- 限制历史消息数量，防止内存溢出
- 设置最大迭代次数，防止无限循环

### 11.3 日志优化

- 异步写入日志文件
- 按日期分割日志文件
- 支持日志级别动态调整

---

## 12. 部署设计

### 12.1 部署架构

```
┌───────────────────────────────────────────────────────────────┐
│                        生产环境部署                            │
│                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   Nginx     │───▶│   Agent     │───▶│   模型服务       │  │
│  │  (反向代理)  │    │  (FastAPI)  │    │  (model_ip:8888) │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
│                            │                                  │
│                            ▼                                  │
│                    ┌─────────────────┐                       │
│                    │    房源API       │                       │
│                    │ (7.225.29.223)  │                       │
│                    └─────────────────┘                       │
└───────────────────────────────────────────────────────────────┘
```

### 12.2 启动命令

```bash
# 生产环境
python run.py --port 8191 --log-level INFO

# 调试环境
python run.py --debug --log-level DEBUG
```

### 12.3 日志管理

```bash
# 日志目录结构
logs/
├── rental_agent_20260301.log
├── rental_agent_20260302.log
└── ...

# 日志轮转 (可选配置logrotate)
/var/log/rental_agent/*.log {
    daily
    rotate 7
    compress
    missingok
}
```

### 12.4 监控指标

| 指标 | 说明 | 获取方式 |
|------|------|---------|
| 请求数 | 总请求次数 | 日志统计 |
| 响应时间 | 平均响应时间 | duration_ms |
| 成功率 | 成功请求占比 | status统计 |
| 错误数 | 错误请求次数 | ERROR日志统计 |

---

## 附录

### A. 系统提示词

```
你是一个专业的租房助手，帮助用户找到合适的房源。

## 你的职责
1. 理解用户的租房需求（区域、价格、户型、装修、通勤等）
2. 使用工具查询和筛选房源
3. 为用户推荐最合适的房源（最多5套）
4. 协助用户完成租房相关操作

## 工具使用指南
- search_houses: 最常用的房源查询工具
- get_houses_nearby: 查询地标附近的房源
- get_house_by_id: 获取房源详情
- get_landmarks/search_landmarks: 查询地标信息
- rent_house: 租房操作
- reset_houses: 重置房源数据

## 重要规则
1. 每次查询最多返回5套房源
2. 房源查询结果必须以JSON格式返回
3. 近地铁标准：地铁距离800米以内
4. 房源查询最终结果必须是JSON格式的房源ID列表
```

### B. 配置参数速查表

| 参数 | 默认值 | 环境变量 |
|------|--------|---------|
| AGENT_HOST | 0.0.0.0 | AGENT_HOST |
| AGENT_PORT | 8191 | AGENT_PORT |
| RENTAL_API_BASE | http://7.225.29.223:8080 | RENTAL_API_BASE |
| MODEL_PORT | 8888 | MODEL_PORT |
| DEFAULT_USER_ID | z00931220 | DEFAULT_USER_ID |
| LOG_LEVEL | INFO | LOG_LEVEL |

### C. 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| V1.0 | 2026-03-01 | 初始版本 |