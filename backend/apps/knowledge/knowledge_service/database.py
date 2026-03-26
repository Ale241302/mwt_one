import os
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector
from datetime import datetime

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id             = Column(Integer, primary_key=True, index=True)
    file_path      = Column(String(500), nullable=False)
    chunk_index    = Column(Integer, nullable=False)
    content        = Column(Text, nullable=False)
    embedding      = Column(Vector(1536))
    kb_visibility  = Column(String(50), default="PUBLIC")
    chunk_metadata = Column(JSON, default={})   # renamed: 'metadata' is reserved by SQLAlchemy
    indexed_at     = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('file_path', 'chunk_index', name='uq_chunk'),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create extension + tables."""
    with engine.connect() as conn:
        conn.execute(__import__('sqlalchemy').text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
