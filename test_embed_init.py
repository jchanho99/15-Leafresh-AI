# test_embed_init.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.chatbot.generate_challenge_docs import generate_challenge_docs
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from dotenv import load_dotenv
import time

load_dotenv()

# 환경변수 로드
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Qdrant 클라이언트 (타임아웃 설정 추가)
qdrant_client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY,
    timeout=30.0  # 타임아웃을 30초로 설정
)

# 임베딩 모델
embedding_model = SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# 거리 측정 방식별 컬렉션 설정
distance_collections = {
    "COSINE": "test_cosine",
    "EUCLID": "test_euclid",
    "DOT": "test_dot",
    "MANHATTAN": "test_manhattan"
}

def create_collections():
    """각 거리 측정 방식별 컬렉션을 생성하고 데이터를 로드합니다."""
    # 먼저 random_sentences 데이터 생성
    print("=== random_sentences 데이터 생성 시작 ===")
    generate_challenge_docs(file_path="challenge_docs.txt", mode="random", num_paragraphs=50)  # 문단 수를 50으로 줄임
    print("=== random_sentences 데이터 생성 완료 ===\n")
    
    for distance, collection_name in distance_collections.items():
        try:
            print(f"\n=== {distance} 컬렉션 생성 시작 ===")
            
            # 기존 컬렉션이 있다면 삭제
            if qdrant_client.collection_exists(collection_name):
                print(f"기존 '{collection_name}' 컬렉션 삭제")
                qdrant_client.delete_collection(collection_name)
            
            # 새 컬렉션 생성
            print(f"'{collection_name}' 컬렉션 생성")
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=getattr(Distance, distance))
            )
            
            # 문서 로드 및 임베딩
            print("문서 로드 및 임베딩 시작")
            documents = TextLoader("challenge_docs.txt").load()
            splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=20)
            chunks = splitter.split_documents(documents)
            
            # 배치 크기 설정
            batch_size = 10
            total_chunks = len(chunks)
            
            # 각 컬렉션에 문서 추가 (배치 처리)
            collection_vectorstore = Qdrant(
                client=qdrant_client,
                collection_name=collection_name,
                embeddings=embedding_model
            )
            
            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i + batch_size]
                print(f"배치 처리 중: {i+1}~{min(i+batch_size, total_chunks)}/{total_chunks}")
                collection_vectorstore.add_documents(batch)
                time.sleep(1)  # 각 배치 사이에 1초 대기
            
            # 벡터 수 확인
            collection_info = qdrant_client.get_collection(collection_name)
            vector_count = collection_info.points_count
            print(f"'{collection_name}' 컬렉션에 {vector_count}개의 벡터가 저장됨")
            
            print(f"=== {distance} 컬렉션 생성 완료 ===\n")
            
        except Exception as e:
            print(f"'{collection_name}' 컬렉션 생성 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    create_collections() 