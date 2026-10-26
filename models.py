from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from database import Base


# 아동 기본 정보 테이블
class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(50), nullable=False)
    class_name = Column(String(50), nullable=False)
    age_months = Column(Integer, nullable=False)
    gender = Column(String(1), nullable=False)

    allergies = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


# 아동별 하루 건강 기록
class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)

    child_id = Column(
        Integer,
        ForeignKey("children.id"),
        nullable=False,
    )

    record_date = Column(Date, nullable=False)

    # 하루 동안 누적되는 체온
    temp_morning = Column(Float, nullable=True)
    temp_noon = Column(Float, nullable=True)
    temp_afternoon = Column(Float, nullable=True)

    # 기존 필드 유지 (이전 API와 호환)
    symptoms = Column(Text, nullable=True)
    observation = Column(Text, nullable=True)

    # QLoRA 분석 결과 (JSON 문자열)
    ai_symptom_scores = Column(Text, nullable=True)
    ai_categories = Column(Text, nullable=True)
    ai_pattern_flags = Column(Text, nullable=True)

    # RF-D 분석 결과
    ai_care_priority = Column(Integer, nullable=True)

    # AI 분석 상태
    ai_status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    ai_analyzed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "child_id",
            "record_date",
            name="uq_child_record_date",
        ),
    )


# 시간대별 개별 관찰 기록
class HealthObservation(Base):
    __tablename__ = "health_observations"

    id = Column(Integer, primary_key=True, index=True)

    health_record_id = Column(
        Integer,
        ForeignKey("health_records.id"),
        nullable=False,
    )

    # morning / noon / afternoon
    time_slot = Column(String(20), nullable=False)

    # 실제 관찰 시간 (예: 09:30)
    observed_time = Column(String(5), nullable=False)

    temperature = Column(Float, nullable=True)

    # 교사가 직접 선택한 증상 (JSON 배열)
    selected_symptoms = Column(Text, nullable=True)

    # 교사의 자연어 기록
    note = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )