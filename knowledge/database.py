"""Sprint 8 S8-07 + S28-GH-SYNC: Conexión PostgreSQL + pgvector."""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://mwt:mwt@postgres:5432/mwt')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Crea la extensión pgvector, la tabla knowledge_chunks y kb_sync_state."""
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
        # S28-GH-SYNC: estado del sync con mwt-knowledge-hub
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS kb_sync_state (
                id               INTEGER PRIMARY KEY DEFAULT 1,
                repo_url         TEXT,
                branch           TEXT,
                last_sha         TEXT,
                last_synced_at   TIMESTAMPTZ,
                last_status      TEXT,
                last_error       TEXT,
                CONSTRAINT kb_sync_state_singleton CHECK (id = 1)
            )
        '''))
        conn.execute(text('''
            INSERT INTO kb_sync_state (id) VALUES (1)
            ON CONFLICT (id) DO NOTHING
        '''))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
