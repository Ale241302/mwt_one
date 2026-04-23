"""Sprint 8 S8-07 + S28-GH-SYNC: Indexer KB.

- run_indexer(conn): full reindex sobre KB_PATH (.md). Se mantiene como fallback.
- index_files(conn, rel_paths, base_dir): reindex incremental de archivos puntuales.
- delete_files_from_index(conn, rel_paths): elimina chunks de archivos borrados.

Chunking por secciones h2/h3. Skip CEO-ONLY (D-13). Embeddings con text-embedding-3-small.
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

from openai import OpenAI
from sqlalchemy import text

logger = logging.getLogger(__name__)

KB_PATH    = Path(os.getenv('KB_PATH', '/kb'))
OPENAI_KEY = os.getenv('OPENAI_API_KEY', '')
client     = OpenAI(api_key=OPENAI_KEY)

CHUNK_SIZE       = 1000                                  # chars por chunk
EMBED_BATCH_SIZE = 96                                    # OpenAI acepta arrays grandes; 96 es cómodo


# ---------------------------------------------------------------------------
# Helpers de chunking
# ---------------------------------------------------------------------------

def _get_visibility(content: str) -> str:
    match = re.search(r'visibility\s*[:=]\s*([\w-]+)', content, re.IGNORECASE)
    return match.group(1).strip() if match else 'all'


def _chunk_by_sections(body: str) -> list[str]:
    parts = re.split(r'(?=^#{2,3} )', body, flags=re.MULTILINE)
    chunks: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        while len(part) > CHUNK_SIZE:
            chunks.append(part[:CHUNK_SIZE])
            part = part[CHUNK_SIZE:]
        if part:
            chunks.append(part)
    return chunks


def _embed(texts: list[str]) -> list[list[float]]:
    all_embs: list[list[float]] = []
    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i:i + EMBED_BATCH_SIZE]
        resp = client.embeddings.create(model='text-embedding-3-small', input=batch)
        all_embs.extend(r.embedding for r in resp.data)
    return all_embs


def _index_one_file(db_conn, abs_path: Path, rel_key: str) -> tuple[int, int]:
    """Indexa un archivo (borrando los chunks previos). Devuelve (inserted, skipped)."""
    content = abs_path.read_text(encoding='utf-8')
    visibility = _get_visibility(content)

    if visibility.upper() == 'CEO-ONLY':
        logger.info('Skipped CEO-ONLY: %s', rel_key)
        # También eliminar chunks viejos si el archivo pasó a CEO-ONLY
        db_conn.execute(text('DELETE FROM knowledge_chunks WHERE file_path = :fp'), {'fp': rel_key})
        return (0, 1)

    chunks = _chunk_by_sections(content)
    if not chunks:
        db_conn.execute(text('DELETE FROM knowledge_chunks WHERE file_path = :fp'), {'fp': rel_key})
        return (0, 0)

    embeddings = _embed(chunks)

    # Borro los chunks viejos y vuelvo a insertar en orden. Evita dejar índices obsoletos
    # cuando el número de chunks se reduce.
    db_conn.execute(text('DELETE FROM knowledge_chunks WHERE file_path = :fp'), {'fp': rel_key})

    inserted = 0
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        emb_str = '[' + ','.join(str(v) for v in emb) + ']'
        db_conn.execute(text('''
            INSERT INTO knowledge_chunks
                (file_path, chunk_index, content, embedding, kb_visibility, metadata, indexed_at)
            VALUES
                (:fp, :ci, :content, :emb::vector, :vis, :meta::jsonb, NOW())
        '''), {
            'fp': rel_key,
            'ci': idx,
            'content': chunk,
            'emb': emb_str,
            'vis': visibility,
            'meta': json.dumps({'source': rel_key}),
        })
        inserted += 1

    return (inserted, 0)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def run_indexer(db_conn) -> dict:
    """Full reindex sobre KB_PATH. Se conserva como fallback y para bootstrap manual."""
    files_indexed = 0
    chunks_inserted = 0
    chunks_skipped = 0
    errors: list[dict] = []

    md_files = list(KB_PATH.rglob('*.md'))
    # Ignorar el mirror interno del repo
    md_files = [p for p in md_files if '_repo' not in p.parts]

    if not md_files:
        return {'files_indexed': 0, 'chunks_inserted': 0, 'chunks_skipped': 0, 'errors': ['No .md files found in KB_PATH']}

    for md_file in md_files:
        try:
            rel_key = str(md_file.relative_to(KB_PATH))
            ins, skip = _index_one_file(db_conn, md_file, rel_key)
            if ins > 0:
                files_indexed += 1
            chunks_inserted += ins
            chunks_skipped  += skip
            db_conn.commit()
        except Exception as exc:
            db_conn.rollback()
            errors.append({'file': str(md_file), 'error': str(exc)})
            logger.exception('Indexer error %s', md_file)

    return {
        'files_indexed': files_indexed,
        'chunks_inserted': chunks_inserted,
        'chunks_skipped': chunks_skipped,
        'errors': errors,
    }


def index_files(db_conn, rel_paths: list[str], base_dir: Path) -> dict:
    """Reindex incremental de archivos específicos.

    Args:
        db_conn: conexión SQLAlchemy (típicamente session.connection()).
        rel_paths: rutas relativas al base_dir (ej. 'docs/pricing/plans.md').
        base_dir: directorio raíz que contiene esos archivos (ej. /kb/_repo).

    La clave en la tabla (file_path) es el rel_path sin normalización extra
    para que coincida con _list_subdir_md_full() de git_sync.py.
    """
    files_indexed = 0
    chunks_inserted = 0
    chunks_skipped = 0
    errors: list[dict] = []

    for rel in rel_paths:
        abs_path = base_dir / rel
        try:
            if not abs_path.is_file():
                errors.append({'file': rel, 'error': 'file not found after sync'})
                continue
            ins, skip = _index_one_file(db_conn, abs_path, rel)
            if ins > 0:
                files_indexed += 1
            chunks_inserted += ins
            chunks_skipped  += skip
            db_conn.commit()
        except Exception as exc:
            db_conn.rollback()
            errors.append({'file': rel, 'error': str(exc)})
            logger.exception('index_files error %s', rel)

    return {
        'files_indexed': files_indexed,
        'chunks_inserted': chunks_inserted,
        'chunks_skipped': chunks_skipped,
        'errors': errors,
    }


def delete_files_from_index(db_conn, rel_paths: list[str]) -> dict:
    """Elimina todos los chunks de los archivos listados (por file_path exacto)."""
    if not rel_paths:
        return {'files_deleted': 0, 'chunks_deleted': 0}
    res = db_conn.execute(text('''
        DELETE FROM knowledge_chunks
         WHERE file_path = ANY(:paths)
    '''), {'paths': rel_paths})
    db_conn.commit()
    return {
        'files_deleted': len(rel_paths),
        'chunks_deleted': res.rowcount or 0,
    }
