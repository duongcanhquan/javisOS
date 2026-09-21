// Trang Tổ chức (Javis gốc): danh sách Javis con, tạo mới, bật/tắt.
(function () {
  "use strict";

  const esc = (s) => (s || "").toString()
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");

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

  async function render(el) {
    el.innerHTML = '<p class="dim">Đang tải sổ tổ chức…</p>';
    let d;
    try {
      d = await api("/org/tenants");
    } catch (e) {
      el.innerHTML = '<p class="dim">Trang này chỉ có trên Javis gốc (javis.vietmycollege.com).</p>';
      return;
    }
    const rows = (d.tenants || []).map((t) => {
      const href = "https://" + (t.domain || ("javis-" + t.slug + ".vietmycollege.com"));
      const quota = t.quota_gb ? (t.quota_gb + " GB") : "không trần";
      const prot = t.protected ? " (não gốc, không xóa)" : "";
      const stopBtn = t.protected
        ? ""
        : `<button class="btn" data-org-stop="${esc(t.slug)}">Tắt</button>`;
      const startBtn = `<button class="btn primary" data-org-start="${esc(t.slug)}">Bật</button>`;
      return `<tr>
        <td><b>${esc(t.name || t.slug)}</b>${esc(prot)}<div class="dim">javis-${esc(t.slug)}</div></td>
        <td><a href="${esc(href)}" target="_blank" rel="noopener">${esc(t.domain || "")}</a></td>
        <td>${esc(stLabel(t.status))}</td>
        <td>${esc(quota)}</td>
        <td>${startBtn} ${stopBtn}</td>
      </tr>`;
    }).join("");
    el.innerHTML = `
      <div class="org-page">
        <p>Mỗi người một Javis tại <code>javis-[tên].vietmycollege.com</code>.
        Đăng nhập mặc định <b>admin / admin</b>, rồi đổi mật khẩu trong Tài khoản.
        DNS wildcard <code>*</code> đã có thì không cần thêm bản ghi.</p>
        <form id="orgCreate" class="org-form">
          <label>Tên (slug)<input name="slug" required placeholder="vd lan" pattern="[a-z0-9]+(-[a-z0-9]+)*" maxlength="32"></label>
          <label>Hiện tên<input name="name" placeholder="Nguyễn Văn A"></label>
          <label>Ổ (GB)<input name="quota_gb" type="number" min="1" max="20" value="2"></label>
          <button class="btn primary" type="submit">Tạo Javis</button>
        </form>
        <p class="dim" id="orgMsg"></p>
        <table class="org-table">
          <thead><tr><th>Người</th><th>Link</th><th>Máy</th><th>Ổ</th><th></th></tr></thead>
          <tbody>${rows || '<tr><td colspan="5" class="dim">Chưa có bản nào.</td></tr>'}</tbody>
        </table>
      </div>
      <style>
        .org-form{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:16px 0}
        .org-form label{display:flex;flex-direction:column;gap:4px;font-size:13px}
        .org-form input{min-width:140px;padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd);background:var(--panel);color:inherit}
        .org-table{width:100%;border-collapse:collapse}
        .org-table th,.org-table td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--glass-brd);vertical-align:top}
        .org-table .btn{margin:0 4px 4px 0}
      </style>`;
    const msg = el.querySelector("#orgMsg");
    const form = el.querySelector("#orgCreate");
    if (form) form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const fd = new FormData(form);
      msg.textContent = "Đang tạo…";
      try {
        await api("/org/tenants", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            slug: String(fd.get("slug") || ""),
            name: String(fd.get("name") || ""),
            quota_gb: Number(fd.get("quota_gb") || 2),
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
  }

  window.JavisOrg = { render };
})();
