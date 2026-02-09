import streamlit as st
import requests
import json
import base64

st.set_page_config(page_title="Information Extraction", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    .stButton button { width: 100%; }
</style>
""", unsafe_allow_html=True)

st.title("🔍 Information Extraction Lab")

api_key = st.sidebar.text_input("Upstage API Key", type="password")

if not api_key:
    st.warning("왼쪽 사이드바에서 API Key를 입력해주세요.")
    st.info("💡 [Console](https://console.upstage.ai)에서 API Key 발급")
else:
    api_type = st.radio(
        "🔧 API 선택",
        ["📄 Universal Extraction", "🧬 Schema Generation", "📋 Prebuilt Extraction"],
        horizontal=True,
        help="Universal: 커스텀 스키마 | Schema Generation: 자동 스키마 생성 | Prebuilt: 특화 모델"
    )
    
    st.divider()
    
    uploaded_file = st.file_uploader(
        "📤 문서 업로드",
        type=["pdf", "jpg", "jpeg", "png"]
    )
    
    if api_type == "📄 Universal Extraction":
        st.markdown("#### 스키마 설정")
        schema_input = st.text_area(
            "JSON Schema",
            value='{\n  "type": "object",\n  "properties": {\n    "name": {\n      "type": "string",\n      "description": "지원자 이름"\n    },\n    "email": {\n      "type": "string",\n      "description": "이메일 주소"\n    },\n    "phone": {\n      "type": "string",\n      "description": "전화번호"\n    },\n    "education": {\n      "type": "array",\n      "description": "학력 사항",\n      "items": {\n        "type": "object",\n        "properties": {\n          "school": {"type": "string"},\n          "degree": {"type": "string"},\n          "major": {"type": "string"},\n          "graduation_date": {"type": "string"}\n        }\n      }\n    },\n    "experience": {\n      "type": "array",\n      "description": "경력 사항",\n      "items": {\n        "type": "object",\n        "properties": {\n          "company": {"type": "string"},\n          "position": {"type": "string"},\n          "period": {"type": "string"},\n          "description": {"type": "string"}\n        }\n      }\n    },\n    "skills": {\n      "type": "array",\n      "description": "보유 기술",\n      "items": {"type": "string"}\n    }\n  },\n  "required": ["name"]\n}',
            height=400
        )
        
        st.markdown("#### 기본 옵션")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mode = st.selectbox(
                "모드 (Beta)",
                ["standard", "enhanced"],
                help="standard: 기본 모드 | enhanced: 복잡한 표, 저품질 스캔, 손글씨에 강함 (추가 비용)"
            )
        
        with col2:
            location = st.checkbox(
                "위치 정보 (Beta)",
                value=False,
                help="추출된 값의 문서 내 위치(페이지 번호, 좌표) 반환. 좌표는 0~1로 정규화"
            )
        
        with col3:
            location_granularity = st.selectbox(
                "위치 세분화 (Beta)",
                ["element", "word", "all"],
                help="element: HTML 요소 전체 좌표 | word: 특정 단어 좌표 | all: 둘 다",
                disabled=not location
            )
        
        col4, col5, col6 = st.columns(3)
        
        with col4:
            split = st.checkbox(
                "문서 분할 (Beta)",
                value=False,
                help="단일 파일 내 여러 문서를 자동 분할하여 개별 처리"
            )
        
        with col5:
            confidence = st.checkbox(
                "신뢰도 (Beta)",
                value=False,
                help="추출 값의 신뢰도(high/low) 반환. 재현율 >95%, low 중 약 50%가 오추출"
            )
        
        with col6:
            enable_chunking = st.checkbox(
                "청킹 활성화 (Beta)",
                value=False,
                help="30페이지 이상 또는 50행 이상 표가 있는 문서에 권장"
            )
        
        if enable_chunking:
            pages_per_chunk = st.number_input(
                "청크당 페이지 수",
                min_value=1,
                max_value=100,
                value=5,
                help="문서를 작은 단위로 나누어 처리"
            )
    
    elif api_type == "🧬 Schema Generation":
        st.markdown("#### 추출 목표")
        extraction_goal = st.text_area(
            "스키마 생성 목표 (System Message)",
            placeholder="예: Generate schema about bank_name, account_number, and balance from bank statement.",
            height=100,
            help="추출하고자 하는 필드와 목적을 설명"
        )
    
    else:
        st.markdown("#### 모델 선택")
        model_type = st.selectbox(
            "Prebuilt 모델",
            ["receipt-extraction", "air-waybill-extraction", "bill-of-lading-and-shipping-request-extraction", 
             "commercial-invoice-and-packing-list-extraction", "kr-export-declaration-certificate-extraction"],
            format_func=lambda x: {
                "receipt-extraction": "영수증",
                "air-waybill-extraction": "항공화물운송장",
                "bill-of-lading-and-shipping-request-extraction": "선하증권 및 선적요청서",
                "commercial-invoice-and-packing-list-extraction": "상업송장 및 포장명세서",
                "kr-export-declaration-certificate-extraction": "수출신고필증"
            }.get(x, x),
            help="특정 문서 유형에 최적화된 모델"
        )
    
    if uploaded_file and st.button("🚀 실행", type="primary"):
        with st.spinner(f"{'🔍 추출' if api_type != '🧬 Schema Generation' else '🧬 스키마 생성'} 중..."):
            try:
                if api_type == "📄 Universal Extraction":
                    schema = json.loads(schema_input)
                    file_bytes = uploaded_file.getvalue()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    payload = {
                        "model": "information-extract",
                        "messages": [{
                            "role": "user",
                            "content": [{
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }]
                        }],
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "document_schema",
                                "schema": schema
                            }
                        },
                        "mode": mode,
                        "location": location,
                        "confidence": confidence,
                        "split": split
                    }
                    
                    if location:
                        payload["location_granularity"] = location_granularity
                    
                    if enable_chunking:
                        payload["chunking"] = {"pages_per_chunk": pages_per_chunk}
                    
                    response = requests.post(
                        "https://api.upstage.ai/v1/information-extraction",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json=payload
                    )
                
                elif api_type == "🧬 Schema Generation":
                    file_bytes = uploaded_file.getvalue()
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    messages = [
                        {"role": "system", "content": extraction_goal}
                    ]
                    
                    if uploaded_file:
                        messages.append({
                            "role": "user",
                            "content": [{
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }]
                        })
                    
                    payload = {
                        "model": "information-extract",
                        "messages": messages
                    }
                    
                    response = requests.post(
                        "https://api.upstage.ai/v1/information-extraction/schema-generation",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json=payload
                    )
                
                else:
                    response = requests.post(
                        "https://api.upstage.ai/v1/information-extraction",
                        headers={"Authorization": f"Bearer {api_key}"},
                        files={"document": uploaded_file.getvalue()},
                        data={"model": model_type}
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("✅ 완료!")
                    
                    st.markdown("### 📊 결과")
                    st.json(result)
                    
                    st.markdown("### 💾 다운로드")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            "📥 JSON 다운로드",
                            json.dumps(result, ensure_ascii=False, indent=2),
                            "result.json",
                            "application/json"
                        )
                    
                    with col2:
                        if api_type == "📄 Universal Extraction":
                            extracted = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                            st.download_button(
                                "📥 추출 데이터 다운로드",
                                extracted,
                                "extracted.json",
                                "application/json"
                            )
                
                else:
                    st.error(f"❌ API 오류 ({response.status_code})")
                    st.code(response.text)
            
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    elif not uploaded_file:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("""
            ### 📄 Universal Extraction
            
            **기능:**
            - 커스텀 JSON 스키마 정의
            - 제로샷 정보 추출
            - 위치/신뢰도 정보
            - 문서 분할 처리
            - 청킹 지원 (대용량)
            
            **사용 예시:**
            - 이력서 파싱
            - 계약서 정보 추출
            - 커스텀 양식 처리
            """)
        
        with col2:
            st.info("""
            ### 🧬 Schema Generation
            
            **기능:**
            - 자동 스키마 생성
            - 목표 기반 설계
            - 최대 3개 이미지 지원
            
            **사용 예시:**
            - 새로운 문서 타입 분석
            - 스키마 프로토타이핑
            - 빠른 POC
            """)
        
        with col3:
            st.info("""
            ### 📋 Prebuilt Extraction
            
            **기능:**
            - 특화 모델 사용
            - 높은 정확도
            - 즉시 사용 가능
            
            **지원 문서:**
            - 영수증
            - 항공화물운송장
            - 선하증권
            - 상업송장
            - 수출신고필증
            """)
        
        st.markdown("---")
