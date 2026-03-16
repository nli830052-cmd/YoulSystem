import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 1. 파일 경로 설정
MANUAL_PATH = "./data/manuals/turbine_manual.txt"
DB_DIR = "./data/chroma_db"

def build_rag_db():
    print("🚀 [Step 1] 매뉴얼 데이터 로딩 중...")
    if not os.path.exists(MANUAL_PATH):
        print(f"❌ 매뉴얼 파일이 없습니다: {MANUAL_PATH}")
        return None
        
    import shutil
    # [중요] 기존에 구축된 낡은 기억(오염된 DB)을 깨끗하게 삭제하고 새로 구축
    if os.path.exists(DB_DIR):
        print("🗑️ 기존 Vector DB 정보(Chroma)를 초기화합니다...")
        import stat
        def remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(DB_DIR, onerror=remove_readonly)


    # 텍스트 파일 읽기
    loader = TextLoader(MANUAL_PATH, encoding="utf-8")
    documents = loader.load()

    # 문서를 적당한 크기로 쪼개기 (청킹)
    # 한 문단씩 쪼개기 위해 빈 줄(\n\n)을 기준으로 나눔
    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=300,
        chunk_overlap=50
    )
    docs = text_splitter.split_documents(documents)
    print(f"✅ 문서를 {len(docs)}개의 덩어리로 쪼갰습니다.")

    print("🚀 [Step 2] 임베딩 모델 준비 중 (CPU용 가벼운 모델)...")
    # 매우 가볍고 빠른 한국어/다국어 지원 임베딩 모델
    embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")

    print("🚀 [Step 3] Vector 데이터베이스(Chroma) 생성 중...")
    # 로컬 폴더(data/chroma_db)에 데이터베이스 저장
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=DB_DIR
    )
    print(f"✅ Vector DB 생성 완료! (저장 위치: {DB_DIR})")
    return vectorstore

def load_rag_db():
    """Streamlit 등에서 DB를 초기화하지 않고 순수하게 로딩(읽기)만 하는 함수"""
    if not os.path.exists(DB_DIR):
        print("❌ 기존 Vector DB가 없습니다. 먼저 터미널에서 python rag_pipeline.py 를 실행해주세요.")
        return None
    
    print("🚀 [1단계] 기존 Vector DB(Chroma)에 접속 중...")
    embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sroberta-multitask")
    return Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

def test_search(vectorstore):
    print("\n--- 🔍 RAG 검색 테스트 시작 ---")
    query = "V-102 밸브 압력이 이상할 때 어떻게 해?"
    print(f"질문: {query}")
    
    # 2개의 가장 연관성 높은 텍스트 덩어리(K=2) 검색
    results = vectorstore.similarity_search(query, k=2)
    
    print("\n[AI가 찾아낸 매뉴얼 내용]")
    for i, doc in enumerate(results, 1):
        print(f"결과 {i}:\n{doc.page_content}\n")
    print("-----------------------------\n")

if __name__ == "__main__":
    db = build_rag_db()
    if db:
        test_search(db)
