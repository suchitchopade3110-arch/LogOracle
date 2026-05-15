"""
services/heal_relay.py
Command relay bridge between LogOracle backend and terminal agent.

Flow:
  1. User approves heal on website → POST /heal/approve
  2. Command queued in /heal/relay/pending (keyed by agent_id)
  3. Terminal agent polls GET /heal/relay/pending/{agent_id}
  4. Agent executes command locally
  5. Agent reports result → POST /heal/relay/result/{token}
  6. Website sees result via GET /heal/relay/status/{token}

New endpoints:
  GET  /heal/relay/pending/{agent_id}  → agent polls this
  POST /heal/relay/result/{token}      → agent reports execution result
  GET  /heal/relay/status/{token}      → frontend checks status
  GET  /heal/relay/agents              → list connected agents
  POST /heal/relay/register            → agent registers itself
"""
import time
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Pending commands keyed by agent_id → list of pending commands
_pending_by_agent: dict = {}

# Execution results keyed by token
_results: dict = {}

# Registered agents
_agents: dict = {}  # agent_id → agent info

COMMAND_TTL    = 300   # 5 min — expire unexecuted commands
RESULT_TTL     = 3600  # 1 hour — keep results


# ── Models ────────────────────────────────────────────────────────────────

class AgentRegisterRequest(BaseModel):
    agent_id:   str           # unique ID for this agent instance
    hostname:   str = ""      # server hostname
    platform:   str = "linux" # linux | windows | macos
    distro:     str = ""      # ubuntu | arch | rhel etc.
    watch_paths: list[str] = []


class RelayResultRequest(BaseModel):
    token:      str
    agent_id:   str
    success:    bool
    output:     str = ""
    returncode: int = 0
    error:      str = ""


# ── Agent registration ────────────────────────────────────────────────────

@router.post("/heal/relay/register")
async def register_agent(req: AgentRegisterRequest):
    """
    Terminal agent calls this on startup.
    Registers itself so backend knows it exists.
    """
    _agents[req.agent_id] = {
        "agent_id":    req.agent_id,
        "hostname":    req.hostname,
        "platform":    req.platform,
        "distro":      req.distro,
        "watch_paths": req.watch_paths,
        "registered_at": time.time(),
        "last_seen":   time.time(),
        "status":      "connected",
    }
    return {
        "registered": True,
        "agent_id":   req.agent_id,
        "message":    f"Agent {req.agent_id} registered. Ready to receive commands.",
    }


@router.get("/heal/relay/agents")
async def list_agents():
    """List all registered agents and their status."""
    now = time.time()
    agents = []
    for agent in _agents.values():
        # Mark as disconnected if not seen in 30s
        last_seen = agent["last_seen"]
        status = "connected" if (now - last_seen) < 30 else "disconnected"
        agents.append({**agent, "status": status,
                        "last_seen_ago": round(now - last_seen)})
    return {"agents": agents, "count": len(agents)}


# ── Command relay ─────────────────────────────────────────────────────────

def queue_command_for_agent(
    agent_id: str,
    token: str,
    command: str,
    description: str,
    finding_message: str = "",
):
    """
    Called by /heal/approve when agent_id is specified.
    Queues command for the agent to pick up.
    """
    if agent_id not in _pending_by_agent:
        _pending_by_agent[agent_id] = []

    _results[token] = {
        "token": token,
        "agent_id": agent_id,
        "status": "pending",
        "success": False,
        "message": f"Waiting for agent {agent_id} to pick up command...",
        "queued_at": time.time(),
    }

    _pending_by_agent[agent_id].append({
        "token":           token,
        "command":         command,
        "description":     description,
        "finding_message": finding_message,
        "queued_at":       time.time(),
        "expires_at":      time.time() + COMMAND_TTL,
        "status":          "pending",
    })


@router.get("/heal/relay/pending/{agent_id}")
async def get_pending_commands(agent_id: str):
    """
    Terminal agent polls this every 5s.
    Returns pending commands and clears the queue.
    """
    # Update last_seen
    if agent_id in _agents:
        _agents[agent_id]["last_seen"] = time.time()
    else:
        # Auto-register unknown agent
        _agents[agent_id] = {
            "agent_id":  agent_id,
            "hostname":  "unknown",
            "platform":  "linux",
            "last_seen": time.time(),
            "status":    "connected",
        }

    now      = time.time()
    pending  = _pending_by_agent.get(agent_id, [])

    # Filter expired commands
    valid    = [c for c in pending if c["expires_at"] > now]
    expired  = [c for c in pending if c["expires_at"] <= now]

    # Mark expired as failed
    for cmd in expired:
        _results[cmd["token"]] = {
            "token":      cmd["token"],
            "status":     "expired",
            "success":    False,
            "output":     "Command expired before agent picked it up.",
            "completed_at": now,
        }

    # Clear queue
    _pending_by_agent[agent_id] = []

    return {
        "agent_id": agent_id,
        "commands": valid,
        "count":    len(valid),
    }


# ── Result reporting ──────────────────────────────────────────────────────

@router.post("/heal/relay/result/{token}")
async def report_result(token: str, req: RelayResultRequest):
    """Terminal agent POSTs here after executing a command."""
    _results[token] = {
        "token":        token,
        "agent_id":     req.agent_id,
        "status":       "success" if req.success else "failed",
        "success":      req.success,
        "output":       req.output,
        "returncode":   req.returncode,
        "error":        req.error,
        "completed_at": time.time(),
        "xp_awarded":   80 if req.success else 0,
    }

    return {"received": True, "token": token}


@router.get("/heal/relay/status/{token}")
async def get_relay_status(token: str):
    """
    Frontend polls this after approving a heal command.
    Returns execution status from the remote agent.
    """
    result = _results.get(token)
    if not result:
        # Check if it's still pending
        for agent_id, cmds in _pending_by_agent.items():
            for cmd in cmds:
                if cmd["token"] == token:
                    return {
                        "token":  token,
                        "status": "pending",
                        "agent":  agent_id,
                        "message": f"Waiting for agent {agent_id} to pick up command...",
                    }
        return {"token": token, "status": "unknown",
                "message": "Token not found. Command may have expired."}

    return result
