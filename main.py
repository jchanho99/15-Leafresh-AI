import os
from dotenv import load_dotenv

from fastapi import FastAPI
import threading

from worker import run_worker
from router import router

# 환경 변수 불러오기
load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# app 초기화
app = FastAPI()
app.include_router(router)

# worker를 main 실행할 때 지속적으로 실행되도록 변경 
# pubsub_v1이 동기로 실행되므로 async를 붙이지 않음 
@app.on_event("startup")
def startup_event():
    threading.Thread(target=run_worker, daemon=True).start()         # FastAPI 서버 실행과 동시에 Pub/Sub 워커를 다른 작업 흐름에서 병렬로 처리하기 위해서 스레딩 사용 

