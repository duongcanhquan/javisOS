/* Nhạc trưởng: tab Phòng, Giao việc, Theo dõi. */
(function () {
  "use strict";
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }
  function brain() {
    try { return window.JavisSessions ? window.JavisSessions.brain() : "brain"; }
    catch (e) { return "brain"; }
  }
  async function api(url, opt) {
    var r = await fetch(url, opt);
    var j = {};
    try { j = await r.json(); } catch (e) { j = { ok: false, error: "Phản hồi không đọc được." }; }
    if (!r.ok && j.ok !== false) j.ok = false;
    if (!r.ok && !j.error) j.error = "Lỗi " + r.status;
    return j;
  }
  function post(url, body) {
    return api(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  }

  var TRANG = {
    nhap: ["Chưa chạy", ""],
    dang_chay: ["Đang chạy", "run"],
    xong: ["Đạt", "ok"],
    lech: ["Còn lệch", "warn"],
    loi: ["Lỗi", "warn"]
  };
  var LOP = { giao: "Giao việc", lam: "Làm", kiem: "Kiểm", hop: "Họp trưởng", sua: "Mang lệnh về" };
  var S = { phong: [], viec: [], chonPhong: "", chonViec: "", agents: [], kho: [], timer: 0, root: null, ban: false, loi: "", tab: "phong", sua: "", _nhap: null };

  function phongChon() {
    return S.phong.filter(function (p) { return p.slug === S.chonPhong; })[0] || null;
  }
  function truongCua(p) {
    return ((p && p.nguoi) || []).filter(function (n) { return n.vai === "truong"; })[0] || null;
  }
  function tenPhong(slug) {
    var p = S.phong.filter(function (x) { return x.slug === slug; })[0];
    return p ? p.ten : slug;
  }
  function pillTrang(st) {
    var x = TRANG[st] || [st || "Chưa chạy", ""];
    return '<span class="nt-pill ' + x[1] + '">' + esc(x[0]) + "</span>";
  }
  function pillQuyet(q) {
    if (q === "DAT") return '<span class="nt-pill ok">Đạt</span>';
    if (q === "CHUA") return '<span class="nt-pill warn">Chưa đạt</span>';
    return "";
  }
  function khongDau(s) {
    return String(s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/đ/g, "d").replace(/Đ/g, "D").toLowerCase();
  }
  function rut(s, n) {
    s = String(s || "").replace(/\s+/g, " ").trim();
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }
  function skillTen(slug) {
    var s = (S.kho || []).filter(function (x) { return x.slug === slug; })[0];
    return s ? (s.name || s.slug) : slug;
  }
  function oSkill(daChon) {
    var arr = (daChon || []).filter(Boolean);
    var chips = arr.map(function (s) {
      return '<button type="button" class="nt-pill" data-bo="' + esc(s) + '">' + esc(skillTen(s)) + " ×</button>";
    }).join("");
    return '<div class="nt-pick"><span class="nt-lbl">Skill trong kho</span>' +
      '<div class="nt-picked" data-picked>' + chips + "</div>" +
      '<input type="hidden" name="skills" value="' + esc(arr.join(", ")) + '">' +
      '<div class="nt-seek-wrap"><input type="search" class="nt-seek" placeholder="Gõ hoặc bấm để tìm skill, rồi chọn" autocomplete="off">' +
      '<div class="nt-seek-list" hidden></div></div>' +
      '<p class="nt-hint">Tối đa 8 skill. Bấm dấu × trên thẻ để bỏ.</p></div>';
  }
  function ganPick() {
    S.root.querySelectorAll(".nt-pick").forEach(function (host) {
      var hidden = host.querySelector('input[name="skills"]');
      var picked = host.querySelector("[data-picked]");
      var seek = host.querySelector(".nt-seek");
      var list = host.querySelector(".nt-seek-list");
      if (!hidden || !seek || !list) return;
      function doc() {
        return (hidden.value || "").split(",").map(function (s) { return s.trim(); }).filter(Boolean);
      }
      function ghi(arr) {
        hidden.value = arr.join(", ");
        picked.innerHTML = arr.map(function (s) {
          return '<button type="button" class="nt-pill" data-bo="' + esc(s) + '">' + esc(skillTen(s)) + " ×</button>";
        }).join("");
      }
      function loc() {
        var q = khongDau(seek.value.trim());
        var co = doc();
        var rows = (S.kho || []).filter(function (s) {
          if (s.enabled === false) return false;
          if (co.indexOf(s.slug) >= 0) return false;
          if (!q) return true;
          return khongDau(s.name + " " + s.slug + " " + (s.description || "") + " " + (s.group || "")).indexOf(q) >= 0;
        }).slice(0, 12);
        list.hidden = false;
        if (!S.kho.length) {
          list.innerHTML = '<p class="nt-hint">Kho skill của brain này đang trống.</p>';
          return;
        }
        if (co.length >= 8) {
          list.innerHTML = '<p class="nt-hint">Đã đủ 8 skill.</p>';
          return;
        }
        if (!rows.length) {
          list.innerHTML = '<p class="nt-hint">Không thấy skill khớp. Enter để thêm chữ vừa gõ.</p>';
          return;
        }
        list.innerHTML = rows.map(function (s) {
          return '<button type="button" data-add="' + esc(s.slug) + '"><b>' + esc(s.name || s.slug) + "</b><small>" +
            esc(s.group || "Chung") + (s.description ? " · " + esc(rut(s.description, 90)) : "") + "</small></button>";
        }).join("");
      }
      function them(slug) {
        slug = String(slug || "").trim().slice(0, 40);
        if (!slug) return;
        var arr = doc();
        if (arr.length >= 8 || arr.indexOf(slug) >= 0) return;
        arr.push(slug);
        ghi(arr);
        seek.value = "";
        loc();
      }
      seek.onfocus = loc;
      seek.onclick = loc;
      seek.oninput = loc;
      seek.onkeydown = function (ev) {
        if (ev.key !== "Enter") return;
        ev.preventDefault();
        var first = list.querySelector("[data-add]");
        if (first) them(first.getAttribute("data-add"));
        else if (seek.value.trim()) them(seek.value.trim());
      };
      host.onclick = function (ev) {
        var bo = ev.target.closest("[data-bo]");
        if (bo) {
          var x = bo.getAttribute("data-bo");
          ghi(doc().filter(function (s) { return s !== x; }));
          return;
        }
        var add = ev.target.closest("[data-add]");
        if (add) them(add.getAttribute("data-add"));
      };
    });
  }
  function agentOpts() {
    if (S._agentHtml != null && S._agentN === S.agents.length) return S._agentHtml;
    S._agentN = S.agents.length;
    S._agentHtml = '<option value="">Không gắn</option>' + S.agents.map(function (a) {
      return '<option value="' + esc(a.slug) + '">' + esc(a.name || a.slug) + "</option>";
    }).join("");
    return S._agentHtml;
  }
  function hienLoi(msg) {
    S.loi = msg || "";
    if (!S.root) return;
    var host = S.root.querySelector(".nt");
    if (!host) {
      if (msg) S.root.innerHTML = '<p class="nt-err" role="alert">' + esc(msg) + "</p>";
      return;
    }
    var cu = S.root.querySelector(".nt > .nt-err");
    if (!msg) { if (cu) cu.remove(); return; }
    if (!cu) {
      cu = document.createElement("p");
      cu.className = "nt-err";
      cu.setAttribute("role", "alert");
      host.insertBefore(cu, host.firstChild);
    }
    cu.textContent = msg;
  }
  function nutGui(form, ev) {
    if (ev && ev.submitter) return ev.submitter;
    return form.querySelector("button[type=submit]");
  }
  function bam(btn, nhan) {
    if (S.ban) return false;
    S.ban = true;
    S.loi = "";
    hienLoi("");
    if (btn) {
      btn.disabled = true;
      btn.dataset.cu = btn.textContent;
      btn.textContent = nhan;
    }
    return true;
  }
  function hong(btn, msg) {
    S.ban = false;
    if (btn) {
      btn.disabled = false;
      if (btn.dataset.cu) btn.textContent = btn.dataset.cu;
    }
    hienLoi(msg || "Không làm được.");
  }
  function chupViec() {
    var f = document.getElementById("ntTaoViec");
    if (!f) return null;
    var det = f.closest("details");
    return {
      tieu_de: f.tieu_de.value,
      brief: f.brief.value,
      vong: f.vong.value,
      phong: Array.prototype.map.call(f.querySelectorAll('input[name="phong"]:checked'), function (x) { return x.value; }),
      open: !!(det && det.open)
    };
  }
  function phucViec(g) {
    var f = document.getElementById("ntTaoViec");
    if (!f || !g) return;
    if (g.tieu_de) f.tieu_de.value = g.tieu_de;
    if (g.brief) f.brief.value = g.brief;
    if (g.vong) f.vong.value = g.vong;
    var det = f.closest("details");
    if (det && (g.open || g.tieu_de || g.brief)) det.open = true;
  }

  function ve(giu) {
    if (!S.root) return;
    var giuViec = giu ? chupViec() : null;
    if (giuViec) S._nhap = giuViec;
    var dang = coDangChay();
    S.root.innerHTML =
      '<div class="nt">' +
      (S.loi ? '<p class="nt-err" role="alert">' + esc(S.loi) + "</p>" : "") +
      '<p class="nt-lead">Phòng để xếp người và skill. Giao việc để giao brief. Theo dõi để xem từng việc chạy.</p>' +
      '<div class="nt-tabs" role="tablist">' +
      '<button type="button" class="nt-tab' + (S.tab === "phong" ? " on" : "") + '" data-tab="phong" role="tab">Phòng</button>' +
      '<button type="button" class="nt-tab' + (S.tab === "giao" ? " on" : "") + '" data-tab="giao" role="tab">Giao việc</button>' +
      '<button type="button" class="nt-tab' + (S.tab === "viec" ? " on" : "") + '" data-tab="viec" role="tab">Theo dõi' +
      (dang ? " · đang chạy" : "") + "</button>" +
      "</div>" +
      '<div class="nt-panel">' + (S.tab === "viec" ? tabViec() : S.tab === "giao" ? tabGiao() : tabPhong()) + "</div></div>";
    gan();
    if (giuViec) phucViec(giuViec);
  }

  function coDangChay() {
    if (S._viecDay && S._viecDay.trang_thai === "dang_chay") return true;
    return S.viec.some(function (v) { return v.trang_thai === "dang_chay"; });
  }

  function tabPhong() {
    var ds = S.phong.length ? '<div class="nt-cards">' + S.phong.map(function (p) {
      var t = truongCua(p);
      return '<button type="button" class="' + (p.slug === S.chonPhong ? "on" : "") + '" data-phong="' + esc(p.slug) + '">' +
        "<b>" + esc(p.ten) + "</b><small>" + (t ? "Trưởng " + esc(t.ten) : "Chưa có trưởng") +
        " · " + (p.nguoi || []).length + " người</small></button>";
    }).join("") + "</div>" : "";
    var mo = S.phong.length ? "" : " open";
    var tao = '<details class="nt-details"' + mo + '><summary>Phòng mới</summary>' +
      '<form id="ntTaoPhong" class="nt-form nt-split">' +
      '<label>Tên<input name="ten" required placeholder="Nội dung"></label>' +
      '<label class="full">Tiêu chí trưởng giữ<textarea name="tieu_chi" placeholder="Rõ ý, đúng brief, không bịa"></textarea></label>' +
      '<div class="nt-row full"><button class="nt-btn pri" type="submit">Tạo phòng</button></div></form></details>';
    if (!S.phong.length) {
      return "<h2>Phòng</h2>" +
        '<p class="nt-hint">Tạo phòng, viết tiêu chí, đặt một trưởng. Rồi sang tab Giao việc.</p>' + tao;
    }
    return "<h2>Phòng</h2>" + ds + thanPhong() + tao;
  }

  function thanPhong() {
    var p = phongChon();
    if (!p) return '<p class="nt-hint">Chọn một phòng.</p>';
    var t = truongCua(p);
    var nguoi = (p.nguoi || []).map(function (n) { return theNguoi(n, !!t); }).join("");
    var moNguoi = t ? "" : " open";
    return '<form id="ntSuaTieu" class="nt-form nt-split">' +
      '<label class="full">Tiêu chí trưởng giữ<textarea name="tieu_chi" required>' + esc(p.tieu_chi || "") + "</textarea></label>" +
      '<div class="nt-row full"><button class="nt-btn pri" type="submit">Lưu tiêu chí</button>' +
      '<button type="button" class="nt-btn danger" id="ntXoaPhong">Xoá phòng</button></div></form>' +
      (t ? '<p class="nt-hint"><span class="nt-pill ok">Có trưởng</span> ' + esc(t.ten) + "</p>"
        : '<p class="nt-call">Chưa có trưởng. Thêm một người với vai Trưởng phòng, rồi mới giao việc.</p>') +
      (nguoi ? '<div class="nt-people">' + nguoi + "</div>" : "") +
      '<details class="nt-details"' + moNguoi + '><summary>Thêm người</summary>' +
      '<form id="ntThemNguoi" class="nt-form nt-split">' +
      '<label>Tên<input name="ten" required placeholder="An"></label>' +
      '<label class="full">Tính cách<textarea name="tinh_cach" placeholder="Thẳng, không viết hộ, bắt lỗi từng câu"></textarea></label>' +
      '<div class="full">' + oSkill([]) + "</div>" +
      '<label>Vai<select name="vai"><option value="thanh_vien"' + (t ? " selected" : "") + '>Thành viên</option><option value="truong"' + (t ? " disabled" : " selected") + '>Trưởng phòng</option></select></label>' +
      '<label>Trợ lý gốc, không bắt buộc<select name="agent">' + agentOpts() + "</select></label>" +
      '<div class="nt-row full"><button class="nt-btn pri" type="submit">Thêm người</button></div></form></details>';
  }

  function theNguoi(n, coTruong) {
    if (S.sua === n.slug) {
      return '<form class="nt-card nt-form" id="ntSuaNguoi">' +
        "<b>" + esc(n.ten) + "</b>" +
        '<label>Tính cách<textarea name="tinh_cach">' + esc(n.tinh_cach || "") + "</textarea></label>" +
        oSkill(n.skills || []) +
        '<label>Vai<select name="vai"><option value="thanh_vien"' + (n.vai !== "truong" ? " selected" : "") +
        '>Thành viên</option><option value="truong"' +
        (n.vai === "truong" ? " selected" : (coTruong ? " disabled" : "")) +
        '>Trưởng phòng</option></select></label>' +
        '<div class="nt-row"><button class="nt-btn pri" type="submit">Lưu</button>' +
        '<button type="button" class="nt-btn ghost" id="ntHuySua">Huỷ</button></div></form>';
    }
    var sk = (n.skills || []).map(function (s) { return '<span class="nt-pill">' + esc(skillTen(s)) + "</span>"; }).join(" ");
    return '<article class="nt-card"><div><b>' + esc(n.ten) + "</b> " +
      (n.vai === "truong" ? '<span class="nt-pill ok">Trưởng phòng</span>' : '<span class="nt-pill">Thành viên</span>') +
      "<p>" + esc(n.tinh_cach || "Chưa viết tính cách.") + "</p>" +
      (sk ? '<p class="nt-chips">' + sk + "</p>" : '<p class="nt-hint">Chưa gán skill.</p>') +
      '</div><div class="nt-row"><button type="button" class="nt-btn ghost" data-sua="' + esc(n.slug) + '">Sửa</button>' +
      '<button type="button" class="nt-btn ghost" data-xoa-nguoi="' + esc(n.slug) + '" data-ten="' + esc(n.ten) + '">Bỏ khỏi phòng</button></div></article>';
  }

  function tabGiao() {
    if (!S.phong.length) {
      return "<h2>Giao việc</h2>" +
        '<p class="nt-hint">Chưa có phòng. Tạo phòng ở tab Phòng trước.</p>' +
        '<button type="button" class="nt-btn" data-tab="phong">Về tab Phòng</button>';
    }
    if (!S.phong.some(truongCua)) {
      return "<h2>Giao việc</h2>" +
        '<p class="nt-call">Chưa giao được. Mỗi phòng tham gia cần một trưởng.</p>' +
        '<button type="button" class="nt-btn" data-tab="phong">Về tab Phòng</button>';
    }
    return "<h2>Giao việc</h2>" +
      '<p class="nt-hint">Viết brief, chọn phòng, rồi bấm Giao việc. Việc vừa giao mở ở tab Theo dõi. Bấm Chạy ở đó để các trưởng bắt đầu.</p>' +
      formViec();
  }

  function tabViec() {
    if (!S.phong.length) {
      return "<h2>Theo dõi</h2>" +
        '<p class="nt-hint">Chưa có phòng. Tạo phòng ở tab Phòng trước.</p>' +
        '<button type="button" class="nt-btn" data-tab="phong">Về tab Phòng</button>';
    }
    return '<div class="nt-watch"><aside class="nt-rail"><h2>Việc</h2>' +
      '<button type="button" class="nt-btn" data-tab="giao">Giao việc mới</button>' +
      dsViec() +
      '</aside><div class="nt-stage" id="ntTheoDoi">' + theoDoi() + "</div></div>";
  }

  function formViec() {
    var n = S._nhap || {};
    var hop = S.phong.map(function (p) {
      var thieu = truongCua(p) ? "" : " disabled";
      var chon = "";
      if (n.phong && n.phong.length) chon = n.phong.indexOf(p.slug) >= 0 ? " checked" : "";
      else if (p.slug === S.chonPhong && truongCua(p)) chon = " checked";
      return '<label class="nt-chip"><input type="checkbox" name="phong" value="' + esc(p.slug) + '"' + chon + thieu + "> " +
        esc(p.ten) + (thieu ? " (thiếu trưởng)" : "") + "</label>";
    }).join("");
    return '<form id="ntTaoViec" class="nt-form nt-split">' +
      '<label>Tên việc<input name="tieu_de" required placeholder="Bài ra mắt khóa" value="' + esc(n.tieu_de || "") + '"></label>' +
      '<label>Vòng tối đa mỗi tầng<input name="vong" type="number" min="1" max="4" value="' + esc(n.vong || "2") + '"></label>' +
      '<label class="full">Brief<textarea name="brief" required placeholder="Việc cần làm, điều cấm, người đọc">' + esc(n.brief || "") + "</textarea></label>" +
      '<span class="nt-lbl full">Phòng tham gia<div class="nt-chips">' + hop + "</div></span>" +
      '<p class="nt-hint full">Hết vòng thì dừng và ghi chỗ còn mở. Không sửa mãi.</p>' +
      '<div class="nt-row full"><button class="nt-btn pri" type="submit">Giao việc</button></div></form>';
  }

  function dsViec() {
    if (!S.viec.length) return '<p class="nt-hint">Chưa có việc. Bấm Giao việc mới.</p>';
    return '<div class="nt-jobs">' + S.viec.map(function (v) {
      return '<button type="button" class="nt-job' + (v.id === S.chonViec ? " on" : "") + '" data-viec="' + esc(v.id) + '">' +
        "<b>" + esc(v.tieu_de) + "</b><small>" + esc((TRANG[v.trang_thai] || [v.trang_thai || ""])[0]) + "</small></button>";
    }).join("") + "</div>";
  }

  function buoc(v) {
    var loi = v.loi || [];
    var mot = (v.phong || []).length < 2;
    var coNoi = loi.some(function (r) { return r.lop === "giao" || r.lop === "kiem"; });
    var coHop = loi.some(function (r) { return r.lop === "hop"; });
    var xong = v.trang_thai === "xong";
    function m(ten, dat, dang) { return '<span class="nt-step' + (dat ? " xong" : dang ? " on" : "") + '">' + ten + "</span>"; }
    return '<div class="nt-steps">' +
      m("Trong phòng", xong || coHop, coNoi && !coHop && !xong) +
      m(mot ? "Không họp liên phòng" : "Họp trưởng", xong || (mot && coNoi), coHop && !xong) +
      m(v.trang_thai === "lech" ? "Còn lệch" : "Bản chốt", xong, v.trang_thai === "lech") +
      "</div>";
  }

  function theoDoi() {
    var v = S._viecDay;
    if (!v) return '<p class="nt-hint">Chọn một việc để xem biên bản.</p>';
    var chay = v.trang_thai === "dang_chay";
    var loi = nhomLoi(v.loi || []);
    var ban = Object.keys(v.ban || {}).map(function (k) {
      return "<h4>" + esc(tenPhong(k)) + "</h4><p>" + esc(v.ban[k] || "") + "</p>";
    }).join("");
    var mo = (v.mo || []).map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("");
    var hienBan = v.trang_thai === "xong" || v.trang_thai === "lech";
    return '<div class="nt-row">' + pillTrang(v.trang_thai) + "<b>" + esc(v.tieu_de) + "</b></div>" +
      '<p class="nt-hint">' + esc(v.brief || "") + "</p>" +
      (v.loi_chay ? '<p class="nt-err">' + esc(v.loi_chay) + "</p>" : "") +
      buoc(v) +
      '<div class="nt-row">' +
      '<button type="button" class="nt-btn pri" id="ntChay"' + (chay ? " disabled" : "") + ">" + (chay ? "Đang chạy" : "Chạy") + "</button>" +
      '<button type="button" class="nt-btn" id="ntThu"' + (chay ? " disabled" : "") + ">Chạy thử</button>" +
      (chay ? "" : '<button type="button" class="nt-btn danger" id="ntXoaViec">Xoá việc</button>') +
      "</div>" +
      '<p class="nt-hint">Chạy dùng model đang chọn, chỉ nháp trong brain. Chạy thử dùng người giả để xem cách chặn bản.</p>' +
      '<div class="nt-log" id="ntLog">' + (loi || '<p class="nt-hint">' + (chay ? "Đang chạy. Lời mới hiện ngay khi có." : "Chưa có lời nào.") + "</p>") + "</div>" +
      (hienBan && ban ? '<div class="nt-ban"><h3>Bản chốt</h3>' + ban + "</div>" : "") +
      (mo ? '<ul class="nt-mo">' + mo + "</ul>" : "") +
      '<p class="nt-hint">Mở lại: nhac-truong/viec/' + esc(v.id) + ".md</p>";
  }

  function loiSach(text) {
    return String(text || "").split("\n").filter(function (line) {
      return !/^\s*(quyet|quyết|sua|sửa|tra)\s*:/i.test(line);
    }).join("\n").trim();
  }

  function nhomLoi(rows) {
    var out = "";
    var khoa = "";
    rows.forEach(function (row) {
      var pha = (row.lop === "hop" ? "Họp trưởng" : "Trong phòng · " + (row.phong_ten || "")) + " · vòng " + row.vong;
      if (pha !== khoa) { khoa = pha; out += '<div class="nt-phase">' + esc(pha) + "</div>"; }
      var vai = row.vai === "truong" ? "Trưởng" : "Thành viên";
      out += '<article class="nt-say"><header><b>' + esc(row.ten) + "</b> " +
        '<span class="nt-pill">' + esc(vai) + "</span> " +
        '<span class="nt-pill">' + esc(LOP[row.lop] || row.lop) + "</span> " +
        pillQuyet(row.quyet) + "</header>" +
        (loiSach(row.loi) ? "<p>" + esc(loiSach(row.loi)) + "</p>" : "") + "</article>";
    });
    return out;
  }

  function gan() {
    S.root.querySelectorAll("[data-tab]").forEach(function (b) {
      b.onclick = function () {
        var raw = b.getAttribute("data-tab");
        var id = raw === "viec" || raw === "giao" ? raw : "phong";
        if (id === S.tab) return;
        if (S.tab === "giao") {
          var giu = chupViec();
          if (giu) S._nhap = giu;
        }
        S.tab = id;
        S.sua = "";
        S.loi = "";
        ve();
        if (id === "viec" && S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
      };
    });
    var tao = document.getElementById("ntTaoPhong");
    if (tao) tao.onsubmit = async function (ev) {
      ev.preventDefault();
      var btn = nutGui(tao, ev);
      if (!bam(btn, "Đang tạo…")) return;
      var fd = new FormData(tao);
      try {
        var j = await post("/nhac-truong/phong", { brain: brain(), ten: fd.get("ten"), tieu_chi: fd.get("tieu_chi") });
        if (!j.ok) return hong(btn, j.error);
        S.phong.push(j.phong);
        S.chonPhong = j.phong.slug;
        S.ban = false;
        ve();
      } catch (e) { hong(btn, "Không kết nối được."); }
    };
    S.root.querySelectorAll("[data-phong]").forEach(function (b) {
      b.onclick = function () {
        var id = b.getAttribute("data-phong");
        if (!id || id === S.chonPhong) return;
        S.chonPhong = id;
        S.sua = "";
        S.loi = "";
        ve(true);
      };
    });
    var them = document.getElementById("ntThemNguoi");
    if (them) them.onsubmit = async function (ev) {
      ev.preventDefault();
      var btn = nutGui(them, ev);
      if (!bam(btn, "Đang thêm…")) return;
      var fd = new FormData(them);
      try {
        var j = await post("/nhac-truong/phong/" + encodeURIComponent(S.chonPhong) + "/nguoi", {
          brain: brain(), ten: fd.get("ten"), tinh_cach: fd.get("tinh_cach"),
          skills: fd.get("skills"), vai: fd.get("vai"), agent: fd.get("agent"),
        });
        if (!j.ok) return hong(btn, j.error);
        var p = phongChon();
        if (p) p.nguoi.push(j.nguoi);
        S.ban = false;
        ve();
      } catch (e) { hong(btn, "Không kết nối được."); }
    };
    var xoa = document.getElementById("ntXoaPhong");
    if (xoa) xoa.onclick = async function () {
      var p = phongChon();
      if (!p || S.ban) return;
      if (!window.confirm("Xoá phòng " + p.ten + "? Biên bản việc đã chạy vẫn giữ.")) return;
      if (!bam(xoa, "Đang xoá…")) return;
      try {
        var j = await api("/nhac-truong/phong/" + encodeURIComponent(p.slug) + "?brain=" + encodeURIComponent(brain()), { method: "DELETE" });
        if (!j.ok) return hong(xoa, j.error);
        S.phong = S.phong.filter(function (x) { return x.slug !== p.slug; });
        if (S.chonPhong === p.slug) S.chonPhong = (S.phong[0] && S.phong[0].slug) || "";
        S.ban = false;
        ve();
      } catch (e) { hong(xoa, "Không kết nối được."); }
    };
    S.root.querySelectorAll("[data-xoa-nguoi]").forEach(function (b) {
      b.onclick = async function () {
        var ten = b.getAttribute("data-ten") || "người này";
        var ns = b.getAttribute("data-xoa-nguoi");
        if (S.ban) return;
        if (!window.confirm("Bỏ " + ten + " khỏi phòng?")) return;
        if (!bam(b, "Đang bỏ…")) return;
        try {
          var j = await api("/nhac-truong/phong/" + encodeURIComponent(S.chonPhong) + "/nguoi/" +
            encodeURIComponent(ns) + "?brain=" + encodeURIComponent(brain()), { method: "DELETE" });
          if (!j.ok) return hong(b, j.error);
          var p = phongChon();
          if (p) p.nguoi = (p.nguoi || []).filter(function (n) { return n.slug !== ns; });
          S.ban = false;
          ve();
        } catch (e) { hong(b, "Không kết nối được."); }
      };
    });
    var tv = document.getElementById("ntTaoViec");
    if (tv) tv.onsubmit = async function (ev) {
      ev.preventDefault();
      var btn = nutGui(tv, ev);
      var fd = new FormData(tv);
      if (!fd.getAll("phong").length) return hienLoi("Chọn ít nhất một phòng đã có trưởng.");
      if (!bam(btn, "Đang giao…")) return;
      try {
        var j = await post("/nhac-truong/viec", {
          brain: brain(), tieu_de: fd.get("tieu_de"), brief: fd.get("brief"),
          phong: fd.getAll("phong"), vong: fd.get("vong"),
        });
        if (!j.ok) return hong(btn, j.error);
        S.viec.unshift({
          id: j.viec.id, tieu_de: j.viec.tieu_de,
          trang_thai: j.viec.trang_thai, phong: j.viec.phong
        });
        S.chonViec = j.viec.id;
        S._viecDay = j.viec;
        S._khoa = "";
        S.tab = "viec";
        S._nhap = null;
        S.ban = false;
        ve();
      } catch (e) { hong(btn, "Không kết nối được."); }
    };
    S.root.querySelectorAll("[data-viec]").forEach(function (b) {
      b.onclick = function () {
        var id = b.getAttribute("data-viec");
        if (!id || id === S.chonViec || S.ban) return;
        S.chonViec = id;
        S.loi = "";
        hienLoi("");
        S.root.querySelectorAll("[data-viec]").forEach(function (x) {
          x.classList.toggle("on", x === b);
        });
        var box = document.getElementById("ntTheoDoi");
        if (box) box.innerHTML = '<p class="nt-hint">Đang mở…</p>';
        S._khoa = "";
        moViec().then(function () {
          capNhatTheoDoi();
          if (S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
        });
      };
    });
    var tc = document.getElementById("ntSuaTieu");
    if (tc) tc.onsubmit = async function (ev) {
      ev.preventDefault();
      var btn = nutGui(tc, ev);
      if (!bam(btn, "Đang lưu…")) return;
      var fd = new FormData(tc);
      try {
        var j = await post("/nhac-truong/phong/" + encodeURIComponent(S.chonPhong), {
          brain: brain(), tieu_chi: fd.get("tieu_chi"),
        });
        if (!j.ok) return hong(btn, j.error);
        var p = phongChon();
        if (p) p.tieu_chi = j.phong.tieu_chi;
        S.ban = false;
        ve();
      } catch (e) { hong(btn, "Không kết nối được."); }
    };
    var sua = document.getElementById("ntSuaNguoi");
    if (sua) sua.onsubmit = async function (ev) {
      ev.preventDefault();
      var btn = nutGui(sua, ev);
      if (!bam(btn, "Đang lưu…")) return;
      var fd = new FormData(sua);
      try {
        var j = await post("/nhac-truong/phong/" + encodeURIComponent(S.chonPhong) + "/nguoi/" + encodeURIComponent(S.sua), {
          brain: brain(), tinh_cach: fd.get("tinh_cach"), skills: fd.get("skills"), vai: fd.get("vai"),
        });
        if (!j.ok) return hong(btn, j.error);
        var p = phongChon();
        if (p) p.nguoi = (p.nguoi || []).map(function (n) { return n.slug === j.nguoi.slug ? j.nguoi : n; });
        S.sua = "";
        S.ban = false;
        ve();
      } catch (e) { hong(btn, "Không kết nối được."); }
    };
    S.root.querySelectorAll("[data-sua]").forEach(function (b) {
      b.onclick = function () { S.sua = b.getAttribute("data-sua") || ""; ve(); };
    });
    S.root.onclick = function (ev) {
      if (ev.target.closest(".nt-pick")) return;
      S.root.querySelectorAll(".nt-seek-list").forEach(function (l) { l.hidden = true; });
    };
    var huy = document.getElementById("ntHuySua");
    if (huy) huy.onclick = function () { S.sua = ""; ve(); };
    var tv2 = document.getElementById("ntTaoViec");
    if (tv2) tv2.oninput = function () { S._nhap = chupViec(); };
    ganPick();
    ganTheoDoi();
  }

  function ganTheoDoi() {
    var chay = document.getElementById("ntChay");
    if (chay) chay.onclick = function () { batDau(false); };
    var thu = document.getElementById("ntThu");
    if (thu) thu.onclick = function () { batDau(true); };
    var xv = document.getElementById("ntXoaViec");
    if (xv) xv.onclick = async function () {
      var v = S._viecDay;
      if (!v || S.ban) return;
      if (!window.confirm("Xoá việc " + v.tieu_de + "?")) return;
      if (!bam(xv, "Đang xoá…")) return;
      try {
        var j = await api("/nhac-truong/viec/" + encodeURIComponent(v.id) + "?brain=" + encodeURIComponent(brain()), { method: "DELETE" });
        if (!j.ok) return hong(xv, j.error);
        S.viec = S.viec.filter(function (x) { return x.id !== v.id; });
        if (S.chonViec === v.id) {
          S.chonViec = (S.viec[0] && S.viec[0].id) || "";
          S._viecDay = null;
        }
        S._khoa = "";
        S.ban = false;
        if (S.chonViec) await moViec();
        ve();
      } catch (e) { hong(xv, "Không kết nối được."); }
    };
  }

  function khoaViec(v) {
    if (!v) return "";
    var loi = v.loi || [];
    var last = loi.length ? (loi[loi.length - 1].loi || "").length : 0;
    return [v.id, v.trang_thai, loi.length, last, v.loi_chay || "", (v.mo || []).length, Object.keys(v.ban || {}).length].join("~");
  }

  function capNhatTheoDoi() {
    if (S._viecDay) {
      var row0 = S.viec.filter(function (x) { return x.id === S._viecDay.id; })[0];
      if (row0) row0.trang_thai = S._viecDay.trang_thai;
    }
    var box = S.root && S.root.querySelector("#ntTheoDoi");
    if (!box) {
      var nut = S.root && S.root.querySelector('.nt-tabs [data-tab="viec"]');
      if (nut) nut.textContent = coDangChay() ? "Theo dõi · đang chạy" : "Theo dõi";
      return;
    }
    var k = khoaViec(S._viecDay);
    var doi = k !== S._khoa;
    if (doi) {
      S._khoa = k;
      var log = document.getElementById("ntLog");
      var satDay = log ? (log.scrollHeight - log.scrollTop - log.clientHeight < 40) : true;
      box.innerHTML = theoDoi();
      ganTheoDoi();
      var log2 = document.getElementById("ntLog");
      if (log2 && satDay) log2.scrollTop = log2.scrollHeight;
    }
    S.root.querySelectorAll("[data-viec]").forEach(function (b) {
      var id = b.getAttribute("data-viec");
      var v = S.viec.filter(function (x) { return x.id === id; })[0];
      if (v && S._viecDay && v.id === S._viecDay.id) v.trang_thai = S._viecDay.trang_thai;
      var small = b.querySelector("small");
      if (small && v) small.textContent = (TRANG[v.trang_thai] || [v.trang_thai || ""])[0];
    });
  }

  function batPoll() {
    if (S.timer) clearInterval(S.timer);
    var dang = S.chonViec;
    S.timer = setInterval(function () {
      if (S._mo || S.chonViec !== dang) {
        if (S.chonViec !== dang) { clearInterval(S.timer); S.timer = 0; }
        return;
      }
      S._mo = true;
      moViec().then(function () {
        S._mo = false;
        if (S.chonViec !== dang) return;
        capNhatTheoDoi();
        var st = S._viecDay && S._viecDay.trang_thai;
        if (st && st !== "dang_chay") {
          clearInterval(S.timer);
          S.timer = 0;
        }
      });
    }, 1000);
  }

  async function batDau(thu) {
    if (!S.chonViec || S.ban || !S._viecDay) return;
    if (S._viecDay.trang_thai === "dang_chay") return;
    var truoc = S._viecDay.trang_thai;
    S.ban = true;
    S._viecDay.trang_thai = "dang_chay";
    if (!thu) S._choChay = S.chonViec;
    S.loi = "";
    S._khoa = "";
    capNhatTheoDoi();
    var j;
    try {
      j = await post("/nhac-truong/viec/" + encodeURIComponent(S.chonViec) + "/chay", {
        brain: brain(), thu: !!thu,
      });
    } catch (e) {
      j = { ok: false, error: "Không kết nối được." };
    }
    S.ban = false;
    if (!j.ok) {
      if (j.error && /đang chạy/i.test(j.error)) {
        S._choChay = S.chonViec;
        batPoll();
        return;
      }
      S._choChay = "";
      S._viecDay.trang_thai = truoc;
      S._khoa = "";
      capNhatTheoDoi();
      return hienLoi(j.error);
    }
    if (j.viec) {
      S._choChay = "";
      S._viecDay = j.viec;
      var row = S.viec.filter(function (x) { return x.id === j.viec.id; })[0];
      if (row) row.trang_thai = j.viec.trang_thai;
      S._khoa = "";
      capNhatTheoDoi();
      return;
    }
    batPoll();
  }

  async function moViec() {
    if (!S.chonViec) { S._viecDay = null; return; }
    var id = S.chonViec;
    var j = await api("/nhac-truong/viec/" + encodeURIComponent(id) + "?brain=" + encodeURIComponent(brain()));
    if (id !== S.chonViec) return;
    if (!j.ok) {
      S._viecDay = null;
      hienLoi(j.error);
      return;
    }
    var v = j.viec;
    if (S._choChay === id && v && v.trang_thai === "nhap") v.trang_thai = "dang_chay";
    else if (v && v.trang_thai !== "nhap") S._choChay = "";
    S._viecDay = v;
  }

  function chonMacDinh() {
    if (S.chonPhong && !S.phong.some(function (p) { return p.slug === S.chonPhong; })) S.chonPhong = "";
    if (!S.chonPhong && S.phong[0]) S.chonPhong = S.phong[0].slug;
    if (S.chonViec && !S.viec.some(function (x) { return x.id === S.chonViec; })) S.chonViec = "";
    if (!S.chonViec && S.viec[0]) S.chonViec = S.viec[0].id;
  }

  async function tai() {
    var b = encodeURIComponent(brain());
    var cap = await Promise.all([
      api("/nhac-truong/phong?brain=" + b),
      api("/nhac-truong/viec?brain=" + b)
    ]);
    var a = cap[0], v = cap[1];
    if (a.ok === false && !a.phong) return hienLoi(a.error);
    S.phong = a.phong || [];
    S.viec = v.viec || [];
    chonMacDinh();
    await moViec();
    S._khoa = "";
    ve();
    if (S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
  }

  async function render(el) {
    S.root = el;
    if (S.timer) { clearInterval(S.timer); S.timer = 0; }
    el.innerHTML = '<p class="nt-hint">Đang tải…</p>';
    var b = encodeURIComponent(brain());
    try {
      var cap = await Promise.all([
        api("/agents?brain=" + b),
        api("/nhac-truong/phong?brain=" + b),
        api("/nhac-truong/viec?brain=" + b),
        api("/skills?brain=" + b)
      ]);
      S.agents = (cap[0] && cap[0].agents) || [];
      S._agentHtml = null;
      S.phong = (cap[1] && cap[1].phong) || [];
      S.viec = (cap[2] && cap[2].viec) || [];
      S.kho = (cap[3] && cap[3].skills) || [];
    } catch (e) {
      S.agents = [];
      return hienLoi("Không tải được Nhạc trưởng.");
    }
    if (cap[1] && cap[1].ok === false && !cap[1].phong) return hienLoi(cap[1].error);
    chonMacDinh();
    await moViec();
    if (S._viecDay && S._viecDay.trang_thai === "dang_chay") S.tab = "viec";
    S._khoa = "";
    ve();
    if (S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
  }

  window.JavisNhacTruong = {
    render: render,
    stop: function () { if (S.timer) clearInterval(S.timer); S.timer = 0; }
  };
})();
