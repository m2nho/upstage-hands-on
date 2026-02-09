# 🚀 Upstage API Hands-on Lab

Upstage의 모든 API를 직접 체험하고 학습하는 실습 모음입니다.

---

## 📋 실습 목록

### 1. [💬 Chat Completions](./01_chat_completions/)
Solar 모델의 모든 파라미터를 실시간으로 테스트하는 Playground

![Chat Completions Demo](./01_chat_completions/images/main_ui.gif)

**주요 기능:**
- Temperature, Top-P, Frequency/Presence Penalty 조절
- JSON Schema 기반 구조화된 출력
- Function Calling으로 외부 API 연동
- Reasoning Effort 설정 (solar-pro2/pro3)

**실습 튜토리얼:**
- Temperature로 창의성 조절하기
- JSON Schema로 구조화된 데이터 추출
- Function Calling으로 날씨 API 연동

---

### 2. [📄 Document Digitization](./02_document_digitization/)
문서를 디지털 데이터로 변환

![Document Digitization Demo](./02_document_digitization/images/main_ui.gif)

**주요 기능:**
- Document Parse: 구조 분석 및 Markdown 변환
- Document OCR: 이미지 텍스트 추출
- Base64 인코딩: 요소 이미지 추출
- Enhanced 모드: 복잡한 표/차트 처리

**실습 튜토리얼:**
- 복잡한 재무제표 파싱 (삼성전자 사례)
- OCR로 문서 텍스트 추출
- Base64 인코딩으로 요소 추출

---

### 3. [🔍 Information Extraction](./03_information_extraction/)
문서에서 원하는 정보를 자동 추출

![Information Extraction Demo](./03_information_extraction/images/main_ui.gif)

**주요 기능:**
- Universal Extraction: JSON 스키마 기반 제로샷 추출
- Schema Generation: 최적 스키마 자동 생성
- Prebuilt Extraction: 영수증, 항공화물운송장 등 특화 모델

**실습 튜토리얼:**
- 이력서 자동 파싱 (Universal)
- 송장 스키마 자동 생성
- 영수증 정보 추출 (Prebuilt)

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

### 실습별 설치 및 실행

#### 01. Chat Completions
```bash
cd 01_chat_completions
pip install streamlit langchain-upstage
streamlit run app.py
```

#### 02. Document Digitization
```bash
cd 02_document_digitization
pip install streamlit requests pdf2image pillow
streamlit run app.py
```

#### 03. Information Extraction
```bash
cd 03_information_extraction
pip install streamlit requests
streamlit run app.py
```