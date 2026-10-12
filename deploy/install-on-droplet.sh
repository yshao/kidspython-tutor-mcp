#!/bin/sh
# Install/update the Discord bridge on the droplet (idempotent).
#   sh install-on-droplet.sh          # from the mcp/ directory
# The bot token is operator-written (never in git):
#   ssh <droplet> 'umask 077; printf "DISCORD_BOT_TOKEN=...\nDISCORD_CHANNEL_ID=...\n" > /opt/discord-bridge/discord-bridge.env'
set -eu

HOST="${DROPLET_HOST:-198.211.99.14}"
KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519_tunnel}"
DIR=/opt/discord-bridge

run() { ssh -i "$KEY" -o BatchMode=yes "root@$HOST" "$@"; }

echo "== venv + deps"
run "python3 -m venv $DIR/venv 2>/dev/null || true; $DIR/venv/bin/pip -q install -U pip"
run "$DIR/venv/bin/pip -q install discord.py httpx"

echo "== bot file"
rsync -az -e "ssh -i $KEY -o BatchMode=yes" discord_bridge.py "root@$HOST:$DIR/discord_bridge.py"

echo "== systemd unit"
rsync -az -e "ssh -i $KEY -o BatchMode=yes" deploy/discord-bridge.service "root@$HOST:/etc/systemd/system/discord-bridge.service"
run "systemctl daemon-reload"

if run "test -s $DIR/discord-bridge.env && grep -q DISCORD_BOT_TOKEN= $DIR/discord-bridge.env"; then
    run "systemctl enable --now discord-bridge" || true
    run "systemctl restart discord-bridge"
    sleep 4
    run "systemctl is-active discord-bridge && journalctl -u discord-bridge -n 5 --no-pager | tail -5"
    echo "== bridge deployed and started"
else
    run "systemctl disable discord-bridge 2>/dev/null || true"
    cat <<'EOF'
== installed but NOT started: token missing.
Operator steps (also in mcp_PLAN.md / discord_bridge_PLAN.md):
  1. discord.com/developers -> New Application -> Bot -> copy the token
     (enable MESSAGE CONTENT INTENT under Bot -> Privileged Gateway Intents)
  2. OAuth2 URL generator: scope bot; permissions View Channels, Send
     Messages, Read Message History -> invite to your server
  3. Create #chat-kidspython; copy its channel ID (enable Developer Mode)
  4. Write the env (on the droplet):
       umask 077; printf 'DISCORD_BOT_TOKEN=<token>\nDISCORD_CHANNEL_ID=<id>\n' > /opt/discord-bridge/discord-bridge.env
  5. systemctl enable --now discord-bridge
EOF
fi
