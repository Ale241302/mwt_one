"""
mwt-knowledge — FastAPI microservice
Sprint 8 · S8-07/08/09/10
"""
from fastapi import FastAPI
from .routers import ask, index, sessions
from .database import engine, Base

app = FastAPI(title="mwt-knowledge", version="0.1.0")

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Routers
app.include_router(ask.router,      prefix="/api/knowledge")
app.include_router(index.router,    prefix="/api/knowledge")
app.include_router(sessions.router, prefix="/api/knowledge")
