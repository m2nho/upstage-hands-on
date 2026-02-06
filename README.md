# 🚀 Upstage API Hands-on Lab

Upstage의 모든 API를 직접 체험하고 학습하는 인터랙티브 실습 모음입니다.

---

## 📋 실습 목록

### 1. [💬 Chat Completions](./01_chat_completions/)
Solar 모델의 모든 파라미터를 실시간으로 테스트하는 Playground

![Chat Completions Demo](./01_chat_completions/images/main_ui.gif)

- Temperature, Top-P, Frequency/Presence Penalty 조절
- JSON Schema 기반 구조화된 출력
- Function Calling으로 외부 API 연동
- Reasoning Effort 설정 (solar-pro2/pro3)

### 2. 📄 Document Digitization (예정)
문서를 디지털 데이터로 변환
- Document Parsing: 구조 분석 및 Markdown 변환
- Document OCR: 이미지 텍스트 추출
- Asynchronous API: 대용량 문서 비동기 처리

### 3. 🔍 Information Extraction (예정)
문서에서 원하는 정보를 자동 추출
- Universal Extraction: JSON 스키마 기반 제로샷 추출
- Schema Generation: 최적 스키마 자동 생성
- Prebuilt Extraction: 영수증, 사업자등록증 특화 모델

### 4. 📊 Document Classification (예정)
문서 종류 자동 분류

### 5. 🧮 Embeddings (예정)
텍스트 벡터화 및 유사도 검색

### 6. 📁 Files Management (예정)
Upstage 클라우드 파일 관리

### 7. ⚙️ Jobs Management (예정)
비동기 작업 생명주기 관리

---

## 🛠 설치 및 실행

### 사전 준비
1. **API 키 발급**: [Upstage Console](https://console.upstage.ai/) → API Keys
2. **Python 3.8+** 설치

### 공통 설치
```bash
pip install streamlit langchain-upstage
```

### 실습 실행
```bash
cd 01_chat_completions
streamlit run app.py
```

---

## 📚 구현 원칙

- **LangChain 우선**: `langchain-upstage` 지원 기능은 LangChain으로 구현
- **SDK 보완**: LangChain 미지원 기능은 Official Python SDK 사용
- **독립 실행**: 각 실습은 독립적으로 실행 가능
- **코드 제공**: 모든 실습에서 실행 가능한 Python 코드 자동 생성

---

## 🔗 참고 자료

- [Upstage API 공식 문서](https://developers.upstage.ai/)
- [LangChain Upstage 통합](https://python.langchain.com/docs/integrations/chat/upstage)
- [Upstage Console](https://console.upstage.ai/)

---

## 📝 라이선스

MIT License
