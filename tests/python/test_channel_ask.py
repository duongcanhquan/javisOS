"""Test hạ khối điều khiển xuống chữ cho kênh không phải web (v0.9.61). Chạy tay / CI:

    python tests/run.py channel_ask

KHÔNG mạng. Phủ: JAVIS_ASK xuống danh sách đánh số, JAVIS_METRICS biến mất sạch
(hồi quy cho lỗi rò sang Telegram), JSON hỏng không nuốt câu trả lời.
"""
from _paths import ROOT, SERVER  # noqa: E402,F401  - nạp server/ vào sys.path (xem tests/python/_paths.py)
import os
import sys
import tempfile

os.environ.setdefault("JAVIS_STATE_DIR", tempfile.mkdtemp(prefix="javis-asktest-"))

import channel_context  # noqa: E402

_fails = []


def check(name, cond):
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        _fails.append(name)


strip = channel_context.strip_control_blocks

# ---- 1. JAVIS_ASK xuống danh sách đánh số ----
ask = ('Doanh thu hôm nay 250k.\n\n<!-- JAVIS_ASK: {"question":"Xem kỳ nào?",'
       '"options":[{"label":"Tuần này","desc":"7 ngày"},{"label":"Tháng này"}]} -->')
out = strip(ask)
check("ask: giữ câu trả lời", "Doanh thu hôm nay 250k." in out)
check("ask: có câu hỏi", "Xem kỳ nào?" in out)
check("ask: đánh số 1", "1. Tuần này" in out)
check("ask: đánh số 2", "2. Tháng này" in out)
check("ask: không lộ khối thô", "JAVIS_ASK" not in out and "<!--" not in out)

# ---- 2. JAVIS_METRICS biến mất sạch (hồi quy lỗi rò sang Telegram) ----
met = 'Báo cáo xong.\n\n<!-- JAVIS_METRICS: [{"label":"Doanh thu","value":"250k"}] -->'
out = strip(met)
check("metrics: biến mất sạch", "JAVIS_METRICS" not in out and "<!--" not in out)
check("metrics: giữ câu trả lời", out.strip() == "Báo cáo xong.")

# ---- 3. Cả hai khối cùng lúc ----
both = ('Báo cáo.\n<!-- JAVIS_METRICS: [{"label":"A","value":"1"}] -->\n'
        '<!-- JAVIS_ASK: {"question":"Chọn?","options":[{"label":"a"}]} -->')
out = strip(both)
check("cả hai: metrics mất, ask thành danh sách", "JAVIS_METRICS" not in out
      and "1. a" in out and "Chọn?" in out)

# ---- 4. JSON hỏng: bỏ khối rác nhưng KHÔNG nuốt câu trả lời ----
bad = 'Câu trả lời thật.\n<!-- JAVIS_ASK: {"question": hỏng rồi -->'
out = strip(bad)
check("json hỏng: giữ câu trả lời", out.strip() == "Câu trả lời thật.")
check("json hỏng: không lộ khối thô", "JAVIS_ASK" not in out)

# ---- 5. Thừa lựa chọn cắt còn 4 ----
many = ('<!-- JAVIS_ASK: {"question":"Chọn?","options":[{"label":"a"},{"label":"b"},'
        '{"label":"c"},{"label":"d"},{"label":"e"}]} -->')
out = strip(many)
check("thừa lựa chọn: cắt còn 4", "4. d" in out and "5. e" not in out)

# ---- 6. Không có khối: trả nguyên văn ----
check("không khối: giữ nguyên", strip("Chỉ là câu trả lời.") == "Chỉ là câu trả lời.")
check("text rỗng: không nổ", strip("") == "")
check("None: không nổ", strip(None) == "")

# ---- 7. Gọt nhật ký "Em sẽ…" (ca UAV 16/09: prompt cấm rồi model vẫn viết) ----
gon = channel_context.gon_nhat_ky_lam_viec
UAV = (
    "Em sẽ dùng slide-wright để dựng lại deck UAV theo bản proposal có sẵn, bổ sung logo, "
    "ảnh minh họa và biểu đồ trực quan rồi xuất PDF gửi anh Quân.\n\n"
    "Em đã thấy bộ UAV hiện có trong projects/uav, có cả proposal, slide cũ, landing page "
    "và ảnh minh họa. Em sẽ dựng bản mới trong exports/slides/ để không làm hỏng file cũ.\n\n"
    "Em sẽ lấy nội dung từ đề án UAV hiện có, nhưng phần nhìn sẽ làm mới theo hướng "
    "aero lab 16:9.\n\n"
    "Em sẽ làm full deck luôn theo yêu cầu.\n\n"
    "Em đã xác định môi trường không có Chrome hệ thống, nên em sẽ xuất PDF bằng bộ render "
    "PDF sẵn có.\n\n"
    "Em sẽ ghi deck HTML mới vào thư mục xuất riêng.\n\n"
    "Em đã dựng xong khung HTML 10 slide, bước tiếp theo là xuất PDF.\n\n"
    "PDF đầu tiên bị bung thành nhiều trang vì bộ xuất PDF quy đổi inch khác với canvas. "
    "Em sẽ chỉnh CSS in sang đúng canvas pixel.\n\n"
    "Bản PDF từ HTML bị tách trang không đúng. Em sẽ xuất lại PDF trực tiếp bằng canvas 16:9.\n\n"
    "Bản PDF mới đã đúng 10 trang / 10 slide. Em sẽ gửi file PDF cho anh Quân ngay.\n\n"
    "Đã thiết kế lại và gửi anh Quân slide proposal UAV bản mới."
)
ra = gon(UAV)
check("CANARY: nhật ký UAV chỉ còn câu chốt Đã…",
      ra == "Đã thiết kế lại và gửi anh Quân slide proposal UAV bản mới.")
check("CANARY: không còn Em sẽ / Em đã thấy",
      "Em sẽ" not in ra and "Em đã thấy" not in ra)
check("câu kết quả thường không bị đụng",
      gon("Doanh thu hôm nay 12 triệu, tăng 8% so với tuần trước.")
      == "Doanh thu hôm nay 12 triệu, tăng 8% so với tuần trước.")
check("rỗng không nổ", gon("") == "" and gon(None) == "")

main_py = (ROOT / "server" / "main.py").read_text(encoding="utf-8")
check("dashboard/Telegram gọt nhật ký trước khi gửi",
      "gon_nhat_ky_lam_viec" in main_py)

if _fails:
    print(f"\nFAIL - {len(_fails)} test: {_fails}")
    sys.exit(1)
print("\nOK - test_channel_ask: tất cả pass")
