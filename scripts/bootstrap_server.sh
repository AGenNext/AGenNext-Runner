#!/usr/bin/env bash
# scripts/bootstrap_server.sh
#
# Called by CI on every deploy.
# - apt update + upgrade runs every time (security patches)
# - Full bootstrap (Docker, user, firewall, swap) runs only once
#   via marker file /var/lib/autonomyx-bootstrap-complete
#
# Idempotent — safe to run repeatedly.

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
MARKER="/var/lib/autonomyx-bootstrap-complete"

# ── Always: wait for apt lock, then update + upgrade ─────────────────────────
echo "=== System packages ==="
for i in $(seq 1 12); do
  fuser /var/lib/dpkg/lock-frontend &>/dev/null || break
  echo "  Waiting for apt lock ($i/12)..."; sleep 5
done

apt-get update -qq
apt-get upgrade -y -qq \
  -o Dpkg::Options::="--force-confdef" \
  -o Dpkg::Options::="--force-confold"
apt-get autoremove -y -qq
echo "  System packages up to date"

# ── First deploy only: full bootstrap ────────────────────────────────────────
if [ -f "$MARKER" ]; then
  echo "=== Server already bootstrapped — skipping one-time setup ==="
  exit 0
fi

echo "=== First deploy: full server bootstrap ==="

# Core packages
apt-get install -y -qq \
  curl wget git ca-certificates gnupg \
  python3 python3-pip openssl jq unzip \
  unattended-upgrades apt-listchanges fail2ban

# Docker
if ! command -v docker &>/dev/null; then
  echo "  Installing Docker Engine..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
  ARCH=$(dpkg --print-architecture)
  echo "deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq \
    docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
  systemctl enable docker
  systemctl start docker
  echo "  Docker installed: $(docker --version)"
else
  echo "  Docker already installed: $(docker --version)"
fi

# ubuntu user
id ubuntu &>/dev/null || useradd -m -s /bin/bash ubuntu
usermod -aG docker ubuntu
mkdir -p /home/ubuntu/.ssh
chmod 700 /home/ubuntu/.ssh
if [ -f /root/.ssh/authorized_keys ]; then
  cp /root/.ssh/authorized_keys /home/ubuntu/.ssh/authorized_keys
  chmod 600 /home/ubuntu/.ssh/authorized_keys
fi
chown -R ubuntu:ubuntu /home/ubuntu/.ssh
echo "  ubuntu user configured"

# Clone repo if not already there
DEPLOY_DIR="/home/ubuntu/autonomyx-model-gateway"
if [ ! -d "$DEPLOY_DIR/.git" ]; then
  git clone https://github.com/OpenAutonomyx/autonomyx-model-gateway.git "$DEPLOY_DIR"
fi
[ -f "$DEPLOY_DIR/.env" ] || cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
chown -R ubuntu:ubuntu "$DEPLOY_DIR"
echo "  Repo ready at $DEPLOY_DIR"

# Unattended security upgrades
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'APT'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
APT
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<'APT'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::Package-Blacklist {
    "docker-ce"; "docker-ce-cli"; "containerd.io";
    "docker-buildx-plugin"; "docker-compose-plugin";
};
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "chinmay@openautonomyx.com";
APT
systemctl enable unattended-upgrades
systemctl restart unattended-upgrades
echo "  Unattended security upgrades configured"

# fail2ban
cat > /etc/fail2ban/jail.local <<'F2B'
[sshd]
enabled  = true
maxretry = 5
bantime  = 3600
findtime = 600
F2B
systemctl enable fail2ban
systemctl restart fail2ban
echo "  fail2ban configured"

# Firewall
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh  comment "SSH"
ufw allow 80   comment "HTTP"
ufw allow 443  comment "HTTPS"
echo "  ufw configured"

# Swap
TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -lt 8192 ] && [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo "/swapfile none swap sw 0 0" >> /etc/fstab
  echo "  2GB swap created"
fi

# frp — install frps as systemd service
echo "→ Installing frps (Fast Reverse Proxy server)..."
FRP_VERSION="0.62.0"
FRP_ARCHIVE="frp_${FRP_VERSION}_linux_amd64.tar.gz"
FRP_URL="https://github.com/fatedier/frp/releases/download/v${FRP_VERSION}/${FRP_ARCHIVE}"

if ! command -v frps &>/dev/null; then
  cd /tmp
  curl -fsSL "$FRP_URL" -o "$FRP_ARCHIVE"
  tar -xzf "$FRP_ARCHIVE"
  cp "frp_${FRP_VERSION}_linux_amd64/frps" /usr/local/bin/frps
  chmod +x /usr/local/bin/frps
  rm -rf "frp_${FRP_VERSION}_linux_amd64" "$FRP_ARCHIVE"
  cd -
  echo "  frps installed: $(frps --version)"
else
  echo "  frps already installed: $(frps --version)"
fi

# Write frps config from template
mkdir -p /etc/frp
FRP_TOKEN="${FRP_TOKEN:-$(openssl rand -hex 32)}"

# Save token to .env if not already there
if ! grep -q "^FRP_TOKEN=" "$DEPLOY_DIR/.env" 2>/dev/null; then
  echo "FRP_TOKEN=${FRP_TOKEN}" >> "$DEPLOY_DIR/.env"
fi

# Write frps.toml with token substituted
sed "s|{{ FRP_TOKEN }}|${FRP_TOKEN}|g"   "$DEPLOY_DIR/frp/frps.toml" > /etc/frp/frps.toml

# Write frpc.toml with token substituted
sed "s|{{ FRP_TOKEN }}|${FRP_TOKEN}|g"   "$DEPLOY_DIR/frp/frpc.toml" > "$DEPLOY_DIR/frp/frpc.rendered.toml"

# Install frps systemd service
cat > /etc/systemd/system/frps.service << 'SVCEOF'
[Unit]
Description=frps - Fast Reverse Proxy Server
After=network.target

[Service]
Type=simple
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/frps -c /etc/frp/frps.toml
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable frps
systemctl restart frps
echo "  frps systemd service running"

# Write marker — bootstrap complete
touch "$MARKER"
echo "=== Server bootstrap complete ==="
