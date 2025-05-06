import os
from dotenv import load_dotenv

from LLM_verify_model import ImageVerifyModel

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from pubsub_helper import add_task

import threading
from worker import run_worker

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
        add_task(data)
        
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

# worker를 main 실행할 때 지속적으로 실행되도록 변경 
# pubsub_v1이 동기로 실행되므로 async를 붙이지 않음 
@app.on_event("startup")
def startup_event():
    threading.Thread(target=run_worker, daemon=True).start()         # FastAPI 서버 실행과 동시에 Pub/Sub 워커를 다른 작업 흐름에서 병렬로 처리하기 위해서 스레딩 사용 

