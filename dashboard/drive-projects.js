/* Trang Kho Drive: sync rclone Google Drive → sources/drive/<slug>/ + Dự án chat. */
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

  function render(el) {
    if (!el) return;
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
          "Đồng bộ thư mục Google Drive (rclone) vào Second Brain, gắn Dự án chat để học và viết skill."
        )
      ) +
      "</p></div>" +
      '<div id="dpStatus" class="jw-hint dim">Đang kiểm tra rclone…</div>' +
      '<div class="jw-card" style="margin-top:12px">' +
      "<h3>Tạo kho mới</h3>" +
      '<div class="jw-field"><label>Tên kho</label>' +
      '<input id="dpName" type="text" placeholder="Ví dụ: Giáo trình Marketing"></div>' +
      '<div class="jw-field"><label>Drive folder ID</label>' +
      '<input id="dpFolder" type="text" placeholder="Lấy từ URL thư mục Drive"></div>' +
      '<div class="jw-field"><label>rclone remote</label>' +
      '<input id="dpRemote" type="text" value="gdrive:" placeholder="Ví dụ: gdrive:"></div>' +
      '<button type="button" class="jw-btn jw-btn-primary" id="dpCreate">Tạo kho</button>' +
      "</div>" +
      '<div id="dpList" style="margin-top:16px"></div>' +
      '<p class="jw-hint" style="margin-top:16px">Hướng dẫn VPS: <code>docs/29-kho-drive.md</code> · ' +
      "<code>scripts/setup-rclone-drive-vps.sh</code></p>" +
      "</div>";

    el.querySelector("#dpCreate").onclick = async function () {
      var name = (el.querySelector("#dpName").value || "").trim();
      var folder = (el.querySelector("#dpFolder").value || "").trim();
      var remote = (el.querySelector("#dpRemote").value || "gdrive:").trim();
      if (!name || !folder) {
        alert("Cần tên kho và Drive folder ID");
        return;
      }
      var res = await postJson("/drive-projects", {
        name: name,
        drive_folder_id: folder,
        rclone_remote: remote,
        brain: brain(),
      });
      if (!res.ok) {
        alert(res.error || "Tạo thất bại");
        return;
      }
      el.querySelector("#dpName").value = "";
      el.querySelector("#dpFolder").value = "";
      await refresh(el);
    };

    refresh(el);
  }

  async function refresh(el) {
    var stEl = el.querySelector("#dpStatus");
    var listEl = el.querySelector("#dpList");
    try {
      var d = await loadStatus();
      var rc = d.rclone || {};
      var remotes = (rc.remotes || []).join(", ") || "(không có)";
      stEl.innerHTML = rc.rclone_installed
        ? '<span class="ok">rclone OK</span> · remotes: ' + esc(remotes)
        : '<span class="warn">Chưa có rclone trên máy chạy Javis</span> — ' +
          esc(d.hint || "");
      var projects = d.projects || [];
      if (!projects.length) {
        listEl.innerHTML = '<p class="dim">Chưa có kho nào trên brain này.</p>';
        return;
      }
      listEl.innerHTML =
        "<h3>Kho trên brain này</h3>" +
        projects
          .map(function (p) {
            var syncBadge =
              p.last_sync_ok === true
                ? '<span class="ok">sync OK</span>'
                : p.last_sync_ok === false
                  ? '<span class="warn">sync lỗi</span>'
                  : '<span class="dim">chưa sync</span>';
            var stats = p.last_sync_stats || {};
            var statsLine =
              stats.mirrored != null
                ? " · mirror " + stats.mirrored + " text / " + (stats.stubs || 0) + " stub"
                : "";
            return (
              '<div class="jw-card" style="margin-top:10px" data-id="' +
              esc(p.id) +
              '">' +
              "<div><b>" +
              esc(p.name) +
              "</b> <code>" +
              esc(p.slug) +
              "</code> " +
              syncBadge +
              statsLine +
              "</div>" +
              '<div class="dim" style="font-size:12px;margin-top:4px">' +
              "folder <code>" +
              esc(p.drive_folder_id) +
              "</code> · remote <code>" +
              esc(p.rclone_remote) +
              "</code><br>" +
              "lần sync: " +
              esc(when(p.last_sync_at)) +
              (p.last_sync_error ? " · " + esc(p.last_sync_error) : "") +
              (p.chat_project_id
                ? "<br>Dự án chat: <code>" + esc(p.chat_project_id) + "</code>"
                : "") +
              "<br>Sources: <code>sources/drive/" +
              esc(p.slug) +
              "/</code>" +
              "</div>" +
              '<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">' +
              '<button type="button" class="jw-btn jw-btn-primary" data-act="sync">Đồng bộ ngay</button>' +
              '<button type="button" class="jw-btn" data-act="files">Mở Tệp tin</button>' +
              '<button type="button" class="jw-btn" data-act="del">Xoá kho</button>' +
              "</div></div>"
            );
          })
          .join("");

      listEl.querySelectorAll("[data-id]").forEach(function (card) {
        var id = card.getAttribute("data-id");
        card.querySelector('[data-act="sync"]').onclick = async function () {
          var btn = this;
          btn.disabled = true;
          btn.textContent = "Đang sync…";
          var res = await postJson("/drive-projects/" + encodeURIComponent(id) + "/sync", {});
          btn.disabled = false;
          btn.textContent = "Đồng bộ ngay";
          if (!res.ok) {
            alert(res.error || (res.rclone && res.rclone.error) || "Sync thất bại");
          }
          await refresh(el);
        };
        card.querySelector('[data-act="files"]').onclick = function () {
          var slug = (projects.find(function (x) {
            return x.id === id;
          }) || {}).slug;
          if (window.JavisOpenFiles && slug) {
            window.JavisOpenFiles("sources/drive/" + slug + "/");
          } else {
            alert("Mở trang Tệp tin → sources/drive/" + (slug || ""));
          }
        };
        card.querySelector('[data-act="del"]').onclick = async function () {
          if (!confirm("Xoá kho khỏi registry? (không xoá corpus; sources giữ lại)")) return;
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
