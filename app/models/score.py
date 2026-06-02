from sqlalchemy import Column, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class StudentScore(Base):
    __tablename__ = "student_scores"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(20), ForeignKey("students.student_id"), nullable=False)
    exam_round = Column(Integer, nullable=False)
    score = Column(Float)
    remark = Column(String(255))

    student = relationship("Student", back_populates="scores")

    __table_args__ = (
        UniqueConstraint("student_id", "exam_round", name="uq_student_scores_student_exam"),
    )
