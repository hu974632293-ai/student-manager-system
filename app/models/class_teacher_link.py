from sqlalchemy import Column, ForeignKey, Integer, Table

from app.core.database import Base


class_teacher_link = Table(
    "class_teacher_link",
    Base.metadata,
    Column("class_id", Integer, ForeignKey("classes.id"), primary_key=True),
    Column("teacher_id", Integer, ForeignKey("teachers.id"), primary_key=True),
)
