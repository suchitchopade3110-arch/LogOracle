import json
from pathlib import Path

from fastapi import APIRouter, HTTPException


router = APIRouter()

SCENARIO_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def _load_scenario(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data


def _scenario_path(scenario_id: str) -> Path:
    safe_id = scenario_id.replace("/", "").replace("\\", "")
    path = SCENARIO_DIR / f"{safe_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {scenario_id}")
    return path


@router.get("/demo/scenarios")
def list_scenarios():
    scenarios = []
    for path in sorted(SCENARIO_DIR.glob("*.json")):
        data = _load_scenario(path)
        scenarios.append({
            "scenario_id": data["scenario_id"],
            "title": data["title"],
            "category": data.get("category", "demo"),
            "severity": data.get("severity", "INFO"),
            "endpoint": data["endpoint"],
            "chat_prompt": data.get("chat_prompt", ""),
        })
    return {"count": len(scenarios), "scenarios": scenarios}


@router.post("/demo/run/{scenario_id}")
async def run_scenario(scenario_id: str):
    data = _load_scenario(_scenario_path(scenario_id))
    endpoint = data.get("endpoint")
    payload = data.get("payload", {})
    if not endpoint or not endpoint.startswith("/"):
        raise HTTPException(status_code=400, detail="Scenario endpoint must be an absolute path")

    result = await _dispatch(endpoint, payload)

    return {
        "scenario": {
            "scenario_id": data["scenario_id"],
            "title": data["title"],
            "category": data.get("category", "demo"),
            "severity": data.get("severity", "INFO"),
            "endpoint": endpoint,
            "chat_prompt": data.get("chat_prompt", ""),
            "expected": data.get("expected", {}),
        },
        "status_code": 200,
        "result": result,
    }


async def _dispatch(endpoint: str, payload: dict):
    if endpoint == "/analyze/log":
        from analysis.routers.analysis_routes import LogRequest, analyze_log
        return await analyze_log(LogRequest(**payload))
    if endpoint == "/analyze/code":
        from analysis.routers.analysis_routes import CodeRequest, analyze_code
        return await analyze_code(CodeRequest(**payload))
    if endpoint == "/analyze/hallucination":
        from analysis.routers.analysis_routes import HallucinationRequest, analyze_hallucination
        return await analyze_hallucination(HallucinationRequest(**payload))
    if endpoint == "/analyze/intent":
        from routers.analyze import analyze_intent
        return await analyze_intent(payload)
    raise HTTPException(status_code=400, detail=f"Scenario endpoint is not demo-runnable: {endpoint}")
