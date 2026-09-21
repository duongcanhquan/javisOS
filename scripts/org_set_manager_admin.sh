#!/usr/bin/env bash
# Đặt admin/admin trên Javis GỐC (javis-manager). Không đụng volume javis-quan.
set -euo pipefail
ENV="${JAVIS_MANAGER_ENV:-/root/javis-manager/.env}"
test -f "$ENV"
if grep -q '^JAVIS_ADMIN_USER=' "$ENV"; then
  sed -i 's/^JAVIS_ADMIN_USER=.*/JAVIS_ADMIN_USER=admin/' "$ENV"
else
  echo 'JAVIS_ADMIN_USER=admin' >> "$ENV"
fi
if grep -q '^JAVIS_ADMIN_PASSWORD=' "$ENV"; then
  sed -i 's/^JAVIS_ADMIN_PASSWORD=.*/JAVIS_ADMIN_PASSWORD=admin/' "$ENV"
else
  echo 'JAVIS_ADMIN_PASSWORD=admin' >> "$ENV"
fi
chmod 600 "$ENV"
docker exec -w /app/server javis-manager python -c "
import config as c
cfg = c.read_settings()
h, salt = c.hash_password('admin')
a = dict(cfg.get('auth') or {})
a['username'] = 'admin'
a['password_hash'] = h
a['salt'] = salt
cfg['auth'] = a
c.write_settings(cfg)
print('SETTINGS_OK')
"
docker restart javis-manager
ok=0
for i in $(seq 1 30); do
  if curl -fsS -m 8 -A Mozilla/5.0 http://127.0.0.1:7778/health >/dev/null 2>&1 \
     || curl -fsS -m 8 -A Mozilla/5.0 https://javis.vietmycollege.com/health >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 2
done
test "$ok" = 1
echo "ADMIN_RESET_OK admin/admin"
