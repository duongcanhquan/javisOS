/* Kho Drive - wizard 3 bước: kết nối Google → tạo kho → dùng hàng ngày. */
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

  function stepBar(connected, hasProjects) {
    function cls(n) {
      if (n === 1) return connected ? "dp-step done" : "dp-step on";
      if (n === 2) {
        if (hasProjects) return "dp-step done";
        if (connected) return "dp-step on";
        return "dp-step";
      }
      return hasProjects ? "dp-step on" : "dp-step";
    }
    return (
      '<ol class="dp-steps" aria-label="Các bước kết nối Kho Drive">' +
      '<li class="' + cls(1) + '"><span class="dp-n">1</span><span class="dp-t">Kết nối Google</span></li>' +
      '<li class="' + cls(2) + '"><span class="dp-n">2</span><span class="dp-t">Tạo kho</span></li>' +
      '<li class="' + cls(3) + '"><span class="dp-n">3</span><span class="dp-t">Dùng hàng ngày</span></li>' +
      "</ol>"
    );
  }

  function tipLinkDrive() {
    return (
      '<details class="dp-tip"><summary>Làm sao lấy link thư mục Drive?</summary>' +
      '<ol class="dp-ol">' +
      "<li>Mở <b>drive.google.com</b> trên trình duyệt.</li>" +
      "<li>Vào đúng thư mục muốn đồng bộ (không phải file lẻ).</li>" +
      "<li>Bấm chuột phải thư mục → <b>Chia sẻ</b> / <b>Sao chép liên kết</b> " +
      "(hoặc mở thư mục rồi chép URL trên thanh địa chỉ).</li>" +
      "<li>Dán nguyên link vào ô bên dưới. VMOS tự lấy ID thư mục.</li>" +
      "</ol>" +
      '<p class="dp-muted">Tài khoản Google vừa Allow phải <b>mở được</b> thư mục đó ' +
      "(chủ sở hữu hoặc được chia sẻ).</p></details>"
    );
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
      esc(
        t(
          "page.drive.sub",
          "Đưa một thư mục Google Drive vào bộ não - làm theo 3 bước bên dưới."
        )
      ) +
      "</p></div>" +
      '<p class="dp-diff dim">' +
      "Trang này <b>khác</b> menu Kết nối → Google Workspace. " +
      "Ở đây chỉ <b>đồng bộ thư mục</b> vào bộ não (rclone), không cần OAuth Workspace." +
      "</p>" +
      '<div id="dpSteps"></div>' +
      '<div id="dpStatus" class="jw-hint dim">Đang kiểm tra…</div>' +
      '<div id="dpConnect" class="jw-card dp-card" style="margin-top:12px;display:none"></div>' +
      '<div id="dpCreateWrap" class="jw-card dp-card" style="margin-top:12px;display:none"></div>' +
      '<div id="dpDaily" class="jw-card dp-card" style="margin-top:12px;display:none"></div>' +
      '<div id="dpList" style="margin-top:16px"></div>' +
      "</div>";

    refresh(el);
  }

  function renderCreate(el, connected) {
    var createWrap = el.querySelector("#dpCreateWrap");
    if (!createWrap) return;
    if (!connected) {
      createWrap.style.display = "none";
      createWrap.innerHTML = "";
      return;
    }
    createWrap.style.display = "";
    createWrap.innerHTML =
      "<h3>Bước 2 - Tạo kho từ thư mục Drive</h3>" +
      '<ol class="dp-ol">' +
      "<li>Đặt <b>tên kho</b> dễ nhớ (ví dụ: Giáo trình Marketing).</li>" +
      "<li>Dán <b>link thư mục</b> Google Drive.</li>" +
      "<li>Bấm <b>Tạo và đồng bộ</b> - chờ xong (lần đầu có thể vài phút).</li>" +
      "</ol>" +
      tipLinkDrive() +
      '<div class="jw-field"><label>Tên kho</label>' +
      '<input id="dpName" type="text" placeholder="Ví dụ: Giáo trình Marketing" autocomplete="off"></div>' +
      '<div class="jw-field"><label>Link thư mục Google Drive</label>' +
      '<input id="dpFolder" type="text" placeholder="https://drive.google.com/drive/folders/…" autocomplete="off"></div>' +
      '<button type="button" class="jw-btn jw-btn-primary" id="dpCreate">Tạo và đồng bộ</button>';

    createWrap.querySelector("#dpCreate").onclick = async function () {
      var name = (createWrap.querySelector("#dpName").value || "").trim();
      var folder = (createWrap.querySelector("#dpFolder").value || "").trim();
      if (!name || !folder) {
        alert("Cần tên kho và link thư mục Drive");
        return;
      }
      var btn = createWrap.querySelector("#dpCreate");
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
      createWrap.querySelector("#dpName").value = "";
      createWrap.querySelector("#dpFolder").value = "";
      await refresh(el);
    };
  }

  function renderDaily(el, hasProjects) {
    var box = el.querySelector("#dpDaily");
    if (!box) return;
    if (!hasProjects) {
      box.style.display = "none";
      return;
    }
    box.style.display = "";
    box.innerHTML =
      "<h3>Bước 3 - Dùng hàng ngày</h3>" +
      '<ol class="dp-ol">' +
      "<li>Sửa / thêm file trên <b>Google Drive</b> như bình thường.</li>" +
      "<li>Quay lại trang này → bấm <b>Đồng bộ lại</b> trên kho cần cập nhật.</li>" +
      "<li>Mở <b>Tệp tin</b> → <code>sources/drive/…</code> hoặc Dự án chat của kho.</li>" +
      "<li>Bảo Javis: <i>đọc / ingest file … rồi viết skill …</i> " +
      "- chọn từng file quan trọng, không nuốt cả kho một lần.</li>" +
      "</ol>";
  }

  function renderConnect(el, d) {
    var box = el.querySelector("#dpConnect");
    if (!box) return;
    var rc = d.rclone || {};
    var connected = !!(d.google_connected || (rc && rc.google_connected));

    if (!rc.rclone_installed) {
      box.style.display = "";
      box.innerHTML =
        "<h3>Bước 1 - Chưa sẵn sàng</h3>" +
        '<p class="jw-hint">Máy chạy VMOS cần <code>rclone</code> (bản Docker từ 0.55.154 đã có). ' +
        "Cập nhật image rồi mở lại trang này.</p>";
      return;
    }

    if (connected) {
      box.style.display = "";
      box.innerHTML =
        "<h3>Bước 1 - Google đã kết nối ✓</h3>" +
        '<p class="jw-hint"><span class="ok">Sẵn sàng tạo kho ở bước 2.</span></p>' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="dpDisconnect">Ngắt kết nối Google</button>';
      box.querySelector("#dpDisconnect").onclick = async function () {
        if (!confirm("Ngắt kết nối Google Drive?")) return;
        await postJson("/drive-projects/rclone/disconnect", {});
        await refresh(el);
      };
      return;
    }

    var local = isLocalHost();
    box.style.display = "";
    if (local) {
      box.innerHTML =
        "<h3>Bước 1 - Kết nối Google Drive</h3>" +
        '<p class="jw-hint">Bạn đang mở VMOS trên <b>máy này</b>. Chỉ cần 2 thao tác:</p>' +
        '<ol class="dp-ol">' +
        "<li>Bấm nút bên dưới → trình duyệt mở Google.</li>" +
        "<li>Chọn tài khoản → bấm <b>Allow / Cho phép</b> → quay lại trang này (tự nhận).</li>" +
        "</ol>" +
        '<button type="button" class="jw-btn jw-btn-primary" id="dpAuthLocal">1. Kết nối Google Drive</button>' +
        '<div id="dpAuthProgress" class="jw-hint" style="display:none;margin-top:8px"></div>' +
        advancedDetails();
      box.querySelector("#dpAuthLocal").onclick = function () {
        startLocalAuth(el, box);
      };
    } else {
      box.innerHTML =
        "<h3>Bước 1 - Kết nối Google Drive (máy đang trên VPS)</h3>" +
        '<p class="jw-hint">Google phải mở trên <b>máy Mac/Windows của bạn</b>, rồi gửi quyền về VPS. ' +
        "Chọn đúng hệ điều hành máy bạn đang ngồi:</p>" +
        '<div class="dp-os">' +
        '<button type="button" class="dp-os-tab on" data-os="mac">Tôi dùng Mac</button>' +
        '<button type="button" class="dp-os-tab" data-os="win">Tôi dùng Windows</button>' +
        "</div>" +
        '<button type="button" class="jw-btn jw-btn-primary" id="dpPairStart">Bắt đầu kết nối</button>' +
        '<div id="dpPairBox" style="display:none;margin-top:12px"></div>' +
        advancedDetails();
      box.querySelector("#dpPairStart").onclick = function () {
        startPair(el, box);
      };
      box.querySelectorAll(".dp-os-tab").forEach(function (tab) {
        tab.onclick = function () {
          box.querySelectorAll(".dp-os-tab").forEach(function (x) {
            x.classList.toggle("on", x === tab);
          });
          var pane = box.querySelector("#dpPairPane");
          if (pane) {
            pane.setAttribute("data-show", tab.getAttribute("data-os"));
          }
        };
      });
    }
    wireAdvanced(el, box);
  }

  function advancedDetails() {
    return (
      '<details class="dp-adv"><summary>Cách khác (chỉ khi nút trên không chạy được)</summary>' +
      '<p class="jw-hint dim" style="margin-top:8px">Dán token JSON từ rclone, hoặc upload file <code>rclone.conf</code>.</p>' +
      '<textarea id="dpToken" rows="3" class="dp-ta" placeholder=\'{"access_token":...}\'></textarea>' +
      '<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="dpTokenSave">Lưu token</button>' +
      '<input type="file" id="dpConfFile" accept=".conf,text/plain">' +
      '<button type="button" class="jw-btn jw-btn-ghost" id="dpConfUpload">Upload conf</button></div></details>'
    );
  }

  function wireAdvanced(el, box) {
    var save = box.querySelector("#dpTokenSave");
    var up = box.querySelector("#dpConfUpload");
    if (save) {
      save.onclick = async function () {
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
    }
    if (up) {
      up.onclick = async function () {
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
  }

  async function startPair(el, box) {
    stopPoll();
    var pairBox = box.querySelector("#dpPairBox");
    var btn = box.querySelector("#dpPairStart");
    var os = "mac";
    var onTab = box.querySelector(".dp-os-tab.on");
    if (onTab) os = onTab.getAttribute("data-os") || "mac";
    if (btn) btn.disabled = true;
    if (pairBox) {
      pairBox.style.display = "";
      pairBox.textContent = "Đang tạo lệnh kết nối…";
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
        '<div id="dpPairPane" data-show="' +
        esc(os) +
        '">' +
        '<div class="dp-pane" data-os="mac">' +
        "<h4>Trên Mac - làm đúng 3 bước</h4>" +
        '<ol class="dp-ol">' +
        "<li>Mở app <b>Terminal</b> (Spotlight → gõ Terminal → Enter).</li>" +
        "<li>Bấm <b>Sao chép lệnh</b> bên dưới → trong Terminal dán (Cmd+V) → Enter.</li>" +
        "<li>Trình duyệt mở Google → Allow → <b>quay lại trang Kho Drive này</b> (chờ vài giây).</li>" +
        "</ol>" +
        '<button type="button" class="jw-btn jw-btn-primary" id="dpCopyMac">Sao chép lệnh Terminal</button>' +
        '<pre class="dp-pre" id="dpMacCmd">' +
        esc(res.mac_terminal || "") +
        "</pre>" +
        '<p class="dp-muted">Không tải file <code>.command</code> nếu không cần - macOS hay chặn. ' +
        "Lệnh Terminal là cách ổn định nhất.</p>" +
        "</div>" +
        '<div class="dp-pane" data-os="win">' +
        "<h4>Trên Windows - làm đúng 3 bước</h4>" +
        '<ol class="dp-ol">' +
        "<li>Bấm <b>Tải file .bat</b> bên dưới → lưu vào Máy tính.</li>" +
        "<li>Double-click file vừa tải (nếu Windows hỏi, chọn <b>Run anyway</b>).</li>" +
        "<li>Trình duyệt mở Google → Allow → <b>quay lại trang Kho Drive này</b>.</li>" +
        "</ol>" +
        '<a class="jw-btn jw-btn-primary" href="' +
        esc(res.win_url) +
        '">Tải cho Windows (.bat)</a>' +
        "</div></div>" +
        '<p class="jw-hint" id="dpPairWait" style="margin-top:12px">Đang chờ bạn Allow Google trên máy… (còn ~15 phút)</p>';

      var copyBtn = pairBox.querySelector("#dpCopyMac");
      if (copyBtn && res.mac_terminal) {
        copyBtn.onclick = async function () {
          try {
            await navigator.clipboard.writeText(res.mac_terminal);
            copyBtn.textContent = "Đã sao chép - dán vào Terminal (Cmd+V)";
            setTimeout(function () {
              copyBtn.textContent = "Sao chép lệnh Terminal";
            }, 2800);
          } catch (e) {
            alert("Không sao chép được. Hãy bôi đen lệnh bên dưới rồi Cmd+C.");
          }
        };
      }
      box.querySelectorAll(".dp-os-tab").forEach(function (tab) {
        tab.onclick = function () {
          box.querySelectorAll(".dp-os-tab").forEach(function (x) {
            x.classList.toggle("on", x === tab);
          });
          var pane = pairBox.querySelector("#dpPairPane");
          if (pane) pane.setAttribute("data-show", tab.getAttribute("data-os"));
        };
      });
    }
    var pairId = res.pair_id;
    var n = 0;
    _pollTimer = setInterval(async function () {
      n += 1;
      if (n > 150) {
        stopPoll();
        var w = box.querySelector("#dpPairWait");
        if (w) w.innerHTML = '<span class="warn">Hết thời gian. Bấm «Bắt đầu kết nối» lại.</span>';
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
    var stEl = el.querySelector("#dpStatus");
    var listEl = el.querySelector("#dpList");
    var stepsEl = el.querySelector("#dpSteps");
    try {
      var d = await loadStatus();
      var rc = d.rclone || {};
      var connected = !!(d.google_connected || rc.google_connected);
      var projects = d.projects || [];
      if (stepsEl) stepsEl.innerHTML = stepBar(connected, projects.length > 0);

      stEl.innerHTML = !rc.rclone_installed
        ? '<span class="warn">Chưa có rclone trên máy VMOS</span>'
        : connected
          ? '<span class="ok">Google đã kết nối</span>' +
            (projects.length
              ? ' · <span class="dim">' + projects.length + " kho</span>"
              : ' · <span class="dim">chưa có kho - làm bước 2</span>')
          : '<span class="warn">Chưa kết nối Google - bắt đầu từ bước 1</span>';

      renderConnect(el, d);
      renderCreate(el, connected && rc.rclone_installed);
      renderDaily(el, projects.length > 0);

      if (!projects.length) {
        listEl.innerHTML = "";
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
              '<button type="button" class="jw-btn jw-btn-ghost" data-act="files">Mở tệp</button>' +
              '<button type="button" class="jw-btn jw-btn-ghost" data-act="del">Xoá</button>' +
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
