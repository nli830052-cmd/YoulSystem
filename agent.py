import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool

from langchain_core.messages import HumanMessage
from rag_pipeline import build_rag_db

# ==========================================
# 🛑 중요: 여기에 Gemini API 키를 입력하세요! (Google AI Studio에서 무료 발급 가능)
# ==========================================
os.environ["GOOGLE_API_KEY"] = "AIzaSyAMuHYvCcADicZVo00CHdocDsQESgGnAOs" # 이곳을 지우고 본인의 Gemini API 키를 붙여넣으세요!

# 1. RAG (문서 검색) 시스템 연동
print("🚀 [1단계] RAG 지식 데이터베이스 로딩 중...")
vectorstore = build_rag_db()
if vectorstore is None:
    raise Exception("Vector DB(Chroma)에 접속할 수 없습니다. RAG 파이프라인부터 다시 실행해주세요.")

rag_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

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
    docs = rag_retriever.invoke(query)
    return "\n".join([doc.page_content for doc in docs])

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

# 에이전트에게 4가지 손발(도구)을 달아줍니다.
tools = [
    search_maintenance_manual, 
    get_equipment_status, 
    update_equipment_status, 
    set_3d_camera_focus
]

# 스스로 생각하고(Thought) 행동(Action)할 수 있는 ReAct 구조의 에이전트 생성
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
    
    # 에이전트 실행!
    response = agent_executor.invoke({"messages": [HumanMessage(content=user_prompt)]})
    
    print("\n" + "="*50)
    print("💡 [최종 AI 답변]")
    print(response["messages"][-1].content)
    print("="*50)
    
    print("\n✅ 실제 파일에 잘 반영되었는지 확인해보세요: data/erp_db.json 및 data/3d_viewer_state.json")
