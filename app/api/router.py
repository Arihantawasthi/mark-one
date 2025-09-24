from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter(tags=["newsletter"])

@router.get("/")
def health_check():
    return { "status": "ok", "service": "scrapper" }
