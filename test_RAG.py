# LLM_chatbot_free_text_model.py
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_qdrant import Qdrant
from langchain_community.embeddings import SentenceTransformerEmbeddings
from qdrant_client import QdrantClient
from langchain_google_vertexai import VertexAI
from dotenv import load_dotenv
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader
import os
import time

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
embedding_model = SentenceTransformerEmbeddings(model_name="BAAI/bge-small-en-v1.5")

vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embeddings=embedding_model
)

# 기본 RAG
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 50})

# 유사도 임계값 적용 RAG (코사인 유사도 기준)
threshold_retrievers = {
    "임계값 0.9 RAG (매우 엄격)": vectorstore.as_retriever(
        search_kwargs={
            "k": 50,
            "score_threshold": 0.9  # 거의 동일한 의미
        }
    ),
    "임계값 0.7 RAG (보통)": vectorstore.as_retriever(
        search_kwargs={
            "k": 50,
            "score_threshold": 0.7  # 유사한 의미
        }
    )
}

# MMR 적용 RAG
mmr_retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 20,
        "mmr": True,
        "mmr_threshold": 0.7
    }
)

# 메타데이터 필터링 적용 RAG
metadata_retrievers = {
    "제로웨이스트 RAG": vectorstore.as_retriever(
        search_kwargs={
            "k": 20,
            "filter": {
                "category": "제로웨이스트"
            }
        }
    ),
    "에너지절약 RAG": vectorstore.as_retriever(
        search_kwargs={
            "k": 20,
            "filter": {
                "category": "에너지절약"
            }
        }
    ),
    "친환경운송 RAG": vectorstore.as_retriever(
        search_kwargs={
            "k": 20,
            "filter": {
                "category": "친환경운송"
            }
        }
    )
}

# RAG 방식 챌린지 추천을 위한 Output Parser 정의
rag_response_schemas = [
    ResponseSchema(name="recommend", description="추천 텍스트를 한 문장으로 출력해줘."),
    ResponseSchema(name="challenges", description="추천 챌린지 리스트, 각 항목은 title, description 포함, description은 한 문장으로 요약해주세요.")
]

# LangChain의 StructuredOutputParser를 사용하여 JSON 포맷을 정의
rag_parser = StructuredOutputParser.from_response_schemas(rag_response_schemas)

# JSON 포맷을 이스케이프 처리
escaped_format = rag_parser.get_format_instructions().replace("{", "{{").replace("}", "}}")

# 테스트용 프롬프트 템플릿
test_prompt = PromptTemplate(
    input_variables=["context", "query"],
    template=f"""
반드시 문서에서 제공된 정보를 기반으로 사용자에게 적절한 친환경 챌린지를 3개 추천해주세요.

문서:
{{context}}

현재 요청:
{{query}}

응답은 반드시 다음 JSON 형식을 따라주세요:
{escaped_format}
"""
)

# 테스트용 LLMChain (창의적인 응답을 위해 temperature=0.9)
test_chain = LLMChain(
    llm=VertexAI(model_name="gemini-2.0-flash", temperature=0.9),
    prompt=test_prompt
)

def test_rag_performance(query: str, num_runs: int = 3):
    """RAG 성능 테스트 함수
    
    Args:
        query: 테스트할 쿼리
        num_runs: 각 설정별 실행 횟수
    """
    results = {}
    
    # 모든 RAG 방식
    all_retrievers = {
        "기본 RAG": base_retriever,
        **threshold_retrievers,  # 임계값 RAG들
        "MMR RAG": mmr_retriever,
        **metadata_retrievers  # 메타데이터 필터링 RAG들
    }
    
    for name, retriever in all_retrievers.items():
        total_time = 0
        total_docs = 0
        successful_runs = 0
        
        print(f"\n=== {name} 테스트 ===")
        
        for i in range(num_runs):
            try:
                # 검색 시간 측정
                start_time = time.time()
                docs = retriever.get_relevant_documents(query)
                search_time = time.time() - start_time
                
                # 문서 수 기록
                total_docs += len(docs)
                
                # LLM 응답 생성 시간 측정
                start_time = time.time()
                context = "\n".join([doc.page_content for doc in docs])
                response = test_chain.invoke({
                    "context": context,
                    "query": query
                })
                llm_time = time.time() - start_time
                
                total_time += (search_time + llm_time)
                successful_runs += 1
                
                print(f"실행 {i+1}:")
                print(f"- 검색된 문서 수: {len(docs)}")
                print(f"- 검색 시간: {search_time:.2f}초")
                print(f"- LLM 응답 시간: {llm_time:.2f}초")
                print(f"- 총 소요 시간: {search_time + llm_time:.2f}초")
                
            except Exception as e:
                print(f"실행 {i+1} 실패: {str(e)}")
        
        if successful_runs > 0:
            avg_time = total_time / successful_runs
            avg_docs = total_docs / successful_runs
            results[name] = {
                "평균 소요 시간": f"{avg_time:.2f}초",
                "평균 검색 문서 수": f"{avg_docs:.1f}개",
                "성공률": f"{(successful_runs/num_runs)*100:.1f}%"
            }
    
    print("\n=== 테스트 결과 요약 ===")
    for name, metrics in results.items():
        print(f"\n{name}:")
        for metric, value in metrics.items():
            print(f"- {metric}: {value}")

if __name__ == "__main__":
    test_queries = [
        "환경을 위해 분리수거를 잘하고 싶어요",
        "텀블러 사용하는 방법 알려줘",
        "친환경 운송수단 추천해줘",
        "에너지 절약하는 방법이 궁금해"
    ]
    
    for query in test_queries:
        print(f"\n=== 쿼리: '{query}' 테스트 시작 ===")
        test_rag_performance(query)
        print(f"=== 쿼리: '{query}' 테스트 종료 ===\n")

# LLM 초기화 (VertexAI)
llm = VertexAI(model_name="gemini-2.0-flash", temperature=0.5)

# LLMChain 체인 생성 (retriever는 app_router에서 별도 사용)
qa_chain = LLMChain(
    llm=llm,
    prompt=custom_prompt
)