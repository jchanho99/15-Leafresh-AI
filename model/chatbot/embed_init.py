# embed_init.py
# Qdrant와 SentenceTransformerEmbeddings를 사용하여 문서 임베딩 및 저장
from generate_challenge_docs import generate_challenge_docs
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import VectorParams, Distance, PointStruct
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from dotenv import load_dotenv
import os
import hashlib

load_dotenv()

# 환경변수 로드
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")

# Qdrant 클라이언트
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# 현재 존재하는 컬렉션 목록 조회
try:
    existing_collections = qdrant_client.get_collections().collections
    existing_names = [coll.name for coll in existing_collections]
    print(f"현재 Qdrant에 존재하는 컬렉션 목록: {existing_names}")
except Exception as e:
    print(f"컬렉션 목록 조회 중 오류 발생: {str(e)}")

# 콜렉션 없으면 새로 생성
try:
    collections = qdrant_client.get_collections().collections
    collection_names = [coll.name for coll in collections]

    if not qdrant_client.collection_exists(COLLECTION_NAME):
        print(f" '{COLLECTION_NAME}' 컬렉션 생성")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    else:
        print(f" '{COLLECTION_NAME}' 컬렉션이 이미 존재합니다.")
except Exception as e:
    print(f"컬렉션 생성 중 오류 발생: {str(e)}")

# 임베딩 모델
embedding_fn = SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5")

# Qdrant vectorstore 객체
vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embeddings=embedding_fn,
)

RESET_COLLECTION = os.getenv("RESET_COLLECTION", "false").lower() == "true"
"""
환경변수 RESET_COLLECTION이 존재하지 않으면 기본값은 "false"로 간주"
컬렉션을 리셋할지 여부 (환경변수 또는 코드로 지정)
환경변수로 설정된 경우 우선 적용
예: export RESET_COLLECTION=true
기존 컬렉션을 완전히 삭제 후 새로 생성
"""

if RESET_COLLECTION:
    try:
        print(f"기존 컬렉션 '{COLLECTION_NAME}' 삭제 중")
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"컬렉션 초기화 완료: '{COLLECTION_NAME}'")
    except Exception as e:
        print(f"컬렉션 초기화 중 오류 발생: {str(e)}")

# 문서 생성 및 벡터 저장은 항상 실행
try:
    # 크롤링 및 데이터 생성
    result = generate_challenge_docs(file_path=None, mode="random")
    fixed_challenges = result["fixed_challenges"]
    crawled_challenges = result["crawled_challenges"]
    
    # 청크 분할
    splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=20)
    documents = []
    
    # 1. 고정 데이터 처리
    for challenge in fixed_challenges:
        # 고정 데이터의 메타데이터 추출
        metadata = {
            "category": (
                "제로웨이스트" if "제로웨이스트" in challenge or "플라스틱" in challenge or "분리수거" in challenge else
                "플로깅" if "플로깅" in challenge or "정화" in challenge or "청소" in challenge else
                "비건" if "비건" in challenge or "채식" in challenge or "식단" in challenge else
                "에너지절약" if "에너지" in challenge or "전기" in challenge or "냉난방" in challenge else
                "업사이클" if "업사이클" in challenge or "재활용" in challenge or "DIY" in challenge else
                "문화공유" if "공유" in challenge or "캠페인" in challenge or "워크숍" in challenge else
                "디지털탄소" if "디지털" in challenge or "이메일" in challenge or "클라우드" in challenge else
                "기타"
            ),
            "source": "기본데이터"
        }
        documents.append(Document(page_content=challenge, metadata=metadata))
    
    # 2. 크롤링 데이터 처리
    for challenge in crawled_challenges:
        documents.append(Document(
            page_content=challenge["content"],
            metadata=challenge["metadata"]
        ))
    
    # 청크 분할
    chunks = splitter.split_documents(documents)
    
    print(f"'{len(documents)}'개 문서 로드 및 '{len(chunks)}'개 청크 생성 완료")

    # 임베딩 및 Qdrant 저장 (중복 방지 - upsert 사용)
    points_to_insert = []
    for i, chunk in enumerate(chunks):
        # 문서 내용의 해시값을 ID로 사용 (중복 방지)
        doc_id = hashlib.sha256(chunk.page_content.encode('utf-8')).hexdigest()
        
        vector = embedding_fn.embed_query(chunk.page_content)
        points_to_insert.append(
            PointStruct(
                id=doc_id,
                vector=vector,
                payload=chunk.metadata
            )
        )

    # Qdrant에 포인트 삽입
    # upsert: ID가 존재하면 업데이트, 없으면 삽입 (중복 방지)
    # wait=True: 작업 완료까지 대기
    response = qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        wait=True,
        points=points_to_insert
    )
    print(f"Qdrant 삽입 응답: {response.status}")
    print(f"{len(points_to_insert)}개 포인트 삽입 시도 완료 (중복 포함)")
    
    try:
        collection_info = qdrant_client.get_collection(COLLECTION_NAME)
        vector_count = collection_info.points_count
        print(f"현재 Qdrant에 저장된 총 누적 벡터 수: {vector_count}")
    except Exception as e:
        print(f"벡터 수 조회 중 오류 발생: {str(e)}")
except Exception as e:
    print(f"문서 임베딩 중 오류 발생: {str(e)}")
