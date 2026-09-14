/* Trang Khóa API: dán khóa dịch vụ (Atlas, Kling, Tavily, ElevenLabs...) và khóa tự thêm.
 * Javis nhớ trong settings (mã hoá) rồi bơm vào env cho skill. Không phải trang Models.
 *
 * File riêng: console.js đã dày. Test: node tests/js/test_tool_apis.js
 * Ghi chu: KHONG dung ky tu em dash. */
(function () {
  "use strict";

  function ic(ten, opt) {
    return (typeof window !== "undefined" && window.ic) ? window.ic(ten, opt) : "";
  }
  function t(k) {
    return (typeof window !== "undefined" && window.t) ? window.t(k) : k;
  }
  function esc(s) {
    return (s || "").toString()
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function lang() {
    return (typeof window !== "undefined" && window.JavisI18n && JavisI18n.lang())
      ? JavisI18n.lang() : "vi";
  }
  function nn(vi, en) {
    return lang() === "en" ? (en || vi || "") : (vi || en || "");
  }

  async function defPost(op, extra) {
    const fd = new FormData();
    fd.append("op", op);
    extra = extra || {};
    ["id", "env", "key"].forEach(function (k) {
      if (extra[k] != null) fd.append(k, extra[k]);
    });
    try {
      const r = await fetch("/tool-apis", { method: "POST", body: fd });
      let d = {};
      try { d = await r.json(); } catch (e) { d = { ok: false, error: "HTTP " + r.status }; }
      if (!r.ok && d && !d.error) d.error = "HTTP " + r.status;
      return d;
    } catch (e) {
      return { ok: false, error: String(e && e.message ? e.message : e) };
    }
  }

  function statusHtml(it) {
    if (it.set) {
      const duoi = it.suffix ? ("••••" + esc(it.suffix)) : t("tool_apis.set");
      return '<span class="ta-pill on">' + ic("check", { cls: "ic-ok" }) + " " +
        esc(t("tool_apis.set")) + (it.suffix ? " " + duoi : "") + "</span>";
    }
    if (it.from_env) {
      return '<span class="ta-pill env">' + esc(t("tool_apis.from_env")) + "</span>";
    }
    return '<span class="ta-pill off">' + esc(t("tool_apis.empty")) + "</span>";
  }

  function card(it, custom) {
    const kindUrl = it.kind === "url";
    const ph = kindUrl ? t("tool_apis.url_ph") : t("tool_apis.key_ph");
    const inputType = kindUrl ? "text" : "password";
    const where = it.where
      ? '<a class="ta-where" href="' + esc(it.where) + '" target="_blank" rel="noopener noreferrer">' +
        esc(t("tool_apis.get_key")) + "</a>"
      : "";
    const tieu = custom ? esc(it.env) : esc(nn(it.label, it.label_en));
    const mo = custom ? esc(t("tool_apis.custom_one")) : esc(nn(it.dung_de, it.dung_de_en));
    const envLine = '<div class="ta-env"><code>' + esc(it.env) + "</code></div>";
    return '<div class="prov-card ta-card" data-id="' + esc(it.id || "") + '" data-env="' + esc(it.env || "") + '"' +
      (custom ? ' data-custom="1"' : "") + ">" +
      '<div class="prov-head"><span class="prov-shield ' + (it.set || it.from_env ? "on" : "") + '">' +
      ic("key") + "</span>" +
      '<div class="prov-info"><div class="prov-name">' + tieu + "</div>" +
      '<div class="prov-status">' + statusHtml(it) + "</div></div></div>" +
      '<p class="ta-desc">' + mo + "</p>" + envLine + where +
      '<div class="ta-row">' +
      '<input class="js-input ta-key" type="' + inputType + '" autocomplete="off" placeholder="' + esc(ph) + '">' +
      '<button type="button" class="gcard-btn ta-save">' + esc(t("tool_apis.save")) + "</button>" +
      (it.set || custom
        ? '<button type="button" class="gcard-btn ghost ta-clear">' + esc(t("tool_apis.clear")) + "</button>"
        : "") +
      "</div>" +
      '<div class="gcard-meta ta-msg" hidden></div>' +
      "</div>";
  }

  function groupBlock(title, inner) {
    if (!inner) return "";
    return '<section class="ta-group"><h3 class="ta-h">' + esc(title) + "</h3>" +
      '<div class="prov-grid ta-grid">' + inner + "</div></section>";
  }

  function wire(el, data) {
    el.querySelectorAll(".ta-card").forEach(function (cardEl) {
      const save = cardEl.querySelector(".ta-save");
      const clr = cardEl.querySelector(".ta-clear");
      const inp = cardEl.querySelector(".ta-key");
      const msg = cardEl.querySelector(".ta-msg");
      function bao(ok, chu) {
        msg.hidden = !chu;
        msg.textContent = chu || "";
        msg.classList.toggle("ta-err", !ok);
      }
      if (save) {
        save.onclick = async function () {
          const val = (inp && inp.value || "").trim();
          if (!val) { bao(false, t("tool_apis.need_key")); return; }
          save.disabled = true;
          const custom = cardEl.getAttribute("data-custom") === "1";
          const d = custom
            ? await defPost("set_custom", { env: cardEl.getAttribute("data-env"), key: val })
            : await defPost("set", { id: cardEl.getAttribute("data-id"), key: val });
          save.disabled = false;
          if (!d || !d.ok) { bao(false, (d && d.error) || t("tool_apis.fail")); return; }
          if (inp) inp.value = "";
          renderInto(el, d);
        };
      }
      if (clr) {
        clr.onclick = async function () {
          clr.disabled = true;
          const custom = cardEl.getAttribute("data-custom") === "1";
          const d = custom
            ? await defPost("clear_custom", { env: cardEl.getAttribute("data-env") })
            : await defPost("clear", { id: cardEl.getAttribute("data-id") });
          clr.disabled = false;
          if (!d || !d.ok) { bao(false, (d && d.error) || t("tool_apis.fail")); return; }
          renderInto(el, d);
        };
      }
    });
    const addBtn = el.querySelector("#taAdd");
    if (addBtn) {
      addBtn.onclick = async function () {
        const envEl = el.querySelector("#taNewEnv");
        const keyEl = el.querySelector("#taNewKey");
        const msg = el.querySelector("#taAddMsg");
        const env = (envEl && envEl.value || "").trim();
        const key = (keyEl && keyEl.value || "").trim();
        function bao(ok, chu) {
          if (!msg) return;
          msg.hidden = !chu;
          msg.textContent = chu || "";
          msg.classList.toggle("ta-err", !ok);
        }
        if (!env || !key) { bao(false, t("tool_apis.need_both")); return; }
        addBtn.disabled = true;
        const d = await defPost("set_custom", { env: env, key: key });
        addBtn.disabled = false;
        if (!d || !d.ok) { bao(false, (d && d.error) || t("tool_apis.fail")); return; }
        renderInto(el, d);
      };
    }
  }

  function htmlFrom(data) {
    data = data || { groups: [], items: [], custom: [] };
    const byG = {};
    (data.items || []).forEach(function (it) {
      (byG[it.group] = byG[it.group] || []).push(it);
    });
    const gMeta = {};
    (data.groups || []).forEach(function (g) { gMeta[g.id] = g; });
    let body = "";
    const seen = {};
    (data.groups || []).forEach(function (g) {
      if (!g || g.id === "custom") return;
      seen[g.id] = true;
      const inner = (byG[g.id] || []).map(function (it) { return card(it, false); }).join("");
      body += groupBlock(nn(g.label, g.label_en), inner);
    });
    Object.keys(byG).forEach(function (gid) {
      if (gid === "custom" || seen[gid]) return;
      const g = gMeta[gid] || { id: gid, label: gid, label_en: gid };
      const inner = (byG[gid] || []).map(function (it) { return card(it, false); }).join("");
      body += groupBlock(nn(g.label, g.label_en), inner);
    });
    const customInner = (data.custom || []).map(function (it) { return card(it, true); }).join("");
    const gCust = gMeta.custom || { label: t("tool_apis.custom_title"), label_en: t("tool_apis.custom_title") };
    body += groupBlock(nn(gCust.label, gCust.label_en), customInner);
    body +=
      '<section class="ta-group ta-add">' +
      "<h3 class=\"ta-h\">" + esc(t("tool_apis.add_title")) + "</h3>" +
      '<p class="ta-desc">' + esc(t("tool_apis.custom_hint")) + "</p>" +
      '<div class="ta-row ta-add-row">' +
      '<input class="js-input" id="taNewEnv" autocomplete="off" placeholder="' + esc(t("tool_apis.env_ph")) + '">' +
      '<input class="js-input" id="taNewKey" type="password" autocomplete="off" placeholder="' + esc(t("tool_apis.key_ph")) + '">' +
      '<button type="button" class="gcard-btn" id="taAdd">' + esc(t("tool_apis.add")) + "</button>" +
      "</div>" +
      '<div class="gcard-meta ta-msg" id="taAddMsg" hidden></div>' +
      "</section>";
    return '<div class="ta-page">' +
      '<p class="jx-page-lead">' + esc(t("tool_apis.lead")) + "</p>" +
      '<p class="ta-note">' + esc(t("tool_apis.models_note")) + "</p>" +
      body + "</div>";
  }

  function renderInto(el, data) {
    el.innerHTML = htmlFrom(data);
    wire(el, data);
  }

  async function render(el) {
    if (!el) return;
    el.innerHTML = '<div class="cview-placeholder"><div class="ph-ico">' +
      ic("loader", { cls: "ic-xl ic-spin" }) + "</div><div>" + esc(t("common.loading")) + "</div></div>";
    let data = { groups: [], items: [], custom: [] };
    try {
      const r = await fetch("/tool-apis", { cache: "no-store" });
      data = await r.json();
    } catch (e) {
      el.innerHTML = '<div class="dim">' + esc(t("tool_apis.fail")) + "</div>";
      return;
    }
    renderInto(el, data);
  }

  const API = { render: render, htmlFrom: htmlFrom };
  if (typeof window !== "undefined") window.JavisToolApis = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})();
