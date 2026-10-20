from sqlalchemy import Column, Integer, String, Text

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
