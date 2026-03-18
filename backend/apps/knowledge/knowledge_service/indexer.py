"""Sprint 8 S8-07: Indexer KB.
Recorre .md en /kb/, hace chunking por secciones h2/h3.
Skip CEO-ONLY (D-13). Llama text-embedding-3-small. Upsert.
"""
import os
import re
import json
import logging
from pathlib import Path
from sqlalchemy import text
from openai import OpenAI


logger = logging.getLogger(__name__)


KB_PATH    = Path(os.getenv('KB_PATH', '/kb'))
OPENAI_KEY = os.getenv('OPENAI_API_KEY', '')
client     = OpenAI(api_key=OPENAI_KEY)


CHUNK_SIZE = 1000  # caracteres máx por chunk


def _get_visibility(content: str) -> str:
    """Extrae visibility del frontmatter del archivo .md."""
    match = re.search(r'visibility\s*[:=]\s*([\w\-\[\]]+)', content, re.IGNORECASE)
    return match.group(1).strip() if match else 'PUBLIC'


def _chunk_by_sections(text: str) -> list[str]:
    """Divide el texto por secciones ## / ###."""
    parts = re.split(r'(?=^#{2,3} )', text, flags=re.MULTILINE)
    chunks = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Sub-divide si el chunk es muy grande
        while len(part) > CHUNK_SIZE:
            chunks.append(part[:CHUNK_SIZE])
            part = part[CHUNK_SIZE:]
        if part:
            chunks.append(part)
    return chunks


def _embed(texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(
        model='text-embedding-3-small',
        input=texts,
    )
    return [r.embedding for r in resp.data]


def run_indexer(db_conn) -> dict:
    """Ejecuta el indexer. Devuelve resumen."""
    files_indexed  = 0
    chunks_inserted = 0
    chunks_skipped  = 0
    errors = []

    md_files = list(KB_PATH.rglob('*.md'))
    if not md_files:
        return {
            'files_indexed': 0,
            'chunks_inserted': 0,
            'chunks_skipped': 0,
            'errors': ['No .md files found in KB_PATH'],
        }

    for md_file in md_files:
        try:
            content    = md_file.read_text(encoding='utf-8')
            visibility = _get_visibility(content)

            # D-13: excluir CEO-ONLY
            if 'CEO-ONLY' in visibility.upper():
                chunks_skipped += 1
                logger.info('Skipped CEO-ONLY: %s', md_file)
                continue

            chunks = _chunk_by_sections(content)
            if not chunks:
                continue

            embeddings = _embed(chunks)
            file_path  = str(md_file.relative_to(KB_PATH))

            for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                emb_str = '[' + ','.join(str(v) for v in emb) + ']'
                db_conn.execute(text('''
                    INSERT INTO knowledge_chunks
                        (file_path, chunk_index, content, embedding, kb_visibility, chunk_metadata, indexed_at)
                    VALUES
                        (:fp, :ci, :content, :emb::vector, :vis, :chunk_metadata::jsonb, NOW())
                    ON CONFLICT (file_path, chunk_index) DO UPDATE SET
                        content      = EXCLUDED.content,
                        embedding    = EXCLUDED.embedding,
                        kb_visibility = EXCLUDED.kb_visibility,
                        indexed_at   = NOW()
                '''), {
                    'fp':      file_path,
                    'ci':      idx,
                    'content': chunk,
                    'emb':     emb_str,
                    'vis':     visibility,
                    'chunk_metadata': json.dumps({'source': file_path}),
                })
                chunks_inserted += 1

            db_conn.commit()
            files_indexed += 1

        except Exception as exc:
            db_conn.rollback()   # ← limpia la tx abortada antes del siguiente archivo
            errors.append({'file': str(md_file), 'error': str(exc)})
            logger.error('Indexer error %s: %s', md_file, exc)

    return {
        'files_indexed':  files_indexed,
        'chunks_inserted': chunks_inserted,
        'chunks_skipped':  chunks_skipped,
        'errors':          errors,
    }
