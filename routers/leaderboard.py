from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_leaderboard():
    return {"status": "stub", "leaders": []}

