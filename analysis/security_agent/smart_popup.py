import time

CONFIDENCE_THRESHOLD = 0.85
COOLDOWN_SECONDS     = 300

_last_popup_time: float = 0.0

def should_popup(finding: dict, corroborated: bool = True) -> bool:
    global _last_popup_time
    if finding.get("severity") != "CRITICAL":       return False
    if finding.get("confidence", 0) < CONFIDENCE_THRESHOLD: return False
    if not corroborated:                             return False
    if time.time() - _last_popup_time < COOLDOWN_SECONDS:   return False
    _last_popup_time = time.time()
    return True

def format_popup_message(finding: dict, platform: str) -> str:
    msg = finding.get("message", "Critical issue detected")
    if platform == "windows":
        fix = finding.get("fix_windows") or finding.get("fix", "Review Windows Event Viewer")
    elif platform == "macos":
        fix = finding.get("fix_linux") or finding.get("fix", "Check Console.app for details")
    else:
        fix = finding.get("fix_linux") or finding.get("fix", "Review logs immediately")
    return f"{msg}. Suggested fix: {fix}"
