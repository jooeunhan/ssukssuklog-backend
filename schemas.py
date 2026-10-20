from pydantic import BaseModel, ConfigDict, Field


# 아동 등록 시 전달받는 데이터 형식
class ChildCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    class_name: str = Field(min_length=1, max_length=50)
    age_months: int = Field(ge=0, le=216)
    gender: str = Field(pattern="^(M|F)$")
    allergies: str | None = None
    notes: str | None = None


# 아동 등록 후 반환할 데이터 형식
class ChildResponse(ChildCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


# 아동 정보 수정 시 사용하는 데이터 형식
class ChildUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    class_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    age_months: int | None = Field(
        default=None,
        ge=0,
        le=216
    )

    gender: str | None = Field(
        default=None,
        pattern="^(M|F)$"
    )

    allergies: str | None = None

    notes: str | None = None
