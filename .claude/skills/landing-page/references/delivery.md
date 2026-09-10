# Delivery - hiển thị và đóng gói

## Mặc định (làm đủ khi môi trường cho phép)

### 1. Vault (bản chính)

```
exports/landing/<slug>/
  BRIEF.md
  COPY.md
  index.html
  landing-<slug>.zip    # nếu pack được
  <slug>.pke            # nếu Webcake được
```

Trong câu trả lời cuối, nhúng:

```markdown
[Mở landing](exports/landing/<slug>/index.html)
[Tải zip](exports/landing/<slug>/landing-<slug>.zip)
```

Dashboard phục vụ qua `/files/raw`. Trình sửa file mở HTML trong iframe.

### 2. Chat preview

- Có thể mở artifact HTML (fence `html` đủ dài) **hoặc** bảo user bấm link vault.
- Nhắc: artifact sandbox có thể chặn một số CDN/script; bản vault mới là nguồn sự thật.

### 3. Zip

Từ root skill (hoặc đường dẫn tuyệt đối tới script):

```bash
python3 scripts/pack_landing.py "/path/to/vault/exports/landing/<slug>"
```

Script tạo `landing-<slug>.zip` cạnh folder (gồm html/md/ảnh, bỏ zip cũ và `.pke` khỏi
lần zip sau nếu muốn nhẹ - mặc định gồm mọi file thường).

Không có Python/shell (API engine hạn chế) → vẫn giao `index.html`, hướng dẫn user
nén tay folder trên máy.

### 4. Webcake

Nếu có `node` và user muốn sửa kéo-thả:

1. Nạp skill `html-to-webcake`
2. Chạy pipeline HTML → spec → `.pke` → lint 0 ERROR
3. Đặt `.pke` cạnh `index.html`, link tải, nhắc upload Webcake

### 5. Không làm

- Không claim «đã lên domain» nếu chưa deploy hosting.
- Không `file://` trong markdown chat.
- Không xoá bản HTML sau khi có `.pke` - giữ cả hai.
