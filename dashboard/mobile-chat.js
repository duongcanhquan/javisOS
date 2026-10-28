// Wiring giao diện chat trên điện thoại (mobile-only, <=860px):
//  - dời chip model (#mbOpen + #mbPop) và nút + (#newChatBtn) lên header khi mobile, trả về khi desktop
//  - dời nhóm Hệ thống (chọn brain, đổi tông, loa, dải HỆ THỐNG) vào đáy ngăn kéo
//  - nút + = hội thoại mới (reset) + focus ô nhập
//  - ngăn kéo điều hướng: nút menu mở/đóng, backdrop / Esc / chọn mục thì đóng
//  - rút gọn placeholder ô nhập cho vừa bề ngang điện thoại
(function () {
  function init() {
    var mq = window.matchMedia("(max-width: 860px)");
    var railEl = document.querySelector(".rail");
    var railParent = railEl ? railEl.parentElement : null;
    var railNext = railEl ? railEl.nextSibling : null;

    // ---- 1) Header mobile: dời chip model + nút + lên header; desktop trả về chỗ cũ ----
    var mbOpen = document.getElementById("mbOpen");
    var mbPop = document.getElementById("mbPop");
    var modelBar = document.getElementById("modelBar");
    var headerRoot = document.querySelector(".hud-top");
    var headerCenter = document.querySelector(".hud-center-title");
    var newChatBtn = document.getElementById("newChatBtn");
    var origNewChatParent = newChatBtn ? newChatBtn.parentElement : null;
    var notificationTrigger = document.getElementById("notificationTrigger");
    var origNotificationParent = notificationTrigger ? notificationTrigger.parentElement : null;
    var origNotificationNext = notificationTrigger ? notificationTrigger.nextSibling : null;
    function placeHeader() {
      if (!headerRoot) return;
      if (mq.matches) {
        if (notificationTrigger && notificationTrigger.parentElement !== headerRoot) {
          var navToggle = document.getElementById("navToggle");
          if (navToggle && navToggle.parentElement === headerRoot) headerRoot.insertBefore(notificationTrigger, navToggle.nextSibling);
          else headerRoot.insertBefore(notificationTrigger, headerRoot.firstChild);
        }
        if (mbOpen && mbOpen.parentElement !== headerRoot) {
          if (headerCenter && headerCenter.parentElement === headerRoot) headerRoot.insertBefore(mbOpen, headerCenter.nextSibling);
          else headerRoot.appendChild(mbOpen);
          if (mbPop) headerRoot.insertBefore(mbPop, mbOpen.nextSibling);
        }
        if (newChatBtn && newChatBtn.parentElement !== headerRoot) headerRoot.appendChild(newChatBtn);  // + về cuối header
      } else {
        if (mbOpen && modelBar && mbOpen.parentElement !== modelBar) {
          modelBar.insertBefore(mbOpen, modelBar.firstChild);
          if (mbPop) modelBar.insertBefore(mbPop, mbOpen.nextSibling);
        }
        if (newChatBtn && origNewChatParent && newChatBtn.parentElement !== origNewChatParent) origNewChatParent.appendChild(newChatBtn);
        if (notificationTrigger && origNotificationParent && notificationTrigger.parentElement !== origNotificationParent) {
          if (origNotificationNext && origNotificationNext.parentElement === origNotificationParent) {
            origNotificationParent.insertBefore(notificationTrigger, origNotificationNext);
          } else {
            origNotificationParent.appendChild(notificationTrigger);
          }
        }
      }
    }

    // ---- 2) Nhóm Hệ thống: mobile dời vào đáy ngăn kéo, desktop trả về chỗ cũ ----
    var sysHost = null, sysBtns = null, moved = [];
    function ensureSysHost() {
      if (sysHost || !railEl) return;
      sysHost = document.createElement("div");
      sysHost.className = "rail-sys";
      var lbl = document.createElement("div");
      lbl.className = "rail-sys-lbl";
      lbl.textContent = "Hệ thống";
      sysHost.appendChild(lbl);
      sysBtns = document.createElement("div");
      sysBtns.className = "rail-sys-btns";
      sysHost.appendChild(sysBtns);
      var foot = railEl.querySelector(".rail-foot");
      railEl.insertBefore(sysHost, foot || null);
    }
    function moveEl(el, toBtns) {
      if (!el) return;
      ensureSysHost();
      if (!sysHost) return;
      moved.push({ el: el, parent: el.parentElement, next: el.nextSibling });
      (toBtns ? sysBtns : sysHost).appendChild(el);
    }
    // Gỡ hẳn khung "Hệ thống" khỏi rail. PHẢI có hàm này: `ensureSysHost` dựng khung một lần
    // rồi giữ tham chiếu, còn `placeSystem` trước đây chỉ trả các nút về chỗ cũ mà KHÔNG dọn
    // cái khung rỗng. Nên sau một lần đi qua màn hẹp là cái nhãn "Hệ thống" ở lại vĩnh viễn,
    // đứng chình ình trên hàng version mà bên dưới chẳng còn gì (chủ repo báo 01/09: "thi
    // thoảng chữ hệ thống to lại hiện ra trong khi chỗ đó đáng nhẽ là không có gì").
    function boSysHost() {
      if (sysHost && sysHost.parentElement) sysHost.parentElement.removeChild(sysHost);
      sysHost = null; sysBtns = null;
    }
    function placeSystem() {
      if (mq.matches) {
        if (!moved.length) {
          moveEl(document.querySelector(".navbar-brain"), false);
          moveEl(document.getElementById("themeWrap") || document.getElementById("themeToggle"), true);
          // Nút loa header đã bỏ (0.48.3), nút loa thanh nhập cũng bỏ (02/09): giọng đi theo
          // mic, bấm mic là bật loa. Không còn nút loa nào để dời cả.
          moveEl(document.getElementById("sysBar"), false);
        }
        // Nhãn không được đứng một mình. Mấy nút mượn nằm trong HUD, mà HUD bị vẽ lại ở vài
        // đường (đổi brain, đổi trang) - lúc đó chúng biến mất khỏi khung này và để lại đúng
        // cái nhãn trơ ra. Còn nút thì giữ, hết nút thì dọn.
        if (sysHost && !sysHost.querySelector(".navbar-brain, #themeWrap, #themeToggle, #sysBar")) {
          moved = [];
          boSysHost();
        }
      } else if (moved.length) {
        moved.forEach(function (m) {
          if (m.next && m.next.parentElement === m.parent) m.parent.insertBefore(m.el, m.next);
          else m.parent.appendChild(m.el);
        });
        moved = [];
        boSysHost();   // trả nút về desktop rồi thì cái khung rỗng cũng phải đi theo
      } else {
        boSysHost();   // desktop mà vẫn còn khung (dựng hụt, hoặc nút bị vẽ lại mất) -> dọn
      }
    }

    // ---- 3) Placeholder ngắn cho ô nhập trên mobile ----
    var chatInput = document.getElementById("chatInput");
    var longPh = chatInput ? chatInput.getAttribute("placeholder") : "";
    function setPlaceholder() {
      if (chatInput) chatInput.setAttribute("placeholder", mq.matches ? "Nói hoặc gõ cho VMOS…" : longPh);
    }

    // ---- 4) Nút + = hội thoại mới (reset) + focus ô nhập cho phản hồi tức thì ----
    var reset = document.getElementById("resetBtn");
    if (newChatBtn && reset) newChatBtn.addEventListener("click", function () {
      reset.click();
      if (chatInput) { try { chatInput.focus(); } catch (e) {} }
    });

    // ---- 5) Ngăn kéo điều hướng ----
    var toggle = document.getElementById("navToggle");
    var backdrop = document.getElementById("navBackdrop");
    // 0.216.0 upstream: một lần chạm trên iPhone có thể thành HAI cú bấm; cú 2 đóng ngay menu vừa mở.
    var NGAN_DONG = 400, moLuc = 0;
    function openNav() {
      document.body.classList.add("nav-open");
      if (backdrop) backdrop.hidden = false;
      if (toggle) toggle.setAttribute("aria-expanded", "true");
      moLuc = Date.now();
    }
    function closeNav() {
      document.body.classList.remove("nav-open");
      if (backdrop) backdrop.hidden = true;
      if (toggle) toggle.setAttribute("aria-expanded", "false");
    }
    function closeByTap() { if (Date.now() - moLuc >= NGAN_DONG) closeNav(); }
    if (toggle) toggle.addEventListener("click", function () {
      document.body.classList.contains("nav-open") ? closeByTap() : openNav();
    });
    if (backdrop) backdrop.addEventListener("click", closeByTap);
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeNav(); });
    if (railEl) railEl.addEventListener("click", function (e) {
      if (e.target.closest(".rail-item") && mq.matches) closeNav();
    });

    // ---- 6) Bung/thu khoang não (mobile-only) ----
    // Khoang não trên điện thoại chỉ cao hơn 200px một chút. Kể cả sau khi đã siết lề canh
    // khung, thu nhỏ nhãn và làm mỏng dải số liệu, chừng đó vẫn không phải chỗ để NHÌN một
    // đồ thị - đây mới là câu trả lời cho "não bé quá không thấy gì".
    // Bung xong phải gọi refit(): canvas vừa đổi kích thước, mà mức zoom hiện tại là mức
    // canh cho khung CŨ, giữ nguyên là đồ thị vẫn bé y như lúc chưa bung.
    var brainMaxBtn = document.getElementById("brainMaxBtn");
    function refitGraph(delay) {
      setTimeout(function () {
        try {
          var g = window.__javisGraph;
          if (g && typeof g.refit === "function") g.refit(360);
          else if (g && typeof g.resize === "function") g.resize();
        } catch (e) {}
      }, delay || 60);
    }
    function setBrainMax(on) {
      document.body.classList.toggle("brain-max", !!on);
      if (brainMaxBtn) {
        brainMaxBtn.setAttribute("aria-pressed", on ? "true" : "false");
        brainMaxBtn.title = on ? "Thu khoang não về khung nhỏ"
                               : "Bung khoang não ra toàn màn để nhìn rõ đồ thị";
      }
      refitGraph(340);   // đợi hết hoạt ảnh đổi layout rồi mới đo lại
    }
    if (brainMaxBtn) brainMaxBtn.addEventListener("click", function () {
      setBrainMax(!document.body.classList.contains("brain-max"));
    });
    // Về desktop (xoay máy, đổi cửa sổ) thì trạng thái bung không còn nghĩa gì: khoang não
    // vốn đã là cả cột giữa. Bỏ cờ đi kẻo khung chat biến mất trên màn rộng.
    function syncBrainMax() {
      if (!mq.matches && document.body.classList.contains("brain-max")) setBrainMax(false);
    }

    function muteRailNotes(e) {
      if (!railEl || mq.matches) return;
      var btn = e && e.target && e.target.closest && e.target.closest(".rail-grp-lbl, .rail-item");
      if (btn && btn.hasAttribute("title")) btn.removeAttribute("title");
    }

    function placeTopNav() {
      if (!railEl || !headerRoot || !railParent) return;
      if (!mq.matches) {
        if (railEl.parentElement !== headerRoot) headerRoot.appendChild(railEl);
      } else if (railEl.parentElement === headerRoot) {
        if (railNext && railNext.parentElement === railParent) railParent.insertBefore(railEl, railNext);
        else railParent.appendChild(railEl);
      }
    }

    // ---- 7) Bàn phím ảo + chiều cao app (port từ upstream 0.359 / visualViewport) ----
    // Đo vùng nhìn thấy, gắn kb-open; lúc nghỉ ghi --app-h để PWA iPhone không hụt đầu / thừa đáy.
    var vv = window.visualViewport;
    var rootStyle = document.documentElement.style;
    var mocCao = 0, kbHen = 0, vuaGo = false;
    function dangGo() {
      var a = document.activeElement;
      if (!a || a === document.body) return false;
      var tag = (a.tagName || "").toLowerCase();
      if (tag === "textarea" || a.isContentEditable) return true;
      if (tag !== "input") return false;
      return !/^(button|checkbox|radio|range|color|file|submit|reset|image|hidden)$/i.test(a.type || "");
    }
    function syncKeyboard() {
      kbHen = 0;
      if (!vv) return;
      var go = dangGo();
      if (!go || !mocCao) mocCao = Math.max(go ? mocCao : 0, vv.height);
      var mo = mq.matches && go && mocCao - vv.height > 120;
      document.body.classList.toggle("kb-open", mo);
      if (mo) {
        rootStyle.setProperty("--vv-h", Math.round(vv.height) + "px");
        rootStyle.setProperty("--vv-top", Math.max(0, Math.round(vv.offsetTop)) + "px");
        rootStyle.setProperty("--vv-ptop", Math.max(0, Math.round(vv.pageTop)) + "px");
      } else {
        rootStyle.removeProperty("--vv-h");
        rootStyle.removeProperty("--vv-top");
        rootStyle.removeProperty("--vv-ptop");
      }
      if (mq.matches && !go && Math.abs((vv.scale || 1) - 1) < 0.01 && vv.height > 200) {
        rootStyle.setProperty("--app-h", Math.round(vv.height) + "px");
        if (vuaGo && (window.scrollY || document.documentElement.scrollTop)) window.scrollTo(0, 0);
      } else if (!mq.matches) {
        rootStyle.removeProperty("--app-h");
      }
      vuaGo = go;
    }
    function henKeyboard() {
      if (!kbHen) kbHen = (window.requestAnimationFrame || setTimeout)(syncKeyboard);
    }
    if (vv) {
      vv.addEventListener("resize", henKeyboard);
      vv.addEventListener("scroll", henKeyboard);
      document.addEventListener("focusin", henKeyboard);
      document.addEventListener("focusout", function () { henKeyboard(); setTimeout(syncKeyboard, 350); });
      window.addEventListener("orientationchange", function () { mocCao = 0; setTimeout(syncKeyboard, 400); });
    }

    function applyAll() { placeHeader(); placeSystem(); placeTopNav(); setPlaceholder(); syncBrainMax(); syncKeyboard(); }
    if (railEl) railEl.addEventListener("mouseover", muteRailNotes);
    applyAll();

    var onChange = function () { applyAll(); if (!mq.matches) closeNav(); };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else if (mq.addListener) mq.addListener(onChange);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
