from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List, Dict
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


MAX_CONTENT_CHARS = 50000
MAX_TOKENS_ESTIMATE = 4
NEED_SPLIT_THRESHOLD = 60000


def truncate_content(content: str, max_chars: int = MAX_CONTENT_CHARS) -> str:
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[Conteúdo truncado por limite de tamanho]"


def split_content_into_parts(content: str, max_chars: int = MAX_CONTENT_CHARS) -> List[Dict]:
    if not content or len(content) == 0:
        return []

    if len(content) <= max_chars:
        return [{
            "part_index": 0,
            "content": content,
            "char_count": len(content),
            "total_parts": 1
        }]

    parts = []
    total_parts = (len(content) + max_chars - 1) // max_chars

    for i in range(total_parts):
        start = i * max_chars
        end = start + max_chars
        part_content = content[start:end]

        parts.append({
            "part_index": i,
            "content": part_content,
            "char_count": len(part_content),
            "total_parts": total_parts
        })

    return parts


def get_content_needs_split(content: str) -> bool:
    return len(content) > NEED_SPLIT_THRESHOLD


router = APIRouter(prefix="/api", tags=["quiz"])


@router.post("/generate")
async def generate_quiz(request: QuizGenerateRequest):
    from app.agents import QuizAgent
    from app.models import QuizPartsResponse, ContentPartResponse

    conn = get_connection()
    cursor = conn.cursor()

    content_to_use = ""

    if request.categoria:
        cursor.execute("""
            SELECT content FROM materials WHERE category = ?
        """, (request.categoria,))
        materials = cursor.fetchall()
        if materials:
            content_to_use = "\n\n".join([m["content"] for m in materials])

    if not content_to_use and request.conteudo:
        content_to_use = request.conteudo

    if not content_to_use:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="É necessário fornecer conteúdo ou uma categoria com materiais"
        )

    needs_split = get_content_needs_split(content_to_use)
    parts = split_content_into_parts(content_to_use, MAX_CONTENT_CHARS)

    if needs_split and request.part_index is None:
        conn.close()
        return QuizPartsResponse(
            titulo=request.titulo,
            categoria=request.categoria,
            total_parts=len(parts),
            parts=[ContentPartResponse(**{k: v for k, v in p.items() if k != "content"}) for p in parts],
            message=f"Este material tem {len(content_to_use)} caracteres e foi dividido em {len(parts)} partes. "
                   f"Escolha part_index de 0 a {len(parts)-1} para gerar o quiz de uma parte específica."
        )

    if request.part_index is not None:
        if request.part_index < 0 or request.part_index >= len(parts):
            conn.close()
            raise HTTPException(
                status_code=400,
                detail=f"part_index inválido. Use valores entre 0 e {len(parts)-1}"
            )
        content_to_use = parts[request.part_index]["content"]
    else:
        content_to_use = truncate_content(content_to_use, MAX_CONTENT_CHARS)

    agent = QuizAgent()
    result = agent.generate(content_to_use, num_questions=request.num_perguntas)

    quiz_id = str(uuid.uuid4())
    material_hash = compute_hash(content_to_use)

    cursor.execute("""
        INSERT INTO quizzes (id, titulo, material_hash, criado_em)
        VALUES (?, ?, ?, ?)
    """, (quiz_id, request.titulo, material_hash, datetime.now().isoformat()))

    perguntas = []
    for i, q in enumerate(result.get("questions", [])):
        cursor.execute("""
            INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
            VALUES (?, ?, ?, ?, ?)
        """, (
            quiz_id,
            q["enunciado"],
            json.dumps(q["opcoes"]),
            q["resposta_correta"],
            q.get("explicacao", "")
        ))

        perguntas.append(QuestionModel(
            enunciado=q["enunciado"],
            opcoes=q["opcoes"],
            resposta_correta=q["resposta_correta"],
            explicacao=q.get("explicacao", "")
        ))

    conn.commit()
    conn.close()

    return QuizResponse(
        quiz_id=quiz_id,
        titulo=request.titulo,
        perguntas=perguntas
    )


@router.post("/generate/file")
async def generate_quiz_from_file(
    file: UploadFile = File(...),
    titulo: str = Form(...),
    num_perguntas: int = Form(10),
    categoria: Optional[str] = Form(None)
):
    from app.agents import QuizAgent
    from app.pdf_utils import extract_text

    content = await file.read()
    content_text = extract_text(content, file.filename or "")

    if not content_text.strip():
        raise HTTPException(status_code=400, detail="Não foi possível extrair texto do arquivo")

    conn = get_connection()
    cursor = conn.cursor()

    content_to_use = ""

    if categoria:
        cursor.execute("""
            SELECT content FROM materials WHERE category = ?
        """, (categoria,))
        materials = cursor.fetchall()
        if materials:
            content_to_use = "\n\n".join([m["content"] for m in materials])
            content_to_use += "\n\n" + content_text
        else:
            content_to_use = content_text
    else:
        content_to_use = content_text

    needs_split = get_content_needs_split(content_to_use)
    parts = split_content_into_parts(content_to_use, MAX_CONTENT_CHARS)

    if needs_split:
        conn.close()
        from app.models import QuizPartsResponse, ContentPartResponse
        return QuizPartsResponse(
            titulo=titulo,
            categoria=categoria,
            total_parts=len(parts),
            parts=[ContentPartResponse(**{k: v for k, v in p.items() if k != "content"}) for p in parts],
            message=f"Este material tem {len(content_to_use)} caracteres e foi dividido em {len(parts)} partes. "
                   f"Escolha part_index de 0 a {len(parts)-1} para gerar o quiz de uma parte específica."
        )

    content_to_use = truncate_content(content_to_use, MAX_CONTENT_CHARS)

    agent = QuizAgent()
    result = agent.generate(content_to_use, num_questions=num_perguntas)

    quiz_id = str(uuid.uuid4())
    material_hash = compute_hash(content_to_use)

    cursor.execute("""
        INSERT INTO quizzes (id, titulo, material_hash, criado_em)
        VALUES (?, ?, ?, ?)
    """, (quiz_id, titulo, material_hash, datetime.now().isoformat()))

    perguntas = []
    for i, q in enumerate(result.get("questions", [])):
        cursor.execute("""
            INSERT INTO questions (quiz_id, enunciado, opcoes, resposta_correta, explicacao)
            VALUES (?, ?, ?, ?, ?)
        """, (
            quiz_id,
            q["enunciado"],
            json.dumps(q["opcoes"]),
            q["resposta_correta"],
            q.get("explicacao", "")
        ))

        perguntas.append(QuestionModel(
            enunciado=q["enunciado"],
            opcoes=q["opcoes"],
            resposta_correta=q["resposta_correta"],
            explicacao=q.get("explicacao", "")
        ))

    conn.commit()
    conn.close()

    return QuizResponse(
        quiz_id=quiz_id,
        titulo=titulo,
        perguntas=perguntas
    )


@router.get("/quiz/{quiz_id}")
async def get_quiz(quiz_id: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, titulo, material_hash, criado_em
        FROM quizzes WHERE id = ?
    """, (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        conn.close()
        raise HTTPException(status_code=404, detail="Quiz não encontrado")

    cursor.execute("""
        SELECT id, enunciado, opcoes, resposta_correta, explicacao
        FROM questions WHERE quiz_id = ?
    """, (quiz_id,))
    questions = cursor.fetchall()

    cursor.execute("""
        SELECT id, acertos, total, completado_em
        FROM results WHERE quiz_id = ?
    """, (quiz_id,))
    result = cursor.fetchone()

    conn.close()

    perguntas = []
    for q in questions:
        opcoes = json.loads(q["opcoes"])
        perguntas.append({
            "enunciado": q["enunciado"],
            "opcoes": opcoes,
            "resposta_correta": q["resposta_correta"],
            "explicacao": q["explicacao"] or ""
        })

    response = {
        "quiz_id": quiz["id"],
        "titulo": quiz["titulo"],
        "perguntas": perguntas
    }

    if result:
        response["resultado_id"] = result["id"]
        response["acertos"] = result["acertos"]
        response["total"] = result["total"]
        response["completado_em"] = result["completado_em"]

    return response


@router.post("/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, request: QuizResultRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM quizzes WHERE id = ?", (quiz_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Quiz não encontrado")

    cursor.execute("""
        SELECT id, resposta_correta
        FROM questions WHERE quiz_id = ?
    """, (quiz_id,))
    questions = cursor.fetchall()

    if not questions:
        conn.close()
        raise HTTPException(status_code=400, detail="Quiz sem perguntas")

    acertos = 0
    total = len(questions)

    for i, question in enumerate(questions):
        question_index = i
        user_answer = request.respostas.get(question_index)
        if user_answer == question["resposta_correta"]:
            acertos += 1

    cursor.execute("SELECT id FROM results WHERE quiz_id = ?", (quiz_id,))
    existing_result = cursor.fetchone()

    if existing_result:
        cursor.execute("""
            UPDATE results
            SET acertos = ?, total = ?, completado_em = ?
            WHERE quiz_id = ?
        """, (acertos, total, datetime.now().isoformat(), quiz_id))
        result_id = existing_result["id"]
    else:
        cursor.execute("""
            INSERT INTO results (quiz_id, acertos, total, completado_em)
            VALUES (?, ?, ?, ?)
        """, (quiz_id, acertos, total, datetime.now().isoformat()))
        result_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return {
        "quiz_id": quiz_id,
        "acertos": acertos,
        "total": total,
        "completado_em": datetime.now().isoformat()
    }


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
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hash, filename, content, category, criado_em
        FROM materials
        WHERE category = ?
        ORDER BY criado_em DESC
    """, (category,))
    rows = cursor.fetchall()
    conn.close()

    materials = [
        MaterialResponse(
            hash=row["hash"],
            filename=row["filename"],
            content=row["content"],
            category=row["category"],
            criado_em=row["criado_em"]
        )
        for row in rows
    ]
    return materials


@router.post("/upload")
async def upload_material(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None)
):
    from app.pdf_utils import extract_text

    content = await file.read()
    content_text = extract_text(content, file.filename or "")

    if not content_text.strip():
        content_text = content.decode("utf-8", errors="ignore")

    material_hash = compute_hash(content_text)

    filename = file.filename or "unknown"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT hash FROM materials WHERE hash = ?", (material_hash,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {
            "hash": material_hash,
            "filename": filename,
            "content": content_text,
            "category": category,
            "message": "Material ja existe (hash duplicado)"
        }

    cursor.execute("""
        INSERT INTO materials (hash, filename, content, category, criado_em)
        VALUES (?, ?, ?, ?, ?)
    """, (material_hash, filename, content_text, category, datetime.now().isoformat()))

    conn.commit()
    conn.close()

    return {
        "hash": material_hash,
        "filename": filename,
        "content": content_text,
        "category": category,
        "criado_em": datetime.now().isoformat()
    }