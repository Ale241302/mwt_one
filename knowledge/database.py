"""Sprint 8 S8-07: Conexión PostgreSQL + pgvector."""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://mwt:mwt@postgres:5432/mwt')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Crea la extensión pgvector y la tabla knowledge_chunks."""
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id SERIAL PRIMARY KEY,
                file_path TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding vector(1536),
                kb_visibility TEXT NOT NULL DEFAULT \'all\',
                metadata JSONB DEFAULT \'{}\',
                indexed_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (file_path, chunk_index)
            )
        '''))
        conn.execute(text('''
            CREATE INDEX IF NOT EXISTS idx_chunks_hnsw
            ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)
        '''))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
