---
name: Báo cáo giáo dục sáng
description: "Tóm tắt ~10 bài báo mới về CĐ/ĐH Việt Nam (chính sách, tuyển sinh, liên kết DN) kèm link, gửi Telegram/Zalo."
description_en: "Morning digest of ~10 latest VN higher-ed news (policy, admissions, industry links) with URLs for Telegram/Zalo."
group: Nội dung
---

# Báo cáo giáo dục sáng (CĐ / ĐH)

## Khi nào dùng

- Nhắc hẹn **8h sáng** hàng ngày (nhãn `Báo cáo giáo dục CĐ-ĐH 8h`).
- User hỏi: "tin giáo dục hôm nay", "tóm tắt báo CĐ ĐH", "điểm tin cao đẳng đại học".

## Mục tiêu

Mỗi sáng gửi **đúng một tin nhắn** (Telegram + Zalo nếu `chat_id=all`) gồm khoảng **10 bài mới nhất** về:

- Chính sách / thông tư / quyết định Bộ GD&ĐT, UBND liên quan CĐ-ĐH
- Tuyển sinh, học phí, chương trình đào tạo
- Liên kết doanh nghiệp, thực tập, việc làm sinh viên
- Chất lượng, kiểm định, xếp hạng (khi có tin mới)

Kèm **link đọc gốc** từng bài. Không viết luận dài.

## Chuẩn bị

1. Ưu tiên **Tavily** (`tavily_search` / `tavily_extract`). Không có thì WebSearch/WebFetch. Thiếu cả hai → nói thẳng không tra được web, không bịa tin.
2. Giờ theo **VN (UTC+7)**. Ưu tiên bài **24–48 giờ gần nhất**; thiếu thì nới 7 ngày và ghi rõ.
3. Chỉ **đọc / tóm tắt**. Không đăng bài, không gửi email ngoài báo cáo nhắc.

## Nguồn ưu tiên (~10 báo / cổng)

Lọc hoặc ưu tiên kết quả từ (và trang chuyên mục giáo dục của họ):

1. Báo Giáo dục & Thời đại / giaoducthoidai.vn  
2. Vietnamnet Giáo dục  
3. Dân trí Giáo dục  
4. Tuổi Trẻ Giáo dục  
5. Thanh Niên Giáo dục  
6. VnExpress Giáo dục  
7. Tiền Phong Giáo dục  
8. Báo Chính phủ (mục giáo dục / đào tạo)  
9. Cổng thông tin Bộ GD&ĐT (moet.gov.vn) - văn bản mới  
10. Người Lao Động / Lao Động (mục giáo dục nghề nghiệp / CĐ-ĐH)

Có thể thêm 1–2 nguồn uy tín khác nếu bài sát CĐ-ĐH hơn. Tránh tin viral không nguồn, blog SEO, tin trùng lead.

## Cách chạy (bắt buộc)

### 1. Thu thập

Chạy **2–4** truy vấn Tavily/WebSearch kiểu:

- `cao đẳng đại học chính sách OR thông tư site:moet.gov.vn OR giáo dục`
- `tuyển sinh đại học OR cao đẳng 2026`
- `liên kết doanh nghiệp đào tạo nghề OR thực tập sinh viên`
- `học phí đại học OR tự chủ đại học`

Với mỗi query lấy 5–8 kết quả. Dedup theo URL/title. Chọn **~10 bài** mới nhất, đa nguồn (tránh 10 bài cùng một báo).

### 2. Đọc nhanh

Với bài quan trọng (chính sách / số liệu): `tavily_extract` hoặc WebFetch 1 lần để không tóm sai lead. Bài còn lại đủ từ title + snippet nếu rõ.

### 3. Viết tin nhắn

Tiếng Việt, ngắn, **có link đầy đủ** (http/https). Không bảng markdown phức tạp (Telegram/Zalo đọc kém). Không em dash.

Khuôn:

```markdown
### Điểm tin CĐ/ĐH · <dd/mm>

1. **<Tiêu đề ngắn>** - <báo>, <giờ/ngày nếu có>
   <1–2 câu ý chính / tác động>
   <URL>

2. ...
(đủ ~10 mục)

**Nhịp chính hôm nay:** <1 câu: chính sách / tuyển sinh / DN / khác>
**Nguồn đã quét:** <liệt kê 6–10 tên báo đã thấy kết quả>
```

Nếu dưới 10 bài thật: gửi số có thật + ghi "chỉ thấy N bài đủ mới trong 48h". Không đệm bài cũ để cho đủ 10 nếu user không yêu cầu.

## Bẫy

- Bịa số liệu tuyển sinh / học phí / tên thông tư.
- Link search Google thay vì link bài.
- Trộn tin phổ thông / cấp 1-2 nếu không đụng CĐ-ĐH.
- Báo cáo dài > ~3500 ký tự: cắt bớt mô tả, giữ đủ 10 link.

## Kiểm chứng trước khi gửi

- Có khoảng 8–10 mục (hoặc N + lý do thiếu).
- Mỗi mục có URL mở được (http…).
- Ít nhất 1 mục về chính sách/văn bản nếu ngày đó có; nếu không có thì ghi rõ ở "Nhịp chính".
- Không có mật khẩu / token / PII.
