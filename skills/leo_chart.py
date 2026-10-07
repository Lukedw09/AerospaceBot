"""Shared 2D PNG + HTML chart writer for skills."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CHART_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { color-scheme: light; --ink: #1b2631; --muted: #34495e; --line: #d5d8dc; --paper: #f7f9fb; }
  body { margin: 0; background: var(--paper); color: var(--ink); font-family: "Segoe UI", Helvetica, Arial, sans-serif; }
  header { padding: 16px 20px 8px; }
  h1 { margin: 0; font-size: 20px; font-weight: 560; }
  p.note { margin: 6px 0 0; color: var(--muted); font-size: 13px; }
  .wrap { display: flex; align-items: flex-start; gap: 16px; padding: 8px 20px 20px; }
  canvas { width: min(820px, 100%); height: auto; background: #fff; border: 1px solid var(--line); }
  #legend { min-width: 240px; background: #fff; border: 1px solid var(--line); padding: 12px 14px; font-size: 13px; }
  #legend h2 { margin: 0 0 8px; font-size: 13px; letter-spacing: 0.02em; }
  .row { display: flex; align-items: center; gap: 8px; margin: 6px 0; }
  .swatch { width: 14px; height: 14px; border-radius: 2px; flex: 0 0 auto; }
  .row span { color: var(--muted); margin-left: auto; font-variant-numeric: tabular-nums; }
  #scrub { margin-top: 12px; width: 100%; }
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <p class="note" id="note"></p>
</header>
<div class="wrap">
  <canvas id="plot" width="820" height="520"></canvas>
  <aside id="legend"><h2>Legend</h2></aside>
</div>
<script type="application/json" id="chart-json">__CHART_JSON__</script>
<script>
(function () {
  const data = JSON.parse(document.getElementById("chart-json").textContent);
  const canvas = document.getElementById("plot");
  const ctx = canvas.getContext("2d");
  const legend = document.getElementById("legend");
  const palette = ["#1a5276", "#b9770e", "#1e8449", "#6c3483", "#1a6b7a", "#7d6608", "#922b21", "#1b2631"];
  const note = document.getElementById("note");
  if (data.note) note.textContent = data.note;
  function fmt(value) {
    const abs = Math.abs(value);
    if (abs >= 100) return value.toFixed(0);
    if (abs >= 10) return value.toFixed(1);
    return value.toFixed(2);
  }
  function clear() { ctx.clearRect(0, 0, canvas.width, canvas.height); }
  function yTitle(text) {
    ctx.save();
    ctx.translate(18, canvas.height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.font = "13px Segoe UI";
    ctx.fillStyle = "#34495e";
    ctx.textAlign = "center";
    ctx.fillText(text, 0, 0);
    ctx.restore();
  }
  function xTitle(text, y) {
    ctx.font = "13px Segoe UI";
    ctx.fillStyle = "#34495e";
    ctx.textAlign = "center";
    ctx.fillText(text, (70 + 790) / 2, y);
  }
  function frame(left, top, right, bottom) {
    ctx.strokeStyle = "#d5d8dc";
    ctx.lineWidth = 1;
    for (let k = 0; k <= 4; k++) {
      const y = top + (bottom - top) * k / 4;
      ctx.beginPath();
      ctx.moveTo(left, y);
      ctx.lineTo(right, y);
      ctx.stroke();
    }
    ctx.strokeStyle = "#1b2631";
    ctx.beginPath();
    ctx.moveTo(left, bottom);
    ctx.lineTo(left, top);
    ctx.moveTo(left, bottom);
    ctx.lineTo(right, bottom);
    ctx.stroke();
  }
  function addRow(color, name, value, onChange) {
    const row = document.createElement("label");
    row.className = "row";
    if (onChange) {
      const box = document.createElement("input");
      box.type = "checkbox";
      box.checked = true;
      box.addEventListener("change", function () { onChange(box.checked); });
      row.appendChild(box);
    }
    const swatch = document.createElement("i");
    swatch.className = "swatch";
    swatch.style.background = color;
    row.appendChild(swatch);
    row.appendChild(document.createTextNode(name));
    if (value != null) {
      const num = document.createElement("span");
      num.textContent = value;
      row.appendChild(num);
    }
    legend.appendChild(row);
  }
  function waterfall(enabled) {
    clear();
    const unit = data.unit || "m/s";
    const terms = [];
    data.terms.forEach(function (term, i) {
      if (enabled[i]) terms.push(term);
    });
    let run = 0;
    const rows = terms.map(function (term) {
      const start = run;
      run += term.value;
      return { name: term.name, start: start, end: run, value: term.value, color: term.color };
    });
    rows.push({ name: "total", start: 0, end: run, value: run, color: "#1b2631" });
    const vals = [0];
    rows.forEach(function (row) { vals.push(row.start, row.end); });
    const lo = Math.min.apply(null, vals);
    const hi = Math.max.apply(null, vals);
    const span = (hi - lo) || 1;
    const left = 64, right = 790, top = 28, bottom = 450;
    frame(left, top, right, bottom);
    const slot = (right - left) / rows.length;
    const bw = Math.min(48, slot * 0.62);
    function yOf(v) { return bottom - (v - lo) / span * (bottom - top); }
    rows.forEach(function (row, i) {
      const x = left + (i + 0.5) * slot - bw / 2;
      const y1 = yOf(row.start);
      const y2 = yOf(row.end);
      ctx.fillStyle = row.color;
      ctx.fillRect(x, Math.min(y1, y2), bw, Math.max(2, Math.abs(y2 - y1)));
      if (i < rows.length - 1) {
        ctx.strokeStyle = "#aeb6bf";
        ctx.beginPath();
        ctx.moveTo(x + bw, y2);
        ctx.lineTo(x + slot, y2);
        ctx.stroke();
      }
      ctx.fillStyle = "#1b2631";
      ctx.font = "12px Segoe UI";
      ctx.textAlign = "center";
      ctx.fillText(String(i + 1), x + bw / 2, bottom + 18);
    });
    ctx.textAlign = "right";
    ctx.font = "11px Segoe UI";
    ctx.fillStyle = "#34495e";
    for (let k = 0; k <= 4; k++) {
      const v = lo + (hi - lo) * (4 - k) / 4;
      ctx.fillText(fmt(v), left - 8, yOf(v) + 4);
    }
    yTitle(unit);
    xTitle("contribution (see legend)", bottom + 42);
  }
  function stack() {
    clear();
    const unit = data.unit || "kg";
    const names = [];
    data.stages.forEach(function (stage) {
      stage.parts.forEach(function (part) {
        if (part.value > 0 && names.indexOf(part.name) < 0) names.push(part.name);
      });
    });
    const colorOf = {};
    names.forEach(function (name, i) { colorOf[name] = palette[i % palette.length]; });
    const left = 64, right = 790, top = 28, bottom = 450;
    frame(left, top, right, bottom);
    const totals = data.stages.map(function (stage) {
      return stage.parts.reduce(function (sum, part) { return sum + Math.max(part.value, 0); }, 0);
    });
    const hi = Math.max.apply(null, totals.concat([1]));
    const slot = (right - left) / Math.max(data.stages.length, 1);
    const bw = Math.min(72, slot * 0.55);
    data.stages.forEach(function (stage, i) {
      let y = bottom;
      const x = left + (i + 0.5) * slot - bw / 2;
      stage.parts.forEach(function (part) {
        if (part.value <= 0) return;
        const h = part.value / hi * (bottom - top);
        y -= h;
        ctx.fillStyle = colorOf[part.name];
        ctx.fillRect(x, y, bw, h);
      });
      ctx.fillStyle = "#1b2631";
      ctx.font = "13px Segoe UI";
      ctx.textAlign = "center";
      ctx.fillText(stage.name, x + bw / 2, bottom + 22);
    });
    ctx.textAlign = "right";
    ctx.font = "11px Segoe UI";
    ctx.fillStyle = "#34495e";
    for (let k = 0; k <= 4; k++) {
      const v = hi * (4 - k) / 4;
      const y = bottom - (bottom - top) * (4 - k) / 4;
      ctx.fillText(fmt(v), left - 8, y + 4);
    }
    yTitle(unit);
    return colorOf;
  }
  function series(index) {
    clear();
    const xs = data.xs;
    const ys = data.ys;
    const left = 64, right = 790, top = 28, bottom = 450;
    const xmin = Math.min.apply(null, xs), xmax = Math.max.apply(null, xs);
    const ymin = Math.min.apply(null, ys.concat([0]));
    const ymax = Math.max.apply(null, ys.concat([0]));
    const spanX = (xmax - xmin) || 1;
    const spanY = (ymax - ymin) || 1;
    frame(left, top, right, bottom);
    function px(x) { return left + (x - xmin) / spanX * (right - left); }
    function py(y) { return bottom - (y - ymin) / spanY * (bottom - top); }
    ctx.beginPath();
    xs.forEach(function (x, i) {
      if (i === 0) ctx.moveTo(px(x), py(ys[i]));
      else ctx.lineTo(px(x), py(ys[i]));
    });
    ctx.strokeStyle = "#1a5276";
    ctx.lineWidth = 2;
    ctx.stroke();
    const k = Math.max(0, Math.min(xs.length - 1, index | 0));
    ctx.fillStyle = "#c0392b";
    ctx.beginPath();
    ctx.arc(px(xs[k]), py(ys[k]), 5, 0, 6.3);
    ctx.fill();
    ctx.textAlign = "right";
    ctx.font = "11px Segoe UI";
    ctx.fillStyle = "#34495e";
    for (let g = 0; g <= 4; g++) {
      const v = ymin + spanY * (4 - g) / 4;
      ctx.fillText(fmt(v), left - 8, py(v) + 4);
    }
    ctx.textAlign = "center";
    ctx.fillText(fmt(xmin), px(xmin), bottom + 18);
    ctx.fillText(fmt(xmax), px(xmax), bottom + 18);
    yTitle(data.ylabel || "");
    xTitle(data.xlabel || "", bottom + 40);
    return k;
  }
  if (data.kind === "waterfall") {
    const enabled = data.terms.map(function () { return true; });
    data.terms.forEach(function (term, i) {
      term.color = term.value < 0 ? "#922b21" : palette[i % palette.length];
    });
    function paint() { waterfall(enabled); }
    data.terms.forEach(function (term, i) {
      const unit = data.unit || "m/s";
      addRow(term.color, (i + 1) + ". " + term.name, (term.value >= 0 ? "+" : "") + fmt(term.value) + " " + unit, function (on) {
        enabled[i] = on;
        paint();
      });
    });
    addRow("#1b2631", "total", "sum of checked rows");
    paint();
  } else if (data.kind === "stack") {
    const colorOf = stack();
    Object.keys(colorOf).forEach(function (name) { addRow(colorOf[name], name, data.unit || "kg"); });
  } else {
    const markName = data.markName || "marked point";
    const seriesName = data.seriesName || "series";
    addRow("#1a5276", seriesName, data.ylabel || "");
    const value = document.createElement("div");
    value.className = "row";
    legend.appendChild(value);
    function show(index) {
      const k = series(index);
      value.innerHTML = "";
      const swatch = document.createElement("i");
      swatch.className = "swatch";
      swatch.style.background = "#c0392b";
      const text = document.createElement("span");
      text.style.marginLeft = "0";
      text.style.color = "#1b2631";
      text.textContent = markName + ": " + fmt(data.xs[k]) + ", " + fmt(data.ys[k]);
      value.appendChild(swatch);
      value.appendChild(text);
    }
    const slider = document.createElement("input");
    slider.id = "scrub";
    slider.type = "range";
    slider.min = "0";
    slider.max = String(Math.max(data.xs.length - 1, 0));
    slider.value = String(data.mark || 0);
    slider.addEventListener("input", function () { show(Number(slider.value)); });
    legend.appendChild(slider);
    show(Number(slider.value));
  }
})();
</script>
</body>
</html>
"""


def write_chart(png: Path, title: str, payload: dict, *, html: bool = True) -> Path:
    import matplotlib

    if "matplotlib.pyplot" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    png = png.resolve()
    png.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    kind = payload["kind"]
    if kind == "waterfall":
        run = 0.0
        for i, term in enumerate(payload["terms"]):
            run += term["value"]
            ax.bar(
                i,
                term["value"],
                color="#922b21" if term["value"] < 0 else f"C{i % 8}",
                label=term["name"],
            )
        ax.bar(len(payload["terms"]), run, color="#1b2631", label="total")
        ax.legend(fontsize=8)
        ax.set_ylabel(payload.get("unit", "m/s"))
        ax.set_xticks([])
    elif kind == "stack":
        labels = [s["name"] for s in payload["stages"]]
        names: list[str] = []
        for stage in payload["stages"]:
            for part in stage["parts"]:
                if part["value"] > 0 and part["name"] not in names:
                    names.append(part["name"])
        bottoms = [0.0] * len(labels)
        for name in names:
            heights = []
            for stage in payload["stages"]:
                heights.append(sum(part["value"] for part in stage["parts"] if part["name"] == name))
            ax.bar(labels, heights, bottom=bottoms, label=name)
            bottoms = [b + h for b, h in zip(bottoms, heights)]
        ax.legend()
        ax.set_ylabel(payload.get("unit", "kg"))
    else:
        ax.plot(payload["xs"], payload["ys"], color="#1a5276", label=payload.get("seriesName", "series"))
        mark = int(payload.get("mark") or 0)
        ax.scatter(
            [payload["xs"][mark]],
            [payload["ys"][mark]],
            color="#c0392b",
            label=payload.get("markName", "marked point"),
            zorder=3,
        )
        ax.legend()
        ax.set_xlabel(payload.get("xlabel", ""))
        ax.set_ylabel(payload.get("ylabel", ""))
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(png, dpi=120)
    plt.close(fig)
    if not html:
        return png
    html_path = png.with_suffix(".html")
    encoded = json.dumps(payload, allow_nan=False).replace("<", "\\u003c")
    page = CHART_HTML.replace("__TITLE__", title).replace("__CHART_JSON__", encoded)
    html_path.write_text(page, encoding="utf-8")
    return html_path
