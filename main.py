# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import stream, analyze, heal, quiz, leaderboard, export
from core.config import settings

app = FastAPI(title="LogOracle API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before prod
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream.router,      prefix="/stream",      tags=["stream"])
app.include_router(analyze.router,     prefix="/analyze",     tags=["analyze"])
app.include_router(heal.router,        prefix="/heal",        tags=["heal"])
app.include_router(quiz.router,        prefix="/quiz",        tags=["quiz"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(export.router,      prefix="/export",      tags=["export"])

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
