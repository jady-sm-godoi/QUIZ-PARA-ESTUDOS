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
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            q.id as quiz_id,
            q.titulo,
            q.material_hash,
            q.criado_em,
            r.id as resultado_id,
            r.acertos,
            r.total,
            r.completado_em
        FROM quizzes q
        LEFT JOIN results r ON q.id = r.quiz_id
        ORDER BY q.criado_em DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    history = []
    for row in rows:
        item = {
            "quiz_id": row["quiz_id"],
            "titulo": row["titulo"],
            "material_hash": row["material_hash"],
            "criado_em": row["criado_em"],
        }
        if row["resultado_id"]:
            item["resultado_id"] = row["resultado_id"]
            item["acertos"] = row["acertos"]
            item["total"] = row["total"]
            item["completado_em"] = row["completado_em"]
        history.append(item)

    return history


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, COUNT(*) as material_count
        FROM materials
        WHERE category IS NOT NULL AND category != ''
        GROUP BY category
        ORDER BY category ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    categories = [
        CategoryResponse(name=row["category"], material_count=row["material_count"])
        for row in rows
    ]
    return categories


@router.get("/categories/{category}/materials", response_model=list[MaterialResponse])
async def get_category_materials(category: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    category: Optional[str] = None
):
    raise HTTPException(status_code=501, detail="Not implemented")