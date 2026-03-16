# AI Agent for Digital Twin-based Plant Maintenance

본 문서는 율시스템 면접 대비용 토이 프로젝트의 전체 진행 흐름과 **현재까지 완료된 단계별 작업 내역**을 문서화한 것입니다.

---

## 🚀 전체 프로젝트 단계 (Project Flow)

- [x] **도메인 분석 및 기획서 작성** (율시스템 비즈니스 모델 및 JD 분석)
- [x] **[STEP 1] Mock 데이터 구축** (가상 ERP / 3D 뷰어 JSON 및 유지보수 매뉴얼 생성)
- [x] **[STEP 2] RAG 시스템 구축** (설비 매뉴얼 텍스트 임베딩 및 VectorDB 검색기 테스트)
- [x] **[STEP 3] MCP 서버 구축** (ERP 및 3D JSON 파일 제어용 Python MCP Tool 개발)
- [x] **[STEP 4] AI Agent 통합** (LangChain + LLM + RAG + MCP 연동 및 자율 워크플로우 테스트)
- [x] **[STEP 5] 대시보드 웹 구현** (Streamlit 기반 실시간 관제 UI 및 AI 챗봇 통합)

---

## ✅ 상세 진행 내역 (Completed Tasks)

### [기획 완료] 솔루션 아키텍처 제안
- **대상:** 율시스템 비즈니스(원자력/플랜트 기반 I3D 플랫폼) 타겟 다운
- **핵심 기술:** 회사 JD 100% 반영 (LLM 기반 RAG 확보, MCP 안전한 접근 증명, AI 에이전트 자동화 구현)
- **개발 환경 최적화 설계:** AMD Ryzen CPU / 4GB VRAM 환경에서도 끊김없이 구동할 수 있도록, 무거운 DB 및 3D 툴 대신 **가벼운 JSON 기반 상태 제어** 및 가벼운 로컬 벡터 저장소(ChromaDB) 선택

### [STEP 1 완료] 가상 상태 데이터 세팅
실제 무거운 시스템을 대신하여 상황을 모사(Mocking)할 수 있는 핵심 파일 3개를 생성 및 셋업했습니다.

1. `data/erp_db.json` 생성 완료
   - **역할:** 사내 Legacy 시스템(SAP/ERP)의 설비 데이터 시뮬레이션
   - **내용:** 1구역의 핵심 가스터빈(T-100) 및 밸브(V-102)의 "정상" 상태값과 온도, 압력 데이터 기록

2. `data/3d_viewer_state.json` 생성 완료
   - **역할:** intelli3D Webviewer(디지털 트윈) 시뮬레이션
   - **내용:** 작업자 화면의 3D 공간 상 카메라 좌표(X, 0, Y: 0, Z: 10) 초기 상태 기록

3. `data/manuals/turbine_manual.txt` 생성 완료
   - **역할:** AI가 RAG 파이프라인으로 검색할 지식 문서 확보
   - **내용:** T-100의 비정상 온도 상승 시 즉각 조치 매뉴얼과, 해당 설비의 3D 공간상 절대 좌표(X: 15.2, Y: 30.5, Z: 5.0) 가이드 포함

---

### [STEP 2 완료] RAG (문서 지식 검색) 시스템 코딩
1. 파이썬 가상환경 의존성(`requirements.txt`) 구성 및 충돌 해결 완료.
2. `turbine_manual.txt` 데이터 로딩하여 로컬 CPU 전용 초경량 임베딩 모델(`jhgan/ko-sroberta-multitask`) 기반 벡터 변환 수행.
3. ChromaDB에 지식 섭취 완료 후, 자연어 질의("V-102 밸브 압력이 이상할 때 어떻게 해?")에 대한 1순위 문서 검색 기능 자체 테스트 성공.

### [STEP 3 완료] MCP 서버 (보안 접근) 시스템 구축
1. Anthropic의 `FastMCP` 라이브러리를 사용해 "YoulSystem_MCP" 라는 통신/보안 서버 구축(`mcp_server.py`).
2. 외부 AI가 내부 `JSON` 파일(ERP 데이터, 3D 뷰어 상태)을 임의로 망칠 수 없도록, 내부 함수를 거쳐서만 접근 가능하도록 캡슐화.
3. AI Agent가 자율적으로 판단하여 사용할 3개의 필수 "도구(Tool/API)" 정의:
   - `get_equipment_status`: 장비의 현재 상태(온도, 압력 등) 조회
   - `update_equipment_status`: 조치 가이드에 따라 장비를 "점검 요망"이나 "수리 중"으로 상태값 덮어쓰기
   - `set_3d_camera_focus`: 매뉴얼에 명시된 특정 X, Y, Z 좌표로 3D 도면의 카메라 위치를 즉시 동기화

---

### [STEP 4 완료] 대망의 AI Agent 통합 (ReAct Framework)
1. **API Key 및 LLM 연동:** OpenAI(GPT-4o-mini 등) 또는 호환 가능한 LLM API를 연결하여 ReAct 에이전트의 "지능(두뇌)" 역할 수행.
2. **도구(Tool) 권한 부여:** LangChain 프레임워크를 활용하여 에이전트에게 1) **RAG 검색 도구(retriever)**와 2) **MCP 서버의 3대 제어 도구(상태 확인, 업데이트, 3D 포커스)**를 통합 제공.
3. **최종 자율 대응(ReAct) 시나리오 구현:** 작업자의 단일 자연어 명령("가스터빈 온도가 너무 높아. 필요한 조치 다 취해줘")을 입력받아, 에이전트가 스스로 **'매뉴얼 검색 -> 조치법 파악 -> ERP 시스템 갱신 -> 3D 뷰어 동기화'**의 연쇄 작업을 완벽히 자동 수행하는 로직 완성.

### [STEP 5 완료] 대시보드 웹 UI 구현 (Streamlit)
1. **관제 대시보드 (Dashboard):** 사내망(ERP)과 3D 뷰어 데이터를 의미하는 JSON 파일의 데이터를 실시간으로 읽어와 좌측 화면에 대시보드 위젯 형태로 시각화.
2. **AI 챗봇 연동 (Copilot Window):** 우측 화면에 작업자가 자연어로 명령할 수 있는 채팅 인터페이스(ChatGPT 형태) 구축.
3. **실시간 시각적 연동 완료:** 챗봇에 명령을 내리면, AI(MCP)가 백그라운드에서 JSON 파일을 수정함과 동시에 웹뷰가 자동 갱신(rerun)되면서 좌측의 온도/상태 위젯과 3D 좌표 계기판이 실시간으로 통제되는 기믹 완성.

---

## 🎉 프로젝트 완료 (All Tasks Done)
율시스템(YoulSystem) 맞춤형 AI Agent (Mock CAD/DT Copilot) 프로토타입 개발이 모두 성공적으로 완료되었습니다! 면접 및 포트폴리오 시연용으로 즉각 활용 가능합니다.
