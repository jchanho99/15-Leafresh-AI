from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import HTTPException

from dotenv import load_dotenv

from censorship_router import router as censorship_router
from censorship_router import validation_exception_handler, http_exception_handler

load_dotenv()

# app 초기화
app = FastAPI()

# 라우터 등록
app.include_router(censorship_router)

# 예외 처리 
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)



