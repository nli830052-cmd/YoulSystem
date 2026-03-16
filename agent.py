import os
import json
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool

from langchain_core.messages import HumanMessage
from rag_pipeline import load_rag_db

# ==========================================
# 🛑 중요: 여기에 Gemini API 키를 입력하세요! (Google AI Studio에서 무료 발급 가능)
# ==========================================
os.environ["GOOGLE_API_KEY"] = "AIzaSyAMuHYvCcADicZVo00CHdocDsQESgGnAOs" # 이곳을 지우고 본인의 Gemini API 키를 붙여넣으세요!

# 1. RAG (문서 검색) 시스템 연동
print("🚀 [1단계] RAG 지식 데이터베이스 로딩 중...")
vectorstore = load_rag_db()
if vectorstore is None:
    raise Exception("Vector DB(Chroma)에 접속할 수 없습니다. RAG 파이프라인부터 다시 실행해주세요.")

# 1차망: 벡터 유사도 검색으로 여유있게 후보군 10개를 넉넉히 가져옵니다.
rag_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# ==========================================
# 2. 요원의 도구(Tool) 정의 (MCP 기반 제어 흉내내기)
# ==========================================
ERP_DB_PATH = "./data/erp_db.json"
VIEWER_STATE_PATH = "./data/3d_viewer_state.json"

def _read_json(file_path: dict) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(file_path: str, data: dict):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@tool
def search_maintenance_manual(query: str) -> str:
    """
    [지식 검색 도구] 설비의 고장 대처법, 조치 메뉴얼, 3D 좌표 등을 알고 싶을 때 무조건 가장 먼저 이 도구를 사용하여 검색하세요.
    """
    # 1. 벡터 검색 (의미 기반) - 10개 확보
    docs = rag_retriever.invoke(query)
    
    # 2. 정규표현식(Regex)을 이용한 고유 설비 번호 추출 (예: t-101, V-102, HX-105 등 소문자 포함)
    # 패턴: [영대문자/소문자 1~2개]-[숫자 3자리] -> 사용자 입력이 1구역 t-101 이어도 감지 가능
    equip_id_match = re.search(r'[a-zA-Z]{1,2}-\d{3}', query)
    
    if equip_id_match:
        # 매뉴얼 원본 문서에는 'T-101'처럼 무조건 대문자로 적혀 있으므로, 
        # 추출한 소문자 문자열(예: 't-101')을 .upper()를 이용해 대문자('T-101')로 강제 변환
        target_id = equip_id_match.group().upper()
        
        # 3. 하이브리드 재정렬 (Re-ranking): 추출된 키워드(T-101 등)가 실제로 본문에 있는 문서만 최우선으로 올림
        exact_match_docs = [doc for doc in docs if target_id in doc.page_content]
        other_docs = [doc for doc in docs if target_id not in doc.page_content]
        
        # 키워드 일치 문서를 상단에 배치하고, 나머지는 뒤로 붙임
        sorted_docs = exact_match_docs + other_docs
        
        # 최종적으로 상위 3개만 AI에게 전달하여 혼란(환각)을 방지
        final_docs = sorted_docs[:3]
    else:
        # 설비 번호가 없는 일반적인 질문이면 원래 벡터 검색 점수대로 상위 3개만 전달
        final_docs = docs[:3]
        
    return "\n\n".join([doc.page_content for doc in final_docs])

@tool
def get_equipment_status(equipment_id: str) -> str:
    """
    [ERP 시스템 도구] 특정 설비(예: T-100, V-102)의 현재 온도, 압력, 상태를 조회할 때 사용합니다.
    """
    db = _read_json(ERP_DB_PATH)
    if equipment_id in db:
        return json.dumps(db[equipment_id], ensure_ascii=False)
    return f"오류: {equipment_id} 설비를 찾을 수 없습니다."

@tool
def get_all_equipment_summary() -> str:
    """
    [ERP 시스템 도구] 전체 장비의 기본 정보(ID, 이름, 상태, 최근 점검일 등) 목록을 한 번에 조회합니다.
    "특정 날짜에 점검된 장비를 찾아줘" 또는 "수리 중인 장비를 모두 알려줘"와 같이 전체 현황을 파악해야 할 때 이 도구를 사용하세요.
    """
    db = _read_json(ERP_DB_PATH)
    summary = []
    for eq_id, info in db.items():
        summary.append(f"- ID: {eq_id} | 이름: {info.get('name')} | 상태: {info.get('status')} | 최근 점검일: {info.get('last_checked')}")
    return "\n".join(summary)

@tool
def update_equipment_status(equipment_id: str, new_status: str) -> str:
    """
    [ERP 시스템 도구] 가이드라인에 따라 특정 장비의 상태(status)를 "점검 요망" 또는 "수리 중" 등으로 변경할 때 사용합니다.
    """
    db = _read_json(ERP_DB_PATH)
    if equipment_id in db:
        db[equipment_id]["status"] = new_status
        _write_json(ERP_DB_PATH, db)
        return f"성공! {equipment_id} 설비 상태가 '{new_status}'로 업데이트 되었습니다."
    return f"업데이트 실패: {equipment_id} 설비를 찾을 수 없습니다."

@tool
def set_3d_camera_focus(coords: str) -> str:
    """
    [3D Viewer 도구] 3D 디지털 트윈 화면의 카메라 좌표를 즉시 이동시킵니다. 
    입력값은 반드시 "X좌표,Y좌표,Z좌표" 형태의 문자열(예: "15.2,30.5,5.0")이어야 합니다.
    """
    try:
        x, y, z = map(float, coords.split(","))
        state_data = _read_json(VIEWER_STATE_PATH)
        state_data["camera_coordinates"] = {"x": x, "y": y, "z": z}
        state_data["focus_object"] = "AI_Auto_Focused_Area"
        _write_json(VIEWER_STATE_PATH, state_data)
        return f"3D 카메라 이동 완료. 현재 좌표: (X: {x}, Y: {y}, Z: {z})"
    except Exception as e:
        return "좌표 입력 형식이 잘못되었습니다. 'x,y,z' 형식으로 입력하세요."

# 3. 브레인(LLM) 및 에이전트 결합
print("🚀 [2단계] AI Agent 두뇌 활성화 중...")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)

# 에이전트에게 5가지 손발(도구)을 달아줍니다.
tools = [
    search_maintenance_manual, 
    get_equipment_status, 
    get_all_equipment_summary,
    update_equipment_status, 
    set_3d_camera_focus
]

# AI가 환각(Hallucination)을 일으키지 못하도록 강력한 가드레일(시스템 프롬프트)을 작성합니다.
SYSTEM_PROMPT = """
당신은 율시스템(YoulSystem)의 I3D 플랜트 유지보수 AI Copilot입니다.
다음의 규칙을 '절대적'으로 준수해야 합니다:
1. [환각 방지]: 당신이 가진 도구(Tool)를 사용해서 얻은 결과값에 없는 정보는 절대 유추하거나 지어내지 마세요.
2. 만약 도구를 사용했는데도 원하는 설비나 데이터가 존재하지 않는다면, 
   반드시 "현재 시스템 데이터 상에 해당 정보가 존재하지 않습니다." 또는 "모르겠습니다."라고 있는 그대로만 대답하세요.
3. 임의의 날짜, 수치, 조치 방법을 인터넷에서 학습한 사전 지식으로 마음대로 채워 넣으면 대형 사고가 발생합니다.
"""

# 스스로 생각하고(Thought) 행동(Action)할 수 있는 ReAct 구조의 에이전트 생성 (버전 충돌 방지를 위해 인자 제거)
agent_executor = create_react_agent(llm, tools)

# 4. 모의 상황 실행 (사용자 명령)
if __name__ == "__main__":
    print("\n" + "="*50)
    print(" 🤖 율시스템 플랜트 유지보수 AI Copilot 🤖 ")
    print("="*50 + "\n")
    
    # 🚨 모의 시나리오 질문:
    user_prompt = "1구역의 가스터빈(T-100) 온도가 너무 높다고 경고가 떴어. 매뉴얼을 찾아보고 필요한 시스템 조치를 모두 취해줘."
    
    print(f"👤 작업자 명령: {user_prompt}\n")
    print("="*20 + " [AI 에이전트의 자율 문제 해결(Reasoning & Action)] " + "="*20)
    
    # 에이전트 실행! (대화 기록 맨 앞에 시스템 프롬프트를 시스템 메시지로 삽입)
    from langchain_core.messages import SystemMessage
    response = agent_executor.invoke({"messages": [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ]})
    
    print("\n" + "="*50)
    print("💡 [최종 AI 답변]")
    print(response["messages"][-1].content)
    print("="*50)
    
    print("\n✅ 실제 파일에 잘 반영되었는지 확인해보세요: data/erp_db.json 및 data/3d_viewer_state.json")
