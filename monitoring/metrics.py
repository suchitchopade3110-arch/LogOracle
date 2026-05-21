from prometheus_client import Counter, Histogram, Gauge, Info

REQUEST_COUNT = Counter(
    "logoracle_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "logoracle_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ANALYSIS_COUNT = Counter(
    "logoracle_analyses_total",
    "Total log analyses run",
    ["status"]
)

ANALYSIS_DURATION = Histogram(
    "logoracle_analysis_duration_seconds",
    "Log analysis pipeline duration",
    buckets=[1, 2, 5, 10, 30, 60]
)

GROQ_TOKENS_USED = Counter(
    "logoracle_groq_tokens_total",
    "Total GROQ tokens consumed"
)

ACTIVE_AGENTS = Gauge(
    "logoracle_active_agents",
    "Currently active agents",
    ["agent_type"]
)

FINDINGS_DETECTED = Counter(
    "logoracle_findings_total",
    "Findings detected",
    ["severity", "category"]
)

APP_INFO = Info("logoracle_app", "LogOracle app info")
APP_INFO.info({
    "version": "2.0.0",
    "model": "llama3.1-8b",
    "inference": "groq"
})
