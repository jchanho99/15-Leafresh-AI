import os
from dotenv import load_dotenv

from LLM_verify_model import ImageVerifyModel

from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import Optional
from datetime import date
from urllib.parse import urlparse

# 환경 변수 불러오기
load_dotenv()
bucket_name = os.getenv("BUCKET_NAME")

# FastAPI 초기화
app = FastAPI()
verifier = ImageVerifyModel()

# 요청 데이터 모델
class ImageVerificationRequest(BaseModel):
    imageUrl: str           
    memberId: int
    challengeId: int
    date: date
    challengeName: str

# 응답 데이터 모델
class ImageVerificationResponse(BaseModel):
    status: int
    message: str
    data: Optional[dict] = None

@app.post("/ai/image/Verification", response_model=ImageVerificationResponse, status_code=202)
async def verify_image(req: ImageVerificationRequest):
    try: 
        # url에서 파일명만 파싱 진행 
        parsed_url = urlparse(req.imageUrl)
        blob_name = parsed_url.path.split("/")[-1]

        result = verifier.image_verify(
            bucket_name=bucket_name,
            blob_name=blob_name,
            challenge_type=req.challengeName
        )
        # 추후 변경 필요
        return {
            "status": 202,
            "message": "이미지 인증이 완료되었습니다.",
            "data": {"result": result}
        }
    except Exception as e:
        return {
            "status": 500,
            "message": f"이미지 인증 중 오류 발생: {e}",
            "data": None
        }

