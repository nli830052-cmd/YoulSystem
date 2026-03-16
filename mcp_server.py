import json
import os
from mcp.server.fastmcp import FastMCP

# 1. MCP 서버 초기화
# 이 서버의 이름은 "YoulSystem_MCP" 입니다.
mcp = FastMCP("YoulSystem_MCP")

# 파일 경로 고정 (안전하게 이 파일들만 접근 가능)
ERP_DB_PATH = "./data/erp_db.json"
VIEWER_STATE_PATH = "./data/3d_viewer_state.json"

def _read_json(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _write_json(file_path: str, data: dict):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================================================
# 2. LLM이 사용할 수 있는 "안전한 도구(Tool)" 3가지 정의
# ==========================================================

@mcp.tool()
def get_equipment_status(equipment_id: str) -> str:
    """
    [ERP 시스템 연동] 특정 설비(예: T-100, V-102)의 현재 상태와 센서 값을 조회합니다.
    """
    db = _read_json(ERP_DB_PATH)
    if equipment_id in db:
        return json.dumps(db[equipment_id], ensure_ascii=False)
    return f"오류: {equipment_id} 에 해당하는 설비가 ERP에 존재하지 않습니다."

@mcp.tool()
def update_equipment_status(equipment_id: str, new_status: str) -> str:
    """
    [ERP 시스템 연동] 특정 설비의 관리 상태(status)를 새로운 값(예: "점검 요망", "작동 중")으로 업데이트합니다.
    """
    db = _read_json(ERP_DB_PATH)
    if equipment_id in db:
        old_status = db[equipment_id]["status"]
        db[equipment_id]["status"] = new_status
        _write_json(ERP_DB_PATH, db)
        return f"성공! {equipment_id} 설비 상태 변경: '{old_status}' -> '{new_status}'"
    return f"업데이트 실패: {equipment_id} 설비를 찾을 수 없습니다."

@mcp.tool()
def set_3d_camera_focus(x: float, y: float, z: float) -> str:
    """
    [3D Viewer 연동] 3D 디지털 트윈 화면의 카메라 좌표를 특정 X, Y, Z 위치로 즉각 이동시킵니다.
    """
    state_data = _read_json(VIEWER_STATE_PATH)
    state_data["camera_coordinates"] = {
        "x": x,
        "y": y,
        "z": z
    }
    state_data["focus_object"] = "AI_Auto_Focused_Area"
    _write_json(VIEWER_STATE_PATH, state_data)
    
    return f"3D 카메라 위치 조정 완료. 현재 좌표: (X: {x}, Y: {y}, Z: {z})"

# 3. 메인 실행부
if __name__ == "__main__":
    print("🛡️ 율시스템 전용 MCP 서버 부팅 완료! 대기 중...")
    # 표준 입출력(stdio)을 통해 보안 통신을 시작합니다.
    mcp.run()
