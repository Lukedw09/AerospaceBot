#!/usr/bin/env python3
"""Bake a self-contained solid-motor grain lab.

The HTML page recomputes in the browser. This program seeds that page and
prints the same initial point.
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

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SKILL_DIR = Path(__file__).resolve().parent
ROOT = SKILL_DIR.parent
sys.path.insert(0, str(ROOT / "ROCKET - CircularPortGrainHistory"))
sys.path.insert(0, str(ROOT / "ROCKET - ChamberVolumeAndCaseHoopStress"))

import chamber_case  # noqa: E402
import circular_port_grain_history as grain  # noqa: E402

PLOT_TITLE = "Solid motor grain lab"
JS_FILES = (
    "solid_params.js",
    "case_hoop.js",
    "grain_history.js",
    "lab.js",
)
DEFAULT_PORT = 0.05
DEFAULT_LENGTH = 1.0
DEFAULT_WEB = 0.08
DEFAULT_KN = 120.0
DEFAULT_RHO = 1800.0
DEFAULT_CSTAR = 1550.0
DEFAULT_BURN_S = 10.0
ASSUMPTIONS = (
    "interactive circular-port grain lab seed; inhibited ends; "
    "Ab = 2*pi*r*L; Ro = Rp + web; Kn = Ab0/At so At = Ab0/Kn; "
    "rburn = a*pc**n; pc = (K*a*rho_b*c*)**(1/(1-n)); "
    "K = Ab/At at the instantaneous port; "
    "case hoop uses Ro as the case radius, sigma_h = pc*Ro/t; "
    "MS = allowable/sigma_h - 1 at peak pc; "
    "sections show ignition geometry; "
    "constant a, n, rho_b, and c*; quasi-steady mass balance; "
    "no erosive burning; n < 1; optional sliver percent stops the history; "
    "the HTML page recomputes these relations in the browser"
)


class DesignError(Exception):
    """The seed is not a usable grain point."""


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def default_a() -> float:
    """Saint Robert a for a 10 s burn at n = 1/2 on the default grain."""
    outer = DEFAULT_PORT + DEFAULT_WEB
    numer = math.log(outer / DEFAULT_PORT) * DEFAULT_PORT
    denom = DEFAULT_BURN_S * DEFAULT_KN * DEFAULT_RHO * DEFAULT_CSTAR
    return math.sqrt(numer / denom)


def default_seed() -> dict:
    return {
        "web": DEFAULT_WEB,
        "port": DEFAULT_PORT,
        "kn": DEFAULT_KN,
        "length": DEFAULT_LENGTH,
        "a": default_a(),
        "n": 0.5,
        "rho": DEFAULT_RHO,
        "cstar": DEFAULT_CSTAR,
        "thickness": 0.008,
        "allowable": 2.5e8,
        "sliver": 0.0,
    }


def _positive(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DesignError(f"{name} must be finite and > 0")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise DesignError(f"{name} must be finite and > 0")
    return number


def evaluate(seed: dict) -> dict:
    """Grain point. Field names match Lab.evaluate in js/lab.js."""
    web = _positive("web", seed["web"])
    port = _positive("port radius", seed["port"])
    kn = _positive("Kn", seed["kn"])
    length = _positive("grain length", seed["length"])
    a = _positive("burn-rate coefficient", seed["a"])
    n = float(seed["n"])
    rho = _positive("propellant density", seed["rho"])
    cstar = _positive("c*", seed["cstar"])
    thickness = _positive("wall thickness", seed["thickness"])
    allowable = _positive("allowable stress", seed["allowable"])
    sliver_percent = float(seed["sliver"])
    if not math.isfinite(n) or n >= 1.0:
        raise DesignError("burn-rate exponent n must be finite and < 1")
    if not math.isfinite(sliver_percent) or sliver_percent < 0.0 or sliver_percent >= 100.0:
        raise DesignError("sliver percent must be finite and in [0, 100)")
    outer = port + web
    sliver = sliver_percent / 100.0
    ab0 = grain.circular_port_burning_area(port, length)
    throat = ab0 / kn
    grain.validate_ballistics(a, n, throat, rho, cstar)
    burning_area_ratio, equilibrium_chamber_pressure, burn_rate = grain.load_solid()
    hist = grain.history(
        a,
        n,
        throat,
        rho,
        cstar,
        port,
        length,
        outer,
        sliver,
        burning_area_ratio,
        equilibrium_chamber_pressure,
        burn_rate,
    )
    pcs = list(hist["pc"])
    hoop = [chamber_case.hoop_stress(pc, outer, thickness) for pc in pcs]
    margin = [chamber_case.margin_of_safety(allowable, stress) for stress in hoop]
    i_max = max(range(len(pcs)), key=pcs.__getitem__)
    return {
        "ok": True,
        "error": None,
        "web": web,
        "port": port,
        "kn": kn,
        "length": length,
        "a": a,
        "n": n,
        "rho": rho,
        "cstar": cstar,
        "thickness": thickness,
        "allowable": allowable,
        "sliver": sliver,
        "sliverPercent": sliver_percent,
        "Ro": outer,
        "At": throat,
        "Ab0": ab0,
        "w0": hist["w0_m"],
        "tBurn": hist["t_burn_s"],
        "KInitial": hist["K_initial"],
        "KBurnout": hist["K_burnout"],
        "pcInitial": hist["pc_initial_Pa"],
        "pcBurnout": hist["pc_burnout_Pa"],
        "pcMax": pcs[i_max],
        "wremBurnout": hist["wrem_end_m"],
        "AbBurnout": hist["Ab_burnout_m2"],
        "rEnd": hist["r_end_m"],
        "hoopMax": hoop[i_max],
        "marginMin": margin[i_max],
        "thinWall": chamber_case.thin_wall(outer, thickness),
        "tOverR": thickness / outer,
        "nSamples": len(hist["times"]),
        "times": list(hist["times"]),
        "pc": pcs,
        "Ab": list(hist["Ab"]),
        "wrem": list(hist["wrem"]),
        "K": list(hist["K"]),
        "radius": list(hist["radius"]),
        "hoop": hoop,
        "margin": margin,
    }


def design_point(seed: dict) -> dict:
    try:
        return evaluate(seed)
    except (DesignError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


def read_lab_js() -> str:
    parts = []
    for name in JS_FILES:
        parts.append((SKILL_DIR / "js" / name).read_text(encoding="utf-8"))
    return "\n".join(parts)


def embed_json(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def bake_html(seed: dict) -> str:
    template = (SKILL_DIR / "viewer" / "template.html").read_text(encoding="utf-8")
    html = template.replace("__TITLE__", PLOT_TITLE)
    html = html.replace("__SEED_JSON__", embed_json(seed))
    html = html.replace("__LAB_JS__", read_lab_js().replace("</", "<\\/"))
    if "__TITLE__" in html or "__SEED_JSON__" in html or "__LAB_JS__" in html:
        raise DesignError("viewer template still contains a placeholder")
    return html


def _draw_lateral(ax, result: dict) -> None:
    outer = result["Ro"] + result["thickness"]
    case = plt.Circle((0.0, 0.0), outer, color="#1b2631")
    grain_disk = plt.Circle((0.0, 0.0), result["Ro"], color="#c4a574")
    port = plt.Circle((0.0, 0.0), result["port"], color="#f7f9fb")
    ax.add_patch(case)
    ax.add_patch(grain_disk)
    ax.add_patch(port)
    ax.set_aspect("equal", adjustable="box")
    limit = outer * 1.08
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_title("Lateral section")
    ax.set_xlabel("radius [m]")


def _draw_longitudinal(ax, result: dict) -> None:
    length = result["length"]
    outer = result["Ro"] + result["thickness"]
    cap = min(0.03 * length, 0.02)
    ax.add_patch(plt.Rectangle((0.0, -outer), length, 2.0 * outer, color="#1b2631"))
    ax.add_patch(plt.Rectangle((0.0, -result["Ro"]), length, 2.0 * result["Ro"], color="#c4a574"))
    ax.add_patch(plt.Rectangle((0.0, -result["port"]), length, 2.0 * result["port"], color="#f7f9fb"))
    web = result["Ro"] - result["port"]
    for x0, y0 in (
        (0.0, result["port"]),
        (0.0, -result["Ro"]),
        (length - cap, result["port"]),
        (length - cap, -result["Ro"]),
    ):
        ax.add_patch(plt.Rectangle((x0, y0), cap, web, color="#7b241c"))
    ax.axhline(0.0, color="#7f8c8d", lw=0.8, ls="--")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlim(-0.02 * length, length * 1.02)
    ax.set_ylim(-outer * 1.35, outer * 1.35)
    ax.set_title("Longitudinal section")
    ax.set_xlabel("length [m]")


def write_png(path: Path, result: dict) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 8.2))
    _draw_lateral(axes[0, 0], result)
    _draw_longitudinal(axes[0, 1], result)
    axes[1, 0].plot(result["times"], result["pc"], color="#1a5276", linewidth=1.8)
    axes[1, 0].set_title("Chamber pressure")
    axes[1, 0].set_xlabel("time [s]")
    axes[1, 0].set_ylabel("pc [Pa]")
    axes[1, 0].grid(True, alpha=0.35)
    axes[1, 1].plot(result["times"], result["Ab"], color="#117a65", linewidth=1.8)
    axes[1, 1].set_title("Burn area")
    axes[1, 1].set_xlabel("time [s]")
    axes[1, 1].set_ylabel("Ab [m²]")
    axes[1, 1].grid(True, alpha=0.35)
    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(result: dict, png: Path, html: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("a", result["a"])
    print_kv("n", result["n"])
    print_kv("rho_b_kg_m3", result["rho"])
    print_kv("cstar_m_s", result["cstar"])
    print_kv("web_m", result["web"])
    print_kv("Rp_m", result["port"])
    print_kv("Ro_m", result["Ro"])
    print_kv("L_m", result["length"])
    print_kv("Kn", result["kn"])
    print_kv("At_m2", result["At"])
    print_kv("Ab0_m2", result["Ab0"])
    print_kv("w0_m", result["w0"])
    print_kv("sliver_percent", result["sliverPercent"])
    print_kv("t_burn_s", result["tBurn"])
    print_kv("K_initial", result["KInitial"])
    print_kv("K_burnout", result["KBurnout"])
    print_kv("pc_initial_Pa", result["pcInitial"])
    print_kv("pc_burnout_Pa", result["pcBurnout"])
    print_kv("pc_max_Pa", result["pcMax"])
    print_kv("Ab_burnout_m2", result["AbBurnout"])
    print_kv("wrem_burnout_m", result["wremBurnout"])
    print_kv("case_thickness_m", result["thickness"])
    print_kv("allowable_Pa", result["allowable"])
    print_kv("t_over_R", result["tOverR"])
    print_kv("thin_wall", result["thinWall"])
    print_kv("hoop_max_Pa", result["hoopMax"])
    print_kv("margin_at_pc_max", result["marginMin"])
    print_kv("n_samples", result["nSamples"])
    print_kv("graph", str(png.resolve()))
    print_kv("viewer", str(html.resolve()))


def seed_from_args(ns: argparse.Namespace) -> dict:
    seed = default_seed()
    seed["web"] = ns.web
    seed["port"] = ns.port
    seed["kn"] = ns.kn
    seed["length"] = ns.length
    seed["a"] = ns.a
    seed["n"] = ns.n
    seed["rho"] = ns.rho
    seed["cstar"] = ns.cstar
    seed["thickness"] = ns.thickness
    seed["allowable"] = ns.allowable
    seed["sliver"] = ns.sliver
    return seed


def _close(actual: object, expected: object) -> bool:
    if isinstance(actual, str) or isinstance(expected, str):
        return actual == expected
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual is expected
    scale = max(abs(float(actual)), abs(float(expected)), 1.0)
    return abs(float(actual) - float(expected)) <= 1e-5 * scale


PARITY_KEYS = (
    "ok",
    "Ro",
    "At",
    "Ab0",
    "tBurn",
    "pcInitial",
    "pcBurnout",
    "pcMax",
    "wremBurnout",
    "AbBurnout",
    "KInitial",
    "KBurnout",
    "hoopMax",
    "marginMin",
    "thinWall",
    "nSamples",
)


def node_parity(cases: list[tuple[str, dict, dict]]) -> str:
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
  return context.Lab.computeDesign(item.seed);
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
            json.dumps({"cases": [{"name": name, "seed": seed} for name, seed, _expected in cases]}),
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
        for series in ("times", "pc", "Ab", "wrem", "margin"):
            js_series = got.get(series) or []
            py_series = expected.get(series) or []
            if len(js_series) != len(py_series):
                raise DesignError(f"{name} {series} length {len(js_series)} != {len(py_series)}")
            for index in (0, 100, len(py_series) - 1):
                if not _close(js_series[index], py_series[index]):
                    raise DesignError(
                        f"{name} {series}[{index}]: JS {js_series[index]!r} != Python {py_series[index]!r}"
                    )
    return "pass"


def run_check() -> int:
    seed = default_seed()
    point = design_point(seed)
    if not point["ok"]:
        print(f"CHECK FAIL: {point['error']}", file=sys.stderr)
        return 1
    if not _close(point["tBurn"], DEFAULT_BURN_S):
        print(f"CHECK FAIL: t_burn = {point['tBurn']}, expected {DEFAULT_BURN_S}", file=sys.stderr)
        return 1
    if not _close(point["Ro"], DEFAULT_PORT + DEFAULT_WEB):
        print("CHECK FAIL: outer radius is not port plus web", file=sys.stderr)
        return 1
    if point["marginMin"] <= 0.0 or point["thinWall"] != "yes":
        print("CHECK FAIL: default case is not a thin wall with positive margin", file=sys.stderr)
        return 1
    if point["nSamples"] != grain.N_CURVE:
        print("CHECK FAIL: sample count is not the grain-history curve length", file=sys.stderr)
        return 1
    if point["times"][0] != 0.0:
        print("CHECK FAIL: history must start at t = 0", file=sys.stderr)
        return 1
    burning_area_ratio, equilibrium_chamber_pressure, burn_rate = grain.load_solid()
    hist = grain.history(
        seed["a"],
        seed["n"],
        point["At"],
        seed["rho"],
        seed["cstar"],
        seed["port"],
        seed["length"],
        point["Ro"],
        0.0,
        burning_area_ratio,
        equilibrium_chamber_pressure,
        burn_rate,
    )
    if not _close(point["tBurn"], hist["t_burn_s"]):
        print("CHECK FAIL: burn time does not match circular_port_grain_history", file=sys.stderr)
        return 1
    if not _close(point["pcInitial"], hist["pc_initial_Pa"]):
        print("CHECK FAIL: initial pc does not match circular_port_grain_history", file=sys.stderr)
        return 1
    if not _close(point["pc"][-1], hist["pc"][-1]):
        print("CHECK FAIL: burnout pc does not match circular_port_grain_history", file=sys.stderr)
        return 1
    if not _close(point["Ab"][100], hist["Ab"][100]):
        print("CHECK FAIL: burn area does not match circular_port_grain_history", file=sys.stderr)
        return 1
    hoop = chamber_case.hoop_stress(point["pcMax"], point["Ro"], point["thickness"])
    margin = chamber_case.margin_of_safety(point["allowable"], hoop)
    if not _close(point["hoopMax"], hoop) or not _close(point["marginMin"], margin):
        print("CHECK FAIL: hoop or margin does not match chamber_case", file=sys.stderr)
        return 1
    sliver_seed = default_seed()
    sliver_seed["sliver"] = 25.0
    sliver_point = design_point(sliver_seed)
    if not sliver_point["ok"]:
        print(f"CHECK FAIL: {sliver_point['error']}", file=sys.stderr)
        return 1
    if not (sliver_point["tBurn"] < point["tBurn"]):
        print("CHECK FAIL: sliver must shorten the burn", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        html = bake_html(seed)
        (root / "lab.html").write_text(html, encoding="utf-8")
        if any(token in html for token in ("__TITLE__", "__SEED_JSON__", "__LAB_JS__")):
            print("CHECK FAIL: placeholder left in HTML", file=sys.stderr)
            return 1
        if "<script src=" in html.lower():
            print("CHECK FAIL: HTML loads an external script", file=sys.stderr)
            return 1
        if "addEventListener" not in html or 'id="lateral"' not in html:
            print("CHECK FAIL: HTML is missing the live grain panels", file=sys.stderr)
            return 1
        png = root / "grain.png"
        write_png(png, point)
        if not png.is_file() or png.stat().st_size < 8:
            print("CHECK FAIL: PNG was not written", file=sys.stderr)
            return 1
    try:
        parity = node_parity([("seed", seed, point), ("sliver", sliver_seed, sliver_point)])
    except DesignError as exc:
        print(f"CHECK FAIL: {exc}", file=sys.stderr)
        return 1
    print("check: pass")
    print_kv("node_parity", parity)
    print_kv("At_m2", point["At"])
    print_kv("t_burn_s", point["tBurn"])
    print_kv("pc_max_Pa", point["pcMax"])
    print_kv("margin_at_pc_max", point["marginMin"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    seed = default_seed()
    parser = argparse.ArgumentParser(
        description="Bake an interactive solid-motor circular-port grain page."
    )
    parser.add_argument("--web", type=float, default=seed["web"], help="initial web [m]")
    parser.add_argument("--port", type=float, default=seed["port"], help="initial port radius [m]")
    parser.add_argument("--kn", type=float, default=seed["kn"], help="ignition burning-area ratio Kn")
    parser.add_argument("--length", type=float, default=seed["length"], help="grain length [m]")
    parser.add_argument("--a", type=float, default=seed["a"], help="burn-rate coefficient a [m/(s·Pa^n)]")
    parser.add_argument("--n", type=float, default=seed["n"], help="burn-rate pressure exponent n")
    parser.add_argument("--rho", type=float, default=seed["rho"], help="propellant density [kg/m^3]")
    parser.add_argument("--cstar", type=float, default=seed["cstar"], help="characteristic velocity [m/s]")
    parser.add_argument("--thickness", type=float, default=seed["thickness"], help="case wall thickness [m]")
    parser.add_argument("--allowable", type=float, default=seed["allowable"], help="allowable case stress [Pa]")
    parser.add_argument("--sliver", type=float, default=seed["sliver"], help="sliver volume percent")
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
    out = Path(args.out) if args.out else SKILL_DIR / "solid_motor_grain_lab.png"
    if out.suffix.lower() != ".png":
        out = out.with_suffix(".png")
    html_path = out.with_suffix(".html")
    try:
        write_png(out, result)
        html_path.write_text(bake_html(seed), encoding="utf-8")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out, html_path)
    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
