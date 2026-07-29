#!/bin/bash
# deploy-media-engine.sh
# Run this ON the media engine server (46.62.211.72) as a user with sudo.
# Usage:  bash deploy-media-engine.sh
set -e

BINARY_PATH="/usr/local/bin/mediad"
SERVICE="mediad"

echo "=== Ichebo Media Engine Deploy ==="

# 1. Replace binary (assumes you already uploaded mediad-new via scp)
if [ -f /tmp/mediad-new ]; then
  echo "[1/3] Installing new binary..."
  sudo cp /tmp/mediad-new "$BINARY_PATH"
  sudo chmod +x "$BINARY_PATH"
  echo "    Done: $BINARY_PATH"
else
  echo "[1/3] SKIP: /tmp/mediad-new not found. Upload binary first."
fi

# 2. Update nginx to proxy /upload
echo "[2/3] Checking nginx /upload proxy..."
NGINX_CONF="/etc/nginx/conf.d/nginx-media.conf"
if [ -f "$NGINX_CONF" ] && ! grep -q "location /upload" "$NGINX_CONF"; then
  sudo tee -a "$NGINX_CONF" > /dev/null << 'NGINX'

# Upload portal page (added by deploy-media-engine.sh)
location /upload {
    proxy_pass         http://127.0.0.1:8090/upload;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
}
NGINX
  echo "    Added /upload proxy to $NGINX_CONF"
  sudo nginx -t && sudo nginx -s reload
else
  echo "    /upload already proxied or conf not found — skipping nginx"
fi

# 3. Restart mediad
echo "[3/3] Restarting $SERVICE..."
sudo systemctl restart "$SERVICE"
sleep 2
sudo systemctl status "$SERVICE" --no-pager | head -6

echo ""
echo "=== Deploy complete ==="
echo "Test: curl https://video.ichebo.org/upload"
echo "      Expected: HTTP 400 (token required) — not 404."
