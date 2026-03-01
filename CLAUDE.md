# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

租房 AI Agent - 智能租房助手系统，使用 FastAPI + OpenAI Function Calling 实现。通过模型服务调用工具完成房源查询、筛选和推荐。

**网络要求**: 房源API和模型服务需要在内网环境访问。
- 房源API: `http://7.225.29.223:8080`
- 模型服务: `http://{model_ip}:8888`

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务 - 正式模式(V1接口)
python run.py

# 启动服务 - 调试模式(V2接口，无需Session-ID)
python run.py --debug --log-level DEBUG

# 指定端口
python run.py --port 8191

# 健康检查
curl http://localhost:8191/health

# 运行调试测试
python tests/debug_runner.py --sample tests/test_samples/sample_1.json --model-ip <内网模型IP>
```

## 架构要点

### 请求处理流程
```
Request → AgentService → SessionManager (获取/创建会话)
                          ↓
                     ModelService (调用模型)
                          ↓
                     Tool Execution (执行工具调用，可能多轮迭代)
                          ↓
                     Response
```

### 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| AgentService | `app/services/agent_service.py` | 核心业务逻辑，工具调用编排，支持最多10轮迭代 |
| ModelService | `app/services/model_service.py` | 模型API调用，V1/V2接口切换 |
| SessionManager | `app/utils/session_manager.py` | 会话管理，内存存储，最多20轮对话历史 |

### 工具系统

工具基类位于 `app/tools/base.py`，分为三类：
- **LandmarkTool**: 地标工具(4个)，不需要 X-User-ID
- **HouseTool**: 房源工具(8个)，需要 X-User-ID
- **RentTool**: 租房操作工具(4个)，需要 X-User-ID

添加新工具时：
1. 继承对应的基类
2. 实现 `name`, `description`, `parameters`, `execute()` 方法
3. 在 `app/tools/__init__.py` 的 `ALL_TOOLS` 列表中注册

### V1 vs V2 接口

| 模式 | API路径 | Session-ID | 使用场景 |
|------|---------|------------|---------|
| 正式 | /v1/chat/completions | 需要 | 评测时使用 |
| 调试 | /v2/chat/completions | 不需要 | 本地调试 |

通过 `--debug` 参数切换，由 `settings.DEBUG_MODE` 控制。

## 关键设计决策

1. **新会话自动重置**: 首次访问时调用 `reset_houses` 确保数据干净
2. **工具调用迭代**: AgentService.MAX_ITERATIONS = 10，防止无限循环
3. **房源查询输出格式**: 最终结果必须是JSON `{"message": "...", "houses": ["HF_1", ...]}`
4. **近地铁标准**: 地铁距离800米以内

## 日志系统

- 日志文件: `logs/rental_agent_YYYYMMDD.log`
- 格式: `时间戳 | 级别 | 模块 | 消息`
- 使用 `get_logger()` 获取全局logger实例

## 测试样例

测试样例位于 `tests/test_samples/`，格式：
```json
{
  "case_id": "sample_001",
  "case_type": "Single",  // 或 "Multi"
  "turns": [{"turn_id": 1, "message": "..."}],
  "expected_houses": ["HF_1", "HF_2"]
}
```