from sqlalchemy import inspect, text

from database import Base, engine
import models


def migrate_database():
    # 기존 DB에 어떤 테이블과 컬럼이 있는지 확인
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # 기존 health_records 테이블에 추가할 컬럼
    new_columns = {
        "ai_symptom_scores": "TEXT",
        "ai_categories": "TEXT",
        "ai_pattern_flags": "TEXT",
        "ai_care_priority": "INTEGER",
        "ai_status": "VARCHAR(20) NOT NULL DEFAULT 'pending'",
        "ai_analyzed_at": "DATETIME",
    }

    if "health_records" in existing_tables:
        existing_columns = {
            column["name"]
            for column in inspector.get_columns("health_records")
        }

        with engine.begin() as connection:
            for column_name, column_type in new_columns.items():
                if column_name not in existing_columns:
                    connection.execute(
                        text(
                            f"ALTER TABLE health_records "
                            f"ADD COLUMN {column_name} {column_type}"
                        )
                    )
                    print(f"[추가 완료] {column_name}")
                else:
                    print(f"[이미 존재] {column_name}")

    # 새 health_observations 테이블 생성
    Base.metadata.create_all(bind=engine)

    print("\n데이터베이스 업데이트 완료!")


if __name__ == "__main__":
    migrate_database()