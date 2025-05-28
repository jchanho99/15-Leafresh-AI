# LLM_chatbot_free_text_model.py
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_qdrant import Qdrant
from langchain_community.embeddings import SentenceTransformerEmbeddings
from qdrant_client import QdrantClient
from langchain_google_vertexai import VertexAI
from dotenv import load_dotenv
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence, Optional, Dict, List
import os
import json

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

retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) # 사용자 질문으로 부터 가장 유사한 3개 문서 검색

# RAG 방식 챌린지 추천을 위한 Output Parser 정의
rag_response_schemas = [
    ResponseSchema(name="recommend", description="추천 텍스트를 한 문장으로 출력해줘.(예: '이런 챌린지를 추천합니다.')"),
    ResponseSchema(name="challenges", description="추천 챌린지 리스트, 각 항목은 title, description 포함, description은 한 문장으로 요약해주세요.")
]

# LangChain의 StructuredOutputParser를 사용하여 JSON 포맷을 정의
rag_parser = StructuredOutputParser.from_response_schemas(rag_response_schemas)

# JSON 포맷을 이스케이프 처리
escaped_format = rag_parser.get_format_instructions().replace("{", "{{").replace("}", "}}")

# RAG 방식 챌린지 추천을 위한 PromptTemplate 정의
custom_prompt = PromptTemplate(
    input_variables=["context", "query", "messages"],
    template=f"""
다음 문서와 이전 대화 기록을 참고하여 사용자에게 적절한 친환경 챌린지를 3개 추천해주세요.
반드시 문서에서 제공된 정보를 기반으로 답변해주세요.

이전 대화 기록:
{{messages}}
>>>>>>> 308479e (v2: version_API)

문서:
{{context}}

현재 요청:
{{query}}

응답은 반드시 다음 JSON 형식을 따라주세요:
{escaped_format}
"""
)

# LLM 초기화 (VertexAI)
llm = VertexAI(model_name="gemini-2.0-flash", temperature=0.7)

# LLMChain 체인 생성 (retriever는 app_router에서 별도 사용)
qa_chain = LLMChain(
    llm=llm,
    prompt=custom_prompt
)

# 대화 상태를 관리하기 위한 타입 정의
class ChatState(TypedDict):
    messages: Annotated[Sequence[str], "대화 기록"]
    current_query: str
    context: str
    response: str
    should_continue: bool  # 대화 계속 여부
    error: Optional[str]   # 오류 메시지
    docs: Optional[list]   # 검색된 문서
    sessionId: str   # 세션 ID

# 대화 그래프 노드 정의
def validate_query(state: ChatState) -> ChatState:
    """사용자 질문 유효성 검사"""
    if len(state["current_query"].strip()) < 5:
        state["error"] = "질문은 최소 5자 이상이어야 합니다."
        state["should_continue"] = False
    else:
        state["should_continue"] = True
    return state

def retrieve_context(state: ChatState) -> ChatState:
    """관련 컨텍스트 검색"""
    if not state["should_continue"]:
        return state
    try:
        # RAG 검색 수행
        docs = retriever.get_relevant_documents(state["current_query"])
        state["docs"] = docs
        state["context"] = "\n".join([doc.page_content for doc in docs])
        
        # 검색된 문서가 없는 경우
        if not docs:
            state["error"] = "관련된 챌린지 정보를 찾을 수 없습니다."
            state["should_continue"] = False
    except Exception as e:
        state["error"] = f"컨텍스트 검색 중 오류 발생: {str(e)}"
        state["should_continue"] = False
    return state

def generate_response(state: ChatState) -> ChatState:
    """응답 생성"""
    if not state["should_continue"]:
        return state
    try:
        messages = "\n".join(state["messages"])
        print(f"Generating response for query: {state['current_query']}")  # 디버깅용 로그
        
        response = qa_chain.invoke({
            "context": state["context"],
            "query": state["current_query"],
            "messages": messages
        })
        
        print(f"Raw LLM response: {response['text']}")  # 디버깅용 로그
        
        # JSON 파싱 시도
        try:
            response_text = response["text"]
            if "```json" in response_text:
                response_text = response_text.split("```json")[1]
            if "```" in response_text:
                response_text = response_text.split("```")[0]
            response_text = response_text.strip()
            
            parsed_response = json.loads(response_text)
            # 필수 필드 검증
            if "recommend" not in parsed_response or "challenges" not in parsed_response:
                raise ValueError("응답에 필수 필드가 없습니다.")
            if not isinstance(parsed_response["challenges"], list):
                raise ValueError("challenges는 리스트 형태여야 합니다.")
            
            state["response"] = json.dumps(parsed_response, ensure_ascii=False)
            print(f"Parsed response: {state['response']}")  # 디버깅용 로그
            
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {str(e)}")  # 디버깅용 로그
            state["error"] = "응답 형식이 올바르지 않습니다."
            state["should_continue"] = False
            return state
        except ValueError as e:
            print(f"응답 검증 오류: {str(e)}")  # 디버깅용 로그
            state["error"] = str(e)
            state["should_continue"] = False
            return state
        
        # 대화 기록 업데이트
        state["messages"] = list(state["messages"]) + [
            f"User: {state['current_query']}",
            f"Assistant: {state['response']}"
        ]
    except Exception as e:
        print(f"응답 생성 중 예외 발생: {str(e)}")  # 디버깅용 로그
        state["error"] = f"응답 생성 중 오류 발생: {str(e)}"
        state["should_continue"] = False
    return state

def handle_error(state: ChatState) -> ChatState:
    """오류 처리"""
    if state["error"]:
        state["response"] = state["error"]
        # 오류 메시지도 대화 기록에 추가
        state["messages"] = list(state["messages"]) + [
            f"User: {state['current_query']}",
            f"Assistant: {state['error']}"
        ]
    return state

# 대화 그래프 구성
def create_chat_graph():
    workflow = StateGraph(ChatState)
    
    # 노드 추가
    workflow.add_node("validate", validate_query)
    workflow.add_node("retrieve", retrieve_context)
    workflow.add_node("generate", generate_response)
    workflow.add_node("handle_error", handle_error)
    
    # 엣지 연결
    workflow.add_edge("validate", "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", "handle_error")
    workflow.add_edge("handle_error", END)
    
    # 조건부 라우팅
    workflow.add_conditional_edges(
        "validate",
        lambda x: "retrieve" if x["should_continue"] else "handle_error"
    )
    
    # 시작 노드 설정
    workflow.set_entry_point("validate")
    
    return workflow.compile()

# 대화 그래프 인스턴스 생성
chat_graph = create_chat_graph()

# 대화 상태 저장소
conversation_states: Dict[str, ChatState] = {}

def process_chat(sessionId: str, query: str) -> str:
    """대화 처리 함수"""
    # 이전 대화 상태 가져오기 또는 새로 생성
    if sessionId not in conversation_states:
        conversation_states[sessionId] = {
            "messages": [],
            "current_query": "",
            "context": "",
            "response": "",
            "should_continue": True,
            "error": None,
            "docs": None,
            "sessionId": sessionId
        }
    
    # 현재 상태 업데이트
    state = conversation_states[sessionId]
    state["current_query"] = query
    
    # 대화 그래프 실행
    result = chat_graph.invoke(state)
    
    # 상태 저장
    conversation_states[sessionId] = result
    
    return result["response"]

def clear_conversation(sessionId: str):
    """대화 기록 삭제"""
    if sessionId in conversation_states:
        del conversation_states[sessionId]

def get_conversation_history(sessionId: str) -> List[str]:
    """대화 기록 조회
    
    Args:
        sessionId: 사용자 세션 ID
    
    Returns:
        List[str]: 대화 기록 리스트
    """
    if sessionId in conversation_states:
        return conversation_states[sessionId]["messages"]
    return []
