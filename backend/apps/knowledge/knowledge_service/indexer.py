"""Indexer del KB — procesa .md, skip CEO-ONLY, upsert en knowledge_chunks."""
import os, re
from pathlib import Path
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from .database import KnowledgeChunk

KB_DIR    = Path(os.environ.get("KB_DIR", "/kb"))
oai       = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
EMBED_MODEL = "text-embedding-3-small"


def _get_visibility(content: str) -> str:
    m = re.search(r"visibility:\s*(\S+)", content, re.IGNORECASE)
    return m.group(1).upper() if m else "PUBLIC"


def _chunk_by_sections(text: str) -> list[str]:
    sections = re.split(r"(?=^#{1,3} )", text, flags=re.MULTILINE)
    return [s.strip() for s in sections if s.strip()]


def run_indexer(db: Session) -> dict:
    files_indexed = 0
    chunks_inserted = 0
    chunks_skipped = 0
    errors = []

    for md_file in KB_DIR.rglob("*.md"):
        try:
            raw = md_file.read_text(encoding="utf-8")
            visibility = _get_visibility(raw)

            if visibility == "CEO-ONLY":
                chunks_skipped += 1
                continue

            chunks = _chunk_by_sections(raw)
            for idx, chunk in enumerate(chunks):
                emb = oai.embeddings.create(input=chunk, model=EMBED_MODEL).data[0].embedding
                db.execute(
                    text("""
                        INSERT INTO knowledge_chunks
                            (file_path, chunk_index, content, embedding, kb_visibility, indexed_at)
                        VALUES
                            (:fp, :ci, :content, :emb, :vis, NOW())
                        ON CONFLICT (file_path, chunk_index)
                        DO UPDATE SET
                            content=EXCLUDED.content,
                            embedding=EXCLUDED.embedding,
                            kb_visibility=EXCLUDED.kb_visibility,
                            indexed_at=NOW()
                    """),
                    {"fp": str(md_file), "ci": idx, "content": chunk,
                     "emb": str(emb), "vis": visibility}
                )
                chunks_inserted += 1
            db.commit()
            files_indexed += 1
        except Exception as e:
            errors.append({"file": str(md_file), "error": str(e)})

    return {
        "files_indexed":   files_indexed,
        "chunks_inserted": chunks_inserted,
        "chunks_skipped":  chunks_skipped,
        "errors":          errors,
    }
