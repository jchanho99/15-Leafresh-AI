from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from dotenv import load_dotenv
import os

from router import router as censorship_router

load_dotenv()
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# app 초기화
app = FastAPI()

# 라우터 등록
app.include_router(censorship_router)

# 422 예외 처리
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):      # 사용하지 않더라도 FastAPI는 고정된 규약을 따르므로 request, exc를 유지해야함 
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": 422,
            "message": "필수 항목이 누락되었거나 형식이 잘못되었습니다.",
            "data": None
        }
    )

# 500, 503, 이외 예외 처리
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):

    if exc.status_code == 500:
        message = "챌린지 유사도 분석 중 오류가 발생했습니다. 다시 시도해주세요."
    elif exc.status_code == 503:
        message = "현재 서버가 혼잡하여 요청을 처리할 수 없습니다. 잠시 후 다시 시도해주세요."
    else:
        message = exc.detail 

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "message": message,
            "data": None
        }
    )
