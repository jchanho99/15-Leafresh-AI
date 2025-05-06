from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from dotenv import load_dotenv
import os

from LLM_censorship_model import CensorshipModel

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

app = FastAPI()
model = CensorshipModel()

# 요청 데이터 모델
class ChallengeInfo(BaseModel):   # 모두 선택 항목
    id: Optional[int] = None
    name: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None 

class ValidationRequest(BaseModel):    # 모두 필수 항목
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

@app.post("/ai/challenges/group/validation", response_model=ValidationResponse)
async def validate_challenge(req: ValidationRequest):
    is_creatable, msg = model.validate(req.challengeName, req.startDate, req.endDate, req.challenge)
    return ValidationResponse(
        status=200,
        message=msg,
        data={"result": is_creatable}
    )
