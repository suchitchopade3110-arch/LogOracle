# Bug 2 fix: re-export all security agent functions so router can import from here
from .brute_force import detect_brute_force
from .cve_matcher import match_cves
from .smart_popup import should_popup, format_popup_message
