---
name: Deep Research
description: "Nghiên cứu sâu lặp theo breadth/depth: sinh query, tra web, rút learning, đào tiếp, báo cáo có nguồn."
description_en: "Iterative deep research by breadth/depth: SERP queries, web dig, learnings, recurse, sourced report."
group: Năng suất
---

# Deep Research (Open Deep Research → Javis)

Phương pháp từ [dzhng/deep-research](https://github.com/dzhng/deep-research): nghiên cứu lặp, mỗi vòng sinh query → tra web → rút learning → đào sâu thêm.

Trên Javis chạy bằng **tool sẵn có** (Tavily MCP / WebSearch / WebFetch / query-wiki). Không bắt buộc cài Node Firecrawl; muốn CLI gốc xem `references/upstream.md`.

## Khi nào dùng

- Nghiên cứu chủ đề video, thị trường, đối thủ, xu hướng, fact-check trước khi viết kịch bản / proposal.
- User nói deep research, nghiên cứu sâu, đào sâu chủ đề, research report có nguồn.
- Agent `nghien-cuu-chu-de-video`, Researcher mẫu, hoặc bước nghiên cứu trong Bộ Video / Bộ Proposal.

## Chuẩn bị

1. Đọc brief / `{{input}}` + Memory/wiki liên quan.
2. Kiểm tra kết nối: ưu tiên **Tavily** (`tavily_search`, `tavily_extract`); không có thì WebSearch/WebFetch nếu engine hỗ trợ; không có cả hai thì dùng wiki + nêu rõ thiếu tra web.
3. Chọn tham số (mặc định nếu user không nói):
   - **breadth** = 4 (2-8)
   - **depth** = 2 (1-4)
   - Chế độ **report** (báo cáo dài) trừ khi user chỉ cần câu trả lời ngắn (**answer**).

## Quy trình (bắt buộc theo vòng)

### 0. Follow-up (chỉ khi brief mơ hồ)

Tự đặt tối đa 3 câu làm rõ hướng. Nếu đoán được thì nêu giả định rồi làm - đừng hỏi lan man. Gộp brief + giả định thành `combined_query`.

### 1. Mỗi vòng depth

1. Sinh tối đa `breadth` **SERP query** từ `combined_query` (+ learnings vòng trước nếu có). Mỗi query có:
   - `query` - chuỗi tìm kiếm cụ thể, không trùng nhau
   - `researchGoal` - mục tiêu + hướng đào tiếp sau khi có kết quả
2. Với mỗi query: gọi Tavily search (hoặc WebSearch). Lấy 3-5 URL tốt → `tavily_extract` / WebFetch khi cần thân bài.
3. Rút **learnings** (tối đa ~3-5/query): ngắn, dày thông tin, giữ entity (người/công ty/sản phẩm), số liệu, ngày tháng. Kèm URL nguồn.
4. Rút **followUpQuestions** / hướng mới để vòng sau.
5. Gộp `learnings[]`, `visitedUrls[]` (không trùng).

### 2. Đệ quy

Nếu còn depth: đặt query vòng sau = mục tiêu gốc + learnings mới + câu hỏi follow-up; **breadth vòng sau ≈ ceil(breadth/2)**; depth -= 1. Lặp bước 1.

### 3. Đầu ra

**Report** (mặc định): markdown chi tiết, gồm toàn bộ learnings đã tổ chức theo mục, kết thúc:

```
## Sources
- https://...
```

**Answer**: chỉ câu trả lời ngắn đúng format user yêu cầu + 3-5 URL then chốt.

Cho **video**: thêm mục `Góc kể / hook` (3 ý) và `Motif hình ảnh` để biên kịch dùng ngay.

Cho **thị trường**: ánh xạ learning vào khung skill `nghien-cuu-thi-truong` (phân khúc, đối thủ, xu hướng, insight).

## Giọng nghiên cứu (từ upstream)

- Coi user là analyst giàu kinh nghiệm: chi tiết, có tổ chức, đúng.
- Ưu tiên lập luận tốt hơn "vì nguồn nổi tiếng".
- Speculation được phép nhưng phải **gắn nhãn** (ước tính / dự đoán).
- Không bịa số; thiếu thì ghi "Cần bổ sung".

## Bẫy

- Một lần search rồi dừng khi depth≥2 - sai quy trình.
- Learning sáo rỗng không entity/metric.
- Quên mục Sources.
- Bỏ qua Tavily dù đã đấu MCP.

## Kiểm chứng

- Có ≥ breadth learnings hữu ích hoặc giải thích vì sao ít hơn.
- Mọi claim số có nguồn hoặc nhãn ước tính.
- `visitedUrls` không rỗng nếu đã tra web được.
