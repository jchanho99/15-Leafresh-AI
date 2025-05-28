from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, AsyncIterator
import json
import asyncio

# Adjust the import based on your actual file structure
from ..model.feedback.LLM_feedback_model import FeedbackModel

router = APIRouter()

# Define Pydantic models for the input data based on FeedbackModel's expected input
class Submission(BaseModel):
    submittedAt: str
    isSuccess: bool

class PersonalChallenge(BaseModel):
    title: str
    isSuccess: bool

class GroupChallenge(BaseModel):
    title: str
    startDate: str
    endDate: str
    submissions: List[Submission] = []

class FeedbackRequest(BaseModel):
    memberId: str
    personalChallenges: List[PersonalChallenge] = []
    groupChallenges: List[GroupChallenge] = []

# Helper function to format generator output into SSE format
async def to_sse(generator: AsyncIterator[Dict[str, Any]]) -> AsyncIterator[str]:
    async for data in generator:
        # Ensure data is JSON serializable with proper Korean encoding
        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

@router.post("/api/members/feedback/stream")
async def stream_feedback(request_data: FeedbackRequest):
    feedback_model = FeedbackModel()
    event_generator = feedback_model.generate_feedback(request_data.model_dump())
    return StreamingResponse(to_sse(event_generator), media_type="text/event-stream")