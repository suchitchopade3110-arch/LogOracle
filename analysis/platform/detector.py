# analysis/platform/detector.py
"""
Detect platform (Linux / Windows / macOS) and distro/version
purely from log content signatures — no system calls, works on any host.
"""
import re
from analysis.models.analysis_models import Platform, Distro

# ── Signature maps ─────────────────────────────────────────────────────────

PLATFORM_SIGNATURES: list[tuple[Platform, list[str]]] = [
    ("windows", [
        r"EventID",
        r"Windows Event",
        r"Microsoft-Windows",
        r"ProviderName",
        r"<Event xmlns",
        r"Log Name:\s+",
        r"Event ID:\s+\d+",
        r"Source:\s+\w",
        r"SYSTEM\\CurrentControlSet",
        r"C:\\Windows",
        r"\.evtx",
        r"IIS Web",
        r"W3SVC",
        r"NTLM",
        r"Kerberos",
    ]),
    ("macos", [
        r"com\.apple\.",
        r"kernel\[0\]",
        r"launchd\[1\]",
        r"com\.apple\.xpc",
        r"darwin",
        r"/Library/Logs",
        r"ASL",
        r"macOS",
        r"Mac OS X",
        r"crashreporter",
        r"ReportCrash",
        r"Incident Identifier",   # .crash report header
        r"dyld",
        r"SpringBoard",
    ]),
    ("linux", [
        r"syslog",
        r"journald",
        r"dmesg",
        r"\bkernel:\b",
        r"systemd\[1\]",
        r"/var/log",
        r"sshd\[",
        r"nginx\[",
        r"OOM killer",
        r"EXT4-fs",
        r"\bapt\b",
        r"\byum\b",
        r"\bpacman\b",
    ]),
]

DISTRO_SIGNATURES: list[tuple[Distro, list[str]]] = [
    # Linux
    ("ubuntu",           [r"Ubuntu", r"Debian GNU/Linux", r"\bapt\b", r"dpkg"]),
    ("arch",             [r"Arch Linux", r"\bpacman\b", r"archlinux"]),
    ("rhel",             [r"Red Hat", r"CentOS", r"Rocky Linux", r"AlmaLinux", r"\byum\b", r"\bdnf\b"]),
    ("alpine",           [r"Alpine Linux", r"\bapk\b"]),
    ("debian",           [r"Debian", r"\bapt\b"]),
    # Windows
    ("windows_server",   [r"Windows Server", r"Server 2019", r"Server 2022", r"Server 2016"]),
    ("windows_11",       [r"Windows 11", r"Build 22\d{3}"]),
    ("windows_10",       [r"Windows 10", r"Build 1\d{4}"]),
    # macOS
    ("macos_sequoia",    [r"macOS 15", r"Sequoia"]),
    ("macos_sonoma",     [r"macOS 14", r"Sonoma"]),
    ("macos_ventura",    [r"macOS 13", r"Ventura"]),
]


def detect_platform(log_text: str) -> Platform:
    """Detect platform from log content. Returns linux/windows/macos/unknown."""
    scores: dict[Platform, int] = {"linux": 0, "windows": 0, "macos": 0}

    for platform, patterns in PLATFORM_SIGNATURES:
        for pat in patterns:
            if re.search(pat, log_text, re.IGNORECASE):
                scores[platform] += 1

    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "unknown"


def detect_distro(log_text: str, platform: Platform) -> Distro:
    """Detect specific distro/version. Called after detect_platform."""
    for distro, patterns in DISTRO_SIGNATURES:
        for pat in patterns:
            if re.search(pat, log_text, re.IGNORECASE):
                return distro

    # Fallback by platform
    fallbacks: dict[str, Distro] = {
        "linux":   "ubuntu",
        "windows": "windows_10",
        "macos":   "macos_sonoma",
    }
    return fallbacks.get(platform, "unknown")


def detect_log_format(log_text: str, platform: Platform) -> str:
    """
    Detect specific log format within a platform.
    Returns format string used by format_detector to route to correct parser.
    """
    first_500 = log_text[:2000]

    # Windows
    if platform == "windows":
        if re.search(r"<Event xmlns|EventID|Log Name:", first_500):
            return "winevt"
        if re.search(r"#Software: Microsoft Internet Information", first_500):
            return "iis"
        if re.search(r"Windows PowerShell|PSVersion", first_500):
            return "powershell"
        return "winevt"   # default Windows

    # macOS
    if platform == "macos":
        if re.search(r"Incident Identifier|Exception Type|Crashed Thread", first_500):
            return "crashreport"
        if re.search(r"ASL Module|asl_sender", first_500):
            return "asl"
        return "unified_log"   # default macOS

    # Linux
    if re.search(r"^\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2}", first_500, re.MULTILINE):
        if re.search(r"sshd|sudo|su\[|pam_", first_500):
            return "auth"
        return "syslog"
    if re.search(r"^\[\s*\d+\.\d+\]", first_500, re.MULTILINE):
        return "dmesg"
    if re.search(r"kern\.(warn|err|crit|info)", first_500):
        return "kern"
    if re.search(r"_SOURCE_REALTIME_TIMESTAMP|__CURSOR", first_500):
        return "journald"

    return "generic"
