---
type: workflow
name: Brief báo chí sáng - Giáo dục
slug: brief-bao-chi-sang
status: active
group: Nội dung
description: 8h sáng RSS giao-duc; dán tin_moi_markdown (Báo+giờ+Link); tối đa 10.
model: gemini-3.6-flash-medium
model_provider: antigravity-cli
steps:
  - agent: tong-hop-bao-chi
    task: "Nạp skill tong-hop-bao-chi. Danh mục CỐ ĐỊNH giao-duc. Chạy fetch_rss.py --category giao-duc --limit 10. Viết Tóm tắt. Tin mới = DÁN NGUYÊN tin_moi_markdown (đã có Báo/Xuất bản/Link). CẤM viết lại tin, CẤM bỏ Link."
updated: 2026-09-06
---
Brief sáng giáo dục. Dán nguyên tin_moi_markdown để mỗi tin có link đọc.
