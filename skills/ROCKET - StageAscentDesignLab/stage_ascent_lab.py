#!/usr/bin/env python3
"""Interactive stage-ascent design page.

The page sizes one to three stages from a LEO delta-v budget, optionally
replaces inert from a mass budget, and flies until gravity and drag losses
settle. It does not replace the one-shot programs.
"""

from __future__ import annotations

import argparse
import csv
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
    "ROCKET - LeoDeltaVBudget",
    "ROCKET - StagePropellantSplit",
    "ROCKET - VehicleMassBudget",
    "ROCKET - MultiStageAscent",
    "ROCKET - MaxQAndAeroLoad",
    "ROCKET - BasicTrajectoryLossesFromBodySurface",
):
    sys.path.insert(0, str(ROOT / "skills" / folder))

import basic_trajectory_losses_from_body_surface as trajectory  # noqa: E402
import leo_delta_v_budget as leo  # noqa: E402
import max_q_and_aero_load as maxq  # noqa: E402
import multi_stage_ascent as ascent  # noqa: E402
import stage_propellant_split as split  # noqa: E402
import vehicle_mass_budget as budget  # noqa: E402

PLOT_TITLE = "Stage ascent design"
CHECK_TOL = 1e-6
JS_FILES = (
    "leo_dv.js",
    "split.js",
    "mass_budget.js",
    "ascent.js",
    "maxq.js",
    "lab.js",
)
ASSUMPTIONS = (
    "leo_design_delta_v uses R0 = 6.3742e6 m; the ascent uses R_EARTH = 6.356766e6 m; "
    "the page does not replace either radius; "
    "steering loss stays 0 because a held angle or a gravity turn reports none; "
    "rotation assist, circularization, and margin stay user inputs and are zero when omitted; "
    "the split uses gravity-free delta_v_vacuum with c = Isp * 9.80665; "
    "structural coefficient eps = ms/(ms+mp); equal_dv shares the ideal delta-v; "
    "a mass budget replaces inert after the split and leaves propellant unchanged; "
    "linear inert is mH + k*mp + residuals; explicit inert sums the named components; "
    "vacuum thrust; inert drops at burnout; optional fairing drop by altitude or time; "
    "density on the page is the 1976 table every 100 m through 86 km and 0 above; "
    "q = 0.5*rho*V^2; the loop stops when gravity loss, drag loss, and each propellant "
    "mass change by less than 1 or 0.1 percent, or after 12 passes; "
    "seed assumptions: two stages, equal_dv, payload 500 kg, altitude 200 km, "
    "Isp 280 s and 320 s, eps 0.08 and 0.12, burn times 80 s and 220 s, "
    "kick 0.05 rad, Cd 0.4, area 2 m^2; a third stage Isp 300 s, eps 0.1, "
    "burn time 250 s is unused until the count is 3; mass budget and jettison are off"
)


class DesignError(Exception):
    """The seed is not a usable ascent point."""


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    elif isinstance(value, bool):
        text = "yes" if value else "no"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def changed_little(new: float, old: float) -> bool:
    delta = abs(new - old)
    return delta < 1.0 or delta <= 0.001 * max(abs(new), abs(old))


def stage_defaults(isp: float, eps: float, tb: float) -> dict:
    return {
        "isp": isp,
        "eps": eps,
        "tb": tb,
        "budget": False,
        "law": "linear",
        "k": 0.1,
        "mH": 0.0,
        "residuals": 0.0,
        "tank": 0.0,
        "engineMass": 0.0,
        "engineCount": 1.0,
        "fairing": 0.0,
        "interstage": 0.0,
        "other": 0.0,
    }


def default_seed(
    count: int = 2,
    mode: str = "equal_dv",
    size: str = "payload",
    path: str = "kick",
) -> dict:
    return {
        "count": count,
        "size": size,
        "mode": mode,
        "payload": 500.0,
        "glow": 80000.0,
        "alt": 200000.0,
        "vRot": 0.0,
        "circ": 0.0,
        "margin": None,
        "marginFraction": None,
        "path": path,
        "kick": 0.05,
        "gamma": 1.0,
        "cd": 0.4,
        "area": 2.0,
        "jettison": False,
        "jetMass": 100.0,
        "jetBy": "alt",
        "jetAlt": 50000.0,
        "jetTime": 80.0,
        "stages": [
            stage_defaults(280.0, 0.08, 80.0),
            stage_defaults(320.0, 0.12, 220.0),
            stage_defaults(300.0, 0.10, 250.0),
        ],
    }


def design_delta_v(seed: dict, gravity: float, drag: float) -> dict:
    if seed["alt"] < 0.0:
        raise DesignError("altitude must be >= 0")
    for name, value in (
        ("rotation assist", seed["vRot"]),
        ("circularization", seed["circ"]),
    ):
        if value < 0.0:
            raise DesignError(f"{name} must be >= 0")
    radius = leo.R0 + seed["alt"]
    mu = leo.G0 * leo.R0 * leo.R0
    v_circ = math.sqrt(mu / radius)
    base = leo.design_delta_v(v_circ, seed["vRot"], gravity, drag, 0.0, seed["circ"], 0.0)
    margin = seed["margin"]
    fraction = seed["marginFraction"]
    if margin is not None and fraction is not None:
        raise DesignError("pass a margin or a margin fraction")
    if fraction is not None:
        if fraction < 0.0:
            raise DesignError("margin fraction must be >= 0")
        applied = fraction * base
        source = "fraction"
    elif margin is not None:
        if margin < 0.0:
            raise DesignError("margin must be >= 0")
        applied = margin
        source = "absolute"
    else:
        applied = 0.0
        source = "omitted"
    return {"vCirc": v_circ, "margin": applied, "marginSource": source, "dv": base + applied}


def split_rows(seed: dict, dv: float, stages: list[dict]) -> list[dict]:
    if dv <= 0.0:
        raise DesignError("delta-v must be > 0")
    specs = [(stage["isp"] * split.G0, stage["eps"]) for stage in stages]
    if seed["mode"] == "equal_dv":
        dvs = [dv / len(stages)] * len(stages)
    elif seed["mode"] == "equal_mr":
        ratio = math.exp(dv / sum(c for c, _eps in specs))
        dvs = [c * math.log(ratio) for c, _eps in specs]
    elif seed["mode"] == "max_payload":
        if seed["size"] != "glow":
            raise DesignError("max_payload needs a gross liftoff mass")
        dvs = [fraction * dv for fraction in split.max_payload_fractions(seed["glow"], dv, specs)]
    else:
        raise DesignError("unknown mode")
    if seed["size"] == "payload":
        if seed["payload"] <= 0.0:
            raise DesignError("payload must be > 0")
        return split.stack_from_payload(seed["payload"], dvs, specs)
    if seed["glow"] <= 0.0:
        raise DesignError("gross liftoff mass must be > 0")
    return split.stack_from_glow(seed["glow"], dvs, specs)


def budget_inert(mp: float, stage: dict) -> float | None:
    if not stage["budget"]:
        return None
    if stage["law"] == "linear":
        text = f"mp={mp},k={stage['k']},mH={stage['mH']},residuals={stage['residuals']}"
    else:
        parts = [f"mp={mp}"]
        if stage["tank"] > 0.0:
            parts.append(f"tank={stage['tank']}")
        if stage["engineMass"] > 0.0:
            parts.append(f"engine-mass={stage['engineMass']}")
            parts.append(f"engine-count={stage['engineCount']}")
        if stage["fairing"] > 0.0:
            parts.append(f"fairing={stage['fairing']}")
        if stage["interstage"] > 0.0:
            parts.append(f"interstage={stage['interstage']}")
        if stage["other"] > 0.0:
            parts.append(f"other={stage['other']}")
        if stage["mH"] > 0.0:
            parts.append(f"mH={stage['mH']}")
        if stage["residuals"] > 0.0:
            parts.append(f"residuals={stage['residuals']}")
        text = ",".join(parts)
    return budget.parse_stage(text).inert


def fly(seed: dict, stages: list[dict], payload: float) -> dict:
    mass = payload + sum(stage["mp"] + stage["inert"] for stage in stages)
    mu = trajectory.G0_STD * trajectory.R_EARTH * trajectory.R_EARTH
    hold = seed["path"] == "gamma"
    theta0 = seed["gamma"] if hold else trajectory.kick_flight_path_angle(seed["kick"])
    if not 0.0 <= theta0 <= math.pi / 2.0:
        raise DesignError("flight-path angle is outside 0 to pi/2")
    cd = seed["cd"] if seed["cd"] and seed["cd"] > 0.0 else None
    area = seed["area"]
    if cd is not None and (area is None or area <= 0.0):
        raise DesignError("drag coefficient needs area > 0")
    namespace = argparse.Namespace(
        rho=None, rho0=None, scale_height=None, oat=None, rh=None, cd=cd, alt=None
    )
    density_at, _source, _meta = trajectory.make_density_at(namespace, trajectory.R_EARTH, trajectory.R_EARTH)
    jet = None
    if seed["jettison"]:
        if seed["jetMass"] <= 0.0:
            raise DesignError("jettison needs mass > 0")
        jet = {"mass": seed["jetMass"]}
        if seed["jetBy"] == "time":
            jet["time"] = seed["jetTime"]
        else:
            jet["alt"] = seed["jetAlt"]
    state = (trajectory.R_EARTH, 0.0, 0.0, 0.0)
    t0 = 0.0
    rows: list[tuple] = []
    gravity = drag_loss = ideal = 0.0
    piece = None
    for stage in stages:
        m0 = mass
        tb = stage["tb"]
        if tb <= 0.0:
            raise DesignError("burn time must be > 0")
        mdot = stage["mp"] / tb
        if mdot <= 0.0 or stage["mp"] >= m0:
            raise DesignError("stage masses or burn time are not physical")
        mf = m0 - stage["mp"]
        c = stage["isp"] * trajectory.G0_STD
        ideal += trajectory.delta_v_vacuum(c, m0, mf)
        heading = theta0 if hold or math.hypot(state[2], state[3]) < 1e-9 else ascent.state_theta(state, theta0)
        piece = ascent.ode_stage(
            trajectory,
            m0=m0,
            mdot=mdot,
            tb=tb,
            thrust=mdot * c,
            mu=mu,
            radius_body=trajectory.R_EARTH,
            state=state,
            theta0=heading,
            hold_theta=hold,
            drag_value=None,
            cd=cd,
            area=area,
            density_at=density_at,
            t0=t0,
            jettison=jet,
        )
        if piece.get("dropped"):
            jet = None
        gravity += piece["dvg"]
        drag_loss += piece["dvD"]
        rows.extend(piece["rows"])
        mass = mf - stage["inert"]
        if mass <= 0.0:
            raise DesignError("staging drops the mass through zero")
        state = piece["state"]
        t0 += tb
        if not hold:
            theta0 = piece["theta_bo"]
    if piece is None:
        raise DesignError("stages must be >= 1")
    return {
        "gravity": gravity,
        "drag": drag_loss,
        "ideal": ideal,
        "rows": rows,
        "Vbo": piece["V_bo"],
        "gammaBo": piece["theta_bo"],
        "rBo": piece["r_bo"],
        "Zbo": piece["r_bo"] - trajectory.R_EARTH,
        "stacked": payload + sum(stage["mp"] + stage["inert"] for stage in stages),
    }


def peak_q(rows: list[tuple]) -> dict:
    best = max(range(len(rows)), key=lambda index: rows[index][5])
    peak = rows[best]
    return {
        "qMax": peak[5],
        "tMax": peak[0],
        "zMax": peak[1],
        "vMax": peak[2],
        "interior": rows[0][0] < peak[0] < rows[-1][0],
    }


def one_pass(seed: dict, gravity: float, drag: float) -> dict:
    stages_in = seed["stages"][: seed["count"]]
    budget_dv = design_delta_v(seed, gravity, drag)
    sized = split_rows(seed, budget_dv["dv"], stages_in)
    payload = seed["payload"] if seed["size"] == "payload" else sized[-1]["payload"]
    flown = []
    for row, stage in zip(sized, stages_in):
        inert = row["inert"]
        replaced = budget_inert(row["mp"], stage)
        if replaced is not None:
            inert = replaced
        flown.append(
            {
                "mp": row["mp"],
                "inertSplit": row["inert"],
                "inert": inert,
                "isp": stage["isp"],
                "tb": stage["tb"],
                "dv": row["dv"],
            }
        )
    trip = fly(seed, flown, payload)
    peak = peak_q(trip["rows"])
    return {
        "ok": True,
        "vCirc": budget_dv["vCirc"],
        "margin": budget_dv["margin"],
        "marginSource": budget_dv["marginSource"],
        "dvDesign": budget_dv["dv"],
        "dvIdeal": trip["ideal"],
        "gravity": trip["gravity"],
        "drag": trip["drag"],
        "steering": 0.0,
        "payload": payload,
        "stacked": trip["stacked"],
        "stages": flown,
        "Vbo": trip["Vbo"],
        "gammaBo": trip["gammaBo"],
        "rBo": trip["rBo"],
        "Zbo": trip["Zbo"],
        "qMax": peak["qMax"],
        "tMax": peak["tMax"],
        "zMax": peak["zMax"],
        "interior": peak["interior"],
        "rows": trip["rows"],
    }


def design_point(seed: dict) -> dict:
    gravity = 0.0
    drag = 0.0
    previous_mp = None
    last = None
    for pass_index in range(1, 13):
        try:
            point = one_pass(seed, gravity, drag)
        except (DesignError, ValueError) as exc:
            if last is None:
                return {"ok": False, "error": str(exc)}
            last["settled"] = False
            last["passes"] = pass_index - 1
            last["warning"] = str(exc)
            return last
        point["passes"] = pass_index
        masses_match = previous_mp is not None and all(
            changed_little(stage["mp"], old) for stage, old in zip(point["stages"], previous_mp)
        )
        if masses_match and changed_little(point["gravity"], gravity) and changed_little(point["drag"], drag):
            point["settled"] = True
            return point
        last = point
        gravity = point["gravity"]
        drag = point["drag"]
        previous_mp = [stage["mp"] for stage in point["stages"]]
    last["settled"] = False
    return last


def read_lab_js() -> str:
    return "\n".join((SKILL_DIR / "js" / name).read_text(encoding="utf-8") for name in JS_FILES)


def embed_json(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def density_table() -> list[float]:
    atmosphere, require_altitude, *_rest = trajectory.load_atmosphere()
    values = []
    altitude = 0.0
    while altitude <= trajectory.Z_MAX_1976 + 1e-9:
        values.append(float(atmosphere(require_altitude(altitude, "altitude"))["rho"]))
        altitude += 100.0
    return values


def bake_html(seed: dict) -> str:
    template = (SKILL_DIR / "viewer" / "template.html").read_text(encoding="utf-8")
    html = template.replace("__TITLE__", PLOT_TITLE)
    html = html.replace("__SEED_JSON__", embed_json(seed))
    html = html.replace("__RHO_JSON__", embed_json(density_table()))
    html = html.replace("__LAB_JS__", read_lab_js().replace("</", "<\\/"))
    if any(token in html for token in ("__TITLE__", "__SEED_JSON__", "__RHO_JSON__", "__LAB_JS__")):
        raise DesignError("viewer template still contains a placeholder")
    return html


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise DesignError("matplotlib is required to plot the ascent") from exc
    return plt


def write_png(path: Path, result: dict) -> None:
    plt = ensure_matplotlib()
    rows = result["rows"]
    times = [row[0] for row in rows]
    altitude = [row[1] / 1000.0 for row in rows]
    dynamic = [row[5] / 1000.0 for row in rows]
    fig, axes = plt.subplots(2, 1, figsize=(8.2, 6.2), sharex=True)
    axes[0].plot(times, altitude, color="#1a5276")
    axes[0].set_ylabel("altitude, km")
    axes[0].set_title(PLOT_TITLE)
    axes[1].plot(times, dynamic, color="#1a5276")
    axes[1].scatter([result["tMax"]], [result["qMax"] / 1000.0], color="#922b21", zorder=3)
    axes[1].set_ylabel("q, kPa")
    axes[1].set_xlabel("time, s")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(seed: dict, result: dict, png: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("stages", seed["count"])
    print_kv("mode", seed["mode"])
    print_kv("size", seed["size"])
    print_kv("settled", result["settled"])
    print_kv("passes", result["passes"])
    print_kv("R0_leo_m", leo.R0)
    print_kv("R_earth_m", trajectory.R_EARTH)
    print_kv("v_circ_m_s", result["vCirc"])
    print_kv("gravity_loss_m_s", result["gravity"])
    print_kv("drag_loss_m_s", result["drag"])
    print_kv("steering_loss_m_s", result["steering"])
    print_kv("margin_m_s", result["margin"])
    print_kv("dv_design_m_s", result["dvDesign"])
    print_kv("dv_ideal_m_s", result["dvIdeal"])
    print_kv("payload_kg", result["payload"])
    print_kv("stacked_mass_kg", result["stacked"])
    for index, stage in enumerate(result["stages"], start=1):
        print_kv(f"stage_{index}_mp_kg", stage["mp"])
        print_kv(f"stage_{index}_inert_kg", stage["inert"])
        print_kv(f"stage_{index}_dv_m_s", stage["dv"])
    print_kv("V_bo_m_s", result["Vbo"])
    print_kv("gamma_bo_rad", result["gammaBo"])
    print_kv("Z_bo_m", result["Zbo"])
    print_kv("q_max_Pa", result["qMax"])
    print_kv("t_maxq_s", result["tMax"])
    print_kv("Z_maxq_m", result["zMax"])
    print_kv("q_max_interior", result["interior"])
    if png is not None:
        print_kv("graph", png.resolve())


def parse_stdout(text: str) -> dict[str, str]:
    found = {}
    for line in text.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        found[key] = value
    return found


def write_csv(path: Path, rows: list[tuple]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["t_s", "Z_m", "V_m_s", "gamma_rad", "rho_kg_m3", "q_Pa", "m_kg"])
        for row in rows:
            writer.writerow([f"{value:.8g}" for value in row])


def program_ascent(seed: dict, result: dict, folder: Path) -> dict[str, str]:
    command = [
        sys.executable,
        str(ROOT / "skills" / "ROCKET - MultiStageAscent" / "multi_stage_ascent.py"),
        "--stages",
        str(seed["count"]),
        "--payload",
        str(result["payload"]),
        "--out",
        str(folder / "ascent.png"),
    ]
    for stage in result["stages"]:
        command.extend(
            [
                "--stage",
                f"mp={stage['mp']},inert={stage['inert']},isp={stage['isp']},tb={stage['tb']}",
            ]
        )
    if seed["path"] == "gamma":
        command.extend(["--gamma", str(seed["gamma"])])
    else:
        command.extend(["--kick", str(seed["kick"])])
    if seed["cd"] and seed["cd"] > 0.0:
        command.extend(["--cd", str(seed["cd"]), "--area", str(seed["area"])])
    if seed["jettison"]:
        if seed["jetBy"] == "time":
            command.extend(["--jettison", f"mass={seed['jetMass']},time={seed['jetTime']}"])
        else:
            command.extend(["--jettison", f"mass={seed['jetMass']},alt={seed['jetAlt']}"])
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise DesignError(completed.stderr.strip() or "multi-stage ascent failed")
    return parse_stdout(completed.stdout)


def program_max_q(rows: list[tuple], folder: Path) -> dict[str, str]:
    table = folder / "ascent.csv"
    write_csv(table, rows)
    command = [
        sys.executable,
        str(ROOT / "skills" / "ROCKET - MaxQAndAeroLoad" / "max_q_and_aero_load.py"),
        "--table",
        str(table),
        "--out",
        str(folder / "maxq.png"),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise DesignError(completed.stderr.strip() or "max-q failed")
    return parse_stdout(completed.stdout)


def node_parity(seed: dict, expected: dict) -> str:
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
context.Lab.rho = payload.rho;
const point = context.Lab.designPoint(payload.seed);
process.stdout.write(JSON.stringify(point));
"""
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        script = root / "run.js"
        payload = root / "payload.json"
        source = root / "lab.js"
        script.write_text(runner, encoding="utf-8")
        source.write_text(read_lab_js(), encoding="utf-8")
        payload.write_text(json.dumps({"seed": seed, "rho": density_table()}), encoding="utf-8")
        completed = subprocess.run(
            [node, str(script), str(source), str(payload)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise DesignError(completed.stderr.strip() or "node parity failed")
        got = json.loads(completed.stdout)
    if not got.get("ok"):
        raise DesignError(f"JS design failed: {got.get('error')}")
    for key in ("dvDesign", "gravity", "drag", "Vbo", "Zbo", "qMax"):
        if not close(float(got[key]), float(expected[key]), tol=5e-2):
            raise DesignError(f"{key}: JS {got[key]!r} != Python {expected[key]!r}")
    for index, stage in enumerate(expected["stages"]):
        if not close(float(got["stages"][index]["mp"]), float(stage["mp"]), tol=5e-2):
            raise DesignError(f"stage {index + 1} mp mismatch")
    return "pass"


def require_point(seed: dict, label: str) -> dict:
    point = design_point(seed)
    if not point["ok"]:
        raise DesignError(f"{label}: {point['error']}")
    return point


def run_check() -> int:
    try:
        seed = default_seed()
        point = require_point(seed, "default")
        if not point["settled"]:
            raise DesignError("default seed did not settle")
        again = leo.design_delta_v(
            point["vCirc"], seed["vRot"], point["gravity"], point["drag"], 0.0, seed["circ"], point["margin"]
        )
        if not close(again, point["dvDesign"]):
            raise DesignError("settled losses do not reproduce the design delta-v")
        specs = [(stage["isp"] * split.G0, stage["eps"]) for stage in seed["stages"][: seed["count"]]]
        dvs = [point["dvDesign"] / seed["count"]] * seed["count"]
        sized = split.stack_from_payload(seed["payload"], dvs, specs)
        for index, row in enumerate(sized):
            if not close(point["stages"][index]["mp"], row["mp"]):
                raise DesignError(f"stage {index + 1} propellant does not match the split")
            if not close(point["stages"][index]["inert"], row["inert"]):
                raise DesignError(f"stage {index + 1} inert does not match the split")
        budget_seed = default_seed()
        budget_seed["stages"][0]["budget"] = True
        budget_seed["stages"][0]["k"] = 0.15
        budget_seed["stages"][0]["mH"] = 200.0
        budget_point = require_point(budget_seed, "budget")
        expected_inert = budget.parse_stage(
            f"mp={budget_point['stages'][0]['mp']},k=0.15,mH=200,residuals=0"
        ).inert
        if not close(budget_point["stages"][0]["inert"], expected_inert):
            raise DesignError("mass budget did not replace inert")
        if close(budget_point["stages"][0]["inert"], budget_point["stages"][0]["inertSplit"]):
            raise DesignError("mass budget inert matches the split inert")
        one = default_seed(count=1)
        one["stages"][0]["isp"] = 450.0
        one["stages"][0]["eps"] = 0.05
        one["stages"][0]["tb"] = 90.0
        require_point(one, "one stage")
        require_point(default_seed(count=3), "three stages")
        dropped = default_seed()
        dropped["jettison"] = True
        dropped["jetMass"] = 100.0
        dropped["jetAlt"] = 40000.0
        require_point(dropped, "jettison")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            flown = program_ascent(seed, point, root)
            for key, have in (
                ("gravity_loss_m_s", point["gravity"]),
                ("drag_loss_m_s", point["drag"]),
                ("V_bo_m_s", point["Vbo"]),
                ("Z_bo_m", point["Zbo"]),
            ):
                if not close(float(flown[key]), have, tol=1e-5):
                    raise DesignError(f"{key} does not match MultiStageAscent")
            peaked = program_max_q(point["rows"], root)
            if not close(float(peaked["q_max_Pa"]), point["qMax"], tol=1e-5):
                raise DesignError("q_max does not match MaxQAndAeroLoad")
            png = root / "lab.png"
            write_png(png, point)
            if not png.is_file() or png.stat().st_size <= 0:
                raise DesignError("PNG was not written")
        html = bake_html(seed)
        if "<script src=" in html or "addEventListener" not in html or 'id="parameters"' not in html:
            raise DesignError("baked HTML is not self-contained")
        parity = node_parity(seed, point)
    except DesignError as exc:
        print(f"CHECK FAIL: {exc}", file=sys.stderr)
        return 1
    print_kv("node_parity", parity)
    print_kv("dv_design_m_s", point["dvDesign"])
    print_kv("gravity_loss_m_s", point["gravity"])
    print_kv("Z_bo_m", point["Zbo"])
    print_kv("q_max_Pa", point["qMax"])
    print_kv("stage_1_mp_kg", point["stages"][0]["mp"])
    print("CHECK PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bake the stage ascent design lab.")
    parser.add_argument("--stages", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--mode", choices=("equal_dv", "equal_mr", "max_payload"), default="equal_dv")
    parser.add_argument("--size", choices=("payload", "glow"), default="payload")
    parser.add_argument("--path", choices=("kick", "gamma"), default="kick")
    parser.add_argument("--out", type=str, default=None, help="PNG path; HTML uses the same stem")
    parser.add_argument("--open", action="store_true", help="open the HTML viewer in a browser")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return run_check()
    seed = default_seed(args.stages, args.mode, args.size, args.path)
    result = design_point(seed)
    if not result["ok"]:
        print(result["error"], file=sys.stderr)
        return 1
    out = Path(args.out) if args.out else Path(tempfile.gettempdir()) / "stage-ascent-lab.png"
    write_png(out, result)
    html_path = out.with_suffix(".html")
    html_path.write_text(bake_html(seed), encoding="utf-8")
    emit(seed, result, out)
    print_kv("viewer", html_path.resolve())
    if args.open:
        webbrowser.open(html_path.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
