// Trang Tổ chức: tab Tổng hợp / Cài đặt / Tạo mới / Quản lý. Chỉ admin VMOS gốc.
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

  const MODES = [
    ["byo", "Tự gắn API (riêng)"],
    ["school", "Chỉ kho trường"],
    ["both", "Kho trường + API riêng"],
    ["blocked", "Chặn gọi model"],
  ];

  function modeLabel(m) {
    const hit = MODES.find(([id]) => id === m);
    return hit ? hit[1] : (m || "byo");
  }

  function providerChecks(name, selected) {
    const sel = Array.isArray(selected) ? selected : [];
    return POOL.map(([id, label]) => {
      const on = sel.length === 0 ? false : sel.includes(id);
      return `<label class="org-check org-prov"><input type="checkbox" name="${esc(name)}" value="${esc(id)}"${on ? " checked" : ""}> ${esc(label)}</label>`;
    }).join("");
  }

  function modeSelect(name, cur) {
    const v = cur || "byo";
    return `<select name="${esc(name)}">${MODES.map(([id, label]) =>
      `<option value="${esc(id)}"${id === v ? " selected" : ""}>${esc(label)}</option>`
    ).join("")}</select>`;
  }

  let orgTab = "tong";
  let orgQ = "";
  let orgSt = "all";
  let orgApi = "all";
  let orgKind = "all";
  let orgFlash = "";
  let ramPollTimer = null;
    const RAM_POLL_MS = 12000;

  function stopRamPoll() {
    if (ramPollTimer) {
      clearInterval(ramPollTimer);
      ramPollTimer = null;
    }
  }

  function ramAgo(idleSec, idle) {
    if (Number.isFinite(idleSec) && idleSec >= 0 && idleSec < 1e9) {
      if (idleSec < 90) return "vừa xong";
      if (idleSec < 3600) return Math.floor(idleSec / 60) + " phút trước";
      return Math.floor(idleSec / 3600) + " giờ trước";
    }
    if (idle) return "không thấy tín hiệu";
    return "";
  }

  function liveMachineRowsHtml(machines, ramPer) {
    const list = Array.isArray(machines) ? machines : [];
    return list.map((m) => {
      const mb = Number(m.mem_mb || 0);
      const lim = Number(m.limit_mb || ramPer || 1024);
      const pct = lim ? Math.min(100, Math.round(100 * mb / lim)) : 0;
      const ago = ramAgo(Number(m.idle_sec), m.idle);
      const tag = m.idle
        ? '<span class="org-pill">nghỉ · Docker vẫn bật</span>'
        : '<span class="org-pill on">có tín hiệu gần đây</span>';
      return `<tr data-org-ram-slug="${esc(m.slug || "")}">
        <td><code>${esc(m.slug || "")}</code></td>
        <td data-org-ram="row-mem">${esc(String(mb))} / ${esc(String(lim))} MB (${pct}%)</td>
        <td data-org-ram="row-sig">${tag}${ago ? `<div class="dim" style="font-size:12px;margin-top:2px">${esc(ago)}</div>` : ""}</td>
      </tr>`;
    }).join("");
  }

  function patchRamLive(el, d) {
    if (!el || !d) return;
    const ramPer = Number(d.ram_mb || d.ram_limit_mb || 1024);
    const peopleUsed = Number(d.people_used_mb || 0);
    const peopleIdleMb = Number(d.people_idle_mb || 0);
    const activeN = Number(d.people_active_n || 0);
    const idleN = Number(d.people_idle_n || 0);
    const slotsByRam = Number(d.fit_more_est || 0);
    const runP = Number(d.running != null ? d.running : (d.machines || []).length);
    const ramHostMb = Number(d.host_ram_mb || 0);
    const ramHostGb = ramHostMb ? Math.round(ramHostMb / 1024 * 10) / 10 : 0;
    const avg = runP > 0 ? Math.round(peopleUsed / runP) : 0;

    el.querySelectorAll("[data-org-ram='people-used']").forEach((n) => {
      n.textContent = peopleUsed ? (peopleUsed + " MB") : "…";
    });
    el.querySelectorAll("[data-org-ram='people-used-sub']").forEach((n) => {
      n.textContent = activeN + " có tín hiệu · " + idleN + " nghỉ vẫn tốn " + peopleIdleMb + " MB"
        + (slotsByRam ? (" · ước mở thêm ~" + slotsByRam + " nếu nhả máy nghỉ") : "");
    });
    el.querySelectorAll("[data-org-ram='per-ceil']").forEach((n) => {
      n.textContent = "~" + ramPer + " MB RAM";
    });
    el.querySelectorAll("[data-org-ram='per-ceil-kpi']").forEach((n) => {
      n.textContent = ramPer + " MB";
    });
    el.querySelectorAll("[data-org-ram='per-avg']").forEach((n) => {
      n.textContent = runP
        ? ("đang dùng TB ~" + avg + " MB/máy · trần Docker " + ramPer + " MB (máy cũ có thể còn 768 đến khi tạo lại)")
        : ("trần Docker " + ramPer + " MB · máy mới; máy cũ có thể còn 768 đến khi tạo lại");
    });
    el.querySelectorAll("[data-org-ram='host-meter-lbl']").forEach((n) => {
      n.innerHTML = "RAM đang dùng (Docker): <b>" + esc(String(peopleUsed)) + " MB</b>"
        + (ramHostGb ? (" / " + esc(String(ramHostGb)) + " GB máy") : "")
        + " · " + esc(String(runP)) + " máy mở";
    });
    const pctHost = ramHostMb
      ? Math.max(0, Math.min(100, Math.round(100 * peopleUsed / ramHostMb)))
      : 0;
    el.querySelectorAll("[data-org-ram='host-meter-bar']").forEach((n) => {
      n.style.width = pctHost + "%";
    });
    const rows = liveMachineRowsHtml(d.machines, ramPer);
    el.querySelectorAll("[data-org-ram='machines-body']").forEach((tb) => {
      if (rows) tb.innerHTML = rows;
      else tb.innerHTML = '<tr><td colspan="3" class="dim">Chưa có máy người đang mở.</td></tr>';
    });
    el.querySelectorAll("[data-org-ram='live-empty']").forEach((p) => {
      p.hidden = !!rows;
    });
    el.querySelectorAll("[data-org-ram='live-table']").forEach((w) => {
      w.hidden = !rows;
    });
  }

  function startRamPoll(el) {
    stopRamPoll();
    if (!el) return;
    const tick = async () => {
      if (!el.isConnected || !el.querySelector(".org-page")) {
        stopRamPoll();
        return;
      }
      if (document.hidden) return;
      try {
        const d = await api("/org/ram_live");
        patchRamLive(el, d);
      } catch (e) { /* im lặng: lần sau thử lại */ }
    };
    ramPollTimer = setInterval(tick, RAM_POLL_MS);
  }

  async function api(path, opt) {
    const r = await fetch(path, Object.assign({
      cache: "no-store",
      credentials: "same-origin",
    }, opt || {}));
    let d = {};
    try { d = await r.json(); } catch (e) { d = {}; }
    if (!r.ok) throw new Error(d.error || ("HTTP " + r.status));
    return d;
  }

  function tipOn(btn, text) {
    const card = btn && btn.closest ? btn.closest(".org-card") : null;
    const tip = card && card.querySelector("[data-org-tip]");
    if (tip) tip.textContent = text || "";
  }

  function busyBtn(btn, on) {
    if (!btn) return;
    btn.disabled = !!on;
    btn.setAttribute("aria-busy", on ? "true" : "false");
  }

  function stLabel(s) {
    if (s === "running") return "Đang chạy";
    if (s === "stopped") return "Đã tắt";
    if (s === "missing") return "Chưa có máy";
    if (s === "paused") return "Tạm dừng";
    if (s === "deleted") return "Chờ xóa";
    if (s === "unknown") return "Không rõ";
    return s || "?";
  }

  function fmtAgo(ts) {
    const n = Number(ts || 0);
    if (!n) return "";
    const sec = Math.max(0, Math.floor(Date.now() / 1000 - n));
    if (sec < 60) return "vừa xong";
    if (sec < 3600) return Math.floor(sec / 60) + " phút trước";
    if (sec < 86400) return Math.floor(sec / 3600) + " giờ trước";
    return Math.floor(sec / 86400) + " ngày trước";
  }

  function fmtLeft(purgeAfter) {
    const end = Number(purgeAfter || 0);
    if (!end) return "72 giờ";
    const left = Math.max(0, end - Math.floor(Date.now() / 1000));
    const h = Math.max(1, Math.ceil(left / 3600));
    if (h >= 48) return Math.ceil(h / 24) + " ngày";
    return h + " giờ";
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

  function fmtRamGb(mb) {
    const n = Number(mb || 0);
    if (n <= 0) return "";
    if (n >= 1024) return (Math.round(n / 102.4) / 10) + " GB";
    return n + " MB";
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
    return [t.name, t.slug, t.login_user, t.domain, "javis-" + t.slug, "vmos-" + t.slug,
            t.paused ? "tam dung tam dung tai khoan" : "",
            t.deleted_at ? "cho xoa soft delete khoi phuc" : ""]
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
        || (st === "paused" ? status === "paused"
          : st === "stopped" ? (status === "stopped" || status === "missing")
          : status === st);
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
    const soft = !!el.querySelector(".org-page");
    if (!soft) {
      el.innerHTML = '<p class="dim">Đang tải sổ tổ chức…</p>';
    } else {
      el.classList.add("org-busy");
      const flashEl = el.querySelector("[data-org-flash]");
      if (flashEl) flashEl.textContent = "Đang cập nhật sổ…";
    }
    let d;
    try {
      d = await api("/org/tenants");
    } catch (e) {
      el.classList.remove("org-busy");
      el.innerHTML = '<p class="dim">Trang này chỉ có trên VMOS gốc, dành cho admin đăng nhập tại '
        + '<code>javis.vietmycollege.com</code>. VMOS con không có mục Tổ chức.</p>';
      return;
    }
    el.classList.remove("org-busy");
    const tenants = d.tenants || [];
    const prefix = d.host_prefix || "javis";
    const suffix = d.domain_suffix || "vietmycollege.com";
    const hostOf = (t) => t.domain || (prefix + "-" + t.slug + "." + suffix);
    const people = tenants.filter((t) => !t.protected);
    const running = tenants.filter((t) => t.status === "running").length;
    const stopped = tenants.filter((t) => t.status === "stopped" || t.status === "missing").length;
    const coord = d.coord || {};
    const maxHand = Number(coord.max_running || 6);
    const maxR = Number(coord.effective_max || maxHand);
    const runP = Number(coord.running != null ? coord.running : people.filter((t) => t.status === "running").length);
    const ramPer = Number(coord.ram_mb || 1024);
    const ramEst = Number(coord.ram_est_mb != null ? coord.ram_est_mb : runP * ramPer);
    const ramHost = coord.host_ram_mb ? Math.round(Number(coord.host_ram_mb) / 1024 * 10) / 10 : 0;
    const ramAvail = coord.host_avail_mb ? Math.round(Number(coord.host_avail_mb) / 1024 * 10) / 10 : 0;
    const waitN = Number(coord.waiting || 0);
    const suggestN = Number(coord.suggest || maxR || 0);
    const slotsLeft = Number(coord.slots_left != null ? coord.slots_left : Math.max(0, maxR - runP));
    const reserveMb = Number(coord.reserve_mb || 2800);
    const diskTotB = Number(coord.host_disk_total_bytes || 0);
    const diskFreeB = Number(coord.host_disk_free_bytes || 0);
    const diskUsedB = diskTotB > 0 ? Math.max(0, diskTotB - diskFreeB) : 0;
    const cpuN = Number(coord.host_cpus || 0);
    const quotaSum = people.reduce((s, t) => s + Number(t.quota_gb || 0), 0);
    const sharedN = people.filter((t) => t.shared_api).length;
    const prov = d.providers || {};
    const keysOn = POOL.filter(([id]) => (prov[id] || {}).set).length;
    const flash = orgFlash;
    orgFlash = "";

    const vpsRamLine = ramHost
      ? (`${ramHost} GB tổng · ${ramAvail} GB còn`)
      : "chưa đọc được";
    const vpsDiskLine = diskTotB
      ? (`${fmtGB(diskTotB)} tổng · ${fmtGB(diskFreeB)} trống`)
      : "chưa đọc được";
    const ramLive = (coord && coord.ram_live) || {};
    const liveMachines = Array.isArray(ramLive.machines) ? ramLive.machines : [];
    const budgetMb = Number(coord.budget_people_mb || 0);
    const formula = String(coord.formula || "");
    const peopleUsed = Number((coord.people_used_mb != null ? coord.people_used_mb : ramLive.people_used_mb) || 0);
    const peopleIdleMb = Number((coord.people_idle_mb != null ? coord.people_idle_mb : ramLive.people_idle_mb) || 0);
    const activeN = Number((coord.people_active_n != null ? coord.people_active_n : ramLive.people_active_n) || 0);
    const idleN = Number((coord.people_idle_n != null ? coord.people_idle_n : ramLive.people_idle_n) || 0);
    const slotsByRam = Number((coord.slots_by_ram != null ? coord.slots_by_ram : ramLive.fit_more_est) || 0);
    const avgUsed = runP > 0 ? Math.round(peopleUsed / runP) : 0;
    const liveRows = liveMachineRowsHtml(liveMachines, ramPer);
    const hostUsedPct = (ramHost && peopleUsed)
      ? Math.max(0, Math.min(100, Math.round(100 * peopleUsed / (ramHost * 1024))))
      : 0;
    const ramCalc = `
      <div class="org-sec org-ram-calc">
        <div class="org-sec-h"><div><h3>Tính RAM thật</h3>
          <p class="dim org-sec-sub">Cột RAM = Docker stats máy <b>còn bật</b> (kể cả không chat). Máy nghỉ từ 15 phút thì tự nhả cache file, app vẫn chạy. <b>Tắt máy</b> mới trả hết RAM.
            Cập nhật mỗi ~4 giây. Nhãn tín hiệu = mở trang / chat / API gần đây - không phải «đang chat». Healthcheck và poll nền không tính.
            Máy đã tạo trước khi nâng trần có thể vẫn 768 MB đến khi tắt/bật tạo lại.</p></div></div>
        <div class="org-kpi">
          <div class="org-kpi-i"><span class="org-kpi-l">Ngân sách máy người</span>
            <strong class="org-kpi-v">${budgetMb ? (esc(String(budgetMb)) + " MB") : "?"}</strong>
            <span class="org-kpi-s">host ${esc(String(ramHost || "?"))} GB - chừa ${esc(String(reserveMb))} MB - giữ ${esc(String(Number(coord.keep_free_mb || 400)))} MB</span></div>
          <div class="org-kpi-i"><span class="org-kpi-l">Mỗi máy (trần)</span>
            <strong class="org-kpi-v" data-org-ram="per-ceil-kpi">${esc(String(ramPer))} MB</strong>
            <span class="org-kpi-s">gợi ý tối đa ${esc(String(suggestN))} chỗ (trần tay ${esc(String(maxHand))} → hiệu lực ${esc(String(maxR))})</span></div>
          <div class="org-kpi-i"><span class="org-kpi-l">Đang đo trên VPS</span>
            <strong class="org-kpi-v" data-org-ram="people-used">${peopleUsed ? (esc(String(peopleUsed)) + " MB") : "…"}</strong>
            <span class="org-kpi-s" data-org-ram="people-used-sub">${esc(String(activeN))} có tín hiệu · ${esc(String(idleN))} nghỉ vẫn tốn ${esc(String(peopleIdleMb))} MB
              ${slotsByRam ? (" · ước mở thêm ~" + slotsByRam + " nếu nhả máy nghỉ") : ""}</span></div>
        </div>
        ${formula ? `<p class="dim org-sec-note">${esc(formula)}</p>` : ""}
        <div class="org-table-wrap" data-org-ram="live-table"${liveRows ? "" : " hidden"}>
          <table class="org-table"><thead><tr><th>Máy</th><th>RAM Docker (máy bật)</th><th>Tín hiệu người</th></tr></thead>
          <tbody data-org-ram="machines-body">${liveRows || ""}</tbody></table></div>
        <p class="dim" data-org-ram="live-empty"${liveRows ? " hidden" : ""}>Chưa đo được máy người đang mở (hoặc chưa có máy chạy).</p>
      </div>`;
    const vpsMeters = `
      ${diskTotB ? `<div class="org-meter"><div class="org-meter-lbl">Ổ máy chủ: <b>${esc(fmtGB(diskUsedB))}</b> / ${esc(fmtGB(diskTotB))}</div>
        <div class="org-bar ${diskTotB && diskFreeB / diskTotB < 0.1 ? "hot" : (diskTotB && diskFreeB / diskTotB < 0.2 ? "warn" : "")}"><i style="width:${diskTotB ? Math.max(0, Math.min(100, Math.round(100 * diskUsedB / diskTotB))) : 0}%"></i></div></div>` : ""}
      ${ramHost ? `<div class="org-meter" data-org-ram="host-meter"><div class="org-meter-lbl" data-org-ram="host-meter-lbl">RAM đang dùng (Docker): <b>${esc(String(peopleUsed))}</b> MB / ${esc(String(ramHost))} GB máy · ${esc(String(runP))} máy mở</div>
        <div class="org-bar"><i data-org-ram="host-meter-bar" style="width:${hostUsedPct}%"></i></div>
        <p class="dim org-sec-note" style="margin:6px 0 0">Trần lý thuyết nếu đầy: ${esc(String(ramEst))} MB (${esc(String(runP))}×${esc(String(ramPer))}). Thanh trên là <b>đang dùng thật</b>.</p></div>` : ""}`;
    const vpsKpis = `
      <div class="org-kpi">
        <div class="org-kpi-i"><span class="org-kpi-l">RAM</span><strong class="org-kpi-v">${esc(vpsRamLine)}</strong></div>
        <div class="org-kpi-i"><span class="org-kpi-l">Ổ đĩa</span><strong class="org-kpi-v">${esc(vpsDiskLine)}</strong></div>
        <div class="org-kpi-i"><span class="org-kpi-l">CPU</span><strong class="org-kpi-v">${cpuN ? (cpuN + " lõi") : "chưa rõ"}</strong></div>
        <div class="org-kpi-i"><span class="org-kpi-l">Người trong sổ</span><strong class="org-kpi-v">${esc(String(people.length))} tài khoản</strong>
          <span class="org-kpi-s">đã tạo · tắt / tạm dừng vẫn còn · không bị trần chỗ xóa</span></div>
        <div class="org-kpi-i"><span class="org-kpi-l">Máy đang mở (Docker)</span><strong class="org-kpi-v">${esc(String(runP))}/${esc(String(maxR))}</strong>
          <span class="org-kpi-s">cùng lúc · còn ${esc(String(slotsLeft))} · gợi ý RAM ${esc(String(suggestN))} · trần tay ${esc(String(maxHand))}</span></div>
        <div class="org-kpi-i"><span class="org-kpi-l">Mỗi máy (trần Docker)</span><strong class="org-kpi-v" data-org-ram="per-ceil">~${esc(String(ramPer))} MB RAM</strong>
          <span class="org-kpi-s" data-org-ram="per-avg">${runP
            ? ("đang dùng TB ~" + avgUsed + " MB/máy · chừa ~" + (fmtRamGb(reserveMb) || (reserveMb + " MB")) + " gốc + Quan")
            : ("chừa ~" + (fmtRamGb(reserveMb) || (reserveMb + " MB")) + " gốc + Quan")}</span></div>
        <div class="org-kpi-i"><span class="org-kpi-l">Trần ổ đã cấp</span><strong class="org-kpi-v">${esc(String(quotaSum))} GB · ${esc(String(people.length))} người</strong>
          ${diskFreeB ? `<span class="org-kpi-s">ổ còn ${esc(fmtGB(diskFreeB))}</span>` : ""}</div>
      </div>
      <div class="org-meters">${vpsMeters}</div>`;
    const vpsCard = `<div class="org-sec org-vps">
      <div class="org-sec-h"><div><h3>Máy chủ VPS</h3>
        <p class="dim org-sec-sub">Số liệu máy đang chạy VMOS gốc - dùng để phân bổ chỗ người.</p></div></div>
      ${vpsKpis}</div>`;
    const vpsCardTong = `<div class="org-sec org-vps">
      <div class="org-sec-h"><div><h3>Máy chủ VPS</h3>
        <p class="dim org-sec-sub">Số liệu máy đang chạy VMOS gốc - dùng để phân bổ chỗ người.</p></div>
        <button type="button" class="btn" data-org-goto="cai">Chỉnh trần chỗ</button></div>
      ${vpsKpis}</div>`;

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
      const deleted = !!t.deleted_at;
      const paused = !!t.paused && !deleted;
      const st = deleted ? "deleted" : (paused ? "paused" : (t.status || ""));
      const isRun = st === "running";
      const stopBtn = (prot || paused || deleted || !isRun)
        ? ""
        : `<button type="button" class="org-pwr off" data-org-stop="${esc(t.slug)}" title="Tắt máy (não không xóa)">Tắt máy</button>`;
      const pauseBtn = prot || paused || deleted
        ? ""
        : `<button type="button" class="btn org-btn-ghost" data-org-pause="${esc(t.slug)}">Tạm dừng</button>`;
      const startBtn = deleted || (isRun && !paused)
        ? ""
        : `<button type="button" class="org-pwr on" data-org-start="${esc(t.slug)}" title="${paused ? "Mở khóa và bật máy" : "Bật máy"}">${paused ? "Chạy lại" : "Bật máy"}</button>`;
      const restoreBtn = deleted ? `<button type="button" class="org-pwr on" data-org-restore="${esc(t.slug)}">Khôi phục</button>` : "";
      const pwBtn = prot || deleted ? "" : `<button type="button" class="btn org-btn-ghost" data-org-pw-open="${esc(t.slug)}">Đổi MK</button>`;
      const delBtn = prot ? "" : `<button type="button" class="btn org-btn-danger" data-org-del-open="${esc(t.slug)}">${deleted ? "Xóa ngay" : "Xóa"}</button>`;
      const mode = t.brain_mode || (t.shared_api ? "both" : "byo");
      const provs = Array.isArray(t.providers) ? t.providers : [];
      const ago = fmtAgo(t.last_active);
      const dig = (t.image_digest || "").trim();
      const diskKnown = Number(t.disk_checked_at || 0) > 0 || Number(t.disk_bytes || 0) > 0;
      const diskBar = diskKnown
        ? (() => {
            const disk = Number(t.disk_bytes || 0);
            const cap = Number(t.quota_gb || 0);
            const diskLabel = cap ? (fmtGB(disk) + " / " + cap + " GB") : (fmtGB(disk) + " (không trần)");
            const pct = cap ? Math.max(0, Math.min(100, Math.round(100 * disk / (cap * 1024 * 1024 * 1024)))) : 0;
            const cls = pct >= 95 ? "hot" : (pct >= 80 ? "warn" : "");
            return `<div class="org-meter"><div class="org-meter-lbl">Ổ: <b>${esc(diskLabel)}</b></div>
              <div class="org-bar ${cls}"><i style="width:${cap ? pct : 0}%"></i></div></div>`;
          })()
        : barHtml(t.quota_gb ? "?" : 0, t.quota_gb, "Ổ");
      return `<article class="org-card" data-slug="${esc(t.slug)}"
          data-hay="${esc(haystack(t))}" data-status="${esc(st)}"
          data-shared="${t.shared_api ? "on" : "off"}" data-prot="${prot ? "1" : "0"}"
          data-image-digest="${esc(dig)}" title="${esc(dig ? ("image_digest " + dig) : "")}">
        <header>
          <div>
            <b>${esc(t.name || t.slug)}</b>${prot ? ' <span class="org-pill">bản cũ</span>' : ""}${paused ? ' <span class="org-pill">tạm dừng</span>' : ""}${deleted ? ' <span class="org-pill hot">chờ xóa</span>' : ""}
            <div class="dim"><code>javis-${esc(t.slug)}</code> · <code>${esc(t.login_user || "admin")}</code>${ago ? (" · hoạt động " + esc(ago)) : ""}</div>
            ${prot ? '<div class="dim">Không tắt/xóa bản này từ đây.</div>' : ""}
            ${paused ? '<div class="dim">Tài khoản khóa - bấm Chạy lại.</div>' : ""}
            ${deleted ? `<div class="dim">Não còn ~<b>${esc(fmtLeft(t.purge_after))}</b>.</div>` : ""}
          </div>
        </header>
        <p class="org-card-link"><a href="${esc(href)}" target="_blank" rel="noopener">${esc(t.domain || href)}</a></p>
        <div class="org-usage" data-org-usage="${esc(t.slug)}"
             data-quota="${esc(String(t.quota_gb || 0))}"
             data-tok="${esc(String(t.token_quota || 0))}"
             data-used="${esc(String(t.tokens_used || 0))}"
             data-disk="${esc(String(t.disk_bytes || 0))}"
             data-disk-checked="${esc(String(t.disk_checked_at || 0))}">
          ${diskBar}
          ${barHtml(t.tokens_used || 0, t.token_quota || 0, "Token tháng")}
          <div class="dim">Chế độ: <b>${esc(modeLabel(mode))}</b>${provs.length ? (" · " + esc(provs.join(", "))) : ""}</div>
        </div>
        <div class="org-pwr-row">
          ${startBtn}
          ${stopBtn}
          ${restoreBtn}
          <span class="org-st ${esc(st)}">${esc(stLabel(st))}</span>
        </div>
        <div class="org-acts">
          ${pauseBtn}
          ${pwBtn}
          ${delBtn}
        </div>
        <p class="org-tip dim" data-org-tip aria-live="polite"></p>
        ${deleted ? "" : `<details class="org-more"><summary>Chỉnh cấu hình</summary>
        <form class="org-inline org-edit-form org-edit-grid" data-org-edit="${esc(t.slug)}">
          ${prot ? "" : `<label>Chế độ model${modeSelect("brain_mode", mode)}</label>
          <div class="org-prov-wrap org-span-all"><span class="dim">Provider kho trường (trống = mọi khóa đã dán)</span>${providerChecks("prov_" + t.slug, provs)}</div>`}
          <label>Hiện tên<input name="name" value="${esc(t.name || "")}"></label>
          ${prot ? "" : `<label>Tên đăng nhập<input name="login_user" value="${esc(t.login_user || "")}" maxlength="32"></label>`}
          <label>Ổ GB (0 = không trần)<input name="quota_gb" type="number" min="0" max="20" value="${esc(String(t.quota_gb || 0))}"></label>
          <label>Token/tháng (0 = không trần)<input name="token_quota" type="number" min="0" step="1000" value="${esc(String(t.token_quota || 0))}"></label>
          <button class="btn primary org-save" type="submit">Lưu thay đổi</button>
        </form></details>`}
        <form class="org-inline org-del-form" data-org-del="${esc(t.slug)}" ${deleted ? "" : "hidden"}>
          ${deleted
            ? `<p>Xóa <b>ngay</b> máy <code>${esc(t.slug)}</code>: não mất hết, không lấy lại. Hoặc đợi hết hạn tự xóa.</p>`
            : `<p>Đánh dấu xóa máy <code>${esc(t.slug)}</code>. Não giữ <b>72 giờ</b> rồi mới xóa hẳn. Có thể Khôi phục trong lúc đó.</p>`}
          <label>Gõ <code>${esc(t.slug)}</code> để xác nhận<input name="confirm" required autocomplete="off" placeholder="Ví dụ: ${esc(t.slug)}"></label>
          <button class="btn org-del" type="submit">${deleted ? "Xóa vĩnh viễn ngay" : "Xóa (giữ 72 giờ)"}</button>
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
      const st = t.deleted_at ? "deleted" : (t.paused ? "paused" : (t.status || ""));
      const mode = t.brain_mode || (t.shared_api ? "both" : "byo");
      const modeTxt = t.protected ? "Riêng (bản cũ)" : modeLabel(mode);
      return `<tr>
        <td><button type="button" class="org-link" data-org-goto="quan" data-org-q="${esc(t.slug)}">${esc(t.name || t.slug)}</button></td>
        <td><span class="org-st ${esc(st)}">${esc(stLabel(st))}</span></td>
        <td>${esc(modeTxt)}</td>
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
        <p class="dim" id="orgMsg" data-org-flash>${esc(flash)}</p>

        <section class="org-pane org-pane-tong" data-org-pane="tong" ${orgTab === "tong" ? "" : "hidden"}>
          <p class="org-lead">Chỉ admin VMOS gốc thấy trang này. Mỗi người một não riêng, tự gắn API trên máy họ. Gốc không đọc được chat hay khóa của họ.</p>
          <div class="org-stats" role="group" aria-label="Chỉ số nhanh">
            <button type="button" data-org-goto="quan" data-org-reset="1"><b>${people.length}</b><span>Người trong sổ</span></button>
            <button type="button" data-org-goto="quan" data-org-reset="1" data-org-st="running"><b>${runP}/${maxR}</b><span>Máy đang mở</span></button>
            <button type="button" data-org-goto="cai"><b>${ramHost ? (ramHost + " GB") : "?"} · ${diskTotB ? fmtGB(diskTotB) : "?"}</b><span>RAM · ổ VPS</span></button>
            <button type="button" data-org-goto="cai"><b>${suggestN}</b><span>Gợi ý chỗ người</span></button>
            <button type="button" data-org-goto="cai"><b>${keysOn}/${POOL.length}</b><span>Khóa API đã dán</span></button>
          </div>

          ${vpsCardTong}
          ${ramCalc}

          <div class="org-dash">
            <div class="org-sec">
              <div class="org-sec-h"><div><h3>API</h3>
                <p class="dim org-sec-sub">Trạng thái khóa trong kho trường (tùy chọn).</p></div></div>
              <ul class="org-read">${poolRead}</ul>
              <p class="org-sec-note">Mặc định mỗi người tự dán khóa trên trang Models của máy họ.
                Kho trường: <b>${sharedN}/${people.length || 0}</b> người đang bật.</p>
              <div class="org-sec-acts">
                <button type="button" class="btn" data-org-goto="cai">Kho API trường</button>
              </div>
            </div>
            <div class="org-sec">
              <div class="org-sec-h"><div><h3>Catalog trường</h3>
                <p class="dim org-sec-sub">Đẩy skill / agent / workflow từ Brain Default xuống máy người. Không đè file họ đã sửa.</p></div></div>
              <div class="org-sec-acts org-acts">
                <button type="button" class="btn" id="orgCatDry">Xem trước</button>
                <button type="button" class="btn primary" id="orgCatPush">Đẩy catalog</button>
              </div>
              <p class="dim" id="orgCatMsg"></p>
            </div>
            <div class="org-sec org-sec-snap">
              <div class="org-sec-h"><div><h3>Sổ nhanh</h3>
                <p class="dim org-sec-sub">Bấm tên để mở Quản lý.</p></div>
                <button type="button" class="btn primary" data-org-goto="tao">Tạo người mới</button></div>
              ${tenants.length
                ? `<div class="org-table-wrap"><table class="org-table"><thead><tr><th>Người</th><th>Máy</th><th>Chế độ</th><th>Link</th></tr></thead><tbody>${snapRows}</tbody></table></div>`
                : '<p class="dim">Chưa có người mới, chỉ còn bản cũ của bạn.</p>'}
            </div>
          </div>

          <div class="org-sec org-sec-log">
            <div class="org-sec-h"><div><h3>Nhật ký tổ chức</h3>
              <p class="dim org-sec-sub">Tạo, chính sách, tạm dừng, xóa, đẩy catalog…</p></div></div>
            <div class="org-table-wrap org-table-wrap-log"><table class="org-table" id="orgAuditTable"><thead><tr><th>Lúc</th><th>Việc</th><th>Máy</th><th>Chi tiết</th></tr></thead><tbody id="orgAuditBody"><tr><td colspan="4" class="dim">Đang tải…</td></tr></tbody></table></div>
          </div>
        </section>

        <section class="org-pane org-pane-cai" data-org-pane="cai" ${orgTab === "cai" ? "" : "hidden"}>
          <div class="org-split">
            <div class="org-sec">
              <div class="org-sec-h"><div><h3>Điều phối máy (RAM)</h3>
                <p class="dim org-sec-sub"><b>Không giới hạn số tài khoản.</b> Máy người <b>giữ chạy</b>, không tự tắt theo giờ.
                  Tắt chỉ khi bạn bấm Tắt hoặc Tạm dừng. Não vẫn giữ.</p></div></div>
              ${vpsKpis}
              ${ramCalc}
              <form id="orgCoord" class="org-form org-form-row">
                <label>Trần máy mở cùng lúc<input name="max_running" type="number" min="1" max="20" value="${esc(String(maxHand))}" title="Không phải số người trong sổ. Chỉ số container Docker đang chạy."></label>
                <label>Tự tắt sau (phút)<input name="idle_minutes" type="number" min="0" max="1440" value="0" title="Để 0. Máy không tự tắt."></label>
                <button class="btn primary" type="submit">Lưu điều phối</button>
              </form>
              <p class="dim org-sec-note"><b>Không tự tắt.</b> Máy đang mở giữ chạy đến khi bạn bấm Tắt hoặc Tạm dừng. Não không mất.
                ${ramHost ? (" VPS " + ramHost + " GB, còn " + ramAvail + " GB.") : ""}
                Gợi ý RAM khoảng <b>${esc(String(suggestN))}</b> máy mở. Trần tay đang <b>${esc(String(maxHand))}</b> → hiệu lực <b>${esc(String(maxR))}</b>.</p>
              <p class="dim" id="orgCoordMsg"></p>
            </div>
            <div class="org-sec">
              <div class="org-sec-h"><div><h3>Kho API trường</h3>
                <p class="dim org-sec-sub">Tùy chọn. Mặc định mỗi người tự gắn khóa trên máy họ. Ô trống khi lưu = giữ khóa cũ.</p></div></div>
              <form id="orgPool" class="org-keys org-keys-grid">${poolRows}
                <div class="org-form-actions"><button class="btn primary" type="submit">Lưu khóa API</button></div>
              </form>
              <p class="dim" id="orgPoolMsg"></p>
            </div>
          </div>
        </section>

        <section class="org-pane org-pane-tao" data-org-pane="tao" ${orgTab === "tao" ? "" : "hidden"}>
          <div class="org-sec">
            <div class="org-sec-h"><div><h3>Tạo người mới</h3>
              <p class="dim org-sec-sub">Máy <code>${esc(prefix)}-[slug].${esc(suffix)}</code> · não riêng · MK ≥10 ký tự (chữ + số).
                <b>Không giới hạn số người tạo.</b> Hết chỗ máy mở thì máy mới tạm tắt (não vẫn còn) - họ mở link sẽ xếp hàng / bật khi có chỗ.</p></div></div>
            <form id="orgCreate" class="org-form org-form-grid">
              <label>Tên máy (slug)<input name="slug" required placeholder="Ví dụ: lan" pattern="[a-z0-9]+(-[a-z0-9]+)*" maxlength="32"></label>
              <label>Hiện tên<input name="name" placeholder="Nguyễn Văn A"></label>
              <label>Tên đăng nhập<input name="login_user" required placeholder="Ví dụ: lan" maxlength="32"></label>
              <label>Mật khẩu<input name="password" type="password" required minlength="10" autocomplete="new-password"></label>
              <label>Nhập lại MK<input name="password2" type="password" required minlength="10" autocomplete="new-password"></label>
              <label>Trần ổ (GB)<input name="quota_gb" type="number" min="1" max="20" value="2"></label>
              <label>Trần token/tháng<input name="token_quota" type="number" min="0" step="1000" value="0" title="Chỉ khi dùng kho trường. 0 = không trần"></label>
              <label class="org-span-2">Chế độ model${modeSelect("brain_mode", "byo")}</label>
              <div class="org-prov-wrap org-span-all"><span class="dim">Provider kho trường (tùy chọn)</span>${providerChecks("create_prov", [])}</div>
              <label class="org-check org-span-all"><input name="consent" type="checkbox" required> Đồng ý tạo chỗ xử lý dữ liệu cá nhân (não, chat, khóa trên máy họ; quản trị không đọc nội dung)</label>
              <div class="org-form-actions org-span-all">
                <button class="btn" type="button" id="orgGenPw">Tạo mật khẩu mạnh</button>
                <button class="btn primary" type="submit">Tạo VMOS</button>
              </div>
            </form>
          </div>
        </section>

        <section class="org-pane org-pane-quan" data-org-pane="quan" ${orgTab === "quan" ? "" : "hidden"}>
          <div class="org-sec-h org-quan-head"><div><h3>Quản lý người</h3>
            <p class="dim org-sec-sub">Sổ: <b>${esc(String(people.length))}</b> người · đang mở Docker: <b>${runP}/${maxR}</b>.
              Bật/tắt/tạm dừng không xóa não. Lọc «Đang chạy» chỉ hiện máy mở - chọn «Mọi trạng thái» để thấy hết.</p></div>
            <button type="button" class="btn primary" data-org-goto="tao">Tạo người mới</button></div>
          <div class="org-toolbar">
            <input id="orgSearch" class="org-search" type="search" placeholder="Tìm tên, máy, đăng nhập…" value="${esc(orgQ)}">
            <select id="orgSt" class="org-filter" aria-label="Lọc máy">
              <option value="all"${orgSt === "all" ? " selected" : ""}>Mọi trạng thái</option>
              <option value="running"${orgSt === "running" ? " selected" : ""}>Đang chạy</option>
              <option value="stopped"${orgSt === "stopped" ? " selected" : ""}>Tắt / chưa có</option>
              <option value="paused"${orgSt === "paused" ? " selected" : ""}>Tạm dừng</option>
              <option value="deleted"${orgSt === "deleted" ? " selected" : ""}>Chờ xóa</option>
            </select>
            <select id="orgApi" class="org-filter" aria-label="Lọc API">
              <option value="all"${orgApi === "all" ? " selected" : ""}>Mọi API</option>
              <option value="on"${orgApi === "on" ? " selected" : ""}>Có API chung</option>
              <option value="off"${orgApi === "off" ? " selected" : ""}>Không dùng API chung</option>
            </select>
            <select id="orgKind" class="org-filter" aria-label="Loại máy">
              <option value="all"${orgKind === "all" ? " selected" : ""}>Mọi máy</option>
              <option value="people"${orgKind === "people" ? " selected" : ""}>VMOS người</option>
              <option value="root"${orgKind === "root" ? " selected" : ""}>Bản cũ của bạn</option>
            </select>
            <span class="dim" id="orgCount"></span>
          </div>
          <div class="org-grid">${cards || '<p class="dim">Chưa có người mới, chỉ còn bản cũ của bạn.</p>'}</div>
          <p class="dim" id="orgFilterEmpty" hidden>Không khớp bộ lọc. Xóa ô tìm hoặc chọn lại lọc.</p>
        </section>
      </div>
      <style>
        .org-page{width:100%;max-width:none;box-sizing:border-box}
        .org-busy .org-page{opacity:.72;pointer-events:none;transition:opacity .15s ease}
        .org-tabs.jx-tabs{max-width:none;width:100%;flex-wrap:wrap}
        .org-pane[hidden]{display:none!important}
        .org-pane-tong{display:flex;flex-direction:column;gap:18px}
        .org-lead{margin:0;max-width:72ch}
        .org-warn{padding:10px 12px;border-radius:10px;border:1px solid #e03131;color:#e03131;margin:0 0 4px}
        .org-stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:0}
        .org-stats button{display:flex;flex-direction:column;justify-content:center;gap:4px;width:100%;min-height:76px;text-align:left;padding:12px 14px;border-radius:12px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit;cursor:pointer;font:inherit}
        .org-stats button:hover{border-color:var(--accent,var(--border))}
        .org-stats b{display:block;font-size:clamp(16px,1.4vw,22px);line-height:1.2;word-break:break-word}
        .org-stats span{font-size:12px;opacity:.75}
        .org-sec{padding:16px 18px;border-radius:14px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));min-width:0}
        .org-sec-h{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin:0 0 12px}
        .org-sec-h h3{margin:0;font-size:16px;line-height:1.3}
        .org-sec-sub{margin:4px 0 0;font-size:12.5px;line-height:1.4}
        .org-sec-note{margin:0 0 12px;font-size:13px;line-height:1.45}
        .org-sec-acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto}
        .org-dash{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;align-items:stretch}
        .org-dash > .org-sec{display:flex;flex-direction:column;height:100%}
        .org-sec-snap .org-table-wrap{flex:1;max-height:min(42vh,360px)}
        .org-sec-log .org-table-wrap-log{max-height:min(48vh,420px)}
        .org-kpi{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0 0 12px}
        .org-kpi-i{padding:10px 12px;border-radius:10px;border:1px solid var(--glass-brd,var(--border));background:var(--surface-1,rgba(127,127,127,.06));min-width:0}
        .org-kpi-l{display:block;font-size:11px;text-transform:uppercase;letter-spacing:.04em;opacity:.7;margin-bottom:4px}
        .org-kpi-v{display:block;font-size:14px;font-weight:650;line-height:1.35;word-break:break-word}
        .org-kpi-s{display:block;margin-top:4px;font-size:12px;opacity:.75;line-height:1.35}
        .org-meters{display:grid;gap:8px}
        .org-read{list-style:none;padding:0;margin:0 0 12px;display:grid;gap:8px}
        .org-read li{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap}
        .org-table-wrap{overflow:auto;margin:0;border-radius:10px;border:1px solid var(--glass-brd,var(--border))}
        .org-table{width:100%;border-collapse:collapse;font-size:13px}
        .org-table th,.org-table td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--glass-brd,var(--border));vertical-align:middle}
        .org-table thead th{position:sticky;top:0;background:var(--panel,var(--bg2));z-index:1;font-size:12px;opacity:.85}
        .org-table tbody tr:last-child td{border-bottom:0}
        .org-link{background:none;border:0;padding:0;color:var(--accent,inherit);cursor:pointer;font:inherit;font-weight:600;text-align:left}
        .org-search{flex:1;min-width:180px;padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-filter{padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-form,.org-inline,.org-keys{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin:12px 0 16px}
        .org-form-row{margin:12px 0 8px;align-items:flex-end}
        .org-form-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px 14px;align-items:end;margin:4px 0 0}
        .org-form-grid label,.org-edit-grid label{margin:0;min-width:0}
        .org-form-grid input,.org-form-grid select,.org-edit-grid input,.org-edit-grid select{width:100%;min-width:0;box-sizing:border-box}
        .org-span-2{grid-column:span 2}
        .org-span-all{grid-column:1 / -1}
        .org-form-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:4px}
        .org-keys-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:0}
        .org-keys-grid .org-key{min-width:0;flex:none}
        .org-keys-grid .org-form-actions{grid-column:1 / -1}
        .org-split{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:14px;align-items:start}
        .org-pane-cai,.org-pane-tao,.org-pane-quan{display:flex;flex-direction:column;gap:12px}
        .org-quan-head{margin:0}
        .org-toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0;padding:8px 0;position:sticky;top:0;z-index:3;background:var(--bg,var(--panel));border-bottom:1px solid var(--glass-brd,transparent)}
        .org-inline[hidden]{display:none!important}
        .org-edit-form .org-save{min-height:38px}
        .org-edit-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 12px;align-items:end;margin:10px 0 0;width:100%}
        .org-edit-grid .org-save{justify-self:start}
        .org-more{margin-top:10px;padding-top:8px;border-top:1px solid var(--glass-brd,var(--border))}
        .org-more > summary{cursor:pointer;list-style:none;font-size:13px;font-weight:600;color:var(--text2);user-select:none}
        .org-more > summary::-webkit-details-marker{display:none}
        .org-more > summary::before{content:"▸ ";opacity:.55}
        .org-more[open] > summary::before{content:"▾ "}
        .org-more[open] > summary{margin-bottom:4px;color:var(--text)}
        .org-form label,.org-inline label,.org-key{display:flex;flex-direction:column;gap:4px;font-size:13px}
        .org-form input,.org-inline input,.org-key input{min-width:140px;padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-prov-wrap{width:100%;display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:4px 0}
        .org-prov{font-size:12px}
        .org-form select,.org-inline select{min-width:180px;padding:8px 10px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));color:inherit}
        .org-check{flex-direction:row !important;align-items:center;gap:8px;min-height:38px}
        .org-check input{min-width:auto}
        .org-keys{gap:14px}
        .org-key{min-width:200px;flex:1}
        .org-key-h{display:flex;gap:8px;align-items:center;justify-content:space-between}
        .org-pill{font-size:11px;padding:2px 8px;border-radius:999px;border:1px solid var(--glass-brd,var(--border));opacity:.85}
        .org-pill.on{border-color:#2f9e44;color:#2f9e44}
        .org-pill.hot{border-color:#e03131;color:#e03131}
        .org-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
        .org-card{padding:12px 14px;border-radius:14px;border:1px solid var(--glass-brd,var(--border));background:var(--panel,var(--bg2));min-width:0;display:flex;flex-direction:column;gap:6px}
        .org-card header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}
        .org-card-link{margin:0;font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
        .org-pwr-row{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:4px}
        .org-pwr{border:0;border-radius:10px;padding:8px 14px;font:inherit;font-weight:650;cursor:pointer;min-height:36px;line-height:1.2}
        .org-pwr.on{background:#2f9e44;color:#fff}
        .org-pwr.on:hover{filter:brightness(1.06)}
        .org-pwr.off{background:#e03131;color:#fff}
        .org-pwr.off:hover{filter:brightness(1.06)}
        .org-pwr:disabled{opacity:.55;cursor:wait}
        .org-btn-ghost{background:transparent!important}
        .org-btn-danger,.org-del{border-color:#e03131!important;color:#e03131!important}
        .org-tip{min-height:1.1em;margin:2px 0 0;font-size:12px;color:var(--text2)}
        .org-st{font-size:12px;padding:4px 8px;border-radius:8px;border:1px solid var(--glass-brd,var(--border));white-space:nowrap}
        .org-st.running{border-color:#2f9e44;color:#2f9e44;background:rgba(47,158,68,.12)}
        .org-st.stopped,.org-st.missing{border-color:#e03131;color:#e03131;background:rgba(224,49,49,.1)}
        .org-st.paused{border-color:#f59f00;color:#f59f00;background:rgba(245,159,0,.12)}
        .org-st.deleted{border-color:#e03131;color:#e03131}
        .org-acts{display:flex;flex-wrap:wrap;gap:6px;margin-top:2px}
        .org-acts .btn{padding:6px 10px;font-size:12.5px}
        .org-del-form p{width:100%;margin:0 0 8px;font-size:13px}
        .org-meter{margin:0}
        .org-meter-lbl{font-size:12.5px;margin-bottom:3px}
        .org-bar{height:7px;border-radius:99px;background:rgba(127,127,127,.2);overflow:hidden}
        .org-bar i{display:block;height:100%;background:#2f9e44}
        .org-bar.warn i{background:#f59f00}
        .org-bar.hot i{background:#e03131}
        .org-page h3{margin:8px 0 8px}
        .org-pane-tong h3,.org-sec h3,.org-quan-head h3{margin:0}
        #orgMsg{min-height:1.2em;margin:0}
        @media (max-width:1100px){
          .org-stats{grid-template-columns:repeat(3,minmax(0,1fr))}
          .org-dash{grid-template-columns:1fr 1fr}
          .org-sec-snap{grid-column:1 / -1}
          .org-kpi{grid-template-columns:repeat(2,minmax(0,1fr))}
          .org-split{grid-template-columns:1fr}
          .org-form-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
          .org-keys-grid{grid-template-columns:1fr}
          .org-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
        }
        @media (max-width:720px){
          .org-stats{grid-template-columns:repeat(2,minmax(0,1fr))}
          .org-dash{grid-template-columns:1fr}
          .org-sec-snap{grid-column:auto}
          .org-kpi{grid-template-columns:1fr}
          .org-sec-h{flex-direction:column;align-items:stretch}
          .org-grid{grid-template-columns:1fr}
          .org-form-grid{grid-template-columns:1fr}
          .org-span-2{grid-column:auto}
          .org-edit-grid{grid-template-columns:1fr}
        }
      </style>`;

    const msg = el.querySelector("#orgMsg");
    const poolMsg = el.querySelector("#orgPoolMsg");
    const coordMsg = el.querySelector("#orgCoordMsg");
    const form = el.querySelector("#orgCreate");
    const poolForm = el.querySelector("#orgPool");
    const coordForm = el.querySelector("#orgCoord");
    const gen = el.querySelector("#orgGenPw");

    bindTabs(el);
    bindFilter(el);
    showTab(el, orgTab);

    el.querySelectorAll("[data-org-usage]").forEach(async (box) => {
      const slug = box.getAttribute("data-org-usage");
      const cap = Number(box.getAttribute("data-quota") || 0);
      const tokCap = Number(box.getAttribute("data-tok") || 0);
      let tokUsed = Number(box.getAttribute("data-used") || 0);
      let disk = Number(box.getAttribute("data-disk") || 0);
      const checked = Number(box.getAttribute("data-disk-checked") || 0);
      const fresh = checked > 0 && (Date.now() / 1000 - checked) < 120;
      // Có cache từ list → không gọi /usage (tránh N round-trip). Hết hạn / chưa có thì lấy một lần.
      if (!fresh) {
        try {
          const u = await api("/org/tenants/" + encodeURIComponent(slug) + "/usage");
          disk = u.disk_bytes || 0;
          tokUsed = u.tokens_used || tokUsed;
        } catch (e) {}
      }
      const diskLabel = cap ? (fmtGB(disk) + " / " + cap + " GB") : (fmtGB(disk) + " (không trần)");
      const pct = cap ? Math.max(0, Math.min(100, Math.round(100 * disk / (cap * 1024 * 1024 * 1024)))) : 0;
      const cls = pct >= 95 ? "hot" : (pct >= 80 ? "warn" : "");
      const apiLine = box.querySelector(".dim");
      const apiHtml = apiLine ? apiLine.outerHTML : "";
      box.innerHTML =
        `<div class="org-meter"><div class="org-meter-lbl">Ổ: <b>${esc(diskLabel)}</b></div>
           <div class="org-bar ${cls}"><i style="width:${cap ? pct : 0}%"></i></div></div>`
        + barHtml(tokUsed, tokCap, "Token tháng")
        + apiHtml;
    });

    if (gen) gen.addEventListener("click", () => {
      const pw = genPw();
      form.password.value = pw;
      form.password2.value = pw;
      msg.textContent = "Đã điền mật khẩu mạnh. Gửi cho người đó một lần, VMOS không lưu lại.";
    });
    if (coordForm) coordForm.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const fd = new FormData(coordForm);
      if (coordMsg) coordMsg.textContent = "Đang lưu…";
      try {
        await api("/org/settings/coord", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            max_running: Number(fd.get("max_running") || 6),
            idle_minutes: Number(fd.get("idle_minutes") || 0),
          }),
        });
        orgFlash = "Đã lưu điều phối. Máy nghỉ sẽ tự tắt; mở link là bật lại.";
        orgTab = "cai";
        render(el);
      } catch (e) {
        if (coordMsg) coordMsg.textContent = e.message || "Không lưu được.";
      }
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
        const providers = [];
        form.querySelectorAll('input[name="create_prov"]:checked').forEach((c) => providers.push(c.value));
        const created = await api("/org/tenants", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            slug: String(fd.get("slug") || ""),
            name: String(fd.get("name") || ""),
            login_user: String(fd.get("login_user") || ""),
            password: String(fd.get("password") || ""),
            quota_gb: Number(fd.get("quota_gb") || 2),
            token_quota: Number(fd.get("token_quota") || 0),
            brain_mode: String(fd.get("brain_mode") || "byo"),
            providers,
            consent: !!(form.consent && form.consent.checked),
          }),
        });
        orgQ = String(fd.get("slug") || "");
        orgTab = "quan";
        orgFlash = created.note || "Đã tạo. Gửi tên đăng nhập và mật khẩu. Họ mở link là vào máy mình.";
        render(el);
      } catch (e) {
        const slugTry = String(fd.get("slug") || "").trim().toLowerCase();
        // Proxy/timeout lúc chờ /health hay báo fail dù máy đã ghi sổ - kiểm tra lại danh sách.
        let existed = null;
        if (slugTry) {
          try {
            const lst = await api("/org/tenants");
            existed = (lst.tenants || []).find((t) => t.slug === slugTry) || null;
          } catch (e2) { existed = null; }
        }
        if (existed) {
          orgQ = slugTry;
          orgTab = "quan";
          orgFlash = "Máy «" + slugTry + "» đã có trong sổ dù phản hồi tạo bị lỗi mạng/timeout. "
            + "Kiểm tra trạng thái bên Quản lý; bấm Bật máy nếu chưa chạy.";
          render(el);
        } else {
          msg.textContent = e.message || "Không tạo được.";
        }
      }
    });
    el.querySelectorAll("[data-org-start]").forEach((b) => {
      b.addEventListener("click", async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const slug = b.getAttribute("data-org-start");
        tipOn(b, "Đang bật máy…");
        if (msg) msg.textContent = "Đang bật «" + slug + "»…";
        busyBtn(b, true);
        try {
          await api("/org/tenants/" + encodeURIComponent(slug) + "/start", { method: "POST" });
          orgFlash = "Đã bật máy «" + slug + "».";
          orgTab = "quan";
          render(el);
        } catch (e) {
          busyBtn(b, false);
          const err = e.message || "Không bật được.";
          tipOn(b, err);
          if (msg) msg.textContent = err;
        }
      });
    });
    el.querySelectorAll("[data-org-pause]").forEach((b) => {
      b.addEventListener("click", async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        if (!confirm("Tạm dừng tài khoản này? Máy tắt, mở link không vào được đến khi bấm Chạy lại. Não không xóa.")) return;
        const slug = b.getAttribute("data-org-pause");
        tipOn(b, "Đang tạm dừng…");
        if (msg) msg.textContent = "Đang tạm dừng «" + slug + "»…";
        busyBtn(b, true);
        try {
          await api("/org/tenants/" + encodeURIComponent(slug) + "/pause", { method: "POST" });
          orgFlash = "Đã tạm dừng «" + slug + "». Não còn.";
          orgTab = "quan";
          render(el);
        } catch (e) {
          busyBtn(b, false);
          const err = e.message || "Không tạm dừng được.";
          tipOn(b, err);
          if (msg) msg.textContent = err;
        }
      });
    });
    el.querySelectorAll("[data-org-stop]").forEach((b) => {
      b.addEventListener("click", async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        if (!confirm("Tắt VMOS này? Não và file không xóa.")) return;
        const slug = b.getAttribute("data-org-stop");
        tipOn(b, "Đang tắt máy…");
        if (msg) msg.textContent = "Đang tắt «" + slug + "»…";
        busyBtn(b, true);
        try {
          await api("/org/tenants/" + encodeURIComponent(slug) + "/stop", { method: "POST" });
          orgFlash = "Đã tắt máy «" + slug + "».";
          orgTab = "quan";
          render(el);
        } catch (e) {
          busyBtn(b, false);
          const err = e.message || "Không tắt được.";
          tipOn(b, err);
          if (msg) msg.textContent = err;
        }
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
    async function doCatalog(dry) {
      const box = el.querySelector("#orgCatMsg");
      if (box) box.textContent = dry ? "Đang xem trước…" : "Đang đẩy catalog…";
      try {
        const r = await api("/org/catalog/push", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dry_run: !!dry }),
        });
        const sum = r.summary || {};
        const tenantsObj = r.tenants && !Array.isArray(r.tenants) ? r.tenants : null;
        const n = Number(sum.tenant_count) || (tenantsObj ? Object.keys(tenantsObj).length
          : (Array.isArray(r.tenants) ? r.tenants.length : 0));
        const inst = Number(sum.installed) || 0;
        const upd = Number(sum.updated) || 0;
        const errN = (sum.errors && sum.errors.length) || 0;
        const detail = n
          ? (` · ${n} máy` + (inst || upd ? ` · +${inst} mới / ${upd} cập nhật` : "")
            + (errN ? ` · ${errN} lỗi` : ""))
          : (r.error ? (" · " + r.error) : "");
        if (box) {
          box.textContent = dry
            ? ("Xem trước xong" + detail)
            : (r.ok ? ("Đã đẩy catalog" + detail) : (r.error || "Lỗi đẩy catalog" + detail));
        }
        if (!dry && r.ok) {
          orgFlash = "Đã đẩy catalog xuống " + (n || "các") + " máy người"
            + (inst ? (" (+" + inst + " skill/agent mới).") : ".");
        }
      } catch (e) {
        if (box) box.textContent = e.message || "Không đẩy được.";
      }
    }
    const catDry = el.querySelector("#orgCatDry");
    const catPush = el.querySelector("#orgCatPush");
    if (catDry) catDry.addEventListener("click", () => doCatalog(true));
    if (catPush) catPush.addEventListener("click", () => {
      if (!confirm("Đẩy skill/agent/workflow từ gốc xuống mọi máy người? File họ đã sửa sẽ không bị đè.")) return;
      doCatalog(false);
    });
    (async () => {
      const body = el.querySelector("#orgAuditBody");
      if (!body) return;
      try {
        const a = await api("/org/audit?limit=40");
        const rows = a.rows || [];
        if (!rows.length) {
          body.innerHTML = '<tr><td colspan="4" class="dim">Chưa có nhật ký.</td></tr>';
          return;
        }
        body.innerHTML = rows.map((r) => {
          const when = r.ts ? new Date(r.ts * 1000).toLocaleString("vi-VN") : "";
          return `<tr><td>${esc(when)}</td><td>${esc(r.action || "")}</td><td>${esc(r.slug || "")}</td><td class="dim">${esc(r.extra || "")}</td></tr>`;
        }).join("");
      } catch (e) {
        body.innerHTML = '<tr><td colspan="4" class="dim">' + esc(e.message || "Không đọc được nhật ký") + '</td></tr>';
      }
    })();
    el.querySelectorAll("[data-org-restore]").forEach((b) => {
      b.addEventListener("click", async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const slug = b.getAttribute("data-org-restore");
        tipOn(b, "Đang khôi phục…");
        if (msg) msg.textContent = "Đang khôi phục «" + slug + "»…";
        busyBtn(b, true);
        try {
          await api("/org/tenants/" + encodeURIComponent(slug) + "/restore", { method: "POST" });
          orgFlash = "Đã khôi phục «" + slug + "». Bấm Chạy lại khi cần.";
          orgTab = "quan";
          render(el);
        } catch (e) {
          busyBtn(b, false);
          const err = e.message || "Không khôi phục được.";
          tipOn(b, err);
          if (msg) msg.textContent = err;
        }
      });
    });
    el.querySelectorAll("[data-org-del-open]").forEach((b) => {
      b.addEventListener("click", () => {
        const f = el.querySelector('[data-org-del="' + b.getAttribute("data-org-del-open") + '"]');
        if (f) f.hidden = !f.hidden;
      });
    });
    el.querySelectorAll("form[data-org-del]").forEach((f) => {
      f.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const slug = f.getAttribute("data-org-del");
        const confirmVal = String(f.confirm.value || "").trim().toLowerCase();
        if (confirmVal !== slug) {
          msg.textContent = "Gõ đúng tên máy «" + slug + "» mới xóa được.";
          return;
        }
        const already = !!tenants.find((t) => t.slug === slug && t.deleted_at);
        const purgeNow = already;
        if (purgeNow && !window.confirm("Xóa vĩnh viễn ngay? Não mất hết, không lấy lại.")) return;
        msg.textContent = purgeNow ? "Đang xóa hẳn…" : "Đang đánh dấu xóa…";
        try {
          const body = { confirm: slug };
          if (purgeNow) body.purge_now = true;
          const res = await api("/org/tenants/" + encodeURIComponent(slug), {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          });
          orgFlash = res.purged
            ? ("Đã xóa hẳn " + slug + ".")
            : ("Đã đánh dấu xóa " + slug + ". Não giữ 72 giờ - có thể Khôi phục.");
          orgTab = "quan";
          render(el);
        } catch (e) { msg.textContent = e.message; }
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
        const body = {
          quota_gb: Number(f.quota_gb.value || 0),
          token_quota: Number(f.token_quota.value || 0),
          name: String(f.name.value || ""),
        };
        const login = f.login_user ? String(f.login_user.value || "").trim() : "";
        if (login) body.login_user = login;
        const modeEl = f.querySelector('select[name="brain_mode"]');
        if (modeEl) {
          const providers = [];
          f.querySelectorAll('input[name^="prov_"]:checked').forEach((c) => providers.push(c.value));
          body.brain_mode = String(modeEl.value || "byo");
          body.providers = providers;
        }
        try {
          await api("/org/tenants/" + encodeURIComponent(slug), {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          });
          orgFlash = "Đã lưu thay đổi cho " + slug + ".";
          orgTab = "quan";
          render(el);
        } catch (e) {
          const err = e.message || "Không lưu được.";
          tipOn(f, err);
          if (msg) msg.textContent = err;
        }
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
          msg.textContent = "Đã đặt mật khẩu mới. VMOS gốc không lưu mật khẩu. Gửi cho người đó rồi họ tự đổi.";
          f.hidden = true;
          f.reset();
        } catch (e) { msg.textContent = e.message; }
      });
    });
    startRamPoll(el);
  }

  window.JavisOrg = { render, stopRamPoll };
})();
