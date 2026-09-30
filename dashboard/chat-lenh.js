// Lệnh "/" hệ thống của khung chat: /help /status /model /brain /retry /usage /tasks
// /compact /plan /memory /export /goal. Nhận diện lệnh nằm ở chat-slash.js.
(function () {
  "use strict";

  var GOAL_TOI_DA = 8;
  var GOAL_RE = /<!--\s*JAVIS_GOAL:\s*([\s\S]*?)\s*-->/g;

  function tachMucTieu(text) {
    var s = String(text == null ? "" : text);
    if (s.indexOf("JAVIS_GOAL") < 0) return { clean: s, goal: null };
    var goal = null;
    var clean = s.replace(GOAL_RE, function (_m, j) {
      goal = null;
      try {
        var o = JSON.parse(j);
        if (o && typeof o.done === "boolean") {
          goal = { done: o.done, left: String(o.left || "").trim().slice(0, 300) };
        }
      } catch (e) { /* khối hỏng: bỏ */ }
      return "";
    }).replace(/\n{3,}/g, "\n\n").trim();
    return { clean: clean, goal: goal };
  }

  function chuanSo(s) { return String(s || "").toLowerCase().replace(/\s+/g, " ").trim(); }

  function quyetDinhVongTiep(st, ket) {
    ket = ket || {};
    if (ket.loi) return { act: "dung", ly: "loi" };
    if (ket.hoiLai) return { act: "dung", ly: "hoi_lai" };
    var m = ket.marker;
    if (!m) return { act: "dung", ly: "khong_bao" };
    if (m.done) return { act: "dung", ly: "dat" };
    if (st.vong >= st.toiDa) return { act: "dung", ly: "het_vong" };
    if (st.left && m.left && chuanSo(st.left) === chuanSo(m.left)) {
      return { act: "dung", ly: "khong_tien_trien", left: m.left };
    }
    return { act: "tiep", left: m.left || "" };
  }

  function gonSo(n) {
    n = +n || 0;
    if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1) + "M";
    if (n >= 1e3) return (n / 1e3).toFixed(n >= 1e4 ? 0 : 1) + "k";
    return String(Math.round(n));
  }
  function tien(x) { return "$" + (+x || 0).toFixed(2); }
  function cat(s, n) { s = String(s || ""); return s.length > n ? s.slice(0, n - 1) + "…" : s; }

  function laLenhTat(arg) {
    var k = chuanSo(arg).normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    return ["clear", "off", "stop", "tat", "xoa", "huy"].indexOf(k) !== -1;
  }

  function dinhDangMucDung(d) {
    d = d || {};
    var hn = d.today || {}, tc = d.all_time || {};
    function dong(nhan, tot) {
      tot = tot || {};
      if (!tot.turns) return "- " + nhan + ": chưa có lượt nào";
      var chi = (+tot.cost || 0) > 0 ? ", khoảng " + tien(tot.cost) : "";
      return "- " + nhan + ": " + (tot.turns || 0) + " lượt, vào " + gonSo(tot.in)
        + ", ra " + gonSo(tot.out) + chi;
    }
    var dongRa = ["Mức dùng", dong("Hôm nay", hn.total)];
    (hn.items || []).slice(0, 5).forEach(function (it) {
      dongRa.push("  - " + (it.provider || "?") + " " + (it.model || "") + ": "
        + (it.turns || 0) + " lượt, " + gonSo((it.in || 0) + (it.out || 0)) + " token");
    });
    dongRa.push(dong("Tổng", tc.total));
    if (d.openrouter && d.openrouter.remaining != null) {
      dongRa.push("- OpenRouter còn " + tien(d.openrouter.remaining));
    }
    dongRa.push("", "Chi tiết ở trang Mức dùng.");
    return dongRa.join("\n");
  }

  function dinhDangViec(d) {
    d = d || {};
    var cot = d.columns || {};
    var dong = ["Việc nền"];
    if (d.orchestration === "off") dong.push("AI tự vận hành đang tắt. Việc chỉ nằm trong hàng chờ.");
    else if (d.orchestration === "manual") dong.push("Đang ở chế độ duyệt tay.");
    var nhom = [
      ["running", "Đang chạy"],
      ["blocked", "Bị chặn"],
      ["review", "Chờ duyệt"],
      ["ready", "Sẵn sàng"],
      ["todo", "Việc"],
      ["triage", "Mới vào"],
    ];
    var co = false;
    nhom.forEach(function (g) {
      var ds = cot[g[0]] || [];
      if (!ds.length) return;
      co = true;
      dong.push("", g[1] + " (" + ds.length + ")");
      ds.slice(0, 5).forEach(function (t) { dong.push("- " + cat(t.title || t.id || "?", 70)); });
      if (ds.length > 5) dong.push("- còn " + (ds.length - 5) + " việc");
    });
    if (!co) dong.push("Không có việc đang mở.");
    if (d.completed_24h) dong.push("", "Xong trong 24 giờ: " + d.completed_24h);
    dong.push("", "Xem trên trang Công việc.");
    return dong.join("\n");
  }

  var goal = null;

  function chatApi() { return (typeof window !== "undefined" && window.JavisChatApi) || null; }
  function ghi(md) { var a = chatApi(); if (a && a.note) a.note(md); }

  async function layJson(url, opt) {
    var r = await fetch(url, opt);
    var d = null;
    try { d = await r.json(); } catch (e) { /* thân rỗng */ }
    return { ok: r.ok, status: r.status, d: d };
  }
  function brainHienTai() { var a = chatApi(); return a && a.brain ? a.brain() : "brain"; }

  async function layKhoi(thamSo) {
    var fd = new FormData();
    Object.keys(thamSo).forEach(function (k) { fd.append(k, String(thamSo[k])); });
    var r = await layJson("/slash/block", { method: "POST", body: fd });
    return (r.ok && r.d && r.d.block) || "";
  }

  function lenhHelp() {
    var ds = window.JavisSlash ? window.JavisSlash.buildMenu([]) : [];
    ds = ds.filter(function (x) { return x.kind === "session" || x.kind === "system"; });
    var dong = ["Lệnh trong khung chat"];
    ds.forEach(function (x) { dong.push("- /" + x.cmd + " - " + x.desc); });
    dong.push("", "Gõ /tên-skill để gọi skill. Skill trùng tên lệnh hệ thống thì skill chạy.");
    ghi(dong.join("\n"));
  }

  async function lenhStatus() {
    var a = chatApi();
    var r = await layJson("/slash/status?session_id=" + encodeURIComponent((a && a.sid && a.sid()) || "")
      + "&brain=" + encodeURIComponent(brainHienTai()));
    if (!r.ok || !r.d) return ghi("Không lấy được trạng thái.");
    var d = r.d;
    var dong = ["Trạng thái"];
    dong.push("- Model: " + (d.provider || "?") + " / " + (d.model || "mặc định"));
    dong.push("- Não: " + (d.brain || ""));
    dong.push("- Hội thoại này: " + (d.msg_count || 0) + " tin");
    if (d.version) dong.push("- Bản: " + d.version);
    ghi(dong.join("\n"));
  }

  async function lenhModel(arg) {
    var st = await layJson("/slash/status?brain=" + encodeURIComponent(brainHienTai()));
    var d = (st.d) || {};
    if (!arg) {
      return ghi("Model đang dùng: " + (d.provider || "?") + " / " + (d.model || "mặc định")
        + "\nGõ /model <tên> để đổi, tên phải có trong danh sách của nhà cung cấp đang dùng.");
    }
    if (!d.provider) return ghi("Chưa có nhà cung cấp đang dùng, chưa đổi model.");
    var cat = await layJson("/provider/models?provider=" + encodeURIComponent(d.provider));
    var ids = (cat.d && cat.d.models) || [];
    var q = String(arg).toLowerCase();
    var hit = ids.filter(function (id) { return String(id).toLowerCase() === q; });
    if (hit.length !== 1) {
      return ghi("Không thấy \"" + arg + "\" trong danh sách của " + d.provider
        + ". Model chính giữ nguyên.");
    }
    var fd = new FormData();
    fd.append("section", "model");
    fd.append("data", JSON.stringify({ main: { provider: d.provider, model: hit[0] } }));
    var r = await layJson("/settings", { method: "POST", body: fd });
    if (!r.ok) return ghi("Không đổi được model. Model chính giữ nguyên.");
    ghi("Đã đặt model chính: " + d.provider + " / " + hit[0]);
  }

  async function lenhBrain(arg) {
    var sel = document.getElementById("graphSource");
    var r = await layJson("/brains");
    var brains = (r.d && r.d.brains) || [];
    if (!r.ok || !sel) return ghi("Không lấy được danh sách não.");
    function giaTri(b) { return b.is_default ? "brain" : "path:" + b.path; }
    if (!arg) {
      var dong = ["Não"];
      brains.forEach(function (b) {
        dong.push("- " + b.name + (giaTri(b) === sel.value ? " (đang mở)" : ""));
      });
      dong.push("", "Gõ /brain <tên> để chuyển.");
      return ghi(dong.join("\n"));
    }
    var k = chuanSo(arg);
    var dung = brains.filter(function (b) { return chuanSo(b.name) === k; });
    var gan = dung.length ? dung : brains.filter(function (b) { return chuanSo(b.name).indexOf(k) !== -1; });
    if (gan.length === 1) {
      sel.value = giaTri(gan[0]);
      try { localStorage.setItem("javis.graphSource", sel.value); } catch (e) {}
      sel.dispatchEvent(new Event("change"));
      return ghi("Đã chuyển sang não: " + gan[0].name);
    }
    if (gan.length > 1) return ghi("Nhiều não khớp \"" + arg + "\": " + gan.slice(0, 6).map(function (b) { return b.name; }).join(", "));
    ghi("Không thấy não \"" + arg + "\".");
  }

  function lenhRetry() {
    var a = chatApi();
    if (!a) return;
    var t = a.lastUserText();
    if (!t) return ghi("Chưa có câu nào để gửi lại.");
    if (a.dangChay(a.sid())) return ghi("Đang trả lời. Bấm Dừng rồi gửi lại.");
    a.send(t);
  }

  async function lenhUsage() {
    var r = await layJson("/usage");
    if (!r.ok) return ghi("Không lấy được mức dùng.");
    ghi(dinhDangMucDung(r.d));
  }

  async function lenhTasks() {
    var r = await layJson("/kanban?brain=" + encodeURIComponent(brainHienTai()));
    if (!r.ok) return ghi("Không lấy được việc nền.");
    ghi(dinhDangViec(r.d));
  }

  async function lenhCompact() {
    var a = chatApi();
    var sid = a && a.sid ? a.sid() : "";
    if (!sid) return ghi("Chưa có hội thoại để nén.");
    var r = await layJson("/sessions/" + encodeURIComponent(sid) + "/compact", { method: "POST" });
    var d = r.d || {};
    if (r.status === 404) return ghi("Chưa có hội thoại để nén.");
    if (r.status === 409) return ghi("Hội thoại đang trả lời. Đợi xong rồi nén.");
    if (!r.ok) return ghi("Không nén được.");
    if (d.ok && d.cach === "tom_tat") return ghi("Đã nén " + (d.da_nen || 0) + " tin cũ thành một đoạn tóm tắt.");
    if (d.ly_do === "ngan") return ghi("Hội thoại còn ngắn (" + (d.so_tin || 0) + " tin), chưa cần nén.");
    ghi("Không nén được.");
  }

  async function lenhPlan(arg) {
    if (!arg) return ghi("Cú pháp: /plan việc cần làm");
    var khoi = await layKhoi({ kind: "plan" });
    if (!khoi) return ghi("Không soạn được chỉ dẫn.");
    if (!chatApi().send(arg, { prefix: khoi })) ghi("Khung chat chưa nối, chưa gửi được.");
  }

  async function lenhMemory() {
    var r = await layJson("/slash/memory?brain=" + encodeURIComponent(brainHienTai()));
    if (!r.ok) return ghi("Không đọc được bộ nhớ.");
    var d = r.d || {};
    var text = String(d.text || "").trim();
    if (!text) return ghi("Não này chưa có MEMORY.md.");
    ghi("Bộ nhớ · " + (d.brain || "") + (d.facts ? "\n" + d.facts + " mục nhớ chi tiết." : "") + "\n\n" + text);
  }

  async function lenhExport() {
    var a = chatApi();
    var sid = a && a.sid ? a.sid() : "";
    if (!sid) return ghi("Chưa có hội thoại để tải.");
    var r = await layJson("/sessions/" + encodeURIComponent(sid));
    if (!r.ok || !r.d || !(r.d.messages || []).length) return ghi("Hội thoại này chưa có tin để tải.");
    var dong = ["# " + (r.d.title || "Javis"), ""];
    (r.d.messages || []).forEach(function (m) {
      if (m.role !== "user" && m.role !== "assistant") return;
      var noi = String(m.content || "").replace(/<!--\s*JAVIS_[A-Z_]+:[\s\S]*?-->/g, "").trim();
      if (!noi) return;
      dong.push("", "## " + (m.role === "user" ? "Bạn" : "Javis"), "", noi);
    });
    var md = dong.join("\n") + "\n";
    var ten = "javis-hoi-thoai-" + new Date().toISOString().slice(0, 10) + ".md";
    var url = URL.createObjectURL(new Blob([md], { type: "text/markdown;charset=utf-8" }));
    var link = document.createElement("a");
    link.href = url; link.download = ten;
    document.body.appendChild(link); link.click(); link.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    ghi("Đã tải " + ten);
  }

  async function lenhGoal(arg) {
    if (laLenhTat(arg)) {
      if (goal) { goal = null; return ghi("Đã dừng mục tiêu."); }
      return ghi("Không có mục tiêu nào đang chạy.");
    }
    if (!arg) {
      if (goal) return ghi("Đang làm: " + cat(goal.dk, 120) + " (vòng " + goal.vong + "/" + goal.toiDa + ")");
      return ghi("Cú pháp: /goal mục tiêu. Tối đa " + GOAL_TOI_DA + " vòng. Gõ tin mới hoặc bấm Dừng là dừng.");
    }
    var khoi = await layKhoi({ kind: "goal", dk: arg, vong: 1, toi_da: GOAL_TOI_DA });
    if (!khoi) return ghi("Không soạn được chỉ dẫn.");
    goal = { sid: null, dk: arg, vong: 1, toiDa: GOAL_TOI_DA, left: "", ket: null };
    ghi("Bắt đầu mục tiêu (tối đa " + GOAL_TOI_DA + " vòng): " + cat(arg, 120));
    if (!chatApi().send(arg, { prefix: khoi, goal: true })) {
      goal = null;
      ghi("Khung chat chưa nối, mục tiêu chưa chạy.");
    }
  }

  function daGui(sid, opts) {
    if (goal && opts && opts.goal && !goal.sid) goal.sid = sid;
  }
  function chenNgang(sid) {
    if (goal && (!goal.sid || goal.sid === sid)) {
      goal = null;
      ghi("Bạn vừa nhắn, mục tiêu tự chạy đã dừng.");
    }
  }
  function dungMucTieu() {
    if (!goal) return;
    goal = null;
    ghi("Đã dừng mục tiêu.");
  }
  function ghiNhan(sid, marker, hoiLai) {
    if (goal && goal.sid === sid) goal.ket = { marker: marker, hoiLai: !!hoiLai };
  }
  function baoLoi(sid) {
    if (goal && goal.sid === sid) goal.ket = { loi: true };
  }
  async function tiepVong(sid) {
    var g = goal;
    if (!g || g.sid !== sid) return;
    g.vong += 1;
    var khoi = await layKhoi({ kind: "goal", dk: g.dk, vong: g.vong, toi_da: g.toiDa });
    if (goal !== g) return;
    if (!khoi) { goal = null; return ghi("Không soạn được vòng tiếp."); }
    ghi(g.left
      ? ("Vòng " + g.vong + "/" + g.toiDa + ". Còn: " + g.left)
      : ("Vòng " + g.vong + "/" + g.toiDa));
    if (!chatApi().send("Làm tiếp mục tiêu.", { prefix: khoi, goal: true })) {
      goal = null;
      ghi("Khung chat chưa nối, mục tiêu dừng.");
    }
  }
  function hetLuot(sid) {
    var g = goal;
    var a = chatApi();
    if (!g || !a || g.sid !== sid) return;
    if (a.sid() !== sid) { goal = null; return; }
    if (a.dangChay(sid)) return;
    var qd = quyetDinhVongTiep(g, g.ket);
    g.ket = null;
    if (qd.act === "tiep") {
      g.left = qd.left;
      setTimeout(function () { tiepVong(sid); }, 300);
      return;
    }
    goal = null;
    if (qd.ly === "dat") return ghi("Mục tiêu đã đạt sau " + g.vong + " vòng.");
    if (qd.ly === "het_vong") return ghi("Đã hết " + g.toiDa + " vòng. Mục tiêu chưa xong.");
    if (qd.ly === "khong_tien_trien") return ghi("Hai vòng liền không tiến thêm. Còn: " + (qd.left || ""));
    if (qd.ly === "hoi_lai") return ghi("Javis đang hỏi lại, mục tiêu tạm dừng.");
    if (qd.ly === "loi") return ghi("Vòng vừa rồi lỗi, mục tiêu dừng.");
    ghi("Mục tiêu dừng sau " + g.vong + " vòng vì chưa có dòng báo đã xong hay chưa.");
  }

  async function chay(cmd, arg) {
    arg = String(arg || "").trim();
    try {
      if (cmd === "help") return lenhHelp();
      if (cmd === "status") return await lenhStatus();
      if (cmd === "model") return await lenhModel(arg);
      if (cmd === "brain") return await lenhBrain(arg);
      if (cmd === "retry") return lenhRetry();
      if (cmd === "usage") return await lenhUsage();
      if (cmd === "tasks") return await lenhTasks();
      if (cmd === "compact") return await lenhCompact();
      if (cmd === "plan") return await lenhPlan(arg);
      if (cmd === "memory") return await lenhMemory();
      if (cmd === "export") return await lenhExport();
      if (cmd === "goal") return await lenhGoal(arg);
    } catch (e) {
      ghi("Lệnh không chạy được.");
    }
  }

  var api = {
    GOAL_TOI_DA: GOAL_TOI_DA,
    tachMucTieu: tachMucTieu,
    quyetDinhVongTiep: quyetDinhVongTiep,
    dinhDangMucDung: dinhDangMucDung,
    dinhDangViec: dinhDangViec,
    laLenhTat: laLenhTat,
    chay: chay,
    daGui: daGui,
    chenNgang: chenNgang,
    dungMucTieu: dungMucTieu,
    ghiNhan: ghiNhan,
    baoLoi: baoLoi,
    hetLuot: hetLuot,
    dangCoMucTieu: function () { return !!goal; },
  };
  if (typeof window !== "undefined") window.JavisLenh = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})();
