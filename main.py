import json
from datetime import datetime, time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import Base, engine, get_db
import models
from sqlalchemy.orm import Session
from schemas import (
    ChildCreate,
    ChildResponse,
    ChildUpdate,
    HealthRecordCreate,
    HealthRecordResponse,
    HealthRecordUpdate,
    HealthObservationCreate,
    HealthObservationResponse,
    AIAnalyzeRequest,
)
from ai_service import load_qlora_model, analyze_clinical_note
from rf_service import load_rf_model, predict_care_priority
from temperature_service import analyze_daily_temperature
from personalization_service import analyze_allergy_context

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

# 시간대별 건강 관찰 기록 등록
@app.post(
    "/observations",
    tags=["Health"],
    summary="시간대별 건강 관찰 기록 등록",
    description="아동의 시간대별 체온, 증상, 관찰 내용을 저장합니다.",
    response_model=HealthObservationResponse,
    status_code=201,
)
def create_health_observation(
    observation: HealthObservationCreate,
    db: Session = Depends(get_db),
):
    # 1. 아동 존재 여부 확인
    child = db.query(models.Child).filter(
        models.Child.id == observation.child_id
    ).first()

    if child is None:
        raise HTTPException(
            status_code=404,
            detail="해당 아동을 찾을 수 없습니다.",
        )

    # 2. 하루 건강 기록 조회
    daily_record = db.query(models.HealthRecord).filter(
        models.HealthRecord.child_id == observation.child_id,
        models.HealthRecord.record_date == observation.record_date,
    ).first()

    # 3. 없다면 하루 건강 기록 생성
    if daily_record is None:
        daily_record = models.HealthRecord(
            child_id=observation.child_id,
            record_date=observation.record_date,
            ai_status="pending",
        )

        db.add(daily_record)
        db.flush()

    # 4. 시간대별 체온 반영
    temperature_fields = {
        "morning": "temp_morning",
        "noon": "temp_noon",
        "afternoon": "temp_afternoon",
    }

    if observation.temperature is not None:
        field_name = temperature_fields[observation.time_slot]

        setattr(
            daily_record,
            field_name,
            observation.temperature,
        )

    # 5. 개별 관찰 기록 생성
    new_observation = models.HealthObservation(
        health_record_id=daily_record.id,
        time_slot=observation.time_slot,
        observed_time=observation.observed_time,
        temperature=observation.temperature,
        selected_symptoms=json.dumps(
            observation.selected_symptoms,
            ensure_ascii=False,
        ),
        note=observation.note,
    )

    db.add(new_observation)

    # 6. 기존 AI 분석 결과 무효화
    daily_record.ai_status = "pending"
    daily_record.ai_symptom_scores = None
    daily_record.ai_categories = None
    daily_record.ai_pattern_flags = None
    daily_record.ai_care_priority = None
    daily_record.ai_analyzed_at = None

    # 7. DB 저장
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="건강 기록 저장 중 충돌이 발생했습니다.",
        )

    db.refresh(new_observation)

    # 8. JSON 문자열을 배열로 변환하여 응답
    return {
        "id": new_observation.id,
        "health_record_id": new_observation.health_record_id,
        "time_slot": new_observation.time_slot,
        "observed_time": new_observation.observed_time,
        "temperature": new_observation.temperature,
        "selected_symptoms": json.loads(
            new_observation.selected_symptoms
        ),
        "note": new_observation.note,
        "created_at": new_observation.created_at,
    }

@app.post(
    "/ai/analyze",
    tags=["AI"],
    summary="아동 건강 기록 AI 분석",
    description="QLoRA로 증상 정보를 추출하고 RF-D로 관찰 우선순위를 분류합니다.",
)
def analyze_health_record(
    request: AIAnalyzeRequest,
    db: Session = Depends(get_db),
):
    # 1. 아동 조회
    child = db.query(models.Child).filter(
        models.Child.id == request.child_id
    ).first()

    if child is None:
        raise HTTPException(
            status_code=404,
            detail="해당 아동을 찾을 수 없습니다.",
        )

    # 2. 하루 건강 기록 조회
    daily_record = db.query(models.HealthRecord).filter(
        models.HealthRecord.child_id == request.child_id,
        models.HealthRecord.record_date == request.record_date,
    ).first()

    if daily_record is None:
        raise HTTPException(
            status_code=404,
            detail="해당 날짜의 건강 기록이 없습니다.",
        )

    # 3. 체온 3회 입력 확인
    temperatures = [
        daily_record.temp_morning,
        daily_record.temp_noon,
        daily_record.temp_afternoon,
    ]

    has_all_temperatures = all(
        temp is not None for temp in temperatures
    )

    # 4. 시간대별 관찰 기록 조회
    observations = db.query(
        models.HealthObservation
    ).filter(
        models.HealthObservation.health_record_id == daily_record.id
    ).order_by(
        models.HealthObservation.observed_time.asc()
    ).all()

    # 5. 자연어 관찰 내용 취합
    notes = [
        obs.note.strip()
        for obs in observations
        if obs.note and obs.note.strip()
    ]

    if not notes:
        raise HTTPException(
            status_code=409,
            detail="AI 분석에 사용할 관찰 내용이 없습니다.",
        )

    clinical_note = "\n".join(notes)

    # 6. QLoRA
    try:
        load_qlora_model()

        qlora_result = analyze_clinical_note(
            clinical_note
        )

        # QLoRA 결과 저장
        daily_record.ai_symptom_scores = json.dumps(
            qlora_result["symptom_scores"],
            ensure_ascii=False,
        )

        daily_record.ai_categories = json.dumps(
            qlora_result["categories"],
            ensure_ascii=False,
        )

        daily_record.ai_pattern_flags = json.dumps(
            qlora_result["pattern_flags"],
            ensure_ascii=False,
        )

        # RF-D 결과 기본값
        rf_result = None

        # 7. 체온 3회가 모두 있을 때만 RF-D 실행
        if has_all_temperatures:
            load_rf_model()

            rf_result = predict_care_priority(
                age_months=child.age_months,
                morning_temp=daily_record.temp_morning,
                lunch_temp=daily_record.temp_noon,
                afternoon_temp=daily_record.temp_afternoon,
                qlora_result=qlora_result,
            )

            daily_record.ai_care_priority = rf_result[
                "care_priority"
            ]

            daily_record.ai_status = "completed"

        else:
            daily_record.ai_care_priority = None
            daily_record.ai_status = "partial"

        # 8. 개인별 체온 분석 (기존 AI 결과 저장 전에 실행)
        temperature_analysis = analyze_daily_temperature(
            db=db,
            child_id=child.id,
            record_date=daily_record.record_date,
        )

        # 9. 기존 알레르기 정보와 증상 분석
        allergy_analysis = analyze_allergy_context(
            allergies=child.allergies,
            qlora_result=qlora_result,
        )

        # 10. AI 분석 결과 저장
        daily_record.ai_analyzed_at = datetime.now()
        db.commit()
        db.refresh(daily_record)


    except Exception as e:

        import traceback

        db.rollback()

        print("AI 분석 오류:", repr(e))

        traceback.print_exc()

        daily_record.ai_status = "failed"

        db.commit()

        raise HTTPException(

            status_code=500,

            detail="AI 분석 중 오류가 발생했습니다.",

        )

    # 8. 결과 반환
    return {
        "child_id": child.id,
        "record_date": str(daily_record.record_date),
        "clinical_note": clinical_note,
        "symptom_scores": qlora_result["symptom_scores"],
        "categories": qlora_result["categories"],
        "pattern_flags": qlora_result["pattern_flags"],
        "care_priority": (
            rf_result["care_priority"]
            if rf_result is not None else None
        ),
        "care_priority_label": (
            rf_result["label"]
            if rf_result is not None else None
        ),
        "class_probabilities": (
            rf_result["class_probabilities"]
            if rf_result is not None else None
        ),
        "ai_status": daily_record.ai_status,
        "ai_analyzed_at": daily_record.ai_analyzed_at,
        "temperature_analysis": temperature_analysis,
        "allergy_analysis": allergy_analysis,
    }
