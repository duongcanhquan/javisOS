"""Nới trần RAM một tenant khi host còn trống, kéo về sàn khi không còn chỗ."""
from _paths import SERVER  # noqa: E402,F401

import org_coord as oc
import org_docker as od

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


def row(slug, mem, lim):
    return {"slug": slug, "mem_mb": mem, "limit_mb": lim}


check("768 MB thì nâng sàn", od.memory_should_raise(768 * 1024 * 1024) is True)
check("1024 MB thì giữ sàn", od.memory_should_raise(1024 * 1024 * 1024) is False)
check("2048 MB không bị ensure kéo về sàn", od.memory_should_raise(2048 * 1024 * 1024) is False)
check("chưa đặt trần thì nâng", od.memory_should_raise(0) is True)

# 900 MB muốn lên 2048 cần trống >= 400 + (2048-900) = 1548
check("đủ trống thì nới được", oc.burst_fits(1600, 900) is True)
check("thiếu trống thì không nới", oc.burst_fits(1000, 900) is False)
check("không đọc được RAM trống thì không nới", oc.burst_fits(0, 900) is False)

plan = oc.memory_limit_plan(4000, [row("lan", 900, 1024), row("minh", 200, 1024)])
check("một máy gần đầy được nới 2048", plan.get("lan") == 2048)
check("máy nghỉ ở sàn không bị đụng", "minh" not in plan)

plan = oc.memory_limit_plan(4000, [row("lan", 900, 1024), row("minh", 800, 1024)])
check("hai máy gần đầy thì không nới", plan == {})

plan = oc.memory_limit_plan(4000, [row("lan", 400, 1024), row("minh", 200, 1024)])
check("chưa gần đầy thì giữ sàn", plan == {})

plan = oc.memory_limit_plan(4000, [row("lan", 600, 2048), row("minh", 180, 1024)])
check("đã nới và còn việc thì giữ 2048", plan == {})

plan = oc.memory_limit_plan(4000, [row("lan", 300, 2048), row("minh", 180, 1024)])
check("việc xong thì kéo về 1024", plan.get("lan") == 1024)

plan = oc.memory_limit_plan(4000, [row("lan", 900, 2048), row("minh", 600, 1024)])
check("máy kia mới dùng 600 MB thì người gần đầy vẫn được nới", plan == {})
plan = oc.memory_limit_plan(4000, [row("lan", 900, 2048), row("minh", 800, 1024)])
check("máy kia cũng gần đầy thì kéo người nới về sàn", plan.get("lan") == 1024)

plan = oc.memory_limit_plan(200, [row("lan", 900, 2048)])
check("hết trống và còn hạ an toàn thì về sàn", plan.get("lan") == 1024)

plan = oc.memory_limit_plan(200, [row("lan", 1500, 2048)])
check("đang dùng trên sàn thì không hạ trần", plan == {})

plan = oc.memory_limit_plan(0, [row("lan", 900, 1024)])
check("không đọc được host thì không đổi trần", plan == {})

plan = oc.memory_limit_plan(8000, [row("lan", 3000, 4096)])
check("không hạ trần xuống dưới mức đang dùng", plan == {})

src = (SERVER / "org_docker.py").read_text(encoding="utf-8")
tick = src.split("def tick_coord", 1)[-1].split("\ndef ", 1)[0]
check("tick gọi nới trần", "balance_people_memory()" in tick)
check("nới không tắt máy khác", "def _acquire_slot" in src and "Không tắt máy khác" in src)

if FAIL:
    raise SystemExit(len(FAIL))
print("OK - nới RAM tenant")
