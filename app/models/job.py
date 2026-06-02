from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class StudentJob(Base):
    __tablename__ = "student_jobs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), ForeignKey("students.student_id"), nullable=False)
    name = Column(String(50))
    class_name = Column(String(50))
    job_open_date = Column(Date)
    offer_date = Column(Date)
    company_name = Column(String(100))
    salary = Column(Float)
    position = Column(String(50))
    is_deleted = Column(Boolean, default=False)

    student = relationship("Student", back_populates="job_info")
