from sqlalchemy import Column, Integer, String, Text, Float, Date, ForeignKey

from database import Base


# 아동 기본 정보 테이블
class Child(Base):
    __tablename__ = "children"

    # 아동 고유 번호
    id = Column(Integer, primary_key=True, index=True)

    # 아동 이름
    name = Column(String(50), nullable=False)

    # 소속 반
    class_name = Column(String(50), nullable=False)

    # 개월 수 나이
    age_months = Column(Integer, nullable=False)

    # 성별 (M / F)
    gender = Column(String(1), nullable=False)

    # 알레르기 정보
    allergies = Column(Text, nullable=True)

    # 기타 특이사항
    notes = Column(Text, nullable=True)


class HealthRecord(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)

    # 아동 정보와 연결
    child_id = Column(
        Integer,
        ForeignKey("children.id"),
        nullable=False
    )

    # 기록 날짜
    record_date = Column(Date, nullable=False)

    # 시간대별 체온
    temp_morning = Column(Float, nullable=True)
    temp_noon = Column(Float, nullable=True)
    temp_afternoon = Column(Float, nullable=True)

    # 증상 및 관찰 내용
    symptoms = Column(Text, nullable=True)
    observation = Column(Text, nullable=True)
