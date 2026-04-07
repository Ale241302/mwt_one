"""
S24-08: Script de carga de Knowledge Base a pgvector.

Respeta POL_VISIBILIDAD:
  - Archivos marcados CEO-ONLY en su frontmatter -> SKIP completo
  - Secciones en 'ceo_only_sections' del frontmatter -> excluir solo esas secciones
  - Cada chunk guarda metadata: source_file, visibility, section_id

Uso:
  python scripts/load_kb.py --kb-dir knowledge/docs --reset

Verificacion post-carga:
  SELECT count(*) FROM knowledge_chunks WHERE visibility='CEO-ONLY';  -- debe ser 0
"""
from __future__ import annotations

import os
import re
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger('load_kb')

# ---------------------------------------------------------------------------
# Django setup — permite correr el script standalone
# ---------------------------------------------------------------------------
def _setup_django():
    sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
    import django
    django.setup()


# ---------------------------------------------------------------------------
# Modelos de datos
# ---------------------------------------------------------------------------
VISIBILITY_PUBLIC       = 'PUBLIC'
VISIBILITY_PARTNER_B2B  = 'PARTNER_B2B'
VISIBILITY_INTERNAL     = 'INTERNAL'
VISIBILITY_CEO_ONLY     = 'CEO-ONLY'

ALLOWED_VISIBILITIES = {VISIBILITY_PUBLIC, VISIBILITY_PARTNER_B2B, VISIBILITY_INTERNAL}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    Extrae frontmatter YAML simple (--- ... ---) del inicio del archivo.
    Retorna (meta_dict, body_text).
    """
    meta = {}
    body = text
    pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    match = pattern.match(text)
    if match:
        yaml_block = match.group(1)
        body = text[match.end():]
        for line in yaml_block.splitlines():
            line = line.strip()
            if ':' in line:
                key, _, val = line.partition(':')
                meta[key.strip()] = val.strip().strip('"\'')
    return meta, body


def split_into_chunks(body: str, source_file: str, visibility: str) -> List[dict]:
    """
    Divide el body en chunks por secciones H2/H3.
    Cada chunk: {text, source_file, visibility, section_id}
    """
    chunks = []
    # Dividir por encabezados ## o ###
    sections = re.split(r'(?m)^(#{2,3}\s+.+)$', body)
    current_section = 'intro'
    buffer = ''

    for part in sections:
        if re.match(r'^#{2,3}\s+', part):
            if buffer.strip():
                chunks.append({
                    'text': buffer.strip(),
                    'source_file': source_file,
                    'visibility': visibility,
                    'section_id': _slugify(current_section),
                })
            current_section = part.strip()
            buffer = ''
        else:
            buffer += part

    if buffer.strip():
        chunks.append({
            'text': buffer.strip(),
            'source_file': source_file,
            'visibility': visibility,
            'section_id': _slugify(current_section),
        })
    return chunks


def _slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9_-]', '-', text.lower())[:80]


def load_file(
    filepath: Path,
    ceo_only_override: bool = False,
) -> List[dict]:
    """
    Carga un archivo .md y retorna lista de chunks respetando POL_VISIBILIDAD.
    CEO-ONLY a nivel de archivo -> retorna [] (SKIP completo).
    """
    text = filepath.read_text(encoding='utf-8', errors='ignore')
    meta, body = parse_frontmatter(text)

    file_visibility = meta.get('visibility', VISIBILITY_PUBLIC).upper()
    ceo_only_sections_raw = meta.get('ceo_only_sections', '')
    ceo_only_sections = [
        s.strip() for s in ceo_only_sections_raw.split(',')
        if s.strip()
    ]

    # SKIP completo si el archivo es CEO-ONLY (S24-08)
    if file_visibility == VISIBILITY_CEO_ONLY or ceo_only_override:
        logger.info('SKIP CEO-ONLY: %s', filepath.name)
        return []

    # Si visibility no esta en los permitidos, tratarlo como INTERNAL
    if file_visibility not in ALLOWED_VISIBILITIES:
        logger.warning(
            'Visibility desconocida "%s" en %s -> usando INTERNAL',
            file_visibility, filepath.name
        )
        file_visibility = VISIBILITY_INTERNAL

    # Dividir por secciones con visibilidad del archivo
    chunks = split_into_chunks(body, str(filepath.name), file_visibility)

    # Excluir secciones CEO-ONLY por nombre (S24-08)
    if ceo_only_sections:
        before = len(chunks)
        chunks = [
            c for c in chunks
            if not any(
                ceo_sec.lower() in c['section_id'].lower()
                for ceo_sec in ceo_only_sections
            )
        ]
        excluded = before - len(chunks)
        if excluded:
            logger.info(
                'Excluded %d CEO-ONLY sections from %s', excluded, filepath.name
            )

    return chunks


def embed_and_store(chunks: List[dict], reset: bool = False):
    """
    Genera embeddings e inserta chunks en la tabla knowledge_chunks (pgvector).
    Usa sentence-transformers si esta disponible, fallback a OpenAI >= 1.0.
    """
    if not chunks:
        logger.info('No chunks to store.')
        return

    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        use_st = True
    except ImportError:
        logger.warning('sentence_transformers no disponible, usando OpenAI embeddings')
        use_st = False

    from django.db import connection

    # Inicializar cliente OpenAI una sola vez (openai >= 1.0)
    _openai_client = None
    if not use_st:
        import openai as _openai_lib
        _openai_client = _openai_lib.OpenAI(
            api_key=os.environ.get('OPENAI_API_KEY', '')
        )

    with connection.cursor() as cur:
        # Verificar que pgvector este instalado
        cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        if not cur.fetchone():
            raise RuntimeError(
                'pgvector no esta instalado. Ejecutar: CREATE EXTENSION vector;'
            )

        # Crear tabla si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id          BIGSERIAL PRIMARY KEY,
                source_file TEXT        NOT NULL,
                section_id  TEXT        NOT NULL,
                visibility  TEXT        NOT NULL DEFAULT 'PUBLIC',
                text        TEXT        NOT NULL,
                embedding   vector(384),
                created_at  TIMESTAMPTZ DEFAULT now()
            );
        """)

        if reset:
            logger.info('RESET: borrando knowledge_chunks existentes...')
            cur.execute('TRUNCATE TABLE knowledge_chunks;')

        inserted = 0
        for chunk in chunks:
            text = chunk['text']
            if not text.strip():
                continue

            # Generar embedding
            if use_st:
                emb = model.encode(text).tolist()
            else:
                # openai >= 1.0 — client.embeddings.create(), acceso por atributo
                resp = _openai_client.embeddings.create(
                    input=text,
                    model='text-embedding-3-small'
                )
                emb = resp.data[0].embedding

            # Guardar en DB — NO insertar CEO-ONLY (doble check S24-08)
            visibility = chunk.get('visibility', 'PUBLIC').upper()
            if visibility == VISIBILITY_CEO_ONLY:
                logger.warning(
                    'SKIP CEO-ONLY chunk en insert: %s / %s',
                    chunk['source_file'], chunk['section_id']
                )
                continue

            cur.execute(
                """
                INSERT INTO knowledge_chunks
                    (source_file, section_id, visibility, text, embedding)
                VALUES (%s, %s, %s, %s, %s::vector)
                """,
                [
                    chunk['source_file'],
                    chunk['section_id'],
                    visibility,
                    text,
                    str(emb),
                ]
            )
            inserted += 1

    logger.info('Inserted %d chunks into knowledge_chunks.', inserted)


def run(kb_dir: str, reset: bool = False, pattern: str = '**/*.md'):
    """Punto de entrada principal."""
    _setup_django()

    kb_path = Path(kb_dir)
    if not kb_path.exists():
        logger.error('kb-dir no existe: %s', kb_dir)
        sys.exit(1)

    md_files = sorted(kb_path.glob(pattern))
    logger.info('Encontrados %d archivos .md en %s', len(md_files), kb_dir)

    all_chunks = []
    for filepath in md_files:
        chunks = load_file(filepath)
        all_chunks.extend(chunks)
        logger.info('%s -> %d chunks (visibility=%s)',
                    filepath.name, len(chunks),
                    chunks[0]['visibility'] if chunks else 'SKIP')

    logger.info('Total chunks a indexar: %d', len(all_chunks))
    embed_and_store(all_chunks, reset=reset)
    logger.info('Carga completada.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='S24-08: Carga KB a pgvector')
    parser.add_argument(
        '--kb-dir',
        default='knowledge/docs',
        help='Directorio raiz de los archivos .md de la KB'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Borrar todos los chunks existentes antes de cargar'
    )
    parser.add_argument(
        '--pattern',
        default='**/*.md',
        help='Glob pattern para buscar archivos (default: **/*.md)'
    )
    args = parser.parse_args()
    run(kb_dir=args.kb_dir, reset=args.reset, pattern=args.pattern)
