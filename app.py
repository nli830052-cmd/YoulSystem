import streamlit as st
import json
import time
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# 저희가 완성한 에이전트와 데이터 경로를 가져옵니다.
from agent import agent_executor, ERP_DB_PATH, VIEWER_STATE_PATH, _read_json, SYSTEM_PROMPT

# 1. 웹페이지 기본 설정 (화면을 넓게 씁니다)
st.set_page_config(page_title="율시스템 AI Copilot", page_icon="🏭", layout="wide")

st.title("🏭 율시스템 I3D 플랜트 유지보수 AI Copilot")
st.markdown("**(LLM 기반 ReAct 에이전트 + MCP 로컬 데이터 연동 데모)**")
st.divider()

# --- 프리미엄 UI를 위한 커스텀 CSS 강제 주입 ---
st.markdown("""
<style>
    /* 카드형 Metric 박스 디자인 */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
    }
    /* 다크모드 호환 */
    html[data-theme="dark"] div[data-testid="metric-container"] {
        background-color: #2b2b36;
        border: 1px solid #3f3f4e;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    }
    
    /* 헤더 폰트 스타일링 */
    h1, h2, h3, h4 {
        font-family: 'Pretendard', 'Inter', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. 화면을 좌(대시보드), 우(AI 챗봇) 2개의 열(Column)로 나눕니다.
col1, col2 = st.columns([1, 1]) # 1:1 비율

# ==========================================
# 좌측 화면: 실시간 데이터 대시보드 (MCP 통신결과 확인용)
# ==========================================
with col1:
    st.subheader("📊 실시간 설비/뷰어 모니터링")
    st.info("MCP 서버를 통해 사내망(JSON) 데이터를 안전하게 읽어오는 화면입니다.")
    
    # JSON 파일 읽어오기
    erp_data = _read_json(ERP_DB_PATH)
    viewer_data = _read_json(VIEWER_STATE_PATH)
    
    # 설비 선택 드롭다운 (selectbox)
    equipment_ids = list(erp_data.keys())
    selected_eq = st.selectbox("모니터링할 설비를 선택하세요:", equipment_ids)
    
    with st.container(border=True):
        eq_info = erp_data.get(selected_eq, {})
        st.markdown(f"#### ⚙️ [{selected_eq}] {eq_info.get('name', '알 수 없는 설비')}")
        
        # Streamlit의 예쁜 상태 위젯
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        # 설비 종류별로 보여줄 주요 센서값이 다르므로 동적 할당
        if "temperature" in eq_info:
            metric_col1.metric(label="🌡️ 현재 온도", value=f"{eq_info.get('temperature')} ℃")
        elif "pressure" in eq_info:
            metric_col1.metric(label="💨 현재 압력", value=f"{eq_info.get('pressure')} bar")
        elif "voltage" in eq_info:
            metric_col1.metric(label="⚡ 현재 전압", value=f"{eq_info.get('voltage')} V")
        else:
            metric_col1.metric(label="📊 수치", value="측정됨")
        
        # 상태가 '정상'이면 초록색, 아니면 빨간색 경고 표시
        status = eq_info.get('status', '알 수 없음')
        if status == "정상":
            metric_col2.metric(label="✅ 시스템 상태", value=status)
        else:
            # 비정상일 경우 명확한 시각적 알림
            metric_col2.error(f"🚨 상태: {status}")
            
        # 마지막 점검 날짜 표시
        last_checked = eq_info.get('last_checked', '기록 없음')
        metric_col3.metric(label="📅 최근 점검일", value=last_checked)
        
    st.divider()
    
    # 3D 뷰어 카메라 좌표 상태 (카드 형태)
    with st.container(border=True):
        st.markdown("#### 🎥 3D 디지털 트윈 뷰어 카메라")
        st.write(f"**현재 포커스 대상:** `{viewer_data.get('focus_object', '없음')}`")
        coords = viewer_data.get('camera_coordinates', {})
        st.info(f"📍 **절대 좌표:** X: {coords.get('x')} | Y: {coords.get('y')} | Z: {coords.get('z')}")

# ==========================================
# 우측 화면: AI 비서 챗봇
# ==========================================
with col2:
    st.subheader("💬 AI Copilot 챗봇")
    
    # 대화 기록을 저장하는 컨테이너
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "안녕하세요! 율시스템 플랜트 유지보수 AI입니다.\n설비 점검, 매뉴얼 검색, 시스템 제어를 도와드립니다."}
        ]

    # 채팅창(높이 고정)
    chat_container = st.container(height=600)
    for msg in st.session_state.messages:
        with chat_container.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 사용자 입력 바 (맨 아래쪽)
    if prompt := st.chat_input("명령 (예: T-100 온도가 높아. 조치해줘)"):
        # 내 채팅을 추가하고 화면에 그림
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container.chat_message("user"):
            st.markdown(prompt)
            
        # AI 생각 및 행동 시작
        with chat_container.chat_message("assistant"):
            with st.spinner("AI가 매뉴얼 검색 및 시스템 제어 중입니다... ⚙️"):
                try:
                    # 대화 기록(Context)을 전부 LangChain 메시지로 변환하여 에이전트에게 전달 (기억 유지 기능)
                    langchain_messages = [SystemMessage(content=SYSTEM_PROMPT)]
                    for m in st.session_state.messages:
                        if m["role"] == "user":
                            langchain_messages.append(HumanMessage(content=m["content"]))
                        elif m["role"] == "assistant":
                            langchain_messages.append(AIMessage(content=m["content"]))
                            
                    # Agent 호출 (전체 대화 기록 전달)
                    response = agent_executor.invoke({"messages": langchain_messages})
                    raw_content = response["messages"][-1].content
                    
                    import ast
                    # 만약 raw_content 자체가 "[{'type': 'text', ...}]" 와 같은 문자열(String)로 들어온 경우 리스트로 강제 변환
                    if isinstance(raw_content, str) and raw_content.strip().startswith("[{") and raw_content.strip().endswith("}]"):
                        try:
                            raw_content = ast.literal_eval(raw_content)
                        except Exception:
                            pass
                            
                    # 리스트나 딕셔너리 구조에서 순수 텍스트만 추출
                    if isinstance(raw_content, list):
                        answer = "".join([item.get("text", "") for item in raw_content if isinstance(item, dict) and "text" in item])
                        if not answer:
                            answer = str(raw_content)
                    elif isinstance(raw_content, dict):
                        answer = raw_content.get("text", str(raw_content))
                    else:
                        answer = str(raw_content)
                        
                except Exception as e:
                    answer = f"시스템 오류: {e}"
            
            # AI 답변 출력
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # MCP가 JSON 파일을 바꿨을 테니, 1초 뒤에 웹페이지를 '새로고침' 하여 좌측 대시보드 숫자를 실시간으로 변하게 만듦
            time.sleep(1)
            st.rerun()
