"""POST /api/knowledge/index/ — S8-09 (CEO only)"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import decode_token
from ..indexer import run_indexer

router = APIRouter()


@router.post("/index/")
async def reindex(payload: dict = Depends(decode_token), db: Session = Depends(get_db)):
    if payload.get("role") != "CEO":
        raise HTTPException(status_code=403, detail="CEO role required")
    result = run_indexer(db)
    return result
