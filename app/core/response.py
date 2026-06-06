from typing import Any


MESSAGE_MAP = {
    "success": "操作成功",
    "failed": "操作失败",
    "request validation failed": "请求参数校验失败",
    "database error": "数据库处理异常，请稍后重试",
    "server error": "服务异常，请稍后重试",
    "not found": "资源不存在",
    "permission denied": "当前角色无权执行该操作",
    "login success": "登录成功",
    "current user": "当前用户信息获取成功",
    "students found": "学生列表获取成功",
    "student found": "学生信息获取成功",
    "student created": "学生创建成功",
    "student updated": "学生信息更新成功",
    "student deleted": "学生删除成功",
    "student not found": "学生不存在",
    "student_id is required": "请填写学号",
    "unsupported comment style": "不支持的评语类型",
    "classes found": "班级列表获取成功",
    "class found": "班级信息获取成功",
    "class created": "班级创建成功",
    "class updated": "班级信息更新成功",
    "class deleted": "班级删除成功",
    "class not found": "班级不存在",
    "teachers found": "教师列表获取成功",
    "teacher found": "教师信息获取成功",
    "teacher created": "教师创建成功",
    "teacher updated": "教师信息更新成功",
    "teacher deleted": "教师删除成功",
    "teacher not found": "教师不存在",
    "jobs found": "就业信息获取成功",
    "job created": "就业信息创建成功",
    "job updated": "就业信息更新成功",
    "job deleted": "就业信息删除成功",
    "job record not found": "就业记录不存在",
    "scores found": "成绩列表获取成功",
    "score found": "成绩信息获取成功",
    "score created": "成绩创建成功",
    "scores created": "成绩批量创建成功",
    "score updated": "成绩信息更新成功",
    "score deleted": "成绩删除成功",
    "score not found": "成绩不存在",
    "score already exists": "该成绩记录已存在",
    "some score records already exist": "部分成绩记录已存在",
    "no update fields": "没有可更新的字段",
    "statistics found": "统计数据获取成功",
    "logs found": "日志列表获取成功",
    "question is required": "请填写问题",
    "message is required": "请填写消息内容",
    "query is required": "请填写搜索内容",
    "memory content is required": "请填写记忆内容",
    "memory created": "记忆创建成功",
    "memory deleted": "记忆删除成功",
    "memory not found": "记忆不存在",
    "session not found": "会话不存在",
    "no messages to summarize": "当前会话暂无可摘要的消息",
}

MESSAGE_PATTERNS = (
    ("does not exist", "关联数据不存在，请检查输入内容"),
    ("already exists", "记录已存在，请勿重复提交"),
    ("field ", "必填字段缺失，请补全表单"),
    ("QWEN_API_KEY or DASHSCOPE_API_KEY is required", "未配置通义千问 API Key，请先配置 QWEN_API_KEY 或 DASHSCOPE_API_KEY"),
    ("QWEN_TIMEOUT_SECONDS must be an integer", "通义千问超时时间必须是整数"),
    ("QWEN_TIMEOUT_SECONDS must be greater than 0", "通义千问超时时间必须大于 0"),
    ("Qwen request failed", "通义千问服务请求失败，请检查网络或 API Key 配置"),
    ("Qwen response", "通义千问返回内容异常，请稍后重试"),
    ("OLLAMA_TIMEOUT_SECONDS must be an integer", "Ollama 超时时间必须是整数"),
    ("OLLAMA_TIMEOUT_SECONDS must be greater than 0", "Ollama 超时时间必须大于 0"),
    ("Ollama request failed", "Ollama 本地模型服务请求失败，请确认服务已启动"),
    ("Ollama", "Ollama 本地模型返回内容异常，请稍后重试"),
    ("WEATHER_API_KEY or AMAP_API_KEY is required", "未配置天气服务 Key，请先配置 WEATHER_API_KEY 或 AMAP_API_KEY"),
    ("WEATHER_TIMEOUT_SECONDS must be an integer", "天气服务超时时间必须是整数"),
    ("WEATHER_TIMEOUT_SECONDS must be greater than 0", "天气服务超时时间必须大于 0"),
    ("weather request failed", "天气服务请求失败，请检查配置或稍后重试"),
    ("weather response", "天气服务返回内容异常，请稍后重试"),
    ("city or latitude/longitude is required", "请填写城市，或同时填写纬度和经度"),
    ("city is required", "请填写城市名称"),
    ("SMTP_PORT must be an integer", "邮件端口必须是整数"),
    ("SMTP_HOST is required", "请配置邮件服务器地址"),
    ("SMTP_SENDER or SMTP_USERNAME is required", "请配置邮件发件人或登录账号"),
    ("SMTP_USERNAME is required", "请配置邮件登录账号"),
    ("SMTP_PASSWORD is required", "请配置邮件登录密码"),
    ("email send failed", "邮件发送失败，请检查邮箱配置或稍后重试"),
    ("to_email is required", "请填写收件邮箱"),
    ("subject is required", "请填写邮件主题"),
    ("content is required", "请填写邮件正文"),
)


def _normalize_msg(msg: str | None, default: str) -> str:
    if not msg:
        return default
    if msg in MESSAGE_MAP:
        return MESSAGE_MAP[msg]
    for pattern, replacement in MESSAGE_PATTERNS:
        if pattern in msg:
            return replacement
    return msg


def success(data: Any = None, msg: str = "success") -> dict:
    return {"code": 1, "msg": _normalize_msg(msg, "操作成功"), "data": data}


def fail(msg: str = "failed", data: Any = None) -> dict:
    return {"code": 0, "msg": _normalize_msg(msg, "操作失败"), "data": data}
