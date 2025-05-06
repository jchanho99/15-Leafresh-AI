from fastapi import FastAPI

from dotenv import load_dotenv
import os

from router import router as censorship_router

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# app 초기화
app = FastAPI()

# 라우터 등록
app.include_router(censorship_router)
