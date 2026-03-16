# [Project Proposal] AI Agent for Digital Twin-based Plant Maintenance

## 1. 프로젝트 개요 (Project Overview)
본 프로젝트는 원자력 발전소 및 대규모 플랜트 산업에 특화된 **"디지털 트윈 통합 운영 관리 시스템"**을 고도화하기 위한 AI Agent 프로토타입 개발을 목표로 합니다.
최신 AI 기술인 **RAG(Retrieval-Augmented Generation)**와 **MCP(Model Context Protocol)** 기술을 결합하여, 작업자의 자연어 명령에 따라 자율적으로 설비 매뉴얼을 검색하고 사내 시스템(ERP 및 3D 형상 데이터)과 안전하게 통신하는 업무 자동화 프로세스를 시연합니다.

## 2. 핵심 구현 목표 (Core Objectives)
1. **RAG 기반 도메인 지식 검색:** 방대한 설비 유지보수 가이드라인 및 매뉴얼을 벡터화하여, 작업자의 질의에 빠르고 정확하게 대응하는 지식 검색 파이프라인 구축.
2. **MCP 기반 안전한 시스템 연동:** 사내 보안망 내의 실제 ERP DB 및 3D 모델 데이터에 AI가 직접 접근하는 대신, MCP 서버를 통해 한정된 API(Tool)로만 통신함으로써 최고 수준의 데이터 보안성 확보.
3. **Agentic 워크플로우 자동화:** ReAct(Reasoning and Acting) 프레임워크를 적용하여, AI가 자율적으로 상황을 판단하고 다중 도구(Tool)를 활용하여 유지보수 업무 및 3D 뷰어 조작을 통합 수행.

## 3. 시스템 아키텍처 (System Architecture)

```mermaid
graph LR
    User([현장 작업자]) -- "V-102 밸브 점검 및 3D 위치 확인 요청" --> Agent[AI Agent (ReAct Framework)]
    
    subgraph "1. RAG 파이프라인 (도메인 지식)"
    Agent <--> VectorDB[(Vector DB)]
    VectorDB -- "조치 가이드라인 맵핑" --> Docs[유지보수 매뉴얼 Data]
    end
    
    subgraph "2. MCP 서버 (보안/데이터 연동)"
    Agent -- "Secure API Request" --> MCP_Server[MCP Server]
    MCP_Server <--> ERP[(Legacy System: 가상 JSON DB)]
    MCP_Server <--> 3D_State[(3D Viewer Data: 가상 JSON 설정)]
    end
```

## 4. 기술 스택 (Technology Stack)
본 PoC(개념 증명)는 개발 환경(AMD Ryzen CPU 중심, 4GB VRAM) 리소스의 제약을 고려하여, 빠르고 효율적인 로컬/API 하이브리드 아키텍처로 설계되었습니다.
* **LLM Engine:** OpenAI API (GPT-4o-mini 등 경량 모델) 기반 클라우드 추론 (PC 로컬 리소스 점유율 최소화)
* **Agent Framework:** LangChain (ReAct 모델 적용)
* **RAG Pipeline:**
    * Embedding: `sentence-transformers` (HuggingFace 경량 모델, CPU 구동 최적화)
    * Vector DB: `ChromaDB` (로컬 파일 기반의 경량 데이터베이스)
* **MCP Integration:** Python `mcp` SDK 활용
* **Web UI (Frontend):** `Streamlit` (실시간 통합 관제 대시보드 및 챗봇 인터페이스 시각화)

## 5. 단계별 구현 시나리오 (Implementation Scenario)
현장에서 발생할 수 있는 실제 설비 이상 상황을 가정한 엔드투엔드(End-to-End) 데모 시나리오입니다.

1. **사용자 입력:** "1구역의 가스터빈(T-100) 온도가 비정상적으로 높습니다. 조치 방법과 함께 시스템에 점검 상태로 반영하고 3D 도면 위치를 포커스해 주세요."
2. **AI Action 1 (RAG):** 벡터 DB를 검색하여 '가스터빈 T-100 고온 발생 시 1차 점검 매뉴얼'을 도출.
3. **AI Action 2 (MCP - ERP):** MCP 서버의 `update_equipment_status` 도구를 호출하여, 사내 가상 데이터베이스 상의 T-100 장비 상태를 '점검 요망'으로 안전하게 변경.
4. **AI Action 3 (MCP - 3D):** MCP 서버의 `set_3d_camera_focus` 도구를 호출하여, 3D 뷰어의 가상 카메라 좌표를 T-100 설비 위치(X, Y, Z)로 이동 지시.
5. **최종 응답:** 작업자에게 초기 조치 방법을 설명하고 레거시 시스템 및 3D 뷰어 연동 처리가 완료되었음을 보고.

## 6. 기대 효과 (Expected Impact)
* **데이터 보안성 증명 (Security):** LLM이 기업의 핵심 데이터베이스와 자산(3D 모델)에 직접 접근하지 않는 완전한 격리 구조를 기술적으로 입증.
* **확장성 확보 (Scalability):** 향후 실제 웹 기반 통합 가시화 솔루션 및 기간 시스템(SAP/ERP 등)과 즉각적인 연계가 가능한 모듈형 아키텍처(MCP) 제시.
* **업무 효율성 극대화 (Efficiency):** 기존 분절되어 있던 문서 검색, 시스템 입력, 정밀 3D 모델 로드 프로세스를 통합된 자연어 명령 워크플로우로 단축.
* **통합 관제 가시성 향상 (Visibility):** LLM 에이전트의 작동 결과를 실시간 UI 연동 대시보드(Streamlit)로 즉시 시각화하여 현장 담당자의 직관적인 상황 통제력 강화.
