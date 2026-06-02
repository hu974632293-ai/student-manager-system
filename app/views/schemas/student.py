from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    student_id: str = Field(...)
    class_id: int = Field(...)
    name: str = Field(...)
    native_place: Optional[str] = None
    graduate_school: Optional[str] = None
    major: Optional[str] = None
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    education: Optional[str] = None
    consultant_id: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    is_deleted: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class StudentCommentRequest(BaseModel):
    student_id: str = Field(...)
    style: Optional[str] = "正式"
    extra_notes: Optional[str] = None
