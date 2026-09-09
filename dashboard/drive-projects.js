/* Kho Drive — kết nối Google đơn giản (1 nút / tải tool Mac·Win) → tạo kho bằng link. */
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
    if (!ts) return "—";
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
  function stopPoll() {
    if (_pollTimer) {
      clearInterval(_pollTimer);
      _pollTimer = null;
    }
  }

  function render(el) {
    if (!el) return;
    stopPoll();
    el.innerHTML =
      '<div class="jw-page dp-page">' +
      '<div class="jw-head"><h2>' +
      ic("hard-drive") +
      " " +
      esc(t("page.drive.label", "Kho Drive")) +
      "</h2>" +
      '<p class="jw-lead">' +
      esc(t("page.drive.sub", "Kết nối Google → dán link thư mục → đồng bộ vào bộ não.")) +
      "</p></div>" +
      '<div id="dpStatus" class="jw-hint dim">Đang kiểm tra…</div>' +
      '<div id="dpConnect" class="jw-card" style="margin-top:12px;display:none"></div>' +
      '<div id="dpCreateWrap" class="jw-card" style="margin-top:12px;display:none">' +
      "<h3>Bước 2 — Tạo kho</h3>" +
      '<div class="jw-field"><label>Tên kho</label>' +
      '<input id="dpName" type="text" placeholder="Ví dụ: Giáo trình Marketing"></div>' +
      '<div class="jw-field"><label>Link thư mục Google Drive</label>' +
      '<input id="dpFolder" type="text" placeholder="Dán link thư mục từ trình duyệt"></div>' +
      '<button type="button" class="jw-btn jw-btn-primary" id="dpCreate">Tạo và đồng bộ</button>' +
      "</div>" +
      '<div id="dpList" style="margin-top:16px"></div>' +
      "</div>";

    el.querySelector("#dpCreate").onclick = async function () {
      var name = (el.querySelector("#dpName").value || "").trim();
      var folder = (el.querySelector("#dpFolder").value || "").trim();
      if (!name || !folder) {
        alert("Cần tên kho và link thư mục Drive");
        return;
      }
      var btn = el.querySelector("#dpCreate");
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
      el.querySelector("#dpName").value = "";
      el.querySelector("#dpFolder").value = "";
      await refresh(el);
    };

    refresh(el);
  }

  function renderConnect(el, d) {
    var box = el.querySelector("#dpConnect");
    var createWrap = el.querySelector("#dpCreateWrap");
    if (!box || !createWrap) return;
    var rc = d.rclone || {};
    var connected = !!(d.google_connected || (rc && rc.google_connected));
    createWrap.style.display = connected ? "" : "none";

    if (!rc.rclone_installed) {
      box.style.display = "";
      box.innerHTML =
        "<h3>Chưa sẵn sàng</h3>" +
        '<p class="jw-hint">Máy chạy Javis cần <code>rclone</code> (bản Docker từ 0.55.154 đã có). Cập nhật image rồi thử lại.</p>';
      return;
    }

    if (connected) {
      box.style.display = "";
      box.innerHTML =
        "<h3>Bước 1 — Google đã kết nối ✓</h3>" +
        '<p class="jw-hint"><span class="ok">Sẵn sàng</span></p>' +
        '<button type="button" class="jw-btn" id="dpDisconnect">Ngắt kết nối</button>';
      box.querySelector("#dpDisconnect").onclick = async function () {
        if (!confirm("Ngắt kết nối Google Drive?")) return;
        await postJson("/drive-projects/rclone/disconnect", {});
        await refresh(el);
      };
      return;
    }

    var local = isLocalHost();
    box.style.display = "";
    box.innerHTML =
      "<h3>Bước 1 — Kết nối Google Drive</h3>" +
      (local
        ? '<p class="jw-hint">Bạn đang mở Javis trên máy này. Bấm một lần, Allow Google là xong.</p>' +
          '<button type="button" class="jw-btn jw-btn-primary" id="dpAuthLocal">Kết nối Google Drive</button>' +
          '<div id="dpAuthProgress" class="jw-hint" style="display:none;margin-top:8px"></div>'
        : '<p class="jw-hint">Javis đang trên VPS. Tải tool về máy Mac/Windows → double-click → Allow Google → xong.</p>' +
          '<button type="button" class="jw-btn jw-btn-primary" id="dpPairStart">Tạo link tải (Mac / Windows)</button>' +
          '<div id="dpPairBox" style="display:none;margin-top:12px"></div>') +
      '<details style="margin-top:14px"><summary class="dim">Cách khác (hiếm khi cần)</summary>' +
      '<p class="jw-hint dim" style="margin-top:8px">Dán token JSON hoặc upload rclone.conf nếu tool không chạy được.</p>' +
      '<textarea id="dpToken" rows="3" style="width:100%;font-family:monospace;font-size:12px" placeholder=\'{"access_token":...}\'></textarea>' +
      '<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">' +
      '<button type="button" class="jw-btn" id="dpTokenSave">Lưu token</button>' +
      '<input type="file" id="dpConfFile" accept=".conf,text/plain">' +
      '<button type="button" class="jw-btn" id="dpConfUpload">Upload conf</button></div></details>';

    if (local) {
      box.querySelector("#dpAuthLocal").onclick = function () {
        startLocalAuth(el, box);
      };
    } else {
      box.querySelector("#dpPairStart").onclick = function () {
        startPair(el, box);
      };
    }
    box.querySelector("#dpTokenSave").onclick = async function () {
      var token = (box.querySelector("#dpToken").value || "").trim();
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
    box.querySelector("#dpConfUpload").onclick = async function () {
      var inp = box.querySelector("#dpConfFile");
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

  async function startPair(el, box) {
    stopPoll();
    var pairBox = box.querySelector("#dpPairBox");
    var btn = box.querySelector("#dpPairStart");
    if (btn) btn.disabled = true;
    if (pairBox) {
      pairBox.style.display = "";
      pairBox.textContent = "Đang tạo…";
    }
    var res = await postJson("/drive-projects/rclone/pair/start", {
      base_url: location.origin,
    });
    if (!res.ok) {
      if (pairBox) pairBox.innerHTML = '<span class="warn">' + esc(res.error || "Lỗi") + "</span>";
      if (btn) btn.disabled = false;
      return;
    }
    if (pairBox) {
      pairBox.innerHTML =
        '<p class="jw-hint"><b>Tải về máy bạn rồi double-click:</b></p>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin:8px 0">' +
        '<a class="jw-btn jw-btn-primary" href="' +
        esc(res.mac_url) +
        '">Tải cho Mac (.command)</a>' +
        '<a class="jw-btn jw-btn-primary" href="' +
        esc(res.win_url) +
        '">Tải cho Windows (.bat)</a></div>' +
        '<p class="jw-hint dim">Sau khi Allow Google, quay lại trang này — sẽ tự cập nhật (khoảng 15 phút hiệu lực).</p>' +
        '<p class="jw-hint" id="dpPairWait">Đang chờ kết nối từ máy bạn…</p>';
    }
    var pairId = res.pair_id;
    var n = 0;
    _pollTimer = setInterval(async function () {
      n += 1;
      if (n > 150) {
        stopPoll();
        var w = box.querySelector("#dpPairWait");
        if (w) w.innerHTML = '<span class="warn">Hết thời gian. Bấm tạo link tải lại.</span>';
        if (btn) btn.disabled = false;
        return;
      }
      try {
        var p = await (
          await fetch("/drive-projects/rclone/pair/" + encodeURIComponent(pairId) + "/poll")
        ).json();
        if (p.status === "done") {
          stopPoll();
          await refresh(el);
        } else if (p.status === "error") {
          stopPoll();
          var w2 = box.querySelector("#dpPairWait");
          if (w2) w2.innerHTML = '<span class="warn">' + esc(p.error || "Lỗi") + "</span>";
          if (btn) btn.disabled = false;
        }
      } catch (e) {}
    }, 2000);
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
        ? 'Nếu chưa mở: <a href="' + esc(url) + '" target="_blank" rel="noopener">đăng nhập Google</a> · đang chờ Allow…'
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
    var stEl = el.querySelector("#dpStatus");
    var listEl = el.querySelector("#dpList");
    try {
      var d = await loadStatus();
      var rc = d.rclone || {};
      var connected = !!(d.google_connected || rc.google_connected);
      stEl.innerHTML = !rc.rclone_installed
        ? '<span class="warn">Chưa có rclone trên máy Javis</span>'
        : connected
          ? '<span class="ok">Google đã kết nối</span>'
          : '<span class="warn">Chưa kết nối Google</span>';

      renderConnect(el, d);

      var projects = d.projects || [];
      if (!projects.length) {
        listEl.innerHTML = connected
          ? '<p class="dim">Chưa có kho. Điền tên + link ở trên.</p>'
          : "";
        return;
      }
      listEl.innerHTML =
        "<h3>Kho của bạn</h3>" +
        projects
          .map(function (p) {
            var syncBadge =
              p.last_sync_ok === true
                ? '<span class="ok">sync OK</span>'
                : p.last_sync_ok === false
                  ? '<span class="warn">sync lỗi</span>'
                  : '<span class="dim">chưa sync</span>';
            return (
              '<div class="jw-card" style="margin-top:10px" data-id="' +
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
              '<button type="button" class="jw-btn" data-act="files">Mở tệp</button>' +
              '<button type="button" class="jw-btn" data-act="del">Xoá</button>' +
              "</div></div>"
            );
          })
          .join("");

      listEl.querySelectorAll("[data-id]").forEach(function (card) {
        var id = card.getAttribute("data-id");
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
        card.querySelector('[data-act="files"]').onclick = function () {
          var slug = (projects.find(function (x) {
            return x.id === id;
          }) || {}).slug;
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
      stEl.textContent = "Lỗi: " + ((e && e.message) || e);
    }
  }

  window.JavisDriveProjects = { render: render };
})();
