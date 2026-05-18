from fastapi import APIRouter

router = APIRouter()


@router.post("/generate")
async def generate_quiz(req: dict):
    return {"status": "stub", "questions": []}


@router.post("/answer")
async def answer_quiz(req: dict):
    return {"status": "stub", "correct": False}

