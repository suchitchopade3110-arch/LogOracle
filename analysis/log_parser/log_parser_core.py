"""
analysis/log_parser/log_parser_core.py
Full parse pipeline entry point.
"""
from analysis.platform.detector import detect_platform, detect_distro, detect_log_format
from analysis.log_parser.pii_redactor import redact_pii
from analysis.log_parser.severity_tagger import tag_severity
from analysis.models.analysis_models import ParsedLog


async def parse_log(log_text: str, redact: bool = True) -> ParsedLog:
    """Full parse pipeline. Call this from Suchit's orchestrator."""
    if redact:
        log_text = redact_pii(log_text)

    platform = detect_platform(log_text)
    distro   = detect_distro(log_text, platform)
    fmt      = detect_log_format(log_text, platform)

    parser = _get_parser(fmt)
    events = await parser(log_text)

    return ParsedLog(
        format_detected=fmt,
        platform=platform,
        distro=distro,
        events=events,
        pii_redacted=redact,
        raw_line_count=len(log_text.splitlines()),
    )


def _get_parser(fmt: str):
    from analysis.log_parser.parsers.syslog_parser     import parse as parse_syslog
    from analysis.log_parser.parsers.dmesg_parser      import parse as parse_dmesg
    from analysis.log_parser.parsers.auth_parser       import parse as parse_auth
    from analysis.log_parser.parsers.kern_parser       import parse as parse_kern
    from analysis.log_parser.parsers.journald_parser   import parse as parse_journald
    from analysis.log_parser.parsers.winevt_parser     import parse as parse_winevt
    from analysis.log_parser.parsers.iis_parser        import parse as parse_iis
    from analysis.log_parser.parsers.powershell_parser import parse as parse_ps
    from analysis.log_parser.parsers.unified_log_parser import parse as parse_unified
    from analysis.log_parser.parsers.asl_parser        import parse as parse_asl
    from analysis.log_parser.parsers.crashreport_parser import parse as parse_crash
    from analysis.log_parser.parsers.generic_parser    import parse as parse_generic

    return {
        "syslog":      parse_syslog,
        "dmesg":       parse_dmesg,
        "auth":        parse_auth,
        "kern":        parse_kern,
        "journald":    parse_journald,
        "winevt":      parse_winevt,
        "iis":         parse_iis,
        "powershell":  parse_ps,
        "unified_log": parse_unified,
        "asl":         parse_asl,
        "crashreport": parse_crash,
        "generic":     parse_generic,
    }.get(fmt, parse_generic)
