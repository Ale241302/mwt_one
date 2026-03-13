"""GET /api/knowledge/sessions/ — S8-10"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db
from ..auth import decode_token
from datetime import date

router = APIRouter()


@router.get("/sessions/")
async def list_sessions(
    user_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    payload: dict = Depends(decode_token),
    db: Session = Depends(get_db)
):
    me   = payload["user_id"]
    role = payload.get("role")
    target_user = user_id if (role == "CEO" and user_id) else me

    offset = (page - 1) * page_size
    rows = db.execute(text("""
        SELECT session_id, question, answer, created_at, retain_until
        FROM knowledge_conversationlog
        WHERE user_id = :uid
          AND (retain_until IS NULL OR retain_until >= :today)
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """), {"uid": target_user, "today": date.today(),
           "limit": page_size, "offset": offset}).fetchall()

    return [{"session_id": r[0], "question": r[1], "answer": r[2],
             "created_at": str(r[3]), "retain_until": str(r[4])} for r in rows]


@router.get("/sessions/{session_id}/")
async def session_detail(
    session_id: str,
    payload: dict = Depends(decode_token),
    db: Session = Depends(get_db)
):
    me = payload["user_id"]
    rows = db.execute(text("""
        SELECT session_id, question, answer, chunks_used, created_at, retain_until
        FROM knowledge_conversationlog
        WHERE session_id = :sid AND user_id = :uid
        ORDER BY created_at ASC
    """), {"sid": session_id, "uid": me}).fetchall()
    return [{"session_id": r[0], "question": r[1], "answer": r[2],
             "chunks_used": r[3], "created_at": str(r[4]),
             "retain_until": str(r[5])} for r in rows]
