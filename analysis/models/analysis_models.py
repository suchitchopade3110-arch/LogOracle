# analysis/models/analysis_models.py
from pydantic import BaseModel
from typing import Optional, List, Literal

Platform = Literal["linux", "windows", "macos", "unknown"]
Distro   = Literal["ubuntu", "arch", "rhel", "alpine", "debian",
                   "windows_server", "windows_10", "windows_11",
                   "macos_ventura", "macos_sonoma", "macos_sequoia",
                   "unknown"]

class LogEvent(BaseModel):
    raw: str
    timestamp: Optional[str] = None
    severity: Literal["CRITICAL", "WARNING", "INFO"] = "INFO"
    source: Optional[str] = None         # process: sshd / nginx / kernel / svchost / launchd
    message: str = ""
    format: str = "generic"
    platform: Platform = "unknown"
    event_id: Optional[str] = None       # Windows Event ID (e.g. "4625" = failed logon)

class ParsedLog(BaseModel):
    format_detected: str
    platform: Platform
    distro: Optional[Distro] = None
    events: List[LogEvent]
    pii_redacted: bool = False
    chunk_count: int = 1
    raw_line_count: int = 0

class DistroFix(BaseModel):
    platform: Platform
    distro: Optional[Distro] = None
    command: str
    description: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    warning: Optional[str] = None        # shown before destructive commands
    powershell: bool = False             # True = must run in PowerShell, not cmd

class ASTIssue(BaseModel):
    pass_number: Literal[1, 3]
    line: Optional[int] = None
    col: Optional[int] = None
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    message: str
    cwe_id: Optional[str] = None
    rule_id: Optional[str] = None
    confidence: float = 0.9
    auto_fixable: bool = False

class HallucinationItem(BaseModel):
    name: str                             # e.g. "requests.get_async"
    status: Literal["valid", "deprecated", "hallucinated"]
    registry: str                         # pypi | npm | maven | nuget
    suggestion: Optional[str] = None      # e.g. "Did you mean requests.get()?"
    version_checked: Optional[str] = None

class HallucinationResult(BaseModel):
    valid_count: int
    deprecated_count: int
    hallucinated_count: int
    items: List[HallucinationItem]
    file_analyzed: Optional[str] = None
