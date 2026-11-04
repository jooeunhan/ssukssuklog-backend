from datetime import timedelta
from statistics import median

from sqlalchemy.orm import Session

import models


def analyze_temperature_history(
    db: Session,
    child_id: int,
    record_date,
):
    # 1. 분석 날짜 이전 30일 기록 조회
    start_date = record_date - timedelta(days=30)

    records = (
        db.query(models.HealthRecord)
        .filter(
            models.HealthRecord.child_id == child_id,
            models.HealthRecord.record_date >= start_date,
            models.HealthRecord.record_date < record_date,
        )
        .order_by(models.HealthRecord.record_date)
        .all()
    )

    # 2. 날짜별 체온 데이터 정리
    history = []

    for record in records:
        temperatures = [
            record.temp_morning,
            record.temp_noon,
            record.temp_afternoon,
        ]

        valid_temperatures = [
            float(temp)
            for temp in temperatures
            if temp is not None
        ]

        if not valid_temperatures:
            continue

        history.append({
            "date": str(record.record_date),
            "average_temp": round(
                sum(valid_temperatures) / len(valid_temperatures),
                2,
            ),
            "max_temp": max(valid_temperatures),
            "measurement_count": len(valid_temperatures),
        })

    # 3. 개인 기준 체온 계산에 사용할 기록 선별
    # 38.0℃ 이상 측정된 날짜는 기준값 계산에서 제외
    baseline_history = [
        item
        for item in history
        if item["max_temp"] < 38.0
    ]

    # 4. 평소 체온 계산
    baseline_temp = None

    if len(baseline_history) >= 5:
        baseline_temp = round(
            median([
                item["average_temp"]
                for item in baseline_history
            ]),
            2,
        )

    return {
        "child_id": child_id,
        "history_days": len(history),
        "baseline_days": len(baseline_history),
        "baseline_temp": baseline_temp,
        "history": history,
    }

def analyze_daily_temperature(
    db: Session,
    child_id: int,
    record_date,
):
    # 1. 오늘 건강 기록 조회
    record = (
        db.query(models.HealthRecord)
        .filter(
            models.HealthRecord.child_id == child_id,
            models.HealthRecord.record_date == record_date,
        )
        .first()
    )

    if record is None:
        return None

    # 2. 오늘 체온 정리
    temperatures = {
        "morning": record.temp_morning,
        "noon": record.temp_noon,
        "afternoon": record.temp_afternoon,
    }

    valid_temperatures = {
        slot: float(temp)
        for slot, temp in temperatures.items()
        if temp is not None
    }

    # 3. 가장 최근 측정된 체온
    current_temp = (
        list(valid_temperatures.values())[-1]
        if valid_temperatures
        else None
    )

    # 4. 당일 첫 측정과 마지막 측정의 차이
    daily_temp_change = None

    if len(valid_temperatures) >= 2:
        values = list(valid_temperatures.values())

        daily_temp_change = round(
            values[-1] - values[0],
            2,
        )

    # 5. 개인별 평소 체온 분석
    history_result = analyze_temperature_history(
        db=db,
        child_id=child_id,
        record_date=record_date,
    )

    baseline_temp = history_result["baseline_temp"]

    # 6. 평소 체온과 현재 체온 차이
    baseline_delta = None

    if baseline_temp is not None and current_temp is not None:
        baseline_delta = round(
            current_temp - baseline_temp,
            2,
        )

    return {
        "child_id": child_id,
        "record_date": str(record_date),
        "temperatures": valid_temperatures,
        "current_temp": current_temp,
        "daily_temp_change": daily_temp_change,
        "baseline_temp": baseline_temp,
        "baseline_delta": baseline_delta,
        "baseline_status": (
            "available"
            if baseline_temp is not None
            else "insufficient_data"
        ),
        "history_days": history_result["history_days"],
        "baseline_days": history_result["baseline_days"],
    }