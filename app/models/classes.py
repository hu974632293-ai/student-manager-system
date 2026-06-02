from sqlalchemy import Boolean, Column, Date, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from .class_teacher_link import class_teacher_link


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(String(20), unique=True, index=True, nullable=False)
    start_date = Column(Date)
    head_teacher = Column(String(50))
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False)

    students = relationship("Student", back_populates="class_info")
    teachers = relationship("Teacher", secondary=class_teacher_link, back_populates="classes")
