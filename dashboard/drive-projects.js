/* Kho Drive - wizard 3 bước; VPS tách tab Mac / Windows rõ ràng. */
(function () {
  "use strict";

  function ic(ten, opt) {
    return window.ic ? window.ic(ten, opt) : "";
  }
  function t(k, fb) {
    try {
      if (window.JavisI18n && typeof JavisI18n.t === "function") {
        var v = JavisI18n.t(k);
        if (v && v !== k) return v;
      }
    } catch (e) {}
    return fb || k;
  }
  function esc(s) {
    return (s || "")
      .toString()
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function brain() {
    try {
      if (window.JavisSessions && typeof JavisSessions.brain === "function") {
        return JavisSessions.brain() || "brain";
      }
      if (typeof currentBrainPath === "function") return currentBrainPath() || "brain";
    } catch (e) {}
    return "brain";
  }
  function when(ts) {
    if (!ts) return "-";
    try {
      return new Date(Number(ts) * 1000).toLocaleString();
    } catch (e) {
      return String(ts);
    }
  }
  function isLocalHost() {
    try {
      var h = (location.hostname || "").toLowerCase();
      return h === "localhost" || h === "127.0.0.1" || h === "::1";
    } catch (e) {
      return false;
    }
  }
  function guessOs() {
    try {
      var ua = (navigator.userAgent || "").toLowerCase();
      var p = (navigator.platform || "").toLowerCase();
      if (/win/.test(p) || /windows/.test(ua)) return "win";
      return "mac";
    } catch (e) {
      return "mac";
    }
  }

  async function loadStatus() {
    var r = await fetch("/drive-projects/status?brain=" + encodeURIComponent(brain()));
    return r.json();
  }

  async function postJson(url, obj) {
    var r = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(obj || {}),
    });
    var data = {};
    try {
      data = await r.json();
    } catch (e) {
      data = { ok: false, error: "non-JSON " + r.status };
    }
    data._status = r.status;
    return data;
  }

  var _pollTimer = null;
  var _osTab = guessOs();
  var _pairCache = null;

  function stopPoll() {
    if (_pollTimer) {
      clearInterval(_pollTimer);
      _pollTimer = null;
    }
  }

  /** Bước đang làm: 1 chưa Google · 2 đã Google chưa kho · 3 đã có kho. */
  function currentStep(connected, hasProjects, rcloneOk) {
    if (!rcloneOk) return 1;
    if (!connected) return 1;
    if (!hasProjects) return 2;
    return 3;
  }

  function stepBarHtml(step, connected, hasProjects) {
    function item(n, label, sub) {
      var done = (n === 1 && connected) || (n === 2 && hasProjects) || (n === 3 && hasProjects && step === 3);
      var on = step === n;
      var cls = "dp-step" + (done && !on ? " done" : "") + (on ? " on" : "") + (!on && !done ? " wait" : "");
      var mark = done && !on ? "✓" : String(n);
      return (
        '<li class="' +
        cls +
        '" data-step="' +
        n +
        '">' +
        '<span class="dp-n">' +
        mark +
        "</span>" +
        '<span class="dp-lab"><b>' +
        esc(label) +
        "</b><small>" +
        esc(sub) +
        "</small></span></li>"
      );
    }
    return (
      '<ol class="dp-steps" aria-label="3 bước Kho Drive">' +
      item(1, "Bước 1", "Kết nối Google") +
      item(2, "Bước 2", "Tạo kho từ link") +
      item(3, "Bước 3", "Đồng bộ & dùng") +
      "</ol>"
    );
  }

  function tipLinkDrive() {
    return (
      '<details class="dp-tip"><summary>Cách lấy link thư mục Drive (bấm để xem)</summary>' +
      '<ol class="dp-ol">' +
      "<li>Mở <b>drive.google.com</b>.</li>" +
      "<li>Vào đúng <b>thư mục</b> (không chọn file lẻ).</li>" +
      "<li>Chuột phải → <b>Chia sẻ</b> → <b>Sao chép liên kết</b>, hoặc chép URL trên thanh địa chỉ.</li>" +
      "<li>Dán nguyên link vào ô ở bước 2.</li>" +
      "</ol>" +
      '<p class="dp-muted">Tài khoản vừa Allow phải mở được thư mục đó.</p></details>'
    );
  }

  function advancedDetails() {
    return (
      '<details class="dp-adv"><summary>Cách khác (hiếm khi cần)</summary>' +
      '<p class="jw-hint dim" style="margin-top:8px">Dán token JSON hoặc upload <code>rclone.conf</code>.</p>' +
      '<textarea id="dpToken" rows="3" class="dp-ta" placeholder=\'{"access_token":...}\'></textarea>' +
      '<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="dpTokenSave">Lưu token</button>' +
      '<input type="file" id="dpConfFile" accept=".conf,text/plain">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="dpConfUpload">Upload conf</button></div></details>'
    );
  }

  function render(el) {
    if (!el) return;
    stopPoll();
    _pairCache = null;
    el.innerHTML =
      '<div class="jw-page dp-page">' +
      '<div class="jw-head"><h2 id="dpHeadTitle">' +
      ic("hard-drive") +
      " " +
      esc(t("page.drive.label", "Kho Drive")) +
      "</h2>" +
      '<p class="jw-lead">' +
      esc(t("page.drive.sub", "3 bước: kết nối Google → tạo kho → dùng hàng ngày")) +
      "</p></div>" +
      '<p class="dp-diff dim">Khác menu <b>Kết nối → Google</b>: trang này chỉ đồng bộ <b>một thư mục</b> vào bộ não.</p>' +
      '<div id="dpSteps"></div>' +
      '<div id="dpNow" class="dp-now"></div>' +
      '<div id="dpBody"></div>' +
      '<div id="dpList" style="margin-top:14px"></div>' +
      "</div>";
    try {
      if (window.JavisPromptHelp && typeof window.JavisPromptHelp.mountInline === "function") {
        window.JavisPromptHelp.mountInline(el.querySelector("#dpHeadTitle"));
      }
    } catch (ePh) {}
    refresh(el);
  }

  function wireAdvanced(el, root) {
    var save = root.querySelector("#dpTokenSave");
    var up = root.querySelector("#dpConfUpload");
    if (save) {
      save.onclick = async function () {
        var token = (root.querySelector("#dpToken").value || "").trim();
        if (!token) {
          alert("Dán token trước");
          return;
        }
        var res = await postJson("/drive-projects/rclone/connect", { token: token });
        if (!res.ok) {
          alert(res.error || "Lỗi");
          return;
        }
        await refresh(el);
      };
    }
    if (up) {
      up.onclick = async function () {
        var inp = root.querySelector("#dpConfFile");
        var f = inp && inp.files && inp.files[0];
        if (!f) {
          alert("Chọn file");
          return;
        }
        var text = await f.text();
        var res = await postJson("/drive-projects/rclone/upload-config", { content: text });
        if (!res.ok) {
          alert(res.error || "Lỗi");
          return;
        }
        await refresh(el);
      };
    }
  }

  function renderBody(el, d) {
    var body = el.querySelector("#dpBody");
    var now = el.querySelector("#dpNow");
    if (!body || !now) return;
    var rc = d.rclone || {};
    var connected = !!(d.google_connected || rc.google_connected);
    var projects = d.projects || [];
    var rcloneOk = !!rc.rclone_installed;
    var step = currentStep(connected, projects.length > 0, rcloneOk);

    if (!rcloneOk) {
      now.innerHTML = '<span class="warn">Đang ở bước 1</span> - máy chưa có rclone. Cập nhật image Docker rồi mở lại.';
      body.innerHTML =
        '<div class="jw-card dp-panel on">' +
        "<h3>Bước 1 - Chưa sẵn sàng</h3>" +
        '<p class="jw-hint">Cần <code>rclone</code> trên máy VMOS (Docker từ 0.55.154 đã có).</p></div>';
      return;
    }

    if (step === 1) {
      now.innerHTML =
        '<span class="warn">Đang làm bước 1</span> - kết nối tài khoản Google. Xong sẽ tự sang bước 2.';
      body.innerHTML = htmlStep1(el, d);
      wireStep1(el, body);
      return;
    }

    if (step === 2) {
      now.innerHTML =
        '<span class="ok">Bước 1 xong</span> · <span class="warn">Đang làm bước 2</span> - đặt tên kho và dán link thư mục Drive.';
      body.innerHTML =
        htmlStep1Done(el) +
        '<div class="jw-card dp-panel on" id="dpCreateWrap">' +
        "<h3>Bước 2 - Tạo kho từ thư mục Drive</h3>" +
        '<ol class="dp-ol dp-ol-big">' +
        "<li><b>Đặt tên kho</b> dễ nhớ (ví dụ: Giáo trình Marketing).</li>" +
        "<li><b>Dán link thư mục</b> Google Drive vào ô dưới.</li>" +
        "<li>Bấm <b>Tạo và đồng bộ</b> - lần đầu có thể mất vài phút.</li>" +
        "</ol>" +
        tipLinkDrive() +
        '<div class="jw-field"><label>1. Tên kho</label>' +
        '<input id="dpName" type="text" placeholder="Ví dụ: Giáo trình Marketing" autocomplete="off"></div>' +
        '<div class="jw-field"><label>2. Link thư mục Google Drive</label>' +
        '<input id="dpFolder" type="text" placeholder="https://drive.google.com/drive/folders/…" autocomplete="off"></div>' +
        '<button type="button" class="jw-btn jw-btn-primary" id="dpCreate">3. Tạo và đồng bộ</button>' +
        "</div>" +
        '<div class="jw-card dp-panel wait"><h3>Bước 3 - Dùng hàng ngày</h3>' +
        '<p class="dp-muted">Sẽ mở sau khi bạn tạo kho xong ở bước 2.</p></div>';
      wireStep1Done(el);
      wireCreate(el);
      return;
    }

    // step 3
    now.innerHTML =
      '<span class="ok">Đã sẵn sàng</span> - sửa file trên Drive rồi bấm <b>Đồng bộ lại</b> bên dưới khi cần.';
    body.innerHTML =
      htmlStep1Done(el) +
      '<div class="jw-card dp-panel done-sum">' +
      "<h3>Bước 2 - Đã có kho ✓</h3>" +
      '<p class="jw-hint">Có <b>' +
      projects.length +
      "</b> kho. Muốn thêm kho nữa? " +
      '<button type="button" class="jw-btn jw-btn-ghost" id="dpAddMore">Thêm kho mới</button></p>' +
      '<div id="dpCreateWrap" style="display:none;margin-top:10px"></div></div>' +
      '<div class="jw-card dp-panel on">' +
      "<h3>Bước 3 - Dùng hàng ngày</h3>" +
      '<ol class="dp-ol dp-ol-big">' +
      "<li>Sửa / thêm file trên <b>Google Drive</b>.</li>" +
      "<li>Quay lại đây → bấm <b>Đồng bộ lại</b> trên đúng kho.</li>" +
      "<li>Mở <b>Tệp tin</b> → <code>sources/drive/…</code> (hoặc Dự án chat của kho).</li>" +
      "<li>Nhờ Javis đọc / ingest <b>từng file quan trọng</b> - đừng nuốt cả kho một lần.</li>" +
      "</ol></div>";
    wireStep1Done(el);
    var addBtn = body.querySelector("#dpAddMore");
    if (addBtn) {
      addBtn.onclick = function () {
        var wrap = body.querySelector("#dpCreateWrap");
        if (!wrap) return;
        wrap.style.display = "";
        wrap.innerHTML =
          tipLinkDrive() +
          '<div class="jw-field"><label>Tên kho</label>' +
          '<input id="dpName" type="text" placeholder="Tên kho mới" autocomplete="off"></div>' +
          '<div class="jw-field"><label>Link thư mục Drive</label>' +
          '<input id="dpFolder" type="text" placeholder="https://drive.google.com/drive/folders/…" autocomplete="off"></div>' +
          '<button type="button" class="jw-btn jw-btn-primary" id="dpCreate">Tạo và đồng bộ</button>';
        wireCreate(el);
      };
    }
  }

  function htmlStep1Done(el) {
    return (
      '<div class="jw-card dp-panel done-sum">' +
      "<h3>Bước 1 - Google đã kết nối ✓</h3>" +
      '<p class="jw-hint"><span class="ok">Sẵn sàng.</span> ' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="dpDisconnect">Ngắt kết nối</button></p></div>'
    );
  }

  function wireStep1Done(el) {
    var btn = el.querySelector("#dpDisconnect");
    if (!btn) return;
    btn.onclick = async function () {
      if (!confirm("Ngắt kết nối Google Drive?")) return;
      await postJson("/drive-projects/rclone/disconnect", {});
      _pairCache = null;
      await refresh(el);
    };
  }

  function htmlStep1(el, d) {
    if (isLocalHost()) {
      return (
        '<div class="jw-card dp-panel on">' +
        "<h3>Bước 1 - Kết nối Google (máy này)</h3>" +
        '<ol class="dp-ol dp-ol-big">' +
        "<li>Bấm nút bên dưới - trình duyệt mở Google.</li>" +
        "<li>Chọn tài khoản → <b>Allow / Cho phép</b>.</li>" +
        "<li>Quay lại trang này - tự nhận và sang bước 2.</li>" +
        "</ol>" +
        '<button type="button" class="jw-btn jw-btn-primary" id="dpAuthLocal">Kết nối Google Drive</button>' +
        '<div id="dpAuthProgress" class="jw-hint" style="display:none;margin-top:10px"></div>' +
        advancedDetails() +
        "</div>"
      );
    }
    var os = _osTab === "win" ? "win" : "mac";
    return (
      '<div class="jw-card dp-panel on">' +
      "<h3>Bước 1 - Kết nối Google (VMOS trên VPS)</h3>" +
      '<p class="jw-hint">Google mở trên <b>máy bạn đang ngồi</b>, rồi gửi quyền về VPS. Chọn đúng hệ điều hành:</p>' +
      '<div class="dp-os-tabs" role="tablist">' +
      '<button type="button" role="tab" class="dp-os-tab' +
      (os === "mac" ? " on" : "") +
      '" data-os="mac" aria-selected="' +
      (os === "mac" ? "true" : "false") +
      '">Mac</button>' +
      '<button type="button" role="tab" class="dp-os-tab' +
      (os === "win" ? " on" : "") +
      '" data-os="win" aria-selected="' +
      (os === "win" ? "true" : "false") +
      '">Windows</button>' +
      "</div>" +
      '<div id="dpOsBody" class="dp-os-body" data-show="' +
      esc(os) +
      '">' +
      htmlOsMac() +
      htmlOsWin() +
      "</div>" +
      '<p class="jw-hint" id="dpPairWait" style="display:none;margin-top:12px"></p>' +
      advancedDetails() +
      "</div>"
    );
  }

  function htmlOsMac() {
    return (
      '<div class="dp-os-pane" data-os="mac" role="tabpanel">' +
      '<div class="dp-os-title">Hướng dẫn cho Mac</div>' +
      '<ol class="dp-ol dp-ol-big">' +
      "<li>Bấm <b>Bắt đầu trên Mac</b> bên dưới (một lần là đủ).</li>" +
      "<li>Bấm <b>Sao chép lệnh</b> → mở app <b>Terminal</b> → dán (Cmd+V) → Enter.</li>" +
      "<li>Trình duyệt mở Google → Allow → quay lại trang này.</li>" +
      "</ol>" +
      '<button type="button" class="jw-btn jw-btn-primary" id="dpStartMac">Bắt đầu trên Mac</button>' +
      '<div id="dpMacTools" class="dp-os-tools" style="display:none"></div>' +
      "</div>"
    );
  }

  function htmlOsWin() {
    return (
      '<div class="dp-os-pane" data-os="win" role="tabpanel">' +
      '<div class="dp-os-title">Hướng dẫn cho Windows</div>' +
      '<ol class="dp-ol dp-ol-big">' +
      "<li>Bấm <b>Bắt đầu trên Windows</b> bên dưới.</li>" +
      "<li>Bấm <b>Tải file .bat</b> → double-click file vừa tải (Run anyway nếu Windows hỏi).</li>" +
      "<li>Trình duyệt mở Google → Allow → quay lại trang này.</li>" +
      "</ol>" +
      '<button type="button" class="jw-btn jw-btn-primary" id="dpStartWin">Bắt đầu trên Windows</button>' +
      '<div id="dpWinTools" class="dp-os-tools" style="display:none"></div>' +
      "</div>"
    );
  }

  function wireStep1(el, body) {
    wireAdvanced(el, body);
    var localBtn = body.querySelector("#dpAuthLocal");
    if (localBtn) {
      localBtn.onclick = function () {
        startLocalAuth(el, body);
      };
      return;
    }
    body.querySelectorAll(".dp-os-tab").forEach(function (tab) {
      tab.onclick = function () {
        _osTab = tab.getAttribute("data-os") || "mac";
        body.querySelectorAll(".dp-os-tab").forEach(function (x) {
          var on = x === tab;
          x.classList.toggle("on", on);
          x.setAttribute("aria-selected", on ? "true" : "false");
        });
        var wrap = body.querySelector("#dpOsBody");
        if (wrap) wrap.setAttribute("data-show", _osTab);
        fillOsTools(body);
      };
    });
    var mac = body.querySelector("#dpStartMac");
    var win = body.querySelector("#dpStartWin");
    if (mac) {
      mac.onclick = async function () {
        _osTab = "mac";
        await ensurePair(el, body);
      };
    }
    if (win) {
      win.onclick = async function () {
        _osTab = "win";
        await ensurePair(el, body);
      };
    }
    if (_pairCache) fillOsTools(body);
  }

  function fillOsTools(body) {
    if (!_pairCache || !_pairCache.ok) return;
    var res = _pairCache;
    var macTools = body.querySelector("#dpMacTools");
    var winTools = body.querySelector("#dpWinTools");
    if (macTools) {
      macTools.style.display = "";
      macTools.innerHTML =
        '<button type="button" class="jw-btn jw-btn-primary" id="dpCopyMac">Sao chép lệnh Terminal</button>' +
        '<pre class="dp-pre">' +
        esc(res.mac_terminal || "") +
        "</pre>" +
        '<p class="dp-muted">Dùng lệnh Terminal - đừng tải file <code>.command</code> (macOS hay chặn).</p>';
      var copyBtn = macTools.querySelector("#dpCopyMac");
      if (copyBtn && res.mac_terminal) {
        copyBtn.onclick = async function () {
          try {
            await navigator.clipboard.writeText(res.mac_terminal);
            copyBtn.textContent = "Đã sao chép - dán vào Terminal (Cmd+V)";
            setTimeout(function () {
              copyBtn.textContent = "Sao chép lệnh Terminal";
            }, 2800);
          } catch (e) {
            alert("Không sao chép được. Bôi đen lệnh bên dưới rồi Cmd+C.");
          }
        };
      }
    }
    if (winTools) {
      winTools.style.display = "";
      winTools.innerHTML =
        '<a class="jw-btn jw-btn-primary" href="' +
        esc(res.win_url) +
        '">Tải file .bat cho Windows</a>' +
        '<p class="dp-muted" style="margin-top:8px">Double-click file vừa tải. Nếu Windows cảnh báo: More info → Run anyway.</p>';
    }
  }

  async function ensurePair(el, body) {
    var wait = body.querySelector("#dpPairWait");
    var macBtn = body.querySelector("#dpStartMac");
    var winBtn = body.querySelector("#dpStartWin");
    if (macBtn) macBtn.disabled = true;
    if (winBtn) winBtn.disabled = true;
    if (wait) {
      wait.style.display = "";
      wait.textContent = "Đang tạo lệnh kết nối…";
    }
    if (!_pairCache || !_pairCache.ok) {
      var res = await postJson("/drive-projects/rclone/pair/start", {
        base_url: location.origin,
      });
      _pairCache = res;
      if (!res.ok) {
        if (wait) wait.innerHTML = '<span class="warn">' + esc(res.error || "Lỗi") + "</span>";
        if (macBtn) macBtn.disabled = false;
        if (winBtn) winBtn.disabled = false;
        return;
      }
    }
    fillOsTools(body);
    if (wait) {
      wait.innerHTML =
        '<span class="ok">Đang chờ bạn Allow Google trên máy…</span> ' +
        "<span class=\"dim\">(còn khoảng 15 phút - không đóng trang này)</span>";
    }
    startPairPoll(el, body, _pairCache.pair_id);
  }

  function startPairPoll(el, body, pairId) {
    stopPoll();
    var n = 0;
    _pollTimer = setInterval(async function () {
      n += 1;
      if (n > 150) {
        stopPoll();
        var w = body.querySelector("#dpPairWait");
        if (w) w.innerHTML = '<span class="warn">Hết thời gian. Bấm Bắt đầu lại.</span>';
        var macBtn = body.querySelector("#dpStartMac");
        var winBtn = body.querySelector("#dpStartWin");
        if (macBtn) macBtn.disabled = false;
        if (winBtn) winBtn.disabled = false;
        _pairCache = null;
        return;
      }
      try {
        var p = await (
          await fetch("/drive-projects/rclone/pair/" + encodeURIComponent(pairId) + "/poll")
        ).json();
        if (p.status === "done") {
          stopPoll();
          _pairCache = null;
          await refresh(el);
        } else if (p.status === "error") {
          stopPoll();
          var w2 = body.querySelector("#dpPairWait");
          if (w2) w2.innerHTML = '<span class="warn">' + esc(p.error || "Lỗi") + "</span>";
          _pairCache = null;
          var m2 = body.querySelector("#dpStartMac");
          var wBtn = body.querySelector("#dpStartWin");
          if (m2) m2.disabled = false;
          if (wBtn) wBtn.disabled = false;
        }
      } catch (e) {}
    }, 2000);
  }

  function wireCreate(el) {
    var root = el.querySelector("#dpCreateWrap") || el;
    var btn = root.querySelector("#dpCreate");
    if (!btn) return;
    btn.onclick = async function () {
      var name = (root.querySelector("#dpName").value || "").trim();
      var folder = (root.querySelector("#dpFolder").value || "").trim();
      if (!name || !folder) {
        alert("Cần tên kho và link thư mục Drive");
        return;
      }
      btn.disabled = true;
      btn.textContent = "Đang tạo & đồng bộ…";
      var res = await postJson("/drive-projects", {
        name: name,
        drive_folder_id: folder,
        rclone_remote: "gdrive:",
        brain: brain(),
        sync_now: true,
      });
      btn.disabled = false;
      btn.textContent = "Tạo và đồng bộ";
      if (!res.ok) {
        alert(res.error || "Thất bại");
        if (res.project) await refresh(el);
        return;
      }
      await refresh(el);
    };
  }

  async function startLocalAuth(el, box) {
    stopPoll();
    var prog = box.querySelector("#dpAuthProgress");
    var btn = box.querySelector("#dpAuthLocal");
    if (btn) btn.disabled = true;
    if (prog) {
      prog.style.display = "";
      prog.textContent = "Đang mở Google…";
    }
    var res = await postJson("/drive-projects/rclone/authorize/start", {});
    if (!res.ok) {
      if (prog) prog.innerHTML = '<span class="warn">' + esc(res.error || "Lỗi") + "</span>";
      if (btn) btn.disabled = false;
      return;
    }
    var url = res.auth_url || "";
    var sid = res.session_id || "";
    if (url) {
      try {
        window.open(url, "_blank");
      } catch (e) {}
    }
    if (prog) {
      prog.innerHTML = url
        ? 'Nếu chưa mở: <a href="' +
          esc(url) +
          '" target="_blank" rel="noopener">đăng nhập Google</a> · đang chờ Allow…'
        : "Đang chờ Allow…";
    }
    var n = 0;
    _pollTimer = setInterval(async function () {
      n += 1;
      if (n > 120) {
        stopPoll();
        if (prog) prog.innerHTML = '<span class="warn">Hết thời gian. Thử lại.</span>';
        if (btn) btn.disabled = false;
        return;
      }
      try {
        var p = await (
          await fetch(
            "/drive-projects/rclone/authorize/poll?session=" + encodeURIComponent(sid)
          )
        ).json();
        if (p.status === "done") {
          stopPoll();
          await refresh(el);
        } else if (p.status === "error") {
          stopPoll();
          if (prog) prog.innerHTML = '<span class="warn">' + esc(p.error || "Thất bại") + "</span>";
          if (btn) btn.disabled = false;
        } else if (p.auth_url && p.auth_url !== url) {
          url = p.auth_url;
          if (prog) {
            prog.innerHTML =
              '<a href="' + esc(url) + '" target="_blank" rel="noopener">đăng nhập Google</a> · đang chờ…';
          }
        }
      } catch (e) {}
    }, 2000);
  }

  async function refresh(el) {
    var stepsEl = el.querySelector("#dpSteps");
    var listEl = el.querySelector("#dpList");
    try {
      var d = await loadStatus();
      var rc = d.rclone || {};
      var connected = !!(d.google_connected || rc.google_connected);
      var projects = d.projects || [];
      var step = currentStep(connected, projects.length > 0, !!rc.rclone_installed);
      if (stepsEl) stepsEl.innerHTML = stepBarHtml(step, connected, projects.length > 0);
      renderBody(el, d);

      if (!projects.length) {
        listEl.innerHTML = "";
        return;
      }
      listEl.innerHTML =
        '<h3 class="dp-list-h">Kho của bạn</h3>' +
        projects
          .map(function (p) {
            var syncBadge =
              p.last_sync_ok === true
                ? '<span class="ok">sync OK</span>'
                : p.last_sync_ok === false
                  ? '<span class="warn">sync lỗi</span>'
                  : '<span class="dim">chưa sync</span>';
            return (
              '<div class="jw-card dp-card" style="margin-top:10px" data-id="' +
              esc(p.id) +
              '">' +
              "<div><b>" +
              esc(p.name) +
              "</b> " +
              syncBadge +
              "</div>" +
              '<div class="dim" style="font-size:12px;margin-top:4px">' +
              esc(when(p.last_sync_at)) +
              (p.last_sync_error ? " · " + esc(p.last_sync_error) : "") +
              "</div>" +
              '<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">' +
              '<button type="button" class="jw-btn jw-btn-primary" data-act="sync">Đồng bộ lại</button>' +
              '<button type="button" class="jw-btn jw-btn-ghost" data-act="distill">Chưng cất kho</button>' +
              '<button type="button" class="jw-btn jw-btn-ghost" data-act="files">Mở tệp</button>' +
              '<button type="button" class="jw-btn jw-btn-ghost" data-act="del">Xoá</button>' +
              "</div></div>"
            );
          })
          .join("");

      listEl.querySelectorAll("[data-id]").forEach(function (card) {
        var id = card.getAttribute("data-id");
        var proj = projects.find(function (x) {
          return x.id === id;
        }) || {};
        card.querySelector('[data-act="sync"]').onclick = async function () {
          var b = this;
          b.disabled = true;
          b.textContent = "Đang sync…";
          var res = await postJson("/drive-projects/" + encodeURIComponent(id) + "/sync", {});
          b.disabled = false;
          b.textContent = "Đồng bộ lại";
          if (!res.ok) alert(res.error || "Sync thất bại");
          await refresh(el);
        };
        card.querySelector('[data-act="distill"]').onclick = function () {
          var slug = proj.slug || "";
          var msg =
            "Đọc và chưng cất toàn bộ kho Drive trong sources/drive/" +
            slug +
            "/ (trừ README). " +
            "Liệt kê file unprocessed rồi chạy ingest-source từng file; " +
            "kho lớn thì xếp việc nền theo batch và báo tiến độ. " +
            "PDF chưa có chữ thì nói rõ file nào thiếu.";
          try {
            if (window.Alpine && Alpine.store && Alpine.store("nav")) {
              Alpine.store("nav").page = "chat";
            }
          } catch (e) {}
          if (typeof window.JavisSend === "function") window.JavisSend(msg);
          else alert("Mở chat rồi gửi: " + msg);
        };
        card.querySelector('[data-act="files"]').onclick = function () {
          var slug = proj.slug;
          if (window.JavisOpenFiles && slug) window.JavisOpenFiles("sources/drive/" + slug + "/");
          else alert("Tệp tin → sources/drive/" + (slug || ""));
        };
        card.querySelector('[data-act="del"]').onclick = async function () {
          if (!confirm("Xoá kho này?")) return;
          await postJson("/drive-projects/" + encodeURIComponent(id) + "/delete", {});
          await refresh(el);
        };
      });
    } catch (e) {
      var now = el.querySelector("#dpNow");
      if (now) now.textContent = "Lỗi: " + ((e && e.message) || e);
    }
  }

  window.JavisDriveProjects = { render: render };
})();
