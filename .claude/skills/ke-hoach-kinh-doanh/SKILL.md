---
name: Kế hoạch kinh doanh từ nghiên cứu
description: "Viết kế hoạch KD 12-36 tháng từ nghiên cứu (SOM, JTBD, STEEPLE): mô hình, unit economics, roadmap, rủi ro."
description_en: "Write a 12-36 month business plan from deep research (SOM, JTBD, STEEPLE): model, unit economics, roadmap, risks."
group: Marketing
---

# Kế hoạch kinh doanh từ nghiên cứu thị trường

## Khi nào dùng

- Đã có gói nghiên cứu (`01-research-findings.md`, ideally `03-competitors-personas.md`, `05-proposal.md`) hoặc output skill **`nghien-cuu-thi-truong`**.
- User muốn **kế hoạch kinh doanh** (business plan) chi tiết hơn proposal tóm tắt: mô hình vận hành, đơn vị kinh tế, lộ trình, nguồn lực.
- Sau bước **`phan-tich-tai-chinh-mkt`** (nếu có file `09-finance-model.md` thì neo số vào đó).

## Chuẩn bị

1. Đọc `sources/research/<slug>/01-research-findings.md` (bắt buộc). Nếu thiếu → nạp **`nghien-cuu-thi-truong`** hoặc dừng và hỏi slug/path.
2. Đọc thêm nếu có: `03-competitors-personas.md`, `05-proposal.md`, `09-finance-model.md`.
3. Đọc `memory/MEMORY.md` (ràng buộc vốn, địa điểm, đội ngũ).
4. Không viết lại toàn bộ research - **chưng cất** thành quyết định kinh doanh.

## Quy trình (cấu trúc file đầu ra)

Lưu: `sources/research/<slug>/06-business-plan.md`

```
# [Tên] - Kế hoạch kinh doanh

## 0. Tóm tắt điều hành (≤250 từ)
## 1. Cơ hội & định vị (JTBD + white space từ nghiên cứu)
## 2. Thị trường mục tiêu (SAM/SOM base case + giả định)
## 3. Sản phẩm / dịch vụ & gói giá
## 4. Mô hình doanh thu & unit economics
## 5. Vận hành & năng lực (đội, địa điểm, công suất)
## 6. Lộ trình 90 ngày + 12 tháng (+ 24-36 tháng nếu đủ dữ liệu)
## 7. Tổ chức & quản trị
## 8. Rủi ro & kiểm soát (STEEPLE / pháp lý bắt buộc)
## 9. Nguồn lực & đầu tư (khung)
## Phụ lục: giả định số liệu + nguồn
```

### Chi tiết từng mục

1. **Tóm tắt** - vấn đề, giải pháp, cơ hội SOM base, 3 KPI năm 1.
2. **Định vị** - cho ai, Job nào, khác đối thủ thế nào (3 pillar).
3. **Thị trường** - chỉ số từ nghiên cứu; ghi khoảng tin cậy; không vượt trần SOM base khi đặt chỉ tiêu.
4. **Giá** - bảng gói + lý do neo khảo sát/đối thủ.
5. **Unit economics** - đóng góp gộp, CAC trần, LTV giả định, điểm hòa vốn (neo file tài chính nếu có).
6. **Vận hành** - công suất, bottleneck, giả định tuyển/đào tạo.
7. **Lộ trình** - milestone có ngày/kỳ; owner gợi ý.
8. **Rủi ro** - top 5 + biện pháp; **bắt buộc** rủi ro pháp lý/dữ liệu nếu nghiên cứu có STEEPLE.
9. **Đầu tư** - khung vốn theo giai đoạn (không bịa số tuyệt đối nếu user chưa cho).

## Bẫy

- Copy proposal nguyên khối rồi đổi tên file.
- KPI doanh thu > SOM base case mà không ghi rõ đây là kịch bản tích cực.
- Unit economics thiếu giả định rõ (giá, tỷ lệ chuyển đổi, churn).

## Kiểm chứng

- Người đọc hiểu mô hình kiếm tiền trong 5 phút.
- Mọi số lớn trích từ `01` / `09` hoặc ghi **Giả định:**.
- Có ≥5 quyết định cụ thể (không chỉ mô tả).

## Liên kết

- Trước: **`nghien-cuu-thi-truong`**, **`phan-tich-tai-chinh-mkt`**.
- Song song: **`ke-hoach-marketing`**, **`quy-trinh-van-hanh-kd-mkt`**.
- Tóm tắt pitch: **`proposal-chien-luoc`**.
- Workflow: **`ke-hoach-kd-mkt-tu-nghien-cuu`**.
