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
    dung: ["Đã dừng", "warn"],
    loi: ["Lỗi", "warn"]
  };
  var LOP = { giao: "Xếp việc", lam: "Làm", kiem: "Phản hồi", hop: "Họp trưởng", sua: "Mang lệnh về", nhan: "Nhận bàn giao", doi: "Trả lời", xu: "Trưởng xử", chia: "Góp ý", dap: "Đáp lại", gop: "Trao đổi", ket: "Kết quả" };
  var MAU_TEN = ["#8eb7ff", "#f0a202", "#3ddc97", "#e09cff", "#ff8b7b", "#7ee0d6", "#f2d06b", "#ffb4d0"];
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
  function pillQuyet(q, lop) {
    if (q === "DAT") return '<span class="nt-pill ok">Đạt</span>';
    if (q === "OK") return '<span class="nt-pill ok">Đã nhận</span>';
    if (q === "CHUA" && lop === "nhan") return '<span class="nt-pill warn">Chưa nhận</span>';
    if (q === "CHUA") return '<span class="nt-pill warn">Chưa đạt</span>';
    if (q === "LAM") return '<span class="nt-pill">Làm tiếp</span>';
    if (q === "SUA") return '<span class="nt-pill warn">Bắt sửa</span>';
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
      '<div class="nt-seek-row"><div class="nt-seek-wrap"><input type="search" class="nt-seek" placeholder="Gõ từ khoá để lọc nhanh" autocomplete="off">' +
      '<div class="nt-seek-list" hidden></div></div>' +
      '<button type="button" class="nt-btn" data-mo-kho>Mở kho</button></div>' +
      '<p class="nt-hint" data-kho-dem>Đang tải kho skill…</p></div>';
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
      var di = 0;
      function loc() {
        di = 0;
        var q = khongDau(seek.value.trim());
        var co = doc();
        var khop = (S.kho || []).filter(function (s) {
          if (s.enabled === false) return false;
          if (co.indexOf(s.slug) >= 0) return false;
          if (!q) return true;
          return khongDau(s.name + " " + s.slug + " " + (s.description || "") + " " + (s.group || "")).indexOf(q) >= 0;
        });
        var rows = khop.slice(0, 8);
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
        var thieu = khop.length - rows.length;
        list.innerHTML = rows.map(function (s) {
          return '<button type="button" data-add="' + esc(s.slug) + '"><span class="nt-sk-name">' + esc(s.name || s.slug) +
            '</span><span class="nt-sk-meta">' + esc(s.group || "Chung") +
            (s.description ? " · " + esc(rut(s.description, 64)) : "") + "</span></button>";
        }).join("") +
          '<button type="button" class="nt-kho-more" data-mo-kho>Mở kho theo chuyên mục' +
          (thieu > 0 ? " · còn " + thieu : "") + "</button>";
        danhDau();
        datList();
      }
      function datList() {
        if (list.hidden) return;
        var r = seek.getBoundingClientRect();
        if (r.width < 8 || r.bottom < 0 || r.top > window.innerHeight) {
          list.hidden = true;
          return;
        }
        list.style.position = "fixed";
        list.style.left = Math.round(r.left) + "px";
        list.style.top = Math.round(r.bottom + 4) + "px";
        list.style.width = Math.round(r.width) + "px";
        list.style.right = "auto";
        list.style.maxHeight = Math.max(120, Math.min(240, window.innerHeight - r.bottom - 12)) + "px";
      }
      list._dat = datList;
      function danhDau() {
        var nuts = list.querySelectorAll("[data-add]");
        if (di >= nuts.length) di = 0;
        nuts.forEach(function (n, i) { n.classList.toggle("nt-sk-on", i === di); });
        var n = nuts[di];
        if (!n) return;
        var top = n.offsetTop;
        var bot = top + n.offsetHeight;
        if (top < list.scrollTop) list.scrollTop = top;
        else if (bot > list.scrollTop + list.clientHeight) list.scrollTop = bot - list.clientHeight;
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
      list.onmouseover = function (ev) {
        var b = ev.target.closest("[data-add]");
        if (!b || b.classList.contains("nt-sk-on")) return;
        var nuts = list.querySelectorAll("[data-add]");
        di = Array.prototype.indexOf.call(nuts, b);
        nuts.forEach(function (n, i) { n.classList.toggle("nt-sk-on", i === di); });
      };
      seek.onfocus = loc;
      seek.onclick = loc;
      seek.oninput = loc;
      seek.onkeydown = function (ev) {
        var nuts = list.querySelectorAll("[data-add]");
        if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
          ev.preventDefault();
          if (!nuts.length) return;
          di = ev.key === "ArrowDown" ? Math.min(di + 1, nuts.length - 1) : Math.max(di - 1, 0);
          danhDau();
          return;
        }
        if (ev.key === "Escape") { list.hidden = true; return; }
        if (ev.key !== "Enter") return;
        ev.preventDefault();
        var cur = nuts[di] || nuts[0];
        if (cur) them(cur.getAttribute("data-add"));
        else if (seek.value.trim()) them(seek.value.trim());
      };
      var dem = host.querySelector("[data-kho-dem]");
      if (dem) {
        var nBat = (S.kho || []).filter(function (s) { return s.enabled !== false; }).length;
        dem.textContent = S._khoLoi ? S._khoLoi
          : (nBat ? "Kho có " + nBat + " skill đang bật. Mở kho để xem theo chuyên mục. Tối đa 8." : "Kho skill của brain này đang trống.");
      }
      host._ntDoc = doc;
      host._ntGhi = ghi;
      if (!S._neo) {
        S._neo = function () {
          if (!S.root) return;
          S.root.querySelectorAll(".nt-seek-list").forEach(function (l) { if (l._dat) l._dat(); });
        };
        window.addEventListener("scroll", S._neo, true);
        window.addEventListener("resize", S._neo);
      }
      host.onclick = function (ev) {
        if (ev.target.closest("[data-mo-kho]")) { ev.preventDefault(); moKho(host); return; }
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
  function dongKho() {
    var el = document.getElementById("ntKho");
    if (el) el.remove();
    document.removeEventListener("keydown", khoPhim);
    S._khoHost = null;
  }
  function khoPhim(ev) {
    if (ev.key === "Escape") dongKho();
  }
  function skillBat() {
    return (S.kho || []).filter(function (s) { return s.enabled !== false; });
  }
  function moKho(host) {
    if (!host) return;
    var cu = host.querySelector(".nt-seek-list");
    if (cu) cu.hidden = true;
    S._khoHost = host;
    S._khoNhom = "";
    S._khoQ = "";
    dongKho();
    S._khoHost = host;
    var el = document.createElement("div");
    el.id = "ntKho";
    el.className = "nt-kho";
    el.innerHTML =
      '<div class="nt-kho-panel" role="dialog" aria-label="Kho skill">' +
      '<div class="nt-kho-head"><div><b>Kho skill</b><p class="nt-hint" data-kho-tong></p></div>' +
      '<input type="search" class="nt-kho-q" placeholder="Tìm trong chuyên mục" autocomplete="off">' +
      '<button type="button" class="nt-btn" data-dong-kho>Xong</button></div>' +
      '<div class="nt-kho-body"><div class="nt-kho-cats"></div><div class="nt-kho-list"></div></div>' +
      '<div class="nt-kho-foot"><span data-kho-chon></span><button type="button" class="nt-btn ghost" data-tai-kho>Tải lại kho</button></div>' +
      "</div>";
    document.body.appendChild(el);
    el.addEventListener("click", function (ev) { if (ev.target === el) dongKho(); });
    el.querySelector("[data-dong-kho]").onclick = dongKho;
    el.querySelector(".nt-kho-q").oninput = function () { S._khoQ = this.value; veKhoList(); };
    el.querySelector("[data-tai-kho]").onclick = async function () {
      this.textContent = "Đang tải…";
      this.disabled = true;
      await taiKho();
      veKhoList();
      var nut = document.querySelector("#ntKho [data-tai-kho]");
      if (nut) { nut.textContent = "Tải lại kho"; nut.disabled = false; }
    };
    el.querySelector(".nt-kho-body").onclick = function (ev) {
      var cat = ev.target.closest("[data-nhom]");
      if (cat) { S._khoNhom = cat.getAttribute("data-nhom") || ""; veKhoList(); return; }
      var row = ev.target.closest("[data-slug]");
      if (row) doiSkill(row.getAttribute("data-slug"));
    };
    document.addEventListener("keydown", khoPhim);
    veKhoList();
    var q = el.querySelector(".nt-kho-q");
    if (q) q.focus();
  }
  function doiSkill(slug) {
    var host = S._khoHost;
    if (!host || !host._ntGhi || !host._ntDoc) return;
    slug = String(slug || "").trim().slice(0, 40);
    if (!slug) return;
    var arr = host._ntDoc();
    var i = arr.indexOf(slug);
    if (i >= 0) arr.splice(i, 1);
    else if (arr.length >= 8) return;
    else arr.push(slug);
    host._ntGhi(arr);
    veKhoList();
  }
  function veKhoList() {
    var el = document.getElementById("ntKho");
    var host = S._khoHost;
    if (!el || !host) return;
    var bat = skillBat();
    var tong = el.querySelector("[data-kho-tong]");
    if (tong) tong.textContent = S._khoLoi ? S._khoLoi : (bat.length ? bat.length + " skill đang bật trên brain này." : "Kho đang trống.");
    var da = host._ntDoc ? host._ntDoc() : [];
    var chon = el.querySelector("[data-kho-chon]");
    if (chon) chon.textContent = "Đã gắn " + da.length + "/8";
    var dem = {};
    bat.forEach(function (s) {
      var g = s.group || "Chung";
      dem[g] = (dem[g] || 0) + 1;
    });
    var nhom = Object.keys(dem).sort(function (a, b) {
      return dem[b] - dem[a] || a.localeCompare(b, "vi");
    });
    if (S._khoNhom && nhom.indexOf(S._khoNhom) < 0) S._khoNhom = "";
    var cats = '<button type="button" data-nhom="" class="' + (S._khoNhom ? "" : "on") + '">Tất cả <small>' + bat.length + "</small></button>";
    cats += nhom.map(function (g) {
      return '<button type="button" data-nhom="' + esc(g) + '" class="' + (S._khoNhom === g ? "on" : "") + '">' +
        esc(g) + " <small>" + dem[g] + "</small></button>";
    }).join("");
    el.querySelector(".nt-kho-cats").innerHTML = cats;
    var q = khongDau((S._khoQ || "").trim());
    var rows = bat.filter(function (s) {
      if (S._khoNhom && (s.group || "Chung") !== S._khoNhom) return false;
      if (!q) return true;
      return khongDau(s.name + " " + s.slug + " " + (s.description || "") + " " + (s.group || "")).indexOf(q) >= 0;
    });
    var list = el.querySelector(".nt-kho-list");
    if (!rows.length) {
      list.innerHTML = '<p class="nt-hint">Không có skill trong mục này.</p>';
      return;
    }
    list.innerHTML = rows.map(function (s) {
      var co = da.indexOf(s.slug) >= 0;
      return '<button type="button" class="nt-kho-row' + (co ? " on" : "") + '" data-slug="' + esc(s.slug) + '">' +
        '<span class="nt-sk-name">' + esc(s.name || s.slug) + "</span>" +
        '<span class="nt-sk-meta">' + esc(rut(s.description || s.slug, 110)) + "</span>" +
        '<span class="nt-kho-act">' + (co ? "Bỏ" : (da.length >= 8 ? "Đủ 8" : "Thêm")) + "</span></button>";
    }).join("");
  }
  async function taiKho() {
    var j = await api("/skills?brain=" + encodeURIComponent(brain()));
    S.kho = (j && j.skills) || [];
    S._khoLoi = S.kho.length ? "" : ((j && j.error) || "Không tải được kho skill.");
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
      '<p class="nt-lead">Setup để xếp phòng và người. Giao việc để đưa brief. Theo dõi để xem bàn làm việc và lời trao đổi.</p>' +
      '<div class="nt-tabs" role="tablist">' +
      '<button type="button" class="nt-tab' + (S.tab === "phong" ? " on" : "") + '" data-tab="phong" role="tab">Setup</button>' +
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

  function dsPhongNut() {
    var q = khongDau(S.tim || "");
    var ds = S.phong.filter(function (p) {
      if (!q) return true;
      var hay = khongDau(p.ten + " " + (p.tieu_chi || "") + " " + (p.nguoi || []).map(function (n) { return n.ten + " " + (n.vi_tri || ""); }).join(" "));
      return hay.indexOf(q) >= 0;
    });
    if (!S.phong.length) return '<p class="nt-hint">Chưa có phòng.</p>';
    if (!ds.length) return '<p class="nt-hint">Không thấy phòng khớp.</p>';
    return '<div class="nt-jobs">' + ds.map(function (p) {
      var t = truongCua(p);
      return '<button type="button" class="nt-job' + (p.slug === S.chonPhong ? " on" : "") + '" data-phong="' + esc(p.slug) + '">' +
        "<b>" + esc(p.ten) + "</b><small>" + (p.cach_lam === "lan_luot" ? "Lần lượt" : "Cùng làm") +
        " · " + (t ? esc(t.ten) : "Chưa có trưởng") +
        " · " + (p.nguoi || []).length + " người</small></button>";
    }).join("") + "</div>";
  }

  function formTaoPhong() {
    return '<form id="ntTaoPhong" class="nt-form nt-side">' +
      '<p class="nt-kicker">Phòng mới</p>' +
      '<label>Tên<input name="ten" required placeholder="Marketing" autocomplete="off"></label>' +
      '<label>Cách làm<select name="cach_lam"><option value="lan_luot">Làm lần lượt</option><option value="cung">Làm cùng</option></select></label>' +
      '<button class="nt-btn pri" type="submit">Tạo phòng</button>' +
      '<p class="nt-hint">Lần lượt: người trước xong mới bàn giao người sau. Sơ đồ phòng hiện bên phải.</p></form>';
  }

  function formThemNguoi() {
    var p = phongChon();
    if (!p) return "";
    return '<form id="ntThemNguoi" class="nt-form nt-side">' +
      '<p class="nt-kicker">Thêm vào ' + esc(p.ten) + "</p>" +
      '<label>Tên<input name="ten" required placeholder="An" autocomplete="off"></label>' +
      '<label>Vị trí<input name="vi_tri" placeholder="Chuyên viên thiết kế" autocomplete="off"></label>' +
      '<label>Vai<select name="vai"><option value="thanh_vien">Thành viên</option><option value="truong">Trưởng phòng</option></select></label>' +
      '<p class="nt-hint">Đặt trưởng thì người đang giữ vị trí đó xuống thành viên.</p>' +
      '<label>Tính cách<textarea name="tinh_cach" placeholder="Thẳng, không viết hộ"></textarea></label>' +
      oSkill([]) +
      '<label>Trợ lý gốc<select name="agent">' + agentOpts() + "</select></label>" +
      '<button class="nt-btn pri" type="submit">Thêm người</button></form>';
  }

  function tabPhong() {
    return '<div class="nt-setup"><aside class="nt-rail"><h2>Setup</h2>' +
      '<label class="nt-tim">Tìm<input id="ntTim" type="search" placeholder="Phòng, người, vị trí" value="' + esc(S.tim || "") + '"></label>' +
      '<div id="ntDsPhong">' + dsPhongNut() + "</div>" + formTaoPhong() + formThemNguoi() +
      '</aside><div class="nt-stage">' + thanPhong() + "</div></div>";
  }

  function viecChoPhong(slug) {
    var ds = S.viec.filter(function (v) { return (v.phong || []).indexOf(slug) >= 0; });
    return ds.filter(function (v) { return v.trang_thai === "dang_chay"; })[0] || ds[0] || null;
  }

  function viecHien() {
    var p = phongChon();
    var v = S._viecDay;
    if (!p || !v || (v.phong || []).indexOf(p.slug) < 0) return null;
    return v;
  }

  function laDang(d, n, slug) {
    return !!(d && d.phong === slug && d.ten === n.ten);
  }

  function rotCuoi(v, room, ns) {
    var rows = ((v && v.loi) || []).filter(function (r) { return r.slug === ns && (r.phong === room || r.lop === "hop"); });
    return rows.length ? rows[rows.length - 1] : null;
  }

  function rotNgan(row) {
    if (!row) return "";
    if (row.lop === "nhan" && row.quyet === "OK") return "Đã nhận";
    if (row.lop === "nhan") return "Chưa nhận";
    if (row.lop === "doi") return "Đang trả lời";
    if (row.lop === "lam") return "Đã làm";
    if (row.lop === "giao") return "Đã xếp việc";
    if (row.lop === "kiem") return row.quyet === "DAT" ? "Đạt" : "Chưa đạt";
    if (row.lop === "xu") return "Đã xử";
    if (row.lop === "hop") return row.quyet === "DAT" ? "Họp đạt" : "Họp chưa đạt";
    return LOP[row.lop] || "";
  }

  function dayViec(p, v) {
    var xep = v && v.xep && v.xep[p.slug];
    if (xep && xep.length) {
      return xep.map(function (n) {
        return (p.nguoi || []).filter(function (x) { return x.slug === n.slug; })[0] || n;
      });
    }
    return (p.nguoi || []).filter(function (n) { return n.vai !== "truong"; });
  }

  function banNguoi(n, slug, d, so) {
    var bat = laDang(d, n, slug);
    var ngan = bat ? ({
      giao: "Đang xếp việc", lam: "Đang làm", nhan: "Đang xem bài", doi: "Đang trả lời",
      kiem: "Đang phản hồi", xu: "Đang xử", hop: "Đang họp", sua: "Mang lệnh về"
    })[d.buoc] || "Đang làm" : rotNgan(rotCuoi(viecHien(), slug, n.slug));
    return '<button type="button" class="nt-desk' + (n.vai === "truong" ? " head" : "") + (bat ? " on" : "") + '" data-sua="' + esc(n.slug) + '">' +
      '<span class="nt-ava" aria-hidden="true">' + esc((n.ten || "?").slice(0, 1)) + "</span>" +
      '<span class="nt-seat" aria-hidden="true"></span>' +
      (so ? '<span class="nt-pill run">Bước ' + so + "</span>" : "") +
      "<b>" + esc(n.ten) + "</b>" +
      "<small>" + esc(n.vi_tri || (n.vai === "truong" ? "Trưởng phòng" : "Thành viên")) + "</small>" +
      (ngan ? "<em>" + esc(ngan) + "</em>" : "") +
      "</button>";
  }

  function htmlMap() {
    var p = phongChon();
    if (!p) return "";
    var v = viecHien();
    var d = v && v.trang_thai === "dang_chay" ? v.dang_lam : null;
    var lan = p.cach_lam === "lan_luot";
    var truong = truongCua(p);
    var day = dayViec(p, v);
    var khac = "";
    if (v && (v.phong || []).length > 1) {
      khac = '<div class="nt-links">' + v.phong.map(function (slug, i) {
        var q = S.phong.filter(function (x) { return x.slug === slug; })[0];
        var ten = q ? q.ten : slug;
        var run = d && d.phong === slug;
        return (i ? '<span class="nt-linkbar' + (run ? " on" : "") + '"></span>' : "") +
          '<button type="button" class="nt-roomlink' + (slug === p.slug ? " on" : "") + (run ? " run" : "") + '" data-phong="' + esc(slug) + '">' +
          (q && q.icon ? '<img alt="" src="' + esc(q.icon) + '">' : '<span class="nt-ava">' + esc((ten || "?").slice(0, 1)) + "</span>") +
          "<b>" + esc(ten) + "</b>" + (run ? "<small>đang làm</small>" : "") + "</button>";
      }).join("") + "</div>";
    }
    function noiNhau(a, b) {
      if (!d || d.phong !== p.slug || !a || !b) return "";
      var ab = d.ten === a.ten && d.giao_cho && d.giao_cho.indexOf(b.ten) >= 0;
      var ba = d.ten === b.ten && d.giao_cho && d.giao_cho.indexOf(a.ten) >= 0;
      if (!ab && !ba) return "";
      var doiThoai = d.buoc === "nhan" || d.buoc === "doi" || d.buoc === "chia" || d.buoc === "dap" || d.buoc === "gop";
      return doiThoai ? "talk" : "go";
    }
    function mui(loai) {
      var nhan = loai === "talk" ? "Đang trao đổi" : "Đưa tới";
      return '<span class="nt-arrow' + (loai ? " " + loai : "") + '"><span class="nt-aline"></span><i>' + nhan + "</i></span>";
    }
    var oNgoai = d && d.phong && d.phong !== p.slug;
    var xuong = lan && truong && day[0] ? '<div class="nt-down">' + mui(noiNhau(truong, day[0])) + "</div>" : "";
    var luong = day.map(function (n, i) {
      var muiTen = lan && i < day.length - 1 ? mui(noiNhau(n, day[i + 1])) : "";
      return banNguoi(n, p.slug, d, lan ? i + 1 : 0) + muiTen;
    }).join("");
    return khac +
      '<p class="nt-kicker">' + esc(p.ten) + " · " + (lan ? "Làm lần lượt" : "Làm cùng") + "</p>" +
      (v ? '<p class="nt-hint">' + esc(v.tieu_de || "") + (oNgoai ? " · việc đang xử lý ở " + esc(d.phong_ten || "phòng khác") : "") + "</p>" : '<p class="nt-hint">Chưa có việc. Giao ở tab Giao việc, rồi bấm Chạy.</p>') +
      '<div class="nt-roombox">' +
      (truong ? '<div class="nt-headrow">' + banNguoi(truong, p.slug, d, 0) + "</div>" : '<p class="nt-call">Chưa có trưởng.</p>') +
      xuong +
      (luong ? '<div class="nt-flow">' + luong + "</div>" : '<p class="nt-hint">Chưa có người ngồi bàn. Thêm ở cột trái.</p>') +
      '<p class="nt-hint">Tiêu chí: ' + esc(p.tieu_chi || "") + "</p></div>";
  }

  function htmlTalk() {
    var p = phongChon();
    var v = viecHien();
    if (!p) return "";
    if (!v) return "<h3>Giao tiếp</h3>" + '<p class="nt-hint">Chưa có lời. Khi chạy, hỏi đáp và bàn giao hiện ở đây.</p>';
    var rows = (v.loi || []).slice().reverse();
    return "<h3>Giao tiếp</h3>" + htmlKet(v) +
      '<p class="nt-hint">' + esc(v.tieu_de || "") + " · " + esc((TRANG[v.trang_thai] || [v.trang_thai || ""])[0]) + "</p>" +
      dangLam(v) +
      '<div class="nt-log" id="ntLogPhong">' + (nhomLoi(rows) || '<p class="nt-hint">' + (v.trang_thai === "dang_chay" ? "Đang chờ lời đầu tiên." : "Chưa có lời nào.") + "</p>") + "</div>";
  }

  function thanPhong() {
    var p = phongChon();
    if (!p) return "<h2>Setup</h2>" +
      '<p class="nt-hint">Tạo phòng ở cột trái. Bấm phòng để sửa tên, tiêu chí, người và thứ tự.</p>';
    var t = truongCua(p);
    var lan = p.cach_lam === "lan_luot";
    var tong = lan ? (p.nguoi || []).filter(function (n) { return n.vai !== "truong"; }).length : 0;
    var buoc = 0;
    var nguoi = (p.nguoi || []).map(function (n) {
      var so = 0;
      if (lan && n.vai !== "truong") { buoc += 1; so = buoc; }
      return theNguoi(n, so, tong);
    }).join("");
    return '<div class="nt-setup-body">' +
      '<h2>' + esc(p.ten) + "</h2>" +
      (p.icon ? '<img class="nt-icon" alt="" src="' + esc(p.icon) + '">' : "") +
      '<form id="ntIcon" class="nt-form"><label>Icon phòng<input name="icon" type="file" accept="image/*"></label>' +
      '<p class="nt-hint">Ảnh nhỏ, hiện trên bàn làm việc ở tab Theo dõi.</p></form>' +
      '<details class="nt-details" open><summary>Sửa phòng, vị trí và thứ tự</summary>' +
      '<form id="ntCach" class="nt-form">' +
      '<label>Cách làm<select name="cach_lam">' +
      '<option value="lan_luot"' + (lan ? " selected" : "") + ">Làm lần lượt</option>" +
      '<option value="cung"' + (lan ? "" : " selected") + ">Làm cùng</option></select></label>" +
      '<p class="nt-hint">' + (lan
        ? "Thứ tự bên dưới là quy trình có sẵn. Khi có việc, trưởng xem brief và được xếp lại. Bước sau chưa hiểu thì nói lại với bước trước. Nhận rồi mới làm và chuyển tiếp."
        : "Mọi người nhận cùng brief và viết phần mình. Trưởng đọc bản ghép rồi phản hồi.") +
      "</p></form>" +
      (t ? '<p class="nt-hint"><span class="nt-pill ok">Trưởng</span> ' + esc(t.ten) +
        (t.vi_tri ? " · " + esc(t.vi_tri) : " · chưa đặt vị trí") + "</p>"
        : '<p class="nt-call">Chưa có trưởng. Thêm người ở cột trái và chọn vai Trưởng phòng.</p>') +
      '<form id="ntSuaTieu" class="nt-form">' +
      '<label>Tên phòng<input name="ten" required value="' + esc(p.ten || "") + '"></label>' +
      '<label>Tiêu chí trưởng giữ<textarea name="tieu_chi" required>' + esc(p.tieu_chi || "") + "</textarea></label>" +
      '<div class="nt-row"><button class="nt-btn pri" type="submit">Lưu tiêu chí</button>' +
      '<button type="button" class="nt-btn danger" id="ntXoaPhong">Xoá phòng</button></div></form>' +
      (nguoi ? '<div class="nt-people">' + nguoi + "</div>" : '<p class="nt-hint">Chưa có người. Thêm ở cột trái.</p>') +
      "</details></div>";
  }

  function theNguoi(n, so, tong) {
    if (S.sua === n.slug) {
      return '<form class="nt-card nt-form" id="ntSuaNguoi">' +
        "<b>" + esc(n.ten) + "</b>" +
        '<label>Vị trí<input name="vi_tri" value="' + esc(n.vi_tri || "") + '" placeholder="Chuyên viên thiết kế"></label>' +
        '<label>Vai<select name="vai"><option value="thanh_vien"' + (n.vai !== "truong" ? " selected" : "") +
        '>Thành viên</option><option value="truong"' + (n.vai === "truong" ? " selected" : "") +
        ">Trưởng phòng</option></select></label>" +
        '<p class="nt-hint">Đặt trưởng thì trưởng hiện tại xuống thành viên. Mỗi phòng một trưởng.</p>' +
        '<label>Tính cách<textarea name="tinh_cach">' + esc(n.tinh_cach || "") + "</textarea></label>" +
        oSkill(n.skills || []) +
        '<div class="nt-row"><button class="nt-btn pri" type="submit">Lưu</button>' +
        '<button type="button" class="nt-btn ghost" id="ntHuySua">Huỷ</button></div></form>';
    }
    var sk = (n.skills || []).map(function (s) { return '<span class="nt-pill">' + esc(skillTen(s)) + "</span>"; }).join(" ");
    var thu = so ? '<span class="nt-pill run">Bước ' + so + "</span> " : "";
    var xep = so ? '<button type="button" class="nt-btn ghost" data-len="' + esc(n.slug) + '"' + (so <= 1 ? " disabled" : "") + ">Lên</button>" +
      '<button type="button" class="nt-btn ghost" data-xuong="' + esc(n.slug) + '"' + (so >= tong ? " disabled" : "") + ">Xuống</button>" : "";
    return '<article class="nt-card nt-member"><div><b>' + esc(n.ten) + "</b> " + thu +
      (n.vai === "truong" ? '<span class="nt-pill ok">Trưởng phòng</span>' : '<span class="nt-pill">Thành viên</span>') +
      '<p class="nt-vi-tri">' + (n.vi_tri ? esc(n.vi_tri) : "Chưa đặt vị trí") + "</p>" +
      "<p>" + esc(n.tinh_cach || "Chưa viết tính cách.") + "</p>" +
      (sk ? '<p class="nt-chips">' + sk + "</p>" : '<p class="nt-hint">Chưa gán skill.</p>') +
      '</div><div class="nt-row">' + xep +
      '<button type="button" class="nt-btn ghost" data-sua="' + esc(n.slug) + '">Sửa vị trí</button>' +
      '<button type="button" class="nt-btn ghost" data-xoa-nguoi="' + esc(n.slug) + '" data-ten="' + esc(n.ten) + '">Bỏ khỏi phòng</button></div></article>';
  }

  function tabGiao() {
    if (!S.phong.length) {
      return "<h2>Giao việc</h2>" +
        '<p class="nt-hint">Chưa có phòng. Tạo phòng ở tab Setup trước.</p>' +
        '<button type="button" class="nt-btn" data-tab="phong">Về tab Setup</button>';
    }
    if (!S.phong.some(truongCua)) {
      return "<h2>Giao việc</h2>" +
        '<p class="nt-call">Chưa giao được. Mỗi phòng tham gia cần một trưởng.</p>' +
        '<button type="button" class="nt-btn" data-tab="phong">Về tab Setup</button>';
    }
    return "<h2>Giao việc</h2>" +
      '<p class="nt-hint">Viết brief, chọn phòng, rồi bấm Giao việc. Việc vừa giao mở ở tab Theo dõi. Bấm Chạy ở đó để các trưởng bắt đầu.</p>' +
      formViec();
  }

  function tabViec() {
    if (!S.phong.length) {
      return "<h2>Theo dõi</h2>" +
        '<p class="nt-hint">Chưa có phòng. Tạo phòng ở tab Setup trước.</p>' +
        '<button type="button" class="nt-btn" data-tab="phong">Về tab Setup</button>';
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
      '<label class="full">Tài liệu tham khảo, tối đa 3 file chữ<input name="tai_lieu" type="file" accept=".txt,.md,.csv,.json,.html" multiple></label>' +
      '<p class="nt-hint full">File để hệ thống đọc khi triển khai. PDF hãy dán chữ vào brief.</p>' +
      '<span class="nt-lbl full">Phòng tham gia, thứ tự từ trên xuống là lộ trình<div class="nt-chips">' + hop + "</div></span>" +
      '<p class="nt-hint full">Hết vòng thì dừng và ghi chỗ còn mở. Không sửa mãi. Trong từng phòng, thứ tự người đặt ở Setup.</p>' +
      '<div class="nt-row full"><button class="nt-btn pri" type="submit">Giao việc</button></div></form>';
  }

  function dsViec() {
    if (!S.viec.length) return '<p class="nt-hint">Chưa có việc. Bấm Giao việc mới.</p>';
    return '<div class="nt-jobs">' + S.viec.map(function (v) {
      return '<button type="button" class="nt-job' + (v.id === S.chonViec ? " on" : "") + '" data-viec="' + esc(v.id) + '">' +
        "<b>" + esc(v.tieu_de) + "</b><small>" + esc((TRANG[v.trang_thai] || [v.trang_thai || ""])[0]) + "</small></button>";
    }).join("") + "</div>";
  }

  function dangLam(v) {
    var d = v && v.dang_lam;
    if (!d || v.trang_thai !== "dang_chay") return "";
    var tenBuoc = { giao: "đang xem việc để xếp bước", lam: "đang làm", kiem: "đang phản hồi", hop: "đang họp", sua: "đang mang lệnh về", nhan: "đang xem bàn giao", doi: "đang trả lời", xu: "đang xử lý chỗ chưa thống nhất", chia: "đang góp ý phòng khác", dap: "đang đáp lại", gop: "đang trao đổi trong phòng", ket: "đang viết kết quả" };
    var ai = d.ten + (d.vi_tri ? " · " + d.vi_tri : "");
    var cau = ai + " " + (tenBuoc[d.buoc] || "đang làm");
    if (d.phong_ten) cau += " · phòng " + d.phong_ten;
    if (d.buoc === "nhan" && d.giao_cho) cau = ai + " đang xem bài của " + d.giao_cho + ". Chưa ổn thì nói lại, nhận rồi mới làm";
    else if (d.buoc === "doi" && d.giao_cho) cau = ai + " đang trả lời " + d.giao_cho;
    else if (d.buoc === "lam" && d.giao_cho) cau += ". Xong sẽ bàn giao cho " + d.giao_cho;
    else if (d.giao_cho && d.buoc !== "giao") cau += ". Với " + d.giao_cho;
    return '<p class="nt-live">' + esc(cau) + ".</p>";
  }

  function soDo(v) {
    return (v.phong || []).map(function (slug) {
      var p = S.phong.filter(function (x) { return x.slug === slug; })[0];
      if (!p) return "";
      var xep = (v.xep || {})[slug];
      var day = "";
      var nhan = p.cach_lam === "lan_luot" ? "Lần lượt" : "Cùng làm";
      if (xep && xep.length) {
        nhan = "Trưởng xếp theo việc";
        day = xep.map(function (n, i) {
          return (i + 1) + ". " + n.ten + (n.vi_tri ? " · " + n.vi_tri : "");
        }).join(" → ");
      } else {
        day = (p.nguoi || []).filter(function (n) { return n.vai !== "truong"; }).map(function (n, i) {
          return (i + 1) + ". " + n.ten + (n.vi_tri ? " · " + n.vi_tri : "");
        }).join(" → ");
      }
      return "<p class=\"nt-hint\"><b>" + esc(p.ten) + "</b> · " + nhan +
        (day ? " · " + esc(day) : "") + "</p>";
    }).join("");
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

  function lienKet(text) {
    return esc(text).replace(/https?:\/\/[^\s<&]+/g, function (raw) {
      var u = raw.replace(/[),.;:]+$/g, "");
      var du = raw.slice(u.length);
      if (!u) return raw;
      return '<a href="' + u + '" target="_blank" rel="noopener noreferrer">' + u + "</a>" + du;
    });
  }

  function htmlBanPhong(v) {
    var ban = v.ban || {};
    var body = Object.keys(ban).map(function (slug) {
      var t = String(ban[slug] || "").trim();
      if (!t) return "";
      return "<h4>" + esc(tenPhong(slug)) + "</h4><p>" + lienKet(t) + "</p>";
    }).join("");
    if (!body) return "";
    var mo = (v.ket_qua || "").trim() ? "" : " open";
    return '<details class="nt-ban-day"' + mo + "><summary>Bản từng phòng</summary>" + body + "</details>";
  }

  function htmlKet(v) {
    if (!v || (v.trang_thai !== "xong" && v.trang_thai !== "lech" && v.trang_thai !== "dung")) return "";
    var co = (v.ket_qua || "").trim();
    var pdf = "/nhac-truong/viec/" + encodeURIComponent(v.id) + "/ket-qua?brain=" + encodeURIComponent(brain());
    var md = "nhac-truong/viec/" + v.id + ".md";
    var tl = (v.tai_lieu || []).map(function (f) { return "<li>" + esc((f && f.ten) || "tài liệu") + "</li>"; }).join("");
    var tieu = v.trang_thai === "lech" ? "Kết quả, còn lệch" : (v.trang_thai === "dung" ? "Kết quả khi dừng" : "Kết quả cuối");
    return '<section class="nt-ket"><h3>' + tieu + "</h3>" +
      '<p class="nt-ket-links"><a href="' + esc(pdf) + '" target="_blank" rel="noopener noreferrer">Trang kết quả / PDF</a>' +
      '<button type="button" class="nt-mo-ban" data-md="' + esc(md) + '">Mở biên bản đầy đủ</button></p>' +
      "<p class=\"nt-hint\">Trạng thái: " + esc((TRANG[v.trang_thai] || [v.trang_thai || ""])[0]) +
      (v.tieu_de ? " · " + esc(v.tieu_de) : "") + "</p>" +
      (co ? "<p>" + lienKet(co) + "</p>" : '<p class="nt-hint">Chưa có đoạn kết. Phần đã làm nằm ở bản từng phòng và file biên bản.</p>') +
      ((v.mo || []).length ? "<ul class=\"nt-mo\">" + v.mo.map(function (m) { return "<li>" + esc(m) + "</li>"; }).join("") + "</ul>" : "") +
      (v.loi_chay ? '<p class="nt-err">' + esc(v.loi_chay) + "</p>" : "") +
      htmlBanPhong(v) +
      (tl ? '<p class="nt-hint">Tài liệu đã đưa</p><ul class="nt-mo">' + tl + "</ul>" : "") +
      '<form id="ntThem" class="nt-form">' +
      '<label>Sửa thêm<textarea name="comment" placeholder="Giữ kết quả cũ, chỉ sửa chỗ này"></textarea></label>' +
      '<div class="nt-row"><button class="nt-btn pri" type="submit">Chạy lại với comment</button></div></form>' +
      '<p class="nt-hint">Hệ thống giữ bản cũ và comment này, không làm lại từ đầu.</p></section>';
  }

  function moPdf() {
    var v = viecHien() || S._viecDay;
    if (!v) return;
    window.open("/nhac-truong/viec/" + encodeURIComponent(v.id) + "/ket-qua?brain=" + encodeURIComponent(brain()), "_blank");
  }

  function moBanDay(ev) {
    var rel = ev.currentTarget.getAttribute("data-md") || "";
    if (rel && window.JavisOpenNote) {
      window.JavisOpenNote(rel);
      return;
    }
    moPdf();
  }

  function ganPdf() {
    if (!S.root) return;
    S.root.querySelectorAll(".nt-pdf").forEach(function (b) { b.onclick = moPdf; });
    S.root.querySelectorAll(".nt-mo-ban").forEach(function (b) { b.onclick = moBanDay; });
  }

  function theoDoi() {
    var v = S._viecDay;
    if (!v) return '<p class="nt-hint">Chọn một việc để xem biên bản.</p>';
    var chay = v.trang_thai === "dang_chay";
    var treo = chay && v.song === false;
    var loi = "";
    var hienBan = v.trang_thai === "xong" || v.trang_thai === "lech" || v.trang_thai === "dung";
    var nutChay = treo ? "Khởi động lại" : (chay ? "Đang chạy" : (v.trang_thai === "dung" || v.trang_thai === "loi" ? "Chạy lại" : "Chạy"));
    return '<div class="nt-row">' + pillTrang(treo ? "loi" : v.trang_thai) + "<b>" + esc(v.tieu_de) + "</b></div>" +
      (treo ? '<p class="nt-err">Việc đang ghi là chạy nhưng không còn tiến. Bấm Khởi động lại hoặc Dừng.</p>' : "") +
      '<p class="nt-hint">' + esc(v.brief || "") + "</p>" +
      (v.loi_chay ? '<p class="nt-err">' + esc(v.loi_chay) + "</p>" : "") +
      soDo(v) + nutThuTu(v) + dangLam(v) + buoc(v) +
      '<div class="nt-row">' +
      '<button type="button" class="nt-btn pri" id="ntChay"' + (chay && !treo ? " disabled" : "") + ">" + nutChay + "</button>" +
      (chay ? '<button type="button" class="nt-btn danger" id="ntDung">Dừng</button>' : "") +
      '<button type="button" class="nt-btn" id="ntThu"' + (chay && !treo ? " disabled" : "") + ">Chạy thử</button>" +
      (chay ? "" : '<button type="button" class="nt-btn danger" id="ntXoaViec">Xoá việc</button>') +
      "</div>" +
      '<div class="nt-office"><div class="nt-office-map" id="ntMap">' + htmlMap() +
      '</div><aside class="nt-office-talk" id="ntTalk">' + htmlTalk() + "</aside></div>" +
      (hienBan ? "" : "");
  }

  function loiSach(text) {
    return String(text || "").split("\n").filter(function (line) {
      return !/^\s*(quyet|quyết|sua|sửa|tra|nhan|nhận|thu[_ ]?tu|thứ tự)\s*:/i.test(line);
    }).join("\n").trim();
  }

  function mauTen(slug) {
    var n = 0;
    var s = String(slug || "x");
    for (var i = 0; i < s.length; i++) n = (n + s.charCodeAt(i) * (i + 3)) % MAU_TEN.length;
    return MAU_TEN[n];
  }

  function veGiao(row) {
    if (!row.giao_cho) return "";
    var ngan = { nhan: "xem bài của", doi: "trả lời", chia: "góp ý", dap: "đáp", gop: "trao đổi với" };
    return '<span class="nt-to">' + (ngan[row.lop] || "với") + " " + esc(row.giao_cho) + "</span>";
  }

  function nhomLoi(rows) {
    var out = "";
    var khoa = "";
    var hoi = { nhan: 1, kiem: 1, chia: 1, gop: 1, hop: 1, xu: 1, giao: 1 };
    rows.forEach(function (row) {
      var pha = (row.lop === "hop" || row.lop === "chia" || row.lop === "dap" ? "Giữa các phòng" : (row.phong_ten || "Trong phòng")) + " · vòng " + row.vong;
      if (pha !== khoa) { khoa = pha; out += '<div class="nt-phase">' + esc(pha) + "</div>"; }
      var kieu = hoi[row.lop] ? "hoi" : "tra";
      out += '<article class="nt-say ' + kieu + '"><header><b style="color:' + mauTen(row.slug) + '">' + esc(row.ten) + "</b>" +
        '<span class="nt-meta">' + esc(row.vi_tri || (row.vai === "truong" ? "Trưởng" : "Thành viên")) +
        " · " + esc(LOP[row.lop] || row.lop) + "</span>" +
        pillQuyet(row.quyet, row.lop) + veGiao(row) + "</header>" +
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
        if ((id === "viec" || id === "phong") && S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
      };
    });
    var tao = document.getElementById("ntTaoPhong");
    if (tao) tao.onsubmit = async function (ev) {
      ev.preventDefault();
      var btn = nutGui(tao, ev);
      if (!bam(btn, "Đang tạo…")) return;
      var fd = new FormData(tao);
      try {
        var j = await post("/nhac-truong/phong", {
          brain: brain(), ten: fd.get("ten"), tieu_chi: fd.get("tieu_chi"), cach_lam: fd.get("cach_lam"),
        });
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
        S._khoaPhong = "";
        var vv = viecChoPhong(id);
        if (vv && vv.id !== S.chonViec) {
          S.chonViec = vv.id;
          moViec().then(function () {
            ve(true);
            if (S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
          });
          return;
        }
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
          vi_tri: fd.get("vi_tri"),
        });
        if (!j.ok) return hong(btn, j.error);
        var p = phongChon();
        if (p && j.phong) p.nguoi = j.phong.nguoi || [];
        else if (p) p.nguoi.push(j.nguoi);
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
        var tai = [];
        var inp = tv.querySelector('input[name="tai_lieu"]');
        try { tai = await docTaiLieu(inp); }
        catch (e) { S.ban = false; return hienLoi(e.message || "Không đọc được file."); }
        var xep = {};
        fd.getAll("phong").forEach(function (slug) {
          var p = S.phong.filter(function (x) { return x.slug === slug; })[0];
          if (!p) return;
          xep[slug] = (p.nguoi || []).filter(function (n) { return n.vai !== "truong"; }).map(function (n) { return n.slug; });
        });
        var j = await post("/nhac-truong/viec", {
          brain: brain(), tieu_de: fd.get("tieu_de"), brief: fd.get("brief"),
          phong: fd.getAll("phong"), vong: fd.get("vong"), tai_lieu: tai, xep: xep,
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
    var cach = document.getElementById("ntCach");
    if (cach) cach.onchange = async function () {
      var fd = new FormData(cach);
      var p = phongChon();
      if (!p || S.ban) return;
      S.ban = true;
      try {
        var j = await post("/nhac-truong/phong/" + encodeURIComponent(p.slug), {
          brain: brain(), cach_lam: fd.get("cach_lam"),
        });
        S.ban = false;
        if (!j.ok) return hienLoi(j.error);
        p.cach_lam = j.phong.cach_lam;
        ve();
      } catch (e) { S.ban = false; hienLoi("Không kết nối được."); }
    };
    S.root.querySelectorAll("[data-len],[data-xuong]").forEach(function (b) {
      b.onclick = async function () {
        if (S.ban || b.disabled) return;
        var ns = b.getAttribute("data-len") || b.getAttribute("data-xuong");
        var huong = b.getAttribute("data-len") ? "len" : "xuong";
        if (!bam(b, "…")) return;
        try {
          var j = await post("/nhac-truong/phong/" + encodeURIComponent(S.chonPhong) + "/nguoi/" + encodeURIComponent(ns) + "/thu-tu", {
            brain: brain(), huong: huong,
          });
          if (!j.ok) return hong(b, j.error);
          var p = phongChon();
          if (p && j.phong) p.nguoi = j.phong.nguoi || [];
          S.ban = false;
          ve();
        } catch (e) { hong(b, "Không kết nối được."); }
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
          brain: brain(), tieu_chi: fd.get("tieu_chi"), ten: fd.get("ten"),
        });
        if (!j.ok) return hong(btn, j.error);
        var p = phongChon();
        if (p) { p.tieu_chi = j.phong.tieu_chi; p.ten = j.phong.ten; }
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
          brain: brain(), tinh_cach: fd.get("tinh_cach"), skills: fd.get("skills"),
          vai: fd.get("vai"), vi_tri: fd.get("vi_tri"),
        });
        if (!j.ok) return hong(btn, j.error);
        var p = phongChon();
        if (p && j.phong) p.nguoi = j.phong.nguoi || [];
        else if (p) p.nguoi = (p.nguoi || []).map(function (n) { return n.slug === j.nguoi.slug ? j.nguoi : n; });
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
    var tim = document.getElementById("ntTim");
    if (tim) tim.oninput = function () {
      S.tim = tim.value;
      var box = document.getElementById("ntDsPhong");
      if (box) box.innerHTML = dsPhongNut();
      S.root.querySelectorAll("[data-phong]").forEach(function (b) {
        if (b.classList.contains("nt-roomlink")) return;
        b.onclick = function () {
          var id = b.getAttribute("data-phong");
          if (!id || id === S.chonPhong) return;
          S.chonPhong = id;
          S.sua = "";
          S.loi = "";
          ve();
        };
      });
    };
    var icon = document.getElementById("ntIcon");
    if (icon) icon.icon.onchange = async function () {
      var f = icon.icon.files && icon.icon.files[0];
      if (!f || !S.chonPhong) return;
      try {
        var data = await nenIcon(f);
        var j = await post("/nhac-truong/phong/" + encodeURIComponent(S.chonPhong) + "/icon", { brain: brain(), data: data });
        if (!j.ok) return hienLoi(j.error);
        var p = phongChon();
        if (p) p.icon = j.phong.icon || "";
        ve();
      } catch (e) { hienLoi(e.message || "Không đọc được ảnh."); }
    };
    ganTheoDoi();
    ganPdf();
  }

  function nutThuTu(v) {
    if (!v || v.trang_thai === "dang_chay" || (v.phong || []).length < 2) return "";
    return '<div class="nt-order"><p class="nt-kicker">Thứ tự phòng</p>' + (v.phong || []).map(function (slug, i) {
      return '<span class="nt-chip">' + esc(tenPhong(slug)) +
        '<button type="button" class="nt-btn ghost" data-phong-len="' + esc(slug) + '"' + (i ? "" : " disabled") + ">Lên</button>" +
        '<button type="button" class="nt-btn ghost" data-phong-xuong="' + esc(slug) + '"' + (i < v.phong.length - 1 ? "" : " disabled") + ">Xuống</button></span>";
    }).join("") + "</div>";
  }

  function docTaiLieu(input) {
    var files = Array.prototype.slice.call((input && input.files) || []);
    if (files.length > 3) return Promise.reject(new Error("Chỉ nhận tối đa 3 file."));
    return Promise.all(files.map(function (f) {
      if (f.size > 400000) return Promise.reject(new Error("File quá lớn: " + f.name));
      return f.text().then(function (text) {
        text = String(text || "").trim();
        if (!text) return null;
        return { ten: f.name, noi_dung: text.slice(0, 6000) };
      });
    })).then(function (xs) { return xs.filter(Boolean); });
  }

  async function dungViec() {
    if (!S.chonViec || S.ban) return;
    S.ban = true;
    S.loi = "";
    var j;
    try {
      j = await post("/nhac-truong/viec/" + encodeURIComponent(S.chonViec) + "/dung", { brain: brain() });
    } catch (e) {
      j = { ok: false, error: "Không kết nối được." };
    }
    S.ban = false;
    if (!j.ok) return hienLoi(j.error);
    if (j.viec) S._viecDay = j.viec;
    else if (S._viecDay) S._viecDay.trang_thai = "dung";
    S._khoa = "";
    capNhatTheoDoi();
    batPoll();
  }

  async function chayThem(comment) {
    comment = String(comment || "").trim();
    if (!comment) return hienLoi("Viết comment muốn sửa.");
    if (!S.chonViec || S.ban) return;
    S.ban = true;
    S.loi = "";
    var j;
    try {
      j = await post("/nhac-truong/viec/" + encodeURIComponent(S.chonViec) + "/chay-them", {
        brain: brain(), comment: comment, thu_tu: (S._viecDay && S._viecDay.phong) || [],
      });
    } catch (e) {
      j = { ok: false, error: "Không kết nối được." };
    }
    S.ban = false;
    if (!j.ok) return hienLoi(j.error);
    if (j.viec) {
      S._viecDay = j.viec;
      S._khoa = "";
      capNhatTheoDoi();
      return;
    }
    if (S._viecDay) S._viecDay.trang_thai = "dang_chay";
    S._khoa = "";
    capNhatTheoDoi();
    batPoll();
  }

  async function doiThuTu(slug, huong) {
    var v = S._viecDay;
    if (!v || !slug) return;
    var ds = (v.phong || []).slice();
    var i = ds.indexOf(slug);
    var j = huong === "len" ? i - 1 : i + 1;
    if (i < 0 || j < 0 || j >= ds.length) return;
    var tmp = ds[i];
    ds[i] = ds[j];
    ds[j] = tmp;
    var r = await post("/nhac-truong/viec/" + encodeURIComponent(v.id) + "/thu-tu", { brain: brain(), phong: ds });
    if (!r.ok) return hienLoi(r.error);
    S._viecDay = r.viec;
    S._khoa = "";
    capNhatTheoDoi();
  }

  function nenIcon(file) {
    return new Promise(function (ok, fail) {
      var img = new Image();
      var url = URL.createObjectURL(file);
      img.onload = function () {
        var c = document.createElement("canvas");
        var m = 96;
        var s = Math.min(m / img.width, m / img.height, 1);
        c.width = Math.max(1, Math.round(img.width * s));
        c.height = Math.max(1, Math.round(img.height * s));
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        ok(c.toDataURL("image/jpeg", 0.82));
      };
      img.onerror = function () {
        URL.revokeObjectURL(url);
        fail(new Error("Không đọc được ảnh."));
      };
      img.src = url;
    });
  }

  function ganTheoDoi() {
    var chay = document.getElementById("ntChay");
    if (chay) chay.onclick = function () { batDau(false); };
    var thu = document.getElementById("ntThu");
    if (thu) thu.onclick = function () { batDau(true); };
    var dung = document.getElementById("ntDung");
    if (dung) dung.onclick = function () { dungViec(); };
    var them = document.getElementById("ntThem");
    if (them) them.onsubmit = function (ev) {
      ev.preventDefault();
      var fd = new FormData(them);
      chayThem(fd.get("comment") || "");
    };
    if (!S.root) return;
    S.root.querySelectorAll("[data-phong-len],[data-phong-xuong]").forEach(function (b) {
      b.onclick = function () {
        doiThuTu(b.getAttribute("data-phong-len") || b.getAttribute("data-phong-xuong"), b.hasAttribute("data-phong-len") ? "len" : "xuong");
      };
    });
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
    ganPdf();
  }

  function khoaViec(v) {
    if (!v) return "";
    var loi = v.loi || [];
    var last = loi.length ? (loi[loi.length - 1].loi || "").length : 0;
    var d = v.dang_lam || {};
    return [v.id, v.trang_thai, loi.length, last, v.loi_chay || "", (v.mo || []).length, Object.keys(v.ban || {}).length, d.ten || "", d.buoc || "", d.giao_cho || "", (v.ket_qua || "").length].join("~");
  }

  function capNhatTheoDoi() {
    if (S._viecDay) {
      var row0 = S.viec.filter(function (x) { return x.id === S._viecDay.id; })[0];
      if (row0) row0.trang_thai = S._viecDay.trang_thai;
    }
    capNhatPhong();
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
      var log = document.getElementById("ntLogPhong");
      var satDay = log ? log.scrollTop < 40 : true;
      box.innerHTML = theoDoi();
      ganTheoDoi();
      var log2 = document.getElementById("ntLogPhong");
      if (log2 && satDay) log2.scrollTop = 0;
    }
    S.root.querySelectorAll("[data-viec]").forEach(function (b) {
      var id = b.getAttribute("data-viec");
      var v = S.viec.filter(function (x) { return x.id === id; })[0];
      if (v && S._viecDay && v.id === S._viecDay.id) v.trang_thai = S._viecDay.trang_thai;
      var small = b.querySelector("small");
      if (small && v) small.textContent = (TRANG[v.trang_thai] || [v.trang_thai || ""])[0];
    });
  }

  function capNhatPhong() {
    var map = document.getElementById("ntMap");
    var talk = document.getElementById("ntTalk");
    if (!map || !talk) return;
    var v = viecHien();
    var k = (v ? khoaViec(v) : "") + "|" + S.chonPhong;
    if (k === S._khoaPhong) return;
    S._khoaPhong = k;
    var log = document.getElementById("ntLogPhong");
    var sat = log ? log.scrollTop < 48 : true;
    map.innerHTML = htmlMap();
    talk.innerHTML = htmlTalk();
    ganNhan();
    var log2 = document.getElementById("ntLogPhong");
    if (log2 && sat) log2.scrollTop = 0;
  }

  function ganNhan() {
    var map = document.getElementById("ntMap");
    if (!map) return;
    map.querySelectorAll("[data-phong]").forEach(function (b) {
      b.onclick = function (ev) {
        ev.stopPropagation();
        var id = b.getAttribute("data-phong");
        if (!id || id === S.chonPhong) return;
        S.chonPhong = id;
        S.sua = "";
        S.loi = "";
        S._khoaPhong = "";
        var vv = viecChoPhong(id);
        if (vv && vv.id !== S.chonViec) {
          S.chonViec = vv.id;
          moViec().then(function () {
            ve(true);
            if (S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
          });
          return;
        }
        ve(true);
      };
    });
    map.querySelectorAll("[data-sua]").forEach(function (b) {
      b.onclick = function () {
        S.sua = b.getAttribute("data-sua") || "";
        ve();
      };
    });
    ganPdf();
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
    if (S._viecDay.trang_thai === "dang_chay" && S._viecDay.song !== false) return;
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
    if (v && (v.phong || []).length && (v.phong || []).indexOf(S.chonPhong) < 0) S.chonPhong = v.phong[0];
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
      S._khoLoi = S.kho.length ? "" : ((cap[3] && cap[3].error) || "");
    } catch (e) {
      S.agents = [];
      return hienLoi("Không tải được Nhạc trưởng.");
    }
    if (cap[1] && cap[1].ok === false && !cap[1].phong) return hienLoi(cap[1].error);
    chonMacDinh();
    var dang = S.viec.filter(function (v) { return v.trang_thai === "dang_chay"; })[0];
    if (dang) S.chonViec = dang.id;
    else {
      var vv = viecChoPhong(S.chonPhong);
      if (vv) S.chonViec = vv.id;
    }
    await moViec();
    if (S._viecDay && S._viecDay.dang_lam && S._viecDay.dang_lam.phong) S.chonPhong = S._viecDay.dang_lam.phong;
    S._khoa = "";
    ve();
    if (S._viecDay && S._viecDay.trang_thai === "dang_chay") batPoll();
  }

  window.JavisNhacTruong = {
    render: render,
    stop: function () {
      if (S.timer) clearInterval(S.timer);
      S.timer = 0;
      dongKho();
      if (S._neo) {
        window.removeEventListener("scroll", S._neo, true);
        window.removeEventListener("resize", S._neo);
        S._neo = null;
      }
    }
  };
})();
