import os
from dotenv import load_dotenv

import joblib
import pandas as pd

load_dotenv()

RF_MODEL_PATH = os.getenv("RF_MODEL_PATH")

if not RF_MODEL_PATH:
    raise RuntimeError(
        "RF_MODEL_PATH 환경변수가 설정되지 않았습니다."
    )

rf_model = None
rf_features = None
rf_label_names = None


def load_rf_model():
    global rf_model, rf_features, rf_label_names

    if rf_model is not None:
        return

    bundle = joblib.load(RF_MODEL_PATH)

    print("저장된 모델:", bundle["model_name"])

    if bundle["model_name"] != "RF-D":
        raise ValueError(
            "저장된 최적 모델이 RF-D가 아닙니다."
        )

    rf_model = bundle["model"]
    rf_features = bundle["features"]
    rf_label_names = bundle["label_names"]

    print("RF-D 로딩 완료!")
    print("입력 특성 수:", len(rf_features))


def predict_care_priority(
    age_months,
    morning_temp,
    lunch_temp,
    afternoon_temp,
    qlora_result,
):
    if rf_model is None:
        load_rf_model()

    # RF-D 학습 당시 사용한 특성 순서 유지
    feature_values = {
        feature: 0.0
        for feature in rf_features
    }

    feature_values["age_months"] = age_months
    feature_values["morning_temp"] = morning_temp
    feature_values["lunch_temp"] = lunch_temp
    feature_values["afternoon_temp"] = afternoon_temp

    symptom_scores = qlora_result["symptom_scores"]
    categories = qlora_result["categories"]

    for symptom, score in symptom_scores.items():
        feature_name = f"symptom_{symptom}"

        if feature_name not in feature_values:
            raise ValueError(
                f"알 수 없는 증상: {symptom}"
            )

        score = float(score)

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                f"증상 강도 범위 오류: {symptom}={score}"
            )

        feature_values[feature_name] = score

    for category in categories:
        feature_name = f"category_{category}"

        if feature_name not in feature_values:
            raise ValueError(
                f"알 수 없는 카테고리: {category}"
            )

        feature_values[feature_name] = 1

    X = pd.DataFrame(
        [feature_values],
        columns=rf_features,
    )

    prediction = int(rf_model.predict(X)[0])

    probabilities = rf_model.predict_proba(X)[0]

    return {
        "care_priority": prediction,
        "label": rf_label_names[prediction],
        "class_probabilities": {
            rf_label_names[int(label)]: round(float(prob), 4)
            for label, prob in zip(
                rf_model.classes_,
                probabilities,
            )
        },
    }