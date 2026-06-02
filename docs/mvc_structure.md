# MVC 后端结构说明

当前后端按严格 MVC 分层推进，目标调用链为：

```text
controller -> service -> dao -> model
```

## 分层职责

- `app/controllers/`：FastAPI 路由层，只负责接收请求、依赖注入、调用 service、返回响应。
- `app/services/`：业务逻辑层，负责业务校验、流程编排、异常语义、默认值处理、跨 DAO 调用和返回结构组装。
- `app/dao/`：数据库访问层，只负责 SQLAlchemy CRUD/query，不返回前端文案，不写 HTTP 异常。
- `app/models/`：SQLAlchemy ORM 模型，只定义表结构、关系、索引和约束。
- `app/views/schemas/`：Pydantic 请求/响应模型，当前保留该目录名。
- `app/core/`：数据库连接、统一响应、全局异常等基础设施。

新增 AI 对话功能也按该链路实现：`app/controllers/ai_chat.py` 只注册 `/ai/chat` 路由，`app/services/ai_chat_service.py` 负责会话流程、上下文裁剪、记忆读写编排和大模型客户端调用，`app/dao/ai_chat.py` 只做会话与消息表读写，`app/models/ai_chat.py` 只定义 ORM。

## 统一 API 返回格式

所有后端 API 统一返回：

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

- 成功：`code = 1`
- 业务失败：`code = 0`
- `msg` 为字符串提示
- `data` 为业务数据，无数据时返回 `null`

全局异常处理器会把 FastAPI `HTTPException`、请求参数校验失败、数据库异常和未捕获异常包装为 `code=0` 的固定结构。
