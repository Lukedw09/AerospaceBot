/* Globe: graticule, spin axis, burn holds, orbit morphs, dotted far-side arcs. */
var Lab = Lab || {};

Lab.Globe = {
  ready: false,
  playing: true,
  clock: 0,
  token: "",
  init: function (host) {
    this.host = host;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xf4f7fb);
    this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 1e9);
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    host.appendChild(this.renderer.domElement);
    this.group = new THREE.Group();
    this.group.rotation.x = -Math.PI / 2;
    this.scene.add(this.group);
    this.staticGroup = new THREE.Group();
    this.orbitGroup = new THREE.Group();
    this.group.add(this.staticGroup);
    this.group.add(this.orbitGroup);
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.85));
    var sun = new THREE.DirectionalLight(0xffffff, 0.55);
    sun.position.set(1, 0.6, 0.8);
    this.scene.add(sun);
    this.elev = 0.62;
    this.azim = -0.85;
    this.radius = 7.2;
    this._bind();
    this.ready = true;
    var self = this;
    var last = performance.now();
    function frame(now) {
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      if (self.playing && self.sequence && self.sequence.length) self.clock += dt;
      self._frame();
      self._resize();
      self.renderer.render(self.scene, self.camera);
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  },
  _bind: function () {
    var self = this;
    var dragging = false;
    var lastX = 0;
    var lastY = 0;
    var el = this.renderer.domElement;
    el.addEventListener("pointerdown", function (event) {
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
    });
    window.addEventListener("pointerup", function () { dragging = false; });
    window.addEventListener("pointermove", function (event) {
      if (!dragging) return;
      self.azim -= (event.clientX - lastX) * 0.008;
      self.elev = Math.max(-1.2, Math.min(1.2, self.elev + (event.clientY - lastY) * 0.008));
      lastX = event.clientX;
      lastY = event.clientY;
      self._aim();
    });
    el.addEventListener("wheel", function (event) {
      self.radius = Math.max(0.04, Math.min(40, self.radius * (event.deltaY > 0 ? 1.08 : 0.92)));
      self._aim();
      event.preventDefault();
    }, { passive: false });
  },
  _resize: function () {
    var w = this.host.clientWidth || 640;
    var h = this.host.clientHeight || 420;
    if (this._w === w && this._h === h) return;
    this._w = w;
    this._h = h;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / Math.max(h, 1);
    this.camera.updateProjectionMatrix();
    this._aim();
  },
  _aim: function () {
    var ce = Math.cos(this.elev);
    var span = this.spanKm || 20000;
    var planet = this.planetKm || 6374;
    var dist = Math.max(planet * 3.3, this.radius * span * 0.62);
    this.camera.position.set(
      dist * ce * Math.cos(this.azim),
      dist * Math.sin(this.elev),
      dist * ce * Math.sin(this.azim)
    );
    this.camera.lookAt(0, 0, 0);
  },
  _cachedMap: function (map) {
    var key;
    if (!map) return false;
    if (this._dots) {
      for (key in this._dots) {
        if (this._dots[key] === map) return true;
      }
    }
    if (this._labelTex) {
      for (key in this._labelTex) {
        if (this._labelTex[key] === map) return true;
      }
    }
    if (this._marks) {
      for (key in this._marks) {
        if (this._marks[key] === map) return true;
      }
    }
    return false;
  },
  _clear: function (group) {
    var self = this;
    function dispose(obj) {
      var mats;
      var n;
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        for (n = 0; n < mats.length; n += 1) {
          if (mats[n].map && !self._cachedMap(mats[n].map)) mats[n].map.dispose();
          mats[n].dispose();
        }
      }
      if (obj.children) obj.children.slice().forEach(dispose);
    }
    while (group.children.length) {
      var child = group.children[0];
      group.remove(child);
      dispose(child);
    }
  },
  _km: function (p) {
    return new THREE.Vector3(p[0] / 1000.0, p[1] / 1000.0, p[2] / 1000.0);
  },
  _outward: function () {
    var local = this.group.worldToLocal(this.camera.position.clone());
    if (local.lengthSq() < 1e-9) return [0, 0, 1];
    local.normalize();
    return [local.x, local.y, local.z];
  },
  _behind: function (point, outward, radius) {
    var depth = point.x * outward[0] + point.y * outward[1] + point.z * outward[2];
    var off = point.x * point.x + point.y * point.y + point.z * point.z - depth * depth;
    if (off >= radius * radius) return false;
    return depth < Math.sqrt(Math.max(0, radius * radius - off));
  },
  _split: function (points, hidden) {
    var near = [];
    var far = [];
    var nearRun = [];
    var farRun = [];
    function flush() {
      if (nearRun.length > 1) near.push(nearRun);
      if (farRun.length > 1) far.push(farRun);
      nearRun = [];
      farRun = [];
    }
    var previous = null;
    var i;
    for (i = 0; i < points.length; i += 1) {
      var flag = hidden[i];
      if (previous !== null && flag !== previous) {
        if (flag) nearRun.push(points[i]);
        else farRun.push(points[i]);
        flush();
      }
      (flag ? farRun : nearRun).push(points[i]);
      previous = flag;
    }
    flush();
    return { near: near, far: far };
  },
  _dashes: function (points, dash, gap) {
    var cum = [0];
    var i;
    for (i = 1; i < points.length; i += 1) cum.push(cum[i - 1] + points[i].distanceTo(points[i - 1]));
    var total = cum[cum.length - 1];
    var pieces = [];
    if (!(total > 0)) return pieces;
    function at(distance) {
      if (distance <= 0) return points[0].clone();
      if (distance >= total) return points[points.length - 1].clone();
      var index = 1;
      while (cum[index] < distance) index += 1;
      var span = cum[index] - cum[index - 1];
      var fraction = span <= 0 ? 0 : (distance - cum[index - 1]) / span;
      return points[index - 1].clone().lerp(points[index], fraction);
    }
    var period = dash + gap;
    var distance;
    for (distance = 0; distance < total; distance += period) {
      var end = Math.min(total, distance + dash);
      var piece = [at(distance)];
      for (i = 1; i < points.length - 1; i += 1) {
        if (cum[i] > distance && cum[i] < end) piece.push(points[i].clone());
      }
      piece.push(at(end));
      if (piece.length > 1) pieces.push(piece);
    }
    return pieces;
  },
  _addLine: function (points, color, opacity) {
    var geo = new THREE.BufferGeometry().setFromPoints(points);
    var mat = new THREE.LineBasicMaterial({
      color: color,
      transparent: true,
      opacity: opacity,
      depthTest: false
    });
    var line = new THREE.Line(geo, mat);
    line.frustumCulled = false;
    line.renderOrder = 8;
    this.orbitGroup.add(line);
  },
  drawPath: function (raw, color, opacity) {
    if (!raw || raw.length < 2) return;
    var self = this;
    var points = raw.map(function (p) { return self._km(p); });
    var outward = this._outward();
    var hidden = points.map(function (point) {
      return self._behind(point, outward, self.planetKm * 0.98);
    });
    var split = this._split(points, hidden);
    var i;
    for (i = 0; i < split.near.length; i += 1) this._addLine(split.near[i], color, opacity);
    var dash = Math.max(this.planetKm * 0.05, this.spanKm * 0.02);
    for (i = 0; i < split.far.length; i += 1) {
      var pieces = this._dashes(split.far[i], dash, dash * 0.65);
      var k;
      for (k = 0; k < pieces.length; k += 1) this._addLine(pieces[k], color, opacity * 0.7);
    }
    points.forEach(function (p) {
      self.spanKm = Math.max(self.spanKm, p.length());
    });
  },
  _craftPixels: function () {
    var height = this.host.clientHeight || 420;
    return height * 0.05 / (2 * 1.08);
  },
  _px: function (pixels) {
    var dist = Math.max(this.camera.position.length(), this.planetKm);
    var h = this.host.clientHeight || 420;
    var fov = this.camera.fov * Math.PI / 180;
    return (2 * Math.tan(fov / 2) * dist / h) * pixels;
  },
  _point: function (pos, color, pixels, shape) {
    var sprite = new THREE.Sprite(new THREE.SpriteMaterial({
      map: shape ? this._mark(color, shape) : this._dot(color),
      transparent: true,
      depthTest: false
    }));
    var scale = this._px(pixels || 7);
    sprite.scale.set(scale, scale, 1);
    sprite.position.copy(this._km(pos));
    sprite.renderOrder = 12;
    sprite.frustumCulled = false;
    this.orbitGroup.add(sprite);
    return sprite;
  },
  _dot: function (color) {
    var key = String(color);
    this._dots = this._dots || {};
    if (this._dots[key]) return this._dots[key];
    var canvas = document.createElement("canvas");
    canvas.width = 32;
    canvas.height = 32;
    var ctx = canvas.getContext("2d");
    ctx.fillStyle = key;
    ctx.beginPath();
    ctx.arc(16, 16, 6, 0, Math.PI * 2);
    ctx.fill();
    var texture = new THREE.CanvasTexture(canvas);
    this._dots[key] = texture;
    return texture;
  },
  _mark: function (color, shape) {
    var key = shape + "|" + String(color);
    this._marks = this._marks || {};
    if (this._marks[key]) return this._marks[key];
    var canvas = document.createElement("canvas");
    var ctx;
    if (shape === "craft") {
      canvas.width = 64;
      canvas.height = 64;
      ctx = canvas.getContext("2d");
      ctx.fillStyle = String(color);
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.arc(32, 32, 22, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      var craftTexture = new THREE.CanvasTexture(canvas);
      this._marks[key] = craftTexture;
      return craftTexture;
    }
    canvas.width = 32;
    canvas.height = 32;
    ctx = canvas.getContext("2d");
    ctx.fillStyle = "#ffffff";
    if (shape === "square") {
      ctx.fillRect(3, 3, 26, 26);
      ctx.fillStyle = String(color);
      ctx.fillRect(7, 7, 18, 18);
    } else {
      ctx.beginPath();
      ctx.arc(16, 16, 13, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = String(color);
      ctx.beginPath();
      ctx.arc(16, 16, 8, 0, Math.PI * 2);
      ctx.fill();
    }
    var texture = new THREE.CanvasTexture(canvas);
    this._marks[key] = texture;
    return texture;
  },
  _graticule: function (radius) {
    var lat;
    var lon;
    var step;
    for (lat = -60; lat <= 60; lat += 30) {
      var parallel = [];
      for (lon = -180; lon <= 180; lon += 6) {
        var phi = lat * Math.PI / 180;
        var lam = lon * Math.PI / 180;
        parallel.push([
          radius * Math.cos(phi) * Math.cos(lam),
          radius * Math.cos(phi) * Math.sin(lam),
          radius * Math.sin(phi)
        ]);
      }
      this.drawPath(parallel, "#5d6d7e", lat === 0 ? 0.85 : 0.45);
    }
    for (lon = -180; lon < 180; lon += 30) {
      var meridian = [];
      for (step = -90; step <= 90; step += 4) {
        var phi2 = step * Math.PI / 180;
        var lam2 = lon * Math.PI / 180;
        meridian.push([
          radius * Math.cos(phi2) * Math.cos(lam2),
          radius * Math.cos(phi2) * Math.sin(lam2),
          radius * Math.sin(phi2)
        ]);
      }
      this.drawPath(meridian, "#5d6d7e", 0.45);
    }
    var self = this;
    function mark(text, latDeg, lonDeg) {
      var phi = latDeg * Math.PI / 180;
      var lam = lonDeg * Math.PI / 180;
      var lift = radius * 1.04;
      var xyz = [
        lift * Math.cos(phi) * Math.cos(lam),
        lift * Math.cos(phi) * Math.sin(lam),
        lift * Math.sin(phi)
      ];
      if (self._behind(self._km(xyz), self._outward(), self.planetKm)) return;
      var label = self._text(text);
      label.position.copy(self._km(xyz));
      self.orbitGroup.add(label);
    }
    mark("0°", 0, 0);
    mark("30°E", 0, 30);
    mark("60°E", 0, 60);
    mark("90°E", 0, 90);
    mark("90°W", 0, -90);
    mark("30°N", 30, 0);
    mark("30°S", -30, 0);
    mark("60°N", 60, 0);
    mark("60°S", -60, 0);
  },
  _axis: function (radius) {
    var reach = radius * 1.45;
    this.drawPath([[0, 0, -reach], [0, 0, reach]], "#1b2631", 0.9);
    var tip = this._km([0, 0, reach]);
    var arrow = new THREE.ArrowHelper(
      new THREE.Vector3(0, 0, 1),
      tip.clone().addScaledVector(new THREE.Vector3(0, 0, 1), -this.planetKm * 0.02),
      this.planetKm * 0.16,
      0x1b2631,
      this.planetKm * 0.07,
      this.planetKm * 0.035
    );
    this.orbitGroup.add(arrow);
    var label = this._text("ω");
    label.position.copy(this._km([0, 0, reach * 1.12]));
    this.orbitGroup.add(label);
  },
  _text: function (text) {
    this._labelTex = this._labelTex || {};
    if (!this._labelTex[text]) {
      var canvas = document.createElement("canvas");
      canvas.width = 128;
      canvas.height = 64;
      var ctx = canvas.getContext("2d");
      ctx.fillStyle = "#1b2631";
      ctx.font = "bold 28px Segoe UI, Helvetica, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, 64, 32);
      this._labelTex[text] = new THREE.CanvasTexture(canvas);
    }
    var sprite = new THREE.Sprite(new THREE.SpriteMaterial({
      map: this._labelTex[text],
      transparent: true,
      depthTest: false
    }));
    var scale = this._px(15);
    sprite.scale.set(scale * 2.2, scale, 1);
    sprite.renderOrder = 13;
    return sprite;
  },
  _legend: function (items) {
    var list = document.getElementById("legend");
    if (!list) return;
    list.innerHTML = "";
    var i;
    for (i = 0; i < items.length; i += 1) {
      var li = document.createElement("li");
      var swatch = document.createElement("span");
      swatch.style.display = "inline-block";
      swatch.style.width = "16px";
      swatch.style.height = "3px";
      swatch.style.background = items[i].color;
      if (items[i].icon === "dot") {
        swatch.style.width = "10px";
        swatch.style.height = "10px";
        swatch.style.borderRadius = "50%";
      } else if (items[i].icon === "square") {
        swatch.style.width = "9px";
        swatch.style.height = "9px";
      } else if (items[i].icon === "wedge") {
        swatch.style.width = "12px";
        swatch.style.height = "8px";
        swatch.style.background = items[i].color;
        swatch.style.border = "1px solid " + (items[i].edge || "#6c3483");
        swatch.style.opacity = "0.9";
      }
      li.appendChild(swatch);
      li.appendChild(document.createTextNode(items[i].label));
      list.appendChild(li);
    }
  },
  show: function (spec) {
    if (!this.ready) return;
    var changed = spec.token !== this.token;
    if (changed) {
      this.token = spec.token;
      this.clock = 0;
    }
    this.spec = spec;
    this.sequence = spec.sequence || [];
    this.total = 0;
    var i;
    for (i = 0; i < this.sequence.length; i += 1) this.total += this.sequence[i].wall;
    if (!(this.total > 0)) this.total = 1;
    if (changed || !this._planetReady) {
      this._clear(this.staticGroup);
      this.planetKm = (spec.r0 || Lab.R0_EARTH) / 1000.0;
      this.spanKm = this.planetKm;
      var earth = new THREE.Mesh(
        new THREE.SphereGeometry(this.planetKm, 48, 32),
        new THREE.MeshLambertMaterial({
          color: 0x8fb7d6,
          transparent: true,
          opacity: 0.38,
          depthWrite: false
        })
      );
      earth.scale.set(1, 1, 1 - 1 / 298.257);
      this.staticGroup.add(earth);
      this._planetReady = true;
    }
    this._markKey = "";
    this._legend(spec.legend || []);
    this._frame();
    if (changed) this._aim();
  },
  _schedule: function () {
    var time = this.clock % this.total;
    var cursor = 0;
    var i;
    for (i = 0; i < this.sequence.length; i += 1) {
      var leg = this.sequence[i];
      if (time <= cursor + leg.wall || i === this.sequence.length - 1) {
        var u = leg.wall > 0 ? (time - cursor) / leg.wall : 1;
        if (u < 0) u = 0;
        if (u > 1) u = 1;
        return { leg: leg, u: u };
      }
      cursor += leg.wall;
    }
    return { leg: this.sequence[0], u: 0 };
  },
  _lerpPaths: function (from, to, u) {
    var s = u * u * (3 - 2 * u);
    var n = Math.min(from.length, to.length);
    var out = [];
    var i;
    for (i = 0; i < n; i += 1) {
      out.push([
        from[i][0] + (to[i][0] - from[i][0]) * s,
        from[i][1] + (to[i][1] - from[i][1]) * s,
        from[i][2] + (to[i][2] - from[i][2]) * s
      ]);
    }
    return out;
  },
  _lerpMorph: function (morph, u) {
    var s = u * u * (3 - 2 * u);
    return {
      rp: morph.rp0 + (morph.rp1 - morph.rp0) * s,
      ra: morph.ra0 + (morph.ra1 - morph.ra0) * s,
      inc: morph.i0 + (morph.i1 - morph.i0) * s,
      color: morph.color1,
      s: s
    };
  },
  _frame: function () {
    if (!this.spec) return;
    this._clear(this.orbitGroup);
    this.spanKm = this.planetKm;
    this._graticule(this.planetKm * 1000 * 1.012);
    this._axis(this.planetKm * 1000);
    var schedule = this.sequence.length ? this._schedule() : null;
    var layers = this.spec.layers || [];
    var i;
    var hotLayer = null;
    for (i = 0; i < layers.length; i += 1) {
      var hot = schedule && schedule.leg.focus === layers[i].id;
      var swinging = schedule && schedule.leg.morph && (schedule.leg.morph.hide === layers[i].id || schedule.leg.morph.hide2 === layers[i].id);
      if (swinging) continue;
      if (hot) hotLayer = layers[i];
      else this.drawPath(layers[i].points, layers[i].color, 0.2);
    }
    if (hotLayer) this.drawPath(hotLayer.points, hotLayer.color, 1);
    if (schedule && schedule.leg.kind === "burn" && schedule.leg.morph) {
      if (schedule.leg.morph.paths) {
        var blended = this._lerpPaths(schedule.leg.morph.paths[0], schedule.leg.morph.paths[1], schedule.u);
        this.drawPath(blended, schedule.leg.morph.color, 1);
      } else {
        var shape = this._lerpMorph(schedule.leg.morph, schedule.u);
        this.drawPath(Lab.conicSamples(shape.rp, shape.ra, shape.inc, 181), schedule.leg.morph.color1, 1);
      }
    }
    var burns = this.spec.burns || [];
    for (i = 0; i < burns.length; i += 1) {
      var burn = burns[i];
      var origin = this._km(burn.pos);
      var dir = new THREE.Vector3(burn.dir[0], burn.dir[1], burn.dir[2]);
      if (dir.lengthSq() < 1e-12) dir.set(0, 1, 0);
      dir.normalize();
      var length = Math.max(this.planetKm * 0.08, (this.spanKm || this.planetKm) * 0.045);
      var active = schedule && schedule.leg.kind === "burn" && schedule.leg.burn === i;
      var arrow = new THREE.ArrowHelper(dir, origin, active ? length * 1.25 : length * 0.85, 0xc0392b, length * 0.18, length * 0.08);
      this.orbitGroup.add(arrow);
    }
    (this.spec.markers || []).forEach(function (marker) {
      Lab.Globe._point(marker.pos, marker.color || "#1a5276");
    });
    var at = null;
    if (schedule && schedule.leg.kind === "burn") at = schedule.leg.pos;
    else if (schedule && schedule.leg.points) at = this._sample(schedule.leg.points, schedule.u);
    var flags = this._orbitMarks(this._activePoints(schedule));
    if (at && this._inclination(at)) flags.push("wedge");
    if (at) this._point(at, "#e67e22", this._craftPixels(), "craft");
    this._markLegend(flags);
    var leg = document.getElementById("leg");
    if (leg) leg.textContent = schedule && schedule.leg.label ? schedule.leg.label : "";
  },
  _activePoints: function (schedule) {
    if (!schedule) return null;
    var leg = schedule.leg;
    if (leg.focus === "deputy") return null;
    if (leg.kind === "burn" && leg.morph) {
      if (leg.morph.paths) return this._lerpPaths(leg.morph.paths[0], leg.morph.paths[1], schedule.u);
      var shape = this._lerpMorph(leg.morph, schedule.u);
      return Lab.conicSamples(shape.rp, shape.ra, shape.inc, 181);
    }
    var layers = (this.spec && this.spec.layers) || [];
    var i;
    for (i = 0; i < layers.length; i += 1) {
      if (layers[i].id === leg.focus && layers[i].points && layers[i].points.length > 8) return layers[i].points;
    }
    return leg.points || null;
  },
  _orbitMarks: function (points) {
    var flags = [];
    if (!points || points.length < 8) return flags;
    var i;
    var rmin = Infinity;
    var rmax = 0;
    var imin = 0;
    var imax = 0;
    var zmax = 0;
    for (i = 0; i < points.length; i += 1) {
      var p = points[i];
      var r = Math.hypot(p[0], p[1], p[2]);
      if (r < rmin) { rmin = r; imin = i; }
      if (r > rmax) { rmax = r; imax = i; }
      zmax = Math.max(zmax, Math.abs(p[2]));
    }
    if (!(rmax > 0)) return flags;
    var closed = Math.hypot(points[0][0] - points[points.length - 1][0], points[0][1] - points[points.length - 1][1], points[0][2] - points[points.length - 1][2]) < 0.02 * rmax;
    if ((rmax - rmin) / rmax > 0.02) {
      if (closed || (imin > 0 && imin < points.length - 1)) {
        this._point(points[imin], "#117a65", 11, "dot");
        flags.push("peri");
      }
      if (closed || (imax > 0 && imax < points.length - 1)) {
        this._point(points[imax], "#6c3483", 11, "square");
        flags.push("apo");
      }
    }
    if (zmax > 0.02 * rmax) {
      var an = null;
      var dn = null;
      for (i = 0; i < points.length - 1; i += 1) {
        var a = points[i];
        var b = points[i + 1];
        if (a[2] <= 0 && b[2] > 0) an = this._zCross(a, b);
        else if (a[2] < 0 && b[2] >= 0) an = this._zCross(a, b);
        if (a[2] >= 0 && b[2] < 0) dn = this._zCross(a, b);
        else if (a[2] > 0 && b[2] <= 0) dn = this._zCross(a, b);
      }
      if (an) {
        this._point(an, "#d68910", 11, "dot");
        flags.push("an");
      }
      if (dn) {
        this._point(dn, "#2471a3", 11, "dot");
        flags.push("dn");
      }
    }
    return flags;
  },
  _zCross: function (a, b) {
    var dz = b[2] - a[2];
    var t = dz === 0 ? 0 : (0 - a[2]) / dz;
    if (t < 0) t = 0;
    if (t > 1) t = 1;
    return [
      a[0] + (b[0] - a[0]) * t,
      a[1] + (b[1] - a[1]) * t,
      a[2] + (b[2] - a[2]) * t
    ];
  },
  _inclination: function (craft) {
    var horizontal = Math.hypot(craft[0], craft[1]);
    var radiusM = Math.hypot(horizontal, craft[2]);
    if (radiusM < 1) return false;
    var elevation = Math.atan2(craft[2], horizontal);
    if (Math.abs(elevation) < 0.03) return false;
    var along = horizontal < 1e-3 ? 1 : craft[0] / horizontal;
    var across = horizontal < 1e-3 ? 0 : craft[1] / horizontal;
    var radius = radiusM / 1000;
    var steps = 28;
    var positions = new Float32Array((steps + 1) * 3);
    var indices = [];
    var i;
    for (i = 0; i < steps; i += 1) {
      var tilt = elevation * (i / (steps - 1));
      var idx = (i + 1) * 3;
      positions[idx] = radius * Math.cos(tilt) * along;
      positions[idx + 1] = radius * Math.cos(tilt) * across;
      positions[idx + 2] = radius * Math.sin(tilt);
    }
    positions[steps * 3] = craft[0] / 1000;
    positions[steps * 3 + 1] = craft[1] / 1000;
    positions[steps * 3 + 2] = craft[2] / 1000;
    for (i = 1; i < steps; i += 1) indices.push(0, i, i + 1);
    var geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setIndex(indices);
    var mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({
      color: 0xd2b4de,
      transparent: true,
      opacity: 0.5,
      depthTest: false,
      side: THREE.DoubleSide
    }));
    mesh.frustumCulled = false;
    mesh.renderOrder = 7;
    this.orbitGroup.add(mesh);
    var outline = new Float32Array((steps + 2) * 3);
    outline.set(positions.subarray(3), 3);
    var line = new THREE.Line(new THREE.BufferGeometry().setAttribute("position", new THREE.BufferAttribute(outline, 3)), new THREE.LineBasicMaterial({
      color: 0x6c3483,
      transparent: true,
      opacity: 0.95,
      depthTest: false
    }));
    line.frustumCulled = false;
    line.renderOrder = 7;
    this.orbitGroup.add(line);
    return true;
  },
  _markLegend: function (flags) {
    var key = flags.join("|");
    if (key === this._markKey) return;
    this._markKey = key;
    var items = (this.spec && this.spec.legend ? this.spec.legend : []).slice();
    if (flags.indexOf("an") >= 0) items.push({ label: "Ascending node", color: "#d68910", icon: "dot" });
    if (flags.indexOf("dn") >= 0) items.push({ label: "Descending node", color: "#2471a3", icon: "dot" });
    if (flags.indexOf("peri") >= 0) items.push({ label: "Periapsis", color: "#117a65", icon: "dot" });
    if (flags.indexOf("apo") >= 0) items.push({ label: "Apoapsis", color: "#6c3483", icon: "square" });
    if (flags.indexOf("wedge") >= 0) items.push({ label: "Inclination", color: "#d2b4de", icon: "wedge", edge: "#6c3483" });
    this._legend(items);
  },
  _sample: function (points, u) {
    if (!points || !points.length) return null;
    if (points.length === 1) return points[0];
    var f = Math.max(0, Math.min(0.999999, u)) * (points.length - 1);
    var i0 = Math.floor(f);
    var span = f - i0;
    var a = points[i0];
    var b = points[Math.min(points.length - 1, i0 + 1)];
    return [
      a[0] + (b[0] - a[0]) * span,
      a[1] + (b[1] - a[1]) * span,
      a[2] + (b[2] - a[2]) * span
    ];
  },
  _placeCraft: function () {}
};
