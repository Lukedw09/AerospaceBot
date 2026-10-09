/* Lat-lon map shared by ground track, coverage corridor, and launch azimuth. */
var Lab = Lab || {};

Lab.Map2d = {
  project: function (lat, lon, w, h, pad) {
    var x = pad + ((lon + Math.PI) / (2.0 * Math.PI)) * (w - 2 * pad);
    var y = pad + ((Math.PI / 2.0 - lat) / Math.PI) * (h - 2 * pad);
    return [x, y];
  },
  drawGrid: function (ctx, w, h) {
    ctx.fillStyle = "#d7e6f2";
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "#9bb8d0";
    ctx.lineWidth = 1;
    ctx.font = "11px Segoe UI, Helvetica, sans-serif";
    ctx.fillStyle = "#1b2631";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    var lat;
    var lon;
    ctx.beginPath();
    for (lat = -60; lat <= 60; lat += 30) {
      var a = this.project(lat * Math.PI / 180.0, -Math.PI, w, h, 28);
      var b = this.project(lat * Math.PI / 180.0, Math.PI, w, h, 28);
      ctx.moveTo(a[0], a[1]);
      ctx.lineTo(b[0], b[1]);
    }
    for (lon = -150; lon <= 180; lon += 30) {
      var c = this.project(Math.PI / 2.0, lon * Math.PI / 180.0, w, h, 28);
      var d = this.project(-Math.PI / 2.0, lon * Math.PI / 180.0, w, h, 28);
      ctx.moveTo(c[0], c[1]);
      ctx.lineTo(d[0], d[1]);
    }
    ctx.stroke();
    ctx.strokeStyle = "#1a5276";
    ctx.beginPath();
    var eq0 = this.project(0, -Math.PI, w, h, 28);
    var eq1 = this.project(0, Math.PI, w, h, 28);
    ctx.moveTo(eq0[0], eq0[1]);
    ctx.lineTo(eq1[0], eq1[1]);
    ctx.stroke();
    ctx.fillStyle = "#1b2631";
    for (lat = -60; lat <= 60; lat += 30) {
      var mark = this.project(lat * Math.PI / 180.0, -Math.PI, w, h, 28);
      ctx.textAlign = "right";
      ctx.fillText(lat + "°", mark[0] - 4, mark[1]);
    }
    ctx.textAlign = "center";
    for (lon = -180; lon <= 180; lon += 30) {
      var bottom = this.project(-Math.PI / 2.0, lon * Math.PI / 180.0, w, h, 28);
      var label = lon === -180 ? "180°" : lon + "°";
      ctx.fillText(label, bottom[0], bottom[1] + 12);
    }
  },
  split: function (points) {
    var runs = [];
    var run = [];
    var i;
    for (i = 0; i < points.length; i += 1) {
      if (run.length && Math.abs(points[i].lon - run[run.length - 1].lon) > Math.PI) {
        runs.push(run);
        run = [];
      }
      run.push(points[i]);
    }
    if (run.length) runs.push(run);
    return runs;
  },
  stroke: function (ctx, points, w, h, color, width) {
    var runs = this.split(points);
    ctx.strokeStyle = color;
    ctx.lineWidth = width || 1.6;
    var r;
    for (r = 0; r < runs.length; r += 1) {
      var run = runs[r];
      if (run.length < 2) continue;
      ctx.beginPath();
      var p0 = this.project(run[0].lat, run[0].lon, w, h, 28);
      ctx.moveTo(p0[0], p0[1]);
      var i;
      for (i = 1; i < run.length; i += 1) {
        var p = this.project(run[i].lat, run[i].lon, w, h, 28);
        ctx.lineTo(p[0], p[1]);
      }
      ctx.stroke();
    }
  },
  destination: function (lat, lon, bearing, angle) {
    var lat2 = Math.asin(
      Math.sin(lat) * Math.cos(angle) + Math.cos(lat) * Math.sin(angle) * Math.cos(bearing)
    );
    var lon2 = lon + Math.atan2(
      Math.sin(bearing) * Math.sin(angle) * Math.cos(lat),
      Math.cos(angle) - Math.sin(lat) * Math.sin(lat2)
    );
    return { lat: lat2, lon: Lab.wrapPi(lon2) };
  },
  bearing: function (a, b) {
    var y = Math.sin(b.lon - a.lon) * Math.cos(b.lat);
    var x = Math.cos(a.lat) * Math.sin(b.lat) - Math.sin(a.lat) * Math.cos(b.lat) * Math.cos(b.lon - a.lon);
    return Math.atan2(y, x);
  },
  corridor: function (track, halfAngle) {
    var left = [];
    var right = [];
    var i;
    for (i = 0; i < track.length; i += 1) {
      var nxt = track[Math.min(track.length - 1, i + 1)];
      var prv = track[Math.max(0, i - 1)];
      var brg = this.bearing(i === track.length - 1 ? prv : track[i], i === track.length - 1 ? track[i] : nxt);
      left.push(this.destination(track[i].lat, track[i].lon, brg - Math.PI / 2.0, halfAngle));
      right.push(this.destination(track[i].lat, track[i].lon, brg + Math.PI / 2.0, halfAngle));
    }
    return { left: left, right: right };
  },
  fillCorridor: function (ctx, left, right, w, h) {
    var n = Math.min(left.length, right.length);
    if (n < 2) return;
    ctx.fillStyle = "rgba(146, 43, 33, 0.28)";
    var i;
    for (i = 0; i < n - 1; i += 1) {
      if (Math.abs(left[i + 1].lon - left[i].lon) > Math.PI) continue;
      if (Math.abs(right[i + 1].lon - right[i].lon) > Math.PI) continue;
      var a = this.project(left[i].lat, left[i].lon, w, h, 28);
      var b = this.project(left[i + 1].lat, left[i + 1].lon, w, h, 28);
      var c = this.project(right[i + 1].lat, right[i + 1].lon, w, h, 28);
      var d = this.project(right[i].lat, right[i].lon, w, h, 28);
      ctx.beginPath();
      ctx.moveTo(a[0], a[1]);
      ctx.lineTo(b[0], b[1]);
      ctx.lineTo(c[0], c[1]);
      ctx.lineTo(d[0], d[1]);
      ctx.closePath();
      ctx.fill();
    }
  },
  draw: function (canvas, spec) {
    var w = canvas.width;
    var h = canvas.height;
    var ctx = canvas.getContext("2d");
    this.drawGrid(ctx, w, h);
    var track = spec.track || [];
    var n = Math.max(2, Math.floor(track.length * (spec.fraction === undefined ? 1 : spec.fraction)));
    var shown = track.slice(0, n);
    if (spec.kind === "coverage" && spec.lambda) {
      var band = this.corridor(shown, spec.lambda);
      this.fillCorridor(ctx, band.left, band.right, w, h);
      this.stroke(ctx, band.left, w, h, "#7b241c", 1);
      this.stroke(ctx, band.right, w, h, "#7b241c", 1);
    }
    if (spec.kind === "launch" && spec.site) {
      var site = this.project(spec.site.lat, spec.site.lon, w, h, 28);
      ctx.fillStyle = "#117a65";
      ctx.beginPath();
      ctx.arc(site[0], site[1], 5, 0, 2 * Math.PI);
      ctx.fill();
      if (shown.length) this.stroke(ctx, shown, w, h, "#117a65", 2);
    } else {
      this.stroke(ctx, shown, w, h, "#922b21", 1.8);
    }
  }
};
