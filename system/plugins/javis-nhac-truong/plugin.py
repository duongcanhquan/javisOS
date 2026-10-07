"""Tool `javis_nhac_truong`: chat giao việc cho phòng và chạy, cùng đường với nút trên trang.

Trước tool này trang Nhạc trưởng chỉ có API cho màn hình. Não chat không thấy phòng nào,
không có chỗ hỏi lại, và không gọi được nút Chạy. Tool này đọc phòng của đúng brain đang chat,
chỉ giao khi tên phòng khớp một phòng, và nếu chưa rõ thì trả danh sách để hỏi, không đoán.
"""
from __future__ import annotations

import nhac_truong as nt
import routes.nhac_truong as rte


def _kho(ctx):
    if not getattr(ctx, "vault_root", None):
        return None
    return nt.Kho(ctx.vault_root)


def _liet(ctx) -> str:
    kho = _kho(ctx)
    if kho is None:
        return "ERROR: chưa biết brain nào nên không đọc được phòng."
    ds = kho.ds_phong()
    if not ds:
        return "Chưa có phòng nào trong Nhạc trưởng. Tạo phòng ở trang Nhạc trưởng trước."
    return nt._mo_ta_phong(ds)


def _giao(args, ctx) -> str:
    kho = _kho(ctx)
    if kho is None:
        return "ERROR: chưa biết brain nào nên không giao việc được."
    tieu_de = str((args or {}).get("title") or "").strip()
    brief = str((args or {}).get("brief") or "").strip()
    if not tieu_de or not brief:
        return "ERROR: cần title và brief. Brief là lời giao việc, cùng nội dung người dùng vừa nói."
    ds = kho.ds_phong()
    chon, hoi = nt.chon_phong(ds, str((args or {}).get("phong") or ""))
    if hoi:
        return hoi
    thieu = [p.get("ten") for p in chon if not any(n.get("vai") == "truong" for n in (p.get("nguoi") or []))]
    if thieu:
        return "Phòng " + ", ".join(thieu) + " chưa có trưởng phòng. Nhờ người dùng đặt trưởng trên trang Nhạc trưởng rồi giao lại."
    try:
        viec = nt.tao_viec(kho, tieu_de, brief, [p["slug"] for p in chon], bat_cong=True)
    except nt.LoiNhacTruong as e:
        return f"ERROR: {e}"
    brain = ctx.vault_root
    try:
        trang = rte.bat_chay(brain, viec["id"])
    except nt.LoiNhacTruong as e:
        return f"ERROR: đã tạo việc {viec['id']} nhưng chưa chạy được. {e}"
    ten = ", ".join(p.get("ten") or p.get("slug") for p in chon)
    if trang == "dang_chay":
        return f"Việc \"{viec['tieu_de']}\" ({viec['id']}) đã đang chạy ở phòng {ten}. Xem trên trang Nhạc trưởng, tab Theo dõi."
    return (
        f"Đã giao \"{viec['tieu_de']}\" cho phòng {ten} và bấm chạy. "
        f"Mã việc {viec['id']}. Việc sẽ dừng để duyệt kế hoạch, và dừng lần nữa trước phòng thiết kế hoặc video. "
        f"Khi người dùng nói đồng ý hoặc một câu sửa, gọi op=duyet với id này. "
        f"Xem tiến trình trên trang Nhạc trưởng, tab Theo dõi. "
        f"File nằm trong brain: nhac-truong/viec/{viec['id']}.md. "
        "Đừng hứa sẽ chờ xong rồi tóm tắt trong lượt chat này."
    )


def _xem(args, ctx) -> str:
    kho = _kho(ctx)
    if kho is None:
        return "ERROR: chưa biết brain nào."
    vid = str((args or {}).get("id") or "").strip()
    if not vid:
        thu = kho.goc / "viec"
        files = sorted(thu.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True) if thu.is_dir() else []
        if not files:
            return "Chưa có việc nào."
        vid = files[0].stem
    try:
        v = kho.doc_viec(vid)
    except nt.LoiNhacTruong as e:
        return f"ERROR: {e}"
    ket = (v.get("ket_qua") or "").strip()
    dong = [
        f"{v.get('tieu_de')} ({v.get('id')})",
        f"Trạng thái: {v.get('trang_thai')}",
        "Phòng: " + ", ".join(v.get("phong") or []),
    ]
    if v.get("trang_thai") == "cho_duyet":
        dong.append("Đang chờ duyệt: " + str(v.get("cong") or ""))
        dong.append(nt.tin_cong(v))
        dong.append("Người dùng nói đồng ý thì gọi op=duyet, đừng tự viết tiếp.")
    if v.get("loi_chay"):
        dong.append("Lỗi: " + str(v.get("loi_chay"))[:300])
    if ket:
        dong.append("Kết quả:\n" + ket[:1200])
    else:
        dong.append("Chưa có kết quả. Xem lời trao đổi trên trang Nhạc trưởng.")
        return "\n".join(dong)


def _duyet(args, ctx) -> str:
    kho = _kho(ctx)
    if kho is None:
        return "ERROR: chưa biết brain nào."
    vid = str((args or {}).get("id") or "").strip()
    y = str((args or {}).get("y") or "").strip()[:300]
    try:
        if vid:
            viec = nt.duyet(kho, vid, y)
        else:
            viec = nt.duyet_loi(kho, ("đồng ý " + y).strip())
    except nt.LoiNhacTruong as e:
        return f"ERROR: {e}"
    try:
        rte.bat_chay(ctx.vault_root, viec["id"])
    except nt.LoiNhacTruong as e:
        return f"ERROR: đã ghi duyệt nhưng chưa chạy tiếp được. {e}"
    return (
        f"Đã duyệt \"{viec.get('tieu_de')}\" ({viec.get('id')}). "
        "Chạy tiếp từ chỗ dừng, không làm lại từ đầu. Xem tab Theo dõi."
    )


def register(ctx):
    ctx.register_tool(
        "javis_nhac_truong",
        "Nhạc trưởng: xem phòng ban, giao một việc và chạy như nút Chạy trên trang. "
        "Khi người dùng muốn phòng ban, nhạc trưởng, trưởng phòng hoặc nhiều người trong hệ thống làm một việc, "
        "gọi tool này, đừng tự viết hộ. "
        "op=phong: liệt kê phòng đang có. "
        "op=giao: cần title, brief, và phong là tên hoặc mã phòng. Nhiều phòng thì cách nhau bằng dấu phẩy. "
        "Nếu người dùng chưa nói phòng, hoặc tên không khớp đúng một phòng, tool trả danh sách: HỎI LẠI người dùng, "
        "đừng chọn hộ và đừng gọi op=giao lần nữa cho đến khi họ chỉ phòng. "
        "Chỉ một phòng trong brain thì được giao phòng đó và nói rõ. "
        "Việc chạy ở nền và dừng để người dùng duyệt. Nói mã việc và bảo xem tab Theo dõi. "
        "Không hứa sẽ chờ xong rồi báo lại. "
        "op=xem: đọc trạng thái. Nếu đang chờ duyệt, bảo người dùng nói đồng ý hoặc một câu sửa. "
        "op=duyet: khi người dùng đồng ý hoặc góp một câu. id nếu biết mã việc, y là câu sửa, để trống nếu chỉ đồng ý.",
        _chay,
        schema={
            "type": "object",
            "properties": {
                "op": {"type": "string", "enum": ["phong", "giao", "xem", "duyet"]},
                "y": {"type": "string", "description": "Câu sửa khi duyệt. Để trống nếu chỉ đồng ý."},
                "title": {"type": "string", "description": "Tên việc ngắn"},
                "brief": {"type": "string", "description": "Lời giao việc, đủ ý người dùng vừa nói"},
                "phong": {"type": "string", "description": "Tên hoặc mã phòng, nhiều phòng cách nhau bằng dấu phẩy"},
                "id": {"type": "string", "description": "Mã việc khi op=xem"},
            },
            "required": ["op"],
        },
        min_mode="readonly",
        emoji="🎼",
    )


async def _chay(args, ctx) -> str:
    op = str((args or {}).get("op") or "").strip().lower()
    if op == "phong":
        return _liet(ctx)
    if op == "giao":
        return _giao(args, ctx)
    if op == "xem":
        return _xem(args, ctx)
    if op == "duyet":
        return _duyet(args, ctx)
    return "ERROR: op phải là phong, giao, xem hoặc duyet."
