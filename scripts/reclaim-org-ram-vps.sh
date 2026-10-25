#!/usr/bin/env bash
# Nhả RAM gấp trên VPS: đặt idle=15, trần tay hợp lý, tắt máy nghỉ / vượt chỗ.
# Não + volume giữ nguyên. Chạy trên VPS (manager đang sống).
set -euo pipefail

echo "=== HOST trước ==="
free -m | head -3
date -u

echo "=== Cấu hình điều phối + tắt máy nghỉ ==="
docker exec javis-manager python -c '
import sys, time
sys.path.insert(0, "/app/server")
import org_tenants as ot
import org_coord as oc
import org_docker as od

# Trần tay: tối đa gợi ý RAM (12GB → 8). Idle 15 phút.
suggest = int(oc.suggest_slots(oc.host_mem_mb()[0]) or 8)
hand = min(max(suggest, 1), 8)
c = oc.put_coord(max_running=hand, idle_minutes=15)
print("coord_set max_running", c.get("max_running"), "idle_minutes", c.get("idle_minutes"),
      "effective", oc.effective_max(), "suggest", suggest)

now = int(time.time())
idle_lim = 15 * 60
cap = int(oc.effective_max())
running = od.people_running()
print("people_running_before", len(running), [t.get("slug") for t in running])

# 1) Tắt máy không tín hiệu người >= 15 phút
stopped = []
for t in list(running):
    slug = str(t.get("slug") or "")
    if not slug or t.get("protected"):
        continue
    cname = str(t.get("container") or "")
    ts = od.read_last_active(cname, t, assume_running=True)
    age = now - ts if ts > 0 else 10**9
    if age >= idle_lim:
        try:
            od.stop(slug, park=False)
            stopped.append((slug, "idle", age))
            print("STOP_IDLE", slug, "age_sec", age)
        except Exception as e:
            print("FAIL_IDLE", slug, e)

running = od.people_running()
# 2) Vẫn vượt trần → tắt máy nghỉ lâu nhất (grace 90s)
while len(running) > cap:
    victim = od._pick_evict("", grace_sec=oc.PRESSURE_IDLE_SEC)
    if not victim:
        # không có máy nghỉ đủ lâu: vẫn tắt máy last_active cũ nhất (không protected)
        oldest, oldest_ts = "", now + 1
        for t in running:
            slug = str(t.get("slug") or "")
            if not slug or t.get("protected"):
                continue
            cname = str(t.get("container") or "")
            ts = od.read_last_active(cname, t, assume_running=True) or 1
            if ts < oldest_ts:
                oldest_ts, oldest = ts, slug
        victim = oldest
    if not victim:
        break
    try:
        od.stop(victim, park=False)
        stopped.append((victim, "over_cap", 0))
        print("STOP_CAP", victim)
        running = [t for t in running if str(t.get("slug") or "") != victim]
    except Exception as e:
        print("FAIL_CAP", victim, e)
        break

try:
    od.sync_park()
except Exception as e:
    print("park", e)

print("stopped", len(stopped), stopped)
print("people_running_after", len(od.people_running()), [t.get("slug") for t in od.people_running()])
print("coord_now", oc.coord().get("max_running"), oc.coord().get("idle_minutes"), "eff", oc.effective_max())
'

echo "=== HOST sau ==="
free -m | head -3
echo "=== docker stats ==="
names=$(docker ps --format '{{.Names}}' | grep -E '^javis-' | tr '\n' ' ' || true)
if [ -n "$names" ]; then
  docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}' $names
fi
echo RECLAIM_ORG_RAM_DONE
