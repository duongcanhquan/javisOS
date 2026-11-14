#!/bin/sh
# Entrypoint container: DỜI các thư mục HOME mà CLI ngoài ghi vào sang volume /data
# rồi mới chạy lệnh chính (uvicorn).
#
# Vì sao tồn tại (báo cáo 16/08): Antigravity CLI (`agy`) do người dùng tự cài vào
# ~/.local/bin và giữ đăng nhập trong ~/.antigravity / ~/.config / ~/.gemini - tất cả nằm trong
# HOME của container, mà HOME KHÔNG nằm trên volume nào (chỉ /data, /brains, ~/.claude,
# ~/.codex được persist). Mỗi lần cập nhật image là container mới, HOME mới tinh: bay
# cả binary lẫn đăng nhập, người dùng phải cài + đăng nhập lại từ đầu, mãi mãi.
#
# Cách chữa: mỗi lần boot, link ~/.local, ~/.antigravity, ~/.config, ~/.gemini, ~/.grok vào /data/home/
# (volume /data sẵn có nên KHÔNG cần người dùng sửa docker-compose - chỉ cần image mới).
# Lần đầu sau khi có bản này, nội dung đang có trong HOME được dọn sang volume trước
# khi link, nên ai đã lỡ cài agy trong container hiện tại cũng không mất gì.
#
# An toàn: mọi bước đều nhịn lỗi (|| true / continue) - /data hỏng quyền thì bỏ qua
# việc link và server VẪN LÊN, chỉ mất tính năng giữ-qua-update chứ không chết app.
set -u

PERSIST_ROOT="${JAVIS_HOME_PERSIST:-/data/home}"

# ~/.gemini: `agy` để cấu hình MCP (~/.gemini/config/mcp_config.json - chỗ Javis đấu hub
# vào) và token OAuth của MCP ở đó. Thiếu nó thì mỗi lần cập nhật là mất hết kết nối MCP
# người dùng tự thêm, dù đăng nhập Google vẫn còn. Với GEMINI_FORCE_FILE_STORAGE=true trên
# Docker/headless, agy lưu token ra file thay vì keyring.
#
# ~/.grok: đăng nhập xAI của Grok Build (`~/.grok/auth.json`) cộng cấu hình cá nhân. Bỏ sót
# từ 0.50.0 tới 0.50.3, và nó hỏng đúng kiểu đã hỏng với `agy` hồi 16/08 - chỉ khó thấy hơn
# một bậc: binary `grok` nằm ở ~/.local/bin nên ĐƯỢC giữ, thẻ Models vẫn báo "Đã cài CLI",
# chỉ mỗi phiên đăng nhập là bay. Người dùng báo 29/08: "mỗi lần nâng cấp bản mới là grok
# lại bị logout". Thêm một chữ vào danh sách này là xong, không phải sửa docker-compose.
#
# ~/.copilot: GitHub Copilot CLI (binary `copilot`) - MCP config + phiên đăng nhập nếu có.
#
# ~/.npm và ~/.cache: chỗ `npx` và `uvx` giữ package của các nguồn MCP (~/.npm/_npx,
# ~/.cache/uv). Để ngoài volume thì mỗi lần cập nhật image là mất, và ngay sau cập nhật
# MỌI nguồn tải rồi cài lại cùng lúc — đúng lúc server đang khởi động, đĩa và RAM nghẽn.
# Giữ trên volume thì nguồn khởi động sau cập nhật giống như sau một lần restart thường.
for d in .local .antigravity .config .gemini .grok .copilot .npm .cache; do
    src="$HOME/$d"
    dst="$PERSIST_ROOT/$d"
    # Đã là symlink (boot thứ hai trở đi) → xong từ lâu.
    [ -L "$src" ] && continue
    mkdir -p "$dst" 2>/dev/null || continue
    # Container hiện tại đã có sẵn nội dung (agy cài trước bản này) → dọn sang volume,
    # KHÔNG ghi đè file đã có bên volume (bản bên volume là bản sống qua update).
    if [ -d "$src" ]; then
        cp -an "$src/." "$dst/" 2>/dev/null || true
        rm -rf "$src" 2>/dev/null || continue
    fi
    ln -sfn "$dst" "$src" 2>/dev/null || true
done

# Package npx đã cài (~/.npm/_npx) có thể build cho MỘT phiên bản Node major. Cập nhật
# image đổi major thì xoá chúng để npx cài lại, khỏi nạp nhầm binary cũ. Cache tải nằm cạnh
# nên lần cài lại gần như không cần mạng.
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || true)"
NODE_STAMP="$PERSIST_ROOT/.npm/.javis-node-major"
if [ -n "$NODE_MAJOR" ] && [ -d "$PERSIST_ROOT/.npm" ]; then
    if [ -f "$NODE_STAMP" ] && [ "$(cat "$NODE_STAMP" 2>/dev/null)" != "$NODE_MAJOR" ]; then
        rm -rf "$PERSIST_ROOT/.npm/_npx" 2>/dev/null || true
    fi
    echo "$NODE_MAJOR" > "$NODE_STAMP" 2>/dev/null || true
fi

# Tự cài Antigravity CLI (`agy`) và Grok Build (`grok`) nếu máy chưa có.
# Hai CLI này không phát hành qua npm, và không nhúng binary của Google/xAI vào image công khai.
# Cài nền lúc boot, vào ~/.local và ~/.grok đã link sang /data nên chỉ cài một lần.
# Hỏng thì ghi lại, lần sau thử lại, không cản server lên. Tắt bằng JAVIS_AUTO_INSTALL_CLIS=0.
CLI_STATE="$PERSIST_ROOT/.cli-auto-install"
co_cli() {
    command -v "$1" >/dev/null 2>&1 || [ -x "$2" ] || [ -x "$HOME/.local/bin/$1" ]
}
tu_cai_cli() {
    co_cli "$1" "$2" && { echo "ok $(date +%s)" > "$CLI_STATE/$1" 2>/dev/null; return 0; }
    echo "installing $(date +%s)" > "$CLI_STATE/$1" 2>/dev/null
    echo "[$(date -u +%FT%TZ)] cài $1 từ $3" >> "$CLI_STATE/install.log" 2>/dev/null
    if curl -fsSL --max-time 300 "$3" | bash >> "$CLI_STATE/install.log" 2>&1 && co_cli "$1" "$2"; then
        echo "ok $(date +%s)" > "$CLI_STATE/$1" 2>/dev/null
    else
        echo "failed $(date +%s)" > "$CLI_STATE/$1" 2>/dev/null
    fi
}
if [ "${JAVIS_AUTO_INSTALL_CLIS:-1}" != "0" ] && mkdir -p "$CLI_STATE" 2>/dev/null; then
    ( (
        tu_cai_cli agy "$HOME/.local/bin/agy" https://antigravity.google/cli/install.sh
        tu_cai_cli grok "$HOME/.grok/bin/grok" https://x.ai/cli/install.sh
    ) </dev/null >/dev/null 2>&1 & )
fi

exec "$@"
