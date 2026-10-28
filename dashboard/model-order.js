/* Thứ tự dùng + nhiều API key (port upstream 0.350–0.351, gói mỏng trên fork). */
(function () {
  "use strict";

  function esc(t) {
    return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function labels(provs) {
    var m = {};
    (provs || []).forEach(function (p) { m[p.id] = p.label || p.id; });
    return m;
  }

  function cardHtml(id, i, lab, chatInUse, mainId) {
    var badge = i === 0 ? "MAIN" : ("Dự phòng " + i);
    var using = chatInUse && chatInUse === id && id !== mainId;
    return '<div class="mord-card" draggable="true" data-id="' + esc(id) + '">'
      + '<span class="mord-grip" title="Kéo để đổi thứ tự">⋮⋮</span>'
      + '<div class="mord-main"><div class="mord-name">' + esc(lab[id] || id)
      + (using ? ' <span class="mord-using">ĐANG DÙNG</span>' : "") + "</div>"
      + '<div class="mord-badge">' + esc(badge) + "</div></div>"
      + '<div class="mord-acts">'
      + '<button type="button" class="gcard-btn ghost" data-act="up" title="Lên">↑</button>'
      + '<button type="button" class="gcard-btn ghost" data-act="down" title="Xuống">↓</button>'
      + "</div></div>";
  }

  function keysHtml(prov, accounts) {
    var rows = (accounts || []).map(function (a, i) {
      var rest = a.resting_until && a.resting_until * 1000 > Date.now()
        ? ' <span class="mord-rest">hết lượt đến ' + new Date(a.resting_until * 1000).toLocaleTimeString() + "</span>"
        : "";
      return '<div class="mord-key" data-aid="' + esc(a.id) + '">'
        + '<span class="mord-key-lab">' + esc(a.label || ("Key " + (i + 1))) + "</span>"
        + '<span class="mord-key-mask">' + esc(a.key || "") + rest + "</span>"
        + '<label class="mord-en"><input type="checkbox" data-en="' + esc(a.id) + '"'
        + (a.enabled !== false ? " checked" : "") + "> bật</label></div>";
    }).join("");
    return '<div class="mord-keys" data-prov="' + esc(prov) + '">'
      + '<div class="mord-keys-h">API key · ' + esc(prov) + "</div>"
      + (rows || '<div class="mord-empty">Chưa có key trong danh sách (dùng key cũ ở thẻ nhà cung cấp).</div>')
      + '<div class="mord-key-add">'
      + '<input class="js-input" data-new-lab placeholder="Tên key" value="Key mới">'
      + '<input class="js-input" data-new-key type="password" placeholder="sk-…">'
      + '<button type="button" class="gcard-btn" data-add-key>Thêm key</button></div></div>';
  }

  async function api(path, body) {
    var opt = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
    var r = await fetch(path, opt);
    try { return await r.json(); } catch (e) { return { ok: false, error: "bad json" }; }
  }

  async function mount(el) {
    if (!el) return;
    el.innerHTML = '<div class="mord-loading">Đang tải Thứ tự dùng…</div>';
    var d = await api("/models/routing");
    if (!d || !d.ok) {
      el.innerHTML = '<div class="lv-note">' + esc((d && d.error) || "Không tải được Thứ tự dùng") + "</div>";
      return;
    }
    var lab = labels(d.providers);
    var order = d.order || [];
    var mainId = d.order && d.order[0];
    el.innerHTML = '<section class="cview-section jx-pane mord">'
      + "<h3>Thứ tự dùng</h3>"
      + '<p class="conn-lead">Chat chạy thẻ trên cùng (MAIN). Hết lượt hoặc mọi key nghỉ thì nhảy Dự phòng 1, 2… '
      + "Kéo thẻ hoặc bấm mũi tên để đổi thứ tự. Nhà API có thể thêm nhiều key.</p>"
      + '<div class="mord-list">' + order.map(function (id, i) {
        return cardHtml(id, i, lab, d.chat_in_use, mainId);
      }).join("") + "</div>"
      + '<div class="mord-key-host"></div></section>';

    var list = el.querySelector(".mord-list");
    var keyHost = el.querySelector(".mord-key-host");

    function paintKeys() {
      var html = "";
      (d.providers || []).forEach(function (p) {
        if (p.kind !== "api" || !p.key_field || !p.configured) return;
        if (order.indexOf(p.id) < 0) return;
        html += keysHtml(p.id, (d.accounts && d.accounts[p.id]) || []);
      });
      keyHost.innerHTML = html || "";
      keyHost.querySelectorAll("[data-add-key]").forEach(function (btn) {
        btn.onclick = async function () {
          var box = btn.closest(".mord-keys");
          var prov = box.dataset.prov;
          var labEl = box.querySelector("[data-new-lab]");
          var keyEl = box.querySelector("[data-new-key]");
          var key = (keyEl.value || "").trim();
          if (!key) { keyEl.focus(); return; }
          var cur = ((d.accounts && d.accounts[prov]) || []).map(function (a) {
            return { id: a.id, label: a.label, enabled: a.enabled !== false, key: a.key };
          });
          cur.push({ label: (labEl.value || "Key").trim(), enabled: true, key: key });
          btn.disabled = true;
          var r = await api("/models/routing/accounts", { provider: prov, accounts: cur });
          btn.disabled = false;
          if (!r.ok) { alert(r.error || "Lỗi lưu key"); return; }
          mount(el);
        };
      });
      keyHost.querySelectorAll("[data-en]").forEach(function (cb) {
        cb.onchange = async function () {
          var box = cb.closest(".mord-keys");
          var prov = box.dataset.prov;
          var cur = ((d.accounts && d.accounts[prov]) || []).map(function (a) {
            return { id: a.id, label: a.label, enabled: a.id === cb.getAttribute("data-en") ? cb.checked : a.enabled !== false, key: a.key };
          });
          await api("/models/routing/accounts", { provider: prov, accounts: cur });
          mount(el);
        };
      });
    }
    paintKeys();

    async function saveOrder(ids) {
      var r = await api("/models/routing/order", { order: ids });
      if (!r.ok) { alert(r.error || "Không lưu được thứ tự"); return; }
      mount(el);
    }

    list.querySelectorAll(".mord-card").forEach(function (card) {
      card.querySelectorAll("[data-act]").forEach(function (b) {
        b.onclick = function () {
          var ids = order.slice();
          var i = ids.indexOf(card.dataset.id);
          if (i < 0) return;
          var j = b.dataset.act === "up" ? i - 1 : i + 1;
          if (j < 0 || j >= ids.length) return;
          var t = ids[i]; ids[i] = ids[j]; ids[j] = t;
          saveOrder(ids);
        };
      });
      card.addEventListener("dragstart", function (e) {
        e.dataTransfer.setData("text/plain", card.dataset.id);
        card.classList.add("dragging");
      });
      card.addEventListener("dragend", function () { card.classList.remove("dragging"); });
      card.addEventListener("dragover", function (e) { e.preventDefault(); });
      card.addEventListener("drop", function (e) {
        e.preventDefault();
        var from = e.dataTransfer.getData("text/plain");
        var to = card.dataset.id;
        if (!from || from === to) return;
        var ids = order.slice();
        var i = ids.indexOf(from), j = ids.indexOf(to);
        if (i < 0 || j < 0) return;
        ids.splice(i, 1);
        ids.splice(j, 0, from);
        saveOrder(ids);
      });
    });
  }

  if (typeof window !== "undefined") window.JavisModelOrder = { mount: mount };
})();
