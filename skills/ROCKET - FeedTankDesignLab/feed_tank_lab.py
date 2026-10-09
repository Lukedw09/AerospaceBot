#!/usr/bin/env python3
"""Interactive liquid-engine feed and tank page.

Pressure-fed and electric-pump branches sit side by side. The page recomputes
supply pressure, orifices, blowdown or pump power, and thin-wall tank stress.
An electric pump is not a turbine cycle.
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
for folder in (
    "ROCKET - FeedSystemPressureBudget",
    "ROCKET - InjectorOrificeFlow",
    "ROCKET - PumpHydraulicPower",
    "ROCKET - PressurantBlowdown",
    "ROCKET - TankStructureMass",
    "ROCKET - PropellantLoad",
):
    sys.path.insert(0, str(ROOT / "skills" / folder))

import feed_system_pressure_budget as feed  # noqa: E402
import injector_orifice_flow as injector  # noqa: E402
import pressurant_blowdown as blowdown  # noqa: E402
import propellant_load as propellant  # noqa: E402
import pump_hydraulic_power as pump  # noqa: E402
import tank_structure_mass as tank  # noqa: E402

PLOT_TITLE = "Feed and tank design"
CHECK_TOL = 1e-9
JS_FILES = (
    "feed_budget.js",
    "injector.js",
    "pump.js",
    "blowdown.js",
    "tank.js",
    "propellant.js",
    "lab.js",
)
ASSUMPTIONS = (
    "pressure-fed or electric-pump feed; an electric pump is not a turbine cycle; "
    "p_supply is chamber pressure plus that branch injector drop, one named line drop, "
    "and rho*g*height with g = 9.80665; "
    "orifice area is mdot / (Cd * sqrt(2*rho*dp)); "
    "mixture-ratio flow is propellant_load mdot_o = r*mdot/(r+1); "
    "loaded liquid volume is mdot*tb/((1-residuals)*rho) so residuals stay in the tank "
    "and the injector flow is the expelled volume; residuals must be in [0, 1); "
    "a pressure-fed shell internal volume is that loaded liquid plus the initial ullage; "
    "an electric-pump shell is the loaded liquid only; "
    "blowdown is p2 = p0*(V0/(V0+V_expelled))**n with n > 0 and default n = 1; "
    "a tank is flagged when p2 is below that branch p_supply; "
    "shell thickness and membrane stress use p0 when pressure-fed and the user tank MEOP "
    "when electric-pump-fed, times design factor 1; "
    "sphere membrane stress is p*R/(2*t); cylinder hoop is p*R/t and longitudinal is p*R/(2*t); "
    "flat-head thickness is R*sqrt(p/(S*eta)); weld efficiency is 1; "
    "margin is allowable/stress - 1; t/R >= 0.1 is refused; "
    "allowable stress and material density are assumptions, not a named alloy; "
    "pressurant mass is omitted unless temperature and specific gas constant are both given; "
    "LOX and RP-1 densities 1141 and 810 kg/m3 are the PropellantLoad pair defaults"
)


class DesignError(Exception):
    """The seed is not a usable feed and tank point."""


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        if math.isfinite(value) and abs(value) <= 1e-9:
            value = 0.0
        text = f"{value:.8g}"
    elif isinstance(value, bool):
        text = "yes" if value else "no"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def branch_defaults(dp_inj: float, rho: float, mdot: float) -> dict[str, float]:
    return {
        "mdot": mdot,
        "rho": rho,
        "dpInj": dp_inj,
        "cd": 0.75,
        "count": 20,
        "p0": 4.0e6,
        "v0": 0.1,
        "n": 1.0,
        "pin": 3.0e5,
        "eta": 0.65,
        "etaDrive": 0.9,
        "meop": 5.0e5,
    }


def default_seed(
    architecture: str = "pressure",
    flow_mode: str = "ratio",
    shape: str = "sphere",
) -> dict:
    return {
        "architecture": architecture,
        "flowMode": flow_mode,
        "pc": 2.0e6,
        "dpLine": 1.0e5,
        "height": 1.0,
        "tb": 20.0,
        "residuals": 0.02,
        "allowable": 9.0e8,
        "rhoMat": 4430.0,
        "etaWeld": 1.0,
        "designFactor": 1.0,
        "shape": shape,
        "radius": 0.2,
        "mdot": 2.0,
        "r": 2.3,
        "ox": branch_defaults(2.0e5, 1141.0, 1.4),
        "fuel": branch_defaults(1.5e5, 810.0, 0.6),
    }


def branch_point(seed: dict, name: str, mdot: float) -> dict[str, float | bool | None]:
    src = seed[name]
    tank.require_fraction("residuals fraction", seed["residuals"])
    if not math.isfinite(seed["tb"]) or seed["tb"] <= 0.0:
        raise DesignError("burn time must be > 0")
    _manifold, head, supply = feed.supply_pressure(
        seed["pc"], src["dpInj"], seed["dpLine"], src["rho"], seed["height"], feed.G0
    )
    # Residuals stay behind. The injector delivers mdot for the whole burn.
    volume = mdot * seed["tb"] / (src["rho"] * (1.0 - seed["residuals"]))
    expelled = (1.0 - seed["residuals"]) * volume
    area = injector.orifice_area(mdot, src["rho"], src["cd"], src["dpInj"])
    diameter = injector.orifice_diameter(area, src["count"])
    tank_pressure = src["p0"] if seed["architecture"] == "pressure" else src["meop"]
    if seed["architecture"] == "pressure":
        blowdown.require_positive(f"{name} polytropic exponent", src["n"])
        blowdown.require_positive(f"{name} initial ullage", src["v0"])
        shell_volume = volume + src["v0"]
    else:
        shell_volume = volume
    shell = tank.evaluate(
        shell_volume,
        src["rho"],
        0.0,
        tank_pressure,
        seed["allowable"],
        seed["rhoMat"],
        seed["shape"],
        seed["radius"] if seed["shape"] == "cylinder" else None,
        seed["etaWeld"],
        seed["designFactor"],
        1.0,
        None,
        None,
    )
    pressure = float(shell["p_design_Pa"])
    radius = float(shell["R_m"])
    thickness = float(shell["t_barrel_m"]) if seed["shape"] == "cylinder" else float(shell["t_m"])
    if seed["shape"] == "sphere":
        sigma = pressure * radius / (2.0 * thickness)
        sigma_long = None
    else:
        sigma = pressure * radius / thickness
        sigma_long = pressure * radius / (2.0 * thickness)
    row: dict[str, float | bool | None] = {
        "mdot": mdot,
        "volume": volume,
        "expelled": expelled,
        "head": head,
        "supply": supply,
        "area": area,
        "diameter": diameter,
        "tankPressure": tank_pressure,
        "pDesign": pressure,
        "radius": radius,
        "thickness": thickness,
        "tHead": None if seed["shape"] == "sphere" else float(shell["t_head_m"]),
        "length": None if seed["shape"] == "sphere" else float(shell["L_m"]),
        "sigma": sigma,
        "sigmaLong": sigma_long,
        "margin": seed["allowable"] / sigma - 1.0,
        "mass": float(shell["m_tank_kg"]),
        "p2": None,
        "flagged": None,
        "rise": None,
        "shaft": None,
        "drive": None,
    }
    if seed["architecture"] == "pressure":
        v2 = blowdown.end_ullage(src["v0"], expelled)
        p2 = blowdown.blowdown_pressure(src["p0"], src["v0"], v2, src["n"])
        row["p2"] = p2
        row["flagged"] = p2 < supply
    else:
        rise = supply - src["pin"]
        if rise <= 0.0:
            raise DesignError(f"{name} pump inlet is not below the supply pressure")
        row["rise"] = rise
        row["shaft"] = pump.shaft_power(mdot, src["rho"], rise, src["eta"])
        row["drive"] = row["shaft"] / src["etaDrive"]
    return row


def design_point(seed: dict) -> dict:
    try:
        if seed["flowMode"] == "ratio":
            mdot_ox = propellant.oxidizer_flow(seed["mdot"], seed["r"])
            mdot_fuel = propellant.fuel_flow(seed["mdot"], seed["r"])
            mdot = seed["mdot"]
            ratio = seed["r"]
        else:
            mdot_ox = seed["ox"]["mdot"]
            mdot_fuel = seed["fuel"]["mdot"]
            mdot = mdot_ox + mdot_fuel
            ratio = mdot_ox / mdot_fuel
        return {
            "ok": True,
            "architecture": seed["architecture"],
            "flowMode": seed["flowMode"],
            "mdot": mdot,
            "r": ratio,
            "ox": branch_point(seed, "ox", mdot_ox),
            "fuel": branch_point(seed, "fuel", mdot_fuel),
        }
    except (DesignError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


def read_lab_js() -> str:
    return "\n".join((SKILL_DIR / "js" / name).read_text(encoding="utf-8") for name in JS_FILES)


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


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise DesignError("matplotlib is required to sketch the feed system") from exc
    return plt


def write_png(path: Path, seed: dict, result: dict) -> None:
    plt = ensure_matplotlib()
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 4.6))
    for ax, name, title in ((axes[0], "ox", "oxidizer"), (axes[1], "fuel", "fuel")):
        row = result[name]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title)
        circle = plt.Circle((0.5, 0.72), 0.16, fill=False, lw=1.6)
        ax.add_patch(circle)
        ax.plot([0.5, 0.5], [0.56, 0.18], color="black", lw=1.4)
        ax.add_patch(plt.Rectangle((0.28, 0.08), 0.44, 0.1, fill=False, lw=1.4))
        ax.text(0.5, 0.72, f"{row['sigma'] / 1e6:.3g} MPa", ha="center", va="center", fontsize=8)
        ax.text(0.62, 0.36, f"{row['supply'] / 1e6:.3g} MPa", ha="left", va="center", fontsize=8)
        if seed["architecture"] == "pressure" and row["flagged"]:
            ax.text(0.5, 0.95, "short", ha="center", color="#922b21", fontsize=9)
        elif seed["architecture"] == "pressure":
            ax.text(0.5, 0.95, "clears", ha="center", fontsize=9)
        else:
            ax.text(0.5, 0.95, f"{row['drive'] / 1e3:.3g} kW", ha="center", fontsize=9)
    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def emit(seed: dict, result: dict, png: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("architecture", result["architecture"])
    print_kv("flow_mode", result["flowMode"])
    print_kv("electric_pump_is_not_a_turbine_cycle", "yes")
    print_kv("shell_pressure", "p0" if seed["architecture"] == "pressure" else "tank_meop")
    print_kv("mdot_kg_s", result["mdot"])
    print_kv("r", result["r"])
    for name in ("ox", "fuel"):
        row = result[name]
        print_kv(f"p_supply_{name}_Pa", row["supply"])
        print_kv(f"A_{name}_m2", row["area"])
        print_kv(f"d_{name}_m", row["diameter"])
        print_kv(f"m_tank_{name}_kg", row["mass"])
        print_kv(f"p_design_{name}_Pa", row["pDesign"])
        print_kv(f"R_{name}_m", row["radius"])
        print_kv(f"t_{name}_m", row["thickness"])
        print_kv(f"sigma_{name}_Pa", row["sigma"])
        print_kv(f"margin_{name}", row["margin"])
        if seed["architecture"] == "pressure":
            print_kv(f"p2_{name}_Pa", row["p2"])
            print_kv(f"flagged_{name}", row["flagged"])
        else:
            src = seed[name]
            print_kv(f"pin_{name}_Pa", src["pin"])
            print_kv(f"eta_pump_{name}", src["eta"])
            print_kv(f"eta_drive_{name}", src["etaDrive"])
            print_kv(f"meop_{name}_Pa", src["meop"])
            print_kv(f"rise_{name}_Pa", row["rise"])
            print_kv(f"P_shaft_{name}_W", row["shaft"])
            print_kv(f"P_drive_{name}_W", row["drive"])
        if seed["shape"] == "cylinder":
            print_kv(f"sigma_long_{name}_Pa", row["sigmaLong"])
            print_kv(f"t_head_{name}_m", row["tHead"])
    if png is not None:
        print_kv("graph", png.resolve())


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
  return context.Lab.designPoint(item.seed);
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
    keys = (
        "supply",
        "area",
        "diameter",
        "mass",
        "pDesign",
        "radius",
        "thickness",
        "sigma",
        "margin",
        "p2",
        "rise",
        "shaft",
        "drive",
    )
    for (name, _seed, expected), got in zip(cases, report["designs"]):
        if not got.get("ok"):
            raise DesignError(f"{name} JS design failed: {got.get('error')}")
        for side in ("ox", "fuel"):
            for key in keys:
                want = expected[side][key]
                have = got[side].get(key)
                if want is None:
                    if have is not None:
                        raise DesignError(f"{name} {side}.{key}: JS {have!r} != Python None")
                    continue
                if not isinstance(have, (int, float)) or not close(float(have), float(want)):
                    raise DesignError(f"{name} {side}.{key}: JS {have!r} != Python {want!r}")
            if expected["architecture"] == "pressure" and bool(got[side]["flagged"]) != bool(expected[side]["flagged"]):
                raise DesignError(f"{name} {side} flag mismatch")
    return "pass"


def run_check() -> int:
    pressure = design_point(default_seed())
    if not pressure["ok"]:
        print(f"CHECK FAIL: {pressure['error']}", file=sys.stderr)
        return 1
    seed = default_seed()
    for name, dp, rho in (("ox", 2.0e5, 1141.0), ("fuel", 1.5e5, 810.0)):
        _m, _h, supply = feed.supply_pressure(2.0e6, dp, 1.0e5, rho, 1.0, feed.G0)
        if not close(pressure[name]["supply"], supply):
            print(f"CHECK FAIL: {name} supply", file=sys.stderr)
            return 1
        area = injector.orifice_area(pressure[name]["mdot"], rho, 0.75, dp)
        if not close(pressure[name]["area"], area):
            print(f"CHECK FAIL: {name} orifice area", file=sys.stderr)
            return 1
        volume = pressure[name]["volume"]
        expelled = (1.0 - 0.02) * volume
        if not close(expelled, pressure[name]["mdot"] * seed["tb"] / rho):
            print(f"CHECK FAIL: {name} expelled volume is not the injector flow", file=sys.stderr)
            return 1
        v2 = blowdown.end_ullage(0.1, expelled)
        p2 = blowdown.blowdown_pressure(4.0e6, 0.1, v2, 1.0)
        if not close(pressure[name]["p2"], p2):
            print(f"CHECK FAIL: {name} blowdown", file=sys.stderr)
            return 1
        shell = tank.evaluate(volume + 0.1, rho, 0.0, 4.0e6, 9.0e8, 4430.0, "sphere", None, 1.0, 1.0, 1.0, None, None)
        if not close(pressure[name]["mass"], float(shell["m_tank_kg"])):
            print(f"CHECK FAIL: {name} shell mass", file=sys.stderr)
            return 1
        internal = (4.0 / 3.0) * math.pi * float(pressure[name]["radius"]) ** 3
        if not close(internal, volume + 0.1):
            print(f"CHECK FAIL: {name} shell omits the ullage", file=sys.stderr)
            return 1
        if not close(pressure[name]["sigma"], 9.0e8 * 1.0):
            print(f"CHECK FAIL: {name} membrane stress", file=sys.stderr)
            return 1
        if pressure[name]["flagged"]:
            print(f"CHECK FAIL: default {name} tank is flagged", file=sys.stderr)
            return 1
    short = default_seed()
    short["ox"]["v0"] = 0.001
    short["fuel"]["v0"] = 0.001
    flagged = design_point(short)
    if not flagged["ok"] or not flagged["ox"]["flagged"] or not flagged["fuel"]["flagged"]:
        print("CHECK FAIL: short ullage did not flag both tanks", file=sys.stderr)
        return 1
    cylinder = design_point(default_seed(shape="cylinder"))
    if not cylinder["ok"] or not close(cylinder["ox"]["sigma"], 9.0e8):
        print("CHECK FAIL: cylinder hoop stress", file=sys.stderr)
        return 1
    if cylinder["ox"]["sigmaLong"] is None or not close(cylinder["ox"]["sigmaLong"], 4.5e8):
        print("CHECK FAIL: cylinder longitudinal stress", file=sys.stderr)
        return 1
    electric_seed = default_seed(architecture="electric")
    electric = design_point(electric_seed)
    if not electric["ok"]:
        print(f"CHECK FAIL: {electric['error']}", file=sys.stderr)
        return 1
    rise = electric["ox"]["supply"] - electric_seed["ox"]["pin"]
    shaft = pump.shaft_power(electric["ox"]["mdot"], electric_seed["ox"]["rho"], rise, electric_seed["ox"]["eta"])
    if not close(electric["ox"]["shaft"], shaft) or electric["ox"]["p2"] is not None:
        print("CHECK FAIL: electric pump shaft power", file=sys.stderr)
        return 1
    branches = default_seed(flow_mode="branches")
    split = design_point(branches)
    if not split["ok"] or close(split["ox"]["area"], pressure["ox"]["area"]):
        print("CHECK FAIL: branch flow mode did not change orifice area", file=sys.stderr)
        return 1
    moved = default_seed()
    moved["ox"]["dpInj"] = 4.0e5
    moved_point = design_point(moved)
    if not moved_point["ok"] or close(moved_point["ox"]["supply"], pressure["ox"]["supply"]):
        print("CHECK FAIL: injector drop did not move supply pressure", file=sys.stderr)
        return 1
    thicker = default_seed()
    thicker["allowable"] = 4.5e8
    thick_point = design_point(thicker)
    if not thick_point["ok"] or not (thick_point["ox"]["thickness"] > pressure["ox"]["thickness"]):
        print("CHECK FAIL: allowable stress did not change thickness", file=sys.stderr)
        return 1
    bad_residuals = default_seed()
    bad_residuals["residuals"] = 1.5
    if design_point(bad_residuals)["ok"]:
        print("CHECK FAIL: residuals outside [0, 1) were accepted", file=sys.stderr)
        return 1
    bad_n = default_seed()
    bad_n["ox"]["n"] = 0.0
    bad_n["fuel"]["n"] = 0.0
    if design_point(bad_n)["ok"]:
        print("CHECK FAIL: polytropic exponent 0 was accepted", file=sys.stderr)
        return 1
    html = bake_html(default_seed())
    if "<script src=" in html or "addEventListener" not in html:
        print("CHECK FAIL: baked HTML is not self-contained", file=sys.stderr)
        return 1
    try:
        parity = node_parity(
            [
                ("pressure", default_seed(), pressure),
                ("short", short, flagged),
                ("cylinder", default_seed(shape="cylinder"), cylinder),
                ("electric", electric_seed, electric),
                ("branches", branches, split),
            ]
        )
    except DesignError as exc:
        print(f"CHECK FAIL: {exc}", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "feed.png"
        write_png(png, seed, pressure)
        if not png.is_file() or png.stat().st_size <= 0:
            print("CHECK FAIL: PNG was not written", file=sys.stderr)
            return 1
    print_kv("node_parity", parity)
    print_kv("p_supply_ox_Pa", pressure["ox"]["supply"])
    print_kv("p_supply_fuel_Pa", pressure["fuel"]["supply"])
    print_kv("A_ox_m2", pressure["ox"]["area"])
    print_kv("p2_ox_Pa", pressure["ox"]["p2"])
    print_kv("sigma_ox_Pa", pressure["ox"]["sigma"])
    print_kv("m_tank_ox_kg", pressure["ox"]["mass"])
    print_kv("P_shaft_ox_W", electric["ox"]["shaft"])
    print("CHECK PASS")
    return 0


def _set_branches(seed: dict, key: str, value: float | None) -> None:
    if value is None:
        return
    seed["ox"][key] = value
    seed["fuel"][key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bake the feed and tank design lab.")
    parser.add_argument("--architecture", choices=("pressure", "electric"), default="pressure", help="pressure-fed or electric pump")
    parser.add_argument("--flow", choices=("ratio", "branches"), default="ratio", help="total flow and mixture ratio, or separate branch flows")
    parser.add_argument("--shape", choices=("sphere", "cylinder"), default="sphere", help="tank shape")
    parser.add_argument("--pc", type=float, default=None, help="chamber pressure [Pa]")
    parser.add_argument("--dp-line", type=float, default=None, help="line pressure drop [Pa]")
    parser.add_argument("--height", type=float, default=None, help="tank-to-injector height [m]")
    parser.add_argument("--tb", type=float, default=None, help="burn time [s]")
    parser.add_argument("--residuals", type=float, default=None, help="residual fraction")
    parser.add_argument("--allowable", type=float, default=None, help="allowable stress [Pa]")
    parser.add_argument("--rho-mat", type=float, default=None, help="tank material density [kg/m^3]")
    parser.add_argument("--r", type=float, default=None, help="mixture ratio")
    parser.add_argument("--mdot", type=float, default=None, help="total propellant flow [kg/s]")
    parser.add_argument("--dp-inj-ox", type=float, default=None, help="oxidizer injector drop [Pa]")
    parser.add_argument("--dp-inj-fuel", type=float, default=None, help="fuel injector drop [Pa]")
    parser.add_argument("--cd", type=float, default=None, help="orifice discharge coefficient")
    parser.add_argument("--orifices", type=int, default=None, help="orifice count per branch")
    parser.add_argument("--rho-ox", type=float, default=None, help="oxidizer density [kg/m^3]")
    parser.add_argument("--rho-fuel", type=float, default=None, help="fuel density [kg/m^3]")
    parser.add_argument("--p0", type=float, default=None, help="initial tank pressure [Pa]")
    parser.add_argument("--ullage", type=float, default=None, help="initial ullage volume [m^3]")
    parser.add_argument("--n", type=float, default=None, help="blowdown polytropic exponent")
    parser.add_argument("--eta-weld", type=float, default=None, help="weld efficiency")
    parser.add_argument("--design-factor", type=float, default=None, help="tank design factor")
    parser.add_argument("--radius", type=float, default=None, help="cylinder radius [m]")
    parser.add_argument("--pin", type=float, default=None, help="electric-pump inlet pressure [Pa]")
    parser.add_argument("--eta-pump", type=float, default=None, help="electric-pump efficiency")
    parser.add_argument("--eta-drive", type=float, default=None, help="electric-pump motor efficiency")
    parser.add_argument("--meop", type=float, default=None, help="electric-pump tank MEOP [Pa]")
    parser.add_argument("--out", type=str, default=None, help="PNG path; HTML uses the same stem")
    parser.add_argument("--open", action="store_true", help="open the HTML viewer in a browser")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser


def seed_from_args(args: argparse.Namespace) -> dict:
    seed = default_seed(args.architecture, args.flow, args.shape)
    for key, value in (
        ("pc", args.pc),
        ("dpLine", args.dp_line),
        ("height", args.height),
        ("tb", args.tb),
        ("residuals", args.residuals),
        ("allowable", args.allowable),
        ("rhoMat", args.rho_mat),
        ("r", args.r),
        ("mdot", args.mdot),
        ("etaWeld", args.eta_weld),
        ("designFactor", args.design_factor),
        ("radius", args.radius),
    ):
        if value is not None:
            seed[key] = value
    if args.dp_inj_ox is not None:
        seed["ox"]["dpInj"] = args.dp_inj_ox
    if args.dp_inj_fuel is not None:
        seed["fuel"]["dpInj"] = args.dp_inj_fuel
    if args.rho_ox is not None:
        seed["ox"]["rho"] = args.rho_ox
    if args.rho_fuel is not None:
        seed["fuel"]["rho"] = args.rho_fuel
    _set_branches(seed, "cd", args.cd)
    _set_branches(seed, "count", args.orifices)
    _set_branches(seed, "p0", args.p0)
    _set_branches(seed, "v0", args.ullage)
    _set_branches(seed, "n", args.n)
    _set_branches(seed, "pin", args.pin)
    _set_branches(seed, "eta", args.eta_pump)
    _set_branches(seed, "etaDrive", args.eta_drive)
    _set_branches(seed, "meop", args.meop)
    return seed


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return run_check()
    seed = seed_from_args(args)
    result = design_point(seed)
    if not result["ok"]:
        print(f"error: {result['error']}", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / "feed-tank-lab.png"
    write_png(out, seed, result)
    html_path = out.with_suffix(".html")
    html_path.write_text(bake_html(seed), encoding="utf-8")
    emit(seed, result, out)
    print_kv("viewer", html_path.resolve())
    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
