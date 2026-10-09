#!/usr/bin/env python3
"""Bake an interactive compressible-flow classroom page.

The HTML recomputes isentropic stagnation, a normal shock, a wedge, a cone,
a diamond airfoil, Fanno and Rayleigh ducts, Prandtl-Glauert, and a pitot
Mach in the browser. This program does not replace those one-shot skills.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Compressible flow lab"
JS_FILES = (
    "isentropic.js",
    "normal_shock.js",
    "prandtl_meyer.js",
    "conical_shock.js",
    "diamond_airfoil.js",
    "fanno_rayleigh.js",
    "prandtl_glauert.js",
    "rayleigh_pitot.js",
    "lab.js",
)
MODES = (
    "isentropic",
    "normal",
    "wedge",
    "cone",
    "diamond",
    "fanno",
    "rayleigh",
    "prandtl_glauert",
    "rayleigh_pitot",
)
ASSUMPTIONS = (
    "calorically perfect gas; the page overlays the one-shot compressible skills "
    "and does not replace them; an omitted gamma is 1.4; angles are radians on "
    "the CLI and degrees on the page; Prandtl-Glauert uses user coefficients only "
    "and does not divide drag by beta; duct lines are contours of the stream "
    "function, equally spaced because rho*V is constant in a constant-area duct; "
    "a detached shock does not invent a wave angle"
)


class DesignError(Exception):
    pass


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def _module(folder: str, name: str):
    path = str(SKILL_DIR.parent / folder)
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module(name)


def default_seed() -> dict:
    gamma = 1.4
    mach = 2.0
    ratio = (((gamma + 1.0) / 2.0) * mach * mach) ** (gamma / (gamma - 1.0)) * (
        (gamma + 1.0) / (2.0 * gamma * mach * mach - (gamma - 1.0))
    ) ** (1.0 / (gamma - 1.0))
    return {
        "mode": "wedge",
        "mach": mach,
        "delta": math.radians(10.0),
        "epsilon": math.radians(5.0),
        "alpha": math.radians(2.0),
        "gamma": gamma,
        "fld": None,
        "ttRatio": None,
        "clInc": 0.5,
        "cmInc": -0.05,
        "cdInc": 0.02,
        "cpminInc": -0.8,
        "pitot": ratio * 101325.0,
        "staticPressure": 101325.0,
        "temperature": None,
        "pressure": None,
        "density": None,
    }


def _panel(panel: dict | None) -> dict:
    if panel is None:
        return {"wave": None, "M": None, "p": None, "theta": None, "delta_max": None}
    return {
        "wave": panel.get("wave"),
        "M": panel.get("M"),
        "p": panel.get("p_over_pinf"),
        "theta": panel.get("theta"),
        "delta_max": panel.get("delta_max"),
    }


def design_point(seed: dict) -> dict:
    mode = seed["mode"]
    if mode not in MODES:
        return {"ok": False, "mode": mode, "error": "unknown mode"}
    gamma = float(seed["gamma"])
    try:
        if mode == "isentropic":
            iso = _module("AERO - IsentropicStagnation", "isentropic_stagnation")
            state = iso.stagnation_state(
                float(seed["mach"]),
                gamma,
                seed["temperature"],
                seed["pressure"],
                seed["density"],
            )
            state = dict(state)
            state.update(ok=True, mode=mode, error=None)
            return state
        if mode == "normal":
            shock = _module("AERO - NormalShock", "normal_shock")
            state = dict(shock.shock_state(float(seed["mach"]), gamma))
            state.update(ok=True, mode=mode, error=None)
            return state
        if mode == "wedge":
            wedge = _module("AERO - PrandtlMeyerAndShocks", "prandtl_meyer_and_shocks")
            wedge.require_inputs(float(seed["mach"]), gamma, float(seed["delta"]))
            state = dict(wedge.evaluate(float(seed["mach"]), gamma, float(seed["delta"])))
            state.update(ok=True, mode=mode, error=None)
            return state
        if mode == "cone":
            cone = _module("AERO - ConicalShock", "conical_shock")
            cone.require_inputs(float(seed["mach"]), gamma, float(seed["delta"]))
            state = dict(cone.evaluate(float(seed["mach"]), gamma, float(seed["delta"])))
            state.update(ok=True, mode=mode, error=None)
            return state
        if mode == "diamond":
            diamond = _module(
                "AERO - DiamondAirfoilShockExpansion",
                "diamond_airfoil_shock_expansion",
            )
            diamond.require_inputs(
                float(seed["mach"]),
                gamma,
                float(seed["epsilon"]),
                float(seed["alpha"]),
            )
            state = diamond.evaluate(
                float(seed["mach"]),
                gamma,
                float(seed["epsilon"]),
                float(seed["alpha"]),
            )
            upper = _panel(state["u1"])
            lower = _panel(state["l1"])
            upper_te = _panel(state["u2"])
            lower_te = _panel(state["l2"])
            return {
                "ok": True,
                "mode": mode,
                "error": None,
                "mach": state["mach"],
                "gamma": state["gamma"],
                "epsilon": state["epsilon"],
                "alpha": state["alpha"],
                "delta_u1": state["delta_u1"],
                "delta_l1": state["delta_l1"],
                "shoulder": state["shoulder"],
                "solution": state["solution"],
                "wave_u1": upper["wave"],
                "M_u1": upper["M"],
                "p_u1": upper["p"],
                "theta_u1": upper["theta"],
                "delta_max_u1": upper["delta_max"],
                "wave_l1": lower["wave"],
                "M_l1": lower["M"],
                "p_l1": lower["p"],
                "theta_l1": lower["theta"],
                "delta_max_l1": lower["delta_max"],
                "wave_u2": upper_te["wave"],
                "M_u2": upper_te["M"],
                "p_u2": upper_te["p"],
                "theta_u2": upper_te["theta"],
                "wave_l2": lower_te["wave"],
                "M_l2": lower_te["M"],
                "p_l2": lower_te["p"],
                "theta_l2": lower_te["theta"],
                "Cp_u1": state["Cp_u1"],
                "Cp_u2": state["Cp_u2"],
                "Cp_l1": state["Cp_l1"],
                "Cp_l2": state["Cp_l2"],
                "cn": state["cn"],
                "ca": state["ca"],
                "cl": state["cl"],
                "cd": state["cd"],
            }
        if mode in ("fanno", "rayleigh"):
            duct = _module("AERO - FannoAndRayleighFlow", "fanno_and_rayleigh_flow")
            state = dict(duct.duct_state(mode, float(seed["mach"]), gamma))
            state.update(
                ok=True,
                mode=mode,
                error=None,
                choked="yes" if abs(float(state["M"]) - 1.0) <= 1e-6 else "no",
                fld=None,
                four_f_L_remaining_over_D=None,
                tt_ratio=None,
                exit_mach=None,
                choked_by_length=None,
                choked_by_heat=None,
            )
            if mode == "fanno":
                state["Tt_over_Ttstar"] = None
            else:
                state["four_f_Lmax_over_D"] = None
            if mode == "fanno" and seed["fld"] is not None:
                exit_mach, choked = duct.fanno_exit_mach(
                    float(seed["mach"]), gamma, float(seed["fld"])
                )
                state["fld"] = float(seed["fld"])
                state["four_f_L_remaining_over_D"] = max(
                    0.0, float(state["four_f_Lmax_over_D"]) - float(seed["fld"])
                )
                state["choked_by_length"] = choked
                state["exit_mach"] = exit_mach
            if mode == "rayleigh" and seed["ttRatio"] is not None:
                exit_mach, choked = duct.rayleigh_exit_mach(
                    float(seed["mach"]), gamma, float(seed["ttRatio"])
                )
                state["tt_ratio"] = float(seed["ttRatio"])
                state["choked_by_heat"] = choked
                state["exit_mach"] = exit_mach
            return state
        if mode == "prandtl_glauert":
            pg = _module(
                "AERO - PrandtGlauertCorrectionandCriticalMach",
                "prandtl_glauert_correction_and_critical_mach",
            )
            state = dict(
                pg.correction_state(
                    float(seed["mach"]),
                    gamma,
                    seed["clInc"],
                    seed["cpminInc"],
                    seed["cmInc"],
                    seed["cdInc"],
                    "user",
                )
            )
            state.update(ok=True, mode=mode, error=None)
            return state
        if mode == "rayleigh_pitot":
            pitot = _module("AERO - RayleighPitotMach", "rayleigh_pitot_mach")
            state = dict(
                pitot.pitot_state(
                    float(seed["pitot"]), float(seed["staticPressure"]), gamma
                )
            )
            state.update(ok=True, mode=mode, error=None)
            return state
    except (ValueError, ImportError) as exc:
        return {"ok": False, "mode": mode, "error": str(exc)}
    return {"ok": False, "mode": mode, "error": "unknown mode"}


def read_lab_js() -> str:
    return "\n".join((SKILL_DIR / "js" / name).read_text(encoding="utf-8") for name in JS_FILES)


def embed_json(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def bake_html(seed: dict) -> str:
    template = (SKILL_DIR / "viewer" / "template.html").read_text(encoding="utf-8")
    html = template.replace("__TITLE__", PLOT_TITLE)
    html = html.replace("__SEED_JSON__", embed_json(seed))
    html = html.replace("__LAB_JS__", read_lab_js().replace("</", "<\\/"))
    if any(token in html for token in ("__TITLE__", "__SEED_JSON__", "__LAB_JS__")):
        raise DesignError("viewer template still contains a placeholder")
    return html


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise DesignError("matplotlib is required to sketch the flow") from exc
    return plt


def write_png(path: Path, result: dict) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(7.4, 4.4))
    mode = result.get("mode")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    if not result.get("ok"):
        ax.text(0.4, 3, result.get("error") or "not solved", color="#922b21")
    elif mode == "normal":
        ax.plot([1, 9], [4.2, 4.2], color="#1b2631", lw=2)
        ax.plot([1, 9], [1.8, 1.8], color="#1b2631", lw=2)
        ax.plot([5, 5], [1.8, 4.2], color="#922b21", lw=2.4)
        ax.annotate("", xy=(4.2, 3), xytext=(1.4, 3), arrowprops={"arrowstyle": "-|>", "color": "#1a5276"})
        ax.annotate("", xy=(8.2, 3), xytext=(5.6, 3), arrowprops={"arrowstyle": "-|>", "color": "#1a5276"})
        ax.text(1.2, 4.5, f"M1 {result['M1']:.3g}", fontsize=9)
        ax.text(5.3, 4.5, f"M2 {result['M2']:.3g}", fontsize=9)
        ax.text(1.2, 0.6, f"p2/p1 {result['p2_over_p1']:.3g}   pt2/pt1 {result['pt2_over_pt1']:.3g}", fontsize=9)
    elif mode in ("fanno", "rayleigh"):
        ax.plot([1, 9], [4.2, 4.2], color="#1b2631", lw=2)
        ax.plot([1, 9], [1.8, 1.8], color="#1b2631", lw=2)
        for y in (2.3, 3.0, 3.7):
            ax.annotate("", xy=(8.4, y), xytext=(1.4, y), arrowprops={"arrowstyle": "-|>", "color": "#1a5276"})
        title = "Fanno friction duct" if mode == "fanno" else "Rayleigh heat-addition duct"
        ax.text(1.2, 5.1, title, fontsize=11)
        ax.text(1.2, 0.7, f"M {result['M']:.3g}   V/V* {result['V_over_Vstar']:.3g}", fontsize=9)
    elif mode == "wedge":
        delta = float(result["delta"])
        ax.plot([2, 7, 2 + 5 * math.cos(delta)], [2, 2, 2 + 5 * math.sin(delta)], color="#1b2631")
        if result.get("attached") and result.get("theta") is not None:
            theta = float(result["theta"])
            ax.plot([2, 2 + 6 * math.cos(theta)], [2, 2 + 6 * math.sin(theta)], color="#922b21", lw=2)
            ax.text(1.2, 5.2, f"wedge  theta {math.degrees(theta):.2f} deg", fontsize=10)
        else:
            arc = [2 + 0.8 * math.cos(angle) for angle in (i * math.pi / 24 for i in range(8, 16))]
            arc_y = [2 + 0.8 * math.sin(angle) for angle in (i * math.pi / 24 for i in range(8, 16))]
            ax.plot(arc, arc_y, color="#922b21", lw=2, linestyle="--")
            ax.text(1.2, 5.2, "wedge  detached shock", fontsize=10)
    elif mode == "cone" and result.get("attached") and result.get("theta") is not None:
        delta = result["delta"]
        theta = result["theta"]
        ax.plot([2, 7, 7, 2], [3, 3 + 5 * math.tan(delta), 3 - 5 * math.tan(delta), 3], color="#1b2631")
        ax.plot([2, 2 + 6 * math.cos(theta)], [3, 3 + 6 * math.sin(theta)], color="#922b21", lw=2)
        ax.plot([2, 2 + 6 * math.cos(theta)], [3, 3 - 6 * math.sin(theta)], color="#922b21", lw=2)
        ax.text(1.2, 5.4, f"cone  Cp {result['Cp']:.3g}", fontsize=10)
    elif mode == "cone":
        arc = [2 + 1.2 * math.cos(angle) for angle in (i * math.pi / 24 for i in range(6, 19))]
        arc_y = [3 + 1.2 * math.sin(angle) for angle in (i * math.pi / 24 for i in range(6, 19))]
        ax.plot(arc, arc_y, color="#922b21", lw=2, linestyle="--")
        ax.text(1.2, 5.4, "cone  detached shock", fontsize=10)
    elif mode == "diamond":
        ax.plot([2, 5, 8, 5, 2], [3, 3.8, 3, 2.2, 3], color="#1b2631")
        ax.text(1.2, 5.2, f"diamond  {result['solution']}", fontsize=10)
        if result.get("cl") is not None:
            ax.text(1.2, 0.7, f"cl {result['cl']:.3g}   cd {result['cd']:.3g}", fontsize=9)
    elif mode == "rayleigh_pitot":
        ax.plot([1, 5], [3, 3], color="#1a5276")
        ax.plot([5, 5], [2.2, 3.8], color="#1b2631", lw=3)
        if result.get("branch") == "supersonic":
            ax.plot([4.4, 4.4], [2.2, 3.8], color="#922b21", lw=2)
        ax.text(1.2, 5.1, f"{result['branch']}   M {result['M']:.4g}", fontsize=10)
    elif mode == "isentropic":
        ax.plot([8, 8], [1, 5], color="#1b2631", lw=2)
        ax.annotate("", xy=(7.6, 3), xytext=(1.5, 4.2), arrowprops={"arrowstyle": "-|>", "color": "#1a5276"})
        ax.text(1.2, 0.7, f"pt/p {result['pt_over_p']:.3g}   Tt/T {result['Tt_over_T']:.3g}", fontsize=9)
    elif mode == "prandtl_glauert":
        ax.text(1.2, 4.2, f"beta {result['beta']:.4g}", fontsize=12)
        ax.text(1.2, 3.4, f"CL {result['CL']}", fontsize=11)
        critical = result.get("M_cr")
        if isinstance(critical, (int, float)) and math.isfinite(float(critical)):
            critical_text = f"Mcr {float(critical):.4g}"
        else:
            critical_text = "Mcr not defined"
        ax.text(1.2, 2.6, critical_text, fontsize=11)
        ax.text(1.2, 1.6, "Cd is not divided by beta", fontsize=9)
    else:
        ax.text(1.2, 3, mode or "lab", fontsize=12)
    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def emit(result: dict, png: Path, html: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", result.get("mode"))
    print_kv("ok", "yes" if result.get("ok") else "no")
    if result.get("error"):
        print_kv("error", result["error"])
    for key in (
        "M",
        "M1",
        "M2",
        "gamma",
        "attached",
        "shock",
        "theta",
        "solution",
        "p2_over_p1",
        "pt2_over_pt1",
        "ds_over_R",
        "Mc",
        "Cp",
        "cl",
        "cd",
        "T_over_Tstar",
        "V_over_Vstar",
        "four_f_Lmax_over_D",
        "Tt_over_Ttstar",
        "exit_mach",
        "choked_by_length",
        "choked_by_heat",
        "beta",
        "CL",
        "M_cr",
        "branch",
        "q",
        "pt_over_p",
        "Tt_over_T",
    ):
        if key in result and result[key] is not None:
            value = result[key]
            if isinstance(value, bool):
                value = "yes" if value else "no"
            print_kv(key, value)
    print_kv("graph", str(png.resolve()))
    print_kv("viewer", str(html.resolve()))


def seed_from_args(ns: argparse.Namespace) -> dict:
    seed = default_seed()
    if ns.mode is not None:
        seed["mode"] = ns.mode
    if ns.mach is not None:
        seed["mach"] = ns.mach
    if ns.delta is not None:
        seed["delta"] = ns.delta
    if ns.epsilon is not None:
        seed["epsilon"] = ns.epsilon
    if ns.alpha is not None:
        seed["alpha"] = ns.alpha
    if ns.gamma is not None:
        seed["gamma"] = ns.gamma
    if ns.fld is not None:
        seed["fld"] = ns.fld
    if ns.tt_ratio is not None:
        seed["ttRatio"] = ns.tt_ratio
    if ns.cl_inc is not None:
        seed["clInc"] = ns.cl_inc
    if ns.cm_inc is not None:
        seed["cmInc"] = ns.cm_inc
    if ns.cd_inc is not None:
        seed["cdInc"] = ns.cd_inc
    if ns.cpmin_inc is not None:
        seed["cpminInc"] = ns.cpmin_inc
    if ns.pitot is not None:
        seed["pitot"] = ns.pitot
    if ns.static is not None:
        seed["staticPressure"] = ns.static
    if ns.temperature is not None:
        seed["temperature"] = ns.temperature
    if ns.pressure is not None:
        seed["pressure"] = ns.pressure
    if ns.density is not None:
        seed["density"] = ns.density
    return seed


def _close(actual: object, expected: object) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual is expected
    if actual is None or expected is None:
        return actual is None and expected is None
    if isinstance(actual, str) or isinstance(expected, str):
        return actual == expected
    scale = max(abs(float(actual)), abs(float(expected)), 1.0)
    return abs(float(actual) - float(expected)) <= 2e-4 * scale


PARITY = {
    "isentropic": ("ok", "M", "Tt_over_T", "pt_over_p", "rhot_over_rho", "Tt", "a"),
    "normal": ("ok", "M1", "M2", "p2_over_p1", "T2_over_T1", "rho2_over_rho1", "pt2_over_pt1", "ds_over_R"),
    "wedge": ("ok", "attached", "shock", "theta", "M2", "p2_over_p1", "pm_M", "expansion", "fan", "delta_max"),
    "cone": ("ok", "attached", "shock", "theta", "Mc", "Cp", "pc_over_p1", "M2"),
    "diamond": ("ok", "solution", "cl", "cd", "p_u1", "p_l1", "wave_u1"),
    "fanno": ("ok", "T_over_Tstar", "V_over_Vstar", "four_f_Lmax_over_D", "exit_mach", "choked_by_length"),
    "rayleigh": ("ok", "T_over_Tstar", "Tt_over_Ttstar", "p_over_pstar", "exit_mach", "choked_by_heat"),
    "prandtl_glauert": ("ok", "beta", "CL", "Cd", "Cp_min", "M_cr", "supercritical"),
    "rayleigh_pitot": ("ok", "M", "q", "branch", "relation", "ratio"),
}


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
  try {
    return context.Lab.designPoint(item.seed);
  } catch (err) {
    return { ok: false, error: String(err) };
  }
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
        for key in PARITY[expected["mode"]]:
            if not _close(got.get(key), expected.get(key)):
                raise DesignError(
                    f"{name} {key}: JS {got.get(key)!r} != Python {expected.get(key)!r}"
                )
    return "pass"


def _case(mode: str, **overrides) -> dict:
    seed = default_seed()
    seed["mode"] = mode
    seed.update(overrides)
    return seed


def run_check() -> int:
    cases = [
        ("iso", _case("isentropic", mach=2.0, temperature=288.15, pressure=101325.0, density=1.225)),
        ("normal", _case("normal", mach=2.0)),
        ("wedge", _case("wedge")),
        ("detached", _case("wedge", delta=math.radians(40.0))),
        ("cone", _case("cone", delta=math.radians(10.0))),
        ("diamond", _case("diamond")),
        ("fanno", _case("fanno", mach=0.5, fld=0.2)),
        ("rayleigh", _case("rayleigh", mach=0.5, ttRatio=1.2)),
        ("pg", _case("prandtl_glauert", mach=0.6)),
        ("pitot", _case("rayleigh_pitot")),
    ]
    solved = []
    for name, seed in cases:
        result = design_point(seed)
        if name == "detached":
            if result.get("ok") and result.get("attached") is not False:
                print("CHECK FAIL: a 40 deg wedge at Mach 2 stayed attached", file=sys.stderr)
                return 1
            continue
        if not result.get("ok"):
            print(f"CHECK FAIL: {name}: {result.get('error')}", file=sys.stderr)
            return 1
        solved.append((name, seed, result))
    normal = next(item for item in solved if item[0] == "normal")[2]
    if abs(normal["p2_over_p1"] - 4.5) > 1e-9:
        print("CHECK FAIL: Mach 2 normal-shock pressure ratio is not 4.5", file=sys.stderr)
        return 1
    bad_pg = design_point(_case("prandtl_glauert", mach=1.2))
    if bad_pg.get("ok"):
        print("CHECK FAIL: supersonic Prandtl-Glauert was accepted", file=sys.stderr)
        return 1
    subsonic = design_point(_case("rayleigh_pitot", pitot=1.2 * 101325.0, staticPressure=101325.0))
    if subsonic.get("branch") != "subsonic":
        print("CHECK FAIL: low pitot ratio was not subsonic", file=sys.stderr)
        return 1
    negative = design_point(_case("wedge", delta=-0.1))
    if negative.get("ok") or "deflection" not in str(negative.get("error")):
        print("CHECK FAIL: a negative wedge angle was not rejected", file=sys.stderr)
        return 1
    slow_wedge = design_point(_case("wedge", mach=0.8))
    if slow_wedge.get("ok") or "greater than 1" not in str(slow_wedge.get("error")):
        print("CHECK FAIL: a subsonic wedge did not name the Mach limit", file=sys.stderr)
        return 1
    flat = design_point(_case("diamond", epsilon=0.0))
    if flat.get("ok"):
        print("CHECK FAIL: a zero diamond half-angle was accepted", file=sys.stderr)
        return 1
    html = bake_html(default_seed())
    if any(token in html for token in ("__TITLE__", "__SEED_JSON__", "__LAB_JS__")):
        print("CHECK FAIL: placeholder left in HTML", file=sys.stderr)
        return 1
    if "<script src=" in html.lower():
        print("CHECK FAIL: HTML loads an external script", file=sys.stderr)
        return 1
    if "Lab.boot" not in html or "addEventListener" not in html:
        print("CHECK FAIL: HTML is missing the live page", file=sys.stderr)
        return 1
    try:
        parity = node_parity(solved)
    except DesignError as exc:
        print(f"CHECK FAIL: {exc}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_png(path, next(item for item in solved if item[0] == "wedge")[2])
        if not path.is_file() or path.stat().st_size < 1000:
            print("CHECK FAIL: check plot was not written", file=sys.stderr)
            return 1
    print("check: pass")
    print_kv("node_parity", parity)
    print_kv("modes", len(solved))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bake an interactive compressible-flow classroom page.")
    parser.add_argument("--mode", choices=MODES, default=None)
    parser.add_argument("--mach", type=float, default=None)
    parser.add_argument("--delta", type=float, default=None, help="wedge or cone angle [rad]")
    parser.add_argument("--epsilon", type=float, default=None, help="diamond half-angle [rad]")
    parser.add_argument("--alpha", type=float, default=None, help="diamond angle of attack [rad]")
    parser.add_argument("--gamma", type=float, default=None)
    parser.add_argument("--fld", type=float, default=None, help="Fanno 4fL/D")
    parser.add_argument("--tt-ratio", type=float, default=None, dest="tt_ratio")
    parser.add_argument("--cl-inc", type=float, default=None)
    parser.add_argument("--cm-inc", type=float, default=None)
    parser.add_argument("--cd-inc", type=float, default=None)
    parser.add_argument("--cpmin-inc", type=float, default=None)
    parser.add_argument("--pitot", type=float, default=None)
    parser.add_argument("--static", type=float, default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--pressure", type=float, default=None)
    parser.add_argument("--density", type=float, default=None)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--check", action="store_true")
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
    if not result.get("ok"):
        print(f"error: {result.get('error')}", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else SKILL_DIR / "compressible_flow_design.png"
    if out.suffix.lower() != ".png":
        out = out.with_suffix(".png")
    html_path = out.with_suffix(".html")
    try:
        write_png(out, result)
        html_path.write_text(bake_html(seed), encoding="utf-8")
    except (OSError, DesignError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out, html_path)
    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
