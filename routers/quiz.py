from fastapi import APIRouter, Depends
from auth.dependencies import get_current_user

router = APIRouter()


@router.post("/generate")
async def generate_quiz(req: dict, user: dict = Depends(get_current_user)):
    return {"status": "stub", "questions": []}


@router.post("/answer")
async def answer_quiz(req: dict, user: dict = Depends(get_current_user)):
    return {"status": "stub", "correct": False}

