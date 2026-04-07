"""POST /api/knowledge/ask/ — S8-08"""
import os, json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis as redis_lib
from openai import OpenAI
from ..database import get_db
from ..auth import decode_token

router = APIRouter()
oai   = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
redis = redis_lib.from_url(os.environ.get("REDIS_URL", "redis://redis:6379"))

ALLOWED_PERMISSIONS = {"ASK_KNOWLEDGE_OPS", "ASK_KNOWLEDGE_PRODUCTS", "ASK_KNOWLEDGE_PRICING"}
EMBED_MODEL  = "text-embedding-3-small"
CHAT_MODEL   = "gpt-4o-mini"
SESSION_TTL  = 30 * 60  # 30 min


class AskRequest(BaseModel):
    question:   str
    session_id: str | None = None
    expediente_ref: int | None = None


@router.post("/ask/")
async def ask(req: AskRequest, payload: dict = Depends(decode_token), db: Session = Depends(get_db)):
    perms = set(payload.get("permissions", []))
    if not perms & ALLOWED_PERMISSIONS:
        raise HTTPException(status_code=403, detail="Permission required: ASK_KNOWLEDGE_*")

    user_id    = payload["user_id"]
    session_id = req.session_id or f"{user_id}-{__import__('uuid').uuid4().hex[:8]}"
    redis_key  = f"kw:session:{user_id}:{session_id}"

    # Historial multi-turn
    history_raw = redis.get(redis_key)
    history     = json.loads(history_raw) if history_raw else []

    # Embed + búsqueda vectorial
    emb = oai.embeddings.create(input=req.question, model=EMBED_MODEL).data[0].embedding
    vis_filter = "'PUBLIC'"
    if "ASK_KNOWLEDGE_PRICING" in perms:
        vis_filter = "'PUBLIC','PRICING'"

    rows = db.execute(text(f"""
        SELECT text FROM knowledge_chunks
        WHERE kb_visibility IN ({vis_filter})
        ORDER BY embedding <=> :emb\\:\\:vector
        LIMIT 5
    """), {"emb": str(emb)}).fetchall()

    context = "\n\n".join(r[0] for r in rows)
    chunks_used = [r[0][:80] for r in rows]

    messages = [
        {"role": "system", "content": f"Eres el asistente MWT ONE. Usa este contexto:\n\n{context}"}
    ] + history + [{"role": "user", "content": req.question}]

    resp   = oai.chat.completions.create(model=CHAT_MODEL, messages=messages, max_tokens=1024)
    answer = resp.choices[0].message.content

    # Guardar ConversationLog en Django DB
    db.execute(text("""
        INSERT INTO knowledge_conversationlog
            (session_id, user_id, user_role, question, answer, chunks_used, created_at, retain_until)
        VALUES
            (:sid, :uid, :role, :q, :a, :chunks, NOW(),
             NOW() + INTERVAL '90 days')
    """), {
        "sid": session_id,
        "uid": int(user_id) if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()) else None,
        "role": payload.get("role", ""),
        "q": req.question, "a": answer,
        "chunks": json.dumps(chunks_used)
    })
    db.commit()

    # Actualizar historial en Redis
    history.append({"role": "user",      "content": req.question})
    history.append({"role": "assistant", "content": answer})
    redis.setex(redis_key, SESSION_TTL, json.dumps(history))

    return {"answer": answer, "session_id": session_id, "chunks_used": chunks_used}
