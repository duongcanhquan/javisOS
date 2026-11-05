#!/usr/bin/env bash
# Nhả RAM gấp trên VPS (chỉ khi FORCE_STOP=1): tắt máy nghỉ / vượt chỗ.
# Mặc định: KHÔNG tự tắt tenant, KHÔNG ép idle=15 (chủ muốn máy luôn mở).
# Não + volume giữ nguyên. Chạy trên VPS (manager đang sống).
#
#   IDLE_MINUTES=0 FORCE_STOP=0 bash scripts/reclaim-org-ram-vps.sh   # chỉ chỉnh coord
#   FORCE_STOP=1 IDLE_MINUTES=15 bash ...                          # nhả RAM kiểu cũ
set -euo pipefail

IDLE_MINUTES="${IDLE_MINUTES:-0}"
FORCE_STOP="${FORCE_STOP:-0}"
MAX_RUNNING="${MAX_RUNNING:-20}"

echo "=== HOST trước ==="
free -m | head -3
date -u
echo "IDLE_MINUTES=$IDLE_MINUTES FORCE_STOP=$FORCE_STOP MAX_RUNNING=$MAX_RUNNING"

echo "=== Cấu hình điều phối (mặc định không tự tắt) ==="
docker exec -e IDLE_MINUTES="$IDLE_MINUTES" -e MAX_RUNNING="$MAX_RUNNING" -e FORCE_STOP="$FORCE_STOP" javis-manager python -c '
import os, sys, time
sys.path.insert(0, "/app/server")
import org_tenants as ot
import org_coord as oc
import org_docker as od

idle = int(os.environ.get("IDLE_MINUTES") or 0)
hand = int(os.environ.get("MAX_RUNNING") or 20)
hand = max(1, min(20, hand))
c = oc.put_coord(max_running=hand, idle_minutes=idle)
print("coord_set max_running", c.get("max_running"), "idle_minutes", c.get("idle_minutes"),
      "effective", oc.effective_max(), "suggest", oc.suggest_slots(oc.host_mem_mb()[0]))

force = (os.environ.get("FORCE_STOP") or "0").strip() == "1"
running = od.people_running()
print("people_running_before", len(running), [t.get("slug") for t in running])
stopped = []
if not force:
    print("SKIP_STOP (FORCE_STOP!=1) — chỉ giữ coord, không tắt máy người")
else:
    now = int(time.time())
    idle_lim = max(60, idle * 60) if idle > 0 else 15 * 60
    cap = int(oc.effective_max())
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
    while len(running) > cap:
        victim = od._pick_evict("", grace_sec=oc.PRESSURE_IDLE_SEC)
        if not victim:
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
