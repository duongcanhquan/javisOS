# Chat attach local folder — design

**Date:** 2026-09-25  
**Status:** approved (user: «Ok làm đi»)

## Goal

Nút chọn **folder trên máy cá nhân** cạnh icon đính kèm trong ô chat. Sau khi chọn, Javis coi folder đó là ngữ cảnh phiên: **đọc toàn bộ** hoặc **làm theo lệnh** (tóm tắt, tìm, ingest…).

## Non-goals

- Không thay Kho Drive (Google).
- Không đọc thẳng ổ đĩa máy khi Javis chạy VPS (browser phải upload).
- Không mass-ingest tự động lúc chọn — chỉ khi user bảo chưng cất / lưu source.

## UX

1. Nút folder (icon `folder-open`) cạnh `#attachBtn`.
2. Click → `showDirectoryPicker` (Chrome/Edge) hoặc fallback `<input webkitdirectory>`.
3. Một chip thư mục trên `#attachBar`: tên folder + số file (+ đang tải).
4. Gửi tin: kèm khối ngữ cảnh đường dẫn stage + cây file tương đối.
5. Giới hạn: ≤50 file, ≤100 MB tổng, ≤15 MB/file (ảnh ≤8 MB). File vượt → bỏ qua + ghi chú trên chip.

## Data flow

```
Browser pick folder → POST /upload/folder (multipart + relpath)
  → STATE_DIR/.staging/folders/<id>/… (giữ cây thư mục)
  → chip + pendingAttachments (kind: folder)
  → sendMessage: [Thư mục đính kèm…] + lời user
  → engine đọc qua javis_read_file / staging (đã cho phép trên chat chủ)
```

## Context prompt (rút gọn)

- Đường gốc stage + danh sách `relpath`.
- Mặc định: đọc / thao tác theo lệnh; không tự lưu Sources.
- User nói đọc hết / tóm tắt / chưng cất / ingest → làm theo (ingest chỉ khi nói rõ).

## Compat

- Chrome / Edge / Chromium: Directory Picker.
- Safari / Firefox / mobile: `webkitdirectory`.
- Không hỗ trợ: báo một dòng trên attach bar.
