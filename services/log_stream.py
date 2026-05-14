"""
services/log_stream.py
SSE real-time log tail endpoint.
Accepts log lines via POST /ingest/logs, streams them to all SSE subscribers.
"""
import asyncio
import json
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
from collections import deque

router = APIRouter()

# Ring buffer of last 500 log lines — shared across all SSE connections
_log_buffer: deque = deque(maxlen=500)
_subscribers: list = []  # list of asyncio.Queue


class LogIngestRequest(BaseModel):
    lines: List[str]
    source: str = "manual"  # manual | journald | syslog | auth


def _broadcast(event: dict):
    """Push event to all active SSE subscribers."""
    msg = f"data: {json.dumps(event)}\n\n"
    dead = []
    for q in _subscribers:
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.remove(q)


@router.post("/ingest/logs")
async def ingest_logs(req: LogIngestRequest):
    """
    Push log lines into the stream.
    Called by: local logoracle-agent script, demo runner, manual paste.
    """
    for line in req.lines:
        entry = {
            "type":      "log_line",
            "line":      line,
            "source":    req.source,
            "timestamp": time.time(),
        }
        _log_buffer.append(entry)
        _broadcast(entry)

    return {"ingested": len(req.lines)}


async def _stream_log_events(queue: asyncio.Queue):
    """Yield buffered history then live events."""
    # 1. Send last 100 buffered lines immediately on connect
    for entry in list(_log_buffer)[-100:]:
        yield f"data: {json.dumps({**entry, 'buffered': True})}\n\n"

    # 2. Stream live events
    while True:
        try:
            msg = await asyncio.wait_for(queue.get(), timeout=30.0)
            yield msg
        except asyncio.TimeoutError:
            # Keepalive ping
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"


@router.get("/stream/logs")
async def stream_logs():
    """
    SSE endpoint — frontend connects once, receives log lines in real time.
    EventSource: new EventSource('/stream/logs')
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)
    _subscribers.append(queue)

    async def cleanup():
        async for chunk in _stream_log_events(queue):
            yield chunk
        if queue in _subscribers:
            _subscribers.remove(queue)

    return StreamingResponse(
        cleanup(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering":"no",
            "Access-Control-Allow-Origin": "*",
        },
    )
