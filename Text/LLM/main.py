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
from Text.LLM.router.censorship_router import validation_exception_handler, http_exception_handler

from Text.LLM.router.chatbot_router import router as chatbot_router

from Text.LLM.router import feedback_router

load_dotenv()

# app 초기화
app = FastAPI()

# router 등록
app.include_router(censorship_router)
app.include_router(chatbot_router)
app.include_router(feedback_router.router)

# censorship model exceptions (422, 500, 503 etc.)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

