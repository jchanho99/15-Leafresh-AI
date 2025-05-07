from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

from LLM_censorship_model import CensorshipModel

router = APIRouter()
model = CensorshipModel()

# 요청 데이터 모델
class ChallengeInfo(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None 

class ValidationRequest(BaseModel):
    memberId: Optional[int] = None
    challengeName: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    challenge: Optional[List[ChallengeInfo]] = []

# 응답 데이터 모델
class ValidationResponse(BaseModel):
    status: int
    message: str
    data: Optional[dict] = None

@router.post("/ai/challenges/group/validation", response_model=ValidationResponse)
async def validate_challenge(req: ValidationRequest):

    if req.memberId is None:
        return JSONResponse(status_code=400, content={
            "status": 400, "message": "사용자 ID는 필수 항목입니다.", "data": None
        })
    if not req.challengeName:
        return JSONResponse(status_code=400, content={
            "status": 400, "message": "챌린지 이름은 필수 항목입니다.", "data": None
        })
    if not req.startDate:
        return JSONResponse(status_code=400, content={
            "status": 400, "message": "시작 날짜는 필수 항목입니다.", "data": None
        })
    if not req.endDate:
        return JSONResponse(status_code=400, content={
            "status": 400, "message": "끝 날짜는 필수 항목입니다.", "data": None
        })

    is_creatable, msg = model.validate(req.challengeName, req.startDate, req.endDate, req.challenge)
    return ValidationResponse(
        status=200,
        message=msg,
        data={"result": is_creatable}
    )

