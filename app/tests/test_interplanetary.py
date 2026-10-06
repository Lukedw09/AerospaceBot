"""Multi-case checks for the LEO-to-planet patched-conic programs.

Expected numbers come from the formula-catalogue expressions (vis-viva,
elliptic half-period, Hohmann phase angle, synodic period, inclined excess
speed, sphere of influence, and characteristic energy), not from a copied
textbook delta-v. The programs are the system under test.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["AUTH_DISABLED"] = "1"

from app.catalog import load_catalog, tool_by_name
from app.runner import run_tool
from app.server import build_server

ROOT = Path(__file__).resolve().parents[2]
BODY_SCRIPT = ROOT / "skills" / "ASTRO - SolarSystemBody" / "solar_system_body.py"
HELIO_SCRIPT = ROOT / "skills" / "ASTRO - HeliocentricHohmann" / "heliocentric_hohmann.py"
LEO_SCRIPT = ROOT / "skills" / "ASTRO - LeoToLowOrbit" / "leo_to_low_orbit.py"
BODY_JSON = ROOT / "skills" / "ASTRO - SolarSystemBody" / "bodies.json"
SAMPLE_PNGS = (
    ROOT / "skills" / "ASTRO - HeliocentricHohmann" / "heliocentric_hohmann.png",
    ROOT / "skills" / "ASTRO - LeoToLowOrbit" / "leo_to_low_orbit.png",
)

G0 = 9.80665
R0_EARTH = 6.3742e6
ORBIT_ORDER = (
    "mercury",
    "venus",
    "earth",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
)
TARGETS = tuple(name for name in ORBIT_ORDER if name != "earth")
REL = 1e-6

FORMULAS: dict = {}
EVALUATE = None


def setUpModule() -> None:
    global FORMULAS, EVALUATE
    path = ROOT / "skills" / "FormulaCatalouge" / "checks" / "check_formulas.py"
    spec = importlib.util.spec_from_file_location("catalogue_check_formulas", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the formula catalogue checker")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    text = (ROOT / "skills" / "FormulaCatalouge" / "formulas.md").read_text(encoding="utf-8")
    FORMULAS = {formula.name: formula for formula in module.parse_formulas(text)}
    EVALUATE = module.evaluate
    for folder in (
        ROOT / "skills" / "ASTRO - SolarSystemBody",
        ROOT / "skills" / "ASTRO - HeliocentricHohmann",
        ROOT / "skills" / "ASTRO - LeoToLowOrbit",
    ):
        if str(folder) not in sys.path:
            sys.path.insert(0, str(folder))


def cat(name: str, **values: float) -> float:
    formula = FORMULAS[name]
    env = dict(values)
    if "pi" in formula.symbols:
        env["pi"] = math.pi
    return EVALUATE(formula.expr, env)


def close(actual: float, expected: float, rel: float = REL, tol: float = 0.0) -> bool:
    if math.isinf(actual) or math.isinf(expected):
        return math.isinf(actual) and math.isinf(expected)
    return abs(actual - expected) <= tol + rel * max(abs(actual), abs(expected))


def wrap_phase(angle: float) -> float:
    """Specified print range (-pi, pi]."""
    turned = math.remainder(angle, 2.0 * math.pi)
    if turned <= -math.pi:
        turned += 2.0 * math.pi
    return turned


def load_table() -> dict:
    raw = json.loads(BODY_JSON.read_text(encoding="utf-8"))
    bodies = {}
    for row in raw["bodies"]:
        name = row["name"]
        mu = G0 * R0_EARTH * R0_EARTH if name == "earth" else row["mu_m3_s2"]
        bodies[name] = {
            "class": row["class"],
            "mu": mu,
            "radius": row["radius_m"],
            "a": row["a_helio_m"],
            "e": row["e"],
            "i_deg": row["i_deg"],
        }
    return bodies


def radius_of(body: dict, mode: str) -> float:
    semi = body["a"]
    ecc = body["e"]
    if mode == "mean":
        return semi
    if mode == "perihelion":
        return semi * (1.0 - ecc)
    if mode == "aphelion":
        return semi * (1.0 + ecc)
    raise AssertionError(mode)


def run(script: Path, args: list[str]) -> tuple[int, dict[str, str], str, str]:
    """Run one program. ``--out nul`` is replaced with a temporary PNG.

    Matplotlib cannot write a figure onto the Windows null device.
    """
    cleaned: list[str] = []
    index = 0
    discard_plot = False
    while index < len(args):
        if args[index] == "--out" and index + 1 < len(args) and args[index + 1] == os.devnull:
            discard_plot = True
            index += 2
            continue
        cleaned.append(args[index])
        index += 1
    if discard_plot:
        with tempfile.TemporaryDirectory() as tmp:
            return _execute(script, [*cleaned, "--out", str(Path(tmp) / "out.png")])
    return _execute(script, cleaned)


def _execute(script: Path, args: list[str]) -> tuple[int, dict[str, str], str, str]:
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )
    data: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        data[key] = value
    return proc.returncode, data, proc.stdout, proc.stderr


def records(stdout: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in stdout.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key == "name":
            current = {}
            found.append(current)
        if current is not None:
            current[key] = value
    return found


def num(data: dict[str, str], key: str) -> float:
    return float(data[key])


def expected_transfer(mu: float, r1: float, r2: float, i1: float, i2: float) -> dict:
    semi = 0.5 * (r1 + r2)
    if r2 > r1:
        direction, sense_depart, sense_arrive = "outward", "prograde", "retrograde"
    elif r1 > r2:
        direction, sense_depart, sense_arrive = "inward", "retrograde", "prograde"
    else:
        direction, sense_depart, sense_arrive = "coast", "none", "none"
    eccentricity = abs(r2 - r1) / (r1 + r2)
    vt1 = cat("vis_viva", mu=mu, r=r1, a=semi)
    vt2 = cat("vis_viva", mu=mu, r=r2, a=semi)
    vp1 = cat("vis_viva", mu=mu, r=r1, a=r1)
    vp2 = cat("vis_viva", mu=mu, r=r2, a=r2)
    n1 = cat("mean_motion", mu=mu, a=r1)
    n2 = cat("mean_motion", mu=mu, a=r2)
    tof = cat("elliptic_half_period", a=semi, mu=mu)
    period = cat("orbital_period", a=semi, mu=mu)
    phase = cat("hohmann_phase_angle", n2=n2, tof=tof)
    di = abs(i2 - i1)
    synodic = math.inf if n1 == n2 else cat("synodic_period", n1=n1, n2=n2)
    return {
        "a": semi,
        "e": eccentricity,
        "direction": direction,
        "sense_depart": sense_depart,
        "sense_arrive": sense_arrive,
        "vt1": vt1,
        "vt2": vt2,
        "vp1": vp1,
        "vp2": vp2,
        "n1": n1,
        "n2": n2,
        "tof": tof,
        "period": period,
        "phase": wrap_phase(phase),
        "phase_raw": phase,
        "di": di,
        "synodic": synodic,
        "vinf_depart_coplanar": cat("inclined_excess_speed", v1=vt1, v2=vp1, di=0.0),
        "vinf_arrive_coplanar": cat("inclined_excess_speed", v1=vt2, v2=vp2, di=0.0),
        "vinf_depart_inclined": cat("inclined_excess_speed", v1=vt1, v2=vp1, di=di),
        "vinf_arrive_inclined": cat("inclined_excess_speed", v1=vt2, v2=vp2, di=di),
        "energy": cat("specific_orbital_energy", mu=mu, a=semi),
    }


def hyperbola_burn(mu: float, radius: float, vinf: float) -> tuple[float, float, float]:
    c3 = cat("characteristic_energy", vinf=vinf)
    semi = cat("semimajor_from_characteristic_energy", mu=mu, C3=c3)
    v_peri = cat("vis_viva", mu=mu, r=radius, a=semi)
    v_circ = cat("vis_viva", mu=mu, r=radius, a=radius)
    return v_peri - v_circ, v_peri, v_circ


def expected_mission(table: dict, target: str, h_leo: float, h_arrive: float, mode: str) -> dict:
    earth = table["earth"]
    body = table[target]
    sun = table["sun"]["mu"]
    r1 = radius_of(earth, mode)
    r2 = radius_of(body, mode)
    i2 = math.radians(body["i_deg"])
    transfer = expected_transfer(table["sun"]["mu"], r1, r2, 0.0, i2)
    r_leo = earth["radius"] + h_leo
    r_low = body["radius"] + h_arrive
    depart_at_depart = hyperbola_burn(earth["mu"], r_leo, transfer["vinf_depart_inclined"])
    capture_at_depart = hyperbola_burn(body["mu"], r_low, transfer["vinf_arrive_coplanar"])
    depart_at_arrive = hyperbola_burn(earth["mu"], r_leo, transfer["vinf_depart_coplanar"])
    capture_at_arrive = hyperbola_burn(body["mu"], r_low, transfer["vinf_arrive_inclined"])
    total_depart = depart_at_depart[0] + capture_at_depart[0]
    total_arrive = depart_at_arrive[0] + capture_at_arrive[0]
    span = max(abs(total_depart), abs(total_arrive), 1.0)
    if abs(total_depart - total_arrive) <= 1e-9 * span or total_depart < total_arrive:
        chosen = "depart"
        depart, capture, vinfs, total = depart_at_depart, capture_at_depart, (
            transfer["vinf_depart_inclined"],
            transfer["vinf_arrive_coplanar"],
        ), total_depart
    else:
        chosen = "arrive"
        depart, capture, vinfs, total = depart_at_arrive, capture_at_arrive, (
            transfer["vinf_depart_coplanar"],
            transfer["vinf_arrive_inclined"],
        ), total_arrive
    return {
        "transfer": transfer,
        "r_leo": r_leo,
        "r_low": r_low,
        "class": body["class"],
        "plane_change_at": chosen,
        "dv_depart": depart[0],
        "v_peri_depart": depart[1],
        "v_circ_depart": depart[2],
        "dv_capture": capture[0],
        "v_peri_arrive": capture[1],
        "v_circ_arrive": capture[2],
        "dv_total": total,
        "dv_total_depart": total_depart,
        "dv_total_arrive": total_arrive,
        "vinf_depart": vinfs[0],
        "vinf_arrive": vinfs[1],
        "c3": cat("characteristic_energy", vinf=vinfs[0]),
        "soi_earth": cat(
            "sphere_of_influence_radius", D=r1, mu2=earth["mu"], mu1=sun
        ),
        "soi_target": cat(
            "sphere_of_influence_radius", D=r2, mu2=body["mu"], mu1=sun
        ),
    }


class CatalogueAnchorTests(unittest.TestCase):
    def test_records_match_the_written_expressions(self) -> None:
        self.assertTrue(close(cat("vis_viva", mu=1, r=1, a=2.5), math.sqrt(1.6)))
        self.assertTrue(close(cat("vis_viva", mu=1, r=4, a=2.5), math.sqrt(0.1)))
        self.assertTrue(close(cat("elliptic_half_period", a=2.5, mu=1), math.pi * math.sqrt(2.5**3)))
        self.assertTrue(close(cat("orbital_period", a=2.5, mu=1), 2 * math.pi * math.sqrt(2.5**3)))
        self.assertTrue(close(cat("inclined_excess_speed", v1=3, v2=1, di=0), 2))
        self.assertTrue(close(cat("inclined_excess_speed", v1=1, v2=1, di=math.pi), 2))
        self.assertTrue(close(cat("synodic_period", n1=2, n2=1), 2 * math.pi))
        self.assertTrue(close(cat("hohmann_phase_angle", n2=1, tof=math.pi / 2), math.pi / 2))
        self.assertTrue(close(cat("characteristic_energy", vinf=3), 9))
        self.assertTrue(close(cat("sphere_of_influence_radius", D=10, mu2=1, mu1=32), 10 * (1 / 32) ** 0.4))
        allow = (ROOT / "skills" / "FormulaCatalouge" / "checks" / "check.md").read_text(encoding="utf-8")
        self.assertIn("`inclined_excess_speed` (flight): coplanar_reduction, equal_speed_half_turn", allow)
        self.assertIn("`hohmann_phase_angle` (flight): quarter_coast, fast_target", allow)
        self.assertIn("`synodic_period` (flight): twice_and_one, either_order", allow)


class SolarSystemBodyTests(unittest.TestCase):
    def test_each_body_matches_the_table(self) -> None:
        table = load_table()
        for name, body in table.items():
            with self.subTest(body=name):
                code, data, stdout, stderr = run(BODY_SCRIPT, ["--body", f"  {name.upper()} "])
                self.assertEqual(code, 0, stderr)
                self.assertEqual(data["name"], name)
                self.assertEqual(data["class"], body["class"])
                self.assertTrue(close(num(data, "mu_m3_s2"), body["mu"], tol=1.0))
                self.assertTrue(close(num(data, "radius_m"), body["radius"], tol=1.0))
                if name == "sun":
                    self.assertEqual(data["a_helio_m"], "none")
                    self.assertEqual(data["e"], "none")
                    self.assertEqual(data["i_rad"], "none")
                    self.assertIn("no heliocentric orbit", stdout)
                    continue
                self.assertTrue(close(num(data, "a_helio_m"), body["a"]))
                self.assertTrue(close(num(data, "e"), body["e"]))
                self.assertTrue(close(num(data, "i_deg"), body["i_deg"]))
                self.assertTrue(close(num(data, "i_rad"), math.radians(body["i_deg"])))
                self.assertTrue(close(num(data, "r_mean_m"), radius_of(body, "mean")))
                self.assertTrue(close(num(data, "r_perihelion_m"), radius_of(body, "perihelion")))
                self.assertTrue(close(num(data, "r_aphelion_m"), radius_of(body, "aphelion")))
                self.assertGreater(num(data, "r_aphelion_m"), num(data, "r_mean_m"))
                self.assertGreater(num(data, "r_mean_m"), num(data, "r_perihelion_m"))

    def test_list_order_and_earth_constants(self) -> None:
        code, _, stdout, stderr = run(BODY_SCRIPT, ["--list"])
        self.assertEqual(code, 0, stderr)
        names = [row["name"] for row in records(stdout)]
        self.assertEqual(names, ["sun", *ORBIT_ORDER])
        earth = next(row for row in records(stdout) if row["name"] == "earth")
        self.assertTrue(close(float(earth["mu_m3_s2"]), G0 * R0_EARTH * R0_EARTH, tol=1.0))
        self.assertTrue(close(float(earth["radius_m"]), R0_EARTH, tol=0.0))
        self.assertEqual(earth["i_deg"], "0")
        self.assertEqual(earth["mu_source"], "g0_R0")
        pluto = next(row for row in records(stdout) if row["name"] == "pluto")
        neptune = next(row for row in records(stdout) if row["name"] == "neptune")
        self.assertEqual(pluto["class"], "dwarf")
        self.assertLess(float(pluto["r_perihelion_m"]), float(neptune["a_helio_m"]))
        previous = 0.0
        for name in ORBIT_ORDER:
            row = next(item for item in records(stdout) if item["name"] == name)
            semi = float(row["a_helio_m"])
            self.assertGreater(semi, previous)
            previous = semi

    def test_rejects_unknown_and_conflicting_flags(self) -> None:
        missing_code, _, _, missing_err = run(BODY_SCRIPT, [])
        self.assertEqual(missing_code, 1)
        self.assertIn("--body", missing_err)
        unknown_code, _, _, unknown_err = run(BODY_SCRIPT, ["--body", "moon"])
        self.assertEqual(unknown_code, 1)
        self.assertIn("unknown body", unknown_err)
        both_code, _, _, both_err = run(BODY_SCRIPT, ["--body", "mars", "--list"])
        self.assertEqual(both_code, 1)
        self.assertIn("not both", both_err)

    def test_builtin_check(self) -> None:
        code, _, stdout, stderr = run(BODY_SCRIPT, ["--check"])
        self.assertEqual(code, 0, stderr)
        self.assertNotIn("CHECK FAIL", stdout + stderr)


class HeliocentricTests(unittest.TestCase):
    def assert_transfer(self, data: dict[str, str], mu: float, r1: float, r2: float, i1: float, i2: float) -> None:
        expect = expected_transfer(mu, r1, r2, i1, i2)
        self.assertEqual(data["direction"], expect["direction"])
        self.assertEqual(data["sense_depart"], expect["sense_depart"])
        self.assertEqual(data["sense_arrive"], expect["sense_arrive"])
        self.assertTrue(close(num(data, "a_m"), expect["a"]))
        self.assertTrue(close(num(data, "e"), expect["e"], tol=1e-9))
        self.assertTrue(close(num(data, "di_rad"), expect["di"], tol=1e-9))
        self.assertTrue(close(num(data, "v_planet_depart_m_s"), expect["vp1"]))
        self.assertTrue(close(num(data, "v_planet_arrive_m_s"), expect["vp2"]))
        self.assertTrue(close(num(data, "v_transfer_depart_m_s"), expect["vt1"]))
        self.assertTrue(close(num(data, "v_transfer_arrive_m_s"), expect["vt2"]))
        self.assertTrue(close(num(data, "tof_s"), expect["tof"]))
        self.assertTrue(close(num(data, "period_s"), expect["period"]))
        self.assertTrue(close(num(data, "tof_s"), 0.5 * num(data, "period_s"), tol=1e-6))
        self.assertTrue(close(num(data, "n_depart_rad_s"), expect["n1"]))
        self.assertTrue(close(num(data, "n_arrive_rad_s"), expect["n2"]))
        self.assertTrue(close(num(data, "phase_rad"), expect["phase"], tol=1e-6))
        self.assertGreater(num(data, "phase_rad"), -math.pi)
        self.assertLessEqual(num(data, "phase_rad"), math.pi)
        turned = math.remainder(num(data, "phase_rad") - expect["phase_raw"], 2.0 * math.pi)
        self.assertTrue(close(turned, 0.0, tol=1e-5))
        if math.isinf(expect["synodic"]):
            self.assertEqual(data["synodic_s"], "inf")
        else:
            self.assertTrue(close(num(data, "synodic_s"), expect["synodic"]))
        self.assertTrue(close(num(data, "vinf_depart_coplanar_m_s"), abs(expect["vt1"] - expect["vp1"]), tol=1e-6))
        self.assertTrue(close(num(data, "vinf_arrive_coplanar_m_s"), abs(expect["vt2"] - expect["vp2"]), tol=1e-6))
        self.assertTrue(close(num(data, "vinf_depart_coplanar_m_s"), expect["vinf_depart_coplanar"], tol=1e-6))
        self.assertTrue(close(num(data, "vinf_arrive_coplanar_m_s"), expect["vinf_arrive_coplanar"], tol=1e-6))
        self.assertTrue(close(num(data, "vinf_depart_inclined_m_s"), expect["vinf_depart_inclined"]))
        self.assertTrue(close(num(data, "vinf_arrive_inclined_m_s"), expect["vinf_arrive_inclined"]))
        depart_speed = num(data, "v_transfer_depart_m_s")
        arrive_speed = num(data, "v_transfer_arrive_m_s")
        energy_depart = cat("specific_orbital_energy_from_speed", v=depart_speed, mu=mu, r=r1)
        energy_arrive = cat("specific_orbital_energy_from_speed", v=arrive_speed, mu=mu, r=r2)
        self.assertTrue(close(energy_depart, expect["energy"]))
        self.assertTrue(close(energy_arrive, expect["energy"]))
        self.assertTrue(close(r1 * depart_speed, r2 * arrive_speed))
        if expect["di"] == 0.0:
            self.assertTrue(close(num(data, "vinf_depart_inclined_m_s"), num(data, "vinf_depart_coplanar_m_s"), tol=1e-6))
            self.assertTrue(close(num(data, "vinf_arrive_inclined_m_s"), num(data, "vinf_arrive_coplanar_m_s"), tol=1e-6))
        else:
            self.assertGreater(num(data, "vinf_depart_inclined_m_s"), num(data, "vinf_depart_coplanar_m_s"))
            self.assertGreater(num(data, "vinf_arrive_inclined_m_s"), num(data, "vinf_arrive_coplanar_m_s"))

    def test_unit_radii_are_the_hand_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "unit.png"
            code, data, _, stderr = run(
                HELIO_SCRIPT,
                ["--r1", "1", "--r2", "4", "--mu", "1", "--i1", "0", "--i2", "0", "--out", str(out)],
            )
            self.assertEqual(code, 0, stderr)
            png = out.read_bytes()
        self.assert_transfer(data, 1.0, 1.0, 4.0, 0.0, 0.0)
        self.assertTrue(close(num(data, "a_m"), 2.5, tol=0.0))
        self.assertTrue(close(num(data, "e"), 0.6, tol=1e-9))
        self.assertTrue(close(num(data, "v_planet_depart_m_s"), 1.0, tol=1e-9))
        self.assertTrue(close(num(data, "v_planet_arrive_m_s"), 0.5, tol=1e-9))
        self.assertTrue(close(num(data, "v_transfer_depart_m_s"), math.sqrt(1.6)))
        self.assertTrue(close(num(data, "v_transfer_arrive_m_s"), math.sqrt(0.1)))
        self.assertEqual(data["direction"], "outward")
        self.assertTrue(png.startswith(b"\x89PNG"))

    def test_zero_inclination_and_equal_orbits(self) -> None:
        code, flat, _, stderr = run(
            HELIO_SCRIPT,
            ["--r1", "2", "--r2", "5", "--mu", "3", "--i1", "0.4", "--i2", "0.4", "--out", os.devnull],
        )
        self.assertEqual(code, 0, stderr)
        self.assert_transfer(flat, 3.0, 2.0, 5.0, 0.4, 0.4)
        turned = run(
            HELIO_SCRIPT,
            ["--r1", "1e11", "--r2", "1e11", "--mu", "1.32712e20", "--i1", "0", "--i2", str(math.pi), "--out", os.devnull],
        )
        self.assertEqual(turned[0], 0, turned[3])
        data = turned[1]
        self.assertEqual(data["direction"], "coast")
        self.assertEqual(data["sense_depart"], "none")
        self.assertEqual(data["synodic_s"], "inf")
        self.assertTrue(close(num(data, "phase_rad"), 0.0, tol=1e-6))
        self.assertTrue(close(num(data, "vinf_depart_coplanar_m_s"), 0.0, tol=1e-4))
        speed = num(data, "v_planet_depart_m_s")
        self.assertTrue(close(num(data, "vinf_depart_inclined_m_s"), 2.0 * speed))
        self.assertTrue(close(num(data, "vinf_arrive_inclined_m_s"), 2.0 * speed))

    def test_named_targets_from_earth_and_radius_modes(self) -> None:
        table = load_table()
        sun = table["sun"]["mu"]
        tofs = {}
        synodics = {}
        for target in TARGETS:
            for mode in ("mean", "perihelion", "aphelion"):
                with self.subTest(target=target, mode=mode):
                    with tempfile.TemporaryDirectory() as tmp:
                        out = Path(tmp) / "helio.png"
                        code, data, stdout, stderr = run(
                            HELIO_SCRIPT,
                            ["--from", "Earth", "--to", target, "--radius-mode", mode, "--out", str(out)],
                        )
                        png = out.read_bytes() if out.is_file() else b""
                    self.assertEqual(code, 0, stderr)
                    r1 = radius_of(table["earth"], mode)
                    r2 = radius_of(table[target], mode)
                    i2 = math.radians(table[target]["i_deg"])
                    self.assert_transfer(data, sun, r1, r2, 0.0, i2)
                    self.assertEqual(data["from"], "earth")
                    self.assertEqual(data["to"], target)
                    self.assertEqual(data["radius_mode"], mode)
                    self.assertIn("not the planet-centered rocket burns", stdout)
                    self.assertTrue(png.startswith(b"\x89PNG"))
                    self.assertGreater(len(png), 2000)
                    if mode == "mean":
                        tofs[target] = num(data, "tof_s")
                        synodics[target] = num(data, "synodic_s")
                        if r2 > r1:
                            self.assertEqual(data["direction"], "outward")
                            self.assertGreater(num(data, "phase_rad"), 0.0)
                        else:
                            self.assertEqual(data["direction"], "inward")
        self.assertLess(tofs["mercury"], tofs["venus"])
        self.assertLess(tofs["venus"], tofs["mars"])
        self.assertLess(tofs["mars"], tofs["jupiter"])
        self.assertLess(tofs["jupiter"], tofs["saturn"])
        self.assertLess(tofs["saturn"], tofs["uranus"])
        self.assertLess(tofs["uranus"], tofs["neptune"])
        self.assertLess(tofs["neptune"], tofs["pluto"])
        self.assertLess(synodics["mercury"], synodics["venus"])
        outer = ("mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
        for left, right in zip(outer, outer[1:]):
            self.assertGreater(synodics[left], synodics[right])
        earth_year = cat("orbital_period", a=table["earth"]["a"], mu=sun)
        for target in outer:
            self.assertGreater(synodics[target], earth_year)

    def test_neptune_pluto_perihelion_flips_inward(self) -> None:
        table = load_table()
        sun = table["sun"]["mu"]
        for mode, direction in (("mean", "outward"), ("perihelion", "inward"), ("aphelion", "outward")):
            with self.subTest(mode=mode):
                code, data, _, stderr = run(
                    HELIO_SCRIPT,
                    ["--from", "neptune", "--to", "pluto", "--radius-mode", mode, "--out", os.devnull],
                )
                self.assertEqual(code, 0, stderr)
                r1 = radius_of(table["neptune"], mode)
                r2 = radius_of(table["pluto"], mode)
                i1 = math.radians(table["neptune"]["i_deg"])
                i2 = math.radians(table["pluto"]["i_deg"])
                self.assert_transfer(data, sun, r1, r2, i1, i2)
                self.assertEqual(data["direction"], direction)

    def test_other_planet_pairs(self) -> None:
        table = load_table()
        sun = table["sun"]["mu"]
        for depart, arrive in (("venus", "mercury"), ("jupiter", "saturn"), ("mercury", "neptune")):
            with self.subTest(depart=depart, arrive=arrive):
                code, data, _, stderr = run(
                    HELIO_SCRIPT,
                    ["--from", depart, "--to", arrive, "--out", os.devnull],
                )
                self.assertEqual(code, 0, stderr)
                self.assert_transfer(
                    data,
                    sun,
                    table[depart]["a"],
                    table[arrive]["a"],
                    math.radians(table[depart]["i_deg"]),
                    math.radians(table[arrive]["i_deg"]),
                )

    def test_radius_grid_against_the_catalogue(self) -> None:
        import heliocentric_hohmann as helio

        radii = (0.2, 1.0, 1.0 + 1e-6, 3.0, 10.0, 40.0)
        angles = (0.0, 1e-4, math.radians(1.848), math.radians(7.004), math.pi / 2, math.pi)
        for r1 in radii:
            for r2 in radii:
                for di in angles:
                    with self.subTest(r1=r1, r2=r2, di=di):
                        got = helio.solve_hohmann(1.0, r1, r2, 0.0, di, "radii", "mean", "r1", "r2")
                        expect = expected_transfer(1.0, r1, r2, 0.0, di)
                        self.assertEqual(got.direction, expect["direction"])
                        self.assertEqual(got.sense_depart, expect["sense_depart"])
                        self.assertTrue(close(got.a, expect["a"]))
                        self.assertTrue(close(got.e, expect["e"], tol=1e-12))
                        self.assertTrue(close(got.tof, expect["tof"]))
                        self.assertTrue(close(got.phase, expect["phase"], tol=1e-9))
                        speed = max(expect["vt1"], expect["vp1"], expect["vt2"], expect["vp2"], 1.0)
                        noise = 1e-8 * speed
                        self.assertTrue(close(got.vinf_depart_coplanar, abs(expect["vt1"] - expect["vp1"]), tol=noise))
                        self.assertTrue(close(got.vinf_depart_inclined, expect["vinf_depart_inclined"], tol=noise))
                        self.assertTrue(close(got.vinf_arrive_inclined, expect["vinf_arrive_inclined"], tol=noise))
                        if math.isinf(expect["synodic"]):
                            self.assertTrue(math.isinf(got.synodic))
                        else:
                            self.assertTrue(close(got.synodic, expect["synodic"]))
                        if di == 0.0:
                            self.assertTrue(close(got.vinf_depart_inclined, got.vinf_depart_coplanar, tol=noise))
                        else:
                            self.assertGreater(got.vinf_depart_inclined + noise, got.vinf_depart_coplanar)

    def test_mars_bands_and_png_title_file(self) -> None:
        code, data, _, stderr = run(
            HELIO_SCRIPT,
            ["--from", "earth", "--to", "mars", "--out", os.devnull],
        )
        self.assertEqual(code, 0, stderr)
        self.assertGreater(num(data, "tof_s"), 2.0e7)
        self.assertLess(num(data, "tof_s"), 2.5e7)
        self.assertGreater(num(data, "vinf_depart_coplanar_m_s"), 2500)
        self.assertLess(num(data, "vinf_depart_coplanar_m_s"), 3500)
        self.assertGreater(num(data, "synodic_s"), 6.4e7)
        self.assertLess(num(data, "synodic_s"), 7.1e7)
        self.assertGreater(num(data, "phase_rad"), math.radians(40))
        self.assertLess(num(data, "phase_rad"), math.radians(50))

    def test_rejects_bad_inputs(self) -> None:
        cases = (
            (["--from", "sun", "--to", "mars"], "central body"),
            (["--from", "earth", "--to", "earth"], "different"),
            (["--from", "earth", "--r1", "1", "--r2", "2", "--mu", "1"], "not both"),
            (["--from", "earth"], "both"),
            (["--from", "earth", "--to", "mars", "--i1", "0.1"], "body table"),
            (["--r1", "-1", "--r2", "2", "--mu", "1"], "> 0"),
            (["--r1", "1", "--r2", "2", "--mu", "0"], "> 0"),
            (["--to", "moon", "--from", "earth"], "unknown body"),
        )
        for args, needle in cases:
            with self.subTest(args=args):
                code, _, _, stderr = run(HELIO_SCRIPT, [*args, "--out", os.devnull])
                self.assertEqual(code, 1, stderr)
                self.assertIn(needle, stderr)
        bad = run(HELIO_SCRIPT, ["--from", "earth", "--to", "mars", "--radius-mode", "Mean"])
        self.assertEqual(bad[0], 2)

    def test_builtin_check_leaves_the_sample_png(self) -> None:
        sample = SAMPLE_PNGS[0]
        before = sample.stat().st_mtime_ns
        code, _, stdout, stderr = run(HELIO_SCRIPT, ["--check"])
        self.assertEqual(code, 0, stderr)
        self.assertNotIn("CHECK FAIL", stdout + stderr)
        self.assertEqual(sample.stat().st_mtime_ns, before)


class LeoToLowOrbitTests(unittest.TestCase):
    def assert_mission(self, data: dict[str, str], stdout: str, table: dict, target: str, h_leo: float, h_arrive: float, mode: str) -> None:
        expect = expected_mission(table, target, h_leo, h_arrive, mode)
        transfer = expect["transfer"]
        self.assertEqual(data["to"], target)
        self.assertEqual(data["class"], expect["class"])
        self.assertEqual(data["radius_mode"], mode)
        self.assertEqual(data["plane_change_at"], expect["plane_change_at"])
        self.assertEqual(
            [data[f"path_{index}"] for index in range(1, 7)],
            [
                "circular LEO",
                "Earth departure hyperbola",
                "Earth sphere of influence",
                "heliocentric half-ellipse",
                "target sphere of influence and arrival hyperbola",
                "circular low orbit",
            ],
        )
        self.assertTrue(close(num(data, "r_leo_m"), expect["r_leo"], tol=1e-3))
        self.assertTrue(close(num(data, "r_low_m"), expect["r_low"], tol=1e-3))
        self.assertTrue(close(num(data, "h_leo_m"), h_leo, tol=1e-3))
        self.assertTrue(close(num(data, "h_arrive_m"), h_arrive, tol=1e-3))
        self.assertTrue(close(num(data, "a_m"), transfer["a"]))
        self.assertTrue(close(num(data, "e"), transfer["e"], tol=1e-9))
        self.assertEqual(data["direction"], transfer["direction"])
        self.assertTrue(close(num(data, "tof_s"), transfer["tof"]))
        self.assertTrue(close(num(data, "period_s"), transfer["period"]))
        self.assertTrue(close(num(data, "phase_rad"), transfer["phase"], tol=1e-6))
        self.assertTrue(close(num(data, "di_rad"), transfer["di"], tol=1e-9))
        if math.isinf(transfer["synodic"]):
            self.assertEqual(data["synodic_s"], "inf")
        else:
            self.assertTrue(close(num(data, "synodic_s"), transfer["synodic"]))
        self.assertTrue(close(num(data, "vinf_depart_m_s"), expect["vinf_depart"]))
        self.assertTrue(close(num(data, "vinf_arrive_m_s"), expect["vinf_arrive"]))
        self.assertTrue(close(num(data, "C3_m2_s2"), expect["c3"]))
        self.assertTrue(close(num(data, "C3_m2_s2"), num(data, "vinf_depart_m_s") ** 2))
        self.assertTrue(close(num(data, "dv_depart_m_s"), expect["dv_depart"]))
        self.assertTrue(close(num(data, "dv_capture_m_s"), expect["dv_capture"]))
        self.assertTrue(close(num(data, "dv_total_m_s"), expect["dv_total"]))
        self.assertTrue(close(num(data, "dv_total_m_s"), num(data, "dv_depart_m_s") + num(data, "dv_capture_m_s")))
        self.assertTrue(close(num(data, "dv_total_if_plane_change_at_depart_m_s"), expect["dv_total_depart"]))
        self.assertTrue(close(num(data, "dv_total_if_plane_change_at_arrive_m_s"), expect["dv_total_arrive"]))
        smaller = min(num(data, "dv_total_if_plane_change_at_depart_m_s"), num(data, "dv_total_if_plane_change_at_arrive_m_s"))
        self.assertTrue(close(num(data, "dv_total_m_s"), smaller, tol=1e-4))
        self.assertTrue(close(num(data, "v_periapsis_depart_m_s"), expect["v_peri_depart"]))
        self.assertTrue(close(num(data, "v_circular_leo_m_s"), expect["v_circ_depart"]))
        self.assertTrue(close(num(data, "v_periapsis_arrive_m_s"), expect["v_peri_arrive"]))
        self.assertTrue(close(num(data, "v_circular_low_m_s"), expect["v_circ_arrive"]))
        self.assertGreater(num(data, "dv_depart_m_s"), 0.0)
        self.assertGreater(num(data, "dv_capture_m_s"), 0.0)
        handwritten_soi = radius_of(table["earth"], mode) * (table["earth"]["mu"] / table["sun"]["mu"]) ** (2.0 / 5.0)
        self.assertTrue(close(expect["soi_earth"], handwritten_soi))
        self.assertTrue(close(num(data, "soi_earth_m"), expect["soi_earth"]))
        self.assertTrue(close(num(data, "soi_target_m"), expect["soi_target"]))
        self.assertLess(num(data, "soi_earth_m"), num(data, "r_helio_depart_m"))
        self.assertLess(num(data, "soi_target_m"), num(data, "r_helio_arrive_m"))
        self.assertGreater(num(data, "soi_earth_m"), table["earth"]["radius"])
        self.assertIn("no separate plane_change_impulse", stdout)
        self.assertNotIn("dv_plane", data)
        self.assertIn("patched conic, not an integrated three-body arc", stdout)
        self.assertIn("alignable with the departure asymptote", stdout)
        self.assertGreaterEqual(stdout.index("path_1"), 0)
        self.assertLess(stdout.index("path_1"), stdout.index("path_6"))

    def test_every_target_mean_orbit(self) -> None:
        table = load_table()
        for target in TARGETS:
            with self.subTest(target=target):
                with tempfile.TemporaryDirectory() as tmp:
                    out = Path(tmp) / "mission.png"
                    code, data, stdout, stderr = run(
                        LEO_SCRIPT,
                        ["--to", target, "--h-leo", "400000", "--h-arrive", "400000", "--out", str(out)],
                    )
                    png = out.read_bytes() if out.is_file() else b""
                self.assertEqual(code, 0, stderr)
                self.assert_mission(data, stdout, table, target, 400000.0, 400000.0, "mean")
                self.assertTrue(png.startswith(b"\x89PNG"))
                self.assertGreater(len(png), 2000)
        code, mars, _, stderr = run(
            LEO_SCRIPT,
            ["--to", "mars", "--h-leo", "400000", "--h-arrive", "400000", "--out", os.devnull],
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(mars["plane_change_at"], "depart")
        self.assertGreater(num(mars, "dv_depart_m_s"), 3000)
        self.assertLess(num(mars, "dv_depart_m_s"), 4500)
        self.assertGreater(num(mars, "dv_total_m_s"), 5000)
        self.assertLess(num(mars, "dv_total_m_s"), 7000)
        self.assertGreater(num(mars, "soi_earth_m"), 8.5e8)
        self.assertLess(num(mars, "soi_earth_m"), 1.0e9)
        code, pluto, _, stderr = run(
            LEO_SCRIPT,
            ["--to", "pluto", "--h-leo", "200000", "--h-arrive", "100000", "--out", os.devnull],
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(pluto["class"], "dwarf")
        self.assertEqual(pluto["plane_change_at"], "arrive")
        self.assertLess(
            num(pluto, "dv_total_if_plane_change_at_arrive_m_s"),
            num(pluto, "dv_total_if_plane_change_at_depart_m_s"),
        )

    def test_radius_modes_and_surface_orbits(self) -> None:
        table = load_table()
        for target, mode in (
            ("mars", "perihelion"),
            ("mars", "aphelion"),
            ("pluto", "perihelion"),
            ("pluto", "aphelion"),
            ("mercury", "mean"),
            ("jupiter", "mean"),
        ):
            altitude = "0" if target in {"mercury", "jupiter"} else "250000"
            with self.subTest(target=target, mode=mode):
                code, data, stdout, stderr = run(
                    LEO_SCRIPT,
                    ["--to", target, "--h-leo", altitude, "--h-arrive", altitude, "--radius-mode", mode, "--out", os.devnull],
                )
                self.assertEqual(code, 0, stderr)
                self.assert_mission(data, stdout, table, target, float(altitude), float(altitude), mode)
                self.assertTrue(close(num(data, "r_helio_depart_m"), radius_of(table["earth"], mode)))
                self.assertTrue(close(num(data, "r_helio_arrive_m"), radius_of(table[target], mode)))

    def test_higher_parking_orbit_lowers_the_burn(self) -> None:
        leo_totals = []
        for height in (0, 200000, 400000, 800000, 2000000):
            code, data, _, stderr = run(
                LEO_SCRIPT,
                ["--to", "mars", "--h-leo", str(height), "--h-arrive", "300000", "--out", os.devnull],
            )
            self.assertEqual(code, 0, stderr)
            leo_totals.append(
                (
                    num(data, "dv_total_m_s"),
                    num(data, "dv_total_if_plane_change_at_depart_m_s"),
                    num(data, "dv_total_if_plane_change_at_arrive_m_s"),
                )
            )
        for earlier, later in zip(leo_totals, leo_totals[1:]):
            self.assertGreater(earlier[0], later[0])
            self.assertGreater(earlier[1], later[1])
            self.assertGreater(earlier[2], later[2])
        arrive_totals = []
        for height in (0, 100000, 300000, 1000000, 5000000):
            code, data, _, stderr = run(
                LEO_SCRIPT,
                ["--to", "mars", "--h-leo", "400000", "--h-arrive", str(height), "--out", os.devnull],
            )
            self.assertEqual(code, 0, stderr)
            arrive_totals.append(num(data, "dv_capture_m_s"))
        for earlier, later in zip(arrive_totals, arrive_totals[1:]):
            self.assertGreater(earlier, later)

    def test_mission_grid_against_the_catalogue(self) -> None:
        import leo_to_low_orbit as leo

        table = load_table()
        altitudes = ((0.0, 0.0), (400000.0, 400000.0), (200000.0, 100000.0), (1.0e6, 5.0e4))
        for target in TARGETS:
            for mode in ("mean", "perihelion", "aphelion"):
                for h_leo, h_arrive in altitudes:
                    with self.subTest(target=target, mode=mode, h_leo=h_leo, h_arrive=h_arrive):
                        got = leo.solve_mission(target, h_leo, h_arrive, mode)
                        expect = expected_mission(table, target, h_leo, h_arrive, mode)
                        self.assertEqual(got.plane_change_at, expect["plane_change_at"])
                        self.assertTrue(close(got.dv_total, expect["dv_total"], tol=1e-4))
                        self.assertTrue(close(got.dv_total_if_depart, expect["dv_total_depart"], tol=1e-4))
                        self.assertTrue(close(got.dv_total_if_arrive, expect["dv_total_arrive"], tol=1e-4))
                        self.assertTrue(close(got.c3, expect["c3"]))
                        self.assertTrue(close(got.soi_earth, expect["soi_earth"]))
                        self.assertTrue(close(got.soi_target, expect["soi_target"]))
                        self.assertTrue(close(got.vinf_depart, expect["vinf_depart"]))
                        depart_energy = got.depart.v_periapsis**2 / 2.0 - got.mu_earth / got.r_leo
                        arrive_energy = got.capture.v_periapsis**2 / 2.0 - got.mu_target / got.r_low
                        self.assertTrue(close(depart_energy, 0.5 * got.vinf_depart**2, rel=1e-9))
                        self.assertTrue(close(arrive_energy, 0.5 * got.vinf_arrive**2, rel=1e-9))
                        self.assertTrue(close(got.transfer.tof, 0.5 * got.transfer.period))
                        turned = math.remainder(
                            got.transfer.phase + got.transfer.n_arrive * got.transfer.tof - math.pi,
                            2.0 * math.pi,
                        )
                        self.assertTrue(close(turned, 0.0, tol=1e-8))

    def test_zero_inclination_burn_matches_the_coplanar_excess(self) -> None:
        import heliocentric_hohmann as helio
        import leo_to_low_orbit as leo

        table = load_table()
        transfer = helio.from_names("earth", "mars", "mean")
        flat = helio.solve_hohmann(
            transfer.mu,
            transfer.r_depart,
            transfer.r_arrive,
            0.0,
            0.0,
            "radii",
            "mean",
            "earth",
            "mars",
        )
        self.assertTrue(close(flat.vinf_depart_inclined, flat.vinf_depart_coplanar, tol=1e-9))
        r_leo = table["earth"]["radius"] + 400000.0
        r_low = table["mars"]["radius"] + 400000.0
        burn = leo.park_burn(table["earth"]["mu"], r_leo, flat.vinf_depart_coplanar)
        expect, _, _ = hyperbola_burn(table["earth"]["mu"], r_leo, flat.vinf_depart_coplanar)
        self.assertTrue(close(burn.dv, expect, tol=1e-6))
        capture = leo.park_burn(table["mars"]["mu"], r_low, flat.vinf_arrive_coplanar)
        expect_capture, _, _ = hyperbola_burn(table["mars"]["mu"], r_low, flat.vinf_arrive_coplanar)
        self.assertTrue(close(capture.dv, expect_capture, tol=1e-6))

    def test_rejects_missing_and_illegal_inputs(self) -> None:
        cases = (
            (["--h-leo", "400000", "--h-arrive", "400000"], "--to"),
            (["--to", "mars", "--h-arrive", "400000"], "--h-leo"),
            (["--to", "mars", "--h-leo", "400000"], "--h-arrive"),
            (["--to", "earth", "--h-leo", "400000", "--h-arrive", "400000"], "another planet"),
            (["--to", "sun", "--h-leo", "400000", "--h-arrive", "400000"], "another planet"),
            (["--to", "moon", "--h-leo", "400000", "--h-arrive", "400000"], "unknown body"),
            (["--to", "mars", "--h-leo", "-1", "--h-arrive", "400000"], "h-leo"),
            (["--to", "mars", "--h-leo", "400000", "--h-arrive", "-10"], "h-arrive"),
            (["--to", "mars", "--h-leo", "nan", "--h-arrive", "400000"], "h-leo"),
            (["--to", "mars", "--h-leo", "inf", "--h-arrive", "400000"], "h-leo"),
        )
        for args, needle in cases:
            with self.subTest(args=args):
                with tempfile.TemporaryDirectory() as tmp:
                    out = str(Path(tmp) / "should-not-exist.png")
                    code, _, _, stderr = run(LEO_SCRIPT, [*args, "--out", out])
                    self.assertEqual(code, 1, stderr)
                    self.assertIn(needle, stderr)
                    self.assertFalse(Path(out).exists())

    def test_builtin_check_leaves_the_sample_png(self) -> None:
        sample = SAMPLE_PNGS[1]
        before = sample.stat().st_mtime_ns
        code, _, stdout, stderr = run(LEO_SCRIPT, ["--check"])
        self.assertEqual(code, 0, stderr)
        self.assertNotIn("CHECK FAIL", stdout + stderr)
        self.assertEqual(sample.stat().st_mtime_ns, before)


class CatalogWiringTests(unittest.TestCase):
    def test_tools_register_and_the_runner_collects_the_png(self) -> None:
        tools = load_catalog(ROOT)
        body = tool_by_name(tools, "solar_system_body")
        helio = tool_by_name(tools, "heliocentric_hohmann")
        mission = tool_by_name(tools, "leo_to_low_orbit")
        self.assertIsNotNone(body)
        self.assertIsNotNone(helio)
        self.assertIsNotNone(mission)
        assert body is not None and helio is not None and mission is not None
        self.assertEqual(body.required_options(), [])
        self.assertEqual(helio.required_options(), [])
        self.assertEqual(mission.required_options(), ["--to", "--h-leo", "--h-arrive"])
        for tool in (body, helio, mission):
            options = {flag.option for flag in tool.flags}
            self.assertNotIn("--check", options)
            self.assertNotIn("--out", options)
        result = run_tool(
            mission,
            {"to": "mars", "h_leo": 400000, "h_arrive": 300000},
            repo_root=ROOT,
        )
        try:
            self.assertEqual(result.exit_code, 0, result.text)
            self.assertIn("graph:", result.text)
            self.assertIn("dv_total_m_s:", result.text)
            self.assertTrue(result.files)
            self.assertTrue(result.files[0].read_bytes().startswith(b"\x89PNG"))
        finally:
            if result.job_dir is not None:
                shutil.rmtree(result.job_dir, ignore_errors=True)
        missing = run_tool(mission, {"to": "mars"}, repo_root=ROOT)
        try:
            self.assertNotEqual(missing.exit_code, 0)
            self.assertIn("h-leo", missing.text)
        finally:
            if missing.job_dir is not None:
                shutil.rmtree(missing.job_dir, ignore_errors=True)

    def test_heliocentric_named_bodies_accept_from_and_to(self) -> None:
        tools = load_catalog(ROOT)
        helio = tool_by_name(tools, "heliocentric_hohmann")
        assert helio is not None
        dests = {flag.option: flag.dest for flag in helio.flags}
        self.assertEqual(dests["--from"], "depart")
        self.assertEqual(dests["--to"], "arrive")
        server = build_server()
        props = server._tool_manager._tools["heliocentric_hohmann"].parameters["properties"]
        self.assertIn("from", props)
        self.assertIn("to", props)
        self.assertNotIn("depart", props)
        named = run_tool(helio, {"from": "earth", "to": "mars"}, repo_root=ROOT)
        try:
            self.assertEqual(named.exit_code, 0, named.text)
            self.assertIn("from: earth", named.text)
            self.assertIn("to: mars", named.text)
        finally:
            if named.job_dir is not None:
                shutil.rmtree(named.job_dir, ignore_errors=True)
        aliased = run_tool(helio, {"depart": "earth", "arrive": "venus"}, repo_root=ROOT)
        try:
            self.assertEqual(aliased.exit_code, 0, aliased.text)
            self.assertIn("from: earth", aliased.text)
            self.assertIn("to: venus", aliased.text)
        finally:
            if aliased.job_dir is not None:
                shutil.rmtree(aliased.job_dir, ignore_errors=True)

    def test_skills_point_at_the_neighbouring_programs(self) -> None:
        helio = (ROOT / "skills" / "ASTRO - HeliocentricHohmann" / "SKILL.md").read_text(encoding="utf-8")
        mission = (ROOT / "skills" / "ASTRO - LeoToLowOrbit" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ASTRO - HohmannTransfer", helio)
        self.assertIn("ASTRO - LeoToLowOrbit", helio)
        self.assertIn("Do not invent", mission)
        self.assertIn("ASTRO - HohmannTransfer", mission)
        self.assertIn("ASTRO - HyperbolicExcess", mission)
        self.assertIn("ROCKET - PayloadtoDeltaV", mission)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in ("ASTRO - SolarSystemBody", "ASTRO - HeliocentricHohmann", "ASTRO - LeoToLowOrbit"):
            self.assertIn(name, readme)


if __name__ == "__main__":
    unittest.main()
