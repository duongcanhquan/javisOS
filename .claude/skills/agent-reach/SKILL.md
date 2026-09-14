---
name: agent-reach
description: "Doctor/cài kênh MXH, video, RSS, GitHub, web (Agent-Reach) khi Tavily hay MCP chưa đủ."
description_en: "Install/check Agent-Reach channels (social, video, RSS, GitHub, web) when Tavily/MCP is not enough."
group: Marketing
license: MIT
metadata:
  version: "1.1"
  upstream: "https://github.com/Panniantong/Agent-Reach"
---

# Agent-Reach (lớp kênh internet)

## Dùng để làm gì

Cho agent **đọc/tìm** trên internet thật (X/Twitter, Reddit, YouTube, Bilibili, XHS, GitHub,
RSS, web…) khi Tavily hay MCP Meta **chưa** phủ. Việc của skill này: **cài, doctor, chọn
backend** - không tự viết scraper.

Nguồn: [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) (MIT).
Skill nghiệp vụ (`lang-nghe-mxh`, `tom-tat-video`, `theo-doi-rss-chu-de`,
`y-tuong-noi-dung-tu-trend`) nạp skill này khi cần kênh ngoài.

## Khi nào dùng

- «Cài Agent Reach», «doctor MXH», «sao không đọc được XHS/Twitter/Reddit»
- Skill lắng nghe / video / RSS báo thiếu kênh
- User hỏi Reach làm được gì trên máy/VPS này

**Không dùng** để viết báo cáo Ads/Page chính thức (MCP Meta) hay số POS.

## Chuẩn bị

1. Engine có **Bash** (Claude Code, Codex, Antigravity, Grok Build) → dùng CLI.
2. Engine API thuần → không gọi `agent-reach`; dùng Tavily / WebFetch / MCP đã đấu và
   **nói rõ** kênh MXH chưa có.
3. Đọc `references/channels.md` (bảng kênh) và `references/safety.md` (Cookie, VPS).

## Cách chạy

### Doctor (ưu tiên)

```bash
command -v agent-reach && agent-reach doctor
# hoặc
agent-reach doctor --json
```

Tóm tắt trong chat: kênh nào OK / thiếu / cần Cookie / cần proxy. Không dump log dài.

### Cài (chỉ khi user đồng ý sửa máy)

```text
Giúp cài Agent Reach theo:
https://raw.githubusercontent.com/Panniantong/Agent-Reach/main/docs/install.md
```

Mặc định an toàn: `agent-reach install` chỉ **kiểm** trừ khi user cho phép `--system`.
Không cài từ PyPI nhầm package khác tên.

### Gọi kênh

Sau doctor: **agent gọi thẳng upstream** (`yt-dlp`, `bili`, `gh`, `twitter`, OpenCLI,
`curl https://r.jina.ai/...`, mcporter/Exa…) theo SKILL upstream Reach. Javis không
bọc lại API.

Chi tiết lệnh theo việc → skill nghiệp vụ tương ứng.

## Fallback (bắt buộc khi Reach thiếu)

| Việc | Không có Reach thì |
|------|---------------------|
| Tra web chung | Tavily / WebSearch / WebFetch |
| Page/Ads Facebook chính thức | `tong-ket-facebook` / `bao-cao-facebook-ads` |
| Báo chí danh mục cố định | `tong-hop-bao-chi` |
| Click trang phức tạp | `agent-browser` (có sẵn) |

Luôn ghi trong báo cáo: **Nguồn kênh:** Reach / Tavily / … và khoảng trống.

## Liên kết

- Lắng nghe chủ đề → `lang-nghe-mxh`
- Video YT/Bilibili → `tom-tat-video`
- RSS topic → `theo-doi-rss-chu-de`
- Trend → content → `y-tuong-noi-dung-tu-trend`
- Nghiên cứu sâu web → `deep-research` (có thể gọi MXH như nhánh phụ)

## Bẫy

- Không lưu Cookie vào vault/git; không dùng nick chính (xem `safety.md`).
- Không ship Agent-Reach vào image Docker Javis; cài trên máy/VPS user.
- Không hứa mọi engine API đều đọc được XHS.

## Kiểm chứng

- [ ] Đã chạy doctor **hoặc** nêu rõ «chưa cài / engine không có shell»
- [ ] Skill nghiệp vụ biết dùng kênh nào / fallback nào
