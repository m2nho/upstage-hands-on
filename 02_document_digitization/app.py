import streamlit as st
import requests
import json
from pdf2image import convert_from_bytes
from PIL import Image, ImageDraw
import io
import base64

st.set_page_config(page_title="Document Digitization", page_icon="📄", layout="wide")

st.markdown("""
<style>
    .stButton button { width: 100%; }
    .element-badge { 
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin: 2px;
    }
    .badge-text { background: #FFE5B4; color: #8B4513; }
    .badge-table { background: #B4E5FF; color: #004080; }
    .badge-figure { background: #FFB4E5; color: #800040; }
    .badge-chart { background: #B4FFB4; color: #004000; }
</style>
""", unsafe_allow_html=True)

st.title("📄 Document Digitization Lab")

api_key = st.sidebar.text_input("Upstage API Key", type="password")

if not api_key:
    st.warning("왼쪽 사이드바에서 API Key를 입력해주세요.")
    st.info("💡 [Console](https://console.upstage.ai)에서 API Key 발급")
else:
    # API 선택
    api_type = st.radio(
        "🔧 API 선택",
        ["📄 Document Parse", "🔍 Document OCR"],
        horizontal=True,
        help="Document Parse: 구조 분석 + 텍스트 추출 | Document OCR: 이미지 텍스트 추출"
    )
    
    st.divider()
    
    # 파일 업로드
    uploaded_file = st.file_uploader(
        "📤 문서 업로드",
        type=["pdf", "jpg", "jpeg", "png", "bmp", "docx", "pptx", "xlsx"]
    )
    
    # 설정
    if api_type == "📄 Document Parse":
        st.markdown("#### 기본 옵션")
        col1, col2, col3 = st.columns(3)
        with col1:
            output_format = st.selectbox("출력", ["html", "markdown", "text"], help="결과 출력 형식")
        with col2:
            ocr = st.selectbox("OCR", ["auto", "force"], help="auto: 이미지만 OCR | force: 모든 파일 OCR")
        with col3:
            coordinates = st.checkbox("좌표", value=True, help="요소의 위치 좌표 반환")
        
        col4, _ = st.columns([1, 2])
        with col4:
            base64_encoding = st.multiselect(
                "Base64 인코딩", 
                ["table", "figure", "chart", "heading1", "header", "footer", "caption", "paragraph", "equation", "list", "index", "footnote"],
                help="선택한 카테고리의 요소를 원본 문서에서 잘라낸 이미지로 추출"
            )
        
        st.markdown("#### 베타 옵션")
        col5, col6, col7 = st.columns(3)
        with col5:
            mode = st.selectbox("모드 (Beta)", ["standard", "enhanced", "auto"], help="standard: 텍스트 중심 문서 | enhanced: 복잡한 표/차트 | auto: 자동 선택")
        with col6:
            chart_recognition = st.checkbox("차트 인식 (Beta)", value=True, help="차트를 표로 변환")
        with col7:
            merge_multipage_tables = st.checkbox("다중 페이지 표 병합 (Beta)", value=False, help="여러 페이지 표를 하나로 병합 (enhanced 모드에서 20페이지 제한)")
    else:
        schema = st.selectbox("스키마", ["None", "clova", "google"], help="Clova 또는 Google OCR API 응답 형식으로 변환 (선택사항)")
        schema = None if schema == "None" else schema
        output_format = "text"
        ocr = "force"
        mode = None
    
    if uploaded_file and st.button("🚀 실행", type="primary", width='stretch'):
        with st.spinner(f"{'📄 파싱' if api_type == '📄 Document Parse' else '🔍 OCR'} 중..."):
            try:
                # API 엔드포인트
                if api_type == "📄 Document Parse":
                    url = "https://api.upstage.ai/v1/document-ai/document-parse"
                    data = {
                        "model": "document-parse",
                        "ocr": ocr,
                        "output_formats": f"['{output_format}']",
                        "coordinates": str(coordinates).lower(),
                        "mode": mode,
                        "chart_recognition": str(chart_recognition).lower(),
                        "merge_multipage_tables": str(merge_multipage_tables).lower()
                    }
                    if base64_encoding:
                        data["base64_encoding"] = str(base64_encoding).replace("'", '"')
                else:
                    url = "https://api.upstage.ai/v1/document-ai/ocr"
                    data = {"model": "ocr"}
                    if schema:
                        data["schema"] = schema
                
                headers = {"Authorization": f"Bearer {api_key}"}
                files = {"document": (uploaded_file.name, uploaded_file.getvalue())}
                
                response = requests.post(url, headers=headers, data=data, files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Document Parse
                    if api_type == "📄 Document Parse":
                        elements = result.get("elements", [])
                        st.success(f"✅ 완료! {len(elements)}개 요소 추출")
                        
                        # 원본 이미지 준비
                        file_bytes = uploaded_file.getvalue()
                        file_ext = uploaded_file.name.split('.')[-1].lower()
                        
                        images = None
                        if file_ext == 'pdf':
                            try:
                                images = convert_from_bytes(file_bytes, dpi=150)
                            except Exception as e:
                                st.warning(f"PDF 변환 실패: {e}. poppler 설치 필요")
                        elif file_ext in ['jpg', 'jpeg', 'png', 'bmp']:
                            try:
                                images = [Image.open(io.BytesIO(file_bytes))]
                            except Exception as e:
                                st.warning(f"이미지 로드 실패: {e}")
                        
                        if not elements:
                            st.warning("추출된 요소가 없습니다.")
                        
                        if 'selected_elem' not in st.session_state:
                            st.session_state.selected_elem = None
                        
                        pages = sorted(set(e.get("page", 1) for e in elements))
                        
                        for page_num in pages:
                            st.markdown(f"## 📄 페이지 {page_num}")
                            
                            page_elements = [e for e in elements if e.get("page") == page_num]
                            
                            col_left, col_right = st.columns([1, 1])
                            
                            with col_left:
                                st.markdown("### 📎 원본")
                                if images and page_num <= len(images):
                                    st.image(images[page_num - 1], width='stretch')
                                else:
                                    st.info("이미지 미리보기 불가")
                            
                            with col_right:
                                st.markdown("### 📝 파싱 결과")
                                for idx, elem in enumerate(page_elements):
                                    category = elem.get("category", "unknown")
                                    content = elem.get("content", {}).get(output_format, "")
                                    
                                    if content:
                                        icons = {
                                            "table": "📊", "figure": "🖼️", "chart": "📈", 
                                            "heading1": "📌", "header": "🔝", "footer": "🔽",
                                            "caption": "💬", "paragraph": "📝", "equation": "🔢",
                                            "list": "📋", "index": "🔖", "footnote": "📎"
                                        }
                                        icon = icons.get(category, "📄")
                                        
                                        with st.expander(f"{icon} {category} #{idx+1}"):
                                            # Base64 이미지 표시
                                            if elem.get("base64_encoding"):
                                                try:
                                                    img_data = base64.b64decode(elem["base64_encoding"])
                                                    img = Image.open(io.BytesIO(img_data))
                                                    st.image(img, caption=f"{category} 이미지", use_container_width=True)
                                                except Exception as e:
                                                    st.warning(f"Base64 디코딩 실패: {e}")
                                            
                                            if output_format == "html":
                                                st.markdown(content, unsafe_allow_html=True)
                                            elif output_format == "markdown":
                                                st.markdown(content, unsafe_allow_html=True)
                                            else:
                                                st.text(content)
                                            
                                            with st.expander("원문 데이터"):
                                                st.json(elem)
                            
                            st.divider()
                        
                        # 다운로드
                    else:
                        pages = result.get("pages", [])
                        st.success(f"✅ 완료! {len(pages)}페이지 OCR")
                        
                        # 디버그: 원본 응답 확인
                        with st.expander("🔍 API 응답 원문 확인"):
                            st.json(result)
                        
                                # 원본 이미지
                        file_bytes = uploaded_file.getvalue()
                        file_ext = uploaded_file.name.split('.')[-1].lower()
                        
                        images = None
                        if file_ext == 'pdf':
                            try:
                                images = convert_from_bytes(file_bytes, dpi=150)
                            except Exception as e:
                                st.warning(f"PDF 변환 실패: {e}. poppler 설치 필요")
                        elif file_ext in ['jpg', 'jpeg', 'png', 'bmp']:
                            try:
                                images = [Image.open(io.BytesIO(file_bytes))]
                            except Exception as e:
                                st.warning(f"이미지 로드 실패: {e}")
                        
                        if not images:
                            st.info("이미지 미리보기를 사용할 수 없습니다. 텍스트 결과만 표시됩니다.")
                        
                        if not pages:
                            st.warning("OCR 결과가 비어있습니다.")
                        
                        for page_idx, page_data in enumerate(pages, 1):
                            st.markdown(f"## 📄 페이지 {page_idx}")
                            
                            col_left, col_right = st.columns([1, 1])
                            
                            with col_left:
                                st.markdown("### 📎 원본 이미지")
                                if images and page_idx <= len(images):
                                    st.image(images[page_idx - 1], width='stretch')
                                else:
                                    st.info("이미지 미리보기 불가")
                            
                            with col_right:
                                st.markdown("### 🔍 OCR 결과")
                                
                                # 여러 가능한 키 확인
                                text_content = page_data.get(output_format) or page_data.get("text") or page_data.get("content", {}).get(output_format, "")
                                
                                if not text_content:
                                    st.warning(f"페이지 {page_idx}에 추출된 텍스트가 없습니다.")
                                    with st.expander("페이지 데이터 확인"):
                                        st.json(page_data)
                                elif output_format == "html":
                                    st.components.v1.html(text_content, height=600, scrolling=True)
                                elif output_format == "markdown":
                                    st.markdown(text_content, unsafe_allow_html=True)
                                else:
                                    st.text_area("텍스트", text_content, height=600, key=f"ocr_text_{page_idx}")
                            
                            st.divider()
                    
                    # 다운로드
                    st.markdown("### 💾 다운로드")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if api_type == "📄 Document Parse":
                            full_content = "\n\n".join([e.get("content", {}).get(output_format, "") for e in elements if e.get("content", {}).get(output_format, "")])
                        else:
                            full_content = "\n\n".join([p.get(output_format, "") for p in pages if p.get(output_format, "")])
                        
                        if full_content.strip():
                            st.download_button(
                                f"📥 {output_format.upper()} 다운로드",
                                full_content,
                                f"result.{output_format}",
                                width='stretch'
                            )
                        else:
                            st.info("다운로드할 내용이 없습니다.")
                    
                    with col2:
                        st.download_button(
                            "📥 JSON 다운로드",
                            json.dumps(result, ensure_ascii=False, indent=2),
                            "result.json",
                            width='stretch'
                        )
                
                else:
                    st.error(f"❌ API 오류 ({response.status_code})")
                    st.code(response.text)
            
            except Exception as e:
                st.error(f"❌ 오류: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    elif not uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("""
            ### 📄 Document Parse
            
            **기능:**
            - 문서 구조 분석 (제목, 단락, 표, 이미지)
            - 레이아웃 보존
            - 차트 인식 및 표 변환
            - 좌표 정보 제공
            
            **사용 예시:**
            - RAG 시스템 구축
            - 표 데이터 추출
            """)
        
        with col2:
            st.info("""
            ### 🔍 Document OCR
            
            **기능:**
            - 이미지에서 텍스트 추출
            - 스캔 문서 디지털화
            
            **사용 예시:**
            - 스캔 문서 텍스트화
            - 명함/영수증 인식
            - 손글씨 인식
            """)
        
        st.markdown("---")
        st.markdown("""
        
        **💡 Tip:** Document Parse는 구조 분석, OCR은 단순 텍스트 추출에 최적화되어 있습니다.
        """)
