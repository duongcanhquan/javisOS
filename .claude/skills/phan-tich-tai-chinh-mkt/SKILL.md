---
name: Phân tích tài chính marketing
description: "Từ SOM/giá/chi phí ước unit economics, hòa vốn, ngân sách MKT, CAC/LTV; neo kế hoạch KD-MKT."
description_en: "From SOM/price/costs estimate unit economics, break-even, MKT budget, CAC/LTV; anchor KD-MKT plans."
group: Tài chính
---

# Phân tích tài chính cho kinh doanh & marketing

## Khi nào dùng

- Sau nghiên cứu thị trường (có SOM, giá tham chiếu, hoặc brief có chi phí cố định).
- Trước khi viết kế hoạch KD / MKT cần **trần số** (ngân sách marketing, CAC, hòa vốn).

## Chuẩn bị

1. Đọc `01-research-findings.md` (SOM base / optimistic / pessimistic, giá).
2. Thu thập chi phí cố định / biến đổi từ brief, Memory, hoặc file đầu tư user chỉ định. **Thiếu thì nêu giả định rõ, không bịa chắc chắn.**
3. Đơn vị: VND; làm tròn hợp lý; luôn ghi công thức ngắn.

## Quy trình

Lưu: `sources/research/<slug>/09-finance-model.md`

```
# [Tên] - Mô hình tài chính & ngân sách marketing

## 1. Giả định đầu vào (bảng)
## 2. Unit economics (đóng góp gộp / đơn vị)
## 3. Điểm hòa vốn (đơn vị / tháng)
## 4. Dự phóng doanh thu 12-36 tháng (3 kịch bản neo SOM)
## 5. Trần ngân sách marketing (% DT hoặc VND)
## 6. CAC trần & LTV giả định
## 7. Độ nhạy (±20% giá / chuyển đổi / churn)
## 8. Kết luận cho kế hoạch KD & MKT (3-5 bullet quyết định)
```

### Công thức tối thiểu

- Đóng góp gộp ≈ Giá - biến phí / đơn vị
- Hòa vốn đơn vị ≈ Chi phí cố định kỳ / đóng góp gộp
- CAC trần ≈ (LTV × biên mục tiêu) hoặc % ngân sách / số khách mục tiêu
- Ngân sách MKT năm 1 ≈ % doanh thu mục tiêu (ghi % và số)

## Bẫy

- Dùng SOM optimistic làm base case im lặng.
- Quên chi phí tuân thủ / mặt bằng / nhân sự trong cố định.
- Đưa số không có giả định.

## Kiểm chứng

- Mọi số có nguồn hoặc dòng **Giả định:**.
- Có bảng độ nhạy ngắn.
- 3-5 quyết định đủ để agent kế hoạch KD/MKT neo vào.

## Liên kết

- Trước: skill **`nghien-cuu-thi-truong`** / file `01-research-findings.md`.
- Sau bước này: **`ke-hoach-kinh-doanh`**, **`ke-hoach-marketing`**.
- Workflow: **`ke-hoach-kd-mkt-tu-nghien-cuu`**.
