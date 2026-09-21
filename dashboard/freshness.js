/* Người gác cổng bản cũ: phát hiện trình duyệt đang chạy code KHÔNG khớp với máy chủ.
 *
 * VÌ SAO CÓ FILE NÀY (vụ 03/09/2026)
 * Chủ repo báo "up file vẫn không chọn được nhiều file" sau khi bản vá đã lên main và đã
 * cập nhật máy chủ. Hoá ra trình duyệt chạy sessions-ui.js CŨ, trong khi dòng chữ ngay
 * cạnh cái ô đó lại là chữ MỚI - vì hai thứ đi hai đường khác nhau tới trình duyệt:
 *   - từ điển i18n: tải kèm `cache: no-cache`, luôn hỏi lại máy chủ  -> LUÔN mới
 *   - file .js/.css: mang `/asset/<phiên bản>/file.js` + đóng dấu cache 1 năm immutable.
 *     Trước đây chỉ `?v=` nên tầng cache bỏ qua query thì giữ meetings.js cũ mãi.
 * Kết quả là một sự cố CÂM: bản vá "không ăn", người dùng tưởng code sai, người sửa không
 * tài nào tái hiện. Chú thích trong main.root() cho thấy repo đã vấp đúng chuyện này một
 * lần trước đó (console.js đứng yên suốt hàng chục bản mà không ai biết).
 *
 * VÌ SAO KHÔNG CHỈ SO SỐ PHIÊN BẢN
 * Ở đúng ca trên, số phiên bản KHỚP mà nội dung thì cũ. Nên file này so chính NỘI DUNG:
 * server nhúng vào trang crc32 của từng file .js/.css, ở đây tải lại đúng URL ấy (lấy từ
 * cache, không tốn mạng) rồi băm và đối chiếu. Lệch nghĩa là thứ đang chạy không phải thứ
 * máy chủ có.
 *
 * ĐIỂM TỰA: index.html được trả kèm `no-store` nên nó LUÔN mới, kể cả khi mọi file JS
 * quanh nó đã cũ. Khối <script id="javis-fresh"> nằm trong đó vì vậy luôn nói thật.
 * Chính file này cũng nạp KHÔNG kèm `?v=` và được đóng dấu `no-cache` (xem middleware
 * _static_cache_headers) - người gác cổng mà cũ theo thì nó gác cái gì.
 */
(function () {
  "use strict";

  var CHU_KY_MS = 5 * 60 * 1000;     // nhịp hỏi lại máy chủ xem đã có bản mới chưa
  var KHOA_DA_TAI = "javis-fresh-reloaded";   // chống vòng lặp tải lại vô tận

  function moc() {
    var el = document.getElementById("javis-fresh");
    if (!el) return null;
    try { return JSON.parse(el.textContent || "{}"); } catch (e) { return null; }
  }

  function assetVer(m) {
    return encodeURIComponent((m && (m.asset_ver || m.version)) || "0");
  }

  /* crc32 khớp từng bit với zlib.crc32 bên Python (server dùng chính hàm đó).
   * Không dùng crypto.subtle: nó chỉ có trong ngữ cảnh bảo mật, mà VMOS rất hay chạy
   * trên http:// theo IP của VPS - dùng nó là người gác cổng chết lặng đúng lúc cần nhất. */
  var BANG = null;
  function bangCrc() {
    if (BANG) return BANG;
    BANG = new Uint32Array(256);
    for (var i = 0; i < 256; i++) {
      var c = i;
      for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      BANG[i] = c >>> 0;
    }
    return BANG;
  }

  function crc32(bytes) {
    var t = bangCrc(), c = 0xFFFFFFFF;
    for (var i = 0; i < bytes.length; i++) c = t[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
    c = (c ^ 0xFFFFFFFF) >>> 0;
    var s = c.toString(16);
    while (s.length < 8) s = "0" + s;
    return s;
  }

  /* Tải một file tĩnh ĐÚNG như trình duyệt đã tải nó lúc dựng trang: KHÔNG ép làm mới, để
   * nó trả về đúng bản đang nằm trong cache (của trình duyệt hay của proxy). Đây mới là
   * thứ cần đo - ép làm mới là đo file trên máy chủ, tức là đo nhầm đầu. */
  function taiNhuTrang(url, epLamMoi) {
    var opt = { credentials: "same-origin" };
    if (epLamMoi) opt.cache = "reload";
    return fetch(url, opt)
      .then(function (r) { return r.ok ? r.arrayBuffer() : null; })
      .catch(function () { return null; });
  }

  /* Trả về danh sách file mà NỘI DUNG đang chạy khác nội dung máy chủ. */
  function doLech(m, epLamMoi) {
    var ds = Object.keys(m.assets || {});
    if (!ds.length) return Promise.resolve([]);
    var ver = assetVer(m);
    return Promise.all(ds.map(function (rel) {
      var url = "/asset/" + ver + "/" + rel;
      // Ép làm mới: thêm ?r= để CDN (Cloudflare) coi là cache key khác.
      if (epLamMoi) url += (url.indexOf("?") >= 0 ? "&" : "?") + "r=" + Date.now();
      return taiNhuTrang(url, epLamMoi).then(function (buf) {
        if (!buf) return null;
        return crc32(new Uint8Array(buf)) === m.assets[rel] ? null : rel;
      });
    })).then(function (kq) { return kq.filter(Boolean); });
  }

  function xoaCacheRoiTaiLai() {
    var viec = [];
    try {
      if (window.caches && caches.keys) {
        viec.push(caches.keys().then(function (ks) {
          return Promise.all(ks.map(function (k) { return caches.delete(k); }));
        }));
      }
    } catch (e) { /* noop */ }
    try {
      if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
        viec.push(navigator.serviceWorker.getRegistrations().then(function (rs) {
          return Promise.all(rs.map(function (r) { return r.unregister(); }));
        }));
      }
    } catch (e2) { /* noop */ }
    try { sessionStorage.removeItem(KHOA_DA_TAI); } catch (e3) { /* noop */ }
    Promise.all(viec).catch(function () { /* noop */ }).then(function () {
      var u = new URL(location.href);
      u.searchParams.set("_fresh", String(Date.now()));
      location.replace(u.toString());
    });
  }

  // ── Dải báo ───────────────────────────────────────────────────────────────────
  function veDai(tieuDe, chiTiet, nhanNut, khiBam) {
    var cu = document.getElementById("javis-fresh-bar");
    if (cu) cu.remove();
    var css = document.createElement("style");
    css.textContent =
      "#javis-fresh-bar{position:fixed;left:50%;transform:translateX(-50%);top:14px;z-index:99999;" +
      "display:flex;align-items:center;gap:12px;max-width:min(92vw,720px);padding:12px 16px;" +
      "border-radius:12px;border:1px solid var(--yellow,#e0a800);background:var(--bg2,#1b1f2a);" +
      "color:var(--text,#e8eaf0);font-size:16px;line-height:1.5;box-shadow:0 10px 30px rgba(0,0,0,.4)}" +
      "#javis-fresh-bar .jf-txt{flex:1 1 auto;min-width:0}" +
      "#javis-fresh-bar .jf-sub{display:block;margin-top:3px;font-size:14px;opacity:.8}" +
      "#javis-fresh-bar button{flex:none;cursor:pointer;border-radius:8px;font-size:15px;padding:7px 13px;" +
      "font-family:inherit;border:1px solid var(--border,#39405180)}" +
      "#javis-fresh-bar .jf-ok{background:var(--yellow,#e0a800);border-color:var(--yellow,#e0a800);" +
      "color:#1a1a1a;font-weight:700}" +
      "#javis-fresh-bar .jf-x{background:transparent;color:var(--text3,#8b93a7)}";
    var bar = document.createElement("div");
    bar.id = "javis-fresh-bar";
    bar.setAttribute("role", "status");
    var txt = document.createElement("div");
    txt.className = "jf-txt";
    txt.textContent = tieuDe;
    if (chiTiet) {
      var sub = document.createElement("span");
      sub.className = "jf-sub";
      sub.textContent = chiTiet;
      txt.appendChild(sub);
    }
    var ok = document.createElement("button");
    ok.className = "jf-ok";
    ok.textContent = nhanNut;
    ok.onclick = khiBam;
    var x = document.createElement("button");
    x.className = "jf-x";
    x.textContent = "Để sau";
    x.onclick = function () { bar.remove(); };
    bar.appendChild(txt); bar.appendChild(ok); bar.appendChild(x);
    document.head.appendChild(css);
    document.body.appendChild(bar);
  }

  /* KHÔNG tự tải lại trang. Người dùng có thể đang gõ dở một câu dài, và mất chữ đang gõ vì
   * một thứ họ không hề bấm là tệ hơn hẳn cái nó chữa. Chỉ hiện dải và để họ bấm. */
  function baoCoBanMoi(verMoi) {
    veDai("VMOS vừa cập nhật lên bản " + verMoi + ".",
          "Tải lại trang để dùng bản mới.", "Tải lại", function () { location.reload(); });
  }

  function baoChayBanCu(ds, daThuTaiLai) {
    var ten = ds.slice(0, 3).join(", ") + (ds.length > 3 ? " và " + (ds.length - 3) + " file nữa" : "");
    if (!daThuTaiLai) {
      veDai("Trình duyệt đang chạy bản cũ của VMOS.",
            "Bấm để tải lại. (" + ten + ")", "Tải lại", function () {
              try { sessionStorage.setItem(KHOA_DA_TAI, "1"); } catch (e) { /* noop */ }
              location.reload();
            });
      return;
    }
    // Tải lại rồi mà vẫn lệch: thường là CDN/Cloudflare giữ file theo URL cũ.
    // Nút dưới xóa Cache Storage + SW rồi mở lại với ?_fresh=… (CDN coi là URL mới).
    veDai("Vẫn đang chạy bản cũ dù đã tải lại.",
          "Ctrl+Shift+R không phá được cache CDN. Bấm nút để xóa cache trang rồi tải lại. "
          + "Vẫn vậy: mở tab ẩn danh, hoặc Cloudflare → Caching → Purge Everything. (" + ten + ")",
          "Xóa cache & tải lại", xoaCacheRoiTaiLai);
  }

  // ── Chạy ──────────────────────────────────────────────────────────────────────
  var m = moc();
  if (!m) return;

  var daThu = false;
  try { daThu = sessionStorage.getItem(KHOA_DA_TAI) === "1"; } catch (e) { /* noop */ }

  function kiemNoiDung() {
    doLech(m, false).then(function (ds) {
      if (!ds.length) {
        try { sessionStorage.removeItem(KHOA_DA_TAI); } catch (e) { /* noop */ }
        return;
      }
      // Có thể chỉ cache local/CDN bẩn: đo lại ép mạng. Khớp → tự xóa cache & tải lại một lần.
      return doLech(m, true).then(function (ds2) {
        if (!ds2.length) {
          console.warn("[javis fresh] cache ban, origin da dung - xoa cache & tai lai");
          xoaCacheRoiTaiLai();
          return;
        }
        console.warn("[javis fresh] đang chạy bản cũ của:", ds2.join(", "));
        baoChayBanCu(ds2, daThu);
      });
    });
  }

  if (document.readyState === "complete") setTimeout(kiemNoiDung, 1200);
  else window.addEventListener("load", function () { setTimeout(kiemNoiDung, 1200); });

  var daBao = false;
  function kiemPhienBan() {
    if (daBao || document.hidden) return;
    fetch("/app-version", { credentials: "same-origin", cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.version || d.version === m.version) return;
        daBao = true;
        baoCoBanMoi(d.version);
      })
      .catch(function () { /* mất mạng một nhịp không phải chuyện để làm phiền người dùng */ });
  }

  setInterval(kiemPhienBan, CHU_KY_MS);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) kiemPhienBan();
  });
})();
