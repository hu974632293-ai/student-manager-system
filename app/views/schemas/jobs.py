from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class StudentJobCreate(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=50)
    class_name: str = Field(..., min_length=1, max_length=50)
    job_open_date: Optional[date] = None
    offer_date: Optional[date] = None
    company_name: Optional[str] = Field(None, max_length=100)
    salary: float = Field(..., gt=0)
    position: Optional[str] = Field(None, max_length=50)
