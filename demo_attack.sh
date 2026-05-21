#!/bin/bash

LOG_FILE="${1:-/tmp/demo.log}"
COUNT="${2:-35}"

echo "🔥 LogOracle Attack Simulation"
echo "   Target log: $LOG_FILE"
echo "   Injecting $COUNT brute-force entries..."
echo ""

> "$LOG_FILE"

for i in $(seq 1 $COUNT); do
    IP="192.168.1.$((RANDOM % 50 + 1))"
    USER=$(shuf -n1 -e root admin ubuntu debian ec2-user)
    PORT=$((RANDOM % 10000 + 20000))
    TIMESTAMP=$(date "+%b %d %H:%M:%S")

    echo "$TIMESTAMP server sshd[$$]: Failed password for $USER from $IP port $PORT ssh2" >> "$LOG_FILE"
    echo "  [$i/$COUNT] Failed password for $USER from $IP"
    sleep 0.15
done

echo ""
echo "✅ Attack simulation complete."
echo "   LogOracle should detect brute-force pattern in findings panel."
echo ""
echo "   Launch TUI to watch:"
echo "   python logoracle_cli.py --watch $LOG_FILE"
