"""
logoracle_agent/relay.py — updated with fail2ban whitelist.
Drop-in replacement for existing relay.py.
"""
import re
import shlex
import subprocess
import threading
import time
import httpx
from rich.console import Console

console = Console()

# Mirrors backend whitelist — double validation
LOCAL_WHITELIST = [
    # fail2ban (primary)
    r"^sudo fail2ban-client set sshd banip (\d{1,3}\.){3}\d{1,3}$",
    r"^sudo fail2ban-client set sshd unbanip (\d{1,3}\.){3}\d{1,3}$",
    r"^sudo fail2ban-client set recidive banip (\d{1,3}\.){3}\d{1,3}$",
    r"^sudo fail2ban-client status sshd$",
    r"^sudo fail2ban-client reload$",
    r"^sudo systemctl restart fail2ban$",
    # UFW
    r"^sudo ufw deny from (\d{1,3}\.){3}\d{1,3} to any port 22$",
    r"^sudo ufw deny from (\d{1,3}\.){3}\d{1,3}$",
    r"^sudo ufw reload$",
    r"^sudo ufw delete deny from (\d{1,3}\.){3}\d{1,3}$",
    # iptables
    r"^sudo iptables -A INPUT -s (\d{1,3}\.){3}\d{1,3} -p tcp --dport 22 -j DROP$",
    r"^sudo iptables -D INPUT -s (\d{1,3}\.){3}\d{1,3} -p tcp --dport 22 -j DROP$",
    r"^sudo iptables-save > /etc/iptables/rules\.v4$",
    # firewall-cmd
    r"^sudo firewall-cmd --add-rich-rule='rule family=ipv4 source address=(\d{1,3}\.){3}\d{1,3} port port=22 protocol=tcp reject' --permanent$",
    r"^sudo firewall-cmd --reload$",
    # services
    r"^sudo systemctl restart (sshd|ssh|nginx|apache2|redis|postgresql|mysql|mongodb)$",
    r"^sudo systemctl stop (sshd|ssh|nginx|apache2|redis|postgresql|mysql|mongodb)$",
    # logs
    r"^sudo journalctl --vacuum-time=\d+d$",
    r"^sudo journalctl --vacuum-size=\d+(M|G)$",
    # macOS
    r"^echo 'block in quick from (\d{1,3}\.){3}\d{1,3} to any' \| sudo pfctl -f -$",
]

POLL_INTERVAL = 5.0


def _is_whitelisted(command: str) -> bool:
    for pattern in LOCAL_WHITELIST:
        if re.match(pattern, command.strip()):
            return True
    return False


def _execute(command: str) -> tuple[bool, str, int]:
    try:
        shell = any(token in command for token in ["|", ">", "'", "\""])
        result = subprocess.run(
            command if shell else shlex.split(command),
            shell=shell,
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout or result.stderr or "Command completed."
        return result.returncode == 0, output, result.returncode
    except subprocess.TimeoutExpired:
        return False, "Timed out after 15 seconds.", -1
    except Exception as e:
        return False, str(e), -1


class HealRelay:
    def __init__(self, base_url: str, agent_id: str, dry_run: bool = False):
        self.base_url = base_url
        self.agent_id = agent_id
        self.dry_run  = dry_run
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._running = False
        self._client  = httpx.Client(timeout=10.0)
        self.executed = 0
        self.failed   = 0

    def start(self):
        self._running = True
        self._thread.start()
        console.print(f"[green]✓ Heal relay active[/green] (polling every {POLL_INTERVAL}s)")
        if self.dry_run:
            console.print("[yellow]⚠ DRY RUN — commands will NOT execute[/yellow]")

    def stop(self):
        self._running = False

    def _run(self):
        while self._running:
            try:
                self._poll()
            except Exception:
                pass
            time.sleep(POLL_INTERVAL)

    def _poll(self):
        r = self._client.get(
            f"{self.base_url}/heal/relay/pending/{self.agent_id}"
        )
        if r.status_code != 200:
            return
        for cmd in r.json().get("commands", []):
            self._handle(cmd)

    def _handle(self, cmd: dict):
        token   = cmd["token"]
        command = cmd["command"]
        desc    = cmd["description"]

        console.print(f"\n[bold yellow]🩹 HEAL COMMAND[/bold yellow]")
        console.print(f"  [cyan]{command}[/cyan]")
        console.print(f"  {desc}")

        if not _is_whitelisted(command):
            console.print("[red]✗ REJECTED — not in local whitelist[/red]")
            self._report(token, False, "Rejected: not in local whitelist.", -1)
            self.failed += 1
            return

        if self.dry_run:
            console.print("[yellow]⚠ DRY RUN — skipped[/yellow]")
            self._report(token, True, f"[DRY RUN] Would execute: {command}", 0)
            return

        success, output, rc = _execute(command)
        if success:
            console.print(f"[green]✓ Done (rc={rc})[/green]")
            self.executed += 1
        else:
            console.print(f"[red]✗ Failed (rc={rc}): {output[:80]}[/red]")
            self.failed += 1

        self._report(token, success, output, rc)

    def _report(self, token: str, success: bool, output: str, rc: int):
        try:
            self._client.post(
                f"{self.base_url}/heal/relay/result/{token}",
                json={"token": token, "agent_id": self.agent_id,
                      "success": success, "output": output[:1000], "returncode": rc},
            )
        except Exception:
            pass
