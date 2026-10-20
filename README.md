# 🌱 쑥쑥로그 (SsukSsukLog) Backend

어린이집 교사를 위한 아동 건강 기록 및 관리 웹 서비스 **쑥쑥로그**의 백엔드 저장소입니다.

## 📌 프로젝트 소개

쑥쑥로그는 어린이집 교사가 아동의 건강 상태를 체계적으로 기록하고 관리할 수 있도록 지원하는 웹 서비스입니다.

아동별 기본 정보와 건강 기록을 관리하고, 향후 AI 기반 건강 기록 분석 및 보호자 안내 메시지 생성 기능을 연동하는 것을 목표로 합니다.

## 🛠 기술 스택

- **Language:** Python
- **Framework:** FastAPI
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Data Validation:** Pydantic
- **API Documentation:** Swagger UI

## 📂 프로젝트 구조

```text
ssukssuklog-backend/
├── main.py          # FastAPI 실행 및 API 엔드포인트
├── database.py      # SQLite 연결 설정
├── models.py        # 데이터베이스 테이블 모델
├── schemas.py       # Pydantic 데이터 검증 스키마
├── .gitignore
└── README.md
```

## 🚀 주요 기능

### 아동 정보 관리

| Method | Endpoint | Description |
|---|---|---|
| POST | `/children` | 아동 등록 |
| GET | `/children` | 전체 아동 목록 조회 |
| GET | `/children/{child_id}` | 특정 아동 조회 |
| PATCH | `/children/{child_id}` | 아동 정보 수정 |
| DELETE | `/children/{child_id}` | 아동 정보 삭제 |

### 건강 기록 관리

- 아동별 건강 기록 테이블 구성
- 날짜별 체온, 증상 및 관찰 내용 저장을 위한 데이터 모델 정의
- 건강 기록 등록 및 조회 API 개발 예정

## 💻 로컬 실행 방법

**1. 가상환경 생성 및 활성화 (Windows)**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**2. 패키지 설치**

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy
```

**3. 서버 실행**

```bash
python -m uvicorn main:app --reload
```

**4. API 문서 확인**

서버 실행 후 아래 주소에서 Swagger UI를 확인할 수 있습니다.

http://127.0.0.1:8000/docs

## 🔮 향후 개발 계획

- 아동별 건강 기록 CRUD API 구현
- React 프론트엔드와 FastAPI 연동
- AI 기반 건강 기록 분석 기능 연동
- GPT-4o-mini 기반 보호자 메시지 초안 생성
- 졸업작품 전시를 위한 배포 환경 구축

## 🔗 Frontend Repository

https://github.com/jooeunhan/ssukssuklog

---

본 프로젝트는 공학종합설계 졸업작품으로 개발 중입니다.