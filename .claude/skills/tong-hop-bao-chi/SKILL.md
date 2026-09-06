---
name: tong-hop-bao-chi
description: "Lọc RSS báo chí (hôm trước→8h sáng), tóm tắt theo chủ đề, gửi tối đa 10 bài mới kèm link qua Telegram/Zalo."
description_en: "Filter press RSS (yesterday→8am), summarize by topic, send up to 10 newest stories with links via Telegram/Zalo."
group: Nội dung
---

# Tổng hợp báo chí (RSS)

## Khi nào dùng

- Brief sáng tự động (nhắc `Tổng hợp báo chí 8h`) theo chủ đề mặc định trong `Javis/bao-chi-cau-hinh.md`.
- User gọi tay: "tổng hợp báo chí chủ đề X", "RSS giáo dục hôm nay", `/tong-hop-bao-chi ...`.
- Cần **tối đa 10 bài mới nhất** trong cửa sổ thời gian, **kèm link gốc**, tóm tắt theo chủ đề.

## Chuẩn bị

1. Đọc `Javis/bao-chi-cau-hinh.md` trong brain đang dùng. Chưa có → tạo từ `references/cau-hinh-mau.md` (cùng thư mục skill), hỏi user duyệt nguồn RSS.
2. Xác định **chủ đề**:
   - Brief sáng / không nêu chủ đề → lấy **Chủ đề mặc định** + **Từ khóa** trong file cấu hình.
   - User nêu chủ đề → dùng chủ đề đó; suy từ khóa ngắn từ chủ đề (3-8 từ), có thể gộp với từ khóa cấu hình.
3. Cửa sổ thời gian (giờ VN, UTC+7): **00:00 hôm qua → 08:00 hôm nay**.
4. Kênh gửi: brief tự động để hệ thống nhắc đẩy kết quả về chat đã gắn (`chat_id`). Gọi tay trên Telegram/Zalo thì trả lời ngay trong phiên; chỉ gọi `zalo_send_*` / gửi TG khi user **yêu cầu rõ** gửi sang kênh khác.

## Cách chạy

1. Chạy script lọc RSS (ưu tiên; đừng tự bịa bài):

```bash
python skills/tong-hop-bao-chi/scripts/fetch_rss.py \
  --config Javis/bao-chi-cau-hinh.md \
  --topic "<chủ đề>" \
  --keywords "<từ khóa, cách nhau dấu phẩy>" \
  --limit 10
```

Nếu skill nằm ở `.claude/skills/...` (mirror hệ thống), dùng đúng path script đó. Engine API không có Bash: dùng WebFetch từng URL RSS trong cấu hình, tự lọc theo cùng cửa sổ thời gian + từ khóa, rồi chọn 10 bài mới nhất (theo `pubDate`).

2. Đọc JSON: `articles[]` (title, link, summary, published), `errors`, `window_*`.
3. Viết báo cáo theo khuôn dưới. **Mỗi bài trong mục 10 bài mới nhất phải có link markdown** `[tiêu đề](url)`.
4. Không bịa bài / link. Feed lỗi → ghi trong mục Nguồn lỗi, vẫn trả phần còn lại.

## Quy trình tóm tắt

1. Gom `articles` theo nhóm ý trong chủ đề (vd tuyển sinh, học phí, chính sách, trường...).
2. Viết 4-8 bullet insight (có căn cứ từ tiêu đề/summary; không bịa số liệu ngoài feed).
3. Liệt kê **đúng tối đa 10** bài mới nhất (đã sort sẵn bởi script).
4. Kết: 1-3 gợi ý theo dõi thêm (tùy chọn).

## Định dạng đầu ra

Tin nhắn ngắn (Telegram/Zalo), tiếng Việt, không bảng, không em dash.

```markdown
### Báo chí · <chủ đề> · <dd/mm>

**Cửa sổ:** 00:00 <hôm qua> → 08:00 <hôm nay> (VN)

**Tóm tắt theo chủ đề**
- ...

**10 bài mới nhất**
1. [Tiêu đề](https://...) · nguồn · giờ
2. ...

**Nguồn lỗi** (bỏ nếu không có)
- ...
```

## Bẫy

- Không gửi tin hàng loạt sang người khác nếu user không nhờ. Brief nhắc hẹn: chỉ trả kết quả; kênh nhận do nhắc cấu hình.
- Không vượt 10 bài ở mục danh sách (trừ khi user đòi nhiều hơn).
- Bài không có `pubDate`: script có thể xếp cuối; ghi chú nếu dùng.
- Cấu hình RSS trống / mọi feed lỗi → nói rõ cần sửa `Javis/bao-chi-cau-hinh.md`, đưa mẫu từ `references/cau-hinh-mau.md`.

## Kiểm chứng

- Có đúng cửa sổ thời gian VN không?
- Có đủ link bấm được cho từng bài trong top 10 không?
- Chủ đề user yêu cầu có khớp phần tóm tắt không?
