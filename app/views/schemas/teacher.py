from typing import Optional

from pydantic import BaseModel, ConfigDict


class TeacherBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TeacherQuery(TeacherBase):
    id: int
    teacher_number: str
    name: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    subject: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False


class TeacherCreate(TeacherBase):
    teacher_number: str
    name: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    subject: Optional[str] = None
    is_active: bool = True


class TeacherUpdate(TeacherBase):
    id: int
    teacher_number: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    subject: Optional[str] = None
    is_active: Optional[bool] = None
