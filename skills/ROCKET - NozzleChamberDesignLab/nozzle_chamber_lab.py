#!/usr/bin/env python3
"""Bake a self-contained 2D nozzle and chamber design lab.

The HTML page recomputes in the browser. This program seeds that page from
frozen CEA tables and prints the same initial point.
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
sys.path.insert(0, str(ROOT / "ROCKET - Area-Mach Graph"))
sys.path.insert(0, str(ROOT / "ROCKET - KickStageNozzle"))
sys.path.insert(0, str(ROOT / "ROCKET - PerformanceParameters" / "src"))

import area_mach  # noqa: E402
import kick_stage_nozzle as kick  # noqa: E402
import load_table  # noqa: E402

G0 = 9.80665
CONV_HALF = math.radians(30.0)
CHAMBER_FACTOR = 2.5
THIN_WALL_LIMIT = 0.1
PLOT_TITLE = "Nozzle chamber design"
JS_FILES = (
    "isentropic.js",
    "throat.js",
    "chamber.js",
    "kick_geometry.js",
    "cea_interp.js",
    "loss_stack.js",
    "lab.js",
)
PACK_COLUMNS = ("r", "Tc_K", "cstar_m_s", "gamma_chamber", "gamma_throat")
ASSUMPTIONS = (
    "interactive nozzle and chamber lab seed; frozen CEA tables from "
    "ROCKET - PerformanceParameters (nearest pc_bar, tie to the higher "
    "pressure, linear mixture ratio, no extrapolation); default gamma is "
    "gamma_throat; optional manual gamma and c* override the table; ideal "
    "nozzle from ROCKET - Area-Mach Graph; delivered c* and CF use eta-cstar "
    "and eta-cf (default 1) as in ROCKET - LossStack; throat sized so "
    "delivered ambient thrust matches --thrust unless Summerfield separation "
    "invalidates ambient CF, in which case the throat is sized on vacuum "
    "thrust and ambient thrust is invalid_separated; chamber volume is "
    "L* * At with a 30 deg convergent frustum and a cylindrical barrel; "
    "divergent wall is a conical length-fraction surrogate "
    "L = f_L * (Re - Rt) / tan(alpha), not a Rao bell; nozzle shell mass is "
    "the frustum lateral area times wall thickness times density; case hoop "
    "stress is pc * Rc / t; g0 = 9.80665 m/s^2; the HTML page recomputes "
    "these relations in the browser"
)


class DesignError(Exception):
    """The seed is not a usable nozzle and chamber point."""


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def default_seed() -> dict:
    return {
        "pair": "LOX/RP1",
        "of": 2.3,
        "pc": 2.0e6,
        "design": "epsilon",
        "epsilon": 5.0,
        "pe": None,
        "pa": 101325.0,
        "thrust": 10000.0,
        "lstar": 1.0,
        "chamberRadius": None,
        "caseThickness": 0.002,
        "allowable": 2.5e8,
        "halfAngle": math.radians(15.0),
        "lengthFraction": 0.8,
        "etaCstar": 1.0,
        "etaCf": 1.0,
        "wallThickness": 0.002,
        "rhoMat": 8000.0,
        "kSep": 0.4,
        "gamma": None,
        "cstar": None,
    }


def _positive(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise DesignError(f"{name} must be > 0")
    number = float(value)
    if not math.isfinite(number) or number <= 0.0:
        raise DesignError(f"{name} must be > 0")
    return number


def chamber_profile(rc: float, rt: float, lstar: float, at: float) -> tuple[float, float, float, bool]:
    if not rc > rt:
        raise DesignError("chamber radius must be greater than throat radius")
    volume = lstar * at
    l_conv = (rc - rt) / math.tan(CONV_HALF)
    v_conv = math.pi / 3.0 * l_conv * (rc * rc + rc * rt + rt * rt)
    if v_conv >= volume:
        return volume, 0.0, l_conv, True
    l_cyl = (volume - v_conv) / (math.pi * rc * rc)
    return volume, l_cyl, l_conv, False


def evaluate(seed: dict) -> dict:
    """Initial design point. Field names match Lab.evaluate in js/lab.js."""
    pc = _positive("chamber pressure", seed["pc"])
    pa = float(seed["pa"])
    if not math.isfinite(pa) or pa < 0.0:
        raise DesignError("ambient pressure must be >= 0")
    thrust = _positive("thrust", seed["thrust"])
    lstar = _positive("L*", seed["lstar"])
    of = float(seed["of"])
    if not math.isfinite(of):
        raise DesignError("mixture ratio must be finite")
    eta_cstar = _positive("efficiencies", seed["etaCstar"])
    eta_cf = _positive("efficiencies", seed["etaCf"])
    k_sep = _positive("k-sep", seed["kSep"])
    case_t = _positive("case thickness", seed["caseThickness"])
    allowable = _positive("allowable stress", seed["allowable"])
    wall_t = _positive("nozzle wall thickness", seed["wallThickness"])
    rho_mat = _positive("material density", seed["rhoMat"])
    half_angle = float(seed["halfAngle"])
    length_fraction = float(seed["lengthFraction"])

    picked = load_table.pick_table(str(seed["pair"]), load_table.pc_bar_from_pa(pc))
    row = load_table.interpolate_row(picked.table, of)
    gamma = float(row["gamma_throat"])
    gamma_source = "gamma_throat"
    cstar_ideal = float(row["cstar_m_s"])
    cstar_source = "table"
    if seed.get("gamma") is not None:
        gamma = _positive("gamma", seed["gamma"])
        if gamma <= 1.0:
            raise DesignError("gamma must be > 1")
        gamma_source = "input"
    if seed.get("cstar") is not None:
        cstar_ideal = _positive("c*", seed["cstar"])
        cstar_source = "input"
    if gamma <= 1.0:
        raise DesignError("gamma must be > 1")

    design = "pe" if seed.get("design") == "pe" else "epsilon"
    if design == "pe":
        if seed.get("pe") is None:
            raise DesignError("pass epsilon or pe")
        pe = _positive("exit pressure", seed["pe"])
        me = kick.mach_from_pressure(pc, pe, gamma)
        epsilon = area_mach.area_ratio(me, gamma)
    else:
        if seed.get("epsilon") is None:
            raise DesignError("pass epsilon or pe")
        epsilon = float(seed["epsilon"])
        if not math.isfinite(epsilon) or epsilon < 1.0:
            raise DesignError("epsilon must be >= 1")
        me = area_mach.invert_supersonic_mach(epsilon, gamma)
        pe = area_mach.exit_pressure(pc, me, gamma)
    if me < 1.0 - 1e-8:
        raise DesignError("design exit is subsonic")

    cf_vac = area_mach.thrust_coefficient_ideal(gamma, pe, pc, 0.0, epsilon, 1.0)
    cf_pa = area_mach.thrust_coefficient_ideal(gamma, pe, pc, pa, epsilon, 1.0)
    expansion = (
        "vacuum_underexpanded" if pa <= 0.0 else area_mach.expansion_flag(pe, pa)
    )
    sep = kick.separation_state(pe, pa, k_sep)
    separated = sep["separation"] == "separated_or_at_risk"
    cstar = cstar_ideal * eta_cstar
    cf_vac_del = cf_vac * eta_cf
    cf_pa_del = cf_pa * eta_cf
    cf_size = cf_vac_del if separated else cf_pa_del
    if cf_size <= 0.0:
        raise DesignError("thrust coefficient must be > 0")
    at = thrust / (cf_size * pc)
    dt = math.sqrt(4.0 * at / math.pi)
    rt = dt / 2.0
    if seed.get("chamberRadius") is None:
        rc = CHAMBER_FACTOR * rt
        chamber_source = "default_2.5_Rt"
    else:
        rc = _positive("chamber radius", seed["chamberRadius"])
        chamber_source = "input"
    geom = kick.conical_geometry(rt, epsilon, half_angle, length_fraction)
    volume, l_cyl, l_conv, volume_short = chamber_profile(rc, rt, lstar, at)
    hoop = pc * rc / case_t
    margin = allowable / hoop - 1.0
    mdot = pc * at / cstar
    thrust_vac = cf_vac_del * pc * at
    thrust_amb = None if separated else cf_pa_del * pc * at
    isp_vac = cstar * cf_vac_del / G0
    isp_amb = None if separated else cstar * cf_pa_del / G0
    # A sonic nozzle has no divergent wall. epsilon = 1 makes L_m = 0.
    if geom["L_m"] == 0.0:
        wall_angle = 0.0
    else:
        wall_angle = math.atan((geom["Re"] - rt) / geom["L_m"])
    return {
        "ok": True,
        "error": None,
        "pair": picked.table["pair"],
        "of": of,
        "pc": pc,
        "pa": pa,
        "gamma": gamma,
        "gammaSource": gamma_source,
        "gammaChamber": float(row["gamma_chamber"]),
        "cstarIdeal": cstar_ideal,
        "cstarSource": cstar_source,
        "Tc": float(row["Tc_K"]),
        "pcTableBar": float(picked.table["pc_bar"]),
        "pcOffsetBar": float(picked.offset_bar),
        "pcWarning": picked.warning,
        "designSource": design,
        "Me": me,
        "epsilon": epsilon,
        "pe": pe,
        "expansion": expansion,
        "CFIdeal": None if separated else cf_pa,
        "CFVac": cf_vac,
        "etaCstar": eta_cstar,
        "etaCf": eta_cf,
        "cstar": cstar,
        "CF": None if separated else cf_pa_del,
        "CFVacDelivered": cf_vac_del,
        "separated": separated,
        "separation": sep["separation"],
        "separationMargin": sep["separation_margin"],
        "Isp": isp_amb,
        "IspVac": isp_vac,
        "At": at,
        "Dt": dt,
        "Rt": rt,
        "Re": geom["Re"],
        "Ae": epsilon * at,
        "mdot": mdot,
        "thrust": thrust_amb,
        "thrustVac": thrust_vac,
        "sizing": "vacuum_because_separated" if separated else "ambient",
        "Vc": volume,
        "Lcyl": l_cyl,
        "Lconv": l_conv,
        "Ldiv": geom["L_m"],
        "Lcone": geom["L_cone_m"],
        "Lslant": geom["L_slant_m"],
        "Rc": rc,
        "chamberRadiusSource": chamber_source,
        "hoop": hoop,
        "margin": margin,
        "thinWall": "yes" if case_t / rc < THIN_WALL_LIMIT else "no",
        "mNozzle": kick.shell_mass(rt, geom["Re"], geom["L_slant_m"], wall_t, rho_mat),
        "volumeShort": volume_short,
        "halfAngle": half_angle,
        "lengthFraction": length_fraction,
        "wallAngle": wall_angle,
        "kSep": k_sep,
        "lstar": lstar,
        "caseThickness": case_t,
        "allowable": allowable,
        "wallThickness": wall_t,
        "rhoMat": rho_mat,
    }


def design_point(seed: dict) -> dict:
    try:
        return evaluate(seed)
    except (DesignError, load_table.TableError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


def build_pack() -> dict:
    catalog = load_table.load_pairs()
    grouped = load_table.all_tables()
    pairs = []
    for name in sorted(grouped):
        spec = catalog.pairs.get(name)
        if spec is None or not spec.cea:
            continue
        tables = []
        for table in sorted(grouped[name], key=lambda item: item["pc_bar"]):
            index = [table["columns"].index(column) for column in PACK_COLUMNS]
            rows = [[row[i] for i in index] for row in table["rows"]]
            tables.append({"pc_bar": table["pc_bar"], "rows": rows})
        pairs.append(
            {
                "pair": name,
                "oxName": spec.oxName,
                "fuelName": spec.fuelName,
                "of_min": spec.of_min,
                "of_max": spec.of_max,
                "of_step": spec.of_step,
                "rho_ox_kg_m3": spec.rho_ox_kg_m3,
                "rho_fuel_kg_m3": spec.rho_fuel_kg_m3,
                "tables": tables,
            }
        )
    return {
        "pc_bar": list(catalog.pc_bar),
        "offset_warn_bar": load_table.OFFSET_WARN_BAR,
        "columns": list(PACK_COLUMNS),
        "pairs": pairs,
    }


def read_lab_js() -> str:
    parts = []
    for name in JS_FILES:
        parts.append((SKILL_DIR / "js" / name).read_text(encoding="utf-8"))
    return "\n".join(parts)


def embed_json(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def bake_html(seed: dict, pack: dict) -> str:
    baked = dict(seed)
    try:
        baked["pair"] = load_table.canonical_pair(str(seed["pair"]))
    except load_table.TableError as exc:
        raise DesignError(str(exc)) from exc
    template = (SKILL_DIR / "viewer" / "template.html").read_text(encoding="utf-8")
    html = template.replace("__TITLE__", PLOT_TITLE)
    html = html.replace("__CEA_PACK__", embed_json(pack))
    html = html.replace("__SEED_JSON__", embed_json(baked))
    html = html.replace("__LAB_JS__", read_lab_js().replace("</", "<\\/"))
    if "__" in html and any(
        token in html for token in ("__TITLE__", "__CEA_PACK__", "__SEED_JSON__", "__LAB_JS__")
    ):
        raise DesignError("viewer template still contains a placeholder")
    return html


def write_png(path: Path, result: dict) -> None:
    x_throat = result["Lcyl"] + result["Lconv"]
    x_exit = x_throat + result["Ldiv"]
    upper = [
        (0.0, result["Rc"]),
        (result["Lcyl"], result["Rc"]),
        (x_throat, result["Rt"]),
        (x_exit, result["Re"]),
    ]
    outline = upper + [(x, -r) for x, r in reversed(upper)]
    xs = [point[0] for point in outline]
    ys = [point[1] for point in outline]
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    ax.fill(xs, ys, color="#d6eaf8", ec="#1b2631", lw=1.2)
    ax.axhline(0.0, color="#7f8c8d", lw=0.8, ls="--")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("axial distance [m]")
    ax.set_ylabel("radius [m]")
    ax.set_title(PLOT_TITLE)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def show_number(key: str, value: object, *, invalid: bool = False) -> None:
    if value is None:
        print_kv(key, "invalid_separated" if invalid else "n/a")
    else:
        print_kv(key, value)


def emit(result: dict, png: Path, html: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("pair", result["pair"])
    print_kv("of", result["of"])
    print_kv("pc_Pa", result["pc"])
    print_kv("pa_Pa", result["pa"])
    print_kv("pc_table_bar", result["pcTableBar"])
    print_kv("pc_offset_bar", result["pcOffsetBar"])
    if result["pcWarning"]:
        print_kv("pc_warning", result["pcWarning"])
    print_kv("gamma", result["gamma"])
    print_kv("gamma_source", result["gammaSource"])
    print_kv("Tc_K", result["Tc"])
    print_kv("cstar_ideal_m_s", result["cstarIdeal"])
    print_kv("cstar_source", result["cstarSource"])
    print_kv("cstar_m_s", result["cstar"])
    print_kv("design_source", result["designSource"])
    print_kv("Me", result["Me"])
    print_kv("epsilon", result["epsilon"])
    print_kv("pe_Pa", result["pe"])
    print_kv("expansion", result["expansion"])
    show_number("CF", result["CF"], invalid=result["separated"])
    print_kv("CF_vac", result["CFVacDelivered"])
    print_kv("eta_cstar", result["etaCstar"])
    print_kv("eta_cf", result["etaCf"])
    show_number("Isp_s", result["Isp"], invalid=result["separated"])
    print_kv("Isp_vac_s", result["IspVac"])
    print_kv("At_m2", result["At"])
    print_kv("Dt_m", result["Dt"])
    print_kv("mdot_kg_s", result["mdot"])
    show_number("thrust_N", result["thrust"], invalid=result["separated"])
    print_kv("thrust_vac_N", result["thrustVac"])
    print_kv("sizing", result["sizing"])
    print_kv("separation", result["separation"])
    show_number("separation_margin", result["separationMargin"])
    print_kv("Vc_m3", result["Vc"])
    print_kv("Rc_m", result["Rc"])
    print_kv("chamber_radius_source", result["chamberRadiusSource"])
    print_kv("Rt_m", result["Rt"])
    print_kv("Re_m", result["Re"])
    print_kv("L_cyl_m", result["Lcyl"])
    print_kv("L_div_m", result["Ldiv"])
    print_kv("wall_angle_rad", result["wallAngle"])
    print_kv("hoop_Pa", result["hoop"])
    print_kv("margin_of_safety", result["margin"])
    print_kv("thin_wall", result["thinWall"])
    print_kv("Lstar_m", result["lstar"])
    print_kv("half_angle_rad", result["halfAngle"])
    print_kv("length_fraction", result["lengthFraction"])
    print_kv("convergent_half_angle_rad", CONV_HALF)
    print_kv("case_thickness_m", result["caseThickness"])
    print_kv("allowable_Pa", result["allowable"])
    print_kv("nozzle_wall_m", result["wallThickness"])
    print_kv("rho_mat_kg_m3", result["rhoMat"])
    print_kv("k_sep", result["kSep"])
    print_kv("m_nozzle_kg", result["mNozzle"])
    print_kv("graph", str(png.resolve()))
    print_kv("viewer", str(html.resolve()))


def seed_from_args(ns: argparse.Namespace) -> dict:
    seed = default_seed()
    try:
        seed["pair"] = load_table.canonical_pair(ns.pair)
    except load_table.TableError as exc:
        raise DesignError(str(exc)) from exc
    seed["of"] = ns.of
    seed["pc"] = ns.pc
    seed["pa"] = ns.pa
    seed["thrust"] = ns.thrust
    seed["lstar"] = ns.lstar
    seed["halfAngle"] = ns.half_angle
    seed["lengthFraction"] = ns.length_fraction
    seed["caseThickness"] = ns.thickness
    seed["allowable"] = ns.allowable
    seed["wallThickness"] = ns.wall_thickness
    seed["rhoMat"] = ns.rho_mat
    seed["etaCstar"] = ns.eta_cstar
    seed["etaCf"] = ns.eta_cf
    seed["kSep"] = ns.k_sep
    seed["chamberRadius"] = ns.chamber_radius
    seed["gamma"] = ns.gamma
    seed["cstar"] = ns.cstar
    if ns.pe is not None and ns.epsilon is not None:
        raise DesignError("pass at most one of --epsilon or --pe")
    if ns.pe is not None:
        seed["design"] = "pe"
        seed["pe"] = ns.pe
        seed["epsilon"] = None
    elif ns.epsilon is not None:
        seed["design"] = "epsilon"
        seed["epsilon"] = ns.epsilon
    return seed


def _close(actual: object, expected: object) -> bool:
    if actual is None or expected is None:
        return actual is None and expected is None
    if isinstance(actual, str) or isinstance(expected, str):
        return actual == expected
    scale = max(abs(float(actual)), abs(float(expected)), 1.0)
    return abs(float(actual) - float(expected)) <= 1e-5 * scale


PARITY_KEYS = (
    "ok",
    "Me",
    "epsilon",
    "pe",
    "gamma",
    "cstarIdeal",
    "cstar",
    "CF",
    "CFVac",
    "CFVacDelivered",
    "At",
    "Dt",
    "Rt",
    "Re",
    "mdot",
    "thrust",
    "thrustVac",
    "Vc",
    "Lcyl",
    "Ldiv",
    "wallAngle",
    "Rc",
    "hoop",
    "margin",
    "mNozzle",
    "Isp",
    "IspVac",
    "wallAngle",
    "expansion",
    "separation",
    "sizing",
    "thinWall",
    "gammaSource",
    "chamberRadiusSource",
    "pcTableBar",
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
const area = context.Lab.areaRatio(2, 1.4);
const designs = payload.cases.map(function (item) {
  return context.Lab.computeDesign(item.seed, payload.pack);
});
process.stdout.write(JSON.stringify({ area: area, designs: designs }));
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
    if abs(report["area"] - 1.6875) > 1e-6:
        raise DesignError(f"JS areaRatio(2, 1.4) = {report['area']}")
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
    got = area_mach.area_ratio(2.0, 1.4)
    if abs(got - 1.6875) > 1e-6:
        print(f"CHECK FAIL: area_ratio(2, 1.4) = {got}", file=sys.stderr)
        return 1
    me = area_mach.invert_supersonic_mach(1.6875, 1.4)
    if abs(me - 2.0) > 1e-4:
        print(f"CHECK FAIL: invert(1.6875) = {me}", file=sys.stderr)
        return 1
    picked = load_table.pick_table("LOX/RP1", 20.0)
    row = load_table.interpolate_row(picked.table, 2.3)
    sea = default_seed()
    sea_point = design_point(sea)
    if not sea_point["ok"]:
        print(f"CHECK FAIL: {sea_point['error']}", file=sys.stderr)
        return 1
    if sea_point["separation"] != "attached":
        print("CHECK FAIL: default sea-level point is separated", file=sys.stderr)
        return 1
    if abs(sea_point["cstarIdeal"] - row["cstar_m_s"]) > 1e-6:
        print("CHECK FAIL: c* does not match the frozen LOX/RP1 row", file=sys.stderr)
        return 1
    if abs(sea_point["gamma"] - row["gamma_throat"]) > 1e-8:
        print("CHECK FAIL: gamma is not gamma_throat", file=sys.stderr)
        return 1
    if sea_point["pcTableBar"] != 20.0:
        print("CHECK FAIL: 2 MPa did not select the 20 bar table", file=sys.stderr)
        return 1
    vacuum = default_seed()
    vacuum["pa"] = 0.0
    vacuum_point = design_point(vacuum)
    if not vacuum_point["ok"]:
        print(f"CHECK FAIL: {vacuum_point['error']}", file=sys.stderr)
        return 1
    if vacuum_point["expansion"] == sea_point["expansion"]:
        print("CHECK FAIL: vacuum and sea level expansion flags match", file=sys.stderr)
        return 1
    if not (vacuum_point["CFVacDelivered"] > sea_point["CF"] ):
        print("CHECK FAIL: vacuum CF is not above ambient CF", file=sys.stderr)
        return 1
    sonic = default_seed()
    sonic["design"] = "epsilon"
    sonic["epsilon"] = 1.0
    sonic["pe"] = None
    sonic_point = design_point(sonic)
    if (
        not sonic_point["ok"]
        or sonic_point["Ldiv"] != 0.0
        or sonic_point["wallAngle"] != 0.0
        or not _close(sonic_point["Re"], sonic_point["Rt"])
    ):
        print("CHECK FAIL: epsilon = 1 did not give a zero-length divergent", file=sys.stderr)
        return 1
    alias = default_seed()
    alias["pair"] = "LOX/RP-1"
    alias_point = design_point(alias)
    if alias_point["pair"] != "LOX/RP1" or not _close(alias_point["cstarIdeal"], sea_point["cstarIdeal"]):
        print("CHECK FAIL: LOX/RP-1 did not resolve to the LOX/RP1 card", file=sys.stderr)
        return 1
    pack = build_pack()
    with tempfile.TemporaryDirectory() as folder:
        html_path = Path(folder) / "lab.html"
        html = bake_html(sea, pack)
        html_path.write_text(html, encoding="utf-8")
        if any(token in html for token in ("__TITLE__", "__CEA_PACK__", "__SEED_JSON__", "__LAB_JS__")):
            print("CHECK FAIL: placeholder left in HTML", file=sys.stderr)
            return 1
        if "<script src=" in html.lower():
            print("CHECK FAIL: HTML loads an external script", file=sys.stderr)
            return 1
        if "LOX/RP1" not in html or "addEventListener" not in html:
            print("CHECK FAIL: HTML is missing the CEA pack or live inputs", file=sys.stderr)
            return 1
        alias_html = bake_html(alias, pack)
        seed_blob = alias_html.split('id="seed-json">', 1)[1].split("</script>", 1)[0]
        if "LOX/RP-1" in seed_blob or "LOX/RP1" not in seed_blob:
            print("CHECK FAIL: HTML seed kept the LOX/RP-1 alias", file=sys.stderr)
            return 1
    try:
        parity = node_parity(
            pack,
            [
                ("sea", sea, sea_point),
                ("vacuum", vacuum, vacuum_point),
                ("sonic", sonic, sonic_point),
            ],
        )
    except DesignError as exc:
        print(f"CHECK FAIL: {exc}", file=sys.stderr)
        return 1
    print("check: pass")
    print_kv("area_ratio_M2", got)
    print_kv("node_parity", parity)
    print_kv("Me", sea_point["Me"])
    print_kv("epsilon", sea_point["epsilon"])
    print_kv("expansion_sea", sea_point["expansion"])
    print_kv("expansion_vacuum", vacuum_point["expansion"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bake an interactive 2D nozzle and chamber design page."
    )
    parser.add_argument("--pair", default="LOX/RP1", help="oxidizer/fuel card pair")
    parser.add_argument("--of", type=float, default=2.3, help="mixture ratio r")
    parser.add_argument("--pc", type=float, default=2.0e6, help="chamber pressure [Pa]")
    parser.add_argument("--epsilon", type=float, default=None, help="area ratio Ae/At")
    parser.add_argument("--pe", type=float, default=None, help="design exit pressure [Pa]")
    parser.add_argument("--pa", type=float, default=101325.0, help="ambient pressure [Pa]")
    parser.add_argument("--thrust", type=float, default=10000.0, help="design thrust [N]")
    parser.add_argument("--lstar", type=float, default=1.0, help="characteristic length [m]")
    parser.add_argument("--chamber-radius", type=float, default=None, help="chamber radius [m]")
    parser.add_argument("--thickness", type=float, default=0.002, help="case wall thickness [m]")
    parser.add_argument("--allowable", type=float, default=2.5e8, help="allowable case stress [Pa]")
    parser.add_argument(
        "--half-angle",
        type=float,
        default=math.radians(15.0),
        help="divergent reference half-angle [rad]",
    )
    parser.add_argument(
        "--length-fraction",
        type=float,
        default=0.8,
        help="divergent length over a full cone",
    )
    parser.add_argument("--eta-cstar", type=float, default=1.0, help="c* efficiency product")
    parser.add_argument("--eta-cf", type=float, default=1.0, help="CF efficiency product")
    parser.add_argument("--wall-thickness", type=float, default=0.002, help="nozzle wall [m]")
    parser.add_argument("--rho-mat", type=float, default=8000.0, help="nozzle material density [kg/m^3]")
    parser.add_argument("--k-sep", type=float, default=0.4, help="Summerfield pe/pa separation ratio")
    parser.add_argument("--gamma", type=float, default=None, help="manual gamma override")
    parser.add_argument("--cstar", type=float, default=None, help="manual c* override [m/s]")
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
    out = Path(args.out) if args.out else SKILL_DIR / "nozzle_chamber_design.png"
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
    sys.exit(main())
