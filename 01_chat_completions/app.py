import streamlit as st
from langchain_upstage import ChatUpstage

st.set_page_config(page_title="Chat Completions", page_icon="💬", layout="wide")
st.title("💬 Chat Completions (LangChain)")

api_key = st.sidebar.text_input("Upstage API Key", type="password")

# API 키 검증
if not api_key:
    st.warning("왼쪽 사이드바에서 API Key를 입력해주세요.")
else:
    # 세션 초기화 버튼
    if st.sidebar.button("🔄 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("⚙️ 설정 및 실행")
        
        model = st.selectbox(
            "모델 선택",
            ["solar-pro3", "solar-pro2", "solar-mini"],
            index=0,
            help="""
            • solar-pro3: 최신 고성능 모델 (solar-pro3-260126)
            • solar-pro2: 이전 버전 고성능 모델 (solar-pro2-251215)
            • solar-mini: 빠르고 경량화된 모델 (solar-mini-250422)
            """
        )
        
        # Reasoning Effort 설정 (모델별 옵션 다름)
        reasoning_effort = None
        if model in ["solar-pro3", "solar-pro2"]:
            if model == "solar-pro3":
                options = ["low", "medium", "high"]
                default_idx = 1
                help_text = """
                복잡한 문제 해결을 위한 추론 레벨 제어
                
                solar-pro3 (동적 추론 예산):
                • high: 복잡한 문제에 최적_reasoning 가능
                • medium: 균형잡힌 추론_reasoning 가능 (기본값)
                • low: 추론 없음, 가장 빠른 응답
                """
            else:
                options = ["minimal", "high"]
                default_idx = 0
                help_text = """
                복잡한 문제 해결을 위한 추론 레벨 제어
                
                solar-pro2:
                • high: 추론 활성화_reasoning 가능
                • minimal: 추론 비활성화_reasoning 가능 (기본값)
                
                참고: medium은 high로, low는 minimal로 취급됨
                """
            
            reasoning_effort = st.selectbox(
                "Reasoning Effort",
                options,
                index=default_idx,
                help=help_text
            )
        
        with st.expander("⚙️ 샘플링 파라미터", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                temperature = st.slider(
                    "Temperature",
                    0.0, 2.0, 0.8, 0.1,
                    help="""
                    샘플링 온도 - 출력의 무작위성 제어
                    
                    • 높은 값 (0.8): 더 무작위적인 출력
                    • 낮은 값 (0.2): 집중되고 결정적인 출력
                    
                    기본값: 0.8 (solar-pro3)
                    범위: 0~2
                    """
                )
                
                top_p = st.slider(
                    "Top P (Nucleus Sampling)",
                    0.0, 1.0, 0.95, 0.05,
                    help="""
                    누적 확률 기반 토큰 샘플링
                    
                    • 0.1: 상위 10% 확률 토큰만 고려
                    • 0.95: 상위 95% 확률 토큰 고려
                    
                    기본값: 0.95 (solar-pro3)
                    범위: 0~1
                    """
                )
            
            with col2:
                frequency_penalty = st.slider(
                    "Frequency Penalty",
                    -2.0, 2.0, 1.1, 0.1,
                    help="""
                    토큰 반복 빈도 제어
                    
                    • 양수 (1.5): 반복 감소, 다양성 증가
                    • 0: 페널티 없음
                    • 음수 (-1.0): 반복 허용
                    
                    기본값: 1.1
                    범위: -2.0~2.0
                    """
                )
                
                presence_penalty = st.slider(
                    "Presence Penalty",
                    -2.0, 2.0, 0.0, 0.1,
                    help="""
                    이미 등장한 토큰의 재등장 제어
                    
                    • 양수 (1.5): 새로운 주제로 유도
                    • 0: 페널티 없음
                    • 음수 (-1.0): 기존 토큰 재사용 장려
                    
                    frequency_penalty와 차이: 빈도가 아닌 존재 여부에 초점
                    기본값: 0
                    범위: -2.0~2.0
                    """
                )
        
        with st.expander("🔧 생성 제어", expanded=True):
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=1,
                max_value=32768,
                value=4096,
                help="""
                생성할 최대 토큰 수 제한
                """
            )
            
            streaming = st.checkbox(
                "스트리밍 활성화",
                value=True,
                help="""
                실시간 응답 스트리밍
                
                • true: 토큰 단위로 실시간 전송 (SSE)
                • false: 완성된 응답을 한 번에 전송
                
                기본값: false
                """
            )
        
        with st.expander("📋 고급 설정", expanded=False):
            response_format_type = st.selectbox(
                "Response Format",
                ["text", "json_object", "json_schema"],
                help="""
                모델 출력 형식 지정
                
                • text: 일반 텍스트
                • json_object: JSON 형식 (스키마 없음, 프롬프트에 'JSON' 필수)
                • json_schema: 사용자 정의 스키마 기반 JSON (Structured outputs)
                
                호환성: 모든 모델 지원
                """
            )
            
            json_schema_input = None
            if response_format_type == "json_schema":
                json_schema_input = st.text_area(
                    "JSON Schema",
                    '''{"name": "response_schema", "strict": true, "schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"], "additionalProperties": false}}''',
                    help="출력 구조를 정의하는 JSON 스키마 (name 필드 필수)"
                )
            
            st.divider()
            
            use_tools = st.checkbox(
                "Function Calling 활성화",
                value=False,
                help="외부 API, 데이터베이스, 함수 호출 기능 활성화"
            )
            
            tools_input = None
            tool_choice = "auto"
            parallel_tool_calls = True
            
            if use_tools:
                st.info("💡 편의상 mock function을 사용합니다. 실제 환경에서는 API 호출이나 DB 쿼리로 대체하세요.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🌡️ 날씨 API 예시 로드"):
                        st.session_state['tools_example'] = 'weather'
                        st.rerun()
                
                with col2:
                    if st.button("❌ 예시 제거"):
                        if 'tools_example' in st.session_state:
                            del st.session_state['tools_example']
                        st.rerun()
                
                if st.session_state.get('tools_example') == 'weather':
                    tools_input = '''[
  {
    "type": "function",
    "function": {
      "name": "get_current_weather",
      "description": "Get the current weather in a given location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "The city and state, e.g. San Francisco, CA"
          },
          "unit": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"]
          }
        },
        "required": ["location"]
      }
    }
  }
]'''
                    with st.expander("📝 Tools 정의 (JSON)", expanded=True):
                        st.code(tools_input, language='json')
                        st.caption("🔹 함수: get_current_weather")
                        st.caption("🔹 파라미터: location (필수), unit (선택)")
                        st.caption("💡 추천 메시지: What's the weather like in Seoul?")
                else:
                    tools_input = None
                    st.warning("⬆️ 위에서 예시를 로드하세요.")
                
                col1, col2 = st.columns(2)
                with col1:
                    tool_choice = st.selectbox(
                        "Tool Choice",
                        ["auto", "none", "required"],
                        help="""
                        • auto: 모델이 자동 선택
                        • none: 함수 호출 안함
                        • required: 반드시 함수 호출
                        """
                    )
                
                with col2:
                    if model == "solar-pro3":
                        parallel_tool_calls = st.checkbox(
                            "Parallel Tool Calls",
                            value=True,
                            help="여러 함수를 동시에 호출 (solar-pro3 전용) - LangChain 미지원"
                        )
                        if parallel_tool_calls:
                            st.warning("⚠️ LangChain에서 parallel_tool_calls 파라미터를 지원하지 않습니다.")
                    else:
                        st.info("Parallel tool calls: solar-pro3 전용")
            
            prompt_cache_key = st.text_input(
                "Prompt Cache Key",
                "",
                help="""
                프롬프트 캐싱을 위한 고유 키
                
                대화 컨텍스트별로 고유 키 사용 권장
                기본값: null
                """
            )
        
        st.subheader("📝 메시지 입력")
        system_prompt = st.text_area(
            "시스템 프롬프트",
            "당신은 친절한 AI 어시스턴트입니다.",
            help="AI의 역할, 행동 방식, 제약사항을 정의합니다."
        )
        
        default_user_message = "안녕하세요!" if response_format_type == "text" else "사용자 정보를 JSON 형식으로 생성해주세요."
        user_message = st.text_area(
            "사용자 메시지",
            default_user_message,
            help="AI에게 전달할 질문이나 요청을 입력하세요."
        )
        
        if response_format_type in ["json_object", "json_schema"] and "json" not in user_message.lower():
            st.warning("⚠️ JSON 출력을 사용하려면 메시지에 'JSON' 단어를 포함해야 합니다.")
        
        if st.button("전송", type="primary"):
            try:
                # JSON 파싱 사전 검증
                import json
                parsed_tools = None
                parsed_schema = None
                
                if use_tools and tools_input:
                    try:
                        parsed_tools = json.loads(tools_input)
                    except json.JSONDecodeError as e:
                        st.error(f"❌ Tools JSON 파싱 오류: {e}")
                        st.stop()
                
                if response_format_type == "json_schema" and json_schema_input:
                    try:
                        parsed_schema = json.loads(json_schema_input)
                    except json.JSONDecodeError as e:
                        st.error(f"❌ JSON Schema 파싱 오류: {e}")
                        st.stop()
                
                # LLM 기본 파라미터 설정
                llm_params = {
                    "api_key": api_key,
                    "model": model,
                    "temperature": temperature,
                    "top_p": top_p,
                    "frequency_penalty": frequency_penalty,
                    "presence_penalty": presence_penalty,
                    "max_tokens": max_tokens
                }
                
                # 추가 파라미터 (model_kwargs) 구성
                model_kwargs = {}
                if reasoning_effort:
                    if model == "solar-pro3":
                        model_kwargs["reasoning_effort"] = reasoning_effort
                    elif model == "solar-pro2":
                        model_kwargs["reasoning_effort"] = reasoning_effort
                
                if response_format_type == "json_object":
                    model_kwargs["response_format"] = {"type": "json_object"}
                elif response_format_type == "json_schema" and parsed_schema:
                    model_kwargs["response_format"] = {
                        "type": "json_schema",
                        "json_schema": parsed_schema
                    }
                
                # Function Calling 설정
                if use_tools and parsed_tools:
                    model_kwargs["tools"] = parsed_tools
                    model_kwargs["tool_choice"] = tool_choice
                
                if prompt_cache_key:
                    model_kwargs["prompt_cache_key"] = prompt_cache_key
                
                if model_kwargs:
                    llm_params["model_kwargs"] = model_kwargs
                
                llm = ChatUpstage(**llm_params)
                
                # 메시지 구성
                messages = [
                    ("system", system_prompt),
                    ("human", user_message)
                ]
                
                # 응답 변수 초기화
                full_response = ""
                response = None
                
                st.subheader("💬 응답:")
                
                # 스트리밍 모드 (툴 호출 제외)
                if streaming and not use_tools:
                    with st.spinner("🔄 응답 생성 중..."):
                        response_placeholder = st.empty()
                        chunks = []
                        
                        for chunk in llm.stream(messages):
                            chunks.append(chunk)
                            full_response += chunk.content
                            response_placeholder.markdown(full_response + "▌")
                        
                        response_placeholder.markdown(full_response)
                        
                        # 디버깅 정보
                        if not full_response:
                            st.error(f"❌ 응답이 비어있습니다! 총 {len(chunks)}개 청크 수신, content 길이: {sum(len(c.content) for c in chunks)}")
                        
                        # 마지막 청크에서 메타데이터 추출
                        for i in range(len(chunks)-1, -1, -1):
                            chunk = chunks[i]
                            if hasattr(chunk, 'response_metadata') and chunk.response_metadata:
                                response = chunk
                                break
                else:
                    # 일반 모드 (invoke)
                    # reasoning 사용 여부 확인
                    use_reasoning = False
                    if reasoning_effort:
                        if (model == "solar-pro3" and reasoning_effort != "low") or \
                           (model == "solar-pro2" and reasoning_effort != "minimal"):
                            use_reasoning = True
                    
                    spinner_msg = "🧠 추론 중..." if use_reasoning else "💬 응답 생성 중..."
                    
                    with st.spinner(spinner_msg):
                        response = llm.invoke(messages)
                        full_response = response.content  # invoke 모드에서도 설정
                    
                    # Function Calling 처리
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        st.success("🔧 모델이 함수 호출을 요청했습니다.")
                        for i, tc in enumerate(response.tool_calls, 1):
                            with st.expander(f"함수 호출 #{i}: {tc.get('name', 'unknown')}"):
                                st.json(tc)
                        
                        # 더미 함수 실행 시뮬레이션
                        st.divider()
                        st.subheader("🔄 함수 실행 및 최종 응답")
                        
                        # Mock 함수 정의 (실제 환경에서는 API 호출로 대체)
                        def get_current_weather(location, unit="fahrenheit"):
                            import json
                            if "seoul" in location.lower():
                                return json.dumps({"location": "Seoul", "temperature": "10", "unit": unit})
                            elif "san francisco" in location.lower():
                                return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
                            elif "paris" in location.lower():
                                return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
                            else:
                                return json.dumps({"location": location, "temperature": "unknown"})
                        
                        # 대화 히스토리에 AI 응답 추가
                        from langchain_core.messages import AIMessage, ToolMessage
                        messages.append(AIMessage(content="", tool_calls=response.tool_calls))
                        
                        # 각 함수 호출 실행 및 결과 수집
                        for tc in response.tool_calls:
                            function_name = tc.get('name')
                            function_args = tc.get('args', {})
                            
                            st.info(f"▶️ 함수 실행: {function_name}({function_args})")
                            
                            # 더미 함수 호출
                            if function_name == "get_current_weather":
                                result = get_current_weather(**function_args)
                                st.code(result, language='json')
                                
                                # 결과를 메시지에 추가
                                messages.append(ToolMessage(
                                    content=result,
                                    tool_call_id=tc.get('id')
                                ))
                        
                        # 함수 실행 결과를 바탕으로 최종 응답 생성
                        st.info("🤖 함수 결과를 바탕으로 최종 응답 생성 중...")
                        
                        # 기본 파라미터 재사용 (tools 제외)
                        final_params = {k: v for k, v in llm_params.items() if k != 'model_kwargs'}
                        final_llm = ChatUpstage(**final_params)
                        
                        if streaming:
                            response_placeholder = st.empty()
                            full_response = ""
                            for chunk in final_llm.stream(messages):
                                full_response += chunk.content
                                response_placeholder.markdown(full_response + "▌")
                            response_placeholder.markdown(full_response)
                        else:
                            final_response = final_llm.invoke(messages)
                            st.markdown(final_response.content)
                    
                    elif response.content:
                        st.markdown(response.content)
                    else:
                        st.warning("응답 컨텐츠가 비어있습니다. 함수 호출만 발생했을 수 있습니다.")
                
                # 응답 메타데이터 표시
                with st.expander("📝 전체 응답 로그"):
                    if response:
                        # 원본 response 객체를 dict로 변환
                        import json
                        
                        # LangChain response 객체를 dict로 변환
                        if hasattr(response, 'dict'):
                            response_dict = response.dict()
                        elif hasattr(response, 'model_dump'):
                            response_dict = response.model_dump()
                        else:
                            response_dict = vars(response)
                        
                        # JSON 원문 표시
                        st.code(json.dumps(response_dict, indent=2, ensure_ascii=False, default=str), language='json')
                        
                        # reasoning_tokens 표시 (편의 기능)
                        metadata = response.response_metadata if hasattr(response, 'response_metadata') else {}
                        token_usage = metadata.get('token_usage')
                        if token_usage:
                            completion_details = token_usage.get('completion_tokens_details', {})
                            reasoning_tokens = completion_details.get('reasoning_tokens')
                            
                            if reasoning_tokens:
                                st.success(f"🧠 reasoning_tokens: {reasoning_tokens:,}")
                    else:
                        st.warning("⚠️ 응답 객체가 없습니다. 스트리밍 중 메타데이터를 받지 못했을 수 있습니다.")
                        if full_response:
                            st.info(f"생성된 응답: {full_response}")
                    
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    with col_right:
        st.subheader("💻 생성된 코드")
        
        # 실제 파라미터 구성
        import json
        
        preview_params = {
            "api_key": "YOUR_API_KEY",
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "max_tokens": max_tokens
        }
        
        preview_kwargs = {}
        if reasoning_effort:
            if model == "solar-pro3":
                preview_kwargs["reasoning_effort"] = reasoning_effort
            elif model == "solar-pro2":
                preview_kwargs["reasoning_effort"] = reasoning_effort
        
        if response_format_type == "json_object":
            preview_kwargs["response_format"] = {"type": "json_object"}
        elif response_format_type == "json_schema" and json_schema_input:
            try:
                preview_kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": json.loads(json_schema_input)
                }
            except json.JSONDecodeError:
                st.warning("⚠️ JSON Schema 파싱 오류")
                preview_kwargs["response_format"] = {"type": "json_schema", "json_schema": {}}
        
        if use_tools and tools_input:
            try:
                preview_kwargs["tools"] = json.loads(tools_input)
                preview_kwargs["tool_choice"] = tool_choice
            except json.JSONDecodeError:
                st.warning("⚠️ Tools JSON 파싱 오류")
        
        if prompt_cache_key:
            preview_kwargs["prompt_cache_key"] = prompt_cache_key
        
        if preview_kwargs:
            preview_params["model_kwargs"] = preview_kwargs
        
        # 코드 생성
        params_str = json.dumps(preview_params, indent=4, ensure_ascii=False)
        stream_code = "for chunk in llm.stream(messages):\n    print(chunk.content, end='', flush=True)" if streaming else "response = llm.invoke(messages)\nprint(response.content)"
        
        code = f'''from langchain_upstage import ChatUpstage

# 파라미터 설정
params = {params_str}

# ChatUpstage 모델 초기화
llm = ChatUpstage(**params)

# 메시지 구성
messages = [
    ("system", """{system_prompt}"""),
    ("human", """{user_message}""")
]

# {'스트리밍' if streaming else '일반'} 응답
{stream_code}
'''
        st.code(code, language='python')
