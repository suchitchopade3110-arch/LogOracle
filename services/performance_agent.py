"""
services/performance_agent.py
Real performance agent using psutil.
GET  /analyze/performance  — current system snapshot
GET  /stream/performance   — SSE real-time metrics every 3s
POST /analyze/performance  — analyze a batch of perf metrics for anomalies
"""
import asyncio
import json
import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

CPU_SPIKE_THRESHOLD   = 85.0   # %
RAM_SPIKE_THRESHOLD   = 85.0   # %
DISK_FULL_THRESHOLD   = 90.0   # %
LOAD_SPIKE_MULTIPLIER = 2.0    # load avg > 2x CPU count


class PerformanceAnalyzeRequest(BaseModel):
    snapshots: List[dict] = []


def _get_snapshot() -> dict:
    """Get current system metrics. Falls back to demo data if psutil unavailable."""
    try:
        import psutil
        cpu     = psutil.cpu_percent(interval=0.5)
        ram     = psutil.virtual_memory()
        disk    = psutil.disk_usage("/")
        load    = psutil.getloadavg()
        cpu_count = psutil.cpu_count()
        net     = psutil.net_io_counters()

        return {
            "cpu_percent":     round(cpu, 1),
            "ram_percent":     round(ram.percent, 1),
            "ram_used_gb":     round(ram.used / 1e9, 2),
            "ram_total_gb":    round(ram.total / 1e9, 2),
            "disk_percent":    round(disk.percent, 1),
            "disk_free_gb":    round(disk.free / 1e9, 2),
            "load_avg_1m":     round(load[0], 2),
            "load_avg_5m":     round(load[1], 2),
            "cpu_count":       cpu_count,
            "net_bytes_sent":  net.bytes_sent,
            "net_bytes_recv":  net.bytes_recv,
            "timestamp":       time.time(),
            "source":          "psutil",
        }
    except ImportError:
        # Demo fallback — realistic static values
        return {
            "cpu_percent":  42.3,
            "ram_percent":  67.8,
            "ram_used_gb":  10.8,
            "ram_total_gb": 16.0,
            "disk_percent": 54.2,
            "disk_free_gb": 183.4,
            "load_avg_1m":  1.82,
            "load_avg_5m":  1.65,
            "cpu_count":    8,
            "net_bytes_sent": 1024000,
            "net_bytes_recv": 4096000,
            "timestamp":    time.time(),
            "source":       "demo",
        }


def _analyze_snapshot(snap: dict) -> List[dict]:
    """Check snapshot for anomalies. Return findings."""
    findings = []

    if snap["cpu_percent"] >= CPU_SPIKE_THRESHOLD:
        findings.append({
            "agent":      "performance",
            "severity":   "CRITICAL" if snap["cpu_percent"] >= 95 else "WARNING",
            "message":    f"CPU spike: {snap['cpu_percent']}% utilization "
                          f"(threshold: {CPU_SPIKE_THRESHOLD}%)",
            "confidence": 0.97,
            "fix":        "Identify top processes: top -b -n1 | head -20. "
                          "Kill runaway process: sudo kill -9 <PID>",
            "finding_id": "perf_cpu_spike",
        })

    if snap["ram_percent"] >= RAM_SPIKE_THRESHOLD:
        findings.append({
            "agent":      "performance",
            "severity":   "CRITICAL" if snap["ram_percent"] >= 95 else "WARNING",
            "message":    f"Memory pressure: {snap['ram_percent']}% used "
                          f"({snap['ram_used_gb']}GB / {snap['ram_total_gb']}GB)",
            "confidence": 0.97,
            "fix":        "sudo sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'. "
                          "Check for leaks: ps aux --sort=-%mem | head -10",
            "finding_id": "perf_ram_pressure",
        })

    if snap["disk_percent"] >= DISK_FULL_THRESHOLD:
        findings.append({
            "agent":      "performance",
            "severity":   "CRITICAL" if snap["disk_percent"] >= 98 else "WARNING",
            "message":    f"Disk nearly full: {snap['disk_percent']}% used "
                          f"({snap['disk_free_gb']}GB free)",
            "confidence": 0.99,
            "fix":        "sudo journalctl --vacuum-time=7d && "
                          "sudo find /var/log -name '*.gz' -mtime +7 -delete",
            "finding_id": "perf_disk_full",
        })

    load_threshold = snap["cpu_count"] * LOAD_SPIKE_MULTIPLIER
    if snap["load_avg_1m"] >= load_threshold:
        findings.append({
            "agent":      "performance",
            "severity":   "WARNING",
            "message":    f"High load average: {snap['load_avg_1m']} "
                          f"({LOAD_SPIKE_MULTIPLIER}x CPU count of {snap['cpu_count']})",
            "confidence": 0.88,
            "fix":        "Check process tree: ps auxf. "
                          "Identify I/O wait: iostat -x 1 5",
            "finding_id": "perf_high_load",
        })

    return findings


@router.get("/analyze/performance")
async def get_performance():
    """Single snapshot + anomaly analysis."""
    snap     = _get_snapshot()
    findings = _analyze_snapshot(snap)
    return {
        "snapshot":      snap,
        "findings":      findings,
        "finding_count": len(findings),
        "healthy":       len(findings) == 0,
    }


@router.post("/analyze/performance")
async def analyze_performance(req: PerformanceAnalyzeRequest):
    """Analyze supplied performance snapshots, or the current snapshot if none are supplied."""
    snapshots = req.snapshots or [_get_snapshot()]
    findings = []
    for index, snapshot in enumerate(snapshots):
        for finding in _analyze_snapshot(snapshot):
            finding = dict(finding)
            finding["snapshot_index"] = index
            findings.append(finding)
    return {
        "snapshot_count": len(snapshots),
        "findings": findings,
        "finding_count": len(findings),
        "healthy": len(findings) == 0,
    }


async def _stream_performance(interval: float = 3.0):
    """SSE stream of performance metrics."""
    while True:
        snap     = _get_snapshot()
        findings = _analyze_snapshot(snap)
        payload  = {
            "type":     "perf_update",
            "snapshot": snap,
            "findings": findings,
        }
        yield f"data: {json.dumps(payload)}\n\n"
        await asyncio.sleep(interval)


@router.get("/stream/performance")
async def stream_performance():
    """SSE real-time performance metrics every 3s."""
    return StreamingResponse(
        _stream_performance(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
