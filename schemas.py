from pydantic import BaseModel, ConfigDict, Field
from datetime import date, datetime
from typing import Literal


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


# 건강 기록 등록 요청
class HealthRecordCreate(BaseModel):
    child_id: int = Field(gt=0)
    record_date: date

    temp_morning: float | None = None
    temp_noon: float | None = None
    temp_afternoon: float | None = None

    symptoms: str | None = None
    observation: str | None = None


# 건강 기록 응답
class HealthRecordResponse(HealthRecordCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)


# 건강 기록 수정 요청
class HealthRecordUpdate(BaseModel):
    record_date: date | None = None

    temp_morning: float | None = None
    temp_noon: float | None = None
    temp_afternoon: float | None = None

    symptoms: str | None = None
    observation: str | None = None

    # 시간대별 관찰 기록 등록
    class HealthObservationCreate(BaseModel):
        child_id: int = Field(gt=0)
        record_date: date

        time_slot: Literal[
            "morning",
            "noon",
            "afternoon",
        ]

        observed_time: str = Field(
            pattern=r"^([01]\d|2[0-3]):[0-5]\d$"
        )

        temperature: float | None = Field(
            default=None,
            ge=30.0,
            le=43.0,
        )

        selected_symptoms: list[str] = Field(
            default_factory=list
        )

        note: str | None = Field(
            default=None,
            max_length=500,
        )

    # 시간대별 관찰 기록 응답
    class HealthObservationResponse(BaseModel):
        id: int
        health_record_id: int

        time_slot: str
        observed_time: str

        temperature: float | None
        selected_symptoms: list[str]
        note: str | None

        created_at: datetime

        model_config = ConfigDict(
            from_attributes=True
        )

    # AI 분석 결과
    class AIAnalysisResponse(BaseModel):
        health_record_id: int

        symptom_scores: dict[str, float]
        categories: list[str]
        pattern_flags: list[str]

        care_priority: int | None = Field(
            default=None,
            ge=0,
            le=2,
        )

        care_priority_label: str | None = None

        status: Literal[
            "pending",
            "completed",
            "failed",
        ]

    # 하루 건강 기록 + AI 결과 조회
    class DailyHealthRecordResponse(BaseModel):
        id: int
        child_id: int
        record_date: date

        temp_morning: float | None
        temp_noon: float | None
        temp_afternoon: float | None

        ai_status: str
        ai_care_priority: int | None

        model_config = ConfigDict(
            from_attributes=True
        )
