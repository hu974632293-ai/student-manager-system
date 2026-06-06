# JWT Refresh Token 与第一阶段 RBAC 完整化设计

## 背景

当前项目已经具备基础认证授权能力：

- `app/services/auth_service.py` 手写生成和校验 JWT access token。
- `app/controllers/auth.py` 通过 `get_current_user` 解析 `Authorization: Bearer <token>`。
- 业务路由大量使用 `require_roles(...)` 做角色门禁。
- `app/core/permissions.py` 维护固定角色、模块和权限码。
- `app/services/access_scope_service.py` 在 service 层做数据范围过滤。

本阶段目标不是推倒重做，而是在现有 MVC 分层基础上补齐 JWT 生命周期，并让 RBAC 从“只按角色判断”向“角色 + 权限码”过渡。

## 目标

1. 登录后返回短期 access token 和长期 refresh token。
2. refresh token 只保存哈希到数据库，服务端可以撤销。
3. 支持刷新 token、退出登录、修改密码后撤销旧 refresh token。
4. 保留现有固定角色和 `app/core/permissions.py` 权限矩阵，不引入动态权限表。
5. 增加 `require_permissions(...)`，新接口优先按权限码授权，旧接口可逐步迁移。
6. 所有新增或修改接口继续返回 `{code, msg, data}`。
7. 新增和修改接口的 FastAPI `summary` 使用中文。

## 非目标

- 不实现后台动态修改角色权限。
- 不新增 `roles`、`permissions`、`role_permissions` 等动态 RBAC 表。
- 不改现有公开 API 路径，除新增认证接口外。
- 不把数据范围判断移到 controller 或 dao。
- 不主动重构无关业务模块。

## 数据模型

新增 `user_refresh_tokens` 表，对应模型建议为 `app/models/refresh_token.py`。

字段建议：

- `id`: 主键。
- `user_id`: 关联 `users.id`。
- `token_hash`: refresh token 哈希，唯一索引。
- `jti`: refresh token 唯一标识，唯一索引。
- `expires_at`: 过期时间。
- `revoked_at`: 撤销时间，未撤销时为空。
- `replaced_by_jti`: 轮换后新 token 的 `jti`，可为空。
- `created_ip`: 创建时客户端 IP，可为空。
- `created_user_agent`: 创建时 User-Agent，可为空。
- `created_at`: 创建时间。

数据库只保存 refresh token 哈希，不保存明文 refresh token。

## JWT 与 Token 生命周期

access token：

- 继续使用 JWT。
- 使用 `HS256`。
- 默认有效期建议从 8 小时缩短到 30 分钟。
- payload 保留 `sub`、`uid`、`role`、`name`、`teacher_id`、`student_id`、`iat`、`exp`。
- 新增 `jti` 方便日志和问题追踪。

refresh token：

- 使用高强度随机字符串，不需要是 JWT。
- 明文只在登录或刷新接口返回给客户端一次。
- 服务端保存哈希、过期时间、撤销状态。
- 刷新时采用轮换策略：旧 refresh token 撤销，新 refresh token 入库。

配置：

- `JWT_SECRET_KEY`: 必须支持环境变量配置。
- `JWT_ACCESS_EXPIRE_MINUTES`: access token 有效期，默认 30。
- `JWT_REFRESH_EXPIRE_DAYS`: refresh token 有效期，默认 7。
- 开发环境可以保留默认密钥，但启动时应记录警告。

## 接口设计

保留：

- `POST /auth/login`: 登录，返回 `access_token`、`refresh_token`、`token_type`、用户信息。
- `GET /auth/me`: 获取当前用户信息。

新增：

- `POST /auth/refresh`: 使用 refresh token 换取新的 access token 和 refresh token。
- `POST /auth/logout`: 撤销当前 refresh token。
- `POST /auth/change-password`: 修改当前用户密码，并撤销该用户已有 refresh token。

响应格式继续统一为：

```json
{
  "code": 1,
  "msg": "success",
  "data": null
}
```

失败场景使用 `code = 0`，例如 refresh token 无效、过期、已撤销、密码错误。

## 分层设计

controller：

- `app/controllers/auth.py` 只负责路由、参数接收、依赖注入、调用 service。
- 保留 `get_current_user`。
- 增加 `require_permissions(...)`，内部读取当前用户权限码。

service：

- `app/services/auth_service.py` 负责登录、当前用户、修改密码等认证业务。
- 新增 `app/services/token_service.py` 负责 refresh token 生成、哈希、入库、撤销和轮换。
- service 返回统一响应结构，不在 dao 中写业务文案。

dao：

- 新增 `app/dao/refresh_token.py`，只做 refresh token 的 CRUD/query。
- 不抛 HTTPException。
- 不写业务规则。

model：

- 新增 refresh token ORM 模型。
- 不写查询逻辑和业务逻辑。

schema：

- 扩展 `app/views/schemas/auth.py`，增加 refresh、logout、change-password 请求结构和登录响应字段。

core：

- 可新增 `app/core/security.py` 承载密码哈希、JWT 编码解码、随机 token 生成等基础能力。
- `app/core/permissions.py` 继续作为固定角色权限矩阵来源。

## RBAC 第一阶段增强

保留：

- 固定角色：`admin`、`teacher`、`student`、`consultant`。
- 固定权限矩阵：`app/core/permissions.py`。
- service 层数据范围过滤：`AccessScopeService`。

新增：

- `require_permissions(*permissions)` 依赖。
- 当前用户输出继续包含 `permissions` 和 `modules`。
- 新增或修改接口优先使用权限码表达授权意图。

迁移原则：

- 不一次性改完所有旧接口，避免大范围风险。
- 对本次涉及的认证接口和权限相关接口先补测试。
- 后续业务改动时，逐步把 `require_roles(...)` 替换成 `require_permissions(...)`。

## 安全与错误处理

- refresh token 明文只返回给客户端，不写日志。
- 日志中继续屏蔽 `token`、`authorization`、`secret` 等敏感字段。
- refresh token 过期、撤销、找不到统一按无效 token 处理。
- 修改密码后撤销该用户所有 refresh token，要求用户重新登录。
- access token 过期仍由 `get_current_user` 返回 401，并通过全局异常处理转成统一响应格式。

## 测试计划

后端验证：

```powershell
python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p)) for p in pathlib.Path('app').rglob('*.py')]; print('AST OK')"
python -c "import app.main; print('import app.main OK')"
python -m pytest -q
```

单元测试重点：

- 登录成功返回 access token 和 refresh token。
- 密码错误返回 `code=0`。
- access token 签名错误或过期无法访问 `/auth/me`。
- refresh token 可以刷新并发生轮换。
- 旧 refresh token 轮换后不可再次使用。
- logout 后 refresh token 不可再用。
- change-password 后旧 refresh token 不可再用。
- `require_permissions(...)` 对有权限和无权限用户分别返回允许和拒绝。

## 实施顺序

1. 新增 refresh token 模型、DAO、schema 和 service。
2. 调整登录响应，写 JWT/refresh token 生命周期测试。
3. 新增 refresh、logout、change-password 接口。
4. 增加 `require_permissions(...)`，补最小权限依赖测试。
5. 运行 AST、`import app.main` 和 pytest 验证。
6. 如涉及前端登录态，再按现有 Vite 前端结构补 token 刷新和退出登录能力。

## 风险与取舍

- 手写 JWT 可以继续保留，改动最小；如果后续要提高标准化程度，可单独切换到 `PyJWT`。
- refresh token 入库会增加数据库依赖，但换来可撤销、可登出、可审计。
- 先不做动态权限表，能避免 RBAC 子系统过度膨胀；后续如果需要后台配置权限，可以在当前权限码基础上平滑迁移。
