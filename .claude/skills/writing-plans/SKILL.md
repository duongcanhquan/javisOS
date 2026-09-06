---
name: Writing Plans
description: "Viết kế hoạch triển khai chi tiết từ spec đã duyệt: task nhỏ, file chạm, test, commit; trước khi code."
description_en: "Write a bite-sized implementation plan from an approved spec before coding."
group: AI
---

# Writing Plans (kế hoạch triển khai từ spec)

## Khi nào dùng

- Đã có **spec / design** được user duyệt (thường sau skill **`brainstorming`** luồng Architectural).
- Cần kế hoạch triển khai nhiều bước **trước khi** đụng code.

## HARD-GATE liên kết

- Nếu chưa có spec duyệt: **dừng** và nạp / chạy **`brainstorming`** trước. Không viết plan từ ý tưởng thô.
- Plan xong **chưa** tự implement trừ khi user bảo chạy plan. Không nhảy sang `frontend-design` giữa lúc viết plan.

## Chuẩn bị

1. Đọc file spec (vd `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`) hoặc đường dẫn user chỉ.
2. Đọc commit/docs liên quan đủ để map file thật trong repo.
3. Nói rõ: "Đang dùng skill writing-plans để lập kế hoạch triển khai."

## Quy trình

1. **Scope:** Spec ôm nhiều subsystem độc lập → đề xuất tách nhiều plan (mỗi plan ship được, test được).
2. **File map:** Liệt kê file tạo/sửa và trách nhiệm từng file (unit rõ biên).
3. **Task nhỏ:** Mỗi task 1 deliverable test được; bước con kiểu 2-5 phút (test đỏ → code → test xanh → commit khi phù hợp).
4. **Ghi plan** vào `docs/superpowers/plans/YYYY-MM-DD-<feature>.md` (user chỉ chỗ khác thì theo user).

### Header bắt buộc

```markdown
# [Tên tính năng] Implementation Plan

> **For agentic workers:** triển khai từng task; dùng checkbox `- [ ]` để theo dõi.

**Goal:** ...
**Architecture:** ...
**Tech Stack:** ...

## Global Constraints
- ...
```

5. Mỗi task: mục tiêu, file chạm, bước làm, cách test, tiêu chí xong.
6. Nhắc ràng buộc từ spec: consent / xóa data 72h / không em dash nếu spec có.

## Bẫy

- Viết plan khi spec còn TBD hoặc chưa được user duyệt.
- Task khổng lồ "làm hết module X" không tách bước test.
- Nhét triển khai UI/production vào lúc đang viết plan.

## Kiểm chứng

- Plan đọc được độc lập (agent mới làm theo không cần hỏi lại ý định).
- Mọi yêu cầu cứng của spec (bảo mật, API xóa, KPI kỹ thuật) xuất hiện trong Global Constraints hoặc task tương ứng.
- Có đường dẫn file plan + spec nguồn ở đầu hoặc cuối tài liệu.
