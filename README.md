# 租房 AI Agent 使用文档

## 目录

1. [项目概述](#1-项目概述)
2. [环境要求](#2-环境要求)
3. [安装部署](#3-安装部署)
4. [配置说明](#4-配置说明)
5. [启动服务](#5-启动服务)
6. [API接口文档](#6-api接口文档)
7. [工具列表](#7-工具列表)
8. [日志说明](#8-日志说明)
9. [本地调试](#9-本地调试)
10. [常见问题](#10-常见问题)

---

## 1. 项目概述

### 1.1 项目背景

租房 AI Agent 是一个智能租房助手系统，能够：
- 精准识别用户租房多元需求
- 自动完成房源信息搜集、筛选、核验
- 多维度分析候选房源
- 输出最多5套高匹配度候选房源

### 1.2 技术架构

```
判题系统请求 -> Agent API (FastAPI:8191)
                    |
                    v
              意图识别 + 工具调用
                    |
                    v
              模型服务 (model_ip:8888) <-> 房源API (7.225.29.223:8080)
                    |
                    v
              结果处理 -> 返回响应
```

### 1.3 项目结构

```
RentalAgent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置文件
│   ├── routers/
│   │   ├── __init__.py
│   │   └── chat.py             # 对话接口路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent_service.py    # Agent核心逻辑
│   │   └── model_service.py    # 模型调用服务
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py             # 工具基类
│   │   ├── landmark_tools.py   # 地标工具(4个)
│   │   ├── house_tools.py      # 房源工具(8个)
│   │   └── rent_tools.py       # 租房操作工具(4个)
│   └── utils/
│       ├── __init__.py
│       ├── session_manager.py  # 会话管理
│       └── logger.py           # 日志模块
├── tests/
│   ├── __init__.py
│   ├── debug_runner.py         # 调试运行器
│   └── test_samples/           # 测试样例
│       ├── sample_1.json
│       └── sample_2.json
├── logs/                       # 日志目录(自动创建)
├── requirements.txt
├── run.py                      # 启动脚本
└── README.md
```

---

## 2. 环境要求

### 2.1 系统要求

- **操作系统**: Linux / Windows / macOS
- **Python版本**: 3.9+
- **网络要求**: 需要能访问内网服务
  - 房源API: `http://7.225.29.223:8080`
  - 模型服务: `http://{model_ip}:8888`

### 2.2 依赖包

```
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0
pydantic>=2.0.0
```

---

## 3. 安装部署

### 3.1 安装依赖

```bash
cd RentalAgent
pip install -r requirements.txt
```

### 3.2 验证安装

```bash
python -c "from app.config import settings; print(f'服务端口: {settings.AGENT_PORT}')"
```

---

## 4. 配置说明

### 4.1 配置文件

配置文件位于 `app/config.py`，主要配置项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| AGENT_HOST | 0.0.0.0 | 服务绑定地址 |
| AGENT_PORT | 8191 | 服务端口 |
| RENTAL_API_BASE | http://7.225.29.223:8080 | 房源API地址 |
| MODEL_PORT | 8888 | 模型服务端口 |
| DEFAULT_USER_ID | xxxxxxxx | 默认用户工号 |
| MAX_HISTORY_TURNS | 20 | 最大对话轮次 |
| LOG_LEVEL | INFO | 日志级别 |
| LOG_DIR | logs | 日志目录 |

### 4.2 修改配置

**方式1：直接修改 config.py**

```python
# app/config.py
DEFAULT_USER_ID: str = "你的工号"
AGENT_PORT: int = 8191
```

**方式2：通过请求参数覆盖**

```json
{
  "model_ip": "192.168.1.100",
  "session_id": "test123",
  "message": "查询房源",
  "user_id": "你的工号"  // 覆盖默认工号
}
```

---

## 5. 启动服务

### 5.1 启动命令

```bash
# 正式模式（V1接口，需要Session-ID）
python run.py

# 调试模式（V2接口，无需Session-ID）
python run.py --debug

# 指定端口
python run.py --port 8080

# 指定日志级别
python run.py --log-level DEBUG

# 组合参数
python run.py --debug --port 8191 --log-level DEBUG
```

### 5.2 命令行参数

| 参数 | 说明 |
|------|------|
| --debug | 启用调试模式，使用V2接口 |
| --host | 服务绑定地址 |
| --port | 服务端口 |
| --log-level | 日志级别 (DEBUG/INFO/WARNING/ERROR) |

### 5.3 启动成功输出

```
============================================================
租房 AI Agent 服务启动中...
============================================================
服务地址: http://0.0.0.0:8191
日志级别: INFO
日志文件: logs/rental_agent_20260301.log
房源API: http://7.225.29.223:8080
============================================================
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8191
```

### 5.4 健康检查

```bash
curl http://localhost:8191/health
```

响应：
```json
{
  "status": "healthy",
  "debug_mode": false,
  "timestamp": "2026-03-01T14:30:00"
}
```

---

## 6. API接口文档

### 6.1 对话接口

**POST /api/v1/chat**

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model_ip | string | 是 | 模型服务IP地址 |
| session_id | string | 是 | 会话ID，用于多轮对话 |
| message | string | 是 | 用户消息 |
| user_id | string | 否 | 用户工号，不传则使用默认值 |

**请求示例：**

```bash
curl -X POST http://localhost:8191/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model_ip": "192.168.1.100",
    "session_id": "session_001",
    "message": "查询海淀区的两居室房源"
  }'
```

**响应参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| session_id | string | 会话ID |
| response | string | Agent回复内容 |
| status | string | 状态 (success/error) |
| tool_results | array | 工具调用结果 |
| timestamp | integer | 时间戳 |
| duration_ms | integer | 处理耗时(毫秒) |

**响应示例：**

```json
{
  "session_id": "session_001",
  "response": "{\"message\": \"为您找到以下房源\", \"houses\": [\"HF_4\", \"HF_6\", \"HF_277\"]}",
  "status": "success",
  "tool_results": [],
  "timestamp": 1709251200,
  "duration_ms": 2500
}
```

### 6.2 健康检查接口

**GET /health**

```bash
curl http://localhost:8191/health
```

---

## 7. 工具列表

### 7.1 地标工具 (无需 X-User-ID)

| 工具名 | 功能 | API路径 |
|--------|------|---------|
| get_landmarks | 获取地标列表，支持类别/区域筛选 | GET /api/landmarks |
| get_landmark_by_name | 按名称精确查询地标 | GET /api/landmarks/name/{name} |
| search_landmarks | 关键词模糊搜索地标 | GET /api/landmarks/search |
| get_landmark_by_id | 按ID查询地标详情 | GET /api/landmarks/{id} |

### 7.2 房源工具 (需要 X-User-ID)

| 工具名 | 功能 | API路径 |
|--------|------|---------|
| get_house_by_id | 根据ID获取房源详情 | GET /api/houses/{house_id} |
| get_house_listings | 获取各平台挂牌记录 | GET /api/houses/listings/{house_id} |
| get_houses_by_community | 按小区名查询房源 | GET /api/houses/by_community |
| search_houses | 多条件筛选房源（核心工具） | GET /api/houses/by_platform |
| get_houses_nearby | 查询地标附近房源 | GET /api/houses/nearby |
| get_nearby_landmarks | 查询小区周边地标 | GET /api/houses/nearby_landmarks |
| get_house_stats | 获取房源统计信息 | GET /api/houses/stats |
| get_landmark_stats | 获取地标统计信息 | GET /api/landmarks/stats |

### 7.3 租房操作工具 (需要 X-User-ID)

| 工具名 | 功能 | API路径 |
|--------|------|---------|
| rent_house | 租房 | POST /api/houses/{house_id}/rent |
| terminate_rental | 退租 | POST /api/houses/{house_id}/terminate |
| take_offline | 下架 | POST /api/houses/{house_id}/offline |
| reset_houses | 重置房源数据 | POST /api/houses/init |

### 7.4 核心工具详解：search_houses

这是最常用的房源查询工具，支持以下筛选条件：

| 参数 | 类型 | 说明 |
|------|------|------|
| district | string | 行政区，逗号分隔 (如: 海淀,朝阳) |
| area | string | 商圈，逗号分隔 |
| min_price | integer | 最低月租金(元) |
| max_price | integer | 最高月租金(元) |
| bedrooms | string | 卧室数，逗号分隔 (如: 1,2) |
| rental_type | string | 整租/合租 |
| decoration | string | 装修: 精装/简装/豪华/毛坯/空房 |
| orientation | string | 朝向: 朝南/朝北/朝东/朝西/南北/东西 |
| elevator | string | 是否有电梯: true/false |
| min_area | integer | 最小面积(平米) |
| max_area | integer | 最大面积(平米) |
| max_subway_dist | integer | 最大地铁距离(米)，近地铁建议800 |
| commute_to_xierqi_max | integer | 到西二旗通勤时间上限(分钟) |
| listing_platform | string | 平台: 链家/安居客/58同城 |
| sort_by | string | 排序字段: price/area/subway |
| sort_order | string | 排序方向: asc/desc |

---

## 8. 日志说明

### 8.1 日志配置

| 配置 | 默认值 | 说明 |
|------|--------|------|
| 日志级别 | INFO | DEBUG/INFO/WARNING/ERROR |
| 日志目录 | logs/ | 自动创建 |
| 日志文件 | rental_agent_YYYYMMDD.log | 按日期分割 |

### 8.2 日志格式

```
时间戳 | 级别 | 模块 | 消息
2026-03-01 14:30:15 | INFO | RentalAgent | 收到对话请求 | session_id: test123
```

### 8.3 日志级别说明

| 级别 | 说明 | 示例 |
|------|------|------|
| DEBUG | 详细调试信息 | 请求参数、响应内容 |
| INFO | 关键操作信息 | 请求开始/结束、工具调用 |
| WARNING | 警告信息 | 重试、降级 |
| ERROR | 错误信息 | 异常、失败 |

### 8.4 日志示例

```
2026-03-01 14:30:15 | INFO     | RentalAgent | ============================================================
2026-03-01 14:30:15 | INFO     | RentalAgent | 租房 AI Agent 服务启动中...
2026-03-01 14:30:15 | INFO     | RentalAgent | 服务地址: http://0.0.0.0:8191
2026-03-01 14:30:20 | INFO     | RentalAgent | 请求开始: POST /api/v1/chat
2026-03-01 14:30:20 | INFO     | RentalAgent | 收到对话请求 | session_id: test123 | model_ip: 192.168.1.100
2026-03-01 14:30:20 | INFO     | RentalAgent | 开始处理消息 | session_id: test123
2026-03-01 14:30:20 | INFO     | RentalAgent | 新会话，重置房源数据 | session_id: test123
2026-03-01 14:30:20 | INFO     | RentalAgent | 调用模型服务 | model_ip: 192.168.1.100
2026-03-01 14:30:21 | INFO     | RentalAgent | 模型请求工具调用 | 迭代: 1 | 工具数: 1
2026-03-01 14:30:21 | INFO     | RentalAgent | 执行工具: search_houses
2026-03-01 14:30:21 | DEBUG    | RentalAgent | 工具参数: {"district": "海淀", "bedrooms": "2"}
2026-03-01 14:30:21 | INFO     | RentalAgent | 工具执行成功: search_houses
2026-03-01 14:30:22 | INFO     | RentalAgent | 模型返回最终回复 | 内容长度: 256
2026-03-01 14:30:22 | INFO     | RentalAgent | 请求处理完成 | 耗时: 2345ms
2026-03-01 14:30:22 | INFO     | RentalAgent | 请求完成: POST /api/v1/chat | 状态码: 200 | 耗时: 2350ms
```

---

## 9. 本地调试

### 9.1 调试模式

调试模式使用 V2 接口，不需要 Session-ID：

```bash
python run.py --debug --log-level DEBUG
```

### 9.2 测试样例

测试样例位于 `tests/test_samples/` 目录：

**单轮对话样例 (sample_1.json):**
```json
{
  "case_id": "sample_001",
  "case_type": "Single",
  "description": "查询海淀区两居室房源",
  "turns": [
    {
      "turn_id": 1,
      "message": "查询海淀区的两居室房源"
    }
  ],
  "expected_houses": ["HF_4", "HF_6", "HF_277"]
}
```

**多轮对话样例 (sample_2.json):**
```json
{
  "case_id": "sample_002",
  "case_type": "Multi",
  "description": "多轮筛选房源",
  "turns": [
    {
      "turn_id": 1,
      "message": "查询海淀区的房源"
    },
    {
      "turn_id": 2,
      "message": "只要两居室的"
    },
    {
      "turn_id": 3,
      "message": "预算5000以内"
    }
  ],
  "expected_houses": ["HF_4", "HF_6"]
}
```

### 9.3 调试运行器

```bash
# 运行单个样例
python tests/debug_runner.py --sample tests/test_samples/sample_1.json --model-ip 192.168.1.100

# 运行所有样例
python tests/debug_runner.py --all --model-ip 192.168.1.100

# 指定Agent服务地址
python tests/debug_runner.py --all --model-ip 192.168.1.100 --agent-url http://localhost:8191
```

### 9.4 调试输出示例

```
=== 调试运行 ===
样例: sample_001
类型: Single
描述: 查询海淀区两居室房源
============================================================

--- 第1轮 ---
用户: 查询海淀区的两居室房源
Agent: 为您找到以下房源...
耗时: 2345ms

============================================================
=== 结果对比 ===
预期: ["HF_4", "HF_6", "HF_277"]
实际: ["HF_4", "HF_6", "HF_277"]
匹配率: 100.0% (3/3)
```

---

## 10. 常见问题

### Q1: 服务启动失败

**现象：** 启动时报错 `Address already in use`

**解决：** 端口被占用，更换端口
```bash
python run.py --port 8192
```

### Q2: 模型调用超时

**现象：** 日志显示 `模型调用超时`

**解决：**
1. 检查 model_ip 是否正确
2. 检查网络是否可访问模型服务
3. 增加超时时间（修改 model_service.py 中的 timeout 参数）

### Q3: 房源API调用失败

**现象：** 工具执行返回错误

**解决：**
1. 检查是否在内网环境
2. 检查 X-User-ID 是否正确
3. 查看详细日志定位问题

### Q4: 多轮对话上下文丢失

**现象：** 后续对话不记得之前的内容

**解决：** 确保使用相同的 session_id

### Q5: 如何查看详细日志

**解决：**
```bash
# 启动时设置DEBUG级别
python run.py --log-level DEBUG

# 或查看日志文件
tail -f logs/rental_agent_20260301.log
```

---

## 附录：完整请求示例

### 示例1：查询海淀区两居室房源

```bash
curl -X POST http://localhost:8191/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model_ip": "192.168.1.100",
    "session_id": "demo_001",
    "message": "查询海淀区的两居室房源，预算5000以内"
  }'
```

### 示例2：查询西二旗附近房源

```bash
curl -X POST http://localhost:8191/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model_ip": "192.168.1.100",
    "session_id": "demo_002",
    "message": "我想在西二旗地铁站附近租房，近地铁的"
  }'
```

### 示例3：多轮对话

```bash
# 第一轮
curl -X POST http://localhost:8191/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model_ip": "192.168.1.100",
    "session_id": "demo_003",
    "message": "查询海淀区的房源"
  }'

# 第二轮（使用相同session_id）
curl -X POST http://localhost:8191/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model_ip": "192.168.1.100",
    "session_id": "demo_003",
    "message": "只要两居室的"
  }'

# 第三轮
curl -X POST http://localhost:8191/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model_ip": "192.168.1.100",
    "session_id": "demo_003",
    "message": "预算5000以内"
  }'
```

---

## 联系方式

如有问题，请联系项目维护人员。
