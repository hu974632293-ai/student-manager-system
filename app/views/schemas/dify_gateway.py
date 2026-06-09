from typing import Optional

from pydantic import BaseModel, Field


class DifyStudentQueryRequest(BaseModel):
    query: Optional[str] = Field(
        default=None,
        description="用户的原始自然语言问题，例如：查询张三的学生信息。",
    )
    student_id: Optional[str] = Field(default=None, description="学号，精确匹配。")
    student_name: Optional[str] = Field(default=None, description="学生姓名，支持模糊匹配。")
    class_id: Optional[int] = Field(default=None, description="班级主键 ID。")
    skip: int = Field(default=0, ge=0, description="跳过的记录数，用于分页。")
    limit: int = Field(default=10, ge=1, le=50, description="返回记录数，最大 50。")
