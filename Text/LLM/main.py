import sys
import os

# Add the project root directory to sys.path
# Assumes this script is in Text/LLM/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, HTTPException

# Correct router imports
from Text.LLM.router.censorship_router import router as censorship_router
from Text.LLM.router.censorship_router import validation_exception_handler as censorship_validation_handler
from Text.LLM.router.censorship_router import http_exception_handler as censorship_http_handler

from Text.LLM.router.chatbot_router import router as chatbot_router

from Text.LLM.router.feedback_router import router as feedback_router
from Text.LLM.router.feedback_router import feedback_exception_handler
from Text.LLM.router.feedback_router import feedback_http_exception_handler

load_dotenv()

# app 초기화
app = FastAPI()

# router 등록
app.include_router(censorship_router)
app.include_router(chatbot_router)
app.include_router(feedback_router)

# 각 라우터별 예외 핸들러 등록
app.add_exception_handler(RequestValidationError, feedback_exception_handler)
app.add_exception_handler(HTTPException, feedback_http_exception_handler)
