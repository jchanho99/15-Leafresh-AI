from fastapi import APIRouter
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
    memberId: int
    challengeName: str
    startDate: str
    endDate: str
    challenge: List[ChallengeInfo]

# 응답 데이터 모델
class ValidationResponse(BaseModel):
    status: int
    message: str
    data: dict

@router.post("/ai/challenges/group/validation", response_model=ValidationResponse)
async def validate_challenge(req: ValidationRequest):
    is_creatable, msg = model.validate(req.challengeName, req.startDate, req.endDate, req.challenge)
    return ValidationResponse(
        status=200,
        message=msg,
        data={"result": is_creatable}
    )
