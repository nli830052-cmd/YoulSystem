import json
import random

equipment_types = [
    ("T-", "가스터빈", [("temperature", "온도", "60~75℃"), ("rpm", "RPM", "30~50")]),
    ("V-", "밸브", [("pressure", "압력", "10~20 bar"), ("flow_rate", "유량", "30~80")]),
    ("P-", "펌프", [("pressure", "압력", "20~30 bar"), ("vibration", "진동", "30 미만")]),
    ("C-", "컴프레서", [("pressure", "압력", "50~70 bar"), ("temperature", "온도", "40~50℃")]),
    ("HX-", "열교환기", [("temperature_in", "입력 온도", "50~80℃"), ("temperature_out", "출력 온도", "30~60℃")]),
    ("G-", "발전기", [("voltage", "전압", "50~80V"), ("rpm", "RPM", "40~60")]),
]

erp_data = {}
manual_lines = []
total_count = 0

for type_prefix, type_name, metrics in equipment_types:
    for i in range(1, 4): # 최대 3개씩 만들되
        if total_count >= 10: # 총합 10개가 되면 강제 중단
            break
        
        total_count += 1
        eq_id = f"{type_prefix}{100+i}"
        eq_name = f"1구역 {type_name} {i}호기"
        status = "정상"
        
        # 랜덤 메트릭 생성
        eq_metrics = {m_key: round(random.uniform(10.0, 100.0), 1) for m_key, m_name, m_range in metrics}
        
        erp_data[eq_id] = {
            "name": eq_name,
            "status": status,
            **eq_metrics,
            "last_checked": "2026-03-16"
        }
        
        # 랜덤 3D 좌표 (소수점 1자리)
        x = round(random.uniform(0.0, 100.0), 1)
        y = round(random.uniform(0.0, 100.0), 1)
        z = round(random.uniform(0.0, 50.0), 1)
        
        # 매뉴얼 텍스트 데이터 작성
        manual_entry = f"[{eq_name} ({eq_id}) 유지보수 매뉴얼]\n"
        manual_entry += f"- 개요: 1구역에서 작동하는 {type_name} 설비입니다.\n"
        
        # [NEW] 정상 범위 정보 추가 (환각 방지용)
        manual_entry += "- [정상 작동 기준(기술 데이터시트)]:\n"
        for m_key, m_name, m_range in metrics:
             manual_entry += f"  * 정상 {m_name}: {m_range}\n"
        
        # 설비 종류별 조치 가이드
        metric_keys = [m[0] for m in metrics]
        if "temperature" in metric_keys or "temperature_in" in metric_keys:
            manual_entry += f"- [고온 경고 조치]: 현재 온도가 정상 기준을 벗어났을 경우 즉시 작동을 중지하고 ERP 시스템 상태를 '점검 요망'으로 변경하세요. 냉각수 라인 누수를 점검해야 합니다.\n"
        if "pressure" in metric_keys:
            manual_entry += f"- [과압/압력 이상 조치]: 현재 압력이 정상 기준을 벗어났을 경우 즉시 바이패스 밸브를 개방하여 압력을 낮추십시오. ERP 상태를 '수리 중'으로 변경하여 2차 피해를 막으세요.\n"
        if "vibration" in metric_keys:
            manual_entry += f"- [진동 이상 조치]: 진동 수치가 정상을 초과할 경우 베어링 마모 또는 파손이 의심됩니다. 설비를 멈추고 '수리 중'으로 상태를 갱신하세요.\n"
        if "voltage" in metric_keys:
            manual_entry += f"- [전압 이상 조치]: 정상 전압 범위를 벗어나면 즉각 차단기를 내리고 상태를 '점검 요망'으로 전환하세요.\n"
            
        manual_entry += f"- [3D 디지털 트윈 연동 좌표]: 해당 {eq_id} 설비의 3D 공간 상 절대 위치는 X: {x}, Y: {y}, Z: {z} 입니다. 3D 뷰어 카메라를 이 위치로 이동시켜 현장 상황을 시각적으로 확인하세요.\n"
        manual_entry += "=" * 50 + "\n\n"
        
        manual_lines.append(manual_entry)

# 1. ERP DB 덮어쓰기 (30개 장비)
with open("c:/YoulSystem/data/erp_db.json", "w", encoding="utf-8") as f:
    json.dump(erp_data, f, ensure_ascii=False, indent=2)

# 2. 매뉴얼 텍스트 덮어쓰기 (30개 매뉴얼)
with open("c:/YoulSystem/data/manuals/turbine_manual.txt", "w", encoding="utf-8") as f:
    f.writelines(manual_lines)

print("✅ 성공: '정상 센서 수치 스펙'이 포함된 30개의 장비 데이터(ERP)와 매뉴얼 텍스트가 업데이트 되었습니다!")
