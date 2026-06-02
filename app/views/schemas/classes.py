from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.views.schemas.teacher import TeacherQuery


class ClassBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ClassQuery(ClassBase):
    id: int
    class_id: str
    start_date: Optional[date] = None
    head_teacher: Optional[str] = None
    description: Optional[str] = None
    is_deleted: bool = False
    teachers: List[TeacherQuery] = []


class ClassCreate(ClassBase):
    class_id: str
    start_date: Optional[date] = None
    head_teacher: Optional[str] = None
    description: Optional[str] = None
    teacher_ids: List[int] = []


class ClassUpdate(ClassBase):
    id: int
    class_id: Optional[str] = None
    start_date: Optional[date] = None
    head_teacher: Optional[str] = None
    description: Optional[str] = None
    teacher_ids: Optional[List[int]] = None


class ClassPageResponse(ClassBase):
    items: List[ClassQuery]
    total: int
    page: int
    size: int
