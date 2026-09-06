---
name: Báo cáo giáo dục sáng
description: "Đọc RSS/link nguồn đã ghim (~10 báo), chọn ~10 bài CĐ/ĐH mới, tóm tắt kèm URL gửi Telegram/Zalo."
description_en: "Read pinned education RSS/links, pick ~10 latest higher-ed items, summarize with URLs for Telegram/Zalo."
group: Nội dung
---

# Báo cáo giáo dục sáng (CĐ / ĐH)

## Khi nào dùng

- Nhắc hẹn **8h sáng** hàng ngày (nhãn `Báo cáo giáo dục CĐ-ĐH 8h`).
- User hỏi: "tin giáo dục hôm nay", "tóm tắt báo CĐ ĐH", "điểm tin cao đẳng đại học".

## Mục tiêu

Mỗi sáng gửi **đúng một tin nhắn** (Telegram + Zalo nếu `chat_id=all`) gồm khoảng **10 bài mới** về CĐ/ĐH, kèm link gốc. Không viết luận dài.

## Cách làm hiệu quả (bắt buộc)

**Không search lan man.** Chỉ đọc nguồn đã ghim trong file cùng skill:

`nguon-rss.md` (cùng thư mục skill này)

User tự thêm/bớt/đổi URL trong file đó. Agent **không** tự bịa thêm domain ngoài danh sách trừ khi user bảo trong lượt chat.

Thứ tự ưu tiên:

1. **RSS** (có `<item>` / `<entry>`) - lấy title + link + pubDate.
2. Không có RSS / feed chết → **WebFetch đúng URL chuyên mục HTML** ghi trong `nguon-rss.md`, bóc vài link bài mới nhất trên trang đó.
3. Tool: ưu tiên WebFetch (hoặc `tavily_extract` nếu chỉ có extract). **Không** dùng Tavily/WebSearch toàn web trừ khi user yêu cầu rõ "search thêm".

Thiếu cả WebFetch lẫn extract → nói thẳng không đọc được nguồn, không bịa tin.

## Chuẩn bị

1. Đọc hết danh sách trong `nguon-rss.md` (bỏ dòng `#`).
2. Giờ **VN (UTC+7)**. Ưu tiên bài **24–48 giờ**; thiếu thì nới 7 ngày và ghi rõ.
3. Chỉ **đọc / tóm tắt**. Không đăng bài ngoài.

## Lọc chủ đề CĐ/ĐH

Feed giáo dục thường lẫn cấp phổ thông. Chỉ giữ bài chạm:

- đại học / cao đẳng / tuyển sinh ĐH-CĐ / học phí ĐH / thông tư-nghị định về GDĐH
- tự chủ đại học, kiểm định, xếp hạng ĐH
- liên kết DN, thực tập, việc làm sinh viên, đào tạo nghề gắn DN

Loại tin thuần tiểu học / THCS / THPT trừ khi đụng thẳng chính sách ảnh hưởng CĐ-ĐH.

## Cách chạy

### 1. Quét nguồn đã ghim

Với mỗi dòng `Tên | URL` trong `nguon-rss.md`:

- WebFetch URL (timeout ngắn).
- Nếu XML/RSS: lấy các item mới (title, link, date).
- Nếu HTML: lấy 3–8 link bài mới nhất trên trang chuyên mục.
- Feed lỗi / chặn: ghi tên nguồn vào mục "Nguồn lỗi", chuyển nguồn tiếp theo. Không dừng cả báo cáo vì 1 feed chết.

Gom toàn bộ item → dedup URL/title.

### 2. Chọn ~10 bài

Ưu tiên mới + đa nguồn + đúng CĐ/ĐH. Tránh 10 bài cùng một báo.

### 3. Đọc lead (tuỳ chọn)

Chính sách / số liệu quan trọng: WebFetch hoặc extract **1 lần** bài đó. Còn lại đủ title + description RSS nếu rõ.

### 4. Viết tin nhắn

Tiếng Việt, ngắn, link đầy đủ http/https. Không bảng phức tạp. Không em dash.

```markdown
### Điểm tin CĐ/ĐH · <dd/mm>

1. **<Tiêu đề ngắn>** - <báo>, <giờ/ngày nếu có>
   <1–2 câu ý chính>
   <URL>

2. ...
(đủ ~10 mục hoặc N + lý do thiếu)

**Nhịp chính hôm nay:** <1 câu>
**Nguồn đã đọc:** <tên nguồn OK>
**Nguồn lỗi:** <nếu có>
```

## User cập nhật nguồn thế nào

Sửa file `nguon-rss.md` trong skill (hoặc bảo Javis: "thêm RSS X vào báo cáo giáo dục sáng"). Sau khi sửa, lần chạy 8h sau dùng list mới - không cần tạo skill khác.

## Bẫy

- Bịa số liệu / tên thông tư.
- Search Google rồi dán link search.
- Bỏ qua `nguon-rss.md` để tự search 10 báo.
- Đệm bài phổ thông cho đủ 10.

## Kiểm chứng trước khi gửi

- ~8–10 mục (hoặc N thật + lý do).
- Mỗi mục có URL bài (không phải URL trang chủ chuyên mục).
- Đã đọc từ list ghim, không bịa nguồn.
