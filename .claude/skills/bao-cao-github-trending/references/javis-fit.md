# Tư vấn Javis-fit (GitHub Trending)

Quyết định **Không / Chỉ xem / Có thể bổ sung** theo loại repo, không theo số sao.

## Không

- Tấn công / pentest / red team / exploit / shellcode / EDR evasion.
- Leak system prompt, jailbreak, «extracted prompts».
- Tải khóa học trả phí (Udemy, Hotmart…), downloader MXH làm mặc định.
- Sản phẩm full khác Javis (ERP/CRM khổng lồ, Android TV, terminal giả CRT).
- Framework ML hạ tầng (Transformers, v.v.) khi Javis đã có đường Ollama/CLI.

## Chỉ xem

- Engine model local lạ (C/Rust) — có thể thành backend sau, chưa phải skill.
- Agent nghiên cứu / code-review app — học kiến trúc, cải workflow có sẵn.
- Demo đẹp không dính OS cá nhân (globe 3D, sinh nhạc nếu user không làm nhạc).

## Có thể bổ sung

- Registry / kho skill: **cherry-pick** từng `SKILL.md` sau khi đọc, không import cả kho.
- Skill video / voice / landing nếu Javis đã có skill cùng việc — lấy 1–2 file, không nuốt studio.
- CLI/API có MCP hoặc lệnh máy rõ → dạng **connector-MCP** hoặc **plugin**, không phải skill chat.

## Dạng bổ sung

| Dạng | Khi nào |
|---|---|
| `skill` | Quy trình làm việc (tóm tắt, viết, review) gói trong SKILL.md |
| `connector-MCP` | Cần gọi API/dịch vụ ngoài đã có MCP |
| `plugin` | Engine/binary chạy cạnh Javis (voice, model local) |
| `không` | Chỉ xem hoặc Không |

Mặc định tối nay: **không tự cài**. «Có thể bổ sung» = đề xuất để chủ quyết.
