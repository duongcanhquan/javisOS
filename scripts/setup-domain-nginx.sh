#!/usr/bin/env bash
set -euo pipefail
DOMAIN="javis.vietmycollege.com"
IP_HINT="165.101.46.238"

echo "==> Set Javis domain in settings"
docker exec -i javis python3 <<'PY'
import json, pathlib
p = pathlib.Path("/data/state/settings.json")
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg.setdefault("domain", {})
cfg["domain"]["custom"] = "javis.vietmycollege.com"
cfg["domain"]["ssl_enabled"] = True
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
print("saved", cfg["domain"])
PY

echo "==> tls-check"
curl -sS "http://127.0.0.1:7777/tls-check?domain=${DOMAIN}"
echo

echo "==> Write nginx site"
cat > /etc/nginx/sites-available/javis <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        proxy_pass http://127.0.0.1:7777;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        client_max_body_size 100m;
    }
}
EOF

ln -sfn /etc/nginx/sites-available/javis /etc/nginx/sites-enabled/javis
nginx -t
systemctl reload nginx
echo "nginx ok for ${DOMAIN} -> 127.0.0.1:7777"

apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq certbot python3-certbot-nginx

echo "==> DNS lookup"
if getent hosts "$DOMAIN"; then
  RESOLVED=$(getent hosts "$DOMAIN" | awk '{print $1; exit}')
  echo "Resolved: $RESOLVED (VPS should be $IP_HINT)"
  if [ "$RESOLVED" = "$IP_HINT" ]; then
    echo "==> Issuing Let's Encrypt cert"
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect || true
  else
    echo "DNS chÆ°a trá» Ä‘Ãºng IP VPS â€” bá» qua certbot. Sau khi DNS OK cháº¡y láº¡i:"
    echo "  certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email --redirect"
  fi
else
  echo "DNS_NOT_READY for $DOMAIN"
  echo "Táº¡o báº£n ghi A: $DOMAIN -> $IP_HINT rá»“i cháº¡y:"
  echo "  certbot --nginx -d $DOMAIN --non-interactive --agree-tos --register-unsafely-without-email --redirect"
fi

echo "==> done"
