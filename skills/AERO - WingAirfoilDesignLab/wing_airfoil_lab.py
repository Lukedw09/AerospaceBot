#!/usr/bin/env python3
"""Interactive wing and airfoil page.

Report 824 charts supply section lift when the designation is in the table.
Any other four-digit section uses thin-airfoil lift. Planform sweep multiplies
the section slope by cos(sweep) before wing_lift_curve_slope. That cosine is
not a catalogue identity.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
ROOT = SKILL_DIR.parents[1]
sys.path.insert(0, str(ROOT / "skills" / "AERO - NACAFourDigitSection"))
sys.path.insert(0, str(ROOT / "skills" / "AERO - WingGeometry"))
sys.path.insert(0, str(ROOT / "skills" / "AERO - FiniteWingLiftCurve"))

import finite_wing_lift_curve as finite  # noqa: E402
import naca_four_digit_section as naca  # noqa: E402
import wing_geometry as winggeo  # noqa: E402

PLOT_TITLE = "Wing and airfoil design"
SLOPE_WINDOW_DEG = 6.0
JS_FILES = (
    "naca_geometry.js",
    "naca_polar.js",
    "wing_geometry.js",
    "finite_wing.js",
    "lab.js",
)
ASSUMPTIONS = (
    "NACA four-digit geometry; Report 824 section cl, alpha_L0, and cl,max "
    "when the designation is in the chart table, otherwise thin-airfoil "
    "a0 = 2*pi and naca4_zero_lift_angle with the user CD0 and CLmax; "
    "planform from WingGeometry; wing slope is wing_lift_curve_slope after "
    "a0_eff = a0*cos(sweep); that cosine is not a catalogue identity; "
    "induced drag at a given CL is CL**2/(pi*AR*e); sweep changes induced "
    "drag only by changing CL(alpha); wing CLmax is the section CLmax with "
    "no extra finite-wing stall credit; omitted sweep is an unswept leading "
    "edge; omitted Reynolds number uses the chart nearest 6e6"
)


class DesignError(Exception):
    """The seed is not a usable wing and airfoil point."""


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    elif value is None:
        text = "n/a"
    else:
        text = str(value)
    print(f"{key}: {text}")


def naca4_zero_lift_angle(m: float, p: float) -> float:
    """naca4_zero_lift_angle. Symmetric sections short-circuit to zero."""
    if m == 0.0:
        return 0.0
    if not 0.0 < p < 1.0:
        raise DesignError("camber station must lie strictly between 0 and 1")
    theta_p = 2.0 * math.atan(math.sqrt(p / (1.0 - p)))
    b = 2.0 * p - 1.0
    s = math.sqrt(p * (1.0 - p))
    inner = (b - 0.5) * theta_p + 2.0 * s * (1.0 - b) + b * s
    ff = m / p**2
    fa = m / (1.0 - p) ** 2
    return (1.0 / math.pi) * (ff * inner + fa * ((b - 0.5) * math.pi - inner))


def catalogue_zero_lift(m: float, p: float) -> float:
    """The catalogue expression, used only to check the helper above."""
    theta_p = 2.0 * math.atan(math.sqrt(p / (1.0 - p)))
    return (1.0 / math.pi) * (
        (m / p**2)
        * (
            (2 * p - 1 - 0.5) * theta_p
            + 2 * (p * (1 - p)) ** 0.5 * (1 - (2 * p - 1))
            + (2 * p - 1) * (p * (1 - p)) ** 0.5
        )
        + (m / (1 - p) ** 2)
        * (
            (2 * p - 1 - 0.5) * math.pi
            - (
                (2 * p - 1 - 0.5) * theta_p
                + 2 * (p * (1 - p)) ** 0.5 * (1 - (2 * p - 1))
                + (2 * p - 1) * (p * (1 - p)) ** 0.5
            )
        )
    )


def measured_a0(alpha_deg: tuple[float, ...], cl: tuple[float, ...], alpha_l0_deg: float) -> float:
    xs: list[float] = []
    ys: list[float] = []
    for angle, lift in zip(alpha_deg, cl):
        if abs(angle - alpha_l0_deg) <= SLOPE_WINDOW_DEG + 1e-9:
            xs.append(math.radians(angle - alpha_l0_deg))
            ys.append(lift)
    if len(xs) < 2:
        raise DesignError("measured lift curve has too few points near zero lift")
    den = sum(x * x for x in xs)
    if den == 0.0:
        raise DesignError("measured slope is undefined")
    return sum(x * y for x, y in zip(xs, ys)) / den


def cd_at_cl_clamped(polar: naca.Polar, cl: float) -> tuple[float, bool]:
    lo, hi = polar.cl_polar[0], polar.cl_polar[-1]
    clamped = cl < lo or cl > hi
    query = min(max(cl, lo), hi)
    return naca.cd_at_cl(polar, query), clamped


def re_source(curves: tuple[naca.Polar, ...] | None, requested: float | None) -> str:
    if curves is None:
        return "n/a"
    if requested is None:
        return "nearest_6e6"
    for item in curves:
        if abs(requested - item.reynolds) <= 1e-6 * item.reynolds:
            return "chart"
    return "log_re_blend"


def default_seed() -> dict:
    return {
        "naca": "2412",
        "re": None,
        "span": 10.0,
        "root": 1.5,
        "tip": 1.0,
        "sweep": None,
        "sweepAt": None,
        "sweepAtGiven": False,
        "e": 1.0,
        "cd0": 0.008,
        "clmaxTheory": 1.2,
        "alpha": math.radians(4.0),
    }


def design_point(seed: dict, catalog: dict | None = None) -> dict:
    try:
        return _design_point(seed, naca.load_catalog() if catalog is None else catalog)
    except (DesignError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


def _design_point(seed: dict, catalog: dict) -> dict:
    digits = naca.parse_designation(str(seed["naca"]))
    curves = catalog.get(digits.designation)
    polar = None
    if curves is not None:
        polar = naca.polar_for(digits, catalog, seed["re"])
    source = "report824" if polar is not None else "thin_airfoil"
    plan = winggeo.planform_from(
        float(seed["span"]),
        float(seed["root"]),
        float(seed["tip"]),
        None if seed["sweep"] is None else float(seed["sweep"]),
        None if seed["sweepAt"] is None else float(seed["sweepAt"]),
        bool(seed["sweepAtGiven"]),
    )
    efficiency = float(seed["e"])
    if not 0.0 < efficiency <= 1.0:
        raise DesignError("span efficiency must satisfy 0 < e <= 1")
    alpha = float(seed["alpha"])
    if not math.isfinite(alpha):
        raise DesignError("angle of attack must be finite")
    sweep_rad = 0.0 if plan.sweep_input is None else plan.sweep_input
    if source == "report824":
        assert polar is not None
        alpha_l0_deg = naca.zero_lift_deg(polar)
        alpha_l0 = math.radians(alpha_l0_deg)
        a0 = measured_a0(polar.alpha_deg, polar.cl, alpha_l0_deg)
        _stall_deg, clmax = naca.clmax(polar)
        cd0 = None
    else:
        cd0 = float(seed["cd0"])
        clmax = float(seed["clmaxTheory"])
        if not math.isfinite(cd0) or cd0 < 0.0:
            raise DesignError("zero-lift drag must be finite and >= 0")
        if not math.isfinite(clmax) or clmax <= 0.0:
            raise DesignError("section CLmax must be finite and > 0")
        alpha_l0 = naca4_zero_lift_angle(digits.m, digits.p)
        a0 = 2.0 * math.pi
    if a0 <= 0.0 or clmax <= 0.0:
        raise DesignError("section slope and maximum lift must be > 0")
    a0_eff = a0 * math.cos(sweep_rad)
    if a0_eff <= 0.0:
        raise DesignError("effective section slope must be > 0")
    slope = finite.wing_slope(a0_eff, plan.aspect_ratio, efficiency)
    alpha_stall = finite.stall_angle(alpha_l0, clmax, slope)
    stalled = alpha >= alpha_stall
    cl = clmax if stalled else finite.wing_lift(slope, alpha, alpha_l0)
    if source == "report824":
        assert polar is not None
        cd, clamped = cd_at_cl_clamped(polar, cl)
        try:
            section_cl = naca.cl_at(polar, math.degrees(alpha))
        except ValueError:
            section_cl = None
    else:
        cd = cd0
        clamped = False
        section_cl = 2.0 * math.pi * (alpha - alpha_l0)
        if section_cl > clmax:
            section_cl = clmax
    cdi = cl**2 / (math.pi * plan.aspect_ratio * efficiency)
    return {
        "ok": True,
        "data_source": source,
        "re_source": re_source(curves, seed["re"]),
        "designation": digits.designation,
        "Re": None if polar is None else polar.reynolds,
        "span": plan.span,
        "root": plan.root,
        "tip": plan.tip,
        "area": plan.area,
        "aspectRatio": plan.aspect_ratio,
        "taper": plan.taper,
        "mac": plan.mac,
        "yMac": plan.y_mac,
        "sweep": plan.sweep_input,
        "sweepAt": plan.sweep_at,
        "sweepAtSource": plan.sweep_at_source,
        "sweepLe": plan.sweep_le,
        "xLeMac": plan.x_le_mac,
        "a0": a0,
        "a0Eff": a0_eff,
        "a": slope,
        "alphaL0": alpha_l0,
        "CLmax": clmax,
        "e": efficiency,
        "CD0": cd0,
        "alpha": alpha,
        "alphaStall": alpha_stall,
        "stalled": stalled,
        "CL": cl,
        "CDi": cdi,
        "cd": cd,
        "CD": cd + cdi,
        "cdClamped": clamped,
        "alphaI": finite.induced_angle(cl, plan.aspect_ratio, efficiency),
        "sectionCl": section_cl,
    }


def build_pack() -> dict:
    catalog = naca.load_catalog()
    airfoils = {}
    for name, curves in catalog.items():
        airfoils[name] = [
            {
                "Re": curve.reynolds,
                "alpha_deg": list(curve.alpha_deg),
                "cl": list(curve.cl),
                "cl_polar": list(curve.cl_polar),
                "cd": list(curve.cd),
            }
            for curve in curves
        ]
    return {"defaultRe": naca.DEFAULT_RE, "airfoils": airfoils}


def read_lab_js() -> str:
    return "\n".join((SKILL_DIR / "js" / name).read_text(encoding="utf-8") for name in JS_FILES)


def embed_json(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def bake_html(seed: dict, pack: dict) -> str:
    template = (SKILL_DIR / "viewer" / "template.html").read_text(encoding="utf-8")
    html = template.replace("__TITLE__", PLOT_TITLE)
    html = html.replace("__POLAR_PACK__", embed_json(pack))
    html = html.replace("__SEED_JSON__", embed_json(seed))
    html = html.replace("__LAB_JS__", read_lab_js().replace("</", "<\\/"))
    leftover = ("__TITLE__", "__POLAR_PACK__", "__SEED_JSON__", "__LAB_JS__")
    if any(token in html for token in leftover):
        raise DesignError("viewer template still contains a placeholder")
    return html


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise DesignError("matplotlib is required to sketch the wing") from exc
    return plt


def write_png(path: Path, result: dict) -> None:
    plt = ensure_matplotlib()
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    half = result["span"] / 2.0
    tip_le = half * math.tan(result["sweepLe"])
    outline_y = [0.0, half, half, 0.0, -half, -half, 0.0]
    outline_x = [
        0.0,
        tip_le,
        tip_le + result["tip"],
        result["root"],
        tip_le + result["tip"],
        tip_le,
        0.0,
    ]
    axes[0].fill(outline_y, outline_x, color="#d6eaf8", zorder=1)
    axes[0].plot(outline_y, outline_x, color="#1b2631", lw=1.2)
    axes[0].plot(
        [result["yMac"], result["yMac"]],
        [result["xLeMac"], result["xLeMac"] + result["mac"]],
        color="#1a5276",
        lw=2.0,
    )
    x_lo = min(outline_x)
    x_hi = max(outline_x)
    arrow_span = -half - 0.18 * result["span"]
    axes[0].annotate(
        "",
        xy=(arrow_span, x_hi),
        xytext=(arrow_span, x_lo),
        arrowprops={"arrowstyle": "-|>", "color": "#922b21", "lw": 1.4},
    )
    axes[0].text(
        arrow_span,
        x_lo,
        "airflow",
        color="#922b21",
        ha="center",
        va="bottom",
        fontsize=8,
    )
    axes[0].set_aspect("equal", adjustable="box")
    axes[0].set_xlim(-half * 1.45, half * 1.08)
    axes[0].set_ylim(x_lo - 0.25 * result["root"], x_hi + 0.12 * result["root"])
    axes[0].invert_yaxis()
    axes[0].set_xlabel("span, m")
    axes[0].set_ylabel("chord, m aft")
    axes[0].set_title("planform")
    alphas = []
    lifts = []
    span = result["alphaStall"] - result["alphaL0"]
    for i in range(81):
        angle = result["alphaL0"] + span * i / 80.0
        alphas.append(math.degrees(angle))
        lifts.append(finite.wing_lift(result["a"], angle, result["alphaL0"]))
    axes[1].plot(alphas, lifts, color="#1a5276", lw=1.6)
    axes[1].scatter(
        [math.degrees(result["alpha"])],
        [result["CL"]],
        color="#1a5276",
        zorder=3,
    )
    axes[1].set_xlabel("angle of attack, deg")
    axes[1].set_ylabel("wing CL")
    axes[1].set_title("wing CL versus angle of attack")
    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def emit(result: dict, png: Path, html: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("data_source", result["data_source"])
    print_kv("re_source", result["re_source"])
    print_kv("designation", result["designation"])
    print_kv("Re", result["Re"])
    print_kv("span_m", result["span"])
    print_kv("root_m", result["root"])
    print_kv("tip_m", result["tip"])
    print_kv("S_m2", result["area"])
    print_kv("AR", result["aspectRatio"])
    print_kv("taper", result["taper"])
    print_kv("MAC_m", result["mac"])
    print_kv("y_MAC_m", result["yMac"])
    print_kv("sweep_rad", result["sweep"])
    print_kv("sweep_at", result["sweepAt"])
    print_kv("sweep_at_source", result["sweepAtSource"])
    print_kv("sweep_le_rad", result["sweepLe"])
    print_kv("a0_per_rad", result["a0"])
    print_kv("a0_eff_per_rad", result["a0Eff"])
    print_kv("a_per_rad", result["a"])
    print_kv("alpha_L0_rad", result["alphaL0"])
    print_kv("CLmax", result["CLmax"])
    print_kv("e", result["e"])
    print_kv("CD0", result["CD0"])
    print_kv("alpha_rad", result["alpha"])
    print_kv("CL", result["CL"])
    print_kv("CDi", result["CDi"])
    print_kv("cd_profile", result["cd"])
    print_kv("CD", result["CD"])
    print_kv("alpha_i_rad", result["alphaI"])
    print_kv("stalled", result["stalled"])
    print_kv("cd_clamped", result["cdClamped"])
    print_kv(
        "cosine_sweep",
        "a0_eff = a0*cos(sweep) before wing_lift_curve_slope; not a catalogue identity",
    )
    print_kv("graph", str(png.resolve()))
    print_kv("viewer", str(html.resolve()))


def seed_from_args(ns: argparse.Namespace) -> dict:
    if ns.sweep is None and ns.sweep_at is not None:
        raise DesignError("pass --sweep when --sweep-at is set")
    seed = default_seed()
    seed["naca"] = ns.naca
    seed["re"] = ns.re
    seed["span"] = ns.span
    seed["root"] = ns.root
    seed["tip"] = ns.tip
    seed["sweep"] = ns.sweep
    seed["sweepAt"] = ns.sweep_at
    seed["sweepAtGiven"] = ns.sweep_at is not None
    seed["e"] = ns.e
    seed["cd0"] = ns.cd0
    seed["clmaxTheory"] = ns.clmax
    seed["alpha"] = ns.alpha
    return seed


def _close(actual: object, expected: object) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual is expected
    if actual is None or expected is None:
        return actual is None and expected is None
    if isinstance(actual, str) or isinstance(expected, str):
        return actual == expected
    scale = max(abs(float(actual)), abs(float(expected)), 1.0)
    return abs(float(actual) - float(expected)) <= 1e-5 * scale


PARITY_KEYS = (
    "ok",
    "data_source",
    "re_source",
    "designation",
    "Re",
    "area",
    "aspectRatio",
    "taper",
    "mac",
    "yMac",
    "sweepLe",
    "a0",
    "a0Eff",
    "a",
    "alphaL0",
    "CLmax",
    "e",
    "CL",
    "CDi",
    "cd",
    "CD",
    "alphaI",
    "stalled",
    "cdClamped",
    "sectionCl",
)


def node_parity(pack: dict, cases: list[tuple[str, dict, dict]]) -> str:
    node = shutil.which("node")
    if node is None:
        return "skipped"
    runner = r"""
const vm = require("vm");
const fs = require("fs");
const code = fs.readFileSync(process.argv[2], "utf8");
const payload = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const context = { Math: Math, console: console, isFinite: isFinite };
vm.createContext(context);
vm.runInContext(code, context);
const designs = payload.cases.map(function (item) {
  return context.Lab.evaluate(item.seed, payload.pack);
});
process.stdout.write(JSON.stringify({ designs: designs }));
"""
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        script = root / "run.js"
        payload = root / "payload.json"
        source = root / "lab.js"
        script.write_text(runner, encoding="utf-8")
        source.write_text(read_lab_js(), encoding="utf-8")
        payload.write_text(
            json.dumps(
                {
                    "pack": pack,
                    "cases": [{"name": name, "seed": seed} for name, seed, _expected in cases],
                }
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [node, str(script), str(source), str(payload)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise DesignError(completed.stderr.strip() or "node parity failed")
        report = json.loads(completed.stdout)
    for (name, _seed, expected), got in zip(cases, report["designs"]):
        if not got.get("ok"):
            raise DesignError(f"{name} JS design failed: {got.get('error')}")
        for key in PARITY_KEYS:
            if not _close(got.get(key), expected.get(key)):
                raise DesignError(
                    f"{name} {key}: JS {got.get(key)!r} != Python {expected.get(key)!r}"
                )
    return "pass"


def run_check() -> int:
    catalog = naca.load_catalog()
    chart = design_point(default_seed(), catalog)
    if not chart["ok"]:
        print(f"CHECK FAIL: {chart['error']}", file=sys.stderr)
        return 1
    digits = naca.parse_designation("2412")
    polar = naca.polar_for(digits, catalog, None)
    alpha_l0 = math.radians(naca.zero_lift_deg(polar))
    _alpha_stall, clmax = naca.clmax(polar)
    if not _close(chart["alphaL0"], alpha_l0) or not _close(chart["CLmax"], clmax):
        print("CHECK FAIL: 2412 zero-lift or cl,max does not match the NACA program", file=sys.stderr)
        return 1
    if chart["data_source"] != "report824" or chart["re_source"] != "nearest_6e6":
        print("CHECK FAIL: 2412 did not open on the nearest 6e6 chart", file=sys.stderr)
        return 1
    plan = winggeo.planform_from(10.0, 1.5, 1.0, None, None, False)
    if not _close(chart["mac"], plan.mac) or not _close(chart["yMac"], plan.y_mac):
        print("CHECK FAIL: MAC does not match WingGeometry", file=sys.stderr)
        return 1
    unswept = finite.wing_slope(chart["a0"], plan.aspect_ratio, 1.0)
    if not _close(chart["a"], unswept):
        print("CHECK FAIL: unswept wing slope does not match wing_lift_curve_slope", file=sys.stderr)
        return 1
    theory = default_seed()
    theory["naca"] = "0015"
    theory_point = design_point(theory, catalog)
    if not theory_point["ok"]:
        print(f"CHECK FAIL: {theory_point['error']}", file=sys.stderr)
        return 1
    if theory_point["data_source"] != "thin_airfoil":
        print("CHECK FAIL: 0015 stayed on a chart", file=sys.stderr)
        return 1
    if not _close(theory_point["a0"], 2.0 * math.pi) or not _close(theory_point["alphaL0"], 0.0):
        print("CHECK FAIL: 0015 is not 2π at zero lift", file=sys.stderr)
        return 1
    camber = default_seed()
    camber["naca"] = "2212"
    camber_point = design_point(camber, catalog)
    if not camber_point["ok"]:
        print(f"CHECK FAIL: {camber_point['error']}", file=sys.stderr)
        return 1
    if not _close(camber_point["alphaL0"], catalogue_zero_lift(0.02, 0.2)):
        print("CHECK FAIL: 2212 zero-lift does not match naca4_zero_lift_angle", file=sys.stderr)
        return 1
    swept = default_seed()
    swept["naca"] = "0015"
    swept["sweep"] = 0.3
    swept_point = design_point(swept, catalog)
    if not swept_point["ok"]:
        print(f"CHECK FAIL: {swept_point['error']}", file=sys.stderr)
        return 1
    swept_plan = winggeo.planform_from(10.0, 1.5, 1.0, 0.3, None, False)
    swept_slope = finite.wing_slope(2.0 * math.pi * math.cos(0.3), swept_plan.aspect_ratio, 1.0)
    if not _close(swept_point["a"], swept_slope) or not _close(swept_point["mac"], swept_plan.mac):
        print("CHECK FAIL: swept slope or MAC does not match the wing programs", file=sys.stderr)
        return 1
    if not _close(swept_point["CDi"], swept_point["CL"] ** 2 / (math.pi * swept_point["aspectRatio"] * swept_point["e"])):
        print("CHECK FAIL: induced drag is not CL^2/(pi*AR*e)", file=sys.stderr)
        return 1
    outside = default_seed()
    outside["re"] = 1.0e5
    outside_point = design_point(outside, catalog)
    if outside_point["ok"]:
        print("CHECK FAIL: Reynolds number outside the chart was accepted", file=sys.stderr)
        return 1
    blended = default_seed()
    blended["re"] = 4.0e6
    blended_point = design_point(blended, catalog)
    blend_polar = naca.polar_for(digits, catalog, 4.0e6)
    if not blended_point["ok"] or not _close(blended_point["alphaL0"], math.radians(naca.zero_lift_deg(blend_polar))):
        print("CHECK FAIL: blended 2412 zero-lift does not match the NACA program", file=sys.stderr)
        return 1
    pack = build_pack()
    with tempfile.TemporaryDirectory() as folder:
        html = bake_html(default_seed(), pack)
        if any(token in html for token in ("__TITLE__", "__POLAR_PACK__", "__SEED_JSON__", "__LAB_JS__")):
            print("CHECK FAIL: placeholder left in HTML", file=sys.stderr)
            return 1
        if "<script src=" in html.lower():
            print("CHECK FAIL: HTML loads an external script", file=sys.stderr)
            return 1
        if "addEventListener" not in html or "3100000" not in html:
            print("CHECK FAIL: HTML is missing the polar pack or live inputs", file=sys.stderr)
            return 1
        (Path(folder) / "lab.html").write_text(html, encoding="utf-8")
    try:
        parity = node_parity(
            pack,
            [
                ("2412", default_seed(), chart),
                ("0015", theory, theory_point),
                ("swept", swept, swept_point),
                ("blend", blended, blended_point),
            ],
        )
    except DesignError as exc:
        print(f"CHECK FAIL: {exc}", file=sys.stderr)
        return 1
    print("check: pass")
    print_kv("node_parity", parity)
    print_kv("data_source", chart["data_source"])
    print_kv("alpha_L0_rad", chart["alphaL0"])
    print_kv("CLmax", chart["CLmax"])
    print_kv("a_per_rad", chart["a"])
    print_kv("MAC_m", chart["mac"])
    print_kv("thin_a0", theory_point["a0"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bake an interactive wing and airfoil design page.")
    parser.add_argument("--naca", default="2412", help="four-digit designation")
    parser.add_argument("--re", type=float, default=None, help="chord Reynolds number")
    parser.add_argument("--span", type=float, default=10.0, help="span [m]")
    parser.add_argument("--root", type=float, default=1.5, help="root chord [m]")
    parser.add_argument("--tip", type=float, default=1.0, help="tip chord [m]")
    parser.add_argument("--sweep", type=float, default=None, help="sweep of --sweep-at [rad]")
    parser.add_argument("--sweep-at", type=float, default=None, help="chord fraction of the sweep")
    parser.add_argument("--e", type=float, default=1.0, help="span efficiency")
    parser.add_argument("--cd0", type=float, default=0.008, help="thin-airfoil zero-lift drag")
    parser.add_argument("--clmax", type=float, default=1.2, help="thin-airfoil section CLmax")
    parser.add_argument("--alpha", type=float, default=math.radians(4.0), help="marked angle of attack [rad]")
    parser.add_argument("--out", type=str, default=None, help="PNG path; HTML uses the same stem")
    parser.add_argument("--open", action="store_true", help="open the HTML viewer in a browser")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        seed = seed_from_args(args)
        result = design_point(seed)
    except DesignError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not result["ok"]:
        print(f"error: {result['error']}", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else SKILL_DIR / "wing_airfoil_design.png"
    if out.suffix.lower() != ".png":
        out = out.with_suffix(".png")
    html_path = out.with_suffix(".html")
    try:
        write_png(out, result)
        html_path.write_text(bake_html(seed, build_pack()), encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out, html_path)
    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
