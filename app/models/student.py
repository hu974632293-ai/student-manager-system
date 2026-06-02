from sqlalchemy import Boolean, Column, Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), unique=True, index=True, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    name = Column(String(50), nullable=False, index=True)
    native_place = Column(String(100))
    graduate_school = Column(String(100))
    major = Column(String(100))
    enrollment_date = Column(Date)
    graduation_date = Column(Date)
    education = Column(String(20))
    consultant_id = Column(Integer, ForeignKey("teachers.id"))
    age = Column(Integer)
    gender = Column(String(10))
    is_deleted = Column(Boolean, default=False)

    class_info = relationship("Class", back_populates="students")
    consultant = relationship("Teacher", foreign_keys=[consultant_id])
    job_info = relationship("StudentJob", back_populates="student", uselist=False)
    scores = relationship("StudentScore", back_populates="student")

    __table_args__ = (
        Index("ix_student_age", "age"),
        Index("ix_student_gender", "gender"),
        Index("ix_student_class_id", "class_id"),
    )
