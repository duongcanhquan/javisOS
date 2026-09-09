/**
 * Công việc → Tạo video: workbench wizard full màn (không timeline).
 * Mỗi tab = một kiểu video; form gọn, lời gần gũi; phải = bước + kết quả.
 * Thời lượng kéo tới 10 phút; số slide/cảnh + yêu cầu riêng theo kiểu.
 */
(function () {
  "use strict";

  var MAX_DURATION_SEC = 600; /* 10 phút */

  var FEATURES = [
    {
      id: "postcard",
      pipeline: "postcard-video",
      label: "Promo ngắn",
      blurb: "Đẹp, ít chữ, nhạc + hiệu ứng",
      full: "Video promo ngắn",
      when: "Giới thiệu sản phẩm / app / dịch vụ trên Reels, TikTok, ads.",
      example: "Ra mắt app ghi chú → clip 30 giây dọc màn hình.",
      time: "Gợi ý 15–45 giây; kéo tối đa 10 phút",
      topicPh: "Ví dụ: Ra mắt app ghi chú cho học sinh",
      needsUrl: true,
      assetsLabel: "Link sản phẩm hoặc ảnh chụp màn hình *",
      assetsHint: "Cần link hoặc ảnh thật để làm đúng giao diện sản phẩm.",
      assetsPh: "https://… hoặc mô tả ảnh đã có",
      duration: {
        min: 10,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 30,
        hint: "Promo thường 15–45 giây. Kéo dài hơn nếu cần (tối đa 10 phút).",
      },
      slides: {
        min: 3,
        max: 24,
        step: 1,
        def: 6,
        label: "Số shot / khung hình",
        hint: "Mỗi shot một nhịp hình; nhiều shot = nhịp nhanh hơn trong cùng thời lượng.",
      },
      extras: [
        {
          id: "vidBgm",
          type: "select",
          label: "Nhạc nền",
          def: "có",
          options: [
            { value: "có", label: "Có nhạc nền" },
            { value: "không", label: "Không nhạc nền" },
            { value: "xuất cả hai", label: "Xuất cả bản có và không nhạc" },
          ],
        },
        {
          id: "vidSfx",
          type: "select",
          label: "Hiệu ứng âm thanh (SFX)",
          def: "vừa",
          options: [
            { value: "ít", label: "Ít" },
            { value: "vừa", label: "Vừa" },
            { value: "nhiều", label: "Nhiều / đậm beat" },
            { value: "không", label: "Không SFX" },
          ],
        },
        {
          id: "vidTextOnScreen",
          type: "select",
          label: "Chữ trên hình",
          def: "ít",
          options: [
            { value: "không", label: "Không chữ" },
            { value: "ít", label: "Ít (headline ngắn)" },
            { value: "nhiều", label: "Nhiều chữ / caption" },
          ],
        },
      ],
    },
    {
      id: "short-vo",
      pipeline: "pixcelvideo",
      label: "Có lời đọc",
      blurb: "Ảnh từng cảnh + giọng nói",
      full: "Video có lời đọc",
      when: "Muốn clip giải thích hoặc bán hàng có giọng đọc sẵn (tiếng Việt).",
      example: "Máy lọc nước gia đình → 30 giây có lời thoại.",
      time: "Kéo thời lượng tới 10 phút; số cảnh tự chia theo lời",
      topicPh: "Ví dụ: Vì sao nên dùng máy lọc nước",
      needsUrl: false,
      assetsLabel: "Link / ảnh tham khảo (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Có thì dán, không có cũng được",
      duration: {
        min: 15,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 45,
        hint: "Có lời đọc: 30–90 giây thường đủ. Video dài hơn = nhiều cảnh / lời hơn (tối đa 10 phút).",
      },
      slides: {
        min: 3,
        max: 40,
        step: 1,
        def: 6,
        label: "Số cảnh (slide ảnh)",
        hint: "Mỗi cảnh một ảnh + một đoạn lời. Tăng số cảnh nếu video dài.",
      },
      extras: [
        {
          id: "vidVoice",
          type: "select",
          label: "Giọng đọc",
          def: "tự chọn",
          options: [
            { value: "tự chọn", label: "Javis tự chọn" },
            { value: "nữ", label: "Giọng nữ" },
            { value: "nam", label: "Giọng nam" },
          ],
        },
        {
          id: "vidPace",
          type: "select",
          label: "Tốc độ đọc",
          def: "vừa",
          options: [
            { value: "chậm", label: "Chậm, rõ" },
            { value: "vừa", label: "Vừa" },
            { value: "nhanh", label: "Nhanh, năng động" },
          ],
        },
        {
          id: "vidCaptions",
          type: "select",
          label: "Phụ đề trên hình",
          def: "có",
          options: [
            { value: "có", label: "Có phụ đề" },
            { value: "không", label: "Không phụ đề" },
          ],
        },
      ],
    },
    {
      id: "collage",
      pipeline: "paperdesign",
      label: "Collage",
      blurb: "Kiểu poster giấy, có lời",
      full: "Video collage giấy",
      when: "Thích kiểu cắt dán báo / Vox: từng cảnh một poster rồi chuyển động.",
      example: "Lạm phát là gì? → collage ~45 giây có lời kể.",
      time: "Số poster = số slide; thời lượng kéo tới 10 phút",
      topicPh: "Ví dụ: Lạm phát giải thích ngắn",
      needsUrl: false,
      assetsLabel: "Ảnh / tài liệu (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Ảnh sản phẩm, logo…",
      duration: {
        min: 20,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 45,
        hint: "Collage thường 30–90 giây. Kéo dài nếu cần nhiều poster (tối đa 10 phút).",
      },
      slides: {
        min: 3,
        max: 30,
        step: 1,
        def: 6,
        label: "Số poster / slide",
        hint: "Mỗi poster một khung cắt-dán trước khi animate.",
      },
      extras: [
        {
          id: "vidPaperStyle",
          type: "select",
          label: "Kiểu giấy",
          def: "báo",
          options: [
            { value: "báo", label: "Cắt dán báo / scrapbook" },
            { value: "sạch", label: "Giấy sạch, tối giản" },
            { value: "vintage", label: "Vintage / giấy cũ" },
          ],
        },
        {
          id: "vidCollageVoice",
          type: "select",
          label: "Lời kể",
          def: "có",
          options: [
            { value: "có", label: "Có lời đọc" },
            { value: "không", label: "Chỉ hình + nhạc" },
          ],
        },
        {
          id: "vidMotion",
          type: "select",
          label: "Chuyển động poster",
          def: "vừa",
          options: [
            { value: "nhẹ", label: "Nhẹ / chậm" },
            { value: "vừa", label: "Vừa" },
            { value: "năng động", label: "Năng động" },
          ],
        },
      ],
    },
    {
      id: "remotion",
      pipeline: "remotion",
      label: "Đồ họa",
      blurb: "Số liệu, UI, chữ chạy",
      full: "Video đồ họa chuyển động",
      when: "Cần biểu đồ, dashboard, chữ/UI chuyển động mượt.",
      example: "Tăng trưởng quý 3 → biểu đồ chuyển động 20 giây.",
      time: "Kéo thời lượng tới 10 phút; chọn số cảnh đồ họa",
      topicPh: "Ví dụ: Số liệu tăng trưởng quý 3",
      needsUrl: false,
      assetsLabel: "Số liệu / ảnh (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Link sheet, ảnh dashboard…",
      duration: {
        min: 10,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 30,
        hint: "Đồ họa ngắn 15–40 giây thường đủ. Dài hơn nếu nhiều biểu đồ (tối đa 10 phút).",
      },
      slides: {
        min: 2,
        max: 20,
        step: 1,
        def: 4,
        label: "Số cảnh đồ họa",
        hint: "Mỗi cảnh một beat số liệu / UI / chữ.",
      },
      extras: [
        {
          id: "vidChartStyle",
          type: "select",
          label: "Phong cách",
          def: "sạch",
          options: [
            { value: "sạch", label: "Sạch / corporate" },
            { value: "năng động", label: "Năng động / startup" },
            { value: "vui", label: "Vui / màu nổi" },
          ],
        },
        {
          id: "vidDataAnim",
          type: "select",
          label: "Animation số liệu",
          def: "có",
          options: [
            { value: "có", label: "Có (số đếm / chart draw)" },
            { value: "nhẹ", label: "Nhẹ" },
            { value: "không", label: "Tĩnh hơn" },
          ],
        },
        {
          id: "vidRemotionVoice",
          type: "select",
          label: "Lời đọc kèm",
          def: "không",
          options: [
            { value: "không", label: "Không lời (chỉ hình)" },
            { value: "có", label: "Có lời đọc" },
          ],
        },
      ],
    },
    {
      id: "auto",
      pipeline: "để đạo diễn chọn",
      label: "Javis chọn",
      blurb: "Điền brief, để Javis quyết",
      full: "Để Javis chọn kiểu phù hợp",
      when: "Chưa chắc kiểu nào - điền đủ ý, Javis chọn đường làm.",
      example: "Giới thiệu quán cà phê → Javis chọn kiểu phù hợp.",
      time: "Thời lượng + số cảnh gợi ý; pipeline do Javis chọn",
      topicPh: "Ví dụ: Video giới thiệu cửa hàng cà phê",
      needsUrl: false,
      assetsLabel: "Link / ảnh (tuỳ chọn)",
      assetsHint: "",
      assetsPh: "Có gì dán vào đây",
      duration: {
        min: 15,
        max: MAX_DURATION_SEC,
        step: 5,
        def: 30,
        hint: "Gợi ý độ dài mong muốn (tối đa 10 phút). Javis chọn kiểu phù hợp.",
      },
      slides: {
        min: 3,
        max: 30,
        step: 1,
        def: 5,
        label: "Số cảnh gợi ý",
        hint: "Gợi ý cho đạo diễn; có thể chỉnh lại theo kiểu được chọn.",
      },
      extras: [
        {
          id: "vidPriority",
          type: "select",
          label: "Ưu tiên",
          def: "cân bằng",
          options: [
            { value: "nhanh", label: "Làm nhanh" },
            { value: "đẹp", label: "Đẹp / tỉ mỉ" },
            { value: "có lời", label: "Ưu tiên có lời đọc" },
            { value: "cân bằng", label: "Cân bằng" },
          ],
        },
        {
          id: "vidMustHave",
          type: "text",
          label: "Bắt buộc có trong video",
          def: "",
          ph: "Ví dụ: hiện logo, giá, CTA đăng ký…",
        },
      ],
    },
  ];

  var STEPS = [
    { id: "research", label: "Tìm hiểu", agents: ["nghien-cuu-chu-de-video"] },
    { id: "script", label: "Viết kịch bản", agents: ["bien-kich-video"] },
    { id: "direct", label: "Làm video", agents: ["dao-dien-video"] },
    { id: "qa", label: "Kiểm tra", agents: ["kiem-chung-video"] },
  ];

  var BASE_FIELD_IDS = [
    "vidTopic",
    "vidGoals",
    "vidAudience",
    "vidDuration",
    "vidSlides",
    "vidAspect",
    "vidLang",
    "vidChannel",
    "vidTone",
    "vidAssets",
    "vidScript",
  ];

  function formatDuration(sec) {
    var n = Math.max(0, Math.round(Number(sec) || 0));
    if (n < 60) return n + " giây";
    var m = Math.floor(n / 60);
    var s = n % 60;
    if (s === 0) return m + " phút";
    return m + " phút " + s + " giây";
  }

  function durationBrief(sec) {
    var n = Math.max(0, Math.round(Number(sec) || 0));
    return formatDuration(n) + " (" + n + "s)";
  }

  function clamp(n, lo, hi) {
    n = Number(n);
    if (!isFinite(n)) n = lo;
    return Math.min(hi, Math.max(lo, n));
  }

  function brain() {
    try {
      if (typeof window.currentBrainPath === "function") return window.currentBrainPath() || "brain";
      return "brain";
    } catch (e) {
      return "brain";
    }
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function composeBrief(v) {
    var f = v.feat;
    var parts = [
      "Chủ đề: " + v.topic,
      "Mục tiêu: " + (v.goals || "(chưa ghi)"),
      "Audience: " + (v.audience || "(chưa ghi)"),
      "Độ dài: " + (v.durationLabel || durationBrief(v.durationSec || 30)),
      "Số slide / cảnh / shot: " + (v.slides || "(chưa ghi)"),
      "Tỉ lệ: " + (v.aspect || "9:16"),
      "Ngôn ngữ VO + chữ trên hình: " + (v.lang || "vi"),
      "Kênh: " + (v.channel || "(chưa ghi)"),
      "Pipeline: " + (f.pipeline || "để đạo diễn chọn"),
      "Tone / vibe: " + (v.tone || "(chưa ghi)"),
    ];
    if (v.extras && v.extras.length) {
      parts.push("Yêu cầu theo kiểu «" + f.full + "»:");
      v.extras.forEach(function (ex) {
        parts.push("- " + ex.label + ": " + ex.value);
      });
    }
    if (v.assets) parts.push("Tài sản / URL: " + v.assets);
    if (v.script) parts.push("Kịch bản / beat dán sẵn:\n" + v.script);
    if (v.files && v.files.length) parts.push("File đính kèm:\n- " + v.files.join("\n- "));
    parts.push(
      "Yêu cầu UI Tạo video: làm đúng pipeline đã chọn; tôn trọng độ dài và số slide đã chọn; thiếu môi trường thì nói rõ và đưa Manual pack, không hứa suông."
    );
    return parts.join("\n");
  }

  function formatLogLine(raw) {
    var s = String(raw == null ? "" : raw);
    if (/^#{1,3}\s/.test(s.trim())) {
      return '<span class="jw-h">' + esc(s.trim().replace(/^#+\s*/, "")) + "</span>";
    }
    if (/^\[(step|status|step_start|xong bước|step_done)/i.test(s.trim())) {
      return '<span class="jw-step">' + esc(s) + "</span>";
    }
    return esc(s);
  }

  function agentToStep(agent) {
    var a = String(agent || "").toLowerCase();
    for (var i = 0; i < STEPS.length; i++) {
      for (var j = 0; j < STEPS[i].agents.length; j++) {
        if (a.indexOf(STEPS[i].agents[j]) >= 0) return i;
      }
    }
    return -1;
  }

  function extrasHtml(f) {
    var list = f.extras || [];
    if (!list.length) return "";
    var html =
      '<p class="jw-sec">3. Yêu cầu «' +
      esc(f.label) +
      '»</p><div class="jw-type-opts">';
    list.forEach(function (ex) {
      html += '<div class="jw-field"><label for="' + esc(ex.id) + '">' + esc(ex.label) + "</label>";
      if (ex.type === "text") {
        html +=
          '<input id="' +
          esc(ex.id) +
          '" type="text" autocomplete="off" placeholder="' +
          esc(ex.ph || "") +
          '">';
      } else {
        html += '<select id="' + esc(ex.id) + '">';
        (ex.options || []).forEach(function (o) {
          html +=
            '<option value="' +
            esc(o.value) +
            '"' +
            (o.value === ex.def ? " selected" : "") +
            ">" +
            esc(o.label) +
            "</option>";
        });
        html += "</select>";
      }
      html += "</div>";
    });
    html += "</div>";
    return html;
  }

  function rangeField(opts) {
    return (
      '<div class="jw-field jw-field-range">' +
      '<div class="jw-range-head"><label for="' +
      esc(opts.id) +
      '">' +
      esc(opts.label) +
      '</label><span class="jw-range-val" id="' +
      esc(opts.valId) +
      '">' +
      esc(opts.valText) +
      "</span></div>" +
      '<input id="' +
      esc(opts.id) +
      '" type="range" min="' +
      opts.min +
      '" max="' +
      opts.max +
      '" step="' +
      opts.step +
      '" value="' +
      opts.value +
      '">' +
      '<div class="jw-range-ends"><span>' +
      esc(opts.minLabel) +
      "</span><span>" +
      esc(opts.maxLabel) +
      "</span></div>" +
      (opts.hint ? '<p class="jw-hint">' + esc(opts.hint) + "</p>" : "") +
      "</div>"
    );
  }

  window.renderTaoVideo = function (root) {
    if (!root) return;
    var uploaded = [];
    var es = null;
    var tabIdx = 0;
    var running = false;
    var stepIdx = -1;
    var draft = {};

    root.innerHTML =
      '<div class="jw jw-video" id="vidJw">' +
      '<div class="jw-top">' +
      '<div class="jw-top-row">' +
      "<div><h2 class=\"jw-title\">Tạo video</h2>" +
      '<p class="jw-lead">Chọn một kiểu ở hàng tab → điền vài dòng bên trái → bấm <b>Tạo video</b>. Theo dõi bước bên phải.</p></div>' +
      "</div>" +
      '<div class="jw-tabs jw-tabs-video" role="tablist" id="vidTabs"></div>' +
      '<p class="jw-tab-hint" id="vidTabHint"></p>' +
      "</div>" +
      '<div class="jw-body">' +
      '<aside class="jw-left"><div class="jw-left-scroll" id="vidLeft"></div></aside>' +
      '<section class="jw-right">' +
      '<div class="jw-right-head"><h3>Đang làm gì</h3><div class="jw-status" id="vidStatus">Chưa chạy</div></div>' +
      '<ol class="jw-steps" id="vidSteps" aria-label="Các bước làm video"></ol>' +
      '<div class="jw-out" id="vidOut">' +
      '<div class="jw-empty" id="vidEmpty">' +
      "<strong>Bắt đầu từ bên trái</strong>" +
      "Chọn tab kiểu video, ghi chủ đề và mục tiêu, rồi bấm Tạo video. " +
      "Tiến trình hiện ở đây. File xong thường nằm trong Files → attachments/videos/." +
      "</div>" +
      '<pre class="jw-log" id="vidLog" hidden></pre>' +
      "</div></section></div></div>";

    var tabsEl = root.querySelector("#vidTabs");
    FEATURES.forEach(function (f, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "jw-tab jw-tab-stack" + (i === 0 ? " on" : "");
      b.setAttribute("role", "tab");
      b.setAttribute("aria-selected", i === 0 ? "true" : "false");
      b.setAttribute("data-i", String(i));
      b.innerHTML =
        '<span class="jw-tab-label">' +
        esc(f.label) +
        '</span><span class="jw-tab-blurb">' +
        esc(f.blurb) +
        "</span>";
      tabsEl.appendChild(b);
    });

    function feat() {
      return FEATURES[tabIdx] || FEATURES[0];
    }

    function fieldIds() {
      var ids = BASE_FIELD_IDS.slice();
      (feat().extras || []).forEach(function (ex) {
        ids.push(ex.id);
      });
      return ids;
    }

    function paintTabHint() {
      var f = feat();
      var el = root.querySelector("#vidTabHint");
      if (!el) return;
      el.innerHTML =
        "<b>" +
        esc(f.full) +
        "</b> · " +
        esc(f.blurb) +
        ' <span class="dim">· ' +
        esc(f.time) +
        "</span>";
    }

    function paintSteps() {
      var el = root.querySelector("#vidSteps");
      if (!el) return;
      el.innerHTML = STEPS.map(function (s, i) {
        var cls = "jw-step-item" + (i === stepIdx ? " on" : i < stepIdx ? " done" : "");
        return (
          '<li class="' +
          cls +
          '"><span class="n">' +
          (i + 1) +
          '</span><span class="jw-step-lab">' +
          esc(s.label) +
          "</span></li>"
        );
      }).join("");
    }

    function setStatus(msg, kind) {
      var el = root.querySelector("#vidStatus");
      if (!el) return;
      el.textContent = msg || "";
      el.className = "jw-status" + (kind === false ? " err" : kind === true ? " ok" : "");
    }

    function showLog() {
      var empty = root.querySelector("#vidEmpty");
      var log = root.querySelector("#vidLog");
      if (empty) empty.hidden = true;
      if (log) log.hidden = false;
    }

    function appendLog(line) {
      showLog();
      var log = root.querySelector("#vidLog");
      if (!log) return;
      log.innerHTML += formatLogLine(line) + "\n";
      var out = root.querySelector("#vidOut");
      if (out) out.scrollTop = out.scrollHeight;
    }

    function advanceStep(agent) {
      var i = agentToStep(agent);
      if (i >= 0 && i !== stepIdx) {
        stepIdx = i;
        paintSteps();
      }
    }

    function saveDraft() {
      fieldIds().forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (el) draft[id] = el.value;
      });
    }

    function restoreDraft() {
      var f = feat();
      var dCfg = f.duration || {};
      var sCfg = f.slides || {};
      var durEl = root.querySelector("#vidDuration");
      var slidesEl = root.querySelector("#vidSlides");

      BASE_FIELD_IDS.forEach(function (id) {
        if (id === "vidDuration" || id === "vidSlides") return;
        var el = root.querySelector("#" + id);
        if (el && draft[id] != null) el.value = draft[id];
      });

      if (durEl) {
        var rawDur = draft.vidDuration != null ? draft.vidDuration : dCfg.def;
        durEl.value = String(clamp(rawDur, dCfg.min || 10, dCfg.max || MAX_DURATION_SEC));
      }
      if (slidesEl) {
        var rawSl = draft.vidSlides != null ? draft.vidSlides : sCfg.def;
        slidesEl.value = String(clamp(rawSl, sCfg.min || 1, sCfg.max || 24));
      }

      (f.extras || []).forEach(function (ex) {
        var el = root.querySelector("#" + ex.id);
        if (!el) return;
        if (draft[ex.id] != null && draft[ex.id] !== "") {
          el.value = draft[ex.id];
        } else if (ex.def != null && ex.type !== "text") {
          el.value = ex.def;
        } else if (ex.type === "text" && ex.def) {
          el.value = ex.def;
        }
      });

      syncRangeLabels();
    }

    function syncRangeLabels() {
      var f = feat();
      var durEl = root.querySelector("#vidDuration");
      var durVal = root.querySelector("#vidDurationVal");
      if (durEl && durVal) {
        durVal.textContent = formatDuration(durEl.value);
      }
      var slidesEl = root.querySelector("#vidSlides");
      var slidesVal = root.querySelector("#vidSlidesVal");
      if (slidesEl && slidesVal) {
        var n = slidesEl.value;
        var lab = (f.slides && f.slides.label) || "Số cảnh";
        slidesVal.textContent = n + " · " + lab.replace(/^Số\s+/i, "").toLowerCase();
      }
    }

    function paintLeft() {
      var f = feat();
      var d = f.duration || { min: 10, max: MAX_DURATION_SEC, step: 5, def: 30 };
      var s = f.slides || { min: 3, max: 24, step: 1, def: 5, label: "Số cảnh" };
      var left = root.querySelector("#vidLeft");
      left.innerHTML =
        '<div class="jw-brief jw-brief-lite">' +
        '<p class="jw-brief-kicker">Kiểu đang chọn</p>' +
        "<h3>" +
        esc(f.full) +
        "</h3>" +
        "<p>" +
        esc(f.when) +
        "</p>" +
        '<p class="jw-ex">Ví dụ: ' +
        esc(f.example) +
        "</p>" +
        "</div>" +
        '<p class="jw-sec">1. Bạn muốn nói gì</p>' +
        '<div class="jw-field"><label for="vidTopic">Chủ đề *</label>' +
        '<input id="vidTopic" type="text" autocomplete="off" placeholder="' +
        esc(f.topicPh) +
        '"></div>' +
        '<div class="jw-field"><label for="vidGoals">Mục tiêu *</label>' +
        '<textarea id="vidGoals" rows="2" placeholder="Ví dụ: Để mọi người nhớ sản phẩm / muốn thử / hiểu một ý"></textarea></div>' +
        '<div class="jw-field"><label for="vidAudience">Người xem</label>' +
        '<input id="vidAudience" type="text" placeholder="Ví dụ: Phụ huynh, chủ quán, học sinh"></div>' +
        '<p class="jw-sec">2. Hình thức</p>' +
        rangeField({
          id: "vidDuration",
          valId: "vidDurationVal",
          label: "Dài bao lâu *",
          min: d.min,
          max: d.max,
          step: d.step || 5,
          value: d.def,
          valText: formatDuration(d.def),
          minLabel: formatDuration(d.min),
          maxLabel: formatDuration(d.max),
          hint: d.hint || "",
        }) +
        rangeField({
          id: "vidSlides",
          valId: "vidSlidesVal",
          label: (s.label || "Số slide / cảnh") + " *",
          min: s.min,
          max: s.max,
          step: s.step || 1,
          value: s.def,
          valText: String(s.def),
          minLabel: String(s.min),
          maxLabel: String(s.max),
          hint: s.hint || "",
        }) +
        '<div class="jw-row2">' +
        '<div class="jw-field"><label for="vidAspect">Khung hình *</label>' +
        '<select id="vidAspect">' +
        '<option value="9:16" selected>Dọc điện thoại (Reels/TikTok)</option>' +
        '<option value="1:1">Vuông</option>' +
        '<option value="16:9">Ngang (YouTube)</option>' +
        "</select></div>" +
        '<div class="jw-field"><label for="vidLang">Ngôn ngữ *</label>' +
        '<select id="vidLang"><option value="vi">Tiếng Việt</option><option value="en">English</option></select></div></div>' +
        '<div class="jw-field"><label for="vidChannel">Đăng ở đâu</label>' +
        '<input id="vidChannel" type="text" placeholder="Reels, TikTok, YouTube, Ads…"></div>' +
        '<div class="jw-field"><label for="vidAssets">' +
        esc(f.assetsLabel) +
        "</label>" +
        '<textarea id="vidAssets" rows="2" placeholder="' +
        esc(f.assetsPh) +
        '"></textarea>' +
        (f.assetsHint ? '<p class="jw-hint">' + esc(f.assetsHint) + "</p>" : "") +
        "</div>" +
        extrasHtml(f) +
        '<details class="jw-more">' +
        "<summary>Thêm kịch bản, tone, file (tuỳ chọn)</summary>" +
        '<div class="jw-field"><label for="vidTone">Giọng / cảm xúc</label>' +
        '<input id="vidTone" type="text" placeholder="Ví dụ: Ấm áp, sạch sẽ, vui, chuyên nghiệp"></div>' +
        '<div class="jw-field"><label for="vidScript">Kịch bản sẵn có</label>' +
        '<textarea id="vidScript" rows="5" placeholder="Có outline hoặc lời thoại thì dán vào. Để trống = Javis viết giúp."></textarea></div>' +
        '<div class="jw-field"><label for="vidFiles">Đính kèm ảnh / logo / file nghe</label>' +
        '<input id="vidFiles" type="file" multiple>' +
        '<p class="jw-hint" id="vidFileList">Chưa chọn file</p></div>' +
        '<div class="jw-actions jw-actions-ghost">' +
        '<button type="button" class="jw-btn jw-btn-ghost" id="vidSeed">Cài bộ làm video (một lần)</button>' +
        "</div></details>" +
        '<div class="jw-actions jw-actions-main">' +
        '<button type="button" class="jw-btn jw-btn-primary" id="vidRun">Tạo video · ' +
        esc(f.label) +
        "</button>" +
        '<button type="button" class="jw-btn jw-btn-ghost" id="vidStop" disabled>Dừng xem</button>' +
        "</div>" +
        '<p class="jw-hint jw-hint-foot">Lần đầu có thể bấm «Cài bộ làm video» trong mục tuỳ chọn. Các lần sau cứ Tạo video.</p>';

      restoreDraft();
      wireLeft();
      paintTabHint();
    }

    function wireLeft() {
      fieldIds().forEach(function (id) {
        var el = root.querySelector("#" + id);
        if (!el) return;
        el.addEventListener("change", saveDraft);
        el.addEventListener("input", function () {
          if (id === "vidDuration" || id === "vidSlides") syncRangeLabels();
          saveDraft();
        });
      });

      var filesEl = root.querySelector("#vidFiles");
      if (filesEl) {
        filesEl.onchange = async function () {
          var files = Array.from(filesEl.files || []);
          uploaded = [];
          var list = root.querySelector("#vidFileList");
          if (!files.length) {
            if (list) list.textContent = "Chưa chọn file";
            return;
          }
          if (list) list.textContent = "Đang tải…";
          for (var i = 0; i < files.length; i++) {
            var fd = new FormData();
            fd.append("file", files[i]);
            fd.append("brain", brain());
            try {
              var r = await (await fetch("/upload", { method: "POST", body: fd })).json();
              if (r && (r.path || r.name)) uploaded.push(r.path || r.name);
              else if (r && r.error) appendLog("Upload lỗi: " + r.error);
            } catch (e) {
              appendLog("Upload lỗi: " + ((e && e.message) || e));
            }
          }
          if (list) {
            list.textContent = uploaded.length
              ? "Đã tải: " + uploaded.join(", ")
              : "Không tải được file.";
          }
        };
      }

      var stopBtn = root.querySelector("#vidStop");
      if (stopBtn) {
        stopBtn.onclick = function () {
          try {
            if (es) es.close();
          } catch (e) {}
          es = null;
          setBusy(false, "Đã dừng theo dõi (việc trên máy có thể vẫn chạy).", true);
        };
      }

      var runBtn = root.querySelector("#vidRun");
      if (runBtn) runBtn.onclick = run;

      var seedBtn = root.querySelector("#vidSeed");
      if (seedBtn) {
        seedBtn.onclick = async function () {
          if (running) return;
          seedBtn.disabled = true;
          seedBtn.textContent = "Đang cài…";
          setStatus("Đang cài bộ làm video…");
          try {
            var fd = new FormData();
            fd.append("brain", brain());
            var r = await (await fetch("/studio/seed-video", { method: "POST", body: fd })).json();
            if (!r || !r.ok) {
              setStatus((r && r.error) || "Cài chưa xong", false);
              return;
            }
            setStatus("Đã sẵn sàng. Bạn có thể bấm Tạo video.", true);
          } catch (e) {
            setStatus(String((e && e.message) || e), false);
          } finally {
            seedBtn.disabled = false;
            seedBtn.textContent = "Cài bộ làm video (một lần)";
          }
        };
      }
    }

    function selectTab(i) {
      saveDraft();
      tabIdx = i;
      tabsEl.querySelectorAll(".jw-tab").forEach(function (btn, j) {
        var on = j === i;
        btn.classList.toggle("on", on);
        btn.setAttribute("aria-selected", on ? "true" : "false");
      });
      paintLeft();
    }

    function clearFieldErrors() {
      root.querySelectorAll(".jw-field.err").forEach(function (w) {
        w.classList.remove("err");
      });
    }

    function markField(id, bad) {
      var el = root.querySelector("#" + id);
      if (!el) return;
      var wrap = el.closest(".jw-field");
      if (wrap) wrap.classList.toggle("err", !!bad);
      if (bad) {
        try {
          el.focus();
        } catch (e) {}
      }
    }

    function setBusy(busy, statusMsg, statusOk) {
      running = !!busy;
      var f = feat();
      var runBtn = root.querySelector("#vidRun");
      var stopBtn = root.querySelector("#vidStop");
      var seedBtn = root.querySelector("#vidSeed");
      if (runBtn) {
        runBtn.disabled = busy;
        runBtn.classList.toggle("jw-busy", busy);
        runBtn.textContent = busy ? "Đang tạo…" : "Tạo video · " + f.label;
      }
      if (stopBtn) stopBtn.disabled = !busy;
      if (seedBtn) seedBtn.disabled = busy;
      tabsEl.querySelectorAll(".jw-tab").forEach(function (t) {
        t.disabled = busy;
      });
      if (statusMsg != null) setStatus(statusMsg, statusOk);
    }

    function readExtras() {
      var f = feat();
      var out = [];
      (f.extras || []).forEach(function (ex) {
        var el = root.querySelector("#" + ex.id);
        var val = el ? String(el.value || "").trim() : "";
        if (!val && ex.type === "text") return;
        if (!val) val = ex.def || "";
        out.push({ id: ex.id, label: ex.label, value: val });
      });
      return out;
    }

    function validateInputs() {
      clearFieldErrors();
      var f = feat();
      saveDraft();
      var topic = ((root.querySelector("#vidTopic") || {}).value || "").trim();
      var goals = ((root.querySelector("#vidGoals") || {}).value || "").trim();
      var assets = ((root.querySelector("#vidAssets") || {}).value || "").trim();
      var durCfg = f.duration || {};
      var slCfg = f.slides || {};
      var durationSec = clamp(
        (root.querySelector("#vidDuration") || {}).value,
        durCfg.min || 10,
        durCfg.max || MAX_DURATION_SEC
      );
      var slides = clamp(
        (root.querySelector("#vidSlides") || {}).value,
        slCfg.min || 1,
        slCfg.max || 40
      );
      var missing = [];
      if (!topic) {
        markField("vidTopic", true);
        missing.push("Chủ đề");
      }
      if (!goals) {
        markField("vidGoals", true);
        missing.push("Mục tiêu");
      }
      if (f.needsUrl && !assets) {
        markField("vidAssets", true);
        missing.push("Link / ảnh sản phẩm");
      }
      if (missing.length) {
        setStatus("Thiếu: " + missing.join(", ") + ". Điền bên trái rồi bấm Tạo video.", false);
        return null;
      }
      return {
        topic: topic,
        goals: goals,
        audience: ((root.querySelector("#vidAudience") || {}).value || "").trim(),
        durationSec: durationSec,
        durationLabel: durationBrief(durationSec),
        slides: slides,
        aspect: ((root.querySelector("#vidAspect") || {}).value || "9:16").trim(),
        lang: ((root.querySelector("#vidLang") || {}).value || "vi").trim(),
        channel: ((root.querySelector("#vidChannel") || {}).value || "").trim(),
        tone: ((root.querySelector("#vidTone") || {}).value || "").trim(),
        assets: assets,
        script: ((root.querySelector("#vidScript") || {}).value || "").trim(),
        extras: readExtras(),
        files: uploaded.slice(),
        feat: f,
      };
    }

    function finishBusy(statusMsg, statusOk) {
      try {
        if (es) es.close();
      } catch (e) {}
      es = null;
      if (statusOk) {
        stepIdx = STEPS.length - 1;
        paintSteps();
      }
      setBusy(false, statusMsg, statusOk);
    }

    tabsEl.querySelectorAll(".jw-tab").forEach(function (btn) {
      btn.onclick = function () {
        if (running) {
          setStatus("Đang chạy - chờ xong hoặc bấm Dừng xem trước khi đổi tab.", false);
          return;
        }
        selectTab(parseInt(btn.getAttribute("data-i"), 10) || 0);
      };
    });

    async function run() {
      if (running) return;
      var v = validateInputs();
      if (!v) return;

      var f = v.feat;
      var brief = composeBrief(v);

      stepIdx = 0;
      paintSteps();
      setBusy(true, "Đang tạo «" + f.full + "»…");
      if (es) {
        try {
          es.close();
        } catch (e1) {}
        es = null;
      }
      var log = root.querySelector("#vidLog");
      if (log) log.innerHTML = "";
      appendLog("--- Brief ---\n" + brief + "\n---");

      try {
        var fd0 = new FormData();
        fd0.append("brain", brain());
        await fetch("/studio/seed-video", { method: "POST", body: fd0 });
      } catch (e0) {}

      var url =
        "/workflows/run?slug=" +
        encodeURIComponent("bo-video-da-pipeline") +
        "&brain=" +
        encodeURIComponent(brain()) +
        "&input=" +
        encodeURIComponent(brief);
      es = new EventSource(url);
      es.onmessage = function (ev) {
        try {
          var data = JSON.parse(ev.data);
          var typ = data.type || "";
          if (typ === "token" || typ === "text" || typ === "chunk") {
            appendLog(data.text || data.token || data.content || "");
          } else if (typ === "step" || typ === "status" || typ === "step_start") {
            advanceStep(data.agent || data.message || "");
            appendLog(
              "[" + typ + "] " + (data.message || data.agent || data.step || JSON.stringify(data))
            );
          } else if (typ === "step_done") {
            advanceStep(data.agent || "");
            appendLog("[xong bước] " + (data.agent || ""));
            if (data.output) {
              var out = String(data.output);
              appendLog(out.length > 5000 ? out.slice(0, 5000) + "\n…(cắt)" : out);
            }
          } else if (typ === "error") {
            appendLog("ERROR: " + (data.message || data.error || ev.data));
            finishBusy("Lỗi khi tạo video", false);
          } else if (typ === "done" || typ === "complete") {
            if (data.result) {
              var res = String(data.result);
              appendLog(res.length > 8000 ? res.slice(0, 8000) + "\n…(cắt)" : res);
            }
            appendLog("--- Xong ---");
            finishBusy("Xong. Xem Files → attachments/videos/ (hoặc đường dẫn trong log).", true);
          } else {
            appendLog(ev.data);
          }
        } catch (eParse) {
          appendLog(ev.data);
        }
      };
      es.onerror = function () {
        finishBusy("Mất kết nối (có thể đã xong hoặc lỗi). Xem log bên dưới.", false);
      };
    }

    paintSteps();
    paintLeft();
  };
})();
