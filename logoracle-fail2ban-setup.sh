#!/bin/bash
# logoracle-fail2ban-setup.sh
# Run this on any server you want LogOracle to protect.
# Sets up fail2ban with LogOracle-optimized config.
#
# Usage:
#   chmod +x logoracle-fail2ban-setup.sh
#   sudo ./logoracle-fail2ban-setup.sh

set -e

echo "🔮 LogOracle — fail2ban Setup"
echo "================================"

# ── Install fail2ban ──────────────────────────────────────────────────────
if command -v apt-get &>/dev/null; then
    echo "Installing fail2ban (apt)..."
    sudo apt-get update -qq && sudo apt-get install -y fail2ban
elif command -v yum &>/dev/null; then
    echo "Installing fail2ban (yum)..."
    sudo yum install -y epel-release && sudo yum install -y fail2ban
elif command -v dnf &>/dev/null; then
    echo "Installing fail2ban (dnf)..."
    sudo dnf install -y fail2ban
elif command -v pacman &>/dev/null; then
    echo "Installing fail2ban (pacman)..."
    sudo pacman -S --noconfirm fail2ban
elif command -v apk &>/dev/null; then
    echo "Installing fail2ban (apk)..."
    sudo apk add fail2ban
else
    echo "❌ Unknown package manager. Install fail2ban manually."
    exit 1
fi

# ── Write LogOracle jail config ───────────────────────────────────────────
echo "Writing LogOracle jail config..."
sudo tee /etc/fail2ban/jail.d/logoracle.conf > /dev/null << 'EOF'
[DEFAULT]
# Ban for 10 minutes on first offence
bantime  = 600
# Count failures within 5 minutes
findtime = 300
# 5 failures = ban (matches LogOracle threshold)
maxretry = 5
# Ignore localhost
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = %(sshd_log)s
backend  = %(sshd_backend)s
maxretry = 5
bantime  = 600

# Recidive jail — permanent ban for repeat offenders
# Triggered after 3 bans within 1 day
[recidive]
enabled  = true
filter   = recidive
logpath  = /var/log/fail2ban.log
action   = %(action_)s
bantime  = -1
findtime = 86400
maxretry = 3
EOF

# ── Enable and start fail2ban ─────────────────────────────────────────────
echo "Enabling fail2ban..."
sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

# ── Verify ───────────────────────────────────────────────────────────────
echo ""
echo "Checking fail2ban status..."
sudo fail2ban-client status
echo ""
sudo fail2ban-client status sshd

echo ""
echo "✅ fail2ban configured for LogOracle"
echo ""
echo "LogOracle will now use fail2ban as the primary blocking method."
echo "Run the LogOracle agent:"
echo ""
echo "  logoracle-agent --watch /var/log/auth.log --relay --agent-id $(hostname)"
echo ""
echo "Verify fail2ban is working:"
echo "  sudo fail2ban-client status sshd"
echo "  sudo fail2ban-client status recidive"
