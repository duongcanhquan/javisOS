/* Văn phòng pixel Nhạc trưởng — campus hybrid + zoom phòng.
   Cảm hứng Pixel Agents (MIT) + sprite Metro City (CC0). */
(function () {
  "use strict";

  var TILE = 16;
  var ZOOM_CAMPUS = 2;
  var ZOOM_FOCUS = 2.5;
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
  var _hits = null;
  var _raf = 0;
  var _imgs = {};
  var _ready = false;
  var _model = null;
  var _layout = null;
  var _chars = [];
  var _t0 = 0;
  var _last = 0;
  var _click = null;
  var _onRoom = null;
  var _onCampus = null;

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

  function emptyTiles(cols, rows) {
    var tiles = [];
    var r, c;
    for (r = 0; r < rows; r++) {
      tiles[r] = [];
      for (c = 0; c < cols; c++) tiles[r][c] = -1;
    }
    return tiles;
  }

  function fillRect(tiles, x0, y0, w, h, id, cols, rows) {
    var x, y;
    for (y = y0; y < y0 + h; y++) {
      for (x = x0; x < x0 + w; x++) {
        if (x >= 0 && y >= 0 && x < cols && y < rows) tiles[y][x] = id;
      }
    }
  }

  function roomSize(people) {
    var n = (people || []).length || 1;
    var staff = Math.max(0, n - ((people || []).some(function (p) { return p.boss; }) ? 1 : 0));
    var perSide = Math.max(1, Math.ceil(staff / 2));
    var w = Math.max(14, 10 + (staff > 4 ? 2 : 0) + (staff > 6 ? 2 : 0));
    var h = Math.max(13, 5 + perSide * 3 + 3);
    return { w: w, h: h };
  }

  function seatPlan(people, x0, y0, w, h) {
    var list = (people || []).slice();
    var boss = null;
    var staff = [];
    list.forEach(function (p) {
      if (p.boss && !boss) boss = p;
      else staff.push(p);
    });
    if (!boss && list.length) {
      boss = list[0];
      staff = list.slice(1);
    }
    var mx = x0 + Math.floor(w / 2) - 1;
    var my = y0 + Math.floor(h / 2) - 1;
    var out = [];
    if (boss) out.push({ p: boss, dx: mx, dy: y0 + 1, boss: true });
    var leftX = x0 + 1;
    var rightX = x0 + w - 3;
    var yTop = y0 + 4;
    var yBot = y0 + h - 4;
    var side = [];
    var y;
    for (y = yTop; y <= yBot; y += 3) side.push({ dx: leftX, dy: y });
    for (y = yTop; y <= yBot; y += 3) side.push({ dx: rightX, dy: y });
    for (var x = leftX + 3; x <= rightX - 3; x += 3) {
      if (Math.abs(x - mx) < 2) continue;
      side.push({ dx: x, dy: yBot });
    }
    staff.forEach(function (p, i) {
      var s = side[i] || { dx: leftX + (i % 3) * 3, dy: yBot - Math.floor(i / 3) * 3 };
      out.push({ p: p, dx: s.dx, dy: s.dy, boss: false });
    });
    return { seats: out, mx: mx, my: my };
  }

  function pipeStatus(room, pipe) {
    if (!room) return "idle";
    if (room.active) return "active";
    var hit = (pipe || []).filter(function (p) { return p.slug === room.slug; })[0];
    if (hit && hit.dat) return "dat";
    if (hit && hit.khoa) return "khoa";
    return "idle";
  }

  function doorBadge(room, pipe, d) {
    var hit = (pipe || []).filter(function (p) { return p.slug === room.slug; })[0];
    var st = "";
    if (room.active && d && d.buoc) st = " · " + String(d.buoc);
    else if (hit && hit.dat) st = " · đạt";
    else if (hit && hit.khoa) st = " · khóa";
    return (room.ten || room.slug) + st;
  }

  /** Campus: lobby | phòng L→R + hành lang | boardroom trên. */
  function buildCampusLayout(model) {
    var rooms = (model && model.rooms) || [];
    var pipe = (model && model.pipeline) || [];
    var queue = (model && model.queue) || [];
    var meeting = (model && model.meeting) || {};
    var d = model && model.dangLam;
    var pad = 1;
    var lobbyW = 7;
    var hallW = 3;
    var boardH = 7;
    var roomW = 11;
    var roomH = 11;
    var n = rooms.length;
    var roomsBlock = n > 0
      ? (n * roomW + Math.max(0, n - 1) * hallW)
      : roomW;
    var cols = pad * 2 + lobbyW + 1 + roomsBlock + 1;
    var rows = pad * 2 + boardH + 1 + roomH + 1;
    var tiles = emptyTiles(cols, rows);
    var floorId = floorFor(model && model.look);
    var hallFloor = (floorId + 4) % 9;
    var furn = [];
    var seats = [];
    var areas = [];
    var halls = [];
    var doors = [];
    var boardSeats = [];

    // Lobby
    var lx0 = pad;
    var ly0 = pad + boardH + 1;
    fillRect(tiles, lx0, ly0, lobbyW, roomH, floorId, cols, rows);
    furn.push({ kind: "bookshelf", x: lx0 + 1, y: ly0, z: 1 });
    furn.push({ kind: "desk", x: lx0 + 2, y: ly0 + 3, z: 3 });
    furn.push({ kind: "chair", x: lx0 + 3, y: ly0 + 5, z: 2 });
    furn.push({ kind: "plant", x: lx0 + lobbyW - 2, y: ly0 + 1, z: 1, big: true });
    areas.push({
      slug: "__lobby",
      ten: "Sảnh",
      x: lx0, y: ly0, w: lobbyW, h: roomH,
      kind: "lobby",
      active: false,
      tickets: queue.slice(0, 4),
    });

    // Boardroom spanning above rooms
    var bx0 = pad + lobbyW + 1;
    var bw = Math.max(roomW, cols - bx0 - pad);
    var by0 = pad;
    fillRect(tiles, bx0, by0, bw, boardH, (floorId + 2) % 9, cols, rows);
    var bmx = bx0 + Math.floor(bw / 2) - 1;
    var bmy = by0 + 2;
    furn.push({ kind: "carpet", x: bmx, y: bmy, z: 0 });
    furn.push({ kind: "bench", x: bmx, y: bmy + 1, z: 2 });
    furn.push({ kind: "coffee_table", x: bmx, y: bmy + 2, z: 2 });
    furn.push({ kind: "painting", x: bmx, y: by0, z: 1 });
    furn.push({ kind: "plant", x: bx0 + 1, y: by0, z: 1, big: true });
    furn.push({ kind: "plant", x: bx0 + bw - 2, y: by0, z: 1, big: true });
    areas.push({
      slug: "__board",
      ten: meeting.on ? ("Họp trưởng" + (meeting.round ? " · vòng " + meeting.round : "")) : "Phòng họp trưởng",
      x: bx0, y: by0, w: bw, h: boardH,
      kind: "board",
      active: !!meeting.on,
    });

    var heads = meeting.heads || [];
    heads.forEach(function (h, i) {
      var hx = bx0 + 2 + (i % Math.max(1, Math.floor(bw / 3))) * 3;
      var hy = by0 + 3 + Math.floor(i / Math.max(1, Math.floor(bw / 3)));
      if (hy > by0 + boardH - 2) hy = by0 + boardH - 2;
      boardSeats.push({
        id: "board/" + h.phong + "/" + h.slug,
        room: h.phong,
        slug: h.slug,
        ten: h.ten,
        role: h.role || "Trưởng",
        boss: true,
        board: true,
        sx: hx,
        sy: hy,
        meetX: bmx + 1,
        meetY: bmy + 1,
        sheet: h.sheet || charSheet(h.slug, h.ten),
      });
    });

    var ox = pad + lobbyW + 1;
    var ry0 = pad + boardH + 1;
    rooms.forEach(function (room, ri) {
      if (ri > 0) {
        var hx0 = ox;
        fillRect(tiles, hx0, ry0, hallW, roomH, hallFloor, cols, rows);
        var prev = rooms[ri - 1];
        var stHall = "pending";
        var prevSt = pipeStatus(prev, pipe);
        var curSt = pipeStatus(room, pipe);
        if (prevSt === "dat" || prevSt === "khoa") stHall = prevSt === "dat" ? "dat" : "khoa";
        if (curSt === "active" || prevSt === "active") stHall = "active";
        halls.push({
          x: hx0, y: ry0, w: hallW, h: roomH,
          status: stHall,
          from: prev.slug,
          to: room.slug,
        });
        ox += hallW;
      }
      var x0 = ox;
      var y0 = ry0;
      var w = roomW;
      var h = roomH;
      fillRect(tiles, x0, y0, w, h, (floorId + (ri % 2)) % 9, cols, rows);
      var plan = seatPlan(room.people || [], x0, y0, w, h);
      var mx = plan.mx;
      var my = plan.my;
      furn.push({ kind: "carpet", x: mx, y: my, z: 0 });
      furn.push({ kind: "bookshelf", x: x0 + 1, y: y0, z: 1 });
      furn.push({ kind: "painting", x: mx, y: y0, z: 1 });
      furn.push({ kind: "plant", x: x0 + w - 2, y: y0, z: 1, big: true });
      furn.push({ kind: "clock", x: x0 + w - 3, y: y0, z: 1 });
      furn.push({ kind: "bin", x: x0 + w - 2, y: y0 + h - 2, z: 2 });
      furn.push({ kind: "cactus", x: x0 + 1, y: y0 + h - 2, z: 2 });

      plan.seats.forEach(function (s) {
        var p = s.p;
        furn.push({ kind: "desk", x: s.dx, y: s.dy, z: 3 });
        furn.push({ kind: "chair", x: s.dx + 1, y: s.dy + 2, z: 2 });
        furn.push({ kind: "pc", x: s.dx + 1, y: s.dy, z: 4 });
        seats.push({
          id: room.slug + "/" + p.slug,
          room: room.slug,
          slug: p.slug,
          ten: p.ten,
          role: p.role,
          boss: !!s.boss,
          sx: s.dx + 1,
          sy: s.dy + 1,
          meetX: mx + 1,
          meetY: my + 1,
          sheet: p.sheet || charSheet(p.slug, p.ten),
        });
      });

      var st = pipeStatus(room, pipe);
      doors.push({
        slug: room.slug,
        x: x0 + Math.floor(w / 2),
        y: y0,
        badge: doorBadge(room, pipe, d),
        status: st,
        idx: ri + 1,
      });
      areas.push({
        slug: room.slug,
        ten: (ri + 1) + ". " + (room.ten || room.slug),
        x: x0, y: y0, w: w, h: h,
        kind: "room",
        active: !!room.active,
        status: st,
        badge: doorBadge(room, pipe, d),
      });
      ox += w;
    });

    return {
      mode: "campus",
      zoom: ZOOM_CAMPUS,
      cols: cols,
      rows: rows,
      tiles: tiles,
      furn: furn,
      seats: seats,
      boardSeats: boardSeats,
      areas: areas,
      halls: halls,
      doors: doors,
      floorId: floorId,
      meetingOn: !!meeting.on,
    };
  }

  /** Focus một phòng — ghế chữ U đầy đủ. */
  function buildFocusLayout(model, focus) {
    var rooms = ((model && model.rooms) || []).filter(function (r) { return r.slug === focus; });
    if (!rooms.length) return buildCampusLayout(model);
    var room = rooms[0];
    var pipe = (model && model.pipeline) || [];
    var d = model && model.dangLam;
    var pad = 2;
    var sz = roomSize(room.people);
    var w = Math.max(sz.w, 16);
    var h = Math.max(sz.h, 14);
    var cols = pad * 2 + w;
    var rows = pad * 2 + h + 1;
    var tiles = emptyTiles(cols, rows);
    var floorId = floorFor(model && model.look);
    var furn = [];
    var seats = [];
    var x0 = pad;
    var y0 = pad + 1;
    fillRect(tiles, x0, y0, w, h, floorId, cols, rows);
    var plan = seatPlan(room.people || [], x0, y0, w, h);
    var mx = plan.mx;
    var my = plan.my;
    furn.push({ kind: "carpet", x: mx, y: my, z: 0 });
    furn.push({ kind: "bookshelf", x: x0 + 1, y: y0, z: 1 });
    furn.push({ kind: "painting", x: mx, y: y0, z: 1 });
    furn.push({ kind: "plant", x: x0 + w - 2, y: y0, z: 1, big: true });
    furn.push({ kind: "clock", x: x0 + w - 3, y: y0, z: 1 });
    furn.push({ kind: "bench", x: mx, y: my + 1, z: 2 });
    furn.push({ kind: "coffee_table", x: mx, y: my + 2, z: 2 });
    furn.push({ kind: "bin", x: x0 + w - 2, y: y0 + h - 2, z: 2 });
    furn.push({ kind: "cactus", x: x0 + 1, y: y0 + h - 2, z: 2 });
    if (plan.seats.some(function (s) { return s.boss; })) {
      furn.push({ kind: "plant", x: mx - 2, y: y0 + 1, z: 2 });
      furn.push({ kind: "plant", x: mx + 3, y: y0 + 1, z: 2 });
    }
    plan.seats.forEach(function (s) {
      var p = s.p;
      furn.push({ kind: "desk", x: s.dx, y: s.dy, z: 3 });
      furn.push({ kind: "chair", x: s.dx + 1, y: s.dy + 2, z: 2 });
      furn.push({ kind: "pc", x: s.dx + 1, y: s.dy, z: 4 });
      seats.push({
        id: room.slug + "/" + p.slug,
        room: room.slug,
        slug: p.slug,
        ten: p.ten,
        role: p.role,
        boss: !!s.boss,
        sx: s.dx + 1,
        sy: s.dy + 1,
        meetX: mx + 1,
        meetY: my + 1,
        sheet: p.sheet || charSheet(p.slug, p.ten),
      });
    });
    var st = pipeStatus(room, pipe);
    var hit = pipe.filter(function (p) { return p.slug === room.slug; })[0] || {};
    return {
      mode: "room",
      zoom: ZOOM_FOCUS,
      focus: focus,
      cols: cols,
      rows: rows,
      tiles: tiles,
      furn: furn,
      seats: seats,
      boardSeats: [],
      areas: [{
        slug: room.slug,
        ten: room.ten || room.slug,
        x: x0, y: y0, w: w, h: h,
        kind: "room",
        active: !!room.active,
        status: st,
        badge: doorBadge(room, pipe, d),
        meta: "ban " + (hit.soBan || 0) + " · file " + (hit.soHang || 0) +
          (hit.khoa ? " · khóa" : "") + (hit.dat ? " · đạt" : ""),
      }],
      halls: [],
      doors: [],
      floorId: floorId,
      meetingOn: !!(model.meeting && model.meeting.on),
    };
  }

  function buildLayout(model) {
    var view = (model && model.view) || { mode: "campus", focus: null };
    if (view.mode === "room" && view.focus) return buildFocusLayout(model, view.focus);
    return buildCampusLayout(model);
  }

  function findPerson(model, roomSlug, slug) {
    var room = ((model.rooms || []).filter(function (r) { return r.slug === roomSlug; })[0]);
    if (!room) return null;
    var hit = null;
    (room.people || []).forEach(function (p) { if (p.slug === slug) hit = p; });
    return hit;
  }

  function headInMeeting(model, slug, room) {
    var m = model && model.meeting;
    if (!m || !m.on) return false;
    return (m.heads || []).some(function (h) {
      return h.slug === slug && (!h.phong || h.phong === room);
    });
  }

  function syncChars(model, layout) {
    var byId = {};
    _chars.forEach(function (c) { byId[c.id] = c; });
    var next = [];
    var meeting = model && model.meeting;
    var useBoard = layout.mode === "campus" && meeting && meeting.on;

    (layout.seats || []).forEach(function (seat) {
      var person = findPerson(model, seat.room, seat.slug);
      if (!person) return;
      var boardSeat = null;
      if (useBoard && person.boss && headInMeeting(model, seat.slug, seat.room)) {
        boardSeat = (layout.boardSeats || []).filter(function (b) {
          return b.slug === seat.slug && b.room === seat.room;
        })[0] || (layout.boardSeats || []).filter(function (b) {
          return b.slug === seat.slug;
        })[0];
      }
      var activeSeat = boardSeat || seat;
      var old = byId[seat.id];
      var state = person.state || "idle";
      var targetX = activeSeat.sx * TILE + TILE / 2;
      var targetY = activeSeat.sy * TILE + TILE;
      if (!boardSeat && (state === "meet" || state === "hop")) {
        targetX = seat.meetX * TILE + TILE / 2;
        targetY = seat.meetY * TILE + TILE;
      }
      if (state === "walk" && person.toSeat) {
        var dest = layout.seats.filter(function (s) {
          return s.room === seat.room && (s.slug === person.toSeat || s.ten === person.toSeat ||
            (person.toSeat && String(person.toSeat).indexOf(s.ten) === 0));
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
      ch.boss = !!(seat.boss || person.boss);
      ch.room = seat.room;
      ch.slug = seat.slug;
      ch.state = boardSeat ? "meet" : state;
      ch.bubble = person.bubble || "";
      ch.recv = !!person.recv;
      ch.on = !!person.on;
      ch.sel = !!person.sel;
      ch.targetX = targetX;
      ch.targetY = targetY;
      ch.sheet = activeSeat.sheet || seat.sheet;
      ch.seat = activeSeat;
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
      var im;
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
      var map = {
        bookshelf: "furniture/DOUBLE_BOOKSHELF.png",
        painting: "furniture/LARGE_PAINTING.png",
        plant: "furniture/LARGE_PLANT.png",
        clock: "furniture/CLOCK.png",
        bench: "furniture/BENCH.png",
        coffee_table: "furniture/COFFEE_TABLE.png",
        bin: "furniture/BIN.png",
        cactus: "furniture/CACTUS.png",
      };
      var path = map[f.kind];
      if (!path) return;
      im = _imgSync[ASSET + path];
      if (!im) return;
      var dw = im.width * zoom;
      var dh = im.height * zoom;
      ctx.drawImage(im, 0, 0, im.width, im.height, px, py + TILE * zoom - dh, dw, dh);
    });
  }

  function hallColor(status) {
    if (status === "active") return "rgba(45,120,90,.85)";
    if (status === "dat") return "rgba(34,140,90,.75)";
    if (status === "khoa") return "rgba(59,90,140,.7)";
    return "rgba(100,116,139,.35)";
  }

  function liveHallStatus(h, model) {
    var pipe = (model && model.pipeline) || [];
    var prev = pipe.filter(function (p) { return p.slug === h.from; })[0];
    var cur = pipe.filter(function (p) { return p.slug === h.to; })[0];
    if ((cur && cur.active) || (prev && prev.active)) return "active";
    if (prev && prev.dat) return "dat";
    if (prev && prev.khoa) return "khoa";
    return h.status || "pending";
  }

  function drawHalls(ctx, layout, zoom, t) {
    (layout.halls || []).forEach(function (h) {
      var status = liveHallStatus(h, _model);
      var x = (h.x + h.w / 2) * TILE * zoom;
      var y = (h.y + h.h / 2) * TILE * zoom;
      var pulse = status === "active" ? (0.65 + 0.35 * Math.sin(t * 4)) : 1;
      ctx.save();
      ctx.globalAlpha = pulse;
      ctx.fillStyle = hallColor(status);
      ctx.beginPath();
      ctx.moveTo(x - 10, y - 8);
      ctx.lineTo(x + 6, y);
      ctx.lineTo(x - 10, y + 8);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    });
  }

  function drawLobbyTickets(ctx, layout, zoom) {
    var lobby = (layout.areas || []).filter(function (a) { return a.kind === "lobby"; })[0];
    if (!lobby) return;
    var tickets = ((_model && _model.queue) || lobby.tickets || []).slice(0, 4);
    ctx.save();
    ctx.font = "bold " + Math.max(9, 4 * zoom) + "px 'Segoe UI',sans-serif";
    if (!tickets.length) {
      ctx.fillStyle = "rgba(51,65,85,.55)";
      ctx.fillText("Hàng đợi trống", (lobby.x + 0.5) * TILE * zoom, (lobby.y + 7) * TILE * zoom);
      ctx.restore();
      return;
    }
    tickets.forEach(function (tk, i) {
      var title = String(tk.tieu_de || tk.id || "việc").slice(0, 16);
      var x = (lobby.x + 0.5) * TILE * zoom;
      var y = (lobby.y + 6.5 + i * 1.1) * TILE * zoom;
      var tw = ctx.measureText(title).width;
      ctx.fillStyle = tk.trang_thai === "dang_chay" ? "rgba(45,120,90,.9)" :
        (tk.trang_thai === "cho_duyet" ? "rgba(217,119,6,.9)" : "rgba(51,65,85,.85)");
      roundRect(ctx, x, y, tw + 10, 14, 4);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.textBaseline = "middle";
      ctx.fillText(title, x + 5, y + 7);
    });
    ctx.restore();
  }

  function drawChar(ctx, ch, zoom, dt) {
    ch.timer += dt;
    var speed = 56;
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

  function matchChar(flowKey) {
    if (!flowKey) return null;
    var k = String(flowKey).trim();
    var hit = null;
    _chars.forEach(function (c) {
      if (c.slug === k || c.ten === k) hit = c;
      else if (c.ten && k.indexOf(c.ten) === 0) hit = c;
      else if (c.slug && k.indexOf(c.slug) >= 0) hit = c;
    });
    return hit;
  }

  function drawFlow(ctx, model, layout, zoom) {
    var flow = model && model.flow;
    if (!flow || !flow.from || !flow.to) return;
    var a = matchChar(flow.from);
    var b = matchChar(flow.to);
    if (!a || !b) return;
    arrowBetween(ctx, a.x * zoom, (a.y - 20) * zoom, b.x * zoom, (b.y - 20) * zoom, "#2d7860", flow.label, zoom);
  }

  function areaCenter(layout, slug) {
    var a = (layout.areas || []).filter(function (x) { return x.slug === slug; })[0];
    if (!a) return null;
    return {
      x: (a.x + a.w / 2) * TILE,
      y: (a.y + a.h / 2) * TILE,
    };
  }

  function drawCrossFlow(ctx, model, layout, zoom) {
    var cf = model && model.crossFlow;
    if (!cf) return;
    var col = "#2563eb";
    if (cf.kind === "hop" || cf.kind === "chia" || cf.kind === "dap") col = "#7c3aed";
    if (cf.kind === "sua") col = "#c2410c";
    if (cf.kind === "pipeline") col = "#2d7860";
    var a = null;
    var b = null;
    var toBoard = cf.kind === "hop" || cf.kind === "chia" || cf.kind === "dap";
    if (cf.fromRoom) a = areaCenter(layout, cf.fromRoom);
    if (toBoard) b = areaCenter(layout, "__board");
    else if (cf.toRoom) b = areaCenter(layout, cf.toRoom);
    if (!a && cf.from) {
      var ca = matchChar(cf.from);
      if (ca) a = { x: ca.x, y: ca.y - 20 };
    }
    if (!b && cf.to) {
      var cb = matchChar(cf.to);
      if (cb) b = { x: cb.x, y: cb.y - 20 };
    }
    if (!a || !b) return;
    arrowBetween(ctx, a.x * zoom, a.y * zoom, b.x * zoom, b.y * zoom, col, cf.label, zoom);
  }

  function arrowBetween(ctx, x1, y1, x2, y2, color, label, zoom) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo((x1 + x2) / 2, Math.min(y1, y2) - 28, x2, y2);
    ctx.stroke();
    var ang = Math.atan2(y2 - ((y1 + y2) / 2 - 14), x2 - (x1 + x2) / 2);
    ctx.beginPath();
    ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - 8 * Math.cos(ang - 0.4), y2 - 8 * Math.sin(ang - 0.4));
    ctx.lineTo(x2 - 8 * Math.cos(ang + 0.4), y2 - 8 * Math.sin(ang + 0.4));
    ctx.closePath();
    ctx.fill();
    if (label) {
      ctx.font = "bold " + Math.max(10, 5 * (zoom || 2)) + "px 'Segoe UI',sans-serif";
      var tw = ctx.measureText(label).width;
      var lx = (x1 + x2) / 2 - tw / 2 - 6;
      var ly = Math.min(y1, y2) - 40;
      roundRect(ctx, lx, ly, tw + 12, 16, 8);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.textBaseline = "middle";
      ctx.fillText(label, lx + 6, ly + 8);
    }
    ctx.restore();
  }

  function drawMeetingRing(ctx, layout, zoom, t) {
    if (!layout.meetingOn) return;
    var board = (layout.areas || []).filter(function (a) { return a.kind === "board"; })[0];
    if (!board) return;
    var cx = (board.x + board.w / 2) * TILE * zoom;
    var cy = (board.y + board.h / 2) * TILE * zoom;
    var r = Math.min(board.w, board.h) * TILE * zoom * 0.35;
    ctx.save();
    ctx.strokeStyle = "rgba(124,58,237," + (0.45 + 0.25 * Math.sin(t * 3)) + ")";
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();
  }

  function liveRoomPipe(slug) {
    return (((_model && _model.pipeline) || []).filter(function (p) { return p.slug === slug; })[0]) || null;
  }

  function drawAreaLabels(ctx, layout, zoom) {
    var meetingOn = (_model && _model.meeting) ? !!_model.meeting.on : !!layout.meetingOn;
    var d = _model && _model.dangLam;
    (layout.areas || []).forEach(function (a) {
      var x = (a.x + a.w / 2) * TILE * zoom;
      var y = (a.y + 0.55) * TILE * zoom;
      var hit = a.kind === "room" ? liveRoomPipe(a.slug) : null;
      var status = a.status || "idle";
      var label = a.ten;
      if (a.kind === "room") {
        if (hit && hit.active) status = "active";
        else if (hit && hit.dat) status = "dat";
        else if (hit && hit.khoa) status = "khoa";
        label = a.ten;
        if (hit && hit.active && d && d.buoc) label = a.ten + " · " + d.buoc;
        else if (hit && hit.dat) label = a.ten + " · đạt";
        else if (hit && hit.khoa) label = a.ten + " · khóa";
      }
      if (a.kind === "board") {
        label = meetingOn
          ? ("Họp trưởng" + (_model.meeting && _model.meeting.round ? " · vòng " + _model.meeting.round : ""))
          : "Phòng họp trưởng";
      }
      ctx.save();
      ctx.font = "bold " + Math.max(10, 4.2 * zoom) + "px 'Segoe UI',sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      var tw = ctx.measureText(label).width;
      var activeBoard = a.kind === "board" && meetingOn;
      var bg = (a.active || status === "active" || activeBoard)
        ? "rgba(45,120,90,.92)"
        : (status === "dat" ? "rgba(34,140,90,.85)"
          : (status === "khoa" ? "rgba(59,90,140,.85)" : "rgba(30,41,59,.78)"));
      if (a.kind === "lobby") bg = "rgba(51,65,85,.88)";
      roundRect(ctx, x - tw / 2 - 8, y - 10, tw + 16, 20, 8);
      ctx.fillStyle = bg;
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.fillText(label, x, y);
      if (a.meta && layout.mode === "room") {
        var meta = a.meta;
        if (hit) {
          meta = "ban " + (hit.soBan || 0) + " · file " + (hit.soHang || 0) +
            (hit.khoa ? " · khóa" : "") + (hit.dat ? " · đạt" : "");
        }
        ctx.font = Math.max(9, 3.5 * zoom) + "px 'Segoe UI',sans-serif";
        ctx.fillStyle = "rgba(30,41,59,.75)";
        ctx.fillText(meta, x, y + 16);
      }
      ctx.restore();
    });
  }

  function labelClass(ch) {
    return "nt-px-label" +
      (ch.on ? " on" : "") +
      (ch.recv ? " recv" : "") +
      (ch.sel ? " sel" : "") +
      (ch.boss ? " boss" : "");
  }

  function updateLabels(zoom) {
    if (!_labels) return;
    var compact = _layout && _layout.mode === "campus";
    var html = _chars.map(function (ch) {
      var left = Math.round(ch.x * zoom);
      var top = Math.round(ch.y * zoom + 2);
      return '<div class="' + labelClass(ch) + (compact ? " compact" : "") +
        '" data-actor-phong="' + esc(ch.room) + '" data-actor="' + esc(ch.slug) +
        '" style="left:' + left + "px;top:" + top + 'px">' +
        (ch.boss ? '<span class="nt-px-star" aria-hidden="true">★</span>' : "") +
        "<b>" + esc(ch.ten) + "</b>" +
        (compact ? "" : "<small>" + esc(ch.role || "") + "</small>") + "</div>";
    }).join("");
    if (_labels.getAttribute("data-k") === String(_chars.length) + html.length && _labels.childNodes.length === _chars.length) {
      var nodes = _labels.querySelectorAll(".nt-px-label");
      _chars.forEach(function (ch, i) {
        var n = nodes[i];
        if (!n) return;
        n.style.left = Math.round(ch.x * zoom) + "px";
        n.style.top = Math.round(ch.y * zoom + 2) + "px";
        n.className = labelClass(ch) + (compact ? " compact" : "");
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

  function roomAt(tileX, tileY) {
    if (!_layout) return null;
    var hit = null;
    (_layout.areas || []).forEach(function (a) {
      if (a.kind !== "room") return;
      if (tileX >= a.x && tileX < a.x + a.w && tileY >= a.y && tileY < a.y + a.h) hit = a.slug;
    });
    return hit;
  }

  function bindCanvasZoom() {
    if (!_canvas) return;
    _canvas.ondblclick = function (ev) {
      if (!_layout || !_onRoom) return;
      if (_layout.mode === "room") return;
      var zoom = zoomOf(_layout);
      var rect = _canvas.getBoundingClientRect();
      var scaleX = _canvas.width / Math.max(1, rect.width);
      var scaleY = _canvas.height / Math.max(1, rect.height);
      var px = (ev.clientX - rect.left) * scaleX;
      var py = (ev.clientY - rect.top) * scaleY;
      var tx = px / (TILE * zoom);
      var ty = py / (TILE * zoom);
      var slug = roomAt(tx, ty);
      if (slug) {
        ev.preventDefault();
        ev.stopPropagation();
        _onRoom(slug);
      }
    };
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function zoomOf(layout) {
    return (layout && layout.zoom) || ZOOM_CAMPUS;
  }

  function frame(now) {
    if (!_canvas || !_ctx || !_layout) { _raf = 0; return; }
    if (!_t0) _t0 = now;
    var dt = Math.min(0.05, (_last ? (now - _last) : 16) / 1000);
    _last = now;
    var zoom = zoomOf(_layout);
    var w = _layout.cols * TILE * zoom;
    var h = _layout.rows * TILE * zoom;
    if (_canvas.width !== w || _canvas.height !== h) {
      _canvas.width = w;
      _canvas.height = h;
    }
    var ctx = _ctx;
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, w, h);
    var g = ctx.createLinearGradient(0, 0, 0, h);
    g.addColorStop(0, "#dbe7f3");
    g.addColorStop(1, "#b7c9b2");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);

    var t = (now - _t0) / 1000;
    drawFloor(ctx, _layout, zoom);
    drawFurn(ctx, _layout, zoom, t);
    drawHalls(ctx, _layout, zoom, t);
    drawLobbyTickets(ctx, _layout, zoom);
    drawAreaLabels(ctx, _layout, zoom);
    drawMeetingRing(ctx, _layout, zoom, t);
    var sorted = _chars.slice().sort(function (a, b) { return a.y - b.y; });
    sorted.forEach(function (ch) { drawChar(ctx, ch, zoom, dt); });
    drawFlow(ctx, _model, _layout, zoom);
    drawCrossFlow(ctx, _model, _layout, zoom);
    updateLabels(zoom);
    _raf = requestAnimationFrame(frame);
  }

  function structureKey(model) {
    var view = (model && model.view) || {};
    // Không nhồi khoa/dat vào key — tránh remount giật khi pipeline đổi trạng thái.
    var meet = (model && model.meeting && model.meeting.on) ? ("m" + ((model.meeting.heads || []).length)) : "";
    var pipeSlugs = ((model && model.pipeline) || []).map(function (p) { return p.slug; }).join(",");
    return ((model && model.rooms) || []).map(function (r) {
      return r.slug + ":" + ((r.people || []).map(function (p) { return p.slug + (p.sheet || ""); }).join(","));
    }).join("|") + "~" + ((model && model.look && model.look.mau) || "") +
      "~" + (view.mode || "campus") + ":" + (view.focus || "") + "~" + pipeSlugs + "~" + meet;
  }

  function bindChrome() {
    if (!_host) return;
    var btn = _host.querySelector("#ntPxCampus");
    if (btn) btn.onclick = function (ev) {
      ev.stopPropagation();
      if (_onCampus) _onCampus();
    };
  }

  function mount(host, model, opts) {
    if (!host) return Promise.resolve();
    _host = host;
    _click = opts && opts.onActor;
    _onRoom = opts && opts.onRoom;
    _onCampus = opts && opts.onCampus;
    _model = model || { rooms: [] };
    var view = (_model.view && _model.view.mode) || "campus";
    host.innerHTML =
      '<div class="nt-pixel-toolbar">' +
      (view === "room"
        ? '<button type="button" class="nt-btn ghost" id="ntPxCampus">Toàn cảnh</button>' +
          '<span class="nt-px-focus-hint">Đang phóng phòng · Esc / Toàn cảnh để quay lại</span>'
        : '<span class="nt-px-legend">Double-click phòng để phóng · sảnh = hàng đợi · trên = họp trưởng</span>') +
      ((_model.meeting && _model.meeting.on && view === "room")
        ? '<button type="button" class="nt-btn ghost" id="ntPxCampus2">Đang họp liên phòng — về toàn cảnh</button>'
        : "") +
      "</div>" +
      '<div class="nt-pixel-stage">' +
      '<canvas class="nt-pixel-canvas" id="ntPixelCanvas" title="Double-click phòng để phóng"></canvas>' +
      '<div class="nt-pixel-labels" id="ntPixelLabels"></div>' +
      "</div>" +
      '<p class="nt-pixel-credit">Pixel campus · Pixel Agents / Metro City (CC0)</p>';
    var c2 = host.querySelector("#ntPxCampus2");
    if (c2) c2.onclick = function (ev) {
      ev.stopPropagation();
      if (_onCampus) _onCampus();
    };
    bindChrome();
    _canvas = host.querySelector("#ntPixelCanvas");
    _labels = host.querySelector("#ntPixelLabels");
    _hits = null;
    _ctx = _canvas.getContext("2d");
    bindCanvasZoom();
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
    if (!_host || !_canvas) return mount(_host, model, { onActor: _click, onRoom: _onRoom, onCampus: _onCampus });
    var prevMode = (_model && _model.view && _model.view.mode) || "campus";
    _model = model || _model;
    var nextMode = (_model.view && _model.view.mode) || "campus";
    var sk = structureKey(_model);
    if (sk !== _host.getAttribute("data-struct") || prevMode !== nextMode) {
      return mount(_host, _model, { onActor: _click, onRoom: _onRoom, onCampus: _onCampus });
    }
    syncChars(_model, _layout);
    if (!_raf) _raf = requestAnimationFrame(frame);
  }

  function destroy() {
    if (_raf) cancelAnimationFrame(_raf);
    _raf = 0;
    _host = _canvas = _ctx = _labels = _hits = _layout = null;
    _chars = [];
  }

  window.JavisNtPixel = {
    mount: mount,
    update: update,
    destroy: destroy,
    ready: function () { return _ready; },
  };
})();
