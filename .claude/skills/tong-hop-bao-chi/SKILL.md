---
name: tong-hop-bao-chi
description: "Tổng hợp/tóm tắt báo chí theo danh mục RSS (giáo dục, tài chính…), tối đa 10 bài + link; brief sáng hoặc gọi tay."
description_en: "Summarize press by RSS category (education, finance…), up to 10 stories with links; morning brief or on demand."
group: Nội dung
---

# Tổng hợp báo chí

Skill = **kỹ năng**: chọn danh mục RSS → lọc cửa sổ sáng → tóm tắt → format gửi (Telegram/Zalo/chat).
Nguồn RSS **tách theo danh mục** trong `Javis/bao-chi-cau-hinh.md` (giáo dục, tài chính, bất động sản… thêm sau được).

## Khi nào dùng

- Workflow/nhắc 8h `brief-bao-chi-sang` → danh mục **`giao-duc`**.
- User gọi tay: «tổng hợp báo chí tài chính», «RSS bất động sản», `/tong-hop-bao-chi tai-chinh`.
- Cần tối đa **10 bài mới** kèm **link gốc**, tóm tắt theo chủ đề danh mục.

## Chuẩn bị

1. Đọc `Javis/bao-chi-cau-hinh.md`. Thiếu → tạo từ `references/cau-hinh-mau.md`.
2. Chọn **danh mục** (`slug`):
   - Brief sáng / workflow giáo dục → `giao-duc` (cố định).
   - User nêu lĩnh vực → map sang slug gần nhất (`tài chính` → `tai-chinh`, `BĐS` → `bat-dong-san`). Không khớp → hỏi hoặc dùng `## Danh mục mặc định`.
3. Cửa sổ giờ VN: **00:00 hôm qua → 08:00 hôm nay**.
4. Kênh gửi: nhắc hẹn đẩy kết quả qua `chat_id`. Gọi tay → trả lời ngay trong phiên; chỉ gửi sang kênh khác khi user **yêu cầu rõ**.

## Cách chạy

```bash
python skills/tong-hop-bao-chi/scripts/fetch_rss.py \
  --config Javis/bao-chi-cau-hinh.md \
  --category giao-duc \
  --limit 10
```

- Đổi `--category` theo danh mục (`tai-chinh`, `bat-dong-san`, …).
- Xem danh mục có sẵn: thêm `--list-categories`.
- Skill ở `.claude/skills/...`: dùng đúng path script đó.
- Không có Bash: WebFetch đúng URL **RSS của danh mục đã chọn**, lọc cùng cửa sổ + từ khóa danh mục, lấy 10 bài mới nhất.

## Quy trình

1. Chạy script (hoặc WebFetch) → JSON `articles[]`, `category`, `errors`.
2. Tóm tắt 4-8 bullet theo nhóm ý trong danh mục (không bịa số ngoài feed).
3. Liệt kê tối đa 10 bài, mỗi bài `[tiêu đề](url)`.
4. Feed lỗi → mục Nguồn lỗi; vẫn trả phần còn lại.

## Định dạng đầu ra

Tin nhắn ngắn, tiếng Việt, không bảng, không em dash.

```markdown
### Báo chí · <nhãn danh mục> · <dd/mm>

**Danh mục:** <slug>
**Cửa sổ:** 00:00 <hôm qua> → 08:00 <hôm nay> (VN)

**Tóm tắt**
- ...

**10 bài mới nhất**
1. [Tiêu đề](https://...) · nguồn · giờ
2. ...

**Nguồn lỗi** (bỏ nếu không có)
- ...
```

## Thêm danh mục mới

Trong `Javis/bao-chi-cau-hinh.md`, thêm khối:

```markdown
## Danh mục: <slug-moi>

### Nhãn
...

### RSS
- https://...

### Từ khóa
từ1, từ2, ...
```

Không cần sửa skill. Workflow 8h vẫn chỉ gọi `giao-duc` trừ khi đổi nhắc/workflow.

## Bẫy

- Brief 8h **không** trộn mọi RSS: chỉ feed của danh mục workflow chỉ định (`giao-duc`).
- Không bịa bài/link; không vượt 10 bài (trừ khi user đòi).
- Không gửi hàng loạt nếu user không nhờ (nhắc hẹn: chỉ trả kết quả).

## Kiểm chứng

- Đúng `--category` / đúng khối RSS chưa?
- Đủ link top 10? Cửa sổ giờ VN đúng chưa?
