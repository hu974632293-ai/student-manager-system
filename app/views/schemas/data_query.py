from pydantic import BaseModel, Field


class DataQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=100, ge=1, le=100)
    show_sql: bool = True


class DataQueryResponse(BaseModel):
    question: str
    sql: str
    columns: list[str]
    rows: list[dict]
    row_count: int
    summary: str
