from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base
from .class_teacher_link import class_teacher_link


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    teacher_number = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    gender = Column(String(10))
    phone = Column(String(20))
    email = Column(String(100))
    subject = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    classes = relationship("Class", secondary=class_teacher_link, back_populates="teachers")
