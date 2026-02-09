import streamlit as st
from langchain_upstage import ChatUpstage, UpstageEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_core.documents import Document
import numpy as np
import tempfile
import os
import shutil
import requests

st.set_page_config(page_title="Embeddings & RAG", page_icon="🧮", layout="wide")
st.title("🧮 Embeddings & RAG Pipeline")

api_key = st.sidebar.text_input("Upstage API Key", type="password")

if not api_key:
    st.warning("왼쪽 사이드바에서 API Key를 입력해주세요.")
else:
    if st.sidebar.button("🔄 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # 사이드바에 현재 상태 표시
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 현재 상태")
    if 'vectorstore' in st.session_state:
        st.sidebar.success("✅ 벡터 저장소 준비됨")
        st.sidebar.info(f"📄 문서: {len(st.session_state.get('docs', []))}개 페이지")
        st.sidebar.info(f"✂️ 청크: {len(st.session_state.get('splits', []))}개")
    else:
        st.sidebar.warning("⚠️ 문서를 업로드하세요")
    
    tab1, tab2, tab3 = st.tabs(["📚 RAG Pipeline", "💬 일반 LLM", "🗄️ Vector DB 내부"])
    
    with tab1:
        st.markdown("### 📚 RAG Pipeline: 문서 기반 질의응답")
        st.info("01_chat_completions (ChatUpstage) + 02_document_digitization (Document Parse) + Embeddings를 결합한 RAG 시스템")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 1️⃣ 문서 업로드 & 파싱")
            uploaded_file = st.file_uploader(
                "문서 선택",
                type=["pdf", "jpg", "jpeg", "png", "docx", "pptx", "xlsx"],
                help="Document Parse로 문서를 파싱합니다"
            )
            
            chunk_size = st.slider("청크 크기", 100, 2000, 500, 100)
            chunk_overlap = st.slider("청크 오버랩", 0, 500, 100, 50)
            
            with st.expander("⚙️ Document Parse 옵션"):
                output_format = st.selectbox(
                    "출력 형식",
                    ["html", "markdown", "text"],
                    index=1,
                    help="html: HTML 태그 | markdown: 마크다운 | text: 순수 텍스트"
                )
                parse_mode = st.selectbox(
                    "모드",
                    ["auto", "standard", "enhanced"],
                    help="auto: 자동 선택 | standard: 일반 문서 | enhanced: 복잡한 표/차트"
                )
                parse_ocr = st.selectbox(
                    "OCR",
                    ["auto", "force"],
                    help="auto: 이미지만 OCR | force: 모든 파일 OCR"
                )
            
            if uploaded_file and st.button("📄 문서 파싱 & 임베딩", type="primary"):
                with st.status("📄 문서 처리 중...", expanded=True) as status:
                    try:
                        # 1. 임시 파일 저장
                        st.write("✅ 1/4: 파일 업로드 중...")
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_path = tmp_file.name
                        st.write(f"✅ 파일 크기: {len(uploaded_file.getvalue()) / 1024:.1f}KB")
                        
                        # 2. Document Parse (API 직접 호출)
                        st.write("✅ 2/4: Document Parse API 호출 중...")
                        
                        with open(tmp_path, 'rb') as f:
                            response = requests.post(
                                'https://api.upstage.ai/v1/document-ai/document-parse',
                                headers={'Authorization': f'Bearer {api_key}'},
                                data={
                                    'ocr': parse_ocr,
                                    'output_formats': f"['{output_format}']",
                                    'mode': parse_mode
                                },
                                files={'document': (uploaded_file.name, f)}
                            )
                        
                        os.unlink(tmp_path)
                        
                        if response.status_code != 200:
                            raise Exception(f"API 오류: {response.status_code} - {response.text}")
                        
                        result = response.json()
                        elements = result.get('elements', [])
                        
                        # LangChain Document 객체로 변환 (페이지별 분리)
                        docs = []
                        pages = {}
                        for elem in elements:
                            page_num = elem.get('page', 1)
                            content = elem.get('content', {}).get(output_format, '')
                            if content:
                                if page_num not in pages:
                                    pages[page_num] = []
                                pages[page_num].append(content)
                        
                        for page_num in sorted(pages.keys()):
                            docs.append(Document(
                                page_content='\n'.join(pages[page_num]),
                                metadata={'page': page_num}
                            ))
                        
                        st.write(f"✅ {len(docs)}개 페이지 파싱 완료 (format={output_format}, mode={parse_mode})")
                        
                        # 3. 텍스트 분할
                        st.write(f"✅ 3/4: 텍스트 분할 중 (chunk_size={chunk_size}, overlap={chunk_overlap})...")
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=chunk_size,
                            chunk_overlap=chunk_overlap
                        )
                        splits = text_splitter.split_documents(docs)
                        st.write(f"✅ {len(splits)}개 청크로 분할 완료")
                        
                        # 4. 임베딩 & 벡터 저장소
                        st.write("✅ 4/4: 임베딩 생성 & Chroma 벡터 저장소 구축 중...")
                        embeddings = UpstageEmbeddings(api_key=api_key, model="embedding-query")
                        
                        # 복잡한 메타데이터 필터링
                        filtered_splits = filter_complex_metadata(splits)
                        
                        # Chroma 임시 디렉토리 생성
                        chroma_dir = tempfile.mkdtemp()
                        vectorstore = Chroma.from_documents(
                            documents=filtered_splits,
                            embedding=embeddings,
                            persist_directory=chroma_dir,
                            collection_metadata={"hnsw:space": "cosine"}
                        )
                        st.write(f"✅ {len(filtered_splits)}개 벡터 저장 완료 (코사인 유사도)")
                        
                        st.session_state['vectorstore'] = vectorstore
                        st.session_state['docs'] = docs
                        st.session_state['splits'] = splits
                        st.session_state['embeddings'] = embeddings
                        st.session_state['chroma_dir'] = chroma_dir
                        
                        status.update(label="✅ 문서 처리 완료!", state="complete")
                    
                    except Exception as e:
                        st.error(f"오류: {str(e)}")
            
            # 파싱된 문서 미리보기
            if 'docs' in st.session_state:
                st.markdown("---")
                st.markdown("#### 📄 파싱된 문서")
                for i, doc in enumerate(st.session_state['docs'], 1):
                    with st.expander(f"페이지 {i} (길이: {len(doc.page_content)}자)"):
                        st.text_area(f"페이지 {i}", doc.page_content, height=200, key=f"parse_doc_{i}")
        
        with col2:
            st.markdown("#### 2️⃣ 질문 & 답변 생성")
            
            if 'vectorstore' not in st.session_state:
                st.warning("⬅️ 먼저 문서를 업로드하고 파싱하세요")
            else:
                model = st.selectbox("모델", ["solar-mini", "solar-pro3", "solar-pro2"], index=0)
                temperature = st.slider("Temperature", 0.0, 2.0, 0.3, 0.1)
                top_k = st.slider("검색할 문서 수", 1, 10, 3, 1)
                
                question = st.text_area(
                    "질문 입력",
                    "이 문서의 주요 내용을 요약해주세요.",
                    height=100
                )
                
                if st.button("🔍 답변 생성", type="primary"):
                    with st.status("🔍 RAG 파이프라인 실행 중...", expanded=True) as status:
                        try:
                            # 1. 유사 문서 검색
                            st.write(f"✅ 1/3: 벡터 저장소에서 유사 문서 검색 중 (top_k={top_k})...")
                            vectorstore = st.session_state['vectorstore']
                            results = vectorstore.similarity_search_with_score(question, k=top_k)
                            
                            # Chroma는 코사인 거리를 반환, 유사도로 변환 후 내림차순 정렬
                            relevant_docs_with_scores = sorted(
                                [(doc, 1 - score) for doc, score in results],
                                key=lambda x: x[1],
                                reverse=True
                            )
                            st.write(f"✅ {len(relevant_docs_with_scores)}개 관련 문서 발견")
                            
                            st.session_state['last_relevant_docs_with_scores'] = relevant_docs_with_scores
                            st.session_state['last_question'] = question
                            
                            status.update(label="✅ 문서 검색 완료", state="running")
                            
                            # 2. 컨텍스트 구성
                            st.write("✅ 2/3: 컨텍스트 구성 중...")
                            context = "\n\n".join([doc.page_content for doc, score in relevant_docs_with_scores])
                            st.write(f"✅ 컨텍스트 총 길이: {len(context)}자")
                            
                            # 3. LLM 답변 생성
                            st.write(f"✅ 3/3: {model} 모델로 답변 생성 중 (temperature={temperature})...")
                            llm = ChatUpstage(api_key=api_key, model=model, temperature=temperature)
                            
                            prompt = f"""다음 문서를 참고하여 질문에 답변하세요.

문서:
{context}

질문: {question}

답변:"""
                            
                            status.update(label="✅ 답변 생성 중...", state="running")
                            
                            st.markdown("##### 💬 답변")
                            response_placeholder = st.empty()
                            full_response = ""
                            
                            for chunk in llm.stream([("human", prompt)]):
                                full_response += chunk.content
                                response_placeholder.markdown(full_response + "▌")
                            
                            response_placeholder.markdown(full_response)
                            status.update(label="✅ RAG 파이프라인 완료!", state="complete")
                        
                        except Exception as e:
                            st.error(f"오류: {str(e)}")
                
                # 검색된 문서 표시
                if 'last_relevant_docs_with_scores' in st.session_state:
                    st.markdown("---")
                    st.markdown("#### 📑 검색된 문서")
                    for i, (doc, score) in enumerate(st.session_state['last_relevant_docs_with_scores'], 1):
                        with st.expander(f"문서 {i} (길이: {len(doc.page_content)}자, 유사도: {score:.4f})"):
                            st.caption(f"📊 코사인 유사도: {score:.4f} (높을수록 더 유사)")
                            st.text_area(f"문서 {i}", doc.page_content, height=200, key=f"search_doc_{i}")
    
    with tab2:
        st.markdown("### 💬 일반 LLM: RAG 없이 질문하기")
        st.info("문서 없이 LLM의 사전 지식만으로 답변")
        
        model_llm = st.selectbox("모델", ["solar-mini", "solar-pro3", "solar-pro2"], index=0, key="llm_model")
        temperature_llm = st.slider("Temperature", 0.0, 2.0, 0.3, 0.1, key="llm_temp")
        
        question_llm = st.text_area(
            "질문 입력",
            st.session_state.get('last_question', "안녕하세요! 무엇을 도와드릴까요?"),
            height=100,
            key="llm_question"
        )
        
        if st.button("💬 답변 생성", type="primary"):
            with st.spinner("답변 생성 중..."):
                try:
                    llm = ChatUpstage(api_key=api_key, model=model_llm, temperature=temperature_llm)
                    
                    st.markdown("##### 💬 답변")
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    for chunk in llm.stream([("human", question_llm)]):
                        full_response += chunk.content
                        response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    
                    if 'vectorstore' in st.session_state:
                        st.info("💡 RAG 탭에서 같은 질문을 해보세요. 문서를 참고하여 더 정확한 답변을 받을 수 있습니다.")
                
                except Exception as e:
                    st.error(f"오류: {str(e)}")
    
    with tab3:
        st.markdown("### 🗄️ Vector DB 내부 들여다보기")
        
        if 'vectorstore' not in st.session_state:
            st.warning("⚠️ 먼저 문서를 업로드하고 파싱하세요")
        else:
            st.success("✅ Chroma 벡터 저장소가 준비되었습니다 (코사인 유사도)")
            
            # 통계 정보
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 원본 페이지", len(st.session_state.get('docs', [])))
            with col2:
                st.metric("✂️ 청크 수", len(st.session_state.get('splits', [])))
            with col3:
                if 'embeddings' in st.session_state:
                    sample_emb = st.session_state['embeddings'].embed_query("test")
                    st.metric("🔢 벡터 차원", len(sample_emb))
            
            st.markdown("---")
            
            # 저장된 모든 청크 보기
            st.markdown("#### 📦 저장된 모든 청크")
            splits = st.session_state.get('splits', [])
            
            for i, split in enumerate(splits, 1):
                with st.expander(f"청크 #{i} (길이: {len(split.page_content)}자)"):
                    st.text_area(f"청크 {i} 내용", split.page_content, height=150, key=f"chunk_{i}")
                    
                    if split.metadata:
                        st.json(split.metadata)
            
            st.markdown("---")
            
            # 벡터 유사도 테스트
            st.markdown("#### 🧪 벡터 유사도 테스트")
            st.info("임의의 쿼리로 벡터 저장소를 직접 검색해보세요")
            
            test_query = st.text_input("테스트 쿼리", "")
            test_k = st.slider("검색할 청크 수", 1, 10, 3, key="test_k")
            
            if test_query and st.button("🔍 벡터 검색 실행"):
                vectorstore = st.session_state['vectorstore']
                
                results = vectorstore.similarity_search_with_score(test_query, k=test_k)
                
                # 코사인 거리를 유사도로 변환 후 정렬
                results_with_similarity = sorted(
                    [(doc, 1 - score) for doc, score in results],
                    key=lambda x: x[1],
                    reverse=True
                )
                
                st.markdown(f"**검색 결과: {len(results_with_similarity)}개 청크**")
                
                for i, (doc, score) in enumerate(results_with_similarity, 1):
                    with st.expander(f"결과 {i} (코사인 유사도: {score:.4f})"):
                        st.text_area(f"내용", doc.page_content, height=150, key=f"test_result_{i}")
                        st.caption(f"💡 점수가 높을수록 유사도가 높습니다 (코사인 유사도)")
                        if doc.metadata:
                            st.json(doc.metadata)
