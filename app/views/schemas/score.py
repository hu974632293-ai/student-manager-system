from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScoreBase(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=20)
    exam_round: int = Field(..., ge=1)
    score: Optional[float] = Field(None, ge=0, le=100)
    remark: Optional[str] = Field(None, max_length=255)

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, value: str):
        if not value.strip():
            raise ValueError("student_id cannot be empty")
        return value.strip()

    model_config = ConfigDict(from_attributes=True)


class ScoreCreate(ScoreBase):
    pass


class ScoreUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=100)
    remark: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(from_attributes=True)


class ScoreResponse(ScoreBase):
    id: int
    student_name: str

    model_config = ConfigDict(from_attributes=True)


class ScoreQueryCombined(BaseModel):
    student_id: Optional[str] = Field(None, min_length=1, max_length=20)
    exam_round: Optional[int] = Field(None, ge=1)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class ScoreQueryByRange(BaseModel):
    min_score: float = Field(0, ge=0, le=100)
    max_score: float = Field(100, ge=0, le=100)
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)

    @model_validator(mode="after")
    def validate_range(self):
        if self.max_score < self.min_score:
            raise ValueError("max_score must be greater than or equal to min_score")
        return self


class ScoreListResponse(BaseModel):
    total: int
    items: List[ScoreResponse]
