import os
from dotenv import load_dotenv

from LLM_verify_model import ImageVerifyModel

from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import Optional
from datetime import date
from urllib.parse import urlparse

from pubsub_helper import publish_message

# 환경 변수 불러오기
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
bucket_name = os.getenv("BUCKET_NAME")

# FastAPI 초기화
app = FastAPI()
verifier = ImageVerifyModel()

# 요청 데이터 모델
class ImageVerificationRequest(BaseModel):
    imageUrl: str           
    memberId: int
    challengeId: int
    date: str # date
    challengeName: str

# 응답 데이터 모델
class ImageVerificationResponse(BaseModel):
    status: int
    message: str
    data: Optional[dict] = None

@app.post("/ai/image/Verification", response_model=ImageVerificationResponse, status_code=202)
async def verify_image(req: ImageVerificationRequest):
    try: 
        data = req.dict()
        data["date"] = str(req.date)        # 명시적 문자열으로 변경 
        publish_message(data)
        
        # 추후 변경 필요
        return {
            "status": 202,
            "message": "이미지 인증 요청이 정상적으로 접수되었습니다. 결과는 추후 콜백으로 전송됩니다.",
            "data": None
        }
    except Exception as e:
        return {
            "status": 500,
            "message": f"이미지 인증 중 오류 발생: {e}",
            "data": None
        }

class CallbackResult(BaseModel):
    memberId: int
    challengeId: int
    date: str
    result: str

@app.post("/api/challenges/{challengeId}/image/verification/result")
async def receive_result(challengeId: int, data: CallbackResult):
    print(f"콜백 수신 완료: {data}")
    return {"status": "received", "challengeId": challengeId}


