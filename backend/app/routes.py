from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
import json

from app.models import (
    QuizGenerateRequest,
    QuizResponse,
    QuizResultRequest,
    QuizResult,
    CategoryResponse,
    MaterialResponse,
    QuestionModel,
)
from app.database import get_connection, compute_hash
import uuid
from datetime import datetime

router = APIRouter(prefix="/api", tags=["quiz"])


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizGenerateRequest):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/quiz/{quiz_id}", response_model=QuizResponse)
async def get_quiz(quiz_id: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/quiz/{quiz_id}/submit", response_model=QuizResult)
async def submit_quiz(quiz_id: str, request: QuizResultRequest):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/history", response_model=list[dict])
async def get_history():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories():
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/categories/{category}/materials", response_model=list[MaterialResponse])
async def get_category_materials(category: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    category: Optional[str] = None
):
    raise HTTPException(status_code=501, detail="Not implemented")