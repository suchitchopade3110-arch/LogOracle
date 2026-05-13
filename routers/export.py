from fastapi import APIRouter, Response
from services.pdf_export import generate_pdf

router = APIRouter()


@router.post("/pdf")
async def export_pdf(req: dict):
    pdf = generate_pdf(req)
    return Response(content=pdf, media_type="application/pdf")
