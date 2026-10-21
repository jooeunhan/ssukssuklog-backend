
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text

from database import Base, engine, get_db
import models
from sqlalchemy.orm import Session
from schemas import (
    ChildCreate,
    ChildResponse,
    ChildUpdate,
    HealthRecordCreate,
    HealthRecordResponse,
    HealthRecordUpdate
)

# 서버 시작 시 데이터베이스 테이블 생성
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield



app = FastAPI(
    title="쑥쑥로그 API",
    description="어린이집 교사를 위한 아동 건강 기록 관리 시스템",
    version="0.1.1",
    lifespan=lifespan
)



# 서버 실행 확인
@app.get(
    "/",
    tags=["Server"],
    summary="서버 실행 확인",
    description="서버가 실행됐는지 확인합니다."
)
def home():
    return {
        "message": "SsukSsukLog Backend Running!"
    }


# 데이터베이스 연결 확인
@app.get(
    "/db-test",
    tags=["Database"],
    summary="데이터베이스 연결 확인",
    description="데이터베이스가 연결됐는지 확인합니다."
)
def db_test():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT 1")
        )

        value = result.scalar()

    return {
        "database": "SQLite",
        "status": "connected",
        "test_result": value
    }


# children 테이블 생성 확인
@app.get(
    "/table-test",
    tags=["Children"],
    summary="테이블 생성 확인",
    description="아동 테이블이 생성됐는지 확인합니다."
)
def table_test():
    with engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='children'"
            )
        )

        table_name = result.scalar()

    return {
        "table": table_name,
        "status": "created" if table_name else "not found"
    }


# 아동 등록 API
@app.post(
    "/children",
    tags=["Children"],
    summary="아동 등록",
    description="아동의 정보를 등록합니다.",
    response_model=ChildResponse,
    status_code=201
)
def create_child(
    child: ChildCreate,
    db: Session = Depends(get_db)
):
    # 요청받은 데이터를 DB 모델로 변환
    new_child = models.Child(
        **child.model_dump()
    )

    # 데이터베이스에 추가
    db.add(new_child)

    # 실제 DB에 저장
    db.commit()

    # 저장된 데이터 다시 불러오기
    db.refresh(new_child)

    # 등록 결과 반환
    return new_child


# 아동 전체 목록 조회 API
@app.get(
    "/children",
    tags=["Children"],
    summary="전체 아동 목록 조회",
    description="등록된 모든 아동의 정보를 조회합니다.",
    response_model=list[ChildResponse]
)
def get_children(db: Session = Depends(get_db)):

    # children 테이블의 모든 아동 조회
    children = db.query(models.Child).all()

    # 조회된 아동 목록 반환
    return children


# 특정 아동 상세 조회 API
@app.get(
    "/children/{child_id}",
    tags=["Children"],
    summary="특정 아동 상세 조회",
    description="특정 아동의 정보를 조회합니다.",
    response_model=ChildResponse
)
def get_child(
    child_id: int,
    db: Session = Depends(get_db)
):

    # ID에 해당하는 아동 조회
    child = db.query(models.Child).filter(
        models.Child.id == child_id
    ).first()

    # 아동이 존재하지 않는 경우
    if child is None:
        raise HTTPException(
            status_code=404,
            detail="해당 아동을 찾을 수 없습니다."
        )

    # 조회된 아동 정보 반환
    return child

@app.patch (
    "/children/{child_id}",
    tags=["Children"],
    summary="아동 정보 수정",
    description="특정 아동의 정보를 수정합니다.",
    response_model=ChildResponse
)
def update_child(
        child_id: int,
        child_data: ChildUpdate,
        db: Session = Depends(get_db)
):

    child = db.query(models.Child).filter(
        models.Child.id == child_id
    ).first()

    if child is None:
        raise HTTPException(
            status_code=404,
            detail="해당 아동을 찾을 수 없습니다."
        )

    updated_data = child_data.model_dump(
        exclude_unset=True
    )

    for key, value in updated_data.items():
        setattr(child, key, value)

    db.commit()

    db.refresh(child)

    return child


# 특정 아동 정보 삭제 API
@app.delete(
    "/children/{child_id}",
    tags=["Children"],
    summary="특정 아동 정보 삭제",
    description="특정 아동의 정보를 삭제합니다."
)
def delete_child(
    child_id: int,
    db: Session = Depends(get_db)
):

    # 삭제할 아동 조회
    child = db.query(models.Child).filter(
        models.Child.id == child_id
    ).first()

    # 존재하지 않는 아동이면 404 반환
    if child is None:
        raise HTTPException(
            status_code=404,
            detail="해당 아동을 찾을 수 없습니다."
        )

    # 데이터베이스에서 아동 삭제
    db.delete(child)

    # 실제 SQLite에 삭제 반영
    db.commit()

    return {
        "message": "아동 정보가 삭제되었습니다.",
        "deleted_child_id": child_id
    }

@app.get(
    "/health-table-test",
    tags=["Health"],
    summary="테이블 생성 확인",
    description="건강 정보 테이블이 생성되었는지 확인합니다."
)
def health_table_test():
    with engine.connect() as connection:
        result = connection.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' "
                "AND name='health_records'"
            )
        ).scalar()

    return {
        "table": result,
        "status": "created" if result else "not found"
    }


# 건강 기록 등록 API
@app.post(
    "/records",
    tags=["Health"],
    summary="건강 기록 등록",
    description="그날의 건강 기록을 등록합니다.",
    response_model=HealthRecordResponse,
    status_code=201
)
def create_health_record(
    record: HealthRecordCreate,
    db: Session = Depends(get_db)
):

    # 1. 아동이 실제로 존재하는지 확인
    child = db.query(models.Child).filter(
        models.Child.id == record.child_id
    ).first()

    if child is None:
        raise HTTPException(
            status_code=404,
            detail="해당 아동을 찾을 수 없습니다."
        )

    # 2. 새로운 건강 기록 생성
    new_record = models.HealthRecord(
        **record.model_dump()
    )

    # 3. 데이터베이스에 저장
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    # 4. 저장된 기록 반환
    return new_record


# 전체 건강 기록 조회 API
@app.get(
    "/records",
    tags=["Health"],
    summary="전체 건강 기록 조회",
    description="전체 아동의 기록된 전체 건강 기록을 조회합니다.",
    response_model=list[HealthRecordResponse]
)
def get_health_records(
    db: Session = Depends(get_db)
):
    records = db.query(models.HealthRecord).all()

    return records


# 특정 아동의 건강 기록 조회 API
@app.get(
    "/children/{child_id}/records",
    tags=["Health"],
    summary="특정 아동 건강 기록 조회",
    description="특정 아동의 건강 기록을 조회합니다.",
    response_model=list[HealthRecordResponse]
)
def get_child_health_records(
    child_id: int,
    db: Session = Depends(get_db)
):

    # 아동이 실제로 존재하는지 확인
    child = db.query(models.Child).filter(
        models.Child.id == child_id
    ).first()

    if child is None:
        raise HTTPException(
            status_code=404,
            detail="해당 아동을 찾을 수 없습니다."
        )

    # 해당 아동의 건강 기록만 조회
    records = db.query(models.HealthRecord).filter(
        models.HealthRecord.child_id == child_id
    ).order_by(
        models.HealthRecord.record_date.desc()
    ).all()

    return records


# 건강 기록 수정 API
@app.patch(
    "/records/{record_id}",
    tags=["Health"],
    summary="건강 기록 수정",
    description="등록된 건강 기록을 수정합니다.",
    response_model=HealthRecordResponse
)
def update_health_record(
    record_id: int,
    record_data: HealthRecordUpdate,
    db: Session = Depends(get_db)
):
    # 1. 수정할 건강 기록 조회
    record = db.query(models.HealthRecord).filter(
        models.HealthRecord.id == record_id
    ).first()

    # 2. 기록이 존재하지 않으면 404 반환
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="해당 건강 기록을 찾을 수 없습니다."
        )

    # 3. 요청받은 항목만 추출
    update_data = record_data.model_dump(
        exclude_unset=True
    )

    # 4. 필수값인 날짜는 null로 수정할 수 없도록 검사
    if update_data.get("record_date", "not_provided") is None:
        raise HTTPException(
            status_code=422,
            detail="기록 날짜는 null로 수정할 수 없습니다."
        )

    # 5. 변경할 항목만 반영
    for key, value in update_data.items():
        setattr(record, key, value)

    # 6. DB에 저장
    db.commit()
    db.refresh(record)

    return record
