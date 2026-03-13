"""Sprint 8 S8-07/08/09: FastAPI Knowledge Service.
Base URL: /api/knowledge/ (proxied via Nginx)
Internal endpoints: /internal/* (X-Internal-Token auth)
"""
import os
import json
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
from database import init_db, get_db
from indexer import run_indexer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERNAL_TOKEN = os.getenv('KNOWLEDGE_INTERNAL_TOKEN', '')
OPENAI_KEY     = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_KEY  = os.getenv('ANTHROPIC_API_KEY', '')

app = FastAPI(title='mwt-knowledge', version='8.0.0')


@app.on_event('startup')
def startup():
    init_db()
    logger.info('mwt-knowledge started — pgvector ready')


def _verify_internal(request: Request):
    token = request.headers.get('X-Internal-Token', '')
    if INTERNAL_TOKEN and token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail='Invalid internal token')


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'mwt-knowledge'}


@app.post('/internal/ask/')
async def internal_ask(request: Request, db: Session = Depends(get_db)):
    """Llamado desde Django. Realiza búsqueda vectorial + Claude."""
    _verify_internal(request)
    body = await request.json()
    question    = body.get('question', '')
    history     = body.get('history', [])
    permissions = body.get('permissions', [])
    session_id  = body.get('session_id', '')

    # --- Embed pregunta ---
    oa_client = OpenAI(api_key=OPENAI_KEY)
    emb_resp = oa_client.embeddings.create(
        model='text-embedding-3-small',
        input=[question],
    )
    q_emb = emb_resp.data[0].embedding
    q_emb_str = '[' + ','.join(str(v) for v in q_emb) + ']'

    # --- Filtro visibilidad por permisos ---
    vis_filter = []
    if 'ask_knowledge_ops' in permissions:      vis_filter.append('ops')
    if 'ask_knowledge_products' in permissions: vis_filter.append('products')
    if 'ask_knowledge_pricing' in permissions:  vis_filter.append('pricing')
    vis_filter.append('all')  # siempre visible
    placeholders = ','.join(f':v{i}' for i in range(len(vis_filter)))
    vis_params   = {f'v{i}': v for i, v in enumerate(vis_filter)}

    rows = db.execute(text(f'''
        SELECT content, kb_visibility,
               1 - (embedding <=> :emb::vector) AS score
        FROM knowledge_chunks
        WHERE kb_visibility IN ({placeholders})
        ORDER BY embedding <=> :emb::vector
        LIMIT 5
    '''), {'emb': q_emb_str, **vis_params}).fetchall()

    chunks_used = [{'content': r[0], 'visibility': r[1], 'score': float(r[2])} for r in rows]
    context = '\n\n'.join(r[0] for r in rows)

    # --- Construir messages para Claude ---
    messages = []
    for h in history[-6:]:  # max 6 turnos previos
        messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': f'Contexto:\n{context}\n\nPregunta: {question}'})

    # --- Llamar Claude claude-3-5-haiku-20241022 ---
    import anthropic
    ac = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    claude_resp = ac.messages.create(
        model='claude-3-5-haiku-20241022',
        max_tokens=1024,
        system='Eres el asistente de conocimiento de MWT. Responde con base en el contexto proporcionado. Sé preciso y conciso.',
        messages=messages,
    )
    answer = claude_resp.content[0].text

    return {'answer': answer, 'session_id': session_id, 'chunks_used': chunks_used}


@app.post('/internal/index/')
async def internal_index(request: Request, db: Session = Depends(get_db)):
    """Ejecuta el indexer del KB. Solo accesible vía token interno."""
    _verify_internal(request)
    result = run_indexer(db.connection())
    return result
