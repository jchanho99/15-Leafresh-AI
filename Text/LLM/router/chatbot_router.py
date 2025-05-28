# chatbot_router.py
from ..model.chatbot.LLM_chatbot_base_info_model import base_prompt, get_llm_response
from ..model.chatbot.LLM_chatbot_free_text_model import qa_chain, retriever, process_chat, clear_conversation
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import json
import re

router = APIRouter()

# 키워드 및 비속어 필터링 리스트
ENV_KEYWORDS = [
    "환경", "지구", "에코", "제로웨이스트", "탄소", "분리수거", "플라스틱", "텀블러", "기후", "친환경",
    "일회용", "미세먼지", "재활용", "자원", "대중교통", "도보", "비건", "탄소중립", "그린", "에너지",
    "쓰레기","아무","추천","챌린지","도움","도와줘","자세히","상세히"
    ]

BAD_WORDS = [
    "시발", "씨발", "fuck", "shit", "개새끼", "병신", "ㅅㅂ", "ㅄ", "ㅂㅅ","fuckyou", "asshole", "tlqkf","ㅈ"
    ]

class CategoryRequest(BaseModel):
    sessionId: Optional[str] = None
    location: Optional[str] = None
    workType: Optional[str] = None
    category: Optional[str] = None
class FreeTextRequest(BaseModel):
    sessionId: Optional[str] = None
    message: Optional[str] = None

# 비-RAG 방식 챌린지 추천
@router.post("/ai/chatbot/recommendation/base-info")
def select_category(req: CategoryRequest):
    missing_fields = []
    # 필수 필드 검사
    if not req.location:
        missing_fields.append("location")
    if not req.workType:
        missing_fields.append("workType")
    if not req.category:
        missing_fields.append("category")
    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": f"{missing_fields}은 필수입니다.",
                "data": None
            }
        )

    # LLM 호출을 위한 prompt 구성
    prompt = base_prompt.format(
        location=req.location,
        workType=req.workType,
        category=req.category
    )

    try:
        response = get_llm_response(prompt)
        # sessionId가 있는 경우 대화 기록에 추가
        if req.sessionId:
            process_chat(req.sessionId, f"카테고리: {req.category}, 위치: {req.location}, 직업: {req.workType}")
        return response
    except HTTPException as http_err:
        raise http_err # 내부 HTTPException을 먼저 처리
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={
                "status": 502,
                "message": "AI 서버로부터 추천 결과를 받아오는 데 실패했습니다.",
                "data": None
            }
        )

# LangChain 기반 RAG 추천
@router.post("/ai/chatbot/recommendation/free-text")
def freetext_rag(req: FreeTextRequest):
    missing_fields = []
    if not req.message or not req.message.strip():
        missing_fields.append("message")

    if missing_fields:
        return JSONResponse(
            status_code=400,
            content={
                "status": 400,
                "message": f"{missing_fields}은 필수입니다.",
                "data": None
            }
        )
    if len(req.message.strip()) < 5:
        return JSONResponse(
            status_code=422,
            content={
                "status": 422,
                "message": "message는 문자열이어야 하며, 최소 5자 이상의 문자열이어야 합니다.",
                "data": None
            }
        )
        
    message_lower = req.message.lower()
    if not any(k in req.message for k in ENV_KEYWORDS) or any(b in message_lower for b in BAD_WORDS):
        return JSONResponse(
            status_code=200,
            content={
                "status": 200,
                "message": "사용자에게 자유 메세지를 기반으로 챌린지를 추천합니다.",
                "data": {
                    "recommend": "저는 친환경 챌린지를 추천해드리는 Leafresh 챗봇이에요! 환경 관련 질문을 해주시면 더 잘 도와드릴 수 있어요.",
                    "challenges": None
                }
            }
        )
    
    try:
        # 대화 기록을 포함한 응답 생성
        response_text = process_chat(req.sessionId, req.message)
        
        try:
            # JSON 파싱 시도
            parsed = json.loads(response_text)
            
            if isinstance(parsed.get("challenges"), str):
                parsed["challenges"] = json.loads(parsed["challenges"])
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": 200,
                    "message": "사용자 자유 메시지를 기반으로 챌린지를 추천합니다.",
                    "data": parsed
                }
            )
            
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=500,
                content={
                    "status": 500,
                    "message": "챌린지 추천 중 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    "data": None
                }
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=502,
            content={
                "status": 502,
                "message": f"AI 서버로부터 추천 결과를 받아오는 데 실패했습니다.", # AI 서버 오류
                "data": None
                }
        )