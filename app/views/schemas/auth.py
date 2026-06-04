from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    role: str
    teacher_id: int | None = None
    student_id: str | None = None
    permissions: list[str] = Field(default_factory=list)
    modules: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
