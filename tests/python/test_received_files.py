"""Kho nhận file 3 tầng (inbox → received → Sources/Drive).

    python tests/run.py received_files
"""
from _paths import ROOT, SERVER  # noqa: E402,F401
import tempfile
from pathlib import Path

import received_files as rf

_fails = []


def check(name, cond, detail=""):
    print(("ok   " if cond else "FAIL ") + name + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        _fails.append(name)


def test_chi_nhan_va_work_intent():
    mark = "[Người dùng gửi ảnh qua Zalo, đã tải về: /b/inbox/zalo/a.jpg]"
    check("caption rỗng → chỉ nhận", rf.chi_nhan_thoi("", mark))
    check("caption thường không work → chỉ nhận", rf.chi_nhan_thoi("ảnh đẹp", mark))
    check("caption phân tích → KHÔNG chỉ nhận", not rf.chi_nhan_thoi("phân tích giúp", mark))
    check("caption giữ lại → work", rf.co_y_lam_viec("giữ lại file này"))
    check("đưa lên Drive → work", rf.co_y_lam_viec("đưa lên Drive folder Báo giá"))
    check("/notes không soft-ack", not rf.chi_nhan_thoi("/notes", mark + "\n/notes"))
    check("thiếu marker → không soft-ack", not rf.chi_nhan_thoi("", "xin chào"))


def test_ghi_nhan_va_promote():
    brain = Path(tempfile.mkdtemp(prefix="javis-recv-"))
    inbox = brain / "inbox" / "zalo"
    inbox.mkdir(parents=True)
    src = inbox / "bao-gia.pdf"
    src.write_bytes(b"%PDF-fake")
    e = rf.ghi_nhan(str(brain), channel="zalo", path=str(src), name="bao-gia.pdf",
                    kind="file", caption="", chat_id="abc")
    check("ghi nhận tier inbox", e.get("tier") == "inbox")
    check("sổ có 1 mục", len(rf.load_index(str(brain))) == 1)
    check("brain_from_inbox", rf.brain_from_inbox(str(inbox)) == str(brain))

    kq = rf.xu_ly_tin_dinh_kem(
        str(brain),
        f"[Người dùng gửi file qua Zalo, đã tải về: {src}]\nphân tích giúp",
        "phân tích giúp",
        "zalo",
    )
    check("có ý làm việc → mode engine", kq["mode"] == "engine")
    check("đã promote khỏi inbox", not src.exists())
    dest = Path(kq["entry"]["path"])
    check("file nằm received/", "received" in str(dest) and dest.is_file(), str(dest))
    check("tier received", kq["entry"].get("tier") == "received")
    check("path trong text đã đổi", str(src) not in kq["text"] and str(dest) in kq["text"])


def test_soft_ack_flow():
    brain = Path(tempfile.mkdtemp(prefix="javis-recv-ack-"))
    inbox = brain / "inbox" / "telegram"
    inbox.mkdir(parents=True)
    src = inbox / "photo.jpg"
    src.write_bytes(b"img")
    rf.ghi_nhan(str(brain), channel="telegram", path=str(src), name="photo.jpg", kind="ảnh")
    mark = f"[Người dùng gửi ảnh qua Telegram, gateway đã tải về: {src}]"
    kq = rf.xu_ly_tin_dinh_kem(str(brain), mark, "", "telegram")
    check("không caption → ack", kq["mode"] == "ack")
    check("ack nhắc tầng trung chuyển", "trung chuyển" in (kq.get("reply") or ""))
    check("file vẫn ở inbox", src.is_file())


def test_follow_up_gan_path():
    brain = Path(tempfile.mkdtemp(prefix="javis-recv-fu-"))
    inbox = brain / "inbox" / "zalo"
    inbox.mkdir(parents=True)
    src = inbox / "hd.jpg"
    src.write_bytes(b"x")
    rf.ghi_nhan(str(brain), channel="zalo", path=str(src), name="hd.jpg", kind="ảnh")
    out = rf.xu_ly_tin_chu(str(brain), "phân tích file vừa gửi giúp", channel="zalo")
    check("follow-up có path", "đã tải về" in out or "tầng" in out)
    check("follow-up promote lên received",
          any(e.get("tier") == "received" for e in rf.load_index(str(brain))))
    check("file không còn inbox", not src.exists())


def test_ten_kho():
    t = rf.ten_kho("zalo", "Báo giá ABC.pdf", "2026-09-04")
    check("tên kho có ngày+kênh", t.startswith("2026-09-04_zalo_"))
    check("giữ đuôi", t.endswith(".pdf"))


if __name__ == "__main__":
    test_chi_nhan_va_work_intent()
    test_ghi_nhan_va_promote()
    test_soft_ack_flow()
    test_follow_up_gan_path()
    test_ten_kho()
    print()
    if _fails:
        print("FAILED (%d): %s" % (len(_fails), ", ".join(_fails)))
        raise SystemExit(1)
    print("ALL PASS")
