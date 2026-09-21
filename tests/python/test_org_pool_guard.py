"""Rate-limit + concurrency API pool + chat capacity canary."""
from _paths import ROOT, SERVER  # noqa: E402,F401
import os
import tempfile

os.environ["JAVIS_STATE_DIR"] = tempfile.mkdtemp(prefix="javis-poolguard-")
os.environ["JAVIS_ORG_POOL_RPM"] = "3"
os.environ["JAVIS_ORG_POOL_CONCURRENCY"] = "1"
os.environ["JAVIS_ORG_POOL_GLOBAL_CONCURRENCY"] = "2"
os.environ["JAVIS_CHAT_MAX_CONCURRENT"] = "2"

import org_pool_guard as opg  # noqa: E402
from chat_runtime import ChatRuntime  # noqa: E402
import asyncio  # noqa: E402

FAIL = []


def check(label, ok):
    print(("PASS" if ok else "FAIL") + ": " + label)
    if not ok:
        FAIL.append(label)


opg._reset_for_tests()
check("rpm_limit reads env=3", opg.rpm_limit() == 3)
check("rate 1 ok", opg.check_rate("lan") is None)
check("rate 2 ok", opg.check_rate("lan") is None)
check("rate 3 ok", opg.check_rate("lan") is None)
check("rate 4 blocked", opg.check_rate("lan") is not None)

opg._reset_for_tests()
a = opg.Inflight("lan")
a.__enter__()
check("slot a ok", a.ok)
b = opg.Inflight("lan")
b.__enter__()
check("slot b blocked by concurrency=1", (not b.ok) and bool(b.error))
a.__exit__(None, None, None)
c = opg.Inflight("lan")
c.__enter__()
check("slot free after release", c.ok)
c.__exit__(None, None, None)

opg._reset_for_tests()
x = opg.Inflight("a"); x.__enter__()
y = opg.Inflight("b"); y.__enter__()
z = opg.Inflight("c"); z.__enter__()
check("global concurrency blocks 3rd", x.ok and y.ok and (not z.ok))
x.__exit__(None, None, None)
x.__exit__(None, None, None)  # idempotent
snap = opg.snapshot()
check("double exit does not undercount", snap["global_inflight"] == 1)
y.__exit__(None, None, None)

# Concurrency reject must not burn RPM (proxy acquires Inflight before check_rate).
opg._reset_for_tests()
hold = opg.Inflight("lan"); hold.__enter__()
check("hold slot", hold.ok)
blocked = opg.Inflight("lan"); blocked.__enter__()
check("second slot blocked", not blocked.ok)
# Simulate org.py order: only check_rate when slot.ok
if blocked.ok:
    opg.check_rate("lan")
check("rpm unused when concurrency blocked", opg.check_rate("lan") is None)
hold.__exit__(None, None, None)

src = (ROOT / "server" / "routes" / "org.py").read_text(encoding="utf-8")
check("stream uses BackgroundTask for slot release", "BackgroundTask" in src)
check("inflight before check_rate in proxy",
      src.find("Inflight(slug)") < src.find("check_rate(slug)"))
cons = (ROOT / "dashboard" / "console.js").read_text(encoding="utf-8")
check("lazy scripts use /asset/ not /static/?v=",
      "/asset/" in cons and 'return "/static/" + file + "?v="' not in cons)
css = (ROOT / "dashboard" / "console.css").read_text(encoding="utf-8")
check("flush pages hide cview-head",
      ":has(.cview-body.cview-flush)" in css and ".cview-head" in css)

rt = ChatRuntime()


async def _noop():
    await asyncio.sleep(60)


async def _run():
    t1 = asyncio.create_task(_noop())
    t2 = asyncio.create_task(_noop())
    t3 = asyncio.create_task(_noop())
    rt.register_job("s1", t1, "chat:1")
    check("not full at 1/2", not rt.at_capacity())
    rt.register_job("s2", t2, "chat:2")
    check("full at 2", rt.at_capacity())
    rt.register_job("s3", t3, "chat:3")
    check("still full with 3", rt.at_capacity() and rt.active_count() == 3)
    t1.cancel(); t2.cancel(); t3.cancel()
    for t in (t1, t2, t3):
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass
    rt.finish_job("s1", t1)
    rt.finish_job("s2", t2)
    rt.finish_job("s3", t3)


asyncio.run(_run())

# router allowlist guard present
src = (ROOT / "server" / "routes" / "org.py").read_text(encoding="utf-8")
check("pool chat checks allowlist", "allowed_pool_providers" in src)
check("pool chat checks paused/soft-delete", "paused" in src and "is_soft_deleted" in src)
check("proxy uses org_pool_guard", "org_pool_guard" in src)
crt = (ROOT / "server" / "chat_runtime.py").read_text(encoding="utf-8")
check("ChatRuntime.at_capacity", "def at_capacity" in crt)
main = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("WS chat calls at_capacity", "at_capacity()" in main)

if FAIL:
    print("\nFAILED:", ", ".join(FAIL))
    raise SystemExit(1)
print("\nOK - test_org_pool_guard")
