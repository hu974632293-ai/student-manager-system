# 项目级 Agent 指令

本项目后续开发必须按严格后端 MVC 分层推进。除非用户明确要求，本文件规则优先于临时个人偏好。

## 工作边界

- 默认只处理后端代码：`app/`、`main.py`、`create_table.py`、`scripts/`、`tests/`、`docs/`。
- 暂时不要主动读取、分析或重构 `frontend/`，用于节省 token。
- 只有当用户点名要求前端改动，或后端 API 变更必须和前端接口对齐时，才读取 `frontend/`。
- 不改现有公开 API 路径，除非用户明确要求。
- 不删除脚本、测试、文档、需求资料等文件，除非后续确认无用并得到用户明确指令。

## MVC 分层规则

目标调用链必须是：

```text
controller -> service -> dao -> model
```

各层职责如下：

- `app/controllers/`
  - 只负责 FastAPI 路由注册、请求参数接收、依赖注入、调用 service、返回 HTTP 响应。
  - 不写业务规则。
  - 不直接调用 dao。
  - 不直接拼复杂返回结构，除非只是包装 service 返回值。

- `app/services/`
  - 承担所有业务逻辑、组合流程、业务校验、异常语义、默认值处理和跨 DAO 调用。
  - 新增或修改业务功能时，优先在 service 中落地。
  - controller 需要的数据结构组装、状态判断、错误含义转换应放在 service。

- `app/dao/`
  - 只负责 SQLAlchemy CRUD/query。
  - 可以封装分页查询、条件查询、统计查询等数据库访问能力。
  - 不写 HTTPException。
  - 不写业务判断。
  - 不返回面向前端展示的文案。
  - 不直接依赖 controller。

- `app/models/`
  - 只定义 SQLAlchemy ORM 模型、表关系、索引、约束。
  - 不写查询逻辑、业务逻辑或 HTTP 逻辑。

- `app/views/schemas/`
  - 只定义 Pydantic 请求和响应 schema。
  - 当前目录名先保持不变；后续可规划改名为 `app/schemas/`，但改名必须同步更新所有 import 和文档。

- `app/core/`
  - 只放数据库连接、配置、基础设施和通用运行时能力。

## 全项目 API 统一返回格式

后端所有接口必须统一返回固定结构体：

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

约束规则：

- 业务执行成功时：`code = 1`。
- 业务异常、处理失败、业务校验未通过时：`code = 0`。
- `code` 必须是数字。
- `msg` 必须是字符串提示文案。
- `data` 用于承载业务数据；无业务数据时必须返回 `null`，不要省略字段。
- 存量所有接口后续必须改造适配该标准。
- 新开发接口强制遵循该返回规范。
- 落地后全项目接口响应格式必须统一，禁止同一项目内混用旧格式、裸数组、裸对象或任意字段名。

## 当前重构方向

- 现有 controller 直接调用 dao 的模块，后续必须逐步改为 `controller -> service -> dao`。
- `student`、`teacher`、`classes`、`jobs`、`score`、`statistics`、`auth` 都应补齐对应 service。
- dao 中现有统计、分页、组合查询可以保留为数据查询能力。
- 业务默认值、异常处理、权限/角色规则、跨表流程、返回结构组装应迁移到 service。
- API 返回结构组装应优先放在 service 或统一响应工具中，controller 只做轻量包装。
- 新增模块时必须同时考虑 `controller + service + dao + model/schema` 的职责边界，不允许只在 controller 或 dao 中堆逻辑。

## 代码约束

- 后续不要继续把业务逻辑写进 `app/controllers/` 或 `app/dao/`。
- service 可以调用多个 dao；dao 不调用 service。
- controller 可以依赖 schema 和 service；controller 不依赖 model/dao，除非是极小的兼容性过渡且需要在改动说明中标明。
- dao 可以依赖 model 和必要 schema 类型；优先让 dao 接收普通参数或 dict，避免 dao 过度绑定 HTTP 输入模型。
- schema 不依赖 controller、service、dao。
- 保持现有 API 路径兼容，除非用户明确要求改路由。
- 所有接口响应必须遵循 `{code, msg, data}` 固定结构。
- 新增或修改功能接口时，FastAPI 路由必须设置中文 `summary`，内容应直接描述该接口功能。

## 验证要求

后端代码修改后至少执行：

```powershell
python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p)) for p in pathlib.Path('app').rglob('*.py')]; print('AST OK')"
python -c "import app.main; print('import app.main OK')"
```

如果当前环境安装了 pytest，继续执行：

```powershell
python -m pytest -q
```

如果没有 pytest，必须说明原因，并用最小手动脚本验证本次变更涉及的关键 service/dao 行为。

涉及 API 响应格式改造时，还必须检查：

- 成功接口返回 `code=1`。
- 失败或业务异常返回 `code=0`。
- 所有响应都包含 `code`、`msg`、`data` 三个字段。
- 无数据时 `data` 为 `null`。

## 文档和清理

- 结构性改动后同步更新 `README.md` 或 `docs/` 中相关说明。
- 清理 `__pycache__`、`.pyc` 等缓存文件，但不要删除用户资料、脚本、测试或文档。
- 项目当前不是必须依赖前端检查；除非用户要求，后端重构不主动读取 `frontend/`。
