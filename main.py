import glob
import json
import logging

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from middleware.auth import APIKeyMiddleware
from middleware.rate_limit import RateLimitMiddleware, limiter, rate_limit_handler
from middleware.request_guard import (
    RequestLogMiddleware,
    RequestSizeMiddleware,
    get_allowed_origins,
    validate_env_on_startup,
)
from routers import stream, analyze, heal, quiz, leaderboard, export, demo
from analysis.routers.analysis_routes import router as analysis_router
from chatbot.routers.chat import router as chat_router
from llm.routers.llm_routes import router as llm_router
from services.agent_stream import router as agent_stream_router
from services.api_agent import router as api_agent_router
from services.correlation_engine import router as correlation_router
from services.leaderboard import router as leaderboard_service_router
from services.log_stream import router as log_stream_router
from services.pdf_export import router as pdf_export_router
from services.performance_agent import router as perf_router
from services.quiz_scheduler import router as quiz_scheduler_router
from services.self_heal import router as self_heal_router
from services.session_utils import router as session_router
from services.autofix_config import router as autofix_config_router
from services.groq_cache import warm_cache
from services.heal_relay import router as heal_relay_router
from services.redis_sessions import get_redis_status

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger("logoracle")

app = FastAPI(title="LogOracle API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLogMiddleware)
app.add_middleware(RequestSizeMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_stream_router,                    tags=["streaming"])
app.include_router(log_stream_router,                      tags=["streaming"])
app.include_router(perf_router,                            tags=["agents"])
app.include_router(analysis_router,                       tags=["analysis"])
app.include_router(correlation_router,                    tags=["analysis"])
app.include_router(api_agent_router,                      tags=["agents"])
app.include_router(autofix_config_router,                  tags=["code"])
app.include_router(analyze.router,     prefix="/analyze",     tags=["analyze"])
app.include_router(self_heal_router,                       tags=["self-heal"])
app.include_router(heal_relay_router,                      tags=["self-heal"])
app.include_router(heal.router,        prefix="/heal",        tags=["heal"])
app.include_router(chat_router,                           tags=["chat"])
app.include_router(llm_router,                            tags=["llm"])
app.include_router(quiz.router,        prefix="/quiz",        tags=["quiz"])
app.include_router(quiz_scheduler_router,                   tags=["growth"])
app.include_router(leaderboard_service_router,             tags=["growth"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])
app.include_router(pdf_export_router,                      tags=["export"])
app.include_router(export.router,      prefix="/export",      tags=["export"])
app.include_router(stream.router,      prefix="/stream",      tags=["stream"])
app.include_router(session_router,                         tags=["session"])
app.include_router(demo.router,                            tags=["demo"])

@app.on_event("startup")
async def startup():
    validate_env_on_startup()
    scenarios = []
    for path in glob.glob("scenarios/*.json"):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                scenarios.append(json.load(handle))
        except Exception:
            pass
    warm_cache(scenarios)
    logger.info("startup_complete scenarios=%s session_backend=%s", len(scenarios), get_redis_status()["backend"])

@app.get("/")
def root():
    return health()

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "session_backend": get_redis_status()}
