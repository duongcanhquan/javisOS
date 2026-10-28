/* Văn phòng pixel Nhạc trưởng — cảm hứng Pixel Agents (MIT) + sprite Metro City (CC0). */
(function () {
  "use strict";

  var TILE = 16;
  var ZOOM = 2;
  var CHAR_W = 16;
  var CHAR_H = 32;
  var ASSET = "/static/nt-pixel/assets/";
  var WALK_CYCLE = [0, 1, 2, 1];
  var TYPE_CYCLE = [3, 4];
  var DIR = { DOWN: 0, UP: 1, RIGHT: 2, LEFT: 2 };

  var _host = null;
  var _canvas = null;
  var _ctx = null;
  var _labels = null;
  var _raf = 0;
  var _imgs = {};
  var _ready = false;
  var _model = null;
  var _layout = null;
  var _chars = [];
  var _furn = [];
  var _t0 = 0;
  var _last = 0;
  var _click = null;

  function loadImg(src) {
    if (_imgs[src]) return _imgs[src];
    var p = new Promise(function (ok, fail) {
      var im = new Image();
      im.onload = function () { ok(im); };
      im.onerror = function () { fail(new Error(src)); };
      im.src = src;
    });
    _imgs[src] = p;
    return p;
  }

  function preload() {
    var list = [];
    var i;
    for (i = 0; i < 6; i++) list.push(ASSET + "characters/char_" + i + ".png");
    for (i = 0; i < 9; i++) list.push(ASSET + "floors/floor_" + i + ".png");
    [
      "furniture/DESK_FRONT.png", "furniture/CHAIR_FRONT.png", "furniture/CHAIR_BACK.png",
      "furniture/PC_FRONT_ON_1.png", "furniture/PC_FRONT_ON_2.png", "furniture/PC_FRONT_ON_3.png",
      "furniture/LARGE_PLANT.png", "furniture/PLANT.png", "furniture/BOOKSHELF.png",
      "furniture/DOUBLE_BOOKSHELF.png", "furniture/COFFEE.png", "furniture/COFFEE_TABLE.png",
      "furniture/CACTUS.png", "furniture/CLOCK.png", "furniture/BIN.png",
      "furniture/BENCH.png", "furniture/LARGE_PAINTING.png", "furniture/HANGING_PLANT.png",
      "carpets/carpet_0.png",
    ].forEach(function (p) { list.push(ASSET + p); });
    return Promise.all(list.map(function (s) {
      return loadImg(s).catch(function () { return null; });
    })).then(function () { _ready = true; });
  }

  var _imgSync = {};
  function warmSync() {
    return preload().then(function () {
      return Promise.all(Object.keys(_imgs).map(function (k) {
        return _imgs[k].then(function (im) {
          if (im) _imgSync[k] = im;
        }).catch(function () {});
      }));
    });
  }

  function hash(s) {
    var n = 0, i;
    s = String(s || "");
    for (i = 0; i < s.length; i++) n = (n + s.charCodeAt(i) * (i + 3)) % 997;
    return n;
  }

  function floorFor(look) {
    var mau = (look && look.mau) || "la";
    if (mau === "bien") return 3;
    if (mau === "cat") return 5;
    if (mau === "than") return 7;
    return 1;
  }

  function charSheet(slug, ten) {
    return "characters/char_" + (hash(slug || ten) % 6) + ".png";
  }

  /** Dựng layout: mỗi phòng một khu, bàn theo hàng, góc họp giữa. */
  function buildLayout(model) {
    var rooms = (model && model.rooms) || [];
    var pad = 2;
    var deskGap = 4;
    var roomPadX = 2;
    var roomPadY = 2;
    var maxPeople = 1;
    rooms.forEach(function (r) {
      maxPeople = Math.max(maxPeople, (r.people || []).length || 1);
    });
    var desksPerRow = Math.min(4, Math.max(2, maxPeople));
    var roomInnerW = Math.max(10, desksPerRow * deskGap + 4);
    var roomInnerH = 10;
    var cols = pad * 2 + rooms.length * (roomInnerW + 2) - (rooms.length ? 2 : 0);
    if (!rooms.length) cols = 16;
    var rows = pad * 2 + roomInnerH + 2;
    var tiles = [];
    var r, c;
    for (r = 0; r < rows; r++) {
      tiles[r] = [];
      for (c = 0; c < cols; c++) tiles[r][c] = -1;
    }
    var floorId = floorFor(model && model.look);
    var furn = [];
    var seats = [];
    var areas = [];
    var ox = pad;
    rooms.forEach(function (room, ri) {
      var x0 = ox;
      var y0 = pad;
      var w = roomInnerW;
      var h = roomInnerH;
      var x, y;
      for (y = y0; y < y0 + h; y++) {
        for (x = x0; x < x0 + w; x++) {
          if (x >= 0 && y >= 0 && x < cols && y < rows) tiles[y][x] = (floorId + (ri % 2)) % 9;
        }
      }
      // Thảm họp giữa phòng
      var mx = x0 + Math.floor(w / 2) - 1;
      var my = y0 + 3;
      furn.push({ kind: "carpet", x: mx, y: my, z: 0 });
      // Kệ / trang trí tường sau
      furn.push({ kind: "bookshelf", x: x0 + 1, y: y0, z: 1 });
      furn.push({ kind: "painting", x: x0 + Math.floor(w / 2) - 1, y: y0, z: 1 });
      furn.push({ kind: "plant", x: x0 + w - 2, y: y0, z: 1, big: true });
      furn.push({ kind: "clock", x: x0 + w - 3, y: y0, z: 1 });
      furn.push({ kind: "bench", x: mx, y: my + 1, z: 2 });
      furn.push({ kind: "coffee_table", x: mx, y: my + 2, z: 2 });
      furn.push({ kind: "bin", x: x0 + w - 2, y: y0 + h - 2, z: 2 });
      furn.push({ kind: "cactus", x: x0 + 1, y: y0 + h - 2, z: 2 });

      var people = room.people || [];
      people.forEach(function (p, pi) {
        var col = pi % desksPerRow;
        var row = Math.floor(pi / desksPerRow);
        var dx = x0 + 2 + col * deskGap;
        var dy = y0 + h - 4 - row * 3;
        furn.push({ kind: "desk", x: dx, y: dy, z: 3 });
        furn.push({ kind: "chair", x: dx + 1, y: dy + 2, z: 2 });
        furn.push({ kind: "pc", x: dx + 1, y: dy, z: 4 });
        seats.push({
          id: room.slug + "/" + p.slug,
          room: room.slug,
          slug: p.slug,
          ten: p.ten,
          role: p.role,
          sx: dx + 1,
          sy: dy + 1,
          meetX: mx + 1,
          meetY: my + 1,
          sheet: charSheet(p.slug, p.ten),
        });
      });
      areas.push({
        slug: room.slug,
        ten: room.ten,
        x: x0,
        y: y0,
        w: w,
        h: h,
        active: !!room.active,
      });
      ox += w + 2;
    });
    return { cols: cols, rows: rows, tiles: tiles, furn: furn, seats: seats, areas: areas, floorId: floorId };
  }

  function syncChars(model, layout) {
    var byId = {};
    _chars.forEach(function (c) { byId[c.id] = c; });
    var next = [];
    (layout.seats || []).forEach(function (seat) {
      var person = null;
      ((model.rooms || []).filter(function (r) { return r.slug === seat.room; })[0] || { people: [] })
        .people.forEach(function (p) { if (p.slug === seat.slug) person = p; });
      if (!person) return;
      var old = byId[seat.id];
      var state = person.state || "idle";
      var targetX = seat.sx * TILE + TILE / 2;
      var targetY = seat.sy * TILE + TILE;
      if (state === "meet" || state === "hop") {
        targetX = seat.meetX * TILE + TILE / 2;
        targetY = seat.meetY * TILE + TILE;
      }
      if (state === "walk" && person.toSeat) {
        var dest = layout.seats.filter(function (s) {
          return s.room === seat.room && (s.slug === person.toSeat || s.ten === person.toSeat);
        })[0];
        if (dest) {
          targetX = (seat.sx * 0.35 + dest.sx * 0.65) * TILE + TILE / 2;
          targetY = (seat.sy * 0.35 + dest.sy * 0.65) * TILE + TILE;
        }
      }
      var ch = old || {
        id: seat.id,
        x: targetX,
        y: targetY,
        dir: DIR.DOWN,
        frame: 0,
        timer: 0,
        sheet: seat.sheet,
      };
      ch.ten = seat.ten;
      ch.role = seat.role;
      ch.room = seat.room;
      ch.slug = seat.slug;
      ch.state = state;
      ch.bubble = person.bubble || "";
      ch.recv = !!person.recv;
      ch.on = !!person.on;
      ch.targetX = targetX;
      ch.targetY = targetY;
      ch.sheet = seat.sheet;
      ch.seat = seat;
      next.push(ch);
    });
    _chars = next;
  }

  function drawFloor(ctx, layout, zoom) {
    var tiles = layout.tiles;
    var r, c, id, im, path;
    for (r = 0; r < layout.rows; r++) {
      for (c = 0; c < layout.cols; c++) {
        id = tiles[r][c];
        if (id < 0) {
          ctx.fillStyle = "rgba(15,23,42,.35)";
          ctx.fillRect(c * TILE * zoom, r * TILE * zoom, TILE * zoom, TILE * zoom);
          continue;
        }
        path = "floors/floor_" + (id % 9) + ".png";
        im = _imgSync[ASSET + path];
        if (im) {
          ctx.imageSmoothingEnabled = false;
          ctx.drawImage(im, 0, 0, 16, 16, c * TILE * zoom, r * TILE * zoom, TILE * zoom, TILE * zoom);
        } else {
          ctx.fillStyle = "#c4b59a";
          ctx.fillRect(c * TILE * zoom, r * TILE * zoom, TILE * zoom, TILE * zoom);
        }
      }
    }
  }

  function drawFurn(ctx, layout, zoom, t) {
    var list = (layout.furn || []).slice().sort(function (a, b) {
      return (a.y + (a.z || 0) * 0.01) - (b.y + (b.z || 0) * 0.01);
    });
    list.forEach(function (f) {
      var px = f.x * TILE * zoom;
      var py = f.y * TILE * zoom;
      var im, path, fw, fh, ox = 0, oy = 0;
      if (f.kind === "carpet") {
        im = _imgSync[ASSET + "carpets/carpet_0.png"];
        if (im) ctx.drawImage(im, 0, 0, 32, 32, px, py, 2 * TILE * zoom, 2 * TILE * zoom);
        return;
      }
      if (f.kind === "desk") {
        im = _imgSync[ASSET + "furniture/DESK_FRONT.png"];
        if (im) ctx.drawImage(im, 0, 0, 48, 32, px, py - TILE * zoom, 3 * TILE * zoom, 2 * TILE * zoom);
        return;
      }
      if (f.kind === "chair") {
        im = _imgSync[ASSET + "furniture/CHAIR_FRONT.png"];
        if (im) ctx.drawImage(im, 0, 0, 16, 16, px, py, TILE * zoom, TILE * zoom);
        return;
      }
      if (f.kind === "pc") {
        var fi = 1 + (Math.floor(t * 4) % 3);
        im = _imgSync[ASSET + "furniture/PC_FRONT_ON_" + fi + ".png"];
        if (im) {
          var ph = im.height * zoom;
          var pw = im.width * zoom;
          ctx.drawImage(im, 0, 0, im.width, im.height, px, py + TILE * zoom - ph, pw, ph);
        }
        return;
      }
      if (f.kind === "carpet") return;
      var map = {
        bookshelf: ["furniture/DOUBLE_BOOKSHELF.png", 0, 0],
        painting: ["furniture/LARGE_PAINTING.png", 0, 0],
        plant: ["furniture/LARGE_PLANT.png", 0, 0],
        clock: ["furniture/CLOCK.png", 0, 0],
        bench: ["furniture/BENCH.png", 0, 0],
        coffee_table: ["furniture/COFFEE_TABLE.png", 0, 0],
        bin: ["furniture/BIN.png", 0, 0],
        cactus: ["furniture/CACTUS.png", 0, 0],
      };
      var m = map[f.kind];
      if (!m) return;
      im = _imgSync[ASSET + m[0]];
      if (!im) return;
      var dw = im.width * zoom;
      var dh = im.height * zoom;
      ctx.drawImage(im, 0, 0, im.width, im.height, px, py + TILE * zoom - dh, dw, dh);
    });
  }

  function drawChar(ctx, ch, zoom, dt) {
    ch.timer += dt;
    var speed = 48;
    var dx = ch.targetX - ch.x;
    var dy = ch.targetY - ch.y;
    var dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > 1) {
      var step = Math.min(dist, speed * dt);
      ch.x += (dx / dist) * step;
      ch.y += (dy / dist) * step;
      if (Math.abs(dx) > Math.abs(dy)) ch.dir = dx > 0 ? DIR.RIGHT : DIR.LEFT;
      else ch.dir = dy > 0 ? DIR.DOWN : DIR.UP;
      if (ch.state === "idle") ch.state = "walk";
    }

    var cycle = WALK_CYCLE;
    var dur = 0.14;
    var row = ch.dir === DIR.UP ? 1 : (ch.dir === DIR.DOWN ? 0 : 2);
    var flip = ch.dir === DIR.LEFT;
    if (ch.state === "type" || ch.state === "on" || ch.state === "lam") {
      cycle = TYPE_CYCLE;
      dur = 0.22;
      row = 0;
      flip = false;
    } else if (ch.state === "idle" || ch.state === "wait" || ch.state === "cho") {
      cycle = [1];
      dur = 1;
    } else if (ch.state === "meet" || ch.state === "hop") {
      cycle = TYPE_CYCLE;
      dur = 0.25;
    }

    if (ch.timer >= dur) {
      ch.timer -= dur;
      ch.frame = (ch.frame + 1) % cycle.length;
    }
    var frame = cycle[ch.frame % cycle.length];
    var im = _imgSync[ASSET + ch.sheet];
    if (!im) return;
    var sx = frame * CHAR_W;
    var sy = row * CHAR_H;
    var dw = CHAR_W * zoom;
    var dh = CHAR_H * zoom;
    var dxp = Math.round(ch.x * zoom - dw / 2);
    var dyp = Math.round(ch.y * zoom - dh);
    ctx.save();
    if (ch.recv) {
      ctx.strokeStyle = "#f59e0b";
      ctx.setLineDash([3, 2]);
      ctx.strokeRect(dxp - 2, dyp - 2, dw + 4, dh + 4);
      ctx.setLineDash([]);
    }
    if (ch.on) {
      ctx.strokeStyle = "rgba(45,120,90,.7)";
      ctx.strokeRect(dxp - 1, dyp - 1, dw + 2, dh + 2);
    }
    if (flip) {
      ctx.translate(dxp + dw, dyp);
      ctx.scale(-1, 1);
      ctx.drawImage(im, sx, sy, CHAR_W, CHAR_H, 0, 0, dw, dh);
    } else {
      ctx.drawImage(im, sx, sy, CHAR_W, CHAR_H, dxp, dyp, dw, dh);
    }
    ctx.restore();

    if (ch.bubble) {
      var text = String(ch.bubble).slice(0, 28);
      ctx.save();
      ctx.font = "bold " + Math.max(10, 5 * zoom) + "px 'Segoe UI',sans-serif";
      var tw = ctx.measureText(text).width;
      var bx = dxp + dw / 2 - tw / 2 - 6;
      var by = dyp - 18;
      ctx.fillStyle = "#fff";
      ctx.strokeStyle = "rgba(0,0,0,.15)";
      roundRect(ctx, bx, by, tw + 12, 16, 6);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#1e293b";
      ctx.textBaseline = "middle";
      ctx.fillText(text, bx + 6, by + 8);
      ctx.restore();
    }
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawFlow(ctx, model, layout, zoom) {
    var flow = model && model.flow;
    if (!flow || !flow.from || !flow.to) return;
    var a = null, b = null;
    _chars.forEach(function (c) {
      if (c.slug === flow.from || c.ten === flow.from) a = c;
      if (c.slug === flow.to || c.ten === flow.to) b = c;
    });
    if (!a || !b) return;
    var x1 = a.x * zoom, y1 = (a.y - 20) * zoom;
    var x2 = b.x * zoom, y2 = (b.y - 20) * zoom;
    ctx.save();
    ctx.strokeStyle = "#2d7860";
    ctx.fillStyle = "#2d7860";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo((x1 + x2) / 2, Math.min(y1, y2) - 24, x2, y2);
    ctx.stroke();
    var ang = Math.atan2(y2 - ((y1 + y2) / 2 - 12), x2 - (x1 + x2) / 2);
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - 8 * Math.cos(ang - 0.4), y2 - 8 * Math.sin(ang - 0.4));
    ctx.lineTo(x2 - 8 * Math.cos(ang + 0.4), y2 - 8 * Math.sin(ang + 0.4));
    ctx.closePath();
    ctx.fill();
    if (flow.label) {
      ctx.font = "bold 11px 'Segoe UI',sans-serif";
      var lab = flow.label;
      var tw = ctx.measureText(lab).width;
      var lx = (x1 + x2) / 2 - tw / 2 - 6;
      var ly = Math.min(y1, y2) - 36;
      ctx.fillStyle = "#2d7860";
      roundRect(ctx, lx, ly, tw + 12, 16, 8);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.textBaseline = "middle";
      ctx.fillText(lab, lx + 6, ly + 8);
    }
    ctx.restore();
  }

  function drawAreaLabels(ctx, layout, zoom) {
    (layout.areas || []).forEach(function (a) {
      var x = (a.x + a.w / 2) * TILE * zoom;
      var y = (a.y + 0.7) * TILE * zoom;
      ctx.save();
      ctx.font = "bold " + Math.max(11, 4.5 * zoom) + "px 'Segoe UI',sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      var tw = ctx.measureText(a.ten).width;
      ctx.fillStyle = a.active ? "rgba(45,120,90,.92)" : "rgba(30,41,59,.75)";
      roundRect(ctx, x - tw / 2 - 8, y - 10, tw + 16, 20, 8);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.fillText(a.ten, x, y);
      ctx.restore();
    });
  }

  function updateLabels(zoom) {
    if (!_labels) return;
    var html = _chars.map(function (ch) {
      var left = Math.round(ch.x * zoom);
      var top = Math.round(ch.y * zoom + 2);
      return '<div class="nt-px-label' + (ch.on ? " on" : "") + (ch.recv ? " recv" : "") +
        '" data-actor-phong="' + esc(ch.room) + '" data-actor="' + esc(ch.slug) +
        '" style="left:' + left + "px;top:" + top + 'px">' +
        "<b>" + esc(ch.ten) + "</b><small>" + esc(ch.role || "") + "</small></div>";
    }).join("");
    if (_labels.getAttribute("data-k") === String(_chars.length) + html.length && _labels.childNodes.length === _chars.length) {
      // cập nhật vị trí thôi
      var nodes = _labels.querySelectorAll(".nt-px-label");
      _chars.forEach(function (ch, i) {
        var n = nodes[i];
        if (!n) return;
        n.style.left = Math.round(ch.x * zoom) + "px";
        n.style.top = Math.round(ch.y * zoom + 2) + "px";
        n.className = "nt-px-label" + (ch.on ? " on" : "") + (ch.recv ? " recv" : "");
      });
      return;
    }
    _labels.setAttribute("data-k", String(_chars.length) + html.length);
    _labels.innerHTML = html;
    if (_click) {
      _labels.querySelectorAll("[data-actor]").forEach(function (el) {
        el.onclick = function (ev) {
          ev.stopPropagation();
          _click(el.getAttribute("data-actor-phong"), el.getAttribute("data-actor"));
        };
      });
    }
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function frame(now) {
    if (!_canvas || !_ctx || !_layout) { _raf = 0; return; }
    if (!_t0) _t0 = now;
    var dt = Math.min(0.05, (_last ? (now - _last) : 16) / 1000);
    _last = now;
    var zoom = ZOOM;
    var w = _layout.cols * TILE * zoom;
    var h = _layout.rows * TILE * zoom;
    if (_canvas.width !== w || _canvas.height !== h) {
      _canvas.width = w;
      _canvas.height = h;
    }
    var ctx = _ctx;
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, w, h);
    // bầu trời / nền
    var g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, "#dbe7f3");
    g.addColorStop(1, "#b7c9b2");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    drawFloor(ctx, _layout, zoom);
    drawFurn(ctx, _layout, zoom, (now - _t0) / 1000);
    drawAreaLabels(ctx, _layout, zoom);
    // characters z-sort by y
    var sorted = _chars.slice().sort(function (a, b) { return a.y - b.y; });
    sorted.forEach(function (ch) { drawChar(ctx, ch, zoom, dt); });
    drawFlow(ctx, _model, _layout, zoom);
    updateLabels(zoom);
    _raf = requestAnimationFrame(frame);
  }

  function structureKey(model) {
    return ((model && model.rooms) || []).map(function (r) {
      return r.slug + ":" + ((r.people || []).map(function (p) { return p.slug; }).join(","));
    }).join("|") + "~" + ((model && model.look && model.look.mau) || "");
  }

  function mount(host, model, opts) {
    if (!host) return Promise.resolve();
    _host = host;
    _click = opts && opts.onActor;
    _model = model || { rooms: [] };
    host.innerHTML =
      '<div class="nt-pixel-stage">' +
      '<canvas class="nt-pixel-canvas" id="ntPixelCanvas"></canvas>' +
      '<div class="nt-pixel-labels" id="ntPixelLabels"></div>' +
      "</div>" +
      '<p class="nt-pixel-credit">Pixel office · cảm hứng Pixel Agents · sprite Metro City (CC0)</p>';
    _canvas = host.querySelector("#ntPixelCanvas");
    _labels = host.querySelector("#ntPixelLabels");
    _ctx = _canvas.getContext("2d");
    return warmSync().then(function () {
      _layout = buildLayout(_model);
      syncChars(_model, _layout);
      _host.setAttribute("data-struct", structureKey(_model));
      if (_raf) cancelAnimationFrame(_raf);
      _last = 0;
      _raf = requestAnimationFrame(frame);
    });
  }

  function update(model) {
    if (!_host || !_canvas) return mount(_host, model, { onActor: _click });
    _model = model || _model;
    var sk = structureKey(_model);
    if (sk !== _host.getAttribute("data-struct")) {
      _layout = buildLayout(_model);
      _host.setAttribute("data-struct", sk);
    }
    syncChars(_model, _layout);
    if (!_raf) _raf = requestAnimationFrame(frame);
  }

  function destroy() {
    if (_raf) cancelAnimationFrame(_raf);
    _raf = 0;
    _host = _canvas = _ctx = _labels = _layout = null;
    _chars = [];
  }

  window.JavisNtPixel = {
    mount: mount,
    update: update,
    destroy: destroy,
    ready: function () { return _ready; },
  };
})();
