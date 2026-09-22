/* Trang Hướng dẫn trong dashboard.
 *
 * Bốn mục menu (nhóm «Hướng dẫn», đặt ngay dưới «Kết nối»):
 *   guide_what    - VMOS làm được gì
 *   guide_connect - Kết nối (Models, MCP, kênh…)
 *   guide_studio  - Skill / Agent / Workflow
 *   guide_work    - Công việc & chức năng khác
 *
 * Nội dung viết sẵn bằng tiếng Việt, chữ đơn giản; sơ đồ bằng HTML/CSS (không cần mạng).
 * console.js gọi window.JavisGuides.render(el, id).
 */
(function () {
  "use strict";

  function ic(ten, opt) { return (window.ic ? window.ic(ten, opt) : ""); }
  function t(k, vars) {
    try { return (window.t ? window.t(k, vars) : k); } catch (e) { return k; }
  }
  const esc = (s) => (s || "").toString()
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");

  function go(id) {
    if (window.JavisNavigate) return window.JavisNavigate(id);
    const s = window.Alpine && Alpine.store("nav");
    if (s && s.go) s.go(id);
  }

  let _cssOk = false;
  function ensureCss() {
    if (_cssOk || document.getElementById("jvGuidesCss")) { _cssOk = true; return; }
    const st = document.createElement("style");
    st.id = "jvGuidesCss";
    st.textContent = `
.jv-g{max-width:920px;margin:0 auto;padding:4px 4px 48px;color:var(--text);line-height:1.55}
.jv-g-hero{margin:0 0 22px;padding:18px 20px;border-radius:14px;
  background:linear-gradient(135deg,var(--info-wash,rgba(80,140,255,.12)),transparent 70%);
  border:1px solid var(--hairline)}
.jv-g-hero h2{margin:0 0 8px;font-size:22px;font-weight:650;color:var(--text-hi,var(--text));display:flex;align-items:center;gap:10px}
.jv-g-hero p{margin:0;color:var(--text2);font-size:15px;max-width:62ch}
.jv-g-toc{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 22px}
.jv-g-toc button{border:1px solid var(--hairline);background:var(--surface-2,var(--bg2));color:var(--text2);
  border-radius:999px;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer}
.jv-g-toc button:hover,.jv-g-toc button.on{border-color:var(--info-line,#5a9);color:var(--info-ink,var(--text));background:var(--info-wash)}
.jv-g-sec{margin:0 0 28px}
.jv-g-sec > h3{margin:0 0 10px;font-size:17px;font-weight:650;color:var(--text-hi,var(--text));
  display:flex;align-items:center;gap:8px}
.jv-g-sec > p,.jv-g-sec li{font-size:14.5px;color:var(--text2)}
.jv-g-sec ul,.jv-g-sec ol{margin:8px 0 0;padding-left:1.25em}
.jv-g-sec li{margin:4px 0}
.jv-g-note{margin:12px 0 0;padding:10px 12px;border-radius:10px;font-size:13.5px;color:var(--text2);
  background:var(--surface-2,rgba(127,127,127,.08));border-left:3px solid var(--info-line,#5a9)}
.jv-g-warn{border-left-color:var(--warn,#e0a33e)}
.jv-g-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}
@media(max-width:720px){.jv-g-grid{grid-template-columns:1fr}}
.jv-g-card{padding:14px 14px 12px;border:1px solid var(--hairline);border-radius:12px;background:var(--bg2,transparent);min-width:0}
.jv-g-card h4{margin:0 0 6px;font-size:14.5px;font-weight:650;color:var(--text);display:flex;align-items:center;gap:7px}
.jv-g-card p{margin:0;font-size:13.5px;color:var(--text2);line-height:1.45}
.jv-g-card .jv-g-go{margin-top:10px}
.jv-g-go{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--hairline);background:var(--surface-2);
  color:var(--text);border-radius:8px;padding:6px 11px;font:inherit;font-size:13px;cursor:pointer}
.jv-g-go:hover{border-color:var(--info-line);color:var(--info-ink,var(--text-hi))}
.jv-g-steps{counter-reset:jvgs;list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:10px}
.jv-g-steps li{position:relative;padding:12px 14px 12px 52px;border:1px solid var(--hairline);border-radius:12px;background:var(--bg2,transparent)}
.jv-g-steps li::before{counter-increment:jvgs;content:counter(jvgs);position:absolute;left:14px;top:12px;
  width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  background:var(--info-wash);color:var(--info-ink,var(--text));font-weight:700;font-size:13px}
.jv-g-steps b{color:var(--text);font-weight:650}
.jv-g-flow{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:14px 0;padding:14px;border-radius:12px;
  border:1px dashed var(--hairline);background:rgba(120,180,255,.04)}
.jv-g-flow .n{padding:10px 14px;border-radius:10px;border:1px solid var(--hairline);background:var(--bg2,var(--surface-2));
  font-size:13.5px;font-weight:600;color:var(--text);text-align:center;min-width:100px}
.jv-g-flow .n.hi{border-color:var(--info-line);background:var(--info-wash)}
.jv-g-flow .ar{color:var(--text3);font-size:18px;flex:none}
.jv-g-pipe{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:8px;align-items:stretch;margin:14px 0}
@media(max-width:720px){.jv-g-pipe{grid-template-columns:1fr;}.jv-g-pipe .ar{justify-self:center;transform:rotate(90deg)}}
.jv-g-pipe .box{padding:12px;border-radius:12px;border:1px solid var(--hairline);background:var(--bg2);text-align:center}
.jv-g-pipe .box b{display:block;font-size:14px;color:var(--text);margin-bottom:4px}
.jv-g-pipe .box span{font-size:12.5px;color:var(--text3)}
.jv-g-pipe .ar{align-self:center;color:var(--text3);font-size:20px}
.jv-g-table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:10px}
.jv-g-table th,.jv-g-table td{border:1px solid var(--hairline);padding:8px 10px;text-align:left;vertical-align:top}
.jv-g-table th{background:var(--surface-2);color:var(--text);font-weight:650}
.jv-g-table td{color:var(--text2)}
.jv-g-map{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:12px}
@media(max-width:800px){.jv-g-map{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.jv-g-map{grid-template-columns:1fr}}
.jv-g-map .m{padding:12px;border-radius:12px;border:1px solid var(--hairline);background:var(--bg2);cursor:pointer;transition:.15s}
.jv-g-map .m:hover{border-color:var(--info-line);background:var(--info-wash)}
.jv-g-map .m .t{font-size:13.5px;font-weight:650;color:var(--text);display:flex;align-items:center;gap:6px;margin-bottom:4px}
.jv-g-map .m .d{font-size:12.5px;color:var(--text3);line-height:1.4}
.jv-g-chk{list-style:none;margin:10px 0 0;padding:0}
.jv-g-chk li{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--hairline);font-size:14px;color:var(--text2)}
.jv-g-chk li:last-child{border-bottom:0}
.jv-g-chk .box{flex:none;width:18px;height:18px;margin-top:2px;border-radius:5px;border:1.5px solid var(--info-line);background:var(--info-wash)}
.jv-g-twin{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
@media(max-width:720px){.jv-g-twin{grid-template-columns:1fr}}
`;
    document.head.appendChild(st);
    _cssOk = true;
  }

  function toc(active) {
    const items = [
      ["guide_what", "VMOS làm được gì"],
      ["guide_connect", "Kết nối"],
      ["guide_studio", "Skill · Agent · Workflow"],
      ["guide_work", "Công việc & chức năng"],
    ];
    return `<div class="jv-g-toc">${items.map(([id, lab]) =>
      `<button type="button" class="${id === active ? "on" : ""}" data-ggo="${esc(id)}">${esc(lab)}</button>`
    ).join("")}</div>`;
  }

  function bind(el) {
    el.querySelectorAll("[data-ggo]").forEach((b) => {
      b.onclick = () => go(b.getAttribute("data-ggo"));
    });
  }

  function hero(icon, title, lead) {
    return `<div class="jv-g-hero"><h2>${ic(icon)} ${esc(title)}</h2><p>${esc(lead)}</p></div>`;
  }

  /* ---------- 1. VMOS làm được gì ---------- */
  function pageWhat() {
    return `<div class="jv-g">
      ${hero("sparkles", "VMOS làm được gì?",
        "VMOS là trợ lý AI gắn với bộ nhớ và công cụ của bạn. Nó chat được, nhớ việc, chạy cộng sự (agent/quy trình), và nối được dịch vụ ngoài (email, Ads, Telegram…).")}
      ${toc("guide_what")}

      <div class="jv-g-sec">
        <h3>${ic("lightbulb")} Bản đồ nhanh - theo menu trái</h3>
        <p>Mỗi nhóm trên rail có một nhiệm vụ. Nhớ thứ tự: <b>Models → Chat → Cộng sự / Skills → Kết nối</b>.</p>
        <div class="jv-g-flow">
          <div class="n hi">1. Kết nối<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Models · MCP</span></div>
          <div class="ar">→</div>
          <div class="n">2. Trợ lý<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Chat</span></div>
          <div class="ar">→</div>
          <div class="n">3. Năng lực<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Cộng sự · Skill</span></div>
          <div class="ar">→</div>
          <div class="n">4. Việc / Bộ não<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Kanban · File</span></div>
        </div>
        <div class="jv-g-note">Mẹo: làm xong <b>Kết nối → Models</b> trước, rồi mới chat. Không có bộ não (model) thì VMOS không trả lời được.</div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("lightbulb")} Nhiệm vụ từng nhóm menu</h3>
        <table class="jv-g-table">
          <thead><tr><th>Nhóm</th><th>Nhiệm vụ</th><th>Trang chính</th></tr></thead>
          <tbody>
            <tr><td><b>Trợ lý</b></td><td>Nói chuyện với AI trên web</td><td>Home · Chat</td></tr>
            <tr><td><b>Bộ não</b></td><td>File, Drive, tự học theo brain</td><td>Files · Drive · Tự học</td></tr>
            <tr><td><b>Code</b></td><td>Dòng lệnh thật trên máy chạy VMOS</td><td>Terminal</td></tr>
            <tr><td><b>Năng lực</b></td><td>Đội AI + hộp thư khách + skill</td><td><b>Cộng sự</b> · Hội thoại khách · Skills · Plugins</td></tr>
            <tr><td><b>Việc</b></td><td>Họp, bài giảng, Kanban…</td><td>Kanban · Họp · …</td></tr>
            <tr><td><b>Kết nối</b></td><td>Não AI + dịch vụ ngoài + kênh ĐT</td><td>Models · Kết nối · Kênh</td></tr>
            <tr><td><b>Hệ thống</b></td><td>Cài đặt, mức dùng, link public</td><td>Cài đặt · <b>Chia sẻ</b></td></tr>
          </tbody>
        </table>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("lightbulb")} Bạn dùng VMOS để làm gì?</h3>
        <div class="jv-g-map">
          <div class="m" data-ggo="chat"><div class="t">${ic("message-circle")} Trò chuyện</div><div class="d">Hỏi việc, viết email, tóm tắt tài liệu, nhờ gợi ý.</div></div>
          <div class="m" data-ggo="kanban"><div class="t">${ic("square-kanban")} Giao việc nền</div><div class="d">Nói một goal - VMOS tự chạy task trên bảng Việc.</div></div>
          <div class="m" data-ggo="skills"><div class="t">${ic("puzzle")} Kỹ năng sẵn</div><div class="d">SEO, kế toán, slide, nghiên cứu… bật skill rồi gọi.</div></div>
          <div class="m" data-ggo="workspace"><div class="t">${ic("bot")} Cộng sự</div><div class="d">Trợ Lý (Agent) và Quy Trình (Workflows) trong một trang.</div></div>
          <div class="m" data-ggo="conversations"><div class="t">${ic("messages-square")} Hội thoại khách</div><div class="d">Hộp thư + bot CSKH Telegram/Zalo.</div></div>
          <div class="m" data-ggo="meetings"><div class="t">${ic("mic")} Cuộc họp</div><div class="d">Ghi lời nói thành chữ, tóm tắt quyết định.</div></div>
          <div class="m" data-ggo="mcp"><div class="t">${ic("plug")} Dữ liệu thật</div><div class="d">Gmail, Ads, POS… qua trang Kết nối.</div></div>
          <div class="m" data-ggo="learn"><div class="t">${ic("brain")} Tự học</div><div class="d">Sau chat, VMOS rút ký ức / Wiki (có thể hoàn tác).</div></div>
          <div class="m" data-ggo="share"><div class="t">${ic("link")} Chia sẻ</div><div class="d">Xem / thu hồi mọi link công khai đang sống.</div></div>
        </div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("list-todo")} 15 phút đầu - làm theo thứ tự này</h3>
        <ul class="jv-g-chk">
          <li><span class="box"></span><span><b>Đăng nhập</b> và chọn đúng <b>bộ não (brain)</b> đang dùng.</span></li>
          <li><span class="box"></span><span>Vào <b>Models</b> - kết nối ít nhất một nhà (Claude, ChatGPT, Gemini, Antigravity…).</span></li>
          <li><span class="box"></span><span>Về <b>Chat</b> - hỏi thử một câu đơn giản để chắc model chạy.</span></li>
          <li><span class="box"></span><span>Mở <b>Cộng sự</b> - xem Trợ Lý / Quy Trình chuẩn đã sync.</span></li>
          <li><span class="box"></span><span>(Tuỳ chọn) <b>Kết nối</b> MCP / Kênh nếu cần Gmail · Ads · Telegram.</span></li>
        </ul>
        <div style="margin-top:14px;display:flex;flex-wrap:wrap;gap:8px">
          <button type="button" class="jv-g-go" data-ggo="models">${ic("cpu")} Mở Models</button>
          <button type="button" class="jv-g-go" data-ggo="guide_connect">${ic("link")} Hướng dẫn kết nối</button>
          <button type="button" class="jv-g-go" data-ggo="workspace">${ic("bot")} Mở Cộng sự</button>
          <button type="button" class="jv-g-go" data-ggo="chat">${ic("message-circle")} Vào Chat</button>
        </div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("info")} Khác chatbot thường ở chỗ nào?</h3>
        <table class="jv-g-table">
          <thead><tr><th>Chatbot thường</th><th>VMOS</th></tr></thead>
          <tbody>
            <tr><td>Chỉ trả lời trong cửa sổ chat</td><td>Có bộ nhớ, file, skill, cộng sự, kênh ngoài</td></tr>
            <tr><td>Mỗi lần hỏi gần như bắt đầu lại</td><td>Wiki / ký ức / dự án gắn theo brain của bạn</td></tr>
            <tr><td>Khó nối Gmail, Ads…</td><td>Trang Kết nối (MCP) + kênh Telegram/Zalo</td></tr>
            <tr><td>Một model cố định</td><td>Đổi nhà cung cấp ở Models mà vẫn giữ skill</td></tr>
          </tbody>
        </table>
      </div>
    </div>`;
  }

  /* ---------- 2. Kết nối ---------- */
  function pageConnect() {
    return `<div class="jv-g">
      ${hero("link", "Hướng dẫn kết nối",
        "Kết nối = cho VMOS «não» (model) và «tay chân» (Gmail, Ads, Telegram…). Làm đúng thứ tự dưới đây sẽ ít lỗi nhất.")}
      ${toc("guide_connect")}

      <div class="jv-g-sec">
        <h3>${ic("workflow")} Thứ tự nên làm</h3>
        <div class="jv-g-flow">
          <div class="n hi">Models<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Bộ não AI</span></div>
          <div class="ar">→</div>
          <div class="n">Kết nối MCP<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Gmail · Ads…</span></div>
          <div class="ar">→</div>
          <div class="n">Kênh<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Telegram · Zalo</span></div>
          <div class="ar">→</div>
          <div class="n">API công cụ<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Key phụ</span></div>
        </div>
        <div class="jv-g-note warn">Chưa có Models mà đã kéo MCP: chat vẫn chết. Luôn nối model trước.</div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("cpu")} 1) Models - chọn bộ não</h3>
        <p>Menu <b>Kết nối → Models</b>. Mỗi «nhà» là một cách chạy AI:</p>
        <div class="jv-g-grid">
          <div class="jv-g-card">
            <h4>${ic("bot")} Claude / ChatGPT (CLI)</h4>
            <p>Đăng nhập tài khoản trên máy hoặc VPS (Claude Code, Codex). Không cần dán API key nếu đã login CLI.</p>
          </div>
          <div class="jv-g-card">
            <h4>${ic("sparkles")} Antigravity (<code>agy</code>)</h4>
            <p>Cài CLI <code>agy</code>, đăng nhập, rồi bấm thử trên thẻ Antigravity trong Models.</p>
          </div>
          <div class="jv-g-card">
            <h4>${ic("key")} API key</h4>
            <p>OpenRouter, OpenAI, Gemini, Anthropic, Groq… dán key vào ô, bấm Kết nối.</p>
          </div>
          <div class="jv-g-card">
            <h4>${ic("sliders-horizontal")} Model chính / phụ</h4>
            <p>Chọn model chat chính; có thể ghim model cho việc nền (Research) và Telegram riêng.</p>
          </div>
        </div>
        <ol class="jv-g-steps">
          <li><b>Mở Models</b> - xem thẻ «Đã kết nối» và «Chưa kết nối».</li>
          <li><b>Chọn một nhà</b> - login CLI hoặc dán key → bấm Kết nối / Thử.</li>
          <li><b>Chọn model mặc định</b> trên cùng trang (ô model chính).</li>
          <li><b>Về Chat hỏi thử</b> - nếu trả lời được là xong bước này.</li>
        </ol>
        <button type="button" class="jv-g-go" data-ggo="models" style="margin-top:12px">${ic("cpu")} Mở trang Models</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("plug")} 2) Kết nối (MCP) - dịch vụ ngoài</h3>
        <p>Menu <b>Kết nối → Kết nối</b>. Đây là chỗ gắn Gmail, Facebook Ads, POS, Drive… Mỗi dịch vụ là một «ổ cắm».</p>
        <div class="jv-g-pipe">
          <div class="box"><b>Bạn</b><span>Bấm Kết nối<br>đăng nhập / dán key</span></div>
          <div class="ar">→</div>
          <div class="box"><b>VMOS</b><span>Giữ phiên an toàn<br>gọi tool khi cần</span></div>
          <div class="ar">→</div>
          <div class="box"><b>Dịch vụ</b><span>Gmail · Ads · …<br>trả số liệu thật</span></div>
        </div>
        <ul>
          <li>Đọc hướng dẫn ngắn trên từng thẻ trước khi bấm.</li>
          <li>Một số dịch vụ cần quyền «đọc» trước, quyền «gửi/sửa» sau.</li>
          <li>Lỗi thường gặp: hết hạn đăng nhập → vào lại thẻ đó bấm Kết nối lại.</li>
        </ul>
        <button type="button" class="jv-g-go" data-ggo="mcp" style="margin-top:10px">${ic("plug")} Mở trang Kết nối</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("send")} 3) Kênh Telegram / Zalo</h3>
        <p>Menu <b>Kết nối → Kênh</b>. Sau khi có bot token (Telegram) hoặc ghép Zalo Bot, bạn nhắn từ điện thoại như nhắn chat trên web.</p>
        <div class="jv-g-note">Bot chuyên trách nằm ở <b>Năng lực → Hội thoại khách</b> (tab Chatbot): mang đúng một Agent ra nói với khách. Khác kênh chính (bạn hỏi Javis từ điện thoại).</div>
        <button type="button" class="jv-g-go" data-ggo="channels" style="margin-top:10px">${ic("send")} Mở trang Kênh</button>
        <button type="button" class="jv-g-go" data-ggo="conversations" style="margin-top:10px;margin-left:8px">${ic("messages-square")} Hội thoại khách</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("key")} 4) API công cụ & Gói</h3>
        <div class="jv-g-twin">
          <div class="jv-g-card">
            <h4>API công cụ</h4>
            <p>Key phụ cho ảnh, tìm web, TTS… Chỉ điền khi skill/tool báo thiếu key.</p>
            <button type="button" class="jv-g-go" data-ggo="tool_apis">Mở API công cụ</button>
          </div>
          <div class="jv-g-card">
            <h4>Gói</h4>
            <p>Cài thêm bộ kết nối / năng lực từ file .zip. Xem trước nội dung gói rồi mới cài.</p>
            <button type="button" class="jv-g-go" data-ggo="packs">Mở Gói</button>
          </div>
        </div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("triangle-alert")} Khi nào «não» không chạy?</h3>
        <ul>
          <li>CLI chưa cài hoặc chưa login trên <b>đúng máy/container</b> đang chạy VMOS.</li>
          <li>Key hết hạn / sai nhà cung cấp.</li>
          <li>Trên VPS nhiều bản: mỗi tenant có bộ não riêng - login trên quan không tự sang maihuong.</li>
        </ul>
      </div>
    </div>`;
  }

  /* ---------- 3. Skill / Agent / Workflow ---------- */
  function pageStudio() {
    return `<div class="jv-g">
      ${hero("puzzle", "Skill · Agent · Workflow",
        "Ba lớp năng lực. Tạo Agent/Workflow ở trang Cộng sự (Năng lực). Hiểu đúng từng lớp rồi mới tạo - đỡ trùng và đỡ rối.")}
      ${toc("guide_studio")}

      <div class="jv-g-sec">
        <h3>${ic("workflow")} Ba lớp khác nhau thế nào?</h3>
        <div class="jv-g-pipe">
          <div class="box"><b>Skill</b><span>Một «công thức»<br>cho một loại việc</span></div>
          <div class="ar">→</div>
          <div class="box"><b>Agent</b><span>«Nhân viên» AI<br>+ skill + model</span></div>
          <div class="ar">→</div>
          <div class="box"><b>Workflow</b><span>Dây chuyền<br>nhiều agent</span></div>
        </div>
        <table class="jv-g-table">
          <thead><tr><th></th><th>Là gì?</th><th>Khi nào dùng?</th><th>Mở ở đâu?</th></tr></thead>
          <tbody>
            <tr><td><b>Skill</b></td><td>File hướng dẫn (SKILL.md). VMOS tự nạp khi câu bạn khớp mô tả.</td><td>Một việc lặp lại: viết SEO, đọc hóa đơn…</td><td>Năng lực → Skills</td></tr>
            <tr><td><b>Agent</b></td><td>Trợ lý có vai trò, prompt, skill, model, tài liệu trợ lý.</td><td>Muốn «người» chuyên một mảng.</td><td>Năng lực → <b>Cộng sự</b> → tab Trợ Lý</td></tr>
            <tr><td><b>Workflow</b></td><td>Chuỗi bước: agent A xong → agent B… có thể kiểm chứng.</td><td>Việc nhiều giai đoạn.</td><td>Cộng sự → tab Quy Trình</td></tr>
          </tbody>
        </table>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("puzzle")} Skill - cài và dùng</h3>
        <ol class="jv-g-steps">
          <li><b>Mở Skills</b> (nhóm Năng lực). Bật/tắt bằng ô tick trên từng thẻ.</li>
          <li><b>Tạo mới</b>: đặt tên nhóm + <b>mô tả tiếng Việt 2–3 dòng</b> (làm gì · cần gì · lưu ý). Tối đa 150 ký tự.</li>
          <li><b>Gọi tay</b>: trong Chat gõ <code>/</code> rồi chọn skill, hoặc nói đúng từ khóa trong mô tả.</li>
          <li><b>Xuất/nhập</b>: tải gói để mang sang máy/brain khác.</li>
        </ol>
        <div class="jv-g-note">Mô tả tốt: «Tóm tắt biên bản họp thành việc cần làm. Cần file .md trong brain. Bỏ qua nếu chưa có ghi chú.» - không mở đầu bằng «Kích hoạt khi…».</div>
        <button type="button" class="jv-g-go" data-ggo="skills" style="margin-top:10px">${ic("puzzle")} Mở Skills</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("bot")} Agent - tạo trợ lý (Cộng sự)</h3>
        <ol class="jv-g-steps">
          <li><b>Năng lực → Cộng sự → tab Trợ Lý (Agent) → + Agent</b>.</li>
          <li>Điền <b>vai trò</b> rõ (2–3 dòng tiếng Việt): làm gì, khi nào, cần dữ liệu gì.</li>
          <li>Tick <b>skills</b> được phép dùng; chọn <b>model</b> (hoặc để mặc định).</li>
          <li>Viết <b>system prompt</b> chi tiết hơn (cách làm, định dạng đầu ra, điều cấm).</li>
          <li>Tuỳ chọn: thêm file vào <b>Tài liệu trợ lý</b> (SOP / mẫu gắn đúng agent, khác tủ tài liệu phiên chat).</li>
        </ol>
        <div class="jv-g-grid">
          <div class="jv-g-card">
            <h4>Ví dụ vai trò tốt</h4>
            <p>«Viết email bán hàng, giọng thân mật. Cần brief sản phẩm trong brain. Không gửi mail thật nếu chưa có danh sách.»</p>
          </div>
          <div class="jv-g-card">
            <h4>Chạy agent ở đâu?</h4>
            <p>Trong Quy Trình, Hội thoại khách (chatbot), hoặc khi bạn nhờ VMOS dùng agent đó. Agent có bộ nhớ / tài liệu riêng trong vault.</p>
          </div>
        </div>
        <button type="button" class="jv-g-go" data-ggo="workspace" style="margin-top:10px">${ic("bot")} Mở Cộng sự</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("workflow")} Workflow - dây chuyền (Cộng sự)</h3>
        <div class="jv-g-flow">
          <div class="n">Bước 1<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Agent nghiên cứu</span></div>
          <div class="ar">→</div>
          <div class="n hi">Bước 2<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Agent viết</span></div>
          <div class="ar">→</div>
          <div class="n">Kiểm chứng<br><span style="font-weight:400;font-size:12px;color:var(--text3)">Agent soi lỗi</span></div>
          <div class="ar">→</div>
          <div class="n">Kết quả<br><span style="font-weight:400;font-size:12px;color:var(--text3)">File / chat</span></div>
        </div>
        <ol class="jv-g-steps">
          <li>Mở <b>Cộng sự → Quy Trình (Workflows)</b>. Nếu mới: bấm <b>Tạo mẫu</b> để có ví dụ chạy được.</li>
          <li>Mỗi bước chọn agent + mô tả nhiệm vụ. Dùng <code>{{input}}</code> cho đầu vào user, <code>{{prev}}</code> cho kết quả bước trước.</li>
          <li>Bật quy trình → bấm <b>▶ Chạy</b> (hoặc gọi từ Telegram/Kanban tùy cấu hình).</li>
        </ol>
        <button type="button" class="jv-g-go" data-ggo="workspace" style="margin-top:10px">${ic("workflow")} Mở Cộng sự</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("messages-square")} Hội thoại khách & Chia sẻ</h3>
        <div class="jv-g-twin">
          <div class="jv-g-card">
            <h4>Hội thoại khách</h4>
            <p>Năng lực → Hội thoại khách: hộp thư + kênh + chatbot mang đúng một Agent ra CSKH.</p>
            <button type="button" class="jv-g-go" data-ggo="conversations">Mở Hội thoại khách</button>
          </div>
          <div class="jv-g-card">
            <h4>Chia sẻ</h4>
            <p>Hệ thống → Chia sẻ: xem / thu hồi link công khai. Tạo agent vẫn ở Cộng sự.</p>
            <button type="button" class="jv-g-go" data-ggo="share">Mở Chia sẻ</button>
          </div>
        </div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("toolbox")} Plugins - dùng thế nào?</h3>
        <p><b>Plugin</b> = mã Python chạy thật, thêm <b>tool</b> (engine gọi được) hoặc <b>hook</b>. Khác skill (chỉ là hướng dẫn chữ) và khác MCP (nguồn dữ liệu/app ngoài).</p>
        <div class="jv-g-flow">
          <div class="n">Năng lực → Plugins</div>
          <div class="ar">→</div>
          <div class="n hi">Bật plugin<br><span style="font-weight:400;font-size:12px;color:var(--text3)">● đang chạy</span></div>
          <div class="ar">→</div>
          <div class="n">Chat nhắc tool<br><span style="font-weight:400;font-size:12px;color:var(--text3)">vd «bây giờ mấy giờ»</span></div>
        </div>
        <ol class="jv-g-steps">
          <li><b>Xem danh sách</b> - menu <b>Năng lực → Plugins</b>. Nhãn: Có sẵn / Toàn cục / Brain này.</li>
          <li><b>Bật đúng cái cần</b> - chỉ thẻ «đang chạy» mới có tool. Đọc hàng chip tool để biết tên tool.</li>
          <li><b>Dùng trong Chat</b> - nói việc + tên tool nếu cần (vd «dùng javis_youtube_read tóm tắt link này»).</li>
          <li><b>Plugin tự cài</b> - cần <code>JAVIS_ENABLE_USER_PLUGINS=true</code> rồi khởi động lại; thả thư mục có <code>plugin.yaml</code> + <code>plugin.py</code>.</li>
        </ol>
        <div class="jv-g-note">Một số plugin cần Kết nối trước (ChatGPT OAuth cho ảnh, Meta Ads, Zalo…). Tool sẽ báo thiếu gì - đừng đoán.</div>
        <table class="jv-g-table">
          <thead><tr><th>Plugin có sẵn (ví dụ)</th><th>Khi nào dùng</th></tr></thead>
          <tbody>
            <tr><td><code>datetime-vn</code></td><td>Hỏi giờ / ngày VN</td></tr>
            <tr><td><code>youtube-read</code></td><td>Tóm tắt video YouTube từ phụ đề</td></tr>
            <tr><td><code>script-video</code></td><td>Render mp4 từ kịch bản (ảnh + TTS)</td></tr>
            <tr><td><code>image-chatgpt</code></td><td>Tạo ảnh (đã login ChatGPT)</td></tr>
            <tr><td><code>javis-task</code> / <code>javis-schedule</code></td><td>Giao việc Kanban / việc định kỳ từ chat</td></tr>
          </tbody>
        </table>
        <button type="button" class="jv-g-go" data-ggo="plugins" style="margin-top:12px">${ic("toolbox")} Mở Plugins</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("play")} Ví dụ bổ sung: AutoClip (cắt highlight video)</h3>
        <p><a href="https://github.com/zhouxiaoka/autoclip" target="_blank" rel="noopener">zhouxiaoka/autoclip</a> - AI trích highlight, cắt clip từ YouTube/Bilibili/file local. <b>Chưa ship sẵn trong VMOS</b>; gắn theo 1 trong 3 cách dưới (ưu tiên MCP).</p>
        <div class="jv-g-pipe">
          <div class="box"><b>1. MCP</b><span>Khuyến nghị<br>có sẵn trong AutoClip</span></div>
          <div class="ar">→</div>
          <div class="box"><b>2. Plugin</b><span>Bọc CLI/API<br>nếu muốn tool VMOS</span></div>
          <div class="ar">→</div>
          <div class="box"><b>3. Skill</b><span>Chỉ dạy quy trình<br>+ Terminal</span></div>
        </div>
        <ol class="jv-g-steps">
          <li><b>Cài AutoClip trên máy/VPS</b> (Docker hoặc <code>pip install -e .</code>). Cần ffmpeg. Kiểm: <code>autoclip doctor</code>.</li>
          <li><b>Cách A - MCP (nhanh nhất)</b>: AutoClip có lệnh <code>autoclip mcp</code>. Trong VMOS: <b>Kết nối → Tự thêm (nâng cao)</b>, loại stdio, lệnh trỏ tới binary trong venv, args <code>mcp</code>. Tool chính: <code>clip_video</code>, <code>get_job_status</code>, <code>export_clip</code>… Chat: «cắt highlight file này bằng AutoClip».</li>
          <li><b>Cách B - Plugin VMOS</b>: viết plugin mỏng gọi <code>autoclip run … --json</code> hoặc HTTP <code>:8000/api/v1/…</code>, đăng ký tool kiểu <code>javis_autoclip_run</code>. Bật user plugins + thả vào thư mục plugin toàn cục/brain.</li>
          <li><b>Cách C - Skill + Terminal</b>: skill hướng dẫn «khi nào gọi autoclip»; agent có shell chạy lệnh. Không cần plugin nếu máy đã có CLI.</li>
        </ol>
        <div class="jv-g-note warn">AutoClip nặng RAM/ổ (thường ≥4–8 GB). Trên VPS nhiều tenant: cài một bản dùng chung hoặc chỉ trên máy có GPU/ffmpeg đủ mạnh. Đừng nhầm với plugin <code>youtube-read</code> (chỉ đọc phụ đề) hay <code>script-video</code> (tạo video từ chữ).</div>
        <div class="jv-g-twin" style="margin-top:12px">
          <div class="jv-g-card">
            <h4>Chat mẫu sau khi nối MCP</h4>
            <p>«Dùng AutoClip cắt highlight video <code>exports/raw/talk.mp4</code>, min_score 0.5, rồi liệt kê file clip.»</p>
          </div>
          <div class="jv-g-card">
            <h4>Đọc thêm</h4>
            <p>Docs VMOS: trang Plugins + Kết nối. AutoClip: <code>docs/CLI_AND_MCP.md</code> trên GitHub (CLI, MCP, Ollama).</p>
          </div>
        </div>
        <div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:8px">
          <button type="button" class="jv-g-go" data-ggo="mcp">${ic("plug")} Mở Kết nối</button>
          <button type="button" class="jv-g-go" data-ggo="plugins">${ic("toolbox")} Mở Plugins</button>
          <button type="button" class="jv-g-go" data-ggo="conversations">${ic("messages-square")} Hội thoại khách</button>
        </div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("messages-square")} Chatbot (trong Hội thoại khách)</h3>
        <p>Đưa một Agent ra bot Telegram/Zalo riêng cho khách - khác kênh chat cá nhân của bạn. Mở <b>Năng lực → Hội thoại khách → tab Chatbot</b>.</p>
        <button type="button" class="jv-g-go" data-ggo="conversations" style="margin-top:10px">${ic("messages-square")} Mở Hội thoại khách</button>
      </div>
    </div>`;
  }

  /* ---------- 4. Công việc & chức năng ---------- */
  function pageWork() {
    return `<div class="jv-g">
      ${hero("clipboard-check", "Công việc & chức năng khác",
        "Sau khi đã nối model: giao việc nền, họp, học từ chat, quản lý file, việc lặp mỗi ngày.")}
      ${toc("guide_work")}

      <div class="jv-g-sec">
        <h3>${ic("square-kanban")} Tạo công việc (Kanban)</h3>
        <p>Menu <b>Công việc → Việc</b>. Bạn nói mục tiêu bằng lời; VMOS tách thành task và chạy nền.</p>
        <div class="jv-g-flow">
          <div class="n">Bạn nói goal</div>
          <div class="ar">→</div>
          <div class="n hi">VMOS đặc tả</div>
          <div class="ar">→</div>
          <div class="n">Chạy task</div>
          <div class="ar">→</div>
          <div class="n">Chờ bạn duyệt<br><span style="font-weight:400;font-size:12px;color:var(--text3)">nếu cần quyền</span></div>
        </div>
        <ol class="jv-g-steps">
          <li>Mở trang <b>Việc</b>, mô tả rõ muốn gì (kèm ràng buộc: deadline, không gửi mail thật…).</li>
          <li>Theo dõi cột trên bảng: đang chạy / cần bạn / xong.</li>
          <li>Nếu task xin quyền hành động thật (gửi tin, đăng bài…) - đọc kỹ rồi mới cho phép.</li>
        </ol>
        <div class="jv-g-note warn">Việc nền có thể tốn token. Xem trang <b>Mức dùng</b> nếu muốn theo dõi chi phí.</div>
        <button type="button" class="jv-g-go" data-ggo="kanban" style="margin-top:10px">${ic("square-kanban")} Mở bảng Việc</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("repeat")} Việc định kỳ (vòng lặp)</h3>
        <p>Menu <b>Công việc → Việc định kỳ</b> (Self-improve / loops). Ví dụ: mỗi sáng tổng kết email, mỗi 2 giờ quét tin.</p>
        <ul>
          <li>Đặt lịch kiểu «mỗi 120 phút» hoặc cron.</li>
          <li>Viết rõ nhiệm vụ trong thân loop - đừng để trống.</li>
          <li>Có thể tắt nhanh khi không cần chạy nền.</li>
        </ul>
        <button type="button" class="jv-g-go" data-ggo="selfimprove" style="margin-top:10px">${ic("repeat")} Mở Việc định kỳ</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("mic")} Cuộc họp · Bài giảng · Video · Marketing</h3>
        <div class="jv-g-grid">
          <div class="jv-g-card">
            <h4>${ic("mic")} Cuộc họp</h4>
            <p>Ghi âm → chữ → tóm tắt quyết định / việc cần làm. Nên nói rõ ngôn ngữ trước khi ghi.</p>
            <button type="button" class="jv-g-go" data-ggo="meetings">Mở Cuộc họp</button>
          </div>
          <div class="jv-g-card">
            <h4>${ic("book-open")} Bài giảng</h4>
            <p>Khung làm bài giảng / lớp học (kết hợp skill bài giảng, slide, OpenMAIC…).</p>
            <button type="button" class="jv-g-go" data-ggo="baigiang">Mở Bài giảng</button>
          </div>
          <div class="jv-g-card">
            <h4>${ic("play")} Video</h4>
            <p>Điều phối pipeline làm video (brief → kịch bản → render).</p>
            <button type="button" class="jv-g-go" data-ggo="video">Mở Video</button>
          </div>
          <div class="jv-g-card">
            <h4>${ic("sparkles")} Marketing</h4>
            <p>Lối tắt vào các việc MKT (SEO, Ads, nghiên cứu) gắn skill/agent sẵn.</p>
            <button type="button" class="jv-g-go" data-ggo="marketing">Mở Marketing</button>
          </div>
        </div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("brain")} Bộ não hàng ngày</h3>
        <div class="jv-g-twin">
          <div class="jv-g-card">
            <h4>${ic("folder-tree")} Tệp tin & Drive</h4>
            <p>Duyệt / sửa file trong brain. Kho Drive đồng bộ thư mục Google vào Second Brain khi đã cấu hình.</p>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px">
              <button type="button" class="jv-g-go" data-ggo="files">Tệp tin</button>
              <button type="button" class="jv-g-go" data-ggo="drive">Drive</button>
            </div>
          </div>
          <div class="jv-g-card">
            <h4>${ic("brain")} Tự học</h4>
            <p>Sau hội thoại, VMOS có thể rút ký ức / Wiki / đề xuất skill. Trang này để xem và hoàn tác nếu rút sai.</p>
            <button type="button" class="jv-g-go" data-ggo="learn" style="margin-top:10px">Mở Tự học</button>
          </div>
        </div>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("message-circle")} Chat hiệu quả hơn</h3>
        <ul>
          <li>Gõ <code>/</code> để gọi skill hoặc lệnh phiên (<code>/new</code>, <code>/stop</code>…).</li>
          <li>Đính file / ảnh khi cần VMOS đọc đúng nguồn.</li>
          <li>Nói rõ ràng: mục tiêu, ràng buộc, định dạng đầu ra mong muốn.</li>
          <li>Một brain = một «văn phòng» kiến thức - đừng lẫn dự án cá nhân vào brain công ty.</li>
        </ul>
        <button type="button" class="jv-g-go" data-ggo="chat" style="margin-top:10px">${ic("message-circle")} Vào Chat</button>
      </div>

      <div class="jv-g-sec">
        <h3>${ic("sliders-horizontal")} Hệ thống</h3>
        <div class="jv-g-map">
          <div class="m" data-ggo="usage"><div class="t">${ic("chart-column")} Mức dùng</div><div class="d">Token & chi phí theo ngày / nhà cung cấp.</div></div>
          <div class="m" data-ggo="settings"><div class="t">${ic("settings")} Cài đặt</div><div class="d">Giao diện, giọng nói, truy cập, đồng bộ template (manager).</div></div>
          <div class="m" data-ggo="account"><div class="t">${ic("circle-user")} Tài khoản</div><div class="d">Mật khẩu, phiên đăng nhập.</div></div>
          <div class="m" data-ggo="logs"><div class="t">${ic("scroll-text")} Nhật ký</div><div class="d">Khi lỗi - xem log để gửi cho admin.</div></div>
          <div class="m" data-ggo="terminal"><div class="t">${ic("terminal")} Terminal</div><div class="d">Dòng lệnh trên máy chạy VMOS (cẩn thận).</div></div>
          <div class="m" data-ggo="guide_what"><div class="t">${ic("sparkles")} Về tổng quan</div><div class="d">Quay lại «VMOS làm được gì».</div></div>
        </div>
      </div>
    </div>`;
  }

  const PAGES = {
    guide_what: pageWhat,
    guide_connect: pageConnect,
    guide_studio: pageStudio,
    guide_work: pageWork,
  };

  function render(el, id) {
    ensureCss();
    const fn = PAGES[id] || pageWhat;
    el.innerHTML = fn();
    bind(el);
  }

  window.JavisGuides = { render, ids: Object.keys(PAGES) };
})();
