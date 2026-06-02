from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StatisticsBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StudentOver30(StatisticsBase):
    student_id: str
    name: str
    gender: Optional[str] = None
    age: int
    native_place: Optional[str] = None
    graduate_school: Optional[str] = None
    major: Optional[str] = None
    education: Optional[str] = None
    enrollment_date: Optional[date] = None
    graduation_date: Optional[date] = None
    class_id: Optional[int] = None
    consultant_id: Optional[int] = None


class ClassGenderCount(StatisticsBase):
    class_id: str
    total_count: int
    male_count: int
    female_count: int


class StudentScoreAbove80(StatisticsBase):
    student_id: str
    name: str
    exam_round: int
    score: float


class StudentFailedScore(StatisticsBase):
    name: str
    class_id: str
    exam_round: int
    score: float


class ExamClassAverageScore(StatisticsBase):
    exam_round: int
    class_id: str
    average_score: float


class TopSalaryStudent(StatisticsBase):
    name: Optional[str] = None
    class_name: Optional[str] = None
    employment_date: Optional[date] = None
    company_name: Optional[str] = None
    salary: Optional[float] = None


class StudentEmploymentDuration(StatisticsBase):
    student_id: str
    name: Optional[str] = None
    class_name: Optional[str] = None
    job_open_date: date
    offer_date: Optional[date] = None
    duration_days: Optional[int] = None


class ClassAverageEmploymentDuration(StatisticsBase):
    class_name: str
    average_duration_days: Optional[float] = None
