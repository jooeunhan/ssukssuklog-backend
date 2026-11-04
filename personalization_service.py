import json


ALLERGY_RELATED_SYMPTOMS = {
    "발진",
    "전신 발진",
    "가려움",
    "두드러기",
    "구토",
    "빠른 호흡",
}


def analyze_allergy_context(
    allergies,
    qlora_result,
):
    # 1. 기존 알레르기 정보 정리
    if isinstance(allergies, str):
        try:
            parsed = json.loads(allergies)
            known_allergies = (
                parsed if isinstance(parsed, list)
                else [allergies]
            )
        except json.JSONDecodeError:
            known_allergies = [
                item.strip()
                for item in allergies.split(",")
                if item.strip()
            ]
    elif isinstance(allergies, list):
        known_allergies = allergies
    else:
        known_allergies = []

    # 2. QLoRA 증상 추출 결과 확인
    symptom_scores = qlora_result.get(
        "symptom_scores", {}
    )

    related_symptoms = [
        symptom
        for symptom, score in symptom_scores.items()
        if (
            symptom in ALLERGY_RELATED_SYMPTOMS
            and isinstance(score, (int, float))
            and score > 0
        )
    ]

    # 3. 추가 확인 필요 여부
    requires_context_review = bool(
        known_allergies and related_symptoms
    )

    return {
        "known_allergies": known_allergies,
        "related_symptoms": related_symptoms,
        "requires_context_review": requires_context_review,
    }