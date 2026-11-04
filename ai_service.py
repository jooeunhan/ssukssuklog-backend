import os
from dotenv import load_dotenv

load_dotenv()

import torch
import json

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)

from peft import PeftModel

BASE_MODEL_NAME = os.getenv(
    "QLORA_BASE_MODEL",
    "Qwen/Qwen2.5-7B-Instruct",
)

ADAPTER_PATH = os.getenv("QLORA_ADAPTER_PATH")

if not ADAPTER_PATH:
    raise RuntimeError(
        "QLORA_ADAPTER_PATH 환경변수가 설정되지 않았습니다."
    )

tokenizer = None
model = None


def load_qlora_model():
    global tokenizer, model

    if model is not None:
        return

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU를 사용할 수 없습니다.")

    print("QLoRA 모델 로딩 시작...")

    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL,
        trust_remote_code=False,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        quantization_config=quantization_config,
        device_map={"": 0},
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
    )

    model = PeftModel.from_pretrained(
        base_model,
        ADAPTER_PATH,
        is_trainable=False,
    )

    model.eval()

    print("QLoRA 모델 로딩 완료!")


def get_qlora_model():
    if model is None or tokenizer is None:
        raise RuntimeError("QLoRA 모델이 아직 로딩되지 않았습니다.")

    return tokenizer, model


def analyze_clinical_note(clinical_note: str):
    tokenizer, model = get_qlora_model()

    messages = [
        {
            "role": "system",
            "content": (
                "당신은 어린이집 교사의 건강 관찰 기록에서 "
                "증상과 증상 강도를 추출하는 정보 추출 모델입니다.\n"

                "반드시 아래 증상 목록에서만 증상명을 선택하세요.\n"
                "기침, 콧물, 빠른 호흡, 발열, 오한, 피로감, "
                "식사량 감소, 구강 통증·병변, 활동성 저하, 보챔, "
                "발진, 전신 발진, 가려움, 두드러기, 설사, 구토\n"

                "카테고리는 반드시 다음 7개 중에서만 선택하세요.\n"
                "호흡기, 체온·전신, 식사·구강, 활동성, 행동, 피부, 소화기\n"

                "비강, 감기, 독감 등 목록에 없는 카테고리는 생성하지 마세요.\n"
                "관찰 기록에 명시되지 않은 증상은 추측하지 마세요.\n"
                "증상 강도는 0.0부터 1.0 사이의 숫자로 표현하세요.\n"

                "반드시 다음 JSON 형식으로만 응답하세요.\n"
                '{"symptom_scores": {"기침": 0.5}, '
                '"categories": ["호흡기"], '
                '"pattern_flags": []}\n'

                "JSON 외의 설명은 작성하지 마세요."
            ),
        },
        {
            "role": "user",
            "content": clinical_note,
        },
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
    ).to(model.device)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    ).strip()

    print("QLoRA 원본 출력:", response)

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        raise ValueError(f"QLoRA JSON 파싱 실패: {response}")