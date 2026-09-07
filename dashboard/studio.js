// ============================================
// JAVIS OS - Studio: Agents / Skills / Workflows
// ============================================
(function () {
  // Locale để định dạng số/ngày. Lấy từ i18n chứ KHÔNG khoá "vi-VN": người dùng đổi
  // ngôn ngữ giao diện thì ngày giờ phải đổi theo, nếu không thì nửa màn hình tiếng Anh
  // mà ngày vẫn dd/mm/yyyy kiểu Việt.
  const LOC = () => (window.JavisI18n && JavisI18n.locale()) || "vi-VN";
  const studio = document.getElementById("studio");
  const editor = document.getElementById("studioEditor");
  const brain = () => (window.currentBrainPath ? currentBrainPath() : "brain");
  const esc = (s) => (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  const api = async (p, o) => {
    // Timeout 12s → loader hiện trạng thái rỗng thay vì kẹt "Đang tải..." mãi nếu server chậm/treo.
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 12000);
    try { return await (await fetch(p, Object.assign({}, o, { signal: ctrl.signal }))).json(); }
    catch (e) { return {}; }
    finally { clearTimeout(t); }
  };
  const fd = (obj) => { const f = new FormData(); Object.entries(obj).forEach(([k, v]) => f.append(k, v)); return f; };

  // ===== Xuất / Nhập năng lực (chia sẻ agent/skill/workflow qua file .zip) =====
  // slug nhận 1 chuỗi hoặc mảng (chọn nhiều) - server gói tất cả vào MỘT file .zip.
  const exportUrl = (kind, slug) => `/export?kind=${kind}&slug=${encodeURIComponent(Array.isArray(slug) ? slug.join(",") : slug)}&brain=${encodeURIComponent(brain())}&deps=1`;
  function exportItem(kind, slug) { window.open(exportUrl(kind, slug), "_blank"); }

  // ===== Chọn nhiều để tải về (16/08): tick từng thẻ hoặc Chọn tất cả, tải MỘT gói =====
  const _sel = { workflow: new Set(), agent: new Set(), skill: new Set() };
  function taiDaChon(kind) {
    const ds = [..._sel[kind]];
    if (ds.length) window.open(exportUrl(kind, ds), "_blank");
  }
  function capNhatNutTai(kind, btnId) {
    const b = document.getElementById(btnId);
    if (!b) return;
    const n = _sel[kind].size;
    b.disabled = !n;
    b.textContent = t("studio.dl_sel") + (n ? ` (${n})` : "");
  }
  // Tick một thẻ. `boxCls` là class của ô tick để Chọn tất cả gom được cả trang.
  function noiSel(kind, btnId, el, slug) {
    el.onchange = () => { el.checked ? _sel[kind].add(slug) : _sel[kind].delete(slug); capNhatNutTai(kind, btnId); };
    el.checked = _sel[kind].has(slug);
  }
  // Chọn tất cả <-> bỏ chọn: đã chọn đủ thì bấm lần nữa là bỏ hết.
  function chonTatCa(kind, btnId, boxCls, slugsHienCo) {
    const duTat = slugsHienCo.length && slugsHienCo.every(s => _sel[kind].has(s));
    _sel[kind] = new Set(duTat ? [] : slugsHienCo);
    document.querySelectorAll("." + boxCls).forEach(c => { c.checked = _sel[kind].has(c.dataset.slug); });
    capNhatNutTai(kind, btnId);
  }
  function importItems(reload) {
    const inp = document.createElement("input");
    inp.type = "file"; inp.accept = ".zip,.md,.skill,application/zip";
    inp.onchange = async () => {
      if (!inp.files || !inp.files.length) return;
      const ow = confirm(t("studio.import_confirm"));
      const f = new FormData();
      f.append("file", inp.files[0]); f.append("brain", brain()); f.append("overwrite", ow ? "1" : "0");
      let r;
      try { r = await (await fetch("/import", { method: "POST", body: f })).json(); }
      catch (e) { alert(t("studio.upload_err") + " " + e.message); return; }
      if (r && r.error) { alert(t("studio.import_fail") + " " + r.error); return; }
      const show = (a) => (a && a.length) ? a.join(", ") : t("studio.none");
      alert(`${t("studio.import_done")}\n• ${t("studio.imported")} ${show(r.imported)}\n• ${t("studio.skipped")} ${show(r.skipped)}`
        + ((r.errors && r.errors.length) ? `\n• ${t("studio.errors")} ${r.errors.join("; ")}` : ""));
      if (reload) reload();
    };
    inp.click();
  }

  // Studio đã tách thành các trang sidebar riêng. openStudio = điều hướng rail (giữ tương thích
  // cho nút header & dải số liệu .bstat ở đáy graph). Console gọi loader qua window.JavisStudio.
  window.openStudio = (tab) => { if (window.Alpine) Alpine.store("nav").go(tab || "workflows"); };
  window.JavisStudio = {
    workflows: loadWorkflows, agents: loadAgents, skills: loadSkills,
  };
  const _studioBtn = document.getElementById("studioOpenBtn");
  if (_studioBtn) _studioBtn.addEventListener("click", () => window.openStudio("workflows"));

  const refreshStats = () => { if (window.loadBrainStats) window.loadBrainStats(); };

  // ===== Khung NHÓM: cột nhóm bên trái + ô tìm - DÙNG CHUNG cho Workflows / Agents / Skills =====
  // Trang Skills có cột nhóm từ lâu, còn Agents và Workflows thì không: brain dùng vài tháng là
  // hai danh sách phẳng vài chục dòng, phải dò bằng mắt. Ở đây gom thành MỘT khung cho cả ba
  // trang - cùng field `group` trong frontmatter, cùng nhóm mặc định, cùng cách lọc, cùng cách
  // xếp trên điện thoại. Chép tay thành ba bản là ba bản trôi lệch nhau ngay lần sửa đầu tiên.
  const NHOM_MD = "Chung";                     // nhóm mặc định khi file chưa khai `group`
  const nhomCua = (x) => (x && String(x.group || "").trim()) || NHOM_MD;

  // Bỏ dấu để gõ "viet email" vẫn ra "Viết email".
  function _spNoAccent(s) {
    s = String(s == null ? "" : s);
    try { s = s.normalize("NFD").replace(/[\u0300-\u036f]/g, ""); } catch (e) {}
    return s.replace(/[đĐ]/g, "d").toLowerCase();
  }

  function demNhom(items) {
    const m = {};
    (items || []).forEach(x => { const g = nhomCua(x); m[g] = (m[g] || 0) + 1; });
    return m;
  }

  // HTML của khung: cột nhóm + ô tìm + một chỗ trống (id=bodyId) để mỗi trang tự vẽ danh sách
  // theo kiểu riêng của nó (thẻ agent, hàng workflow, thẻ skill).
  function khungNhomHtml(items, state, o) {
    const dem = demNhom(items);
    const cats = ["ALL"].concat(Object.keys(dem).sort((a, b) => a.localeCompare(b, LOC())));
    const catHtml = cats.map(c => `<div class="gr-cat ${state.cat === c ? "sel" : ""}" data-cat="${esc(c)}"><span>${c === "ALL" ? esc(t("studio.all")) : esc(c)}</span><span class="n">${c === "ALL" ? items.length : dem[c]}</span></div>`).join("");
    return `<div class="gr">
      <div class="gr-side"><div class="sec">${esc(t("studio.groups"))}</div>${catHtml}</div>
      <div class="gr-main">
        <div class="gr-bar"><h4>${state.cat === "ALL" ? esc(t("studio.all")) : esc(state.cat)}</h4><span class="cnt"></span>
          <input id="${o.searchId}" placeholder="${esc(o.searchPh)}" value="${esc(state.q)}"></div>
        <div class="${o.bodyCls || ""}" id="${o.bodyId}"></div>
      </div></div>`;
  }

  // Lọc theo nhóm đang chọn + ô tìm. `blob` trả chuỗi dùng để dò của một mục.
  function locTheoNhom(items, state, blob) {
    let list = items || [];
    if (state.cat !== "ALL") list = list.filter(x => nhomCua(x) === state.cat);
    const nq = _spNoAccent((state.q || "").trim());
    if (nq) list = list.filter(x => _spNoAccent(blob(x)).includes(nq));
    return list;
  }

  // Bấm nhóm thì vẽ lại CẢ trang (cột nhóm và tiêu đề đổi theo); gõ tìm thì chỉ vẽ lại danh
  // sách, để con trỏ không bị nhảy ra khỏi ô tìm giữa lúc đang gõ.
  function ganKhungNhom(panel, state, o) {
    panel.querySelectorAll(".gr-side .gr-cat").forEach(c => {
      c.onclick = () => { state.cat = c.dataset.cat; o.veLai(); };
    });
    const s = panel.querySelector("#" + o.searchId);
    if (s) s.oninput = () => { state.q = s.value; o.veDanhSach(); };
  }

  function datSoLuong(panel, chu) {
    const el = panel.querySelector(".gr-bar .cnt");
    if (el) el.textContent = chu;
  }

  // Gợi ý nhóm ĐANG CÓ cho ô nhập trong form, để khỏi đẻ "Marketing" và "marketing" song song.
  function nhomDatalist(items, id) {
    const gs = [...new Set((items || []).map(nhomCua))].sort((a, b) => a.localeCompare(b, LOC()));
    return `<datalist id="${id}">${gs.map(g => `<option value="${esc(g)}">`).join("")}</datalist>`;
  }

  function switchTab(tab) {
    document.querySelectorAll(".stab").forEach(b => b.classList.toggle("active", b.dataset.tab === tab));
    ["workflows", "agents", "skills"].forEach(t => document.getElementById("panel-" + t).hidden = (t !== tab));
    if (tab === "workflows") loadWorkflows();
    else if (tab === "agents") loadAgents();
    else loadSkills();
  }

  // ===== Workflows =====
  // Biến workflow đọc thành lời cho ô bước: thay "…" (cũ) vì "Nhận …, tạo project folder"
  // đọc lên cụt nghĩa. Biến lạ thì hiện thẳng tên biến, đừng nuốt thành dấu ba chấm.
  const WF_VARS = { input: "studio.var_input", prev: "studio.var_prev" };   // tên KHOÁ i18n, tra lúc vẽ
  function renderPipeline(steps) {
    return (steps || []).map((s, i) => {
      const task = (s.task || "").replace(/\{\{\s*([\w.-]+)\s*\}\}/g, (m, v) => (WF_VARS[v] ? t(WF_VARS[v]) : v));
      return `<div class="wf-pstep" data-i="${i}">
          <div class="wps-num">${String(i + 1).padStart(2, "0")}</div>
          ${task ? `<div class="wps-task" title="${esc(task)}">${esc(task)}</div>` : ''}
          <div class="wps-name">${esc(s.agent)}</div>
        </div>`;
    }).join('');
  }

  const _wfState = { cat: "ALL", q: "", wfs: [] };

  async function loadWorkflows() {
    _injectStudioCss();
    const panel = document.getElementById("panel-workflows");
    panel.innerHTML = `<div class="empty">${esc(t("common.loading"))}</div>`;
    const d = await api(`/workflows?brain=${encodeURIComponent(brain())}`);
    _wfState.wfs = d.workflows || [];
    _sel.workflow.clear();   // nạp lại trang là làm mới lựa chọn (danh sách có thể đã đổi)
    refreshStats();
    renderWorkflowUI();
  }

  const _wfFiltered = () => locTheoNhom(_wfState.wfs, _wfState,
    (w) => `${w.name} ${w.slug} ${w.description || ""}`);

  function renderWorkflowUI() {
    const panel = document.getElementById("panel-workflows");
    const all = _wfState.wfs;
    panel.innerHTML = `<div class="panel-bar"><h3>Workflows</h3><div class="pb-actions"><button class="s-btn-ghost" id="wfSelAll" title="${esc(t("studio.selall_title"))}">${esc(t("studio.selall"))}</button><button class="s-btn-ghost" id="wfDl" disabled title="${esc(t("studio.dl_title"))}">${esc(t("studio.dl_sel"))}</button><button class="s-btn-ghost" id="wfImport">${esc(t("studio.import"))}</button><button class="s-btn-ghost" id="seedBtn">${esc(t("studio.seed"))}</button><button class="s-btn-ghost" id="seedStrategyBtn" title="NCTT → chiến lược KD/MKT → proposal">Bộ Proposal</button><button class="s-btn-ghost" id="seedVideoBtn" title="Nghiên cứu → kịch bản → đạo diễn đa pipeline">Bộ Video</button><button class="s-btn-ghost" id="seedBaiGiangBtn" title="Bài giảng Gemini: lớp học / video / slide / văn bản">Bộ Bài giảng</button><button class="s-btn-ghost" id="seedMarketingBtn" title="Marketing Gemini: SEO / nghiên cứu / Facebook">Bộ Marketing</button><button class="s-btn-ghost" id="seedPhapCheBtn" title="Agent Pháp chế + sources/phap-che">Bộ Pháp chế</button><button class="s-btn" id="newWf">+ Workflow</button></div></div>
      ${all.length ? khungNhomHtml(all, _wfState, { bodyId: "wfCards", bodyCls: "wf-list",
                                                    searchId: "wfSearch", searchPh: t("studio.wf_search_ph") })
      : `<div class="empty">${esc(t("studio.wf_empty"))}</div>`}`;
    document.getElementById("newWf").onclick = () => editWorkflow(null);
    document.getElementById("wfImport").onclick = () => importItems(loadWorkflows);
    document.getElementById("seedBtn").onclick = async () => { await api("/studio/seed", { method: "POST", body: fd({ brain: brain() }) }); loadWorkflows(); };
    document.getElementById("seedStrategyBtn").onclick = async () => {
      await api("/studio/seed-strategy", { method: "POST", body: fd({ brain: brain() }) });
      loadWorkflows(); loadAgents?.();
    };
    document.getElementById("seedVideoBtn").onclick = async () => {
      const btn = document.getElementById("seedVideoBtn");
      if (btn) { btn.disabled = true; btn.textContent = "Đang tạo…"; }
      try {
        await api("/studio/seed-video", { method: "POST", body: fd({ brain: brain() }) });
        loadWorkflows(); loadAgents?.();
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Bộ Video"; }
      }
    };
    document.getElementById("seedBaiGiangBtn").onclick = async () => {
      const btn = document.getElementById("seedBaiGiangBtn");
      if (btn) { btn.disabled = true; btn.textContent = "Đang tạo…"; }
      try {
        await api("/studio/seed-bai-giang", { method: "POST", body: fd({ brain: brain() }) });
        loadWorkflows(); loadAgents?.();
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Bộ Bài giảng"; }
      }
    };
    document.getElementById("seedMarketingBtn") && (document.getElementById("seedMarketingBtn").onclick = async () => {
      const btn = document.getElementById("seedMarketingBtn");
      if (btn) { btn.disabled = true; btn.textContent = "Đang tạo…"; }
      try {
        await api("/studio/seed-marketing", { method: "POST", body: fd({ brain: brain() }) });
        loadWorkflows(); loadAgents?.();
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Bộ Marketing"; }
      }
    });
    document.getElementById("seedPhapCheBtn").onclick = async () => {
      const btn = document.getElementById("seedPhapCheBtn");
      if (btn) { btn.disabled = true; btn.textContent = "Đang tạo…"; }
      try {
        await api("/studio/seed-phap-che", { method: "POST", body: fd({ brain: brain() }) });
        loadWorkflows(); loadAgents?.();
      } finally {
        if (btn) { btn.disabled = false; btn.textContent = "Bộ Pháp chế"; }
      }
    };
    document.getElementById("wfDl").onclick = () => taiDaChon("workflow");
    // Chọn tất cả = danh sách ĐANG HIỆN (đúng nhóm + đúng ô tìm), giống trang Skills.
    document.getElementById("wfSelAll").onclick = () =>
      chonTatCa("workflow", "wfDl", "wf-sel", _wfFiltered().map(w => w.slug));
    capNhatNutTai("workflow", "wfDl");
    if (!all.length) return;
    ganKhungNhom(panel, _wfState, { searchId: "wfSearch", veLai: renderWorkflowUI, veDanhSach: renderWorkflowList });
    renderWorkflowList();
  }

  function renderWorkflowList() {
    const cards = document.getElementById("wfCards"); if (!cards) return;
    const wfs = _wfFiltered();
    datSoLuong(document.getElementById("panel-workflows"), wfs.length + " workflow");
    if (!wfs.length) { cards.innerHTML = `<div class="empty">${esc(t("studio.wf_no_match"))}</div>`; return; }
    cards.innerHTML = "";
    wfs.forEach(w => {
      const active = w.status === "active";
      const div = document.createElement("div");
      div.className = "wf-row" + (active ? "" : " archived");
      div.dataset.slug = w.slug;
      const mdl = (w.model || "").trim();
      const mprov = (w.model_provider || "").trim();
      const mdlLabel = mdl
        ? `${mprov ? mprov + " · " : ""}${mdl}`
        : t("studio.wf_model_follow");
      div.innerHTML = `
        <div class="wf-header">
          <input type="checkbox" class="wf-sel" data-slug="${esc(w.slug)}" title="${esc(t("studio.sel_one"))}">
          <div class="wf-name">${esc(w.name)}</div>
          <span class="wf-badge ${active ? "ready" : "off"}">${esc(active ? t("studio.ready") : t("studio.archived"))}</span>
          <span class="wf-model${mdl ? " set" : ""}" title="${esc(t("studio.wf_model_hint"))}">${esc(mdlLabel)}</span>
          <span class="wf-group">${ic("folder-open")} ${esc(nhomCua(w))}</span>
          <span class="wf-count">${(w.steps || []).length} ${esc(t("studio.steps"))}</span>
          <div class="wf-spacer"></div>
          <div class="wf-actions">
            <button class="s-btn run" ${active ? "" : "disabled"}>▶ ${esc(t("studio.run"))}</button>
            <button class="s-btn-ghost edit">${esc(t("common.edit"))}</button>
            <button class="s-btn-ghost archive">${esc(active ? t("studio.archived") : t("studio.activate"))}</button>
            <button class="s-btn-ghost exp" title="${esc(t("studio.export_title"))}">${esc(t("studio.export"))}</button>
            <button class="s-btn-ghost del">${esc(t("common.delete"))}</button>
          </div>
        </div>
        ${w.description ? `<div class="wf-desc">${esc(w.description)}</div>` : ''}
        <div class="wf-pipeline">${renderPipeline(w.steps)}</div>`;
      noiSel("workflow", "wfDl", div.querySelector(".wf-sel"), w.slug);
      div.querySelector(".exp").onclick = () => exportItem("workflow", w.slug);
      div.querySelector(".archive").onclick = async () => { await api("/workflows/toggle", { method: "POST", body: fd({ slug: w.slug, brain: brain() }) }); loadWorkflows(); };
      div.querySelector(".run").onclick = () => runWorkflow(w, div);
      div.querySelector(".edit").onclick = () => editWorkflow(w);
      div.querySelector(".del").onclick = async () => { if (confirm(t("studio.del_wf", { ten: w.name }))) { await api("/workflows/delete", { method: "POST", body: fd({ slug: w.slug, brain: brain() }) }); loadWorkflows(); } };
      cards.appendChild(div);
    });
  }

  // ===== Run workflow: modal brief → SSE =====
  function _composeWfBrief(goal, scope, constraints, notes) {
    const parts = [];
    if (goal) parts.push(`Mục tiêu: ${goal}`);
    if (scope) parts.push(`Phạm vi: ${scope}`);
    if (constraints) parts.push(`Ràng buộc: ${constraints}`);
    if (notes) parts.push(`Ghi chú: ${notes}`);
    return parts.join("\n\n");
  }

  function _wfBriefDraftKey(slug) {
    return "javis.wf.brief." + String(slug || "unknown");
  }

  function _loadWfBriefDraft(slug) {
    try {
      const raw = sessionStorage.getItem(_wfBriefDraftKey(slug));
      if (!raw) return null;
      const d = JSON.parse(raw);
      if (!d || typeof d !== "object") return null;
      return {
        goal: String(d.goal || ""),
        scope: String(d.scope || ""),
        constraints: String(d.constraints || ""),
        notes: String(d.notes || ""),
      };
    } catch (e) {
      return null;
    }
  }

  function _saveWfBriefDraft(slug, fields) {
    try {
      const payload = {
        goal: (fields.goal || "").trim(),
        scope: (fields.scope || "").trim(),
        constraints: (fields.constraints || "").trim(),
        notes: (fields.notes || "").trim(),
      };
      if (!payload.goal && !payload.scope && !payload.constraints && !payload.notes) {
        sessionStorage.removeItem(_wfBriefDraftKey(slug));
        return;
      }
      sessionStorage.setItem(_wfBriefDraftKey(slug), JSON.stringify(payload));
    } catch (e) { /* quota / private mode */ }
  }

  function _clearWfBriefDraft(slug) {
    try {
      sessionStorage.removeItem(_wfBriefDraftKey(slug));
    } catch (e) {}
  }

  function _askWfBrief(w) {
    return new Promise((resolve) => {
      let modal = document.getElementById("wfRunModal");
      // Bản cũ không có ô nháp → tạo lại modal một lần.
      if (modal && !modal.querySelector("#wfRunDraftHint")) {
        modal.remove();
        modal = null;
      }
      if (!modal) {
        modal = document.createElement("div");
        modal.id = "wfRunModal";
        modal.className = "wf-run-modal";
        modal.innerHTML = `
          <div class="wf-run-card" role="dialog" aria-modal="true" aria-labelledby="wfRunTitle">
            <div class="wf-run-head">
              <div>
                <h3 id="wfRunTitle"></h3>
                <p class="wf-run-desc" id="wfRunDesc"></p>
              </div>
              <button type="button" class="wf-run-x" id="wfRunClose" aria-label="Close">×</button>
            </div>
            <div class="wf-run-body">
              <p class="wf-run-draft-hint" id="wfRunDraftHint" hidden></p>
              <label for="wfGoal">${esc(t("studio.brief_goal"))} <span class="req">*</span></label>
              <textarea id="wfGoal" rows="3" placeholder="${esc(t("studio.brief_goal_ph"))}"></textarea>
              <label for="wfScope">${esc(t("studio.brief_scope"))}</label>
              <textarea id="wfScope" rows="2" placeholder="${esc(t("studio.brief_scope_ph"))}"></textarea>
              <label for="wfConstraints">${esc(t("studio.brief_constraints"))}</label>
              <textarea id="wfConstraints" rows="2" placeholder="${esc(t("studio.brief_constraints_ph"))}"></textarea>
              <label for="wfNotes">${esc(t("studio.brief_notes"))}</label>
              <textarea id="wfNotes" rows="3" placeholder="${esc(t("studio.brief_notes_ph"))}"></textarea>
              <details class="wf-run-preview">
                <summary>${esc(t("studio.brief_preview"))}</summary>
                <pre id="wfBriefPreview"></pre>
              </details>
              <p class="wf-run-err" id="wfRunErr" hidden></p>
            </div>
            <div class="wf-run-foot">
              <button type="button" class="s-btn-ghost" id="wfRunCancel">${esc(t("common.cancel"))}</button>
              <button type="button" class="s-btn" id="wfRunGo">${esc(t("studio.run_wf"))}</button>
            </div>
          </div>`;
        document.body.appendChild(modal);
      }
      const title = modal.querySelector("#wfRunTitle");
      const desc = modal.querySelector("#wfRunDesc");
      const goal = modal.querySelector("#wfGoal");
      const scope = modal.querySelector("#wfScope");
      const constraints = modal.querySelector("#wfConstraints");
      const notes = modal.querySelector("#wfNotes");
      const preview = modal.querySelector("#wfBriefPreview");
      const err = modal.querySelector("#wfRunErr");
      const draftHint = modal.querySelector("#wfRunDraftHint");
      const slug = w.slug || w.name || "";
      title.textContent = t("studio.run_brief_title", { ten: w.name || w.slug });
      desc.textContent = (w.description || "").trim();
      desc.hidden = !desc.textContent;

      const draft = _loadWfBriefDraft(slug);
      goal.value = draft ? draft.goal : "";
      scope.value = draft ? draft.scope : "";
      constraints.value = draft ? draft.constraints : "";
      notes.value = draft ? draft.notes : "";
      if (draftHint) {
        const hasDraft = !!(
          draft &&
          (draft.goal || draft.scope || draft.constraints || draft.notes)
        );
        draftHint.hidden = !hasDraft;
        draftHint.textContent = hasDraft
          ? "Đã khôi phục bản nháp trong phiên này (bấm ra ngoài vẫn giữ)."
          : "";
      }
      preview.textContent = "";
      err.hidden = true; err.textContent = "";

      const readFields = () => ({
        goal: goal.value,
        scope: scope.value,
        constraints: constraints.value,
        notes: notes.value,
      });
      const syncPreview = () => {
        preview.textContent = _composeWfBrief(goal.value.trim(), scope.value.trim(),
          constraints.value.trim(), notes.value.trim()) || t("studio.brief_preview_empty");
      };
      const persistDraft = () => _saveWfBriefDraft(slug, readFields());
      [goal, scope, constraints, notes].forEach((el) => {
        el.oninput = () => {
          syncPreview();
          persistDraft();
        };
      });
      syncPreview();

      const close = (val) => {
        // Đóng mà chưa chạy → giữ nháp session. Chạy xong → xóa nháp.
        if (val == null) persistDraft();
        else _clearWfBriefDraft(slug);
        modal.classList.remove("open");
        document.removeEventListener("keydown", onKey);
        resolve(val);
      };
      const onKey = (e) => {
        if (e.key === "Escape") close(null);
      };
      document.addEventListener("keydown", onKey);
      modal.querySelector("#wfRunClose").onclick = () => close(null);
      modal.querySelector("#wfRunCancel").onclick = () => close(null);
      modal.onclick = (e) => { if (e.target === modal) close(null); };
      modal.querySelector("#wfRunGo").onclick = () => {
        const g = goal.value.trim();
        if (!g) {
          err.textContent = t("studio.brief_goal_required");
          err.hidden = false;
          goal.focus();
          return;
        }
        close(_composeWfBrief(g, scope.value.trim(), constraints.value.trim(), notes.value.trim()));
      };
      modal.classList.add("open");
      setTimeout(() => goal.focus(), 30);
    });
  }

  // ===== Run workflow: modal brief → SSE (panel rộng; đóng = thu nhỏ, vẫn chạy) =====
  let _wfActive = null; // { es, card, badge, w, status, result, stepTexts, brief }

  function _wfHideDrawerKeepRun() {
    const drawer = document.getElementById("runDrawer");
    if (drawer) drawer.classList.remove("open");
    _wfSyncFloat();
  }

  function _wfShowDrawer() {
    const drawer = document.getElementById("runDrawer");
    if (drawer) drawer.classList.add("open");
    const fl = document.getElementById("runFloat");
    if (fl) fl.hidden = true;
    if (_wfActive) _wfActive.floatAck = true;
  }

  function _wfSyncFloat() {
    const fl = document.getElementById("runFloat");
    const lbl = document.getElementById("runFloatLabel");
    const btn = document.getElementById("runFloatOpen");
    if (!fl || !btn) return;
    const drawerOpen = !!(document.getElementById("runDrawer") &&
      document.getElementById("runDrawer").classList.contains("open"));
    if (!_wfActive || drawerOpen) {
      fl.hidden = true;
      return;
    }
    const st = _wfActive.status;
    // Chỉ hiện chip khi đang chạy / chờ duyệt, hoặc vừa xong/lỗi mà user chưa mở lại.
    if (st === "done" || st === "error") {
      if (_wfActive.floatAck) { fl.hidden = true; return; }
    } else if (st !== "running" && st !== "wait") {
      fl.hidden = true;
      return;
    }
    fl.hidden = false;
    btn.classList.remove("done", "err");
    if (st === "done") {
      btn.classList.add("done");
      if (lbl) lbl.textContent = t("studio.float_done");
    } else if (st === "error") {
      btn.classList.add("err");
      if (lbl) lbl.textContent = t("studio.float_err");
    } else if (st === "wait") {
      if (lbl) lbl.textContent = t("studio.float_wait");
    } else {
      const name = (_wfActive.w && _wfActive.w.name) || "Workflow";
      if (lbl) lbl.textContent = t("studio.float_running", { name });
    }
  }

  function _extractReportLinks(text) {
    const seen = new Set();
    const out = [];
    const add = (href, label, kind) => {
      const key = kind + "|" + href;
      if (!href || seen.has(key)) return;
      seen.add(key);
      out.push({ href, label: label || href, kind });
    };
    const s = String(text || "");
    // Markdown [label](url)
    s.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/gi, (_, lab, url) => {
      add(url, lab, "url");
      return "";
    });
    // Bare URLs
    s.replace(/https?:\/\/[^\s<>"'`)\]}]+/gi, (url) => {
      add(url.replace(/[.,;:!?)]+$/, ""), url.replace(/[.,;:!?)]+$/, ""), "url");
      return "";
    });
    // Vault-ish paths ending in known extensions
    s.replace(/(?:^|[\s("'`])((?:[\w./-]+\.(?:md|html|htm|pdf|png|jpg|jpeg|webp|svg|csv|json|txt|docx?))(?::\d+)?)/gim, (_, p) => {
      const path = p.replace(/:\d+$/, "").replace(/^\.\//, "");
      if (path.startsWith("http")) return "";
      add("#open=" + encodeURIComponent(path), path, "vault");
      return "";
    });
    // Wikilinks [[path]] / [[path|alias]]
    s.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_, target, alias) => {
      const tgt = String(target || "").trim();
      if (!tgt) return "";
      add("#open=" + encodeURIComponent(tgt), alias || tgt, "vault");
      return "";
    });
    return out;
  }

  function _buildWfReportMd(w, brief, stepTexts, result) {
    const lines = [
      "# " + (w.name || w.slug || "Workflow"),
      "",
      "- Slug: `" + (w.slug || "") + "`",
      "- Thời gian: " + new Date().toLocaleString(LOC()),
      "",
    ];
    if (brief) {
      lines.push("## Brief", "", brief, "");
    }
    (stepTexts || []).forEach((st, i) => {
      if (!st) return;
      lines.push("## Bước " + (i + 1) + (st.agent ? " - " + st.agent : ""), "");
      if (st.task) lines.push("*" + st.task + "*", "");
      lines.push(st.text || "(trống)", "");
    });
    if (result) {
      lines.push("## Tổng kết", "", result, "");
    }
    const links = _extractReportLinks(
      [result || ""].concat((stepTexts || []).map((x) => (x && x.text) || "")).join("\n")
    );
    if (links.length) {
      lines.push("## Liên kết", "");
      links.forEach((L) => {
        if (L.kind === "url") lines.push("- [" + L.label + "](" + L.href + ")");
        else lines.push("- [[" + L.label + "]] (`" + decodeURIComponent(L.href.replace(/^#open=/, "")) + "`)");
      });
      lines.push("");
    }
    return lines.join("\n");
  }

  function _downloadText(filename, content, mime) {
    const blob = new Blob([content], { type: mime || "text/plain;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 800);
  }

  function _reportHtmlDoc(title, mdBody) {
    let raw = String(mdBody || "");
    const imgs = [];
    const links = [];
    raw = raw.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, (_, alt, src) => {
      const i = imgs.length;
      imgs.push({ alt, src });
      return "%%IMG" + i + "%%";
    });
    raw = raw.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, (_, lab, url) => {
      const i = links.length;
      links.push({ lab, url });
      return "%%A" + i + "%%";
    });
    let html = esc(raw);
    html = html
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/^# (.+)$/gm, "<h1>$1</h1>")
      .replace(/\n/g, "<br>\n");
    imgs.forEach((im, i) => {
      html = html.split("%%IMG" + i + "%%").join(
        `<img src="${esc(im.src)}" alt="${esc(im.alt)}" style="max-width:100%;height:auto;margin:12px 0">`
      );
    });
    links.forEach((L, i) => {
      html = html.split("%%A" + i + "%%").join(
        `<a href="${esc(L.url)}" target="_blank" rel="noopener">${esc(L.lab)}</a>`
      );
    });
    return `<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">
<title>${esc(title)}</title>
<style>
  body{font-family:Georgia,"Times New Roman",serif;max-width:820px;margin:32px auto;padding:0 20px;line-height:1.55;color:#1a1a1a;background:#fff}
  h1{font-size:1.6rem} h2{font-size:1.25rem;margin-top:1.6em;border-bottom:1px solid #ddd;padding-bottom:.25em}
  h3{font-size:1.1rem;margin-top:1.2em}
  a{color:#0b57d0} img{max-width:100%;height:auto;display:block}
  .meta{color:#555;font-size:.9rem}
  @media print{body{margin:12mm;max-width:none}}
</style></head><body>
<p class="meta">${esc(new Date().toLocaleString(LOC()))} · Javis OS · ${esc(title)}</p>
<article>${html}</article>
</body></html>`;
  }

  function _renderRunExportFoot(w) {
    const foot = document.getElementById("runFoot");
    if (!foot || !_wfActive) return;
    foot.hidden = false;
    foot.innerHTML =
      `<button type="button" class="s-btn" id="runDlMd">${esc(t("studio.dl_md"))}</button>` +
      `<button type="button" class="s-btn-ghost" id="runDlHtml">${esc(t("studio.dl_html"))}</button>` +
      `<button type="button" class="s-btn-ghost" id="runDlPdf">${esc(t("studio.dl_pdf"))}</button>` +
      `<button type="button" class="s-btn-ghost" id="runSaveVault">${esc(t("studio.save_vault"))}</button>`;
    const md = () =>
      _buildWfReportMd(w, _wfActive.brief, _wfActive.stepTexts, _wfActive.result);
    const base = (w.slug || "workflow") + "-bao-cao-" + new Date().toISOString().slice(0, 10);
    foot.querySelector("#runDlMd").onclick = () => _downloadText(base + ".md", md(), "text/markdown;charset=utf-8");
    foot.querySelector("#runDlHtml").onclick = () =>
      _downloadText(base + ".html", _reportHtmlDoc(w.name || w.slug, md()), "text/html;charset=utf-8");
    foot.querySelector("#runDlPdf").onclick = () => {
      const html = _reportHtmlDoc(w.name || w.slug, md());
      const win = window.open("", "_blank");
      if (!win) { alert(t("studio.popup_blocked")); return; }
      win.document.write(html);
      win.document.close();
      setTimeout(() => { try { win.focus(); win.print(); } catch (e) {} }, 350);
    };
    foot.querySelector("#runSaveVault").onclick = async () => {
      const path = "Javis/workflow-runs/" + base + ".md";
      const f = fd({ brain: brain(), path, content: md() });
      const r = await fetch("/files/write", { method: "POST", body: f, credentials: "same-origin" });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || d.error) {
        alert(t("studio.save_fail") + " " + (d.error || r.status));
        return;
      }
      alert(t("studio.save_ok", { path }));
      try {
        if (typeof window.openVaultTarget === "function") window.openVaultTarget(path);
        else location.hash = "#open=" + encodeURIComponent(path);
      } catch (e) {}
    };
  }

  function _appendRunSummary(w, resultText) {
    const stepsEl = document.getElementById("runSteps");
    if (!stepsEl) return;
    const links = _extractReportLinks(
      [resultText || ""]
        .concat((_wfActive && _wfActive.stepTexts || []).map((x) => (x && x.text) || ""))
        .join("\n")
    );
    let linksHtml = "";
    if (links.length) {
      linksHtml =
        `<div class="run-summary-links"><div class="rsl-lbl">${esc(t("studio.summary_links"))}</div>` +
        links
          .map((L) => {
            if (L.kind === "url") {
              return `<a href="${esc(L.href)}" target="_blank" rel="noopener noreferrer">${esc(L.label)}</a>`;
            }
            return `<a href="${esc(L.href)}" data-vault-path="${esc(decodeURIComponent(L.href.replace(/^#open=/, "")))}">${esc(L.label)}</a>`;
          })
          .join("") +
        `</div>`;
    }
    const body = (resultText || "").trim() || t("studio.summary_empty");
    stepsEl.insertAdjacentHTML(
      "beforeend",
      `<div class="run-summary" id="runSummary">` +
        `<h4>${ic("check", { cls: "ic-ok" })} ${esc(t("studio.done"))}</h4>` +
        `<div class="run-summary-body">${esc(body)}</div>` +
        linksHtml +
        `</div>`
    );
    stepsEl.querySelectorAll(".rs-out").forEach((el) => el.classList.add("full"));
    stepsEl.scrollTop = stepsEl.scrollHeight;
    _renderRunExportFoot(w);
  }

  async function runWorkflow(w, card) {
    if (_wfActive && (_wfActive.status === "running" || _wfActive.status === "wait")) {
      _wfShowDrawer();
      alert(t("studio.already_running"));
      return;
    }

    const input = await _askWfBrief(w);
    if (input === null) return;

    const badge = card && card.querySelector(".wf-badge");
    if (card) card.classList.add("running");
    if (badge) {
      badge.className = "wf-badge running";
      badge.innerHTML = ic("loader", { cls: "ic-spin" }) + " " + esc(t("studio.running"));
    }

    const endRun = (ok) => {
      if (card) card.classList.remove("running");
      if (badge) {
        badge.className = "wf-badge ready";
        badge.textContent = ok === false ? t("studio.err_stop") : t("studio.ready");
      }
      card && card.querySelectorAll(".wf-pstep").forEach((el) => el.classList.remove("active"));
    };

    const drawer = document.getElementById("runDrawer");
    const stepsEl = document.getElementById("runSteps");
    const foot = document.getElementById("runFoot");
    document.getElementById("runTitle").textContent = `▶ ${w.name}`;
    stepsEl.innerHTML = `<div class="run-info">${esc(t("studio.starting"))}</div>`;
    if (foot) { foot.hidden = true; foot.innerHTML = ""; }
    drawer.classList.add("open");

    const url =
      `/workflows/run?slug=${encodeURIComponent(w.slug)}&brain=${encodeURIComponent(brain())}&input=${encodeURIComponent(input)}`;
    const es = new EventSource(url);
    const stepDivs = {};
    _wfActive = {
      es, card, badge, w, status: "running", result: "", stepTexts: [], brief: input, floatAck: false,
    };

    const bindClose = () => {
      // Đóng / thu nhỏ = ẨN panel, KHÔNG huỷ EventSource → server tiếp tục chạy.
      const hide = () => _wfHideDrawerKeepRun();
      const minBtn = document.getElementById("runMinimize");
      const closeBtn = document.getElementById("runClose");
      if (minBtn) minBtn.onclick = hide;
      if (closeBtn) closeBtn.onclick = hide;
      const flOpen = document.getElementById("runFloatOpen");
      if (flOpen) flOpen.onclick = () => _wfShowDrawer();
    };
    bindClose();

    const onMsg = (e) => {
      const d = JSON.parse(e.data);
      if (d.type === "start") {
        stepsEl.innerHTML = `<div class="run-info">${d.steps} ${esc(t("studio.steps"))} · workflow ${esc(d.workflow)}</div>`;
      } else if (d.type === "step_start") {
        if (card) {
          card.querySelectorAll(".wf-pstep").forEach((el) => el.classList.remove("active"));
          const ps = card.querySelector(`.wf-pstep[data-i="${d.i}"]`);
          if (ps) ps.classList.add("active");
          if (badge) badge.innerHTML = `${ic("loader", { cls: "ic-spin" })} ${esc(t("studio.step_n", { a: d.i + 1, b: w.steps.length }))}`;
        }
        const div = document.createElement("div");
        div.className = "run-step";
        div.innerHTML = `<div class="rs-head"><span class="rs-num">${d.i + 1}</span><span class="rs-agent">${esc(d.agent)}</span><span class="rs-spin"></span></div><div class="rs-task">${esc(d.task)}</div><div class="rs-out" id="rs-out-${d.i}"></div>`;
        stepsEl.appendChild(div);
        stepDivs[d.i] = div;
        if (!_wfActive.stepTexts[d.i]) _wfActive.stepTexts[d.i] = { agent: d.agent, task: d.task, text: "" };
        else {
          _wfActive.stepTexts[d.i].agent = d.agent;
          _wfActive.stepTexts[d.i].task = d.task;
        }
        stepsEl.scrollTop = stepsEl.scrollHeight;
        _wfSyncFloat();
      } else if (d.type === "step_text") {
        const out = document.getElementById(`rs-out-${d.i}`);
        if (out) {
          out.textContent += d.content;
          stepsEl.scrollTop = stepsEl.scrollHeight;
        }
        if (!_wfActive.stepTexts[d.i]) _wfActive.stepTexts[d.i] = { agent: "", task: "", text: "" };
        _wfActive.stepTexts[d.i].text += d.content || "";
      } else if (d.type === "step_tool") {
        const div = stepDivs[d.i];
        if (div) div.querySelector(".rs-head").insertAdjacentHTML("beforeend", `<span class="rs-tool">${ic("settings")} ${esc(d.tool)}</span>`);
      } else if (d.type === "step_verify") {
        const div = stepDivs[d.i];
        if (div) div.querySelector(".rs-head").insertAdjacentHTML("beforeend",
          `<span class="rs-verify" id="rs-vf-${d.i}">${ic("search")} ${esc(d.agent)} ${esc(t("studio.verifying"))}${d.attempt ? ` ${esc(t("studio.attempt_n", { n: d.attempt + 1 }))}` : ""}...</span>`);
      } else if (d.type === "step_verify_result") {
        const vf = document.getElementById(`rs-vf-${d.i}`);
        if (vf) {
          vf.className = "rs-verify " + (d.passed ? "ok" : "fail");
          vf.innerHTML = (d.passed ? ic("check", { cls: "ic-ok" }) + " " + esc(t("studio.pass")) : ic("circle-x", { cls: "ic-err" }) + " " + esc(t("studio.fail"))) + (d.reason ? ": " + esc(d.reason) : "");
          vf.removeAttribute("id");
        }
      } else if (d.type === "step_retry") {
        const out = document.getElementById(`rs-out-${d.i}`);
        if (out) out.insertAdjacentHTML("beforebegin", `<div class="rs-retry">↻ ${esc(t("studio.retry_n", { n: d.attempt }))}...</div>`);
      } else if (d.type === "step_done") {
        if (card) {
          const ps = card.querySelector(`.wf-pstep[data-i="${d.i}"]`);
          if (ps) { ps.classList.remove("active"); ps.classList.add("done"); }
        }
        const div = stepDivs[d.i];
        if (div) {
          div.classList.add("done");
          const sp = div.querySelector(".rs-spin");
          if (sp) sp.outerHTML = `<span class="rs-ok">${ic("check", { cls: "ic-ok" })}</span>`;
          if (d.verified === false) div.insertAdjacentHTML("beforeend", `<div class="rs-warn">${ic("triangle-alert", { cls: "ic-warn" })} ${esc(t("studio.verify_fail"))}</div>`);
          const out = document.getElementById(`rs-out-${d.i}`);
          if (out && !out.textContent.trim()) out.textContent = d.output || "";
          if (d.output && _wfActive.stepTexts[d.i] && !_wfActive.stepTexts[d.i].text.trim()) {
            _wfActive.stepTexts[d.i].text = d.output;
          }
        }
      } else if (d.type === "step_error") {
        const out = document.getElementById(`rs-out-${d.i}`);
        if (out) out.innerHTML += `<div class="rs-err">${ic("triangle-alert", { cls: "ic-warn" })} ${esc(d.content)}</div>`;
      } else if (d.type === "step_model") {
        const div = stepDivs[d.i];
        if (div) div.querySelector(".rs-head").insertAdjacentHTML("beforeend",
          `<span class="rs-tool">${ic("settings")} model: ${esc(d.model)}</span>`);
      } else if (d.type === "resume") {
        stepsEl.insertAdjacentHTML("beforeend", `<div class="run-info">${ic("loader")} ${esc(t("studio.resume", { n: d.reused }))}</div>`);
      } else if (d.type === "replan") {
        stepsEl.insertAdjacentHTML("beforeend", `<div class="run-info">${ic("search")} ${esc(t("studio.replan", { n: (d.added || []).length, r: d.round }))}</div>`);
      } else if (d.type === "wait_user") {
        es.close();
        _wfActive.status = "wait";
        endRun();
        const canApprove = d.code && d.task_id;
        stepsEl.insertAdjacentHTML("beforeend",
          `<div class="run-info wf-wait">${ic("triangle-alert", { cls: "ic-warn" })} ` +
          `${esc(t("studio.wait1"))} "${esc(d.node || "")}"${d.prompt ? ": " + esc(d.prompt) : ""}` +
          (canApprove
            ? `<div class="wf-wait-act"><button type="button" class="wf-approve" ` +
              `data-task="${esc(d.task_id)}" data-node="${esc(d.node || "")}" ` +
              `data-code="${esc(d.code)}">${esc(t("studio.approve"))} ${esc(d.code)}</button>` +
              `<span class="dim">${esc(t("studio.wait_warn"))}</span></div>`
            : "") +
          `</div>`);
        stepsEl.scrollTop = stepsEl.scrollHeight;
        _wfShowDrawer();
        _wfSyncFloat();
      } else if (d.type === "escalation") {
        stepsEl.insertAdjacentHTML("beforeend", `<div class="run-info">${ic("triangle-alert", { cls: "ic-warn" })} ${esc(t("studio.escalation"))} ${esc(d.reason || "")}</div>`);
      } else if (d.type === "error") {
        try { es.close(); } catch (err) {}
        _wfActive.status = "error";
        endRun(false);
        stepsEl.insertAdjacentHTML("beforeend", `<div class="run-info">${ic("circle-x", { cls: "ic-err" })} ${esc(d.content || t("studio.err_stop"))}</div>`);
        stepsEl.scrollTop = stepsEl.scrollHeight;
        _wfSyncFloat();
      } else if (d.type === "done") {
        try { es.close(); } catch (err) {}
        _wfActive.status = "done";
        _wfActive.result = d.result || (_wfActive.stepTexts.slice(-1)[0] || {}).text || "";
        endRun(true);
        _appendRunSummary(w, _wfActive.result);
        _wfSyncFloat();
      }
    };

    es.onmessage = onMsg;
    es.onerror = () => {
      if (_wfActive && (_wfActive.status === "done" || _wfActive.status === "error" || _wfActive.status === "wait")) return;
      try { es.close(); } catch (err) {}
      if (_wfActive) _wfActive.status = "error";
      endRun(false);
      _wfSyncFloat();
    };

    stepsEl.onclick = (ev) => {
      const btn = ev.target.closest ? ev.target.closest(".wf-approve") : null;
      if (btn && !btn.disabled) {
        btn.disabled = true;
        btn.textContent = t("studio.running");
        const q = new URLSearchParams({
          task_id: btn.dataset.task, node: btn.dataset.node, code: btn.dataset.code,
          slug: w.slug, brain: brain(),
        });
        const es2 = new EventSource(`/workflows/resume?${q}`);
        _wfActive.es = es2;
        _wfActive.status = "running";
        es2.onmessage = onMsg;
        es2.onerror = () => {
          if (_wfActive && (_wfActive.status === "done" || _wfActive.status === "wait")) return;
          try { es2.close(); } catch (err) {}
          if (_wfActive) _wfActive.status = "error";
          endRun(false);
          _wfSyncFloat();
        };
        return;
      }
      const a = ev.target.closest ? ev.target.closest("a[data-vault-path]") : null;
      if (a) {
        ev.preventDefault();
        const p = a.getAttribute("data-vault-path") || "";
        try {
          if (typeof window.openVaultTarget === "function") window.openVaultTarget(p);
          else location.hash = "#open=" + encodeURIComponent(p);
        } catch (err) {}
      }
    };
  }

  // ===== Workflow editor =====
  let agentsCache = [];
  async function editWorkflow(w) {
    const [ad, st] = await Promise.all([
      api(`/agents?brain=${encodeURIComponent(brain())}`),
      api("/settings"),
    ]);
    agentsCache = ad.agents || [];
    if (!agentsCache.length) { alert(t("studio.no_agents")); return; }
    const box = document.getElementById("editorBox");
    const steps = w ? JSON.parse(JSON.stringify(w.steps || [])) : [{ agent: agentsCache[0].slug, task: "" }];
    const opts = (sel) => agentsCache.map(a => `<option value="${a.slug}" ${a.slug === sel ? "selected" : ""}>${esc(a.name)}</option>`).join("");
    const optsV = (sel) => `<option value="">${esc(t("studio.no_verify"))}</option>` + agentsCache.map(a => `<option value="${a.slug}" ${a.slug === sel ? "selected" : ""}>${esc(a.name)}</option>`).join("");
    const agentName = (slug) => { const a = agentsCache.find(x => x.slug === slug); return a ? a.name : (slug || "?"); };
    const MODEL_SEP = "::";
    const uniq = (xs) => [...new Set((xs || []).filter(Boolean))];
    const provs = ((st.model || {}).providers || []).filter(p => p.agent_ok && p.configured);
    const live = await Promise.all(provs.map(p =>
      api(`/provider/models?provider=${encodeURIComponent(p.id)}` + (p.id === "openai-oauth" ? "&refresh=1" : ""))
        .then(d => uniq(d.models)).catch(() => [])));
    const nhomM = provs.map((p, i) => ({ id: p.id, label: p.label, models: uniq(live[i].concat(p.models || [])) }))
                      .filter(g => g.models.length);
    const mVal = (pid, m) => pid + MODEL_SEP + m;
    const modelOptionsHtml = [
      `<option value="">${esc(t("studio.wf_model_default"))}</option>`,
      ...nhomM.map(g => `<optgroup label="${esc(g.label)}">${g.models.map(m =>
        `<option value="${esc(mVal(g.id, m))}">${esc(m)}</option>`).join("")}</optgroup>`),
    ].join("");
    let openIdx = w ? null : 0;
    let ten = w ? (w.name || "") : "";
    let mota = w ? (w.description || "") : "";
    let nhom = w ? nhomCua(w) : NHOM_MD;
    let wfModelVal = (w && w.model)
      ? mVal(w.model_provider || "", w.model)
      : "";
    function move(i, d) {
      const j = i + d;
      if (j < 0 || j >= steps.length) return;
      captureSteps();
      const t = steps[i]; steps[i] = steps[j]; steps[j] = t;
      if (openIdx === i) openIdx = j; else if (openIdx === j) openIdx = i;
      render();
    }
    function render() {
      box.innerHTML = `
        <h3>${esc(w ? t("studio.edit") : t("studio.create"))} Workflow</h3>
        <label>${esc(t("studio.name"))}</label><input id="wfName" value="${esc(ten)}">
        <label>${esc(t("studio.desc"))}</label><input id="wfDesc" value="${esc(mota)}">
        <label>${esc(t("studio.groups"))}</label>
        <input id="wfGroup" list="wfGroupList" value="${esc(nhom)}" placeholder="${esc(t("studio.group_ph"))}">
        ${nhomDatalist(_wfState.wfs, "wfGroupList")}
        <label>${esc(t("studio.wf_model_lbl"))}</label>
        <select id="wfModel">${modelOptionsHtml}</select>
        <div class="dim" style="font-size:12px;margin-top:4px">${esc(t("studio.wf_model_note"))}</div>
        <label>${esc(t("studio.steps_label"))}</label>
        <div id="stepList"></div>
        <button class="s-btn-ghost" id="addStep">${esc(t("studio.add_step"))}</button>
        <div class="editor-actions"><button class="s-btn-ghost" id="cancelEd">${esc(t("common.cancel"))}</button><button class="s-btn" id="saveWf">${esc(t("common.save"))}</button></div>`;
      const selM = box.querySelector("#wfModel");
      if (selM) {
        selM.value = wfModelVal;
        if (wfModelVal && !selM.value && w && w.model) {
          const hit = [...selM.options].find(o => o.value.split(MODEL_SEP).slice(1).join(MODEL_SEP) === w.model);
          if (hit) selM.value = hit.value;
        }
      }
      const sl = box.querySelector("#stepList"); sl.innerHTML = "";
      steps.forEach((st, i) => {
        const open = i === openIdx;
        const row = document.createElement("div"); row.className = "step-row" + (open ? " open" : "");
        const sum = (st.task || "").replace(/\s+/g, " ").trim();
        row.innerHTML = `
          <div class="step-header">
            <span class="step-num">${i + 1}</span>
            <span class="step-sum">${esc(agentName(st.agent))}${sum ? ` · ${esc(sum)}` : ""}</span>
            <select class="st-agent">${opts(st.agent)}</select>
            <button class="st-move" data-d="-1" title="${esc(t("studio.up"))}" ${i === 0 ? "disabled" : ""}>↑</button>
            <button class="st-move" data-d="1" title="${esc(t("studio.down"))}" ${i === steps.length - 1 ? "disabled" : ""}>↓</button>
            <button class="st-del" title="${esc(t("studio.del_step"))}">${ic("x")}</button>
          </div>
          <div class="step-body">
            <textarea class="st-task" rows="3" placeholder="${esc(t("studio.task_ph"))}">${esc(st.task)}</textarea>
            <div class="st-verify">
              <span class="stv-lbl">${esc(t("studio.verify_lbl"))}</span>
              <select class="st-verify-agent">${optsV(st.verify_agent || "")}</select>
              <input class="st-retries" type="number" min="0" max="5" value="${st.max_retries != null ? st.max_retries : 1}">
              <span class="stv-lbl">${esc(t("studio.times"))}</span>
            </div>
          </div>`;
        row.querySelector(".step-header").onclick = (e) => {
          if (e.target.closest("button, select")) return;
          captureSteps(); openIdx = open ? null : i; render();
        };
        row.querySelectorAll(".st-move").forEach(b => { b.onclick = () => move(i, parseInt(b.dataset.d, 10)); });
        row.querySelector(".st-del").onclick = () => {
          captureSteps();
          steps.splice(i, 1);
          if (!steps.length) steps.push({ agent: agentsCache[0].slug, task: "" });
          if (openIdx !== null) { if (openIdx === i) openIdx = null; else if (openIdx > i) openIdx--; }
          render();
        };
        sl.appendChild(row);
      });
      box.querySelector("#addStep").onclick = () => { captureSteps(); steps.push({ agent: agentsCache[0].slug, task: "" }); openIdx = steps.length - 1; render(); };
      box.querySelector("#cancelEd").onclick = () => editor.classList.remove("open");
      box.querySelector("#saveWf").onclick = async () => {
        captureSteps();
        if (!ten.trim()) return alert(t("studio.need_name"));
        const raw = (box.querySelector("#wfModel") || {}).value || "";
        let mProv = "", mName = "";
        if (raw.includes(MODEL_SEP)) {
          const i = raw.indexOf(MODEL_SEP);
          mProv = raw.slice(0, i); mName = raw.slice(i + MODEL_SEP.length);
        }
        await api("/workflows", { method: "POST", body: fd({ name: ten.trim(), description: mota,
          group: nhom.trim() || NHOM_MD, steps: JSON.stringify(steps),
          status: w ? w.status : "active", slug: w ? w.slug : "", brain: brain(),
          model: mName, model_provider: mProv }) });
        editor.classList.remove("open"); loadWorkflows();
      };
    }
    function captureSteps() {
      const oNe = box.querySelector("#wfName"), oMo = box.querySelector("#wfDesc"), oNh = box.querySelector("#wfGroup");
      const oMd = box.querySelector("#wfModel");
      if (oNe) ten = oNe.value;
      if (oMo) mota = oMo.value;
      if (oNh) nhom = oNh.value;
      if (oMd) wfModelVal = oMd.value;
      box.querySelectorAll(".step-row").forEach((r, i) => {
        const va = r.querySelector(".st-verify-agent").value;
        steps[i] = { agent: r.querySelector(".st-agent").value, task: r.querySelector(".st-task").value };
        if (va) { steps[i].verify_agent = va; steps[i].max_retries = parseInt(r.querySelector(".st-retries").value, 10) || 0; }
      });
    }
    render(); editor.classList.add("open");
  }

  // ===== Agents =====
  const _agState = { cat: "ALL", q: "", agents: [] };

  async function loadAgents() {
    _injectStudioCss();
    const panel = document.getElementById("panel-agents");
    panel.innerHTML = `<div class="empty">${esc(t("common.loading"))}</div>`;
    const d = await api(`/agents?brain=${encodeURIComponent(brain())}`);
    _agState.agents = d.agents || [];
    _sel.agent.clear();   // nạp lại trang là làm mới lựa chọn
    refreshStats();
    renderAgentUI();
  }

  const _agFiltered = () => locTheoNhom(_agState.agents, _agState,
    (a) => `${a.name} ${a.slug} ${a.role || ""}`);

  function renderAgentUI() {
    const panel = document.getElementById("panel-agents");
    const all = _agState.agents;
    panel.innerHTML = `<div class="panel-bar"><h3>Agents</h3><div class="pb-actions"><button class="s-btn-ghost" id="agSelAll" title="${esc(t("studio.selall_title"))}">${esc(t("studio.selall"))}</button><button class="s-btn-ghost" id="agDl" disabled title="${esc(t("studio.dl_title"))}">${esc(t("studio.dl_sel"))}</button><button class="s-btn-ghost" id="agImport">${esc(t("studio.import"))}</button><button class="s-btn" id="newAgent">+ Agent</button></div></div>
      ${all.length ? khungNhomHtml(all, _agState, { bodyId: "agCards", bodyCls: "cards",
                                                    searchId: "agSearch", searchPh: t("studio.ag_search_ph") })
      : `<div class="empty">${esc(t("studio.ag_empty"))}</div>`}`;
    document.getElementById("newAgent").onclick = () => editAgent(null);
    document.getElementById("agImport").onclick = () => importItems(loadAgents);
    document.getElementById("agDl").onclick = () => taiDaChon("agent");
    document.getElementById("agSelAll").onclick = () =>
      chonTatCa("agent", "agDl", "ag-sel", _agFiltered().map(a => a.slug));
    capNhatNutTai("agent", "agDl");
    if (!all.length) return;
    ganKhungNhom(panel, _agState, { searchId: "agSearch", veLai: renderAgentUI, veDanhSach: renderAgentList });
    renderAgentList();
  }

  function renderAgentList() {
    const cards = document.getElementById("agCards"); if (!cards) return;
    const list = _agFiltered();
    datSoLuong(document.getElementById("panel-agents"), list.length + " agent");
    if (!list.length) { cards.innerHTML = `<div class="empty">${esc(t("studio.ag_no_match"))}</div>`; return; }
    cards.innerHTML = "";
    list.forEach(a => {
      const div = document.createElement("div"); div.className = "ag-card";
      div.innerHTML = `<div class="ag-name"><input type="checkbox" class="ag-sel" data-slug="${esc(a.slug)}" title="${esc(t("studio.sel_one"))}"> ${ic("bot")} ${esc(a.name)} <span class="ag-model">${esc(a.model_provider ? a.model_provider + "/" : "")}${esc(a.model || "")}</span></div><div class="ag-role">${esc(a.role)}</div><div class="ag-skills">${(a.skills || []).map(s => `<span class="chip-skill">${esc(s)}</span>`).join("") || `<span class="dim">${esc(t("studio.no_skills"))}</span>`}</div><div class="ag-group">${ic("folder-open")} ${esc(nhomCua(a))}</div><div class="wf-actions"><button class="s-btn-ghost edit">${esc(t("common.edit"))}</button><button class="s-btn-ghost exp" title="${esc(t("studio.export_title"))}">${esc(t("studio.export"))}</button><button class="s-btn-ghost del">${esc(t("common.delete"))}</button></div>`;
      noiSel("agent", "agDl", div.querySelector(".ag-sel"), a.slug);
      div.querySelector(".exp").onclick = () => exportItem("agent", a.slug);
      div.querySelector(".edit").onclick = () => editAgent(a);
      div.querySelector(".del").onclick = async () => { if (confirm(t("studio.del_ag", { ten: a.name }))) { await api("/agents/delete", { method: "POST", body: fd({ slug: a.slug, brain: brain() }) }); loadAgents(); } };
      cards.appendChild(div);
    });
  }

  // Giá trị một dòng trong ô chọn model của agent: "<provider>::<model>". Phải mang theo
  // NHÀ chứ không chỉ tên model, vì cùng một tên có ở hai nhà (gemini-2.5-pro: Gemini CLI
  // lẫn Gemini API; claude-*: Claude Code lẫn Anthropic API) - lưu mỗi tên là server phải
  // đoán, mà đoán sai thì chạy nhầm nhà và nhầm cả hoá đơn.
  const MODEL_SEP = "::";

  async function editAgent(a) {
    const [sd, st] = await Promise.all([
      api(`/skills?brain=${encodeURIComponent(brain())}`),
      api("/settings"),
    ]);
    const skills = sd.skills || [];
    const uniq = (xs) => [...new Set((xs || []).filter(Boolean))];
    // CÙNG nguồn với trình chọn model chính (/settings → model.providers), nên thêm nhà mới
    // ở trang Models là ô này có ngay. Lọc `agent_ok`: server chỉ dựng nổi engine agent cho
    // một số nhà (xem AGENT_PROVIDERS), bày thêm là hứa suông. Lọc `configured`: chưa cắm
    // key thì chọn vào cũng không chạy.
    const provs = ((st.model || {}).providers || []).filter(p => p.agent_ok && p.configured);
    // Danh sách LIVE cho nhà có catalog rỗng/đổi liên tục (Codex, Gemini CLI, Groq...).
    // Hỏng một nhà thì chỉ nhà đó rơi về catalog, không kéo cả ô chọn chết theo.
    const live = await Promise.all(provs.map(p =>
      api(`/provider/models?provider=${encodeURIComponent(p.id)}` + (p.id === "openai-oauth" ? "&refresh=1" : ""))
        .then(d => uniq(d.models)).catch(() => [])));
    const nhom = provs.map((p, i) => ({ id: p.id, label: p.label, models: uniq(live[i].concat(p.models || [])) }))
                      .filter(g => g.models.length);
    const val = (pid, m) => pid + MODEL_SEP + m;
    // Agent đang lưu một model không còn trong danh sách nào (nhà đã ngắt key, model bị gỡ):
    // vẫn bày ra để mở form lên KHÔNG âm thầm đổi model của agent thành "Mặc định".
    const dangCo = a && a.model && !nhom.some(g => (!a.model_provider || g.id === a.model_provider) && g.models.includes(a.model));
    const currentOnly = dangCo
      ? `<optgroup label="${esc(t("studio.model_saved"))}"><option value="${esc(val(a.model_provider || "", a.model))}">${esc(a.model)} ${esc(t("studio.saved_suffix"))}</option></optgroup>` : "";
    const modelOptions = (g) =>
      `<optgroup label="${esc(g.label)}">${g.models.map(m => `<option value="${esc(val(g.id, m))}">${esc(m)}</option>`).join("")}</optgroup>`;
    const box = document.getElementById("editorBox");
    box.innerHTML = `<h3>${esc(a ? t("studio.edit") : t("studio.create"))} Agent</h3>
      <label>${esc(t("studio.name"))}</label><input id="agName" value="${esc(a ? a.name : "")}">
      <label>${esc(t("studio.role"))}</label><input id="agRole" value="${esc(a ? a.role : "")}">
      <label>${esc(t("studio.groups"))}</label>
      <input id="agGroup" list="agGroupList" value="${esc(a ? nhomCua(a) : NHOM_MD)}" placeholder="${esc(t("studio.group_ph"))}">
      ${nhomDatalist(_agState.agents, "agGroupList")}
      <label>${esc(t("studio.sys_prompt"))}</label><textarea id="agPrompt" rows="4">${esc(a ? (a.prompt || "") : "")}</textarea>
      <label>Skills</label>
      ${skills.length ? `<div class="sp-box">
        <div class="sp-bar"><input id="spSearch" placeholder="${esc(t("studio.sp_search_ph"))}">
          <span class="sp-count" id="spCount"></span>
          <button type="button" class="s-btn-ghost sp-clear" id="spClear">${esc(t("studio.sp_clear"))}</button></div>
        <div class="sp-groups" id="skillPick"></div>
      </div>` : `<div class="skill-pick"><span class="dim">${esc(t("studio.sp_none"))}</span></div>`}
      <label>Model</label><select id="agModel">
        <option value="">${esc(t("studio.model_default"))}</option>
        ${currentOnly}
        ${nhom.map(modelOptions).join("")}
      </select>
      <div class="dim" style="font-size:12px;margin-top:4px">${esc(nhom.length
        ? t("studio.model_hint")
        : t("studio.model_none"))}</div>
      <div class="editor-actions"><button class="s-btn-ghost" id="cancelEd">${esc(t("common.cancel"))}</button><button class="s-btn" id="saveAg">${esc(t("common.save"))}</button></div>`;
    if (a && a.model) {
      const sel = box.querySelector("#agModel");
      sel.value = val(a.model_provider || "", a.model);
      // Agent CŨ lưu mỗi tên model (chưa có trường nhà): dò dòng đầu tiên trùng tên để form
      // mở lên vẫn hiện đúng model đang chạy, thay vì nhảy về "Mặc định" rồi bấm Lưu là mất.
      if (!sel.value) {
        const hit = [...sel.options].find(o => o.value.split(MODEL_SEP).slice(1).join(MODEL_SEP) === a.model);
        if (hit) sel.value = hit.value;
      }
    }
    // Trạng thái chọn giữ trong Set, DOM chỉ là HÌNH CHIẾU của nó. Đây là chỗ dễ hỏng nhất của
    // khung có bộ lọc: vẽ lại theo bộ lọc rồi lúc lưu mới đi đọc DOM thì mọi skill đang bị lọc
    // ra khỏi màn hình sẽ mất tick, im lặng, và người dùng chỉ phát hiện sau khi agent chạy sai.
    const chosen = new Set(a ? (a.skills || []) : []);
    renderSkillPick(box, skills, chosen);
    box.querySelector("#cancelEd").onclick = () => editor.classList.remove("open");
    box.querySelector("#saveAg").onclick = async () => {
      const name = box.querySelector("#agName").value.trim(); if (!name) return alert(t("studio.need_name"));
      const sk = [...chosen].join(",");
      const raw = box.querySelector("#agModel").value;
      const cut = raw.indexOf(MODEL_SEP);
      const mProv = cut === -1 ? "" : raw.slice(0, cut);
      const mName = cut === -1 ? raw : raw.slice(cut + MODEL_SEP.length);
      await api("/agents", { method: "POST", body: fd({ name, role: box.querySelector("#agRole").value,
        group: box.querySelector("#agGroup").value.trim() || NHOM_MD,
        prompt: box.querySelector("#agPrompt").value, skills: sk, model: mName, model_provider: mProv,
        slug: a ? a.slug : "", brain: brain() }) });
      editor.classList.remove("open"); loadAgents();
    };
    editor.classList.add("open");
  }

  // ===== Khung chọn skill trong màn sửa Agent =====
  // Brain thật đang có 55+ skill, nên danh sách checkbox phẳng là dò bằng mắt qua cả trang.
  // Ở đây: ô tìm + gom nhóm theo field `group` sẵn có của skill (đúng nhóm mà trang Skills
  // dùng, không đẻ cách phân loại thứ hai), mỗi nhóm sổ ra thu vào được.
  function renderSkillPick(box, skills, chosen) {
    const host = box.querySelector("#skillPick");
    if (!host) return;
    const countEl = box.querySelector("#spCount");
    const searchEl = box.querySelector("#spSearch");
    // Nhóm nào đang có skill được tick thì mở sẵn: người sửa agent quan tâm cái đang bật trước.
    const openGroups = new Set(skills.filter(s => chosen.has(s.slug)).map(s => s.group || "Chung"));
    let q = "";

    const draw = () => {
      const nq = _spNoAccent(q.trim());
      const hop = (s) => !nq || _spNoAccent(`${s.name} ${s.slug} ${s.group || ""} ${s.description || ""}`).includes(nq);
      const groups = new Map();
      skills.forEach(s => {
        if (!hop(s)) return;
        const g = s.group || "Chung";
        if (!groups.has(g)) groups.set(g, []);
        groups.get(g).push(s);
      });
      if (countEl) countEl.textContent = t("studio.sp_count", { a: chosen.size, b: skills.length });
      if (!groups.size) { host.innerHTML = `<div class="dim sp-empty">${esc(t("studio.sp_empty", { q }))}</div>`; return; }
      host.innerHTML = "";
      [...groups.keys()].sort((x, y) => x.localeCompare(y, LOC())).forEach(g => {
        const list = groups.get(g);
        const nSel = list.filter(s => chosen.has(s.slug)).length;
        // Đang tìm thì mọi nhóm còn khớp đều sổ ra - lọc xong mà vẫn phải bấm mở từng nhóm
        // thì ô tìm chẳng đỡ được gì.
        const open = !!nq || openGroups.has(g);
        const wrap = document.createElement("div");
        wrap.className = "sp-g" + (open ? " open" : "");
        wrap.innerHTML = `<button type="button" class="sp-g-head">
            <span class="sp-g-caret">${ic("chevron-right")}</span>
            <span class="sp-g-name">${esc(g)}</span>
            <span class="sp-g-n">${nSel ? `${nSel}/${list.length}` : list.length}</span>
          </button><div class="sp-g-body"></div>`;
        const body = wrap.querySelector(".sp-g-body");
        list.forEach(s => {
          const lb = document.createElement("label");
          lb.className = "sp";
          lb.title = s.description || s.name;
          lb.innerHTML = `<input type="checkbox" value="${esc(s.slug)}"${chosen.has(s.slug) ? " checked" : ""}> <span>${esc(s.name)}</span>`;
          lb.querySelector("input").onchange = (e) => {
            if (e.target.checked) { chosen.add(s.slug); openGroups.add(g); } else chosen.delete(s.slug);
            // Vẽ lại để con số của nhóm và ô đếm khớp ngay; Set là nguồn sự thật nên an toàn.
            draw();
          };
          body.appendChild(lb);
        });
        wrap.querySelector(".sp-g-head").onclick = () => {
          if (openGroups.has(g)) openGroups.delete(g); else openGroups.add(g);
          wrap.classList.toggle("open");
        };
        host.appendChild(wrap);
      });
    };

    if (searchEl) searchEl.oninput = () => { q = searchEl.value; draw(); };
    const clearBtn = box.querySelector("#spClear");
    if (clearBtn) clearBtn.onclick = () => { chosen.clear(); draw(); };
    draw();
  }

  // ===== Skills (cột nhóm + tìm kiếm + bật/tắt) =====
  const _skState = { cat: "ALL", q: "", skills: [] };

  // CSS tiêm một lần cho CẢ BA trang Studio: phần `.gr*` là khung nhóm dùng chung (cột nhóm +
  // ô tìm), phần `.sk2*`/`.ag-group`/`.wf-group` là thẻ riêng của từng trang.
  function _injectStudioCss() {
    if (window._skCss) return; window._skCss = true;
    const css = `
    .gr{display:flex;gap:16px;align-items:flex-start}
    .gr-side{width:210px;flex:none;border:1px solid var(--hairline);border-radius:10px;padding:8px;max-height:72vh;overflow:auto}
    .gr-side .sec{font-size:12px;letter-spacing:.08em;color:var(--text3);padding:8px 10px 4px;text-transform:uppercase}
    .gr-cat{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:7px 10px;border-radius:7px;cursor:pointer;font-size:15px;color:var(--text)}
    .gr-cat:hover{background:rgba(120,180,255,.08)} .gr-cat.sel{background:var(--info-wash);color:var(--info-ink)}
    .gr-cat .n{color:var(--text3);font-size:13px;flex:none}
    .gr-main{flex:1;min-width:0}
    .gr-bar{display:flex;gap:10px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
    .gr-bar h4{margin:0;font-size:17px;color:var(--text)} .gr-bar .cnt{color:var(--text3);font-size:14px}
    .gr-bar input{flex:1;min-width:160px;max-width:340px;padding:7px 11px;border-radius:8px;border:1px solid var(--hairline);background:var(--field-bg);color:var(--text);font-size:15px;outline:none}
    /* Nhãn nhóm trên thẻ agent và hàng workflow: nhìn thẻ là biết nó thuộc nhóm nào, khỏi phải
       mở form ra xem. Cùng biểu tượng thư mục với dòng nhóm ở thẻ skill. */
    .ag-group{color:var(--text3);font-size:13px;margin-top:7px;display:flex;align-items:center;gap:5px}
    .wf-group{color:var(--text3);font-size:13px;display:inline-flex;align-items:center;gap:4px;flex:none}
    .sk2-selwrap{display:inline-flex;align-items:center;gap:4px;font-size:12px;color:var(--text3);cursor:pointer;white-space:nowrap}
    .sk2-list{display:flex;flex-direction:column;gap:8px}
    .sk2-card{display:flex;gap:12px;align-items:flex-start;padding:11px 13px;border:1px solid var(--hairline);border-radius:10px}
    .sk2-card:hover{border-color:var(--info-line);background:var(--info-wash)}
    .sk2-card.off{opacity:.5} .sk2-tog{flex:none;margin-top:3px;width:16px;height:16px;cursor:pointer;accent-color:var(--accent)}
    .sk2-info{flex:1;min-width:0} .sk2-info .nm{color:var(--text);font-size:15px;font-weight:600}
    .sk2-info .ds{color:var(--text3);font-size:14px;margin-top:3px;line-height:1.45}
    .sk2-info .gp{color:var(--text3);font-size:13px;margin-top:4px}
    .sk2-act{display:flex;gap:5px;opacity:0;transition:.15s;flex:none} .sk2-card:hover .sk2-act{opacity:1}
    .sk2-act button{background:var(--surface-2);border:1px solid var(--hairline);color:var(--text2);border-radius:6px;cursor:pointer;font-size:13px;padding:3px 9px} .sk2-act button:hover{color:var(--text-hi);border-color:rgba(120,180,255,.5)}
    .sk2-act button.danger:hover{color:var(--red);border-color:rgba(255,120,120,.5)}
    .wf-run-modal{position:fixed;inset:0;z-index:3200;display:none;align-items:center;justify-content:center;
      background:rgba(8,12,18,.58);backdrop-filter:blur(4px);padding:20px;box-sizing:border-box}
    .wf-run-modal.open{display:flex}
    .wf-run-card{width:min(720px,92vw);max-height:90vh;display:flex;flex-direction:column;
      background:var(--bg2,#141820);border:1px solid var(--border,rgba(255,255,255,.12));border-radius:12px;
      box-shadow:0 20px 60px rgba(0,0,0,.45);overflow:hidden}
    .wf-run-head{display:flex;gap:12px;align-items:flex-start;padding:16px 18px 10px;border-bottom:1px solid var(--hairline,rgba(255,255,255,.08))}
    .wf-run-head h3{margin:0;font-size:17px;color:var(--text);font-weight:650}
    .wf-run-desc{margin:6px 0 0;font-size:13px;color:var(--text3);line-height:1.4}
    .wf-run-x{margin-left:auto;width:32px;height:32px;border:0;border-radius:8px;background:transparent;color:var(--text2);font-size:22px;cursor:pointer;line-height:1}
    .wf-run-x:hover{background:var(--surface-2);color:var(--text)}
    .wf-run-body{padding:14px 18px;overflow:auto;display:flex;flex-direction:column;gap:6px}
    .wf-run-body label{font-size:13px;color:var(--text2);margin-top:6px}
    .wf-run-body label .req{color:var(--red,#e07070)}
    .wf-run-body textarea{width:100%;box-sizing:border-box;resize:vertical;min-height:52px;padding:10px 12px;
      border-radius:8px;border:1px solid var(--hairline);background:var(--field-bg,var(--bg));color:var(--text);
      font:inherit;font-size:14px;line-height:1.45}
    .wf-run-body textarea:focus{outline:none;border-color:var(--info-line,rgba(120,180,255,.5))}
    .wf-run-preview{margin-top:10px;border:1px solid var(--hairline);border-radius:8px;padding:8px 10px}
    .wf-run-preview summary{cursor:pointer;color:var(--text2);font-size:13px}
    .wf-run-preview pre{margin:8px 0 0;white-space:pre-wrap;word-break:break-word;font-size:12px;color:var(--text3);line-height:1.45}
    .wf-run-err{margin:8px 0 0;color:var(--red,#e07070);font-size:13px}
    .wf-run-draft-hint{margin:0 0 4px;padding:8px 10px;border-radius:8px;font-size:12.5px;line-height:1.4;
      color:var(--text2);background:var(--surface-2,rgba(127,127,127,.1));border:1px solid var(--border)}
    .wf-run-foot{display:flex;justify-content:flex-end;gap:8px;padding:12px 18px;border-top:1px solid var(--hairline)}
    .sysb{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600;letter-spacing:.02em;color:var(--link-ink);background:var(--info-wash);border:1px solid var(--info-line);vertical-align:2px}
    .sk-usage{font-size:11px;color:var(--text3);margin-left:8px}
    .sk-stale{opacity:.75;font-style:italic;cursor:help}
    /* ===== Mobile (<=860px) ===== xep DOC: nhom thanh dai chip cuon ngang o tren, danh sach
       full-width ben duoi (truoc day cot nhom 210px bop cot con lai con ~150px -> chu vo tung
       tu). Nut thao tac luon hien (truoc day opacity:0 + chi hien khi :hover -> tren dien
       thoai khong co hover nen Sua/Xuat/Xoa khong bao gio bam duoc). */
    @media (max-width:860px){
      .gr{flex-direction:column;gap:12px}
      .gr-side{width:auto;max-height:none;display:flex;flex-direction:row;gap:6px;padding:6px;
        overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}
      .gr-side::-webkit-scrollbar{height:0}
      .gr-side .sec{display:none}
      .gr-cat{flex:none;padding:8px 13px;border:1px solid var(--hairline);
        border-radius:999px;white-space:nowrap}
      .gr-cat .n{padding:1px 6px;border-radius:9px;background:var(--surface-3)}
      .gr-cat.sel{border-color:var(--info-line)}
      .gr-bar input{max-width:none;font-size:16px}   /* 16px: chan iOS tu zoom khi focus */
      .sk2-tog{width:20px;height:20px;margin-top:2px}  /* vung cham lon hon */
      .sk2-card{flex-wrap:wrap;padding:12px 13px}
      .sk2-info .nm{font-size:16px}
      .sk2-act{flex:1 1 100%;opacity:1;margin-top:11px;padding-top:11px;gap:8px;
        border-top:1px solid var(--surface-2);justify-content:flex-end}
      .sk2-act button{padding:7px 14px;font-size:14px}
    }`;
    const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
  }

  async function loadSkills() {
    _injectStudioCss();
    const panel = document.getElementById("panel-skills");
    panel.innerHTML = `<div class="empty">${esc(t("common.loading"))}</div>`;
    let d; try { d = await api(`/skills?brain=${encodeURIComponent(brain())}`); } catch (e) { panel.innerHTML = `<div class="empty">${esc(t("studio.sk_load_err"))}</div>`; return; }
    refreshStats();
    _skState.skills = d.skills || [];
    _sel.skill.clear();   // nạp lại là làm mới lựa chọn (danh sách có thể đã đổi)
    renderSkillUI();
  }

  const _skFiltered = () => locTheoNhom(_skState.skills, _skState,
    (s) => `${s.name} ${s.slug} ${s.description || ""}`);

  function renderSkillUI() {
    const panel = document.getElementById("panel-skills");
    const all = _skState.skills;
    const enabledN = all.filter(s => s.enabled !== false).length;
    panel.innerHTML = `
      <div class="panel-bar"><h3>Skills <span class="dim">${enabledN}/${all.length} ${esc(t("studio.on_count"))} · ${esc(t("studio.source"))} <code>skills/</code></span></h3>
        <div class="pb-actions"><button class="s-btn-ghost" id="skSelAll" title="${esc(t("studio.selall_sk_title"))}">${esc(t("studio.selall"))}</button><button class="s-btn-ghost" id="skDl" disabled title="${esc(t("studio.dl_title"))}">${esc(t("studio.dl_sel"))}</button><button class="s-btn-ghost" id="skImport">${esc(t("studio.import"))}</button><button class="s-btn" id="skNew">+ Skill</button></div></div>
      ${all.length ? khungNhomHtml(all, _skState, { bodyId: "skList", bodyCls: "sk2-list",
                                                    searchId: "skSearch", searchPh: t("studio.sk_search_ph") })
      : `<div class="empty">${esc(t("studio.sk_empty"))}</div>`}`;
    document.getElementById("skNew").onclick = () => openSkillForm(null);
    document.getElementById("skImport").onclick = () => importItems(loadSkills);
    document.getElementById("skDl").onclick = () => taiDaChon("skill");
    // Chọn tất cả = toàn bộ danh sách ĐANG HIỆN (đúng nhóm + đúng ô tìm), trừ skill hệ
    // thống - chúng không xuất được (server bỏ qua) vì brain nào cũng có sẵn theo app.
    document.getElementById("skSelAll").onclick = () =>
      chonTatCa("skill", "skDl", "sk2-sel", _skFiltered().filter(s => !s.system).map(s => s.slug));
    capNhatNutTai("skill", "skDl");
    if (!all.length) return;
    ganKhungNhom(panel, _skState, { searchId: "skSearch", veLai: renderSkillUI, veDanhSach: renderSkillList });
    renderSkillList();
  }

  function renderSkillList() {
    const box = document.getElementById("skList"); if (!box) return;
    const list = _skFiltered();
    datSoLuong(document.getElementById("panel-skills"), list.length + " skill");
    if (!list.length) { box.innerHTML = `<div class="empty">${esc(t("studio.sk_no_match"))}</div>`; return; }
    box.innerHTML = "";
    list.forEach(s => {
      const on = s.enabled !== false;
      const div = document.createElement("div"); div.className = "sk2-card" + (on ? "" : " off");
      const sysBadge = s.system ? ` <span class="sysb" title="${esc(t("studio.sys_title"))}">${esc(t("studio.sys"))}</span>` : "";
      // Telemetry: use_count là tín hiệu DƯƠNG một chiều. Skill nạp native qua .claude/skills
      // không đi qua bộ đếm, nên "chưa thấy dùng" là tham khảo, KHÔNG phải phán quyết.
      let usageHtml = "";
      if (s.use_count > 0) {
        const when = s.last_used_at ? new Date(s.last_used_at * 1000).toLocaleDateString(LOC()) : "";
        usageHtml = ` · <span class="sk-usage">${esc(t("studio.used", { n: s.use_count }))}${when ? ", " + esc(t("studio.last_used")) + " " + when : ""}</span>`;
      } else if (s.stale) {
        usageHtml = ` · <span class="sk-usage sk-stale" title="${esc(t("studio.unused_title"))}">${esc(t("studio.unused"))}</span>`;
      }
      div.innerHTML = `<input type="checkbox" class="sk2-tog" ${on ? "checked" : ""} title="${esc(on ? t("studio.tog_on") : t("studio.tog_off"))}">
        <div class="sk2-info"><div class="nm">${ic("puzzle")} ${esc(s.name)}${sysBadge}</div><div class="ds">${esc(s.description || "")}</div><div class="gp">${ic("folder-open")} ${esc(s.group || "Chung")} · ${esc(s.slug)}${s.source === ".agents" ? " · .agents" : ""}${usageHtml}</div></div>
        <div class="sk2-act">${s.system ? "" : `<label class="sk2-selwrap" title="${esc(t("studio.sel_one"))}"><input type="checkbox" class="sk2-sel" data-slug="${esc(s.slug)}"> ${esc(t("studio.pick"))}</label>`}<button class="edit">${esc(t("common.edit"))}</button>${s.system ? "" : `<button class="exp" title="${esc(t("studio.export_title"))}">${esc(t("studio.export"))}</button><button class="del danger">${esc(t("common.delete"))}</button>`}</div>`;
      div.querySelector(".sk2-tog").onchange = (e) => toggleSkill(s, e.target.checked);
      const selBox = div.querySelector(".sk2-sel");
      if (selBox) noiSel("skill", "skDl", selBox, s.slug);
      div.querySelector(".edit").onclick = () => openSkillForm(s.slug);
      const expBtn = div.querySelector(".exp");
      if (expBtn) expBtn.onclick = () => exportItem("skill", s.slug);
      const delBtn = div.querySelector(".del");
      if (delBtn) delBtn.onclick = () => deleteSkill(s.slug, s.name);
      box.appendChild(div);
    });
  }

  async function toggleSkill(s, enabled) {
    const r = await api("/skills/toggle", { method: "POST", body: fd({ slug: s.slug, enabled: enabled ? "1" : "0", brain: brain() }) });
    if (r && r.error) { alert(t("studio.toggle_err") + " " + r.error); }
    s.enabled = enabled;
    renderSkillUI(); refreshStats();
  }

  async function openSkillForm(slug) {
    const panel = document.getElementById("panel-skills");
    let sk = { slug: "", name: "", group: "Chung", description: "", body: "" };
    if (slug) { try { sk = await api(`/skills/get?slug=${encodeURIComponent(slug)}&brain=${encodeURIComponent(brain())}`); } catch (e) {} }
    const groupOpts = [...new Set(_skState.skills.map(s => s.group || "Chung"))].map(g => `<option value="${esc(g)}">`).join("");
    panel.innerHTML = `<div class="panel-bar"><h3>${esc(slug ? t("studio.sk_edit") : t("studio.sk_new"))}</h3></div>
      <div style="display:flex;flex-direction:column;gap:12px;max-width:660px">
        <div><label>${esc(t("studio.sk_name"))}</label><input id="skName" class="js-input" value="${esc(sk.name)}" placeholder="${esc(t("studio.sk_name_ph"))}"></div>
        <div><label>${esc(t("studio.groups"))}</label><input id="skGroup" class="js-input" list="skGroupList" value="${esc(sk.group || "Chung")}" placeholder="${esc(t("studio.sk_group_ph"))}">
          <datalist id="skGroupList">${groupOpts}</datalist></div>
        <div><label>${esc(t("studio.sk_desc"))}</label><textarea id="skDesc" class="js-input" style="min-height:60px">${esc(sk.description || "")}</textarea></div>
        <div><label>${esc(t("studio.sk_body"))}</label><textarea id="skBody" class="js-input" style="min-height:200px;font-family:ui-monospace,monospace">${esc(sk.body || "")}</textarea></div>
        <div style="display:flex;gap:10px"><button class="s-btn" id="skSave">${ic("save")} ${esc(t("common.save"))}</button><button class="s-btn-ghost" id="skCancel">${esc(t("common.cancel"))}</button></div>
      </div>`;
    panel.querySelector("#skCancel").onclick = () => loadSkills();
    panel.querySelector("#skSave").onclick = async () => {
      const name = panel.querySelector("#skName").value.trim();
      if (!name) { alert(t("studio.need_sk_name")); return; }
      const b = panel.querySelector("#skSave"); b.disabled = true; b.textContent = t("settings.saving");
      await api("/skills", { method: "POST", body: fd({
        name, group: panel.querySelector("#skGroup").value.trim() || "Chung",
        description: panel.querySelector("#skDesc").value, body: panel.querySelector("#skBody").value,
        slug: sk.slug || "", brain: brain() }) });
      loadSkills();
    };
  }

  async function deleteSkill(slug, name) {
    if (!confirm(t("studio.del_sk", { ten: name, slug }))) return;
    await api("/skills/delete", { method: "POST", body: fd({ slug, brain: brain() }) });
    loadSkills();
  }
})();
