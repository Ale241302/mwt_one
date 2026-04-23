"""Sprint 8 S8-07/08/09 + S28-GH-SYNC: FastAPI Knowledge Service.

Base URL: /api/knowledge/     (proxied via Nginx -> Django -> este servicio)
Webhook:  /api/knowledge-webhook/github  (proxied via Nginx -> directo a este servicio)

Endpoints
---------
GET  /health
POST /internal/ask/              (X-Internal-Token)       RAG + Claude
POST /internal/index/            (X-Internal-Token)       full reindex de /kb
POST /internal/sync/             (X-Internal-Token)       sync manual con mwt-knowledge-hub
POST /webhook/github             (X-Hub-Signature-256)    webhook público de GitHub
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os

import anthropic
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from openai import OpenAI
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db, init_db
from indexer import delete_files_from_index, index_files, run_indexer
from git_sync import REPO_DIR, persist_sync_state, sync_repo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERNAL_TOKEN        = os.getenv('KNOWLEDGE_INTERNAL_TOKEN', '')
OPENAI_KEY            = os.getenv('OPENAI_API_KEY', '')
ANTHROPIC_KEY         = os.getenv('ANTHROPIC_API_KEY', '')
GITHUB_WEBHOOK_SECRET = os.getenv('GITHUB_WEBHOOK_SECRET', '').encode()
KB_REPO_BRANCH        = os.getenv('KB_REPO_BRANCH', 'main')

app = FastAPI(title='mwt-knowledge', version='8.1.0')


@app.on_event('startup')
def startup():
    init_db()
    logger.info('mwt-knowledge started — pgvector + kb_sync_state ready')


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _verify_internal(request: Request):
    token = request.headers.get('X-Internal-Token', '')
    if INTERNAL_TOKEN and token != INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail='Invalid internal token')


def _verify_github_signature(body: bytes, signature_header: str | None) -> None:
    """Valida X-Hub-Signature-256 con GITHUB_WEBHOOK_SECRET (HMAC-SHA-256)."""
    if not GITHUB_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail='GITHUB_WEBHOOK_SECRET not configured')
    if not signature_header or not signature_header.startswith('sha256='):
        raise HTTPException(status_code=401, detail='Missing X-Hub-Signature-256')
    received = signature_header.split('=', 1)[1]
    expected = hmac.new(GITHUB_WEBHOOK_SECRET, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received, expected):
        raise HTTPException(status_code=401, detail='Invalid webhook signature')


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'mwt-knowledge'}


# ---------------------------------------------------------------------------
# RAG /internal/ask/
# ---------------------------------------------------------------------------

@app.post('/internal/ask/')
async def internal_ask(request: Request, db: Session = Depends(get_db)):
    """Llamado desde Django. Realiza búsqueda vectorial + Claude."""
    _verify_internal(request)
    body = await request.json()
    question    = body.get('question', '')
    history     = body.get('history', [])
    permissions = body.get('permissions', [])
    session_id  = body.get('session_id', '')

    oa_client = OpenAI(api_key=OPENAI_KEY)
    emb_resp = oa_client.embeddings.create(
        model='text-embedding-3-small',
        input=[question],
    )
    q_emb = emb_resp.data[0].embedding
    q_emb_str = '[' + ','.join(str(v) for v in q_emb) + ']'

    vis_filter = []
    if 'ask_knowledge_ops' in permissions:      vis_filter.append('ops')
    if 'ask_knowledge_products' in permissions: vis_filter.append('products')
    if 'ask_knowledge_pricing' in permissions:  vis_filter.append('pricing')
    vis_filter.append('all')
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

    messages = []
    for h in history[-6:]:
        messages.append({'role': h['role'], 'content': h['content']})
    messages.append({'role': 'user', 'content': f'Contexto:\n{context}\n\nPregunta: {question}'})

    ac = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    claude_resp = ac.messages.create(
        model='claude-3-5-haiku-20241022',
        max_tokens=1024,
        system='Eres el asistente de conocimiento de MWT. Responde con base en el contexto proporcionado. Sé preciso y conciso.',
        messages=messages,
    )
    answer = claude_resp.content[0].text

    return {'answer': answer, 'session_id': session_id, 'chunks_used': chunks_used}


# ---------------------------------------------------------------------------
# Full reindex (manual)
# ---------------------------------------------------------------------------

@app.post('/internal/index/')
async def internal_index(request: Request, db: Session = Depends(get_db)):
    """Full reindex del KB (opera sobre /kb, ignorando /kb/_repo)."""
    _verify_internal(request)
    result = run_indexer(db.connection())
    return result


# ---------------------------------------------------------------------------
# Sync con mwt-knowledge-hub
# ---------------------------------------------------------------------------

def _run_sync_and_reindex(db: Session) -> dict:
    """Ejecuta git sync + reindex incremental + persiste estado. Idempotente."""
    conn = db.connection()
    try:
        diff = sync_repo(conn)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception('git_sync failed')
        return {'ok': False, 'stage': 'git_sync', 'error': str(exc)}

    # Nada cambió
    if not (diff.upserts or diff.deleted):
        persist_sync_state(conn, sha=diff.new_sha, status='noop', error=None)
        db.commit()
        return {
            'ok': True,
            'sha': diff.new_sha,
            'noop': True,
            'diff': diff.as_dict(),
            'reindex': {'files_indexed': 0, 'chunks_inserted': 0, 'files_deleted': 0, 'chunks_deleted': 0},
        }

    # Incremental: primero deletes, luego upserts
    try:
        del_result = delete_files_from_index(conn, diff.deleted)
        up_result  = index_files(conn, diff.upserts, REPO_DIR)
        persist_sync_state(
            conn,
            sha=diff.new_sha,
            status='ok' if not up_result['errors'] else 'partial',
            error=json.dumps(up_result['errors']) if up_result['errors'] else None,
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception('reindex failed')
        persist_sync_state(conn, sha=diff.new_sha, status='error', error=str(exc))
        db.commit()
        return {'ok': False, 'stage': 'reindex', 'error': str(exc), 'diff': diff.as_dict()}

    return {
        'ok': True,
        'sha': diff.new_sha,
        'first_sync': diff.first_sync,
        'diff': diff.as_dict(),
        'reindex': {
            'files_indexed':  up_result['files_indexed'],
            'chunks_inserted': up_result['chunks_inserted'],
            'chunks_skipped':  up_result['chunks_skipped'],
            'errors':          up_result['errors'],
            **del_result,
        },
    }


@app.post('/internal/sync/')
async def internal_sync(request: Request, db: Session = Depends(get_db)):
    """Trigger manual de sync desde Django/scripts (con X-Internal-Token)."""
    _verify_internal(request)
    return _run_sync_and_reindex(db)


@app.post('/webhook/github')
async def webhook_github(
    request: Request,
    db: Session = Depends(get_db),
    x_hub_signature_256: str | None = Header(None, alias='X-Hub-Signature-256'),
    x_github_event:      str | None = Header(None, alias='X-GitHub-Event'),
):
    """Webhook público de GitHub. Solo procesa push a KB_REPO_BRANCH."""
    raw_body = await request.body()
    _verify_github_signature(raw_body, x_hub_signature_256)

    # Ping = GitHub test del webhook
    if x_github_event == 'ping':
        return {'ok': True, 'pong': True}

    if x_github_event != 'push':
        return {'ok': True, 'ignored': f'event={x_github_event}'}

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid JSON body')

    ref = payload.get('ref', '')
    expected_ref = f'refs/heads/{KB_REPO_BRANCH}'
    if ref != expected_ref:
        return {'ok': True, 'ignored': f'ref={ref!r} (expected {expected_ref!r})'}

    return _run_sync_and_reindex(db)
