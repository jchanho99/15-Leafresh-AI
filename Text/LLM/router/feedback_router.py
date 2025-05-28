from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from model.feedback.LLM_feedback_model import FeedbackModel

router = APIRouter()
feedback_model = FeedbackModel()

class Submission(BaseModel):
    isSuccess: bool
    submittedAt: datetime

class GroupChallenge(BaseModel):
    id: int
    title: str
    startDate: datetime
    endDate: datetime
    submissions: List[Submission]

class PersonalChallenge(BaseModel):
    id: int
    title: str
    isSuccess: bool

class FeedbackRequest(BaseModel):
    memberId: int
    personalChallenges: Optional[List[PersonalChallenge]] = []
    groupChallenges: Optional[List[GroupChallenge]] = []

@router.post("/ai/feedback")
async def stream_feedback(request: FeedbackRequest):
    try:
        if not request.memberId:
            return {
                "status": 422,
                "message": "피드백 생성을 위한 활동 데이터가 부족합니다. 최소 1개의 챌린지 참여가 필요합니다.",
                "data": None
            }

        if not request.personalChallenges and not request.groupChallenges:
            return {
                "status": 400,
                "message": "요청 값이 유효하지 않습니다. 챌린지 데이터가 모두 포함되어야 합니다.",
                "data": None
            }

        def sse_generator():
            for chunk in feedback_model.generate_feedback_stream(request.dict()):
                yield f"data: {chunk}\n\n"

        return StreamingResponse(sse_generator(), media_type="text/event-stream")

    except Exception:
        return {
            "status": 500,
            "message": "서버 오류로 피드백 생성을 완료하지 못했습니다. 잠시 후 다시 시도해주세요.",
            "data": None
        }