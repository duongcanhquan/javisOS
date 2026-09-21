// Trang Tổ chức: tạo người (tên+mật khẩu), hạn mức ổ/token, API chung.
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

  async function render(el) {
    el.innerHTML = '<p class="dim">Đang tải sổ tổ chức…</p>';
    let d;
    try {
      d = await api("/org/tenants");
    } catch (e) {
      el.innerHTML = '<p class="dim">Trang này chỉ có trên Javis gốc (javis.vietmycollege.com).</p>';
      return;
    }
    const prov = (d.providers || {});
    const poolRows = POOL.map(([id, label]) => {
      const rec = prov[id] || {};
      const hint = rec.set ? ("Đã lưu " + (rec.mask || "••••")) : "Chưa dán";
      return `<label>${esc(label)}
        <input name="pool_${esc(id)}" type="password" autocomplete="off" placeholder="${esc(hint)}">
      </label>`;
    }).join("");
    const rows = (d.tenants || []).map((t) => {
      const href = "https://" + (t.domain || ("javis-" + t.slug + ".vietmycollege.com"));
      const quota = t.quota_gb ? (t.quota_gb + " GB") : "không trần";
      const tok = t.token_quota
        ? ((t.tokens_used || 0) + " / " + t.token_quota)
        : ((t.tokens_used || 0) + " (không trần)");
      const apiOn = t.shared_api ? "Có" : "Không";
      const prot = t.protected ? " (não gốc)" : "";
      const stopBtn = t.protected
        ? ""
        : `<button class="btn" data-org-stop="${esc(t.slug)}">Tắt</button>`;
      const pwBtn = t.protected
        ? ""
        : `<button class="btn" data-org-pw="${esc(t.slug)}">Đặt lại MK</button>`;
      return `<tr>
        <td><b>${esc(t.name || t.slug)}</b>${esc(prot)}
          <div class="dim">javis-${esc(t.slug)} · đăng nhập <code>${esc(t.login_user || "admin")}</code></div></td>
        <td><a href="${esc(href)}" target="_blank" rel="noopener">${esc(t.domain || "")}</a></td>
        <td>${esc(stLabel(t.status))}</td>
        <td>${esc(quota)}</td>
        <td>${esc(apiOn)}</td>
        <td>${esc(String(tok))}</td>
        <td>
          <button class="btn primary" data-org-start="${esc(t.slug)}">Bật</button>
          ${stopBtn}
          <button class="btn" data-org-edit="${esc(t.slug)}">Hạn mức</button>
          ${pwBtn}
        </td>
      </tr>`;
    }).join("");
    el.innerHTML = `
      <div class="org-page">
        <h3>API chung của Javis gốc</h3>
        <p>Dán khóa API trường vào đây. Khóa ở lại Javis gốc, không chép xuống máy từng người.
        Bật «Dùng API chung» khi tạo hoặc sửa người thì họ gọi qua cổng này, hết hạn mức thì bị chặn.</p>
        <form id="orgPool" class="org-form">${poolRows}
          <button class="btn primary" type="submit">Lưu khóa</button>
        </form>
        <p class="dim" id="orgPoolMsg"></p>

        <h3>Tạo người mới</h3>
        <p>Mỗi người một Javis tại <code>javis-[tên].vietmycollege.com</code>.
        Mật khẩu tối thiểu 10 ký tự, có chữ và số. Họ tự đổi sau trong Tài khoản.
        Javis gốc không lưu mật khẩu.</p>
        <form id="orgCreate" class="org-form">
          <label>Tên máy (slug)<input name="slug" required placeholder="vd lan" pattern="[a-z0-9]+(-[a-z0-9]+)*" maxlength="32"></label>
          <label>Hiện tên<input name="name" placeholder="Nguyễn Văn A"></label>
          <label>Tên đăng nhập<input name="login_user" required placeholder="lan" maxlength="32"></label>
          <label>Mật khẩu<input name="password" type="password" required minlength="10" autocomplete="new-password"></label>
          <label>Nhập lại MK<input name="password2" type="password" required minlength="10" autocomplete="new-password"></label>
          <label>Ổ (GB)<input name="quota_gb" type="number" min="1" max="20" value="2"></label>
          <label>Trần token/tháng<input name="token_quota" type="number" min="0" step="1000" value="0" title="0 = không trần"></label>
          <label class="org-check"><input name="shared_api" type="checkbox"> Dùng API chung</label>
          <button class="btn" type="button" id="orgGenPw">Tạo mật khẩu</button>
          <button class="btn primary" type="submit">Tạo Javis</button>
        </form>
        <p class="dim" id="orgMsg"></p>
        <table class="org-table">
          <thead><tr><th>Người</th><th>Link</th><th>Máy</th><th>Ổ</th><th>API chung</th><th>Token</th><th></th></tr></thead>
          <tbody>${rows || '<tr><td colspan="7" class="dim">Chưa có bản nào.</td></tr>'}</tbody>
        </table>
      </div>
      <style>
        .org-form{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:12px 0 20px}
        .org-form label{display:flex;flex-direction:column;gap:4px;font-size:13px}
        .org-form input{min-width:140px;padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-check{flex-direction:row !important;align-items:center;gap:8px;min-height:38px}
        .org-check input{min-width:auto}
        .org-table{width:100%;border-collapse:collapse}
        .org-table th,.org-table td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--glass-brd,var(--border));vertical-align:top}
        .org-table .btn{margin:0 4px 4px 0}
        .org-page h3{margin:20px 0 8px}
      </style>`;
    const msg = el.querySelector("#orgMsg");
    const poolMsg = el.querySelector("#orgPoolMsg");
    const form = el.querySelector("#orgCreate");
    const poolForm = el.querySelector("#orgPool");
    const gen = el.querySelector("#orgGenPw");
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
        poolMsg.textContent = "Đã lưu khóa. Ô trống giữ khóa cũ.";
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
      msg.textContent = "Đang tạo…";
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
        msg.textContent = "Đã tạo. Mở link sau khoảng 1 phút (Caddy xin HTTPS).";
        render(el);
      } catch (e) {
        msg.textContent = e.message || "Không tạo được.";
      }
    });
    el.querySelectorAll("[data-org-start]").forEach((b) => {
      b.addEventListener("click", async () => {
        try {
          await api("/org/tenants/" + encodeURIComponent(b.getAttribute("data-org-start")) + "/start", { method: "POST" });
          render(el);
        } catch (e) { msg.textContent = e.message; }
      });
    });
    el.querySelectorAll("[data-org-stop]").forEach((b) => {
      b.addEventListener("click", async () => {
        if (!confirm("Tắt Javis này? Não không xóa.")) return;
        try {
          await api("/org/tenants/" + encodeURIComponent(b.getAttribute("data-org-stop")) + "/stop", { method: "POST" });
          render(el);
        } catch (e) { msg.textContent = e.message; }
      });
    });
    el.querySelectorAll("[data-org-edit]").forEach((b) => {
      b.addEventListener("click", async () => {
        const slug = b.getAttribute("data-org-edit");
        const t = (d.tenants || []).find((x) => x.slug === slug) || {};
        const gb = prompt("Trần ổ (GB, 0 = không trần)", String(t.quota_gb || 0));
        if (gb == null) return;
        const tok = prompt("Trần token/tháng (0 = không trần)", String(t.token_quota || 0));
        if (tok == null) return;
        const apiOn = confirm("Dùng API chung của Javis gốc? OK = có, Hủy = không.");
        try {
          await api("/org/tenants/" + encodeURIComponent(slug), {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              quota_gb: Number(gb),
              token_quota: Number(tok),
              shared_api: apiOn,
            }),
          });
          render(el);
        } catch (e) { msg.textContent = e.message; }
      });
    });
    el.querySelectorAll("[data-org-pw]").forEach((b) => {
      b.addEventListener("click", async () => {
        const slug = b.getAttribute("data-org-pw");
        const pw = prompt("Mật khẩu mới (tối thiểu 10 ký tự, có chữ và số). Người dùng đổi được sau.");
        if (pw == null) return;
        try {
          await api("/org/tenants/" + encodeURIComponent(slug) + "/password", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ password: pw }),
          });
          msg.textContent = "Đã đặt mật khẩu mới. Javis gốc không lưu mật khẩu.";
        } catch (e) { msg.textContent = e.message; }
      });
    });
  }

  window.JavisOrg = { render };
})();
