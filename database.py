from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 현재 프로젝트 폴더 경로
BASE_DIR = Path(__file__).resolve().parent

# SQLite 데이터베이스 파일 위치
DB_PATH = BASE_DIR / "ssukssuklog.db"

# SQLite 연결 주소
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# 데이터베이스 연결 엔진
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 데이터베이스 작업용 세션
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# 테이블 모델의 기본 클래스
Base = declarative_base()


# 데이터베이스 세션 제공
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
