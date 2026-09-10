# Visual + motion (Remotion-style) cho bài giảng

## Mục tiêu

Slide **không** là trang Word. Mỗi cảnh có **1 điểm nhấn thị giác** và lời giảng
bám điểm đó.

## Emphasis (ghi vào mục Visual của cảnh)

Chọn 1–2 kỹ thuật / cảnh:

| Kỹ thuật | Khi nào | Ghi trong kịch bản |
|----------|---------|-------------------|
| Big number / stat callout | 1 con số then chốt | «Zoom số X rồi giải thích ý nghĩa» |
| Step reveal | Quy trình 3–5 bước | «Hiện bước 1→2→3 theo lời» |
| Compare split | Hai khái niệm | «Highlight cột trái rồi phải» |
| Callout box | Định nghĩa / công thức | «Pulse khung định nghĩa» |
| Diagram focus | Sơ đồ | «Pan/chỉ từng nút A→B→C» |
| Before/after | Đổi trạng thái | «Lật trước/sau» |

Nếu sau này làm **video Remotion** (`remotion-best-practices` / `lam-video`): biến mỗi
emphasis thành beat (duration khớp độ dài script cảnh).

## Ảnh

- Ưu tiên `javis_generate_image` (ChatGPT OAuth): phong cách nhất quán (cùng palette,
  không chữ lung tung trên ảnh trừ khi brief yêu cầu).
- Lưu `attachments/bai-giang/<slug>/scene-NN.png`, embed trong `lop-hoc.md`.
- Ảnh mang **ý**, không stock generic vô tri; mô tả đối tượng học trong prompt.

## Biểu đồ / sơ đồ

- Có số liệu so sánh / xu hướng → chart (bar/line) hoặc skill **`diagram-design`**.
- Không bịa số: thiếu số → dùng sơ đồ khái niệm hoặc ghi giả định rõ.
- Trục / chú thích tiếng Việt.

## OpenMAIC

OpenMAIC không chạy Remotion. Vẫn **ghi emphasis** trong plan để:
1. LLM generate slide biết bố cục nhấn,
2. TTS biết thứ tự giảng,
3. Có thể làm clip Remotion phụ sau nếu user muốn.
