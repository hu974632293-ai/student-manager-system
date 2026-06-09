# Dify 专用后端网关

## 目标

Dify 不直接调用现有后台页面接口，而是调用 `/dify-gateway/*` 下的稳定工具接口。网关负责两件事：

- 用 `DIFY_GATEWAY_API_KEY` 校验 Dify 是否是可信调用方。
- 映射到 `DIFY_GATEWAY_USERNAME` 指定的系统用户，再复用现有 RBAC 权限和 service 数据范围过滤。

这样后续新增成绩、就业、统计等 Dify 工具时，只需要继续在网关下新增工具接口，并为每个接口绑定对应权限码。

## 环境变量

```env
DIFY_GATEWAY_API_KEY=请换成高强度随机字符串
DIFY_GATEWAY_USERNAME=admin
```

`DIFY_GATEWAY_USERNAME` 默认是 `admin`。生产环境建议创建一个专用账号，例如 `dify_service`，按需要授予最小角色或后续扩展为专用权限。

## 学生查询工具

接口：

```http
POST /dify-gateway/students/query
X-Dify-Token: <DIFY_GATEWAY_API_KEY>
Content-Type: application/json
```

也可以使用：

```http
Authorization: Bearer <DIFY_GATEWAY_API_KEY>
```

请求示例：

```json
{
  "query": "查询张三的学生信息",
  "student_name": "张三",
  "limit": 10
}
```

返回仍保持项目统一格式：

```json
{
  "code": 1,
  "msg": "Dify 学生查询成功",
  "data": {
    "query": "查询张三的学生信息",
    "filters": {
      "student_id": null,
      "student_name": "张三",
      "class_id": null
    },
    "total": 1,
    "students": []
  }
}
```

## 在 Dify 中配置

推荐把该接口作为 OpenAPI/API Tool 导入：

- Base URL：`http://宿主机地址:8088`
- Path：`/dify-gateway/students/query`
- Method：`POST`
- Header：`X-Dify-Token: <DIFY_GATEWAY_API_KEY>`

Dify 负责把用户自然语言转换为 `student_id`、`student_name`、`class_id` 等结构化参数；网关只做接口鉴权、权限复用、数据范围过滤和稳定响应。
