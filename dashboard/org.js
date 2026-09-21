// Trang Tổ chức: tab Tổng hợp / Cài đặt / Tạo mới / Quản lý. Chỉ admin Javis gốc.
(function () {
  "use strict";

  const esc = (s) => (s || "").toString()
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

  const POOL = [
    ["openrouter", "OpenRouter"],
    ["openai", "OpenAI"],
    ["anthropic-api", "Anthropic API"],
    ["gemini", "Gemini API"],
    ["groq", "Groq"],
    ["deepseek", "DeepSeek"],
  ];

  let orgTab = "tong";
  let orgQ = "";
  let orgSt = "all";
  let orgApi = "all";
  let orgKind = "all";
  let orgFlash = "";

  async function api(path, opt) {
    const r = await fetch(path, Object.assign({ cache: "no-store" }, opt || {}));
    let d = {};
    try { d = await r.json(); } catch (e) { d = {}; }
    if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
    return d;
  }

  function stLabel(s) {
    if (s === "running") return "Đang chạy";
    if (s === "stopped") return "Đã tắt";
    if (s === "missing") return "Chưa có máy";
    if (s === "paused") return "Tạm dừng";
    if (s === "unknown") return "Không rõ";
    return s || "?";
  }

  function genPw() {
    const a = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ";
    const d = "23456789";
    let s = "";
    for (let i = 0; i < 10; i++) s += a[Math.floor(Math.random() * a.length)];
    s += d[Math.floor(Math.random() * d.length)];
    s += d[Math.floor(Math.random() * d.length)];
    return s;
  }

  function fmtGB(bytes) {
    const n = Number(bytes || 0);
    if (n <= 0) return "0 GB";
    return (n / (1024 * 1024 * 1024)).toFixed(2) + " GB";
  }

  function barHtml(used, cap, label) {
    if (!cap) {
      return `<div class="org-meter"><span class="dim">${esc(label)}: ${esc(String(used))} (không trần)</span></div>`;
    }
    const pct = Math.max(0, Math.min(100, Math.round(100 * Number(used || 0) / Number(cap))));
    const cls = pct >= 95 ? "hot" : (pct >= 80 ? "warn" : "");
    return `<div class="org-meter">
      <div class="org-meter-lbl">${esc(label)}: <b>${esc(String(used))}</b> / ${esc(String(cap))} (${pct}%)</div>
      <div class="org-bar ${cls}"><i style="width:${pct}%"></i></div>
    </div>`;
  }

  function haystack(t) {
    return [t.name, t.slug, t.login_user, t.domain, "javis-" + t.slug, "vmos-" + t.slug]
      .join(" ").toLowerCase();
  }

  function showTab(root, id) {
    orgTab = id;
    root.querySelectorAll("[data-org-tab]").forEach((b) => {
      const on = b.getAttribute("data-org-tab") === id;
      b.classList.toggle("on", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    root.querySelectorAll("[data-org-pane]").forEach((p) => {
      p.hidden = p.getAttribute("data-org-pane") !== id;
    });
  }

  function applyFilter(root) {
    const q = String(root.querySelector("#orgSearch")?.value || "").trim().toLowerCase();
    const st = String(root.querySelector("#orgSt")?.value || "all");
    const apiF = String(root.querySelector("#orgApi")?.value || "all");
    const kind = String(root.querySelector("#orgKind")?.value || "all");
    orgQ = q; orgSt = st; orgApi = apiF; orgKind = kind;
    let n = 0;
    root.querySelectorAll(".org-card").forEach((card) => {
      const hay = card.getAttribute("data-hay") || "";
      const status = card.getAttribute("data-status") || "";
      const shared = card.getAttribute("data-shared") || "";
      const prot = card.getAttribute("data-prot") === "1";
      const okQ = !q || hay.includes(q);
      const okSt = st === "all"
        || (st === "stopped" ? (status === "stopped" || status === "missing") : status === st);
      const okApi = apiF === "all" || shared === apiF;
      const okKind = kind === "all" || (kind === "root" ? prot : !prot);
      const show = okQ && okSt && okApi && okKind;
      card.hidden = !show;
      if (show) n++;
    });
    const count = root.querySelector("#orgCount");
    if (count) count.textContent = n + " người";
    const empty = root.querySelector("#orgFilterEmpty");
    if (empty) empty.hidden = n > 0;
  }

  function bindTabs(root) {
    root.querySelectorAll("[data-org-tab]").forEach((b) => {
      b.addEventListener("click", () => showTab(root, b.getAttribute("data-org-tab")));
    });
    root.querySelectorAll("[data-org-goto]").forEach((b) => {
      b.addEventListener("click", () => {
        const tab = b.getAttribute("data-org-goto");
        if (b.hasAttribute("data-org-reset")) {
          orgQ = ""; orgSt = "all"; orgApi = "all"; orgKind = "all";
        }
        if (b.hasAttribute("data-org-q")) orgQ = b.getAttribute("data-org-q") || "";
        if (b.hasAttribute("data-org-st")) orgSt = b.getAttribute("data-org-st") || "all";
        const inp = root.querySelector("#orgSearch");
        if (inp) inp.value = orgQ;
        const stEl = root.querySelector("#orgSt");
        if (stEl) stEl.value = orgSt;
        const apiEl = root.querySelector("#orgApi");
        if (apiEl) apiEl.value = orgApi;
        const kindEl = root.querySelector("#orgKind");
        if (kindEl) kindEl.value = orgKind;
        showTab(root, tab);
        applyFilter(root);
      });
    });
  }

  function bindFilter(root) {
    ["#orgSearch", "#orgSt", "#orgApi", "#orgKind"].forEach((sel) => {
      const n = root.querySelector(sel);
      if (!n) return;
      n.addEventListener(sel === "#orgSearch" ? "input" : "change", () => applyFilter(root));
    });
    applyFilter(root);
  }

  async function render(el) {
    el.innerHTML = '<p class="dim">Đang tải sổ tổ chức…</p>';
    let d;
    try {
      d = await api("/org/tenants");
    } catch (e) {
      el.innerHTML = '<p class="dim">Trang này chỉ có trên Javis gốc, dành cho admin đăng nhập tại '
        + '<code>javis.vietmycollege.com</code>. Javis con không có mục Tổ chức.</p>';
      return;
    }
    const tenants = d.tenants || [];
    const prefix = d.host_prefix || "javis";
    const suffix = d.domain_suffix || "vietmycollege.com";
    const hostOf = (t) => t.domain || (prefix + "-" + t.slug + "." + suffix);
    const people = tenants.filter((t) => !t.protected);
    const running = tenants.filter((t) => t.status === "running").length;
    const stopped = tenants.filter((t) => t.status === "stopped" || t.status === "missing").length;
    const sharedN = people.filter((t) => t.shared_api).length;
    const prov = d.providers || {};
    const keysOn = POOL.filter(([id]) => (prov[id] || {}).set).length;
    const flash = orgFlash;
    orgFlash = "";

    const poolRows = POOL.map(([id, label]) => {
      const rec = prov[id] || {};
      const st = rec.set
        ? `<span class="org-pill on">Đã lưu ${esc(rec.mask || "••••")}</span>`
        : `<span class="org-pill">Chưa dán</span>`;
      return `<div class="org-key">
        <div class="org-key-h"><b>${esc(label)}</b> ${st}</div>
        <input name="pool_${esc(id)}" type="password" autocomplete="off"
          placeholder="${rec.set ? "Dán khóa mới để thay" : "Dán khóa API"}">
      </div>`;
    }).join("");

    const poolRead = POOL.map(([id, label]) => {
      const rec = prov[id] || {};
      return `<li><b>${esc(label)}</b> ${rec.set
        ? `<span class="org-pill on">Đã lưu ${esc(rec.mask || "••••")}</span>`
        : `<span class="org-pill">Chưa dán</span>`}</li>`;
    }).join("");

    const cards = tenants.map((t) => {
      const href = "https://" + hostOf(t);
      const prot = t.protected;
      const stopBtn = prot ? "" : `<button class="btn" data-org-stop="${esc(t.slug)}">Tắt máy</button>`;
      const pwBtn = prot ? "" : `<button class="btn" data-org-pw-open="${esc(t.slug)}">Đặt lại mật khẩu</button>`;
      const editBtn = `<button class="btn" data-org-edit-open="${esc(t.slug)}">Sửa hạn mức</button>`;
      const apiBtn = prot ? "" : `<button class="btn" data-org-api="${esc(t.slug)}" data-on="${t.shared_api ? "1" : "0"}">${t.shared_api ? "Tắt API chung" : "Bật API chung"}</button>`;
      return `<article class="org-card" data-slug="${esc(t.slug)}"
          data-hay="${esc(haystack(t))}" data-status="${esc(t.status || "")}"
          data-shared="${t.shared_api ? "on" : "off"}" data-prot="${prot ? "1" : "0"}">
        <header>
          <div>
            <b>${esc(t.name || t.slug)}</b>${prot ? ' <span class="org-pill">não gốc - không quản từ đây</span>' : ""}
            <div class="dim">máy <code>javis-${esc(t.slug)}</code> · đăng nhập <code>${esc(t.login_user || "admin")}</code></div>
          </div>
          <span class="org-st ${esc(t.status || "")}">${esc(stLabel(t.status))}</span>
        </header>
        <p><a href="${esc(href)}" target="_blank" rel="noopener">${esc(t.domain || href)}</a></p>
        <div class="org-usage" data-org-usage="${esc(t.slug)}"
             data-quota="${esc(String(t.quota_gb || 0))}"
             data-tok="${esc(String(t.token_quota || 0))}"
             data-used="${esc(String(t.tokens_used || 0))}">
          ${barHtml(t.quota_gb ? "?" : 0, t.quota_gb, "Ổ")}
          ${barHtml(t.tokens_used || 0, t.token_quota || 0, "Token tháng")}
          <div class="dim">API chung: <b>${t.shared_api ? "Có" : "Không"}</b></div>
        </div>
        <div class="org-acts">
          <button class="btn primary" data-org-start="${esc(t.slug)}">Bật máy</button>
          ${stopBtn}
          ${editBtn}
          ${apiBtn}
          ${pwBtn}
        </div>
        <form class="org-inline" data-org-edit="${esc(t.slug)}" hidden>
          <label>Ổ GB (0 = không trần)<input name="quota_gb" type="number" min="0" max="20" value="${esc(String(t.quota_gb || 0))}"></label>
          <label>Token/tháng (0 = không trần)<input name="token_quota" type="number" min="0" step="1000" value="${esc(String(t.token_quota || 0))}"></label>
          <label>Hiện tên<input name="name" value="${esc(t.name || "")}"></label>
          <button class="btn primary" type="submit">Lưu hạn mức</button>
        </form>
        <form class="org-inline" data-org-pw="${esc(t.slug)}" hidden>
          <label>Mật khẩu mới<input name="password" type="password" minlength="10" autocomplete="new-password" required></label>
          <label>Nhập lại<input name="password2" type="password" minlength="10" autocomplete="new-password" required></label>
          <button class="btn" type="button" data-org-gen="${esc(t.slug)}">Tạo mật khẩu</button>
          <button class="btn primary" type="submit">Đặt mật khẩu</button>
        </form>
      </article>`;
    }).join("");

    const snapRows = tenants.map((t) => {
      const href = "https://" + hostOf(t);
      return `<tr>
        <td><button type="button" class="org-link" data-org-goto="quan" data-org-q="${esc(t.slug)}">${esc(t.name || t.slug)}</button></td>
        <td><span class="org-st ${esc(t.status || "")}">${esc(stLabel(t.status))}</span></td>
        <td>${t.protected ? "Não gốc" : (t.shared_api ? "API chung" : "Riêng")}</td>
        <td><a href="${esc(href)}" target="_blank" rel="noopener">${esc(t.domain || ("javis-" + t.slug))}</a></td>
      </tr>`;
    }).join("");

    el.innerHTML = `
      <div class="org-page">
        ${d.docker === false ? '<p class="org-warn">Chưa gọi được Docker trên máy chủ. Tạo người mới sẽ lỗi cho đến khi deploy gắn DOCKER_GID.</p>' : ""}
        <nav class="jx-tabs org-tabs" role="tablist" aria-label="Tổ chức">
          <button type="button" class="jx-tab${orgTab === "tong" ? " on" : ""}" role="tab"
            data-org-tab="tong" aria-selected="${orgTab === "tong"}">Tổng hợp</button>
          <button type="button" class="jx-tab${orgTab === "cai" ? " on" : ""}" role="tab"
            data-org-tab="cai" aria-selected="${orgTab === "cai"}">Cài đặt chung
            <span class="jx-tab-n">${keysOn}/${POOL.length}</span></button>
          <button type="button" class="jx-tab${orgTab === "tao" ? " on" : ""}" role="tab"
            data-org-tab="tao" aria-selected="${orgTab === "tao"}">Tạo mới</button>
          <button type="button" class="jx-tab${orgTab === "quan" ? " on" : ""}" role="tab"
            data-org-tab="quan" aria-selected="${orgTab === "quan"}">Quản lý
            <span class="jx-tab-n">${tenants.length}</span></button>
        </nav>
        <p class="dim" id="orgMsg">${esc(flash)}</p>

        <section class="org-pane" data-org-pane="tong" ${orgTab === "tong" ? "" : "hidden"}>
          <p class="org-lead">Chỉ admin Javis gốc thấy trang này. Mỗi người một não riêng, tự gắn API trên máy họ. Gốc không đọc được chat hay khóa của họ.</p>
          <div class="org-stats">
            <button type="button" data-org-goto="quan" data-org-reset="1"><b>${tenants.length}</b><span>Người / máy</span></button>
            <button type="button" data-org-goto="quan" data-org-reset="1" data-org-st="running"><b>${running}</b><span>Đang chạy</span></button>
            <button type="button" data-org-goto="quan" data-org-reset="1" data-org-st="stopped"><b>${stopped}</b><span>Tắt / chưa có</span></button>
            <button type="button" data-org-goto="cai"><b>${keysOn}/${POOL.length}</b><span>Khóa API đã dán</span></button>
          </div>
          <div class="org-snap">
            <div>
              <h3>API</h3>
              <ul class="org-read">${poolRead}</ul>
              <p>Mặc định mỗi người tự dán khóa / đăng nhập trên trang Models của máy họ.
              Kho trường: ${sharedN}/${people.length || 0} người đang bật (không bắt buộc).</p>
              <button type="button" class="btn" data-org-goto="cai">Kho API trường (tùy chọn)</button>
            </div>
            <div>
              <h3>Sổ nhanh</h3>
              ${tenants.length
                ? `<div class="org-table-wrap"><table class="org-table"><thead><tr><th>Người</th><th>Máy</th><th>API</th><th>Link</th></tr></thead><tbody>${snapRows}</tbody></table></div>`
                : '<p class="dim">Chưa có bản nào ngoài não gốc.</p>'}
              <button type="button" class="btn primary" data-org-goto="tao">Tạo người mới</button>
            </div>
          </div>
        </section>

        <section class="org-pane" data-org-pane="cai" ${orgTab === "cai" ? "" : "hidden"}>
          <h3>Kho API trường (tùy chọn)</h3>
          <p>Mặc định <b>không dùng</b>: mỗi người tự gắn OpenRouter, Claude, Grok… trên máy họ, não và khóa ở lại volume của họ.
          Chỉ dán khóa vào đây nếu sau này muốn một người dùng chung kho trường (bật từng người trên Quản lý).
          Khóa ở lại Javis gốc, không chép xuống máy con. Ô trống khi lưu thì giữ khóa cũ.</p>
          <form id="orgPool" class="org-keys">${poolRows}
            <button class="btn primary" type="submit">Lưu khóa API</button>
          </form>
          <p class="dim" id="orgPoolMsg"></p>
        </section>

        <section class="org-pane" data-org-pane="tao" ${orgTab === "tao" ? "" : "hidden"}>
          <h3>Tạo người mới</h3>
          <p>Mỗi người một Javis tại <code>${esc(prefix)}-[tên].${esc(suffix)}</code>, <b>não riêng</b>.
          Họ tự vào trang Models trên máy đó để dán API hoặc đăng nhập Claude / Grok của chính họ.
          Mật khẩu tối thiểu 10 ký tự, có chữ và số. Gốc không lưu mật khẩu dạng đọc được, không đọc được não họ.</p>
          <form id="orgCreate" class="org-form">
            <label>Tên máy (slug)<input name="slug" required placeholder="Ví dụ: lan" pattern="[a-z0-9]+(-[a-z0-9]+)*" maxlength="32"></label>
            <label>Hiện tên<input name="name" placeholder="Nguyễn Văn A"></label>
            <label>Tên đăng nhập<input name="login_user" required placeholder="Ví dụ: lan" maxlength="32"></label>
            <label>Mật khẩu<input name="password" type="password" required minlength="10" autocomplete="new-password"></label>
            <label>Nhập lại MK<input name="password2" type="password" required minlength="10" autocomplete="new-password"></label>
            <label>Trần ổ (GB)<input name="quota_gb" type="number" min="1" max="20" value="2"></label>
            <label>Trần token/tháng<input name="token_quota" type="number" min="0" step="1000" value="0" title="Chỉ khi bật API chung. 0 = không trần"></label>
            <label class="org-check"><input name="shared_api" type="checkbox"> Dùng kho API trường (để trống = tự gắn API riêng)</label>
            <button class="btn" type="button" id="orgGenPw">Tạo mật khẩu mạnh</button>
            <button class="btn primary" type="submit">Tạo Javis</button>
          </form>
        </section>

        <section class="org-pane" data-org-pane="quan" ${orgTab === "quan" ? "" : "hidden"}>
          <h3>Quản lý người</h3>
          <p class="dim">Bật/tắt máy, hạn mức ổ, đặt lại mật khẩu. Não và API của họ ở máy họ. «Bật API chung» chỉ khi muốn một người dùng kho trường.</p>
          <div class="org-toolbar">
            <input id="orgSearch" class="org-search" type="search" placeholder="Tìm tên, máy, đăng nhập…" value="${esc(orgQ)}">
            <select id="orgSt" class="org-filter" aria-label="Lọc máy">
              <option value="all"${orgSt === "all" ? " selected" : ""}>Mọi trạng thái</option>
              <option value="running"${orgSt === "running" ? " selected" : ""}>Đang chạy</option>
              <option value="stopped"${orgSt === "stopped" ? " selected" : ""}>Tắt / chưa có</option>
            </select>
            <select id="orgApi" class="org-filter" aria-label="Lọc API">
              <option value="all"${orgApi === "all" ? " selected" : ""}>Mọi API</option>
              <option value="on"${orgApi === "on" ? " selected" : ""}>Có API chung</option>
              <option value="off"${orgApi === "off" ? " selected" : ""}>Không dùng API chung</option>
            </select>
            <select id="orgKind" class="org-filter" aria-label="Loại máy">
              <option value="all"${orgKind === "all" ? " selected" : ""}>Mọi máy</option>
              <option value="people"${orgKind === "people" ? " selected" : ""}>Javis người</option>
              <option value="root"${orgKind === "root" ? " selected" : ""}>Não gốc</option>
            </select>
            <span class="dim" id="orgCount"></span>
          </div>
          <div class="org-grid">${cards || '<p class="dim">Chưa có bản nào ngoài não gốc.</p>'}</div>
          <p class="dim" id="orgFilterEmpty" hidden>Không khớp bộ lọc. Xóa ô tìm hoặc chọn lại lọc.</p>
        </section>
      </div>
      <style>
        .org-tabs.jx-tabs{max-width:760px;width:100%;flex-wrap:wrap}
        .org-pane[hidden]{display:none!important}
        .org-lead{margin:0 0 16px}
        .org-warn{padding:10px 12px;border-radius:10px;border:1px solid #e03131;color:#e03131;margin:0 0 16px}
        .org-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin:0 0 22px}
        .org-stats button{display:block;width:100%;text-align:left;padding:12px 14px;border-radius:12px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit;cursor:pointer;font:inherit}
        .org-stats button:hover{border-color:var(--accent,var(--border))}
        .org-stats b{display:block;font-size:22px;line-height:1.2}
        .org-stats span{font-size:12px;opacity:.75}
        .org-snap{display:grid;grid-template-columns:minmax(220px,280px) 1fr;gap:22px;align-items:start}
        .org-read{list-style:none;padding:0;margin:0 0 12px;display:grid;gap:8px}
        .org-read li{display:flex;justify-content:space-between;gap:8px;align-items:center}
        .org-table-wrap{overflow:auto;margin:0 0 12px}
        .org-table{width:100%;border-collapse:collapse;font-size:13px}
        .org-table th,.org-table td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--glass-brd,var(--border));vertical-align:middle}
        .org-link{background:none;border:0;padding:0;color:var(--accent,inherit);cursor:pointer;font:inherit;font-weight:600;text-align:left}
        .org-toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 14px}
        .org-search{flex:1;min-width:180px;padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-filter{padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-form,.org-inline,.org-keys{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:12px 0 16px}
        .org-form label,.org-inline label,.org-key{display:flex;flex-direction:column;gap:4px;font-size:13px}
        .org-form input,.org-inline input,.org-key input{min-width:140px;padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-check{flex-direction:row !important;align-items:center;gap:8px;min-height:38px}
        .org-check input{min-width:auto}
        .org-keys{gap:14px}
        .org-key{min-width:200px;flex:1}
        .org-key-h{display:flex;gap:8px;align-items:center;justify-content:space-between}
        .org-pill{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid var(--glass-brd,var(--border));opacity:.85}
        .org-pill.on{border-color:#2f9e44;color:#2f9e44}
        .org-grid{display:grid;gap:14px}
        .org-card{padding:14px 16px;border-radius:14px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2))}
        .org-card header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
        .org-st{font-size:12px;padding:4px 8px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));white-space:nowrap}
        .org-st.running{border-color:#2f9e44;color:#2f9e44}
        .org-st.stopped,.org-st.missing{opacity:.7}
        .org-acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
        .org-meter{margin:8px 0}
        .org-meter-lbl{font-size:13px;margin-bottom:4px}
        .org-bar{height:8px;border-radius:99px;background:rgba(127,127,127,.2);overflow:hidden}
        .org-bar i{display:block;height:100%;background:#2f9e44}
        .org-bar.warn i{background:#f59f00}
        .org-bar.hot i{background:#e03131}
        .org-page h3{margin:8px 0 8px}
        #orgMsg{min-height:1.2em;margin:0 0 12px}
        @media (max-width:720px){.org-snap{grid-template-columns:1fr}}
      </style>`;

    const msg = el.querySelector("#orgMsg");
    const poolMsg = el.querySelector("#orgPoolMsg");
    const form = el.querySelector("#orgCreate");
    const poolForm = el.querySelector("#orgPool");
    const gen = el.querySelector("#orgGenPw");

    bindTabs(el);
    bindFilter(el);
    showTab(el, orgTab);

    el.querySelectorAll("[data-org-usage]").forEach(async (box) => {
      const slug = box.getAttribute("data-org-usage");
      const cap = Number(box.getAttribute("data-quota") || 0);
      const tokCap = Number(box.getAttribute("data-tok") || 0);
      let tokUsed = Number(box.getAttribute("data-used") || 0);
      let disk = 0;
      try {
        const u = await api("/org/tenants/" + encodeURIComponent(slug) + "/usage");
        disk = u.disk_bytes || 0;
        tokUsed = u.tokens_used || tokUsed;
      } catch (e) {}
      const diskLabel = cap ? (fmtGB(disk) + " / " + cap + " GB") : (fmtGB(disk) + " (không trần)");
      const pct = cap ? Math.max(0, Math.min(100, Math.round(100 * disk / (cap * 1024 * 1024 * 1024)))) : 0;
      const cls = pct >= 95 ? "hot" : (pct >= 80 ? "warn" : "");
      box.innerHTML =
        `<div class="org-meter"><div class="org-meter-lbl">Ổ: <b>${esc(diskLabel)}</b></div>
           <div class="org-bar ${cls}"><i style="width:${cap ? pct : 0}%"></i></div></div>`
        + barHtml(tokUsed, tokCap, "Token tháng");
    });

    if (gen) gen.addEventListener("click", () => {
      const pw = genPw();
      form.password.value = pw;
      form.password2.value = pw;
      msg.textContent = "Đã điền mật khẩu mạnh. Gửi cho người đó một lần, Javis không lưu lại.";
    });
    if (poolForm) poolForm.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const body = {};
      POOL.forEach(([id]) => {
        const v = String(poolForm["pool_" + id].value || "").trim();
        if (v) body[id] = v;
      });
      poolMsg.textContent = "Đang lưu…";
      try {
        await api("/org/settings/pool", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        orgFlash = "Đã lưu khóa. Ô trống giữ khóa cũ.";
        orgTab = "cai";
        poolForm.reset();
        render(el);
      } catch (e) {
        poolMsg.textContent = e.message || "Không lưu được.";
      }
    });
    if (form) form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      if (String(fd.get("password") || "") !== String(fd.get("password2") || "")) {
        msg.textContent = "Hai mật khẩu không khớp.";
        return;
      }
      msg.textContent = "Đang tạo máy. Chờ khoảng 1 phút…";
      try {
        await api("/org/tenants", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            slug: String(fd.get("slug") || ""),
            name: String(fd.get("name") || ""),
            login_user: String(fd.get("login_user") || ""),
            password: String(fd.get("password") || ""),
            quota_gb: Number(fd.get("quota_gb") || 2),
            token_quota: Number(fd.get("token_quota") || 0),
            shared_api: form.shared_api.checked,
          }),
        });
        orgQ = String(fd.get("slug") || "");
        orgTab = "quan";
        orgFlash = "Đã tạo. Mở link sau khoảng 1 phút (Caddy xin HTTPS). Gửi tên đăng nhập và mật khẩu cho người đó.";
        render(el);
      } catch (e) {
        msg.textContent = e.message || "Không tạo được.";
      }
    });
    el.querySelectorAll("[data-org-start]").forEach((b) => {
      b.addEventListener("click", async () => {
        msg.textContent = "Đang bật…";
        try {
          await api("/org/tenants/" + encodeURIComponent(b.getAttribute("data-org-start")) + "/start", { method: "POST" });
          orgTab = "quan";
          render(el);
        } catch (e) { msg.textContent = e.message; }
      });
    });
    el.querySelectorAll("[data-org-stop]").forEach((b) => {
      b.addEventListener("click", async () => {
        if (!confirm("Tắt Javis này? Não và file không xóa.")) return;
        try {
          await api("/org/tenants/" + encodeURIComponent(b.getAttribute("data-org-stop")) + "/stop", { method: "POST" });
          orgTab = "quan";
          render(el);
        } catch (e) { msg.textContent = e.message; }
      });
    });
    el.querySelectorAll("[data-org-api]").forEach((b) => {
      b.addEventListener("click", async () => {
        const slug = b.getAttribute("data-org-api");
        const on = b.getAttribute("data-on") !== "1";
        try {
          await api("/org/tenants/" + encodeURIComponent(slug), {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ shared_api: on }),
          });
          orgTab = "quan";
          render(el);
        } catch (e) { msg.textContent = e.message; }
      });
    });
    el.querySelectorAll("[data-org-edit-open]").forEach((b) => {
      b.addEventListener("click", () => {
        const f = el.querySelector('[data-org-edit="' + b.getAttribute("data-org-edit-open") + '"]');
        if (f) f.hidden = !f.hidden;
      });
    });
    el.querySelectorAll("[data-org-pw-open]").forEach((b) => {
      b.addEventListener("click", () => {
        const f = el.querySelector('[data-org-pw="' + b.getAttribute("data-org-pw-open") + '"]');
        if (f) f.hidden = !f.hidden;
      });
    });
    el.querySelectorAll("[data-org-gen]").forEach((b) => {
      b.addEventListener("click", () => {
        const f = el.querySelector('[data-org-pw="' + b.getAttribute("data-org-gen") + '"]');
        if (!f) return;
        const pw = genPw();
        f.password.value = pw;
        f.password2.value = pw;
        msg.textContent = "Đã điền mật khẩu mạnh. Gửi cho người đó một lần.";
      });
    });
    el.querySelectorAll("form[data-org-edit]").forEach((f) => {
      f.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const slug = f.getAttribute("data-org-edit");
        try {
          await api("/org/tenants/" + encodeURIComponent(slug), {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              quota_gb: Number(f.quota_gb.value || 0),
              token_quota: Number(f.token_quota.value || 0),
              name: String(f.name.value || ""),
            }),
          });
          orgTab = "quan";
          render(el);
        } catch (e) { msg.textContent = e.message; }
      });
    });
    el.querySelectorAll("form[data-org-pw]").forEach((f) => {
      f.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        if (f.password.value !== f.password2.value) {
          msg.textContent = "Hai mật khẩu không khớp.";
          return;
        }
        const slug = f.getAttribute("data-org-pw");
        try {
          await api("/org/tenants/" + encodeURIComponent(slug) + "/password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: f.password.value }),
          });
          msg.textContent = "Đã đặt mật khẩu mới. Javis gốc không lưu mật khẩu. Gửi cho người đó rồi họ tự đổi.";
          f.hidden = true;
          f.reset();
        } catch (e) { msg.textContent = e.message; }
      });
    });
  }

  window.JavisOrg = { render };
})();
