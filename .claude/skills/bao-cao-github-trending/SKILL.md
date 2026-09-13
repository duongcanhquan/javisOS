---
name: bao-cao-github-trending
description: "Báo cáo GitHub Trending hôm nay: tóm tắt repo, tư vấn có nên đưa vào Javis (skill/connector/không)."
description_en: "Daily GitHub Trending brief: what each repo does, whether it fits Javis (skill/connector/skip)."
group: Năng suất
---

# Báo cáo GitHub Trending

Skill = **kỹ năng**: lấy [GitHub Trending](https://github.com/trending) hôm nay → tóm tắt ngắn → tư vấn Javis. Không cài gì.

## Khi nào dùng

- Nhắc hẹn 20:00 hàng ngày (label `GitHub Trending 20h`).
- User hỏi «trending GitHub hôm nay», «repo nào đáng xem», «cài gì vào Javis từ trending».

Kết quả nhắc hệ thống (`chat_id=all`) gửi **Telegram và Zalo** nếu đã đấu.

## Chuẩn bị

1. Giờ Việt Nam (UTC+7). Phạm vi mặc định: **Today / Any language**.
2. Chỉ **đọc web + ghi file báo cáo**. Không clone repo, không `pip install`, không bật skill mới.
3. Đọc `references/javis-fit.md` trước khi ghi cột tư vấn.

## Cách chạy

```bash
python skills/bao-cao-github-trending/scripts/fetch_trending.py --since daily --limit 15
```

JSON có `items[]` (`full_name`, `url`, `description`, `language`, `stars`, `stars_today`) và `danh_sach_tho` (dán làm xương).

## Quy trình (bắt buộc)

1. Chạy script → lấy JSON. Lỗi fetch → nói thẳng, không bịa repo.
2. Mỗi repo: 1 câu **làm gì** + 1 câu **dùng để làm gì** (từ description; không bịa tính năng).
3. Cột **Với Javis** chỉ một trong: `Không` / `Chỉ xem` / `Có thể bổ sung`.
4. Nếu bổ sung: `skill` / `connector-MCP` / `plugin` / `không`. Cherry-pick, không nuốt cả repo.
5. Chat (Telegram/Zalo): **8–15 dòng**, không bảng Markdown (kênh không đọc bảng).
6. Bản đủ (bảng) lưu `exports/github-trending/YYYY-MM-DD.md`.

## Định dạng tin nhắn

```markdown
### GitHub Trending · <dd/mm>

1. [owner/repo](url) — làm gì. Javis: Không | Chỉ xem | Có thể bổ sung (skill/…)
2. …

**Đáng để mắt**
- …

**Không đưa vào Javis**
- pentest / leak prompt / tải khóa học / app không liên quan (nêu tên nếu có)

Không tự cài gì tối nay.
Bản đủ: exports/github-trending/YYYY-MM-DD.md
```

## Định dạng file vault

Bảng: `# | Repo | Sao hôm nay | Làm gì | Với Javis | Nếu bổ sung thì dạng gì`.

## CẤM

- CẤM khuyên cài pentest, exploit, EDR evasion, leak system prompt, downloader khóa học trả phí.
- CẤM tự cài skill/plugin từ trending.
- CẤM bịa số sao / mô tả khác description.
- CẤM bảng Markdown trong tin Zalo/Telegram (lưu bảng ở file vault).

## Liên kết

- Nhắc cron `0 20 * * *` — seed `scripts/seed-github-trending-vps.sh`.
- `y-tuong-noi-dung-tu-trend` — khi user muốn biến trend thành lịch content, không phải cài repo.
