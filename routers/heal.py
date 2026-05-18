from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.self_heal import SelfHealService

router = APIRouter()
heal_service = SelfHealService()


class ApproveRequest(BaseModel):
    command_id: str
    confirmed: bool


@router.post("/approve")
async def approve_heal(req: ApproveRequest):
    if not req.confirmed:
        raise HTTPException(status_code=400, detail="confirmed must be true")
    return await heal_service.execute(req.command_id)

