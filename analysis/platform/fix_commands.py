# analysis/platform/fix_commands.py
"""
Platform-aware fix command templates.
Given a fix_type + platform + distro → return DistroFix with exact command.

Linux:   apt / pacman / yum / apk
Windows: PowerShell / sc.exe / netsh / wevtutil
macOS:   brew / launchctl / log / system_profiler
"""
from analysis.models.analysis_models import DistroFix, Platform, Distro
from typing import Optional

# ── Fix templates ──────────────────────────────────────────────────────────
# Structure: fix_type → platform → distro (or "all") → command + meta

FIX_TEMPLATES: dict = {

    # ── SERVICE RESTART ─────────────────────────────────────────────────
    "restart_nginx": {
        "linux": {
            "all":    ("sudo systemctl restart nginx",            "Restart nginx web server",              False),
            "alpine": ("sudo rc-service nginx restart",           "Restart nginx (Alpine OpenRC)",         False),
        },
        "windows": {
            "all":    ("Restart-Service -Name W3SVC -Force",      "Restart IIS service",                   True),
        },
        "macos": {
            "all":    ("sudo brew services restart nginx",        "Restart nginx via Homebrew",            False),
        },
    },

    "restart_sshd": {
        "linux": {
            "all":    ("sudo systemctl restart sshd",             "Restart SSH daemon",                    False),
            "arch":   ("sudo systemctl restart sshd",             "Restart SSH daemon",                    False),
        },
        "macos": {
            "all":    ("sudo launchctl kickstart -k system/com.openssh.sshd", "Restart SSH daemon (macOS)", False),
        },
        "windows": {
            "all":    ("Restart-Service -Name sshd -Force",       "Restart OpenSSH Server (Windows)",      True),
        },
    },

    "restart_redis": {
        "linux":   {"all": ("sudo systemctl restart redis",       "Restart Redis server",                  False)},
        "windows": {"all": ("Restart-Service -Name Redis -Force", "Restart Redis",                         True)},
        "macos":   {"all": ("brew services restart redis",        "Restart Redis via Homebrew",            False)},
    },

    # ── IP BLOCKING ──────────────────────────────────────────────────────
    "block_ip": {
        "linux": {
            "all":    ("sudo ufw deny from {ip} && sudo ufw reload",
                       "Block attacker IP via ufw firewall",      False),
            "rhel":   ("sudo firewall-cmd --add-rich-rule='rule family=ipv4 source address={ip} reject' --permanent && sudo firewall-cmd --reload",
                       "Block attacker IP via firewalld",         False),
            "alpine": ("sudo iptables -I INPUT -s {ip} -j DROP", "Block attacker IP via iptables",         False),
        },
        "windows": {
            "all":    ("New-NetFirewallRule -DisplayName 'Block {ip}' -Direction Inbound -RemoteAddress {ip} -Action Block",
                       "Block attacker IP via Windows Firewall",  True),
        },
        "macos": {
            "all":    ("sudo /usr/libexec/ApplicationFirewall/socketfilterfw --blockapp {ip}",
                       "Block IP via macOS firewall (pfctl recommended for IPs)",  False),
        },
    },

    # ── DISK CLEANUP ─────────────────────────────────────────────────────
    "clean_logs": {
        "linux": {
            "all":    ("sudo journalctl --vacuum-time=7d && sudo find /var/log -name '*.gz' -mtime +7 -delete",
                       "Clean old logs — frees disk space",       False),
        },
        "windows": {
            "all":    ("wevtutil cl System && wevtutil cl Application && wevtutil cl Security",
                       "Clear Windows Event Logs (System/App/Security)", True),
        },
        "macos": {
            "all":    ("sudo log erase --all && sudo rm -rf /private/var/log/asl/*.asl",
                       "Clear macOS Unified Logs and ASL logs",   False),
        },
    },

    # ── PACKAGE / UPDATE ─────────────────────────────────────────────────
    "update_packages": {
        "linux": {
            "ubuntu": ("sudo apt update && sudo apt upgrade -y",  "Update all packages (Ubuntu/Debian)",   False),
            "arch":   ("sudo pacman -Syu --noconfirm",            "Update all packages (Arch)",            False),
            "rhel":   ("sudo yum update -y",                      "Update all packages (RHEL/CentOS)",     False),
            "alpine": ("sudo apk update && sudo apk upgrade",     "Update all packages (Alpine)",          False),
        },
        "windows": {
            "all":    ("Install-Module PSWindowsUpdate -Force; Get-WindowsUpdate -Install -AutoReboot",
                       "Install Windows Updates via PSWindowsUpdate", True),
        },
        "macos": {
            "all":    ("sudo softwareupdate -ia && brew update && brew upgrade",
                       "Install macOS software updates + Homebrew upgrades", False),
        },
    },

    # ── INSTALL MISSING SERVICE ──────────────────────────────────────────
    "install_fail2ban": {
        "linux": {
            "ubuntu": ("sudo apt install -y fail2ban && sudo systemctl enable --now fail2ban",
                       "Install and start fail2ban (blocks brute-force automatically)", False),
            "rhel":   ("sudo yum install -y fail2ban && sudo systemctl enable --now fail2ban",
                       "Install and start fail2ban",              False),
            "arch":   ("sudo pacman -S --noconfirm fail2ban && sudo systemctl enable --now fail2ban",
                       "Install and start fail2ban",              False),
        },
        "windows": {
            "all":    ("# fail2ban not available. Use: New-NetFirewallRule for manual IP blocking.\n"
                       "# Or install WinFail2Ban: https://github.com/glasnt/winfail2ban",
                       "fail2ban not available on Windows — manual firewall rule required", True),
        },
        "macos": {
            "all":    ("brew install fail2ban && sudo brew services start fail2ban",
                       "Install and start fail2ban via Homebrew", False),
        },
    },

    # ── RDP BRUTE-FORCE MITIGATION (Windows only) ────────────────────────
    "mitigate_rdp_bruteforce": {
        "windows": {
            "all":    ("Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\RemoteDesktop\\Parameters' "
                       "-Name 'MaxConnectionPolicy' -Value 0\n"
                       "netsh advfirewall firewall add rule name='RDP Rate Limit' protocol=TCP dir=in localport=3389 action=block remoteip={ip}",
                       "Block RDP brute-force attacker IP + harden policy", True),
        },
    },

    # ── OOM / MEMORY ─────────────────────────────────────────────────────
    "clear_memory_cache": {
        "linux": {
            "all":    ("sudo sync && sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'",
                       "Flush Linux page cache, dentries, and inodes", False),
        },
        "windows": {
            "all":    ("Clear-RecycleBin -Force; [System.GC]::Collect()",
                       "Clear Windows recycle bin + trigger GC (limited effect)", True),
        },
        "macos": {
            "all":    ("sudo purge",
                       "Purge macOS disk cache (frees inactive memory)", False),
        },
    },
}


def get_fix(
    fix_type: str,
    platform: Platform,
    distro: Optional[Distro] = None,
    template_vars: dict = {},
) -> Optional[DistroFix]:
    """
    Return platform-aware DistroFix for a given fix_type.
    Tries: distro-specific → "all" → None.
    """
    if fix_type not in FIX_TEMPLATES:
        return None

    platform_map = FIX_TEMPLATES[fix_type].get(platform)
    if not platform_map:
        return None

    # Try distro-specific first, fall back to "all"
    entry = platform_map.get(distro) or platform_map.get("all")
    if not entry:
        return None

    cmd, desc, is_ps = entry

    # Substitute template variables (e.g. {ip})
    for k, v in template_vars.items():
        cmd = cmd.replace("{" + k + "}", str(v))

    # Warn before destructive commands
    warning = None
    if any(word in cmd for word in ["--vacuum", "wevtutil cl", "log erase", "drop_caches", "purge"]):
        warning = "This command is irreversible. Verify you have a backup or snapshot first."

    return DistroFix(
        platform=platform,
        distro=distro,
        command=cmd,
        description=desc,
        confidence="HIGH" if distro and distro != "unknown" else "MEDIUM",
        warning=warning,
        powershell=is_ps,
    )


def list_fix_types() -> list[str]:
    return list(FIX_TEMPLATES.keys())
