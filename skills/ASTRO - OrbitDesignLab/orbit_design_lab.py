#!/usr/bin/env python3
"""Interactive Earth-orbit design lab.

The seed point is computed by the one-shot ASTRO programs. The HTML page
recomputes the same closed-form results in the browser. The LEO-raise tab is
the impulsive Hohmann reference plus a pure plane-change impulse; gravity
loss stays on ASTRO - MultiBurnLeoRaise.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

G0 = 9.80665
R0_EARTH = 6.3742e6
OMEGA_E = 7.292115e-5
AE_WGS84 = 6378137.0
J2 = 1.08228e-3
PLOT_TITLE = "Orbit design lab"
SKILL_DIR = Path(__file__).resolve().parent
SKILLS = SKILL_DIR.parent
CHECK_TOL = 1e-6

JS_FILES = [
    "two_body.js",
    "hohmann.js",
    "bielliptic.js",
    "plane_change.js",
    "geo_stationkeeping.js",
    "clohessy_wiltshire.js",
    "phasing.js",
    "lambert.js",
    "drag_delta_v.js",
    "multi_burn_leo_raise.js",
    "orbit_insertion.js",
    "j2_rates.js",
    "coverage.js",
    "launch_azimuth.js",
    "vacuum_propellant.js",
    "ground_track.js",
    "globe.js",
    "map2d.js",
    "lab.js",
]

PARITY_KEYS = [
    "strategy",
    "hohmann_dv",
    "hohmann_tof",
    "hohmann_recommendation",
    "bielliptic_dv",
    "bielliptic_tof",
    "bielliptic_recommendation",
    "plane_dv",
    "geo_ns",
    "geo_ew",
    "geo_total",
    "cw_x",
    "cw_z",
    "cw_null",
    "cw_hold",
    "phase_dv",
    "lambert_dv1",
    "lambert_dv2",
    "drag_dv",
    "raise_dv",
    "raise_plane",
    "raise_gravity",
    "insertion_dv",
    "insertion_where",
    "eclipse_fraction",
    "gt_lat",
    "gt_lon",
    "coverage_swath",
    "coverage_revisit",
    "coverage_lambda",
    "j2_node",
    "j2_apsis",
    "launch_inc",
    "launch_assist",
    "dv_total",
    "m_propellant",
]

ASSUMPTIONS = (
    "Earth-orbit studio; Hohmann and bielliptic are the impulsive circular-orbit "
    "transfers; plane change is 2*v*sin(di/2) on a circular orbit; GEO station-keeping "
    "uses the geostationary radius and the yearly north-south and east-west impulses; "
    "Clohessy-Wiltshire is planar about a circular chief and the budget scalar is the "
    "hypotenuse of the null or hold components; phasing, Lambert parking burns, drag "
    "per revolution, and insertion circularization are the one-shot results; the LEO "
    "raise tab is MultiBurnLeoRaise's impulsive Hohmann plus a plane-change impulse "
    "at the slower circular radius, with gravity loss left at 0; coverage revisit is "
    "the equatorial count and the map draws that swath along the ground track; "
    "VacuumPropellantMass sums the checked named pieces"
)


class DesignError(Exception):
    pass


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def load_module(folder: str, filename: str, name: str):
    path = SKILLS / folder / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def modules() -> dict:
    return {
        "hohmann": load_module("ASTRO - HohmannTransfer", "hohmann_transfer.py", "orbitlab_hohmann"),
        "bielliptic": load_module("ASTRO - BiellipticTransfer", "bielliptic_transfer.py", "orbitlab_bielliptic"),
        "plane": load_module("ASTRO - PlaneChangeImpulse", "plane_change_impulse.py", "orbitlab_plane"),
        "geo": load_module("ASTRO - GeostationaryStationKeeping", "geostationary_station_keeping.py", "orbitlab_geo"),
        "cw": load_module("ASTRO - RelativeOrbitClohessyWiltshire", "relative_orbit_clohessy_wiltshire.py", "orbitlab_cw"),
        "phase": load_module("ASTRO - RendezvousPhasing", "rendezvous_phasing.py", "orbitlab_phase"),
        "lambert": load_module("ASTRO - LambertTransfer", "lambert_transfer.py", "orbitlab_lambert"),
        "drag": load_module("ASTRO - AerodynamicDragDeltaV", "aerodynamic_drag_delta_v.py", "orbitlab_drag"),
        "raise": load_module("ASTRO - MultiBurnLeoRaise", "multi_burn_leo_raise.py", "orbitlab_raise"),
        "insert": load_module("ASTRO - OrbitInsertionFromBurnout", "orbit_insertion_from_burnout.py", "orbitlab_insert"),
        "op": load_module("ASTRO - OrbitalParameters", "orbital_parameters.py", "orbitlab_op"),
        "ground": load_module("ASTRO - GroundTrackEarth", "ground_track_earth.py", "orbitlab_ground"),
        "cover": load_module("ASTRO - CoverageAndRevisit", "coverage_and_revisit.py", "orbitlab_cover"),
        "j2": load_module("ASTRO - J2SecularRates", "j2_secular_rates.py", "orbitlab_j2"),
        "launch": load_module("ASTRO - LaunchAzimuthInclination", "launch_azimuth_inclination.py", "orbitlab_launch"),
        "vac": load_module("ASTRO - VacuumPropellantMass", "vacuum_propellant_mass.py", "orbitlab_vac"),
    }


def default_seed(r0: float = R0_EARTH) -> dict:
    mu = G0 * r0 * r0
    r1 = r0 + 400000.0
    r2 = (mu / OMEGA_E**2) ** (1.0 / 3.0)
    rb = 2.0 * r2
    r_lam = r0 + 2.0e6
    return {
        "R0": r0,
        "r1": r1,
        "r2": r2,
        "alt": None,
        "ecc": None,
        "rb": rb,
        "strategy": "auto",
        "plane_a": r1,
        "plane_i": math.radians(51.6),
        "plane_di": math.radians(5.0),
        "geo_di": math.radians(0.8),
        "geo_e": 1.0e-4,
        "geo_burns": 12,
        "geo_years": 1.0,
        "cw_x": 1000.0,
        "cw_z": 400.0,
        "cw_xd": 0.05,
        "cw_zd": -0.02,
        "cw_time": 600.0,
        "cw_a": r1,
        "cw_piece": "cw_null",
        "phase_r": r1,
        "phase": math.radians(20.0),
        "phase_lead": "target",
        "phase_revs": 1,
        "lam_r1x": r1,
        "lam_r1y": 0.0,
        "lam_r1z": 0.0,
        "lam_r2x": 0.0,
        "lam_r2y": r_lam,
        "lam_r2z": 0.0,
        "lam_tof": 0.42 * 2.0 * math.pi * math.sqrt(r_lam**3 / mu),
        "lam_way": "short",
        "drag_alt": 400000.0,
        "drag_mass": 500.0,
        "drag_cd": 2.2,
        "drag_area": 1.5,
        "drag_revs": 3,
        "drag_rho": None,
        "raise_r1": r1,
        "raise_r2": r0 + 800000.0,
        "raise_di": math.radians(2.0),
        "ins_r": r1,
        "ins_v": math.sqrt(mu / r1) * 0.99,
        "ins_gamma": math.radians(2.0),
        "el_a": r1,
        "el_e": 0.0,
        "el_i": math.radians(51.6),
        "el_beta": 0.0,
        "gt_a": r1,
        "gt_e": 0.0,
        "gt_i": math.radians(51.6),
        "gt_raan": 0.0,
        "gt_arg": 0.0,
        "gt_nu": 0.0,
        "gt_orbits": 2,
        "cov_alt": 400000.0,
        "cov_elev": math.radians(25.0),
        "cov_i": math.radians(51.6),
        "cov_orbits": 2,
        "j2_a": r1,
        "j2_e": 0.0,
        "j2_i": math.radians(98.0),
        "launch_lat": math.radians(28.5),
        "launch_az": math.radians(90.0),
        "launch_alt": 400000.0,
        "dry": 500.0,
        "isp": 310.0,
        "ve": None,
        "growth": 0.0,
        "budget": {},
    }


def _on(seed: dict, flag: str, fallback: bool) -> bool:
    budget = seed.get("budget") or {}
    if flag not in budget:
        return fallback
    return bool(budget[flag])


def insertion_delta(mod, mu: float, radius_body: float, radius: float, speed: float, gamma: float) -> dict:
    """Same burnout arithmetic as ASTRO - OrbitInsertionFromBurnout.run."""
    energy = speed**2 / 2.0 - mu / radius
    cosine = math.cos(gamma)
    if abs(cosine) <= 1.0e-12:
        cosine = 0.0
    h = radius * speed * cosine
    closed = energy < 0.0 and h > 0.0
    if not closed:
        return {"dv": None, "where": "none"}
    a = -mu / (2.0 * energy)
    ecc = math.sqrt(max(0.0, 1.0 + 2.0 * energy * h * h / (mu * mu)))
    ra = a * (1.0 + ecc)
    nearly = ecc < 1e-4 and abs(gamma) < 1e-3
    if nearly:
        return {"dv": math.sqrt(mu / radius) - speed, "where": "burnout"}
    v_a = math.sqrt(mu * (2.0 / ra - 1.0 / a))
    return {"dv": math.sqrt(mu / ra) - v_a, "where": "apoapsis"}


def compute(seed: dict, mods: dict) -> dict:
    r0 = float(seed["R0"])
    mu = G0 * r0 * r0
    if seed.get("alt") is not None and seed.get("ecc") is not None:
        r1, r2 = mods["hohmann"].radii_from_altitude(r0, float(seed["alt"]), float(seed["ecc"]))
    else:
        r1 = float(seed["r1"])
        r2 = float(seed["r2"])
    rb = float(seed["rb"])
    hoh = mods["hohmann"].solve_transfer(mu, r1, r2, "radii")
    hoh_rec = mods["hohmann"].recommend_against_biparabolic(
        hoh.dv, mods["hohmann"].biparabolic_delta_v(mu, r1, r2)
    )
    bi = mods["bielliptic"].solve_transfer(mu, r1, r2, rb, "radii")
    strategy = seed.get("strategy") or "auto"
    if strategy == "auto":
        strategy = "bielliptic" if bi.recommendation == "bielliptic" else "hohmann"
    plane = mods["plane"].plane_change_impulse(math.sqrt(mu / float(seed["plane_a"])), float(seed["plane_di"]))
    geo = mods["geo"].evaluate(float(seed["geo_di"]), float(seed["geo_e"]), int(seed["geo_burns"]), float(seed["geo_years"]))
    cw = mods["cw"].evaluate(
        float(seed["cw_x"]), float(seed["cw_z"]), float(seed["cw_xd"]), float(seed["cw_zd"]),
        float(seed["cw_time"]), float(seed["cw_a"]), mu,
    )
    phase = mods["phase"].evaluate(
        float(seed["phase_r"]), float(seed["phase"]), str(seed["phase_lead"]), int(seed["phase_revs"]), mu,
    )
    r1v = (float(seed["lam_r1x"]), float(seed["lam_r1y"]), float(seed["lam_r1z"]))
    r2v = (float(seed["lam_r2x"]), float(seed["lam_r2y"]), float(seed["lam_r2z"]))
    lam = mods["lambert"].solve(
        r1v, r2v, float(seed["lam_tof"]), mu, str(seed["lam_way"]),
        math.sqrt(mu / math.hypot(*r1v)), math.sqrt(mu / math.hypot(*r2v)),
    )
    drag = mods["drag"].evaluate(
        float(seed["drag_alt"]), float(seed["drag_mass"]), float(seed["drag_cd"]),
        float(seed["drag_area"]), seed.get("drag_rho"),
    )
    dv1, dv2, dv_h = mods["raise"].hohmann_impulsive(mu, float(seed["raise_r1"]), float(seed["raise_r2"]))
    slower = math.sqrt(mu / max(float(seed["raise_r1"]), float(seed["raise_r2"])))
    di = float(seed["raise_di"])
    dv_plane = 0.0 if abs(di) < 1e-15 else mods["plane"].plane_change_impulse(slower, di)
    inserted = insertion_delta(mods["insert"], mu, r0, float(seed["ins_r"]), float(seed["ins_v"]), float(seed["ins_gamma"]))
    eclipse = mods["op"].circular_orbit_eclipse_fraction(r0, float(seed["el_a"]), float(seed["el_beta"]))
    body = mods["ground"].resolve_body(None if r0 == R0_EARTH else r0, None, None, None, None)
    gt_orbit = mods["ground"].orbit_from_elements(
        body.mu, float(seed["gt_a"]), float(seed["gt_e"]), float(seed["gt_i"]),
        float(seed["gt_raan"]), float(seed["gt_arg"]), float(seed["gt_nu"]), None, "elements",
    )
    sub = mods["ground"].subsatellite_at(body, gt_orbit, gt_orbit.period / 4.0, 0.0, 0.0)
    cover = mods["cover"].evaluate(mods["cover"].R0_EARTH + float(seed["cov_alt"]), float(seed["cov_elev"]))
    j2_body = mods["j2"].resolve_body(r0, None, None, None)
    rates = mods["j2"].evaluate_rates(j2_body, float(seed["j2_a"]), float(seed["j2_e"]), float(seed["j2_i"]))
    launch_i = mods["launch"].inclination_from_azimuth(float(seed["launch_lat"]), float(seed["launch_az"]))
    launch_assist = mods["launch"].rotation_assist(
        mods["launch"].OMEGA_E, mods["launch"].R_WGS84, float(seed["launch_lat"]), float(seed["launch_az"])
    )
    cw_null = math.hypot(cw["dv_null_x_m_s"], cw["dv_null_z_m_s"])
    cw_hold = math.hypot(cw["dv_hold_x_m_s"], cw["dv_hold_z_m_s"])
    pieces: list[tuple[str, float]] = []
    if _on(seed, "hohmann", strategy == "hohmann"):
        pieces += [("hohmann_depart", hoh.dv_depart), ("hohmann_arrive", hoh.dv_arrive)]
    if _on(seed, "bielliptic", strategy == "bielliptic"):
        pieces += [("bielliptic_1", bi.dv1), ("bielliptic_2", bi.dv2), ("bielliptic_3", bi.dv3)]
    if _on(seed, "plane", False):
        pieces.append(("plane_change", plane))
    if _on(seed, "geo", False):
        pieces += [("geo_ns", geo["dv_ns_m_s"]), ("geo_ew", geo["dv_ew_m_s"])]
    if _on(seed, "phasing", False):
        pieces.append(("phasing", float(phase["dv_total_m_s"])))
    if _on(seed, "lambert", False):
        pieces += [("lambert_depart", float(lam["dv1_m_s"])), ("lambert_arrive", float(lam["dv2_m_s"]))]
    if _on(seed, "cw", False):
        pieces.append((str(seed.get("cw_piece") or "cw_null"), cw_hold if seed.get("cw_piece") == "cw_hold" else cw_null))
    if _on(seed, "drag", False):
        pieces.append(("drag", float(drag["dv_per_rev_m_s"]) * float(seed["drag_revs"])))
    if _on(seed, "raise", False):
        pieces.append(("leo_raise", dv_h + dv_plane))
    if _on(seed, "insertion", False):
        pieces.append(("circularization", float(inserted["dv"] or 0.0)))
    dv_total = sum(piece for _name, piece in pieces)
    prop = None
    if seed.get("dry") and (seed.get("isp") or seed.get("ve")) and pieces:
        ve = mods["vac"].exhaust_speed(seed.get("isp"), seed.get("ve"))
        _final, propellant, _wet = mods["vac"].propellant_mass(
            float(seed["dry"]), float(seed.get("growth") or 0.0), dv_total, ve
        )
        prop = propellant
    return {
        "ok": True,
        "mu": mu,
        "r0": r0,
        "r1": r1,
        "r2": r2,
        "rb": rb,
        "strategy": strategy,
        "hohmann_dv": hoh.dv,
        "hohmann_dv_depart": hoh.dv_depart,
        "hohmann_dv_arrive": hoh.dv_arrive,
        "hohmann_tof": hoh.tof,
        "hohmann_recommendation": hoh_rec,
        "bielliptic_dv": bi.dv,
        "bielliptic_dv1": bi.dv1,
        "bielliptic_dv2": bi.dv2,
        "bielliptic_dv3": bi.dv3,
        "bielliptic_tof": bi.tof,
        "bielliptic_recommendation": bi.recommendation,
        "plane_dv": plane,
        "geo_ns": geo["dv_ns_m_s"],
        "geo_ew": geo["dv_ew_m_s"],
        "geo_total": geo["dv_total_m_s"],
        "cw_x": cw["x_m"],
        "cw_z": cw["z_m"],
        "cw_null": cw_null,
        "cw_hold": cw_hold,
        "phase_dv": float(phase["dv_total_m_s"]),
        "lambert_dv1": float(lam["dv1_m_s"]),
        "lambert_dv2": float(lam["dv2_m_s"]),
        "drag_dv": float(drag["dv_per_rev_m_s"]),
        "raise_dv": dv_h + dv_plane,
        "raise_plane": dv_plane,
        "raise_gravity": 0.0,
        "insertion_dv": inserted["dv"],
        "insertion_where": inserted["where"],
        "eclipse_fraction": eclipse,
        "gt_lat": sub.lat_geodetic,
        "gt_lon": sub.lon,
        "coverage_swath": float(cover["swath_m"]),
        "coverage_revisit": int(cover["revisit_periods"]),
        "coverage_lambda": float(cover["lambda_rad"]),
        "j2_node": rates.omega_dot_node,
        "j2_apsis": rates.omega_dot_apsis,
        "launch_inc": launch_i,
        "launch_assist": launch_assist,
        "dv_total": dv_total,
        "m_propellant": prop,
        "pieces": [{"name": name, "dv": dv} for name, dv in pieces],
        "_hoh": hoh,
        "_bi": bi,
    }


def density_table(drag_mod) -> list[list[float]]:
    """Sample the drag program's density. The page interpolates log(rho) between nodes."""
    rows = []
    alt = 0.0
    while alt <= 800000.0 + 1.0:
        rho, _source = drag_mod.density_at(alt, None)
        rows.append([alt, float(rho)])
        alt += 5000.0
    return rows


def read_lab_js() -> str:
    return "\n".join((SKILL_DIR / "js" / name).read_text(encoding="utf-8") for name in JS_FILES)


def embed_json(payload: object) -> str:
    return json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c")


def bake_html(seed: dict, pack: dict) -> str:
    template = (SKILL_DIR / "viewer" / "template.html").read_text(encoding="utf-8")
    three = (SKILL_DIR / "viewer" / "three.min.js").read_text(encoding="utf-8")
    if "</script>" in three.lower():
        three = three.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    html = template.replace("__TITLE__", PLOT_TITLE)
    html = html.replace("__SEED_JSON__", embed_json(seed))
    html = html.replace("__PACK_JSON__", embed_json(pack))
    html = html.replace("__THREE_SOURCE__", three)
    html = html.replace("__LAB_JS__", read_lab_js().replace("</", "<\\/"))
    for token in ("__TITLE__", "__SEED_JSON__", "__PACK_JSON__", "__THREE_SOURCE__", "__LAB_JS__"):
        if token in html:
            raise DesignError(f"viewer template still contains {token}")
    return html


def write_png(path: Path, result: dict) -> None:
    import matplotlib.pyplot as plt

    hoh = result["_hoh"]
    bi = result["_bi"]

    def polar(peri: float, apo: float, nu0: float, nu1: float, count: int = 181):
        a = 0.5 * (peri + apo)
        ecc = 0.0 if math.isclose(peri, apo, rel_tol=1e-12) else (apo - peri) / (apo + peri)
        xs = []
        ys = []
        for index in range(count):
            nu = nu0 + (nu1 - nu0) * index / (count - 1)
            radius = a * (1.0 - ecc * ecc) / (1.0 + ecc * math.cos(nu))
            xs.append(radius * math.cos(nu) / 1000.0)
            ys.append(radius * math.sin(nu) / 1000.0)
        return xs, ys

    fig, ax = plt.subplots(figsize=(7.2, 7.2))
    theta = [2.0 * math.pi * i / 360 for i in range(361)]
    ax.plot([result["r1"] * math.cos(t) / 1000.0 for t in theta], [result["r1"] * math.sin(t) / 1000.0 for t in theta], color="#1a5276", lw=1.0)
    ax.plot([result["r2"] * math.cos(t) / 1000.0 for t in theta], [result["r2"] * math.sin(t) / 1000.0 for t in theta], color="#117a65", lw=1.0)
    hx, hy = polar(hoh.r_depart if hoh.direction != "inward" else hoh.r_arrive, hoh.r_arrive if hoh.direction != "inward" else hoh.r_depart, 0.0, math.pi)
    ax.plot(hx, hy, color="#1b4f72", lw=1.8, label="Hohmann")
    bx, by = polar(min(result["r1"], result["rb"]), max(result["r1"], result["rb"]), 0.0, math.pi)
    ax.plot(bx, by, color="#6c3483", lw=1.4, label="bielliptic")
    cx, cy = polar(min(result["r2"], result["rb"]), max(result["r2"], result["rb"]), math.pi, 2.0 * math.pi)
    ax.plot(cx, cy, color="#922b21", lw=1.4)
    earth = plt.Circle((0.0, 0.0), float(result["r0"]) / 1000.0, color="#8fb7d6", zorder=0)
    ax.add_patch(earth)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X [km]")
    ax.set_ylabel("Y [km]")
    ax.set_title(PLOT_TITLE)
    ax.legend(frameon=False)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def emit(result: dict, png: Path, html: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("strategy", result["strategy"])
    print_kv("r1_m", result["r1"])
    print_kv("r2_m", result["r2"])
    print_kv("rb_m", result["rb"])
    print_kv("hohmann_dv_m_s", result["hohmann_dv"])
    print_kv("hohmann_tof_s", result["hohmann_tof"])
    print_kv("hohmann_recommendation", result["hohmann_recommendation"])
    print_kv("bielliptic_dv_m_s", result["bielliptic_dv"])
    print_kv("bielliptic_tof_s", result["bielliptic_tof"])
    print_kv("bielliptic_recommendation", result["bielliptic_recommendation"])
    print_kv("plane_dv_m_s", result["plane_dv"])
    print_kv("geo_ns_m_s", result["geo_ns"])
    print_kv("geo_ew_m_s", result["geo_ew"])
    print_kv("cw_null_m_s", result["cw_null"])
    print_kv("phase_dv_m_s", result["phase_dv"])
    print_kv("lambert_dv1_m_s", result["lambert_dv1"])
    print_kv("lambert_dv2_m_s", result["lambert_dv2"])
    print_kv("drag_dv_per_rev_m_s", result["drag_dv"])
    print_kv("raise_dv_m_s", result["raise_dv"])
    print_kv("raise_note", "impulsive reference; gravity loss is 0 in this lab")
    print_kv("insertion_dv_m_s", result["insertion_dv"])
    print_kv("coverage_swath_m", result["coverage_swath"])
    print_kv("coverage_revisit_periods", result["coverage_revisit"])
    print_kv("dv_total_m_s", result["dv_total"])
    print_kv("m_propellant_kg", result["m_propellant"])
    print_kv("graph", str(png))
    print_kv("viewer", str(html))


def _close(got: object, expected: object) -> bool:
    if isinstance(expected, str) or isinstance(got, str):
        return got == expected
    if expected is None or got is None:
        return got is None and expected is None
    scale = max(abs(float(expected)), 1.0)
    return abs(float(got) - float(expected)) <= CHECK_TOL * scale


def node_parity(pack: dict, cases: list[tuple[str, dict, dict]]) -> str:
    node = shutil.which("node")
    if node is None:
        return "skipped"
    runner = r"""
const vm = require("vm");
const fs = require("fs");
const code = fs.readFileSync(process.argv[2], "utf8");
const payload = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const context = { Math: Math, console: console, isFinite: isFinite, Number: Number, String: String, JSON: JSON };
vm.createContext(context);
vm.runInContext(code, context);
const designs = payload.cases.map(function (item) {
  try {
    return context.Lab.compute(item.seed, payload.pack);
  } catch (err) {
    return { ok: false, error: String(err && err.message || err) };
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
            json.dumps({"pack": pack, "cases": [{"name": name, "seed": seed} for name, seed, _expected in cases]}),
            encoding="utf-8",
        )
        completed = subprocess.run([node, str(script), str(source), str(payload)], text=True, capture_output=True, check=False)
        if completed.returncode != 0:
            raise DesignError(completed.stderr.strip() or "node parity failed")
        report = json.loads(completed.stdout)
    for (name, _seed, expected), got in zip(cases, report["designs"]):
        if not got.get("ok"):
            raise DesignError(f"{name} JS failed: {got.get('error')}")
        for key in PARITY_KEYS:
            if not _close(got.get(key), expected.get(key)):
                raise DesignError(f"{name} {key}: JS {got.get(key)!r} != Python {expected.get(key)!r}")
    return "pass"


def public_seed(seed: dict) -> dict:
    return {key: value for key, value in seed.items()}


def run_check() -> int:
    mods = modules()
    seed = default_seed()
    point = compute(seed, mods)
    half = default_seed()
    radius = float(half["r1"])
    half_mu = G0 * R0_EARTH * R0_EARTH
    half["lam_r1x"] = radius
    half["lam_r1y"] = 0.0
    half["lam_r1z"] = 0.0
    half["lam_r2x"] = -radius
    half["lam_r2y"] = 0.0
    half["lam_r2z"] = 0.0
    half["lam_tof"] = math.pi * math.sqrt(radius**3 / half_mu)
    half_point = compute(half, mods)
    if half_point["lambert_dv1"] > 1.0e-3 or half_point["lambert_dv2"] > 1.0e-3:
        print("CHECK FAIL: equal-radius 180 degree Lambert is not circular", file=sys.stderr)
        return 1
    chord = default_seed()
    r_peri = 7000.0e3
    r_apo = 14000.0e3
    semimajor = 0.5 * (r_peri + r_apo)
    chord["lam_r1x"] = r_peri
    chord["lam_r1y"] = 0.0
    chord["lam_r1z"] = 0.0
    chord["lam_r2x"] = -r_apo
    chord["lam_r2y"] = 0.0
    chord["lam_r2z"] = 0.0
    chord["lam_tof"] = math.pi * math.sqrt(semimajor**3 / half_mu)
    chord_point = compute(chord, mods)
    v_peri = math.sqrt(half_mu * (2.0 / r_peri - 1.0 / semimajor))
    v_apo = math.sqrt(half_mu * (2.0 / r_apo - 1.0 / semimajor))
    if abs(chord_point["lambert_dv1"] - (v_peri - math.sqrt(half_mu / r_peri))) > 1.0:
        print("CHECK FAIL: 180 degree Hohmann departure burn", file=sys.stderr)
        return 1
    if abs(chord_point["lambert_dv2"] - (math.sqrt(half_mu / r_apo) - v_apo)) > 1.0:
        print("CHECK FAIL: 180 degree Hohmann arrival burn", file=sys.stderr)
        return 1
    other = compute(default_seed(6_300_000.0), mods)
    if other["r1"] <= 6_300_000.0 or other["r2"] <= other["r1"]:
        print("CHECK FAIL: --R0 did not rebuild the default orbits", file=sys.stderr)
        return 1
    if abs(other["j2_node"] - point["j2_node"]) <= 0.0:
        print("CHECK FAIL: J2 nodal rate ignored the new radius", file=sys.stderr)
        return 1
    pack = {"density": density_table(mods["drag"])}
    parity = node_parity(
        pack,
        [("default", seed, point), ("half", half, half_point), ("chord", chord, chord_point)],
    )
    print_kv("node_parity", parity)
    if point["bielliptic_dv"] <= 0.0 or point["hohmann_dv"] <= 0.0:
        print("CHECK FAIL: transfer delta-v", file=sys.stderr)
        return 1
    if point["coverage_swath"] <= 0.0:
        print("CHECK FAIL: coverage swath", file=sys.stderr)
        return 1
    print_kv("check", "pass")
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bake the orbit design lab.")
    parser.add_argument("--r1", type=float, default=None)
    parser.add_argument("--r2", type=float, default=None)
    parser.add_argument("--alt", type=float, default=None)
    parser.add_argument("--ecc", type=float, default=None)
    parser.add_argument("--rb", type=float, default=None)
    parser.add_argument("--R0", type=float, default=None)
    parser.add_argument("--strategy", choices=("auto", "hohmann", "bielliptic"), default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        try:
            return run_check()
        except (DesignError, ValueError) as exc:
            print(f"CHECK FAIL: {exc}", file=sys.stderr)
            return 1
    mods = modules()
    seed = default_seed(args.R0 if args.R0 is not None else R0_EARTH)
    if args.alt is not None or args.ecc is not None:
        if args.alt is None or args.ecc is None:
            print("error: pass both --alt and --ecc", file=sys.stderr)
            return 2
        seed["alt"] = args.alt
        seed["ecc"] = args.ecc
        seed["r1"] = None
        seed["r2"] = None
    else:
        if args.r1 is not None:
            seed["r1"] = args.r1
        if args.r2 is not None:
            seed["r2"] = args.r2
    if args.rb is not None:
        seed["rb"] = args.rb
    if args.strategy is not None:
        seed["strategy"] = args.strategy
    try:
        result = compute(seed, mods)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if seed.get("alt") is not None:
        seed["r1"] = result["r1"]
        seed["r2"] = result["r2"]
        seed["alt"] = None
        seed["ecc"] = None
    winning = "bielliptic" if result["strategy"] == "bielliptic" else "hohmann"
    seed["budget"] = {winning: True}
    result = compute(seed, mods)
    pack = {"density": density_table(mods["drag"])}
    png = Path(args.out).resolve() if args.out else SKILL_DIR / "orbit_design_lab.png"
    if png.suffix.lower() != ".png":
        png = png.with_suffix(".png")
    html_path = png.with_suffix(".html")
    try:
        write_png(png, result)
        html_path.write_text(bake_html(public_seed(seed), pack), encoding="utf-8")
    except (OSError, DesignError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, png, html_path)
    if args.open:
        webbrowser.open(html_path.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
