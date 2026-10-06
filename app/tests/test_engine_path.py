"""Multi-case checks for the liquid-engine path programs.

Oracles are the SP-125 English equations (orifice, pump horsepower, Bartz),
not the SI constants baked into the programs.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["AUTH_DISABLED"] = "1"

from app.catalog import load_catalog, tool_by_name
from app.runner import run_tool

ROOT = Path(__file__).resolve().parents[2]
INCH = 0.0254
LB = 0.45359237
FOOT = 0.3048
PSI = 6894.757293168361
BTU = 1055.05585262
FT_LBF_PER_S = FOOT * 4.4482216152605
G0 = 9.80665

SCRIPTS = {
    "injector": ROOT / "skills" / "ROCKET - InjectorOrificeFlow" / "injector_orifice_flow.py",
    "feed": ROOT / "skills" / "ROCKET - FeedSystemPressureBudget" / "feed_system_pressure_budget.py",
    "pump": ROOT / "skills" / "ROCKET - PumpHydraulicPower" / "pump_hydraulic_power.py",
    "heat": ROOT / "skills" / "ROCKET - ThroatGasSideHeatFlux" / "throat_gas_side_heat_flux.py",
    "coolant": ROOT
    / "skills"
    / "ROCKET - RegenerativeCoolantHeatPickUp"
    / "regenerative_coolant_heat_pickup.py",
}


def run(script: Path, args: list[str]) -> tuple[int, dict[str, str], str]:
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    data: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        data[key] = value
    return proc.returncode, data, proc.stderr


def num(data: dict[str, str], key: str) -> float:
    return float(data[key])


def close(actual: float, expected: float, rel: float = 1e-6, tol: float = 0.0) -> bool:
    """Stdout uses eight significant digits. Comparisons stay at that precision."""
    return abs(actual - expected) <= tol + rel * abs(expected)


def bartz_english(
    diameter_in: float,
    mu_lb_in_s: float,
    cp_btu: float,
    prandtl: float,
    pc_psi: float,
    cstar_fps: float,
    curvature_in: float,
    area_ratio: float = 1.0,
    sigma: float = 1.0,
) -> float:
    """SP-125 equation (4-13) in that note's English units. Btu/(in^2·s·°F)."""
    return (
        (0.026 / diameter_in**0.2)
        * (mu_lb_in_s**0.2 * cp_btu / prandtl**0.6)
        * ((pc_psi * 32.2 / cstar_fps) ** 0.8)
        * ((diameter_in / curvature_in) ** 0.1)
        * area_ratio**0.9
        * sigma
    )


class BuiltInCheckTests(unittest.TestCase):
    def test_each_program_check_passes(self) -> None:
        for name, script in SCRIPTS.items():
            with self.subTest(program=name):
                code, data, err = run(script, ["--check"])
                self.assertEqual(code, 0, err)
                self.assertEqual(data["check"], "pass")
                self.assertNotIn("CHECK FAIL", err)


class InjectorTests(unittest.TestCase):
    def test_sp125_a1_oxidizer_orifice(self) -> None:
        """Sample calculation 4-8, inverted from equation (4-40), not the rounded 32.4 in^2."""
        g_in = 32.2 * 12.0
        rho_lb_in3 = 71.38 / 1728.0
        weight = 1941.0
        cd = 0.75
        dp_psi = 200.0
        area_in2 = weight / (cd * math.sqrt(2.0 * g_in * rho_lb_in3 * dp_psi))
        self.assertLess(abs(area_in2 - 32.4), 0.05)
        speed_in_s = weight / (area_in2 * rho_lb_in3)
        code, data, err = run(
            SCRIPTS["injector"],
            [
                "--mdot",
                str(weight * LB),
                "--rho",
                str(71.38 * LB / FOOT**3),
                "--cd",
                str(cd),
                "--dp",
                str(dp_psi * PSI),
                "--count",
                "1400",
            ],
        )
        self.assertEqual(code, 0, err)
        rho_si = 71.38 * LB / FOOT**3
        mdot = weight * LB
        dp_pa = dp_psi * PSI
        area_si = mdot / (cd * math.sqrt(2.0 * rho_si * dp_pa))
        area = num(data, "A_m2")
        speed = num(data, "v_m_s")
        # SP-125 uses g = 32.2 ft/s^2. Coherent SI differs from that value by about 0.04%.
        self.assertTrue(close(area, area_si))
        self.assertLess(abs(area - area_in2 * INCH**2) / area, 5e-4)
        self.assertTrue(close(speed, mdot / (rho_si * area)))
        self.assertLess(abs(speed - speed_in_s * INCH) / speed, 5e-4)
        self.assertTrue(close(num(data, "q_jet_Pa"), 0.5 * rho_si * speed**2))
        self.assertTrue(close(1400.0 * math.pi * (num(data, "d_m") / 2.0) ** 2, area))
        self.assertLess(abs(area_in2 - 32.4), 0.05)

    def test_dp_and_velocity_round_trip(self) -> None:
        cases = [
            (0.2, 800.0, 0.62, 1.5e5),
            (2.0, 1141.0, 0.75, 2.0e5),
            (40.0, 70.0, 0.9, 6.0e4),
            (0.05, 1500.0, 1.0, 1.0e6),
        ]
        for mdot, rho, cd, dp in cases:
            with self.subTest(mdot=mdot, rho=rho, cd=cd, dp=dp):
                code, from_dp, err = run(
                    SCRIPTS["injector"],
                    ["--mdot", str(mdot), "--rho", str(rho), "--cd", str(cd), "--dp", str(dp), "--count", "7"],
                )
                self.assertEqual(code, 0, err)
                area = num(from_dp, "A_m2")
                speed = num(from_dp, "v_m_s")
                self.assertTrue(close(area, mdot / (cd * math.sqrt(2.0 * rho * dp))))
                self.assertTrue(close(speed, mdot / (rho * area)))
                self.assertTrue(close(num(from_dp, "q_jet_Pa"), 0.5 * rho * speed**2))
                self.assertTrue(
                    close(7.0 * math.pi * (num(from_dp, "d_m") / 2.0) ** 2, area)
                )
                code, from_v, err = run(
                    SCRIPTS["injector"],
                    [
                        "--mdot",
                        str(mdot),
                        "--rho",
                        str(rho),
                        "--cd",
                        str(cd),
                        "--velocity",
                        str(speed),
                    ],
                )
                self.assertEqual(code, 0, err)
                self.assertTrue(close(num(from_v, "dp_Pa"), dp, rel=1e-6, tol=1e-2))
                self.assertTrue(close(num(from_v, "A_m2"), area))
                self.assertNotIn("d_m", from_v)

    def test_discharge_coefficient_warning_bounds(self) -> None:
        for cd, warned in ((0.5, False), (0.92, False), (0.49, True), (0.93, True)):
            with self.subTest(cd=cd):
                code, data, err = run(
                    SCRIPTS["injector"],
                    ["--mdot", "1", "--rho", "1000", "--cd", str(cd), "--dp", "1e5"],
                )
                self.assertEqual(code, 0, err)
                self.assertEqual("warning" in data, warned)

    def test_rejects_bad_inputs(self) -> None:
        cases = [
            (["--mdot", "1"], "missing"),
            (["--mdot", "1", "--rho", "1000", "--cd", "0.7"], "exactly one"),
            (["--mdot", "1", "--rho", "1000", "--cd", "0.7", "--dp", "1e5", "--velocity", "10"], "exactly one"),
            (["--mdot", "-1", "--rho", "1000", "--cd", "0.7", "--dp", "1e5"], "must be > 0"),
            (["--mdot", "1", "--rho", "1000", "--cd", "1.1", "--dp", "1e5"], "Cd"),
            (["--mdot", "1", "--rho", "1000", "--cd", "0.7", "--dp", "0"], "dp"),
            (["--mdot", "1", "--rho", "1000", "--cd", "0.7", "--velocity", "-2"], "velocity"),
            (["--mdot", "1", "--rho", "1000", "--cd", "0.7", "--dp", "1e5", "--count", "0"], "count"),
            (["--mdot", "nan", "--rho", "1000", "--cd", "0.7", "--dp", "1e5"], "finite"),
            (["--mdot", "1", "--rho", "inf", "--cd", "0.7", "--dp", "1e5"], "finite"),
        ]
        for args, needle in cases:
            with self.subTest(args=args):
                code, _data, err = run(SCRIPTS["injector"], args)
                self.assertEqual(code, 2, err)
                self.assertIn(needle, err)

    def test_png_header(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "orifice.png"
            code, data, err = run(
                SCRIPTS["injector"],
                ["--mdot", "2", "--rho", "1000", "--cd", "0.75", "--dp", "2e5", "--count", "4", "--out", str(path)],
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(data["graph"], str(path))
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))


class FeedTests(unittest.TestCase):
    def test_single_branch_with_head_and_named_drops(self) -> None:
        code, data, err = run(
            SCRIPTS["feed"],
            [
                "--pc",
                "2e6",
                "--dp-injector",
                "2e5",
                "--dp",
                "jacket=100000",
                "--dp",
                "line=2.5e4",
                "--rho",
                "1141",
                "--height",
                "3.5",
                "--g",
                "1.62",
            ],
        )
        self.assertEqual(code, 0, err)
        head = 1141.0 * 1.62 * 3.5
        self.assertTrue(close(num(data, "p_manifold_Pa"), 2.2e6))
        self.assertTrue(close(num(data, "dp_extra_Pa"), 1.25e5))
        self.assertTrue(close(num(data, "dp_jacket_Pa"), 1.0e5))
        self.assertTrue(close(num(data, "dp_head_Pa"), head))
        self.assertTrue(close(num(data, "p_supply_Pa"), 2.2e6 + 1.25e5 + head))
        self.assertTrue(close(num(data, "meop_Pa"), num(data, "p_supply_Pa")))

    def test_negative_height_lowers_supply(self) -> None:
        code, data, err = run(
            SCRIPTS["feed"],
            ["--pc", "2e6", "--dp-injector", "0", "--rho", "1000", "--height", "-4"],
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(close(num(data, "dp_head_Pa"), -1000.0 * G0 * 4.0))
        self.assertLess(num(data, "p_supply_Pa"), 2.0e6)

    def test_two_branches_meop_is_the_higher_supply(self) -> None:
        for ox_drop, fuel_drop, expect in ((3.0e5, 5.0e4, "ox"), (4.0e4, 2.5e5, "fuel")):
            with self.subTest(higher=expect):
                code, data, err = run(
                    SCRIPTS["feed"],
                    [
                        "--pc",
                        "5e6",
                        "--dp-injector-ox",
                        str(ox_drop),
                        "--dp-injector-fuel",
                        str(fuel_drop),
                        "--dp",
                        "jacket=8e4",
                        "--rho-ox",
                        "1140",
                        "--rho-fuel",
                        "810",
                        "--height",
                        "2",
                    ],
                )
                self.assertEqual(code, 0, err)
                ox = 5.0e6 + ox_drop + 8.0e4 + 1140.0 * G0 * 2.0
                fuel = 5.0e6 + fuel_drop + 8.0e4 + 810.0 * G0 * 2.0
                self.assertTrue(close(num(data, "p_supply_ox_Pa"), ox))
                self.assertTrue(close(num(data, "p_supply_fuel_Pa"), fuel))
                self.assertTrue(close(num(data, "meop_Pa"), max(ox, fuel)))

    def test_zero_injector_drop_and_no_head(self) -> None:
        code, data, err = run(SCRIPTS["feed"], ["--pc", "1.5e6", "--dp-injector", "0"])
        self.assertEqual(code, 0, err)
        self.assertTrue(close(num(data, "p_supply_Pa"), 1.5e6))
        self.assertTrue(close(num(data, "dp_head_Pa"), 0.0))
        self.assertNotIn("rho_kg_m3", data)

    def test_rejects_bad_inputs(self) -> None:
        cases = [
            ([], "requires --pc"),
            (["--pc", "0", "--dp-injector", "1"], "pc must"),
            (["--pc", "1e6"], "dp-injector"),
            (["--pc", "1e6", "--dp-injector", "1", "--dp-injector-ox", "1", "--dp-injector-fuel", "1"], "not both"),
            (["--pc", "1e6", "--dp-injector-ox", "1"], "both required"),
            (["--pc", "1e6", "--dp-injector", "1", "--height", "2"], "requires --rho"),
            (["--pc", "1e6", "--dp-injector", "1", "--rho", "1000"], "requires --height"),
            (["--pc", "1e6", "--dp-injector", "1", "--dp", "jacket=1", "--dp", "jacket=2"], "repeated"),
            (["--pc", "1e6", "--dp-injector", "1", "--dp", "jacket=-1"], ">= 0"),
            (["--pc", "nan", "--dp-injector", "1"], "finite"),
            (["--pc", "1e6", "--dp-injector", "1", "--g", "0"], "g must"),
            (["--pc", "1e6", "--dp-injector-ox", "1", "--dp-injector-fuel", "1", "--rho", "1000", "--height", "1"], "rho-ox"),
        ]
        for args, needle in cases:
            with self.subTest(args=args):
                code, _data, err = run(SCRIPTS["feed"], args)
                self.assertEqual(code, 2, err)
                self.assertIn(needle, err)

    def test_malformed_drop_is_exit_2(self) -> None:
        for bad in ("jacket", "1e5", "=1", "line-loss=1"):
            with self.subTest(bad=bad):
                code, _data, err = run(
                    SCRIPTS["feed"],
                    ["--pc", "1e6", "--dp-injector", "1", "--dp", bad],
                )
                self.assertEqual(code, 2, err)


class PumpTests(unittest.TestCase):
    def test_sp125_oxidizer_pump_horsepower(self) -> None:
        """Sample calculation 6-4: fhp = 1971 lb/s * 2930 ft / 550."""
        weight = 1971.0
        head_ft = 2930.0
        eta = 10500.0 / 14850.0
        horsepower = weight * head_ft / 550.0
        self.assertTrue(close(horsepower, 10500.0, rel=0.0, tol=0.1))
        mdot = weight * LB
        head_m = head_ft * FOOT
        rho = 1000.0
        dp = rho * G0 * head_m
        code, data, err = run(
            SCRIPTS["pump"],
            [
                "--mdot",
                str(mdot),
                "--rho",
                str(rho),
                "--dp",
                str(dp),
                "--eta",
                str(eta),
                "--eta-drive",
                "0.8",
            ],
        )
        self.assertEqual(code, 0, err)
        expected = weight * head_ft * FT_LBF_PER_S
        self.assertTrue(close(num(data, "P_hyd_W"), expected))
        self.assertTrue(close(num(data, "P_hyd_W"), mdot * dp / rho))
        self.assertTrue(close(num(data, "Vdot_m3_s"), mdot / rho))
        self.assertTrue(close(num(data, "P_shaft_W"), expected / eta))
        self.assertTrue(close(num(data, "P_drive_W"), expected / eta / 0.8))

    def test_power_scales_and_eta_one_matches_hydraulic(self) -> None:
        base = ["--rho", "810", "--eta", "1"]
        code, low, err = run(SCRIPTS["pump"], [*base, "--mdot", "3", "--dp", "4e5"])
        self.assertEqual(code, 0, err)
        self.assertTrue(close(num(low, "P_shaft_W"), num(low, "P_hyd_W")))
        code, doubled, err = run(SCRIPTS["pump"], [*base, "--mdot", "6", "--dp", "8e5"])
        self.assertEqual(code, 0, err)
        self.assertTrue(close(num(doubled, "P_hyd_W"), 4.0 * num(low, "P_hyd_W")))
        self.assertNotIn("P_drive_W", low)

    def test_rejects_bad_inputs(self) -> None:
        cases = [
            (["--mdot", "1", "--rho", "1", "--dp", "1"], "missing"),
            (["--mdot", "1", "--rho", "1", "--dp", "1", "--eta", "0"], "eta"),
            (["--mdot", "1", "--rho", "1", "--dp", "1", "--eta", "1.01"], "eta"),
            (["--mdot", "1", "--rho", "1", "--dp", "-1", "--eta", "0.7"], "must be > 0"),
            (["--mdot", "1", "--rho", "1", "--dp", "1", "--eta", "0.7", "--eta-drive", "0"], "eta-drive"),
            (["--mdot", "nan", "--rho", "1", "--dp", "1", "--eta", "0.7"], "finite"),
        ]
        for args, needle in cases:
            with self.subTest(args=args):
                code, _data, err = run(SCRIPTS["pump"], args)
                self.assertEqual(code, 2, err)
                self.assertIn(needle, err)

    def test_png_header(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pump.png"
            code, data, err = run(
                SCRIPTS["pump"],
                ["--mdot", "2", "--rho", "1000", "--dp", "2e5", "--eta", "0.7", "--out", str(path)],
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))
            self.assertEqual(data["graph"], str(path))


class HeatTests(unittest.TestCase):
    def test_sp125_a1_throat_against_english_equation(self) -> None:
        diameter_in = 24.9
        curvature_in = 11.71
        mu = 4.18e-6
        cp = 0.485
        prandtl = 0.816
        pc_psi = 1000.0
        cstar_fps = 5660.0
        hg_eng = bartz_english(
            diameter_in, mu, cp, prandtl, pc_psi, cstar_fps, curvature_in
        )
        self.assertTrue(close(hg_eng, 0.0027, rel=0.0, tol=5e-5))
        code, data, err = run(
            SCRIPTS["heat"],
            [
                "--pc",
                str(pc_psi * PSI),
                "--Tc",
                str(6140.0 * 5.0 / 9.0),
                "--cstar",
                str(cstar_fps * FOOT),
                "--throat",
                str(diameter_in * INCH),
                "--curvature",
                str(curvature_in * INCH),
                "--tw",
                "800",
                "--mu",
                str(mu * LB / INCH),
                "--cp",
                str(cp * BTU / LB),
                "--pr",
                str(prandtl),
                "--sigma",
                "1",
                "--recovery",
                "1",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(close(num(data, "h_g_W_m2_K"), hg_eng * BTU / INCH**2))
        driving = 6140.0 * 5.0 / 9.0 - 800.0
        self.assertTrue(close(num(data, "q_dot_W_m2"), num(data, "h_g_W_m2_K") * driving))
        self.assertNotIn("warning", data)
        self.assertNotIn("warning_recovery", data)
        self.assertEqual(data["prop_source"], "user")

    def test_mw_gamma_fit_matches_explicit_properties(self) -> None:
        gamma = 1.222
        molar = 22.5
        tc = 6140.0 * 5.0 / 9.0
        prandtl = 4.0 * gamma / (9.0 * gamma - 5.0)
        cp = (gamma / (gamma - 1.0)) * 4616.123393316195 / molar
        mu = 1.1840810853327972e-07 * molar**0.5 * tc**0.6
        common = [
            "--pc",
            "2e6",
            "--Tc",
            str(tc),
            "--cstar",
            "1600",
            "--rt",
            "0.0126156625",
            "--curvature",
            "0.02",
            "--tw",
            "0",
            "--recovery",
            "0.95",
            "--sigma",
            "1.1",
            "--area-ratio",
            "1",
        ]
        code, fitted, err = run(SCRIPTS["heat"], [*common, "--mw", str(molar), "--gamma", str(gamma)])
        self.assertEqual(code, 0, err)
        code, given, err = run(
            SCRIPTS["heat"],
            [*common, "--mu", str(mu), "--cp", str(cp), "--pr", str(prandtl)],
        )
        self.assertEqual(code, 0, err)
        self.assertTrue(close(num(fitted, "h_g_W_m2_K"), num(given, "h_g_W_m2_K")))
        self.assertTrue(close(num(fitted, "Dt_m"), 0.025231325))
        self.assertTrue(close(num(fitted, "q_dot_W_m2"), num(fitted, "h_g_W_m2_K") * 0.95 * tc))
        self.assertEqual(fitted["prop_source"], "sp125_mw_gamma")

    def test_bartz_exponents(self) -> None:
        base = [
            "--Tc",
            "3000",
            "--cstar",
            "1500",
            "--throat",
            "0.05",
            "--curvature",
            "0.04",
            "--tw",
            "500",
            "--mw",
            "20",
            "--gamma",
            "1.2",
            "--recovery",
            "0.9",
            "--sigma",
            "1",
        ]
        code, nominal, err = run(SCRIPTS["heat"], ["--pc", "3e6", *base])
        self.assertEqual(code, 0, err)
        code, doubled, err = run(SCRIPTS["heat"], ["--pc", "6e6", *base])
        self.assertEqual(code, 0, err)
        self.assertTrue(close(num(doubled, "h_g_W_m2_K") / num(nominal, "h_g_W_m2_K"), 2.0**0.8))
        code, wide, err = run(SCRIPTS["heat"], ["--pc", "3e6", *base, "--area-ratio", "2", "--sigma", "1.25"])
        self.assertEqual(code, 0, err)
        ratio = num(wide, "h_g_W_m2_K") / num(nominal, "h_g_W_m2_K")
        self.assertTrue(close(ratio, (2.0**0.9) * 1.25))

    def test_default_sigma_and_recovery_warn(self) -> None:
        code, data, err = run(
            SCRIPTS["heat"],
            [
                "--pc",
                "2e6",
                "--Tc",
                "3000",
                "--cstar",
                "1600",
                "--throat",
                "0.02",
                "--curvature",
                "0.02",
                "--tw",
                "400",
                "--mw",
                "18",
                "--gamma",
                "1.25",
            ],
        )
        self.assertEqual(code, 0, err)
        self.assertIn("sigma=1", data["warning"])
        self.assertIn("0.90", data["warning_recovery"])
        self.assertTrue(close(num(data, "sigma"), 1.0))
        self.assertTrue(close(num(data, "recovery"), 1.0))

    def test_rejects_bad_inputs(self) -> None:
        ok = [
            "--pc",
            "2e6",
            "--Tc",
            "3000",
            "--cstar",
            "1600",
            "--throat",
            "0.02",
            "--curvature",
            "0.02",
            "--tw",
            "400",
            "--mw",
            "18",
            "--gamma",
            "1.25",
        ]
        no_throat: list[str] = []
        skip_value = False
        for item in ok:
            if item == "--throat":
                skip_value = True
                continue
            if skip_value:
                skip_value = False
                continue
            no_throat.append(item)
        cases = [
            (no_throat, "exactly one"),
            ([*ok, "--rt", "0.01"], "exactly one"),
            ([*ok, "--mu", "1e-5"], "together"),
            ([*ok, "--mu", "1e-5", "--cp", "1000", "--pr", "0.7"], "not both"),
            (["--pc", "2e6", "--Tc", "3000", "--cstar", "1600", "--throat", "0.02", "--curvature", "0.02", "--tw", "400", "--gamma", "1"], "mw"),
            ([*ok, "--recovery", "1.01"], "recovery"),
            (["--pc", "2e6", "--Tc", "1000", "--cstar", "1600", "--throat", "0.02", "--curvature", "0.02", "--tw", "1000", "--mw", "18", "--gamma", "1.25", "--recovery", "1"], "exceed tw"),
            (["--pc", "nan", *ok[2:]], "finite"),
            (["--pc", "1e308", "--Tc", "3000", "--cstar", "1600", "--throat", "0.02", "--curvature", "0.02", "--tw", "400", "--mu", "1e308", "--cp", "1e308", "--pr", "0.7", "--sigma", "1", "--recovery", "1"], "not finite"),
        ]
        for args, needle in cases:
            with self.subTest(needle=needle):
                code, _data, err = run(SCRIPTS["heat"], args)
                self.assertEqual(code, 2, err)
                self.assertIn(needle, err)

    def test_png_header(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "flux.png"
            code, _data, err = run(
                SCRIPTS["heat"],
                [
                    "--pc",
                    "2e6",
                    "--Tc",
                    "3000",
                    "--cstar",
                    "1600",
                    "--throat",
                    "0.02",
                    "--curvature",
                    "0.02",
                    "--tw",
                    "400",
                    "--mw",
                    "18",
                    "--gamma",
                    "1.25",
                    "--recovery",
                    "0.95",
                    "--out",
                    str(path),
                ],
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))


class CoolantTests(unittest.TestCase):
    def test_flux_times_area_matches_heat_rate(self) -> None:
        cases = [
            (0.2, 14000.0, 20.0, 2.5e6, 0.004),
            (3.5, 2000.0, 300.0, 8.0e6, 0.01),
            (12.0, 4180.0, 280.0, 1.0e7, 0.002),
        ]
        for mdot, cp, tin, flux, area in cases:
            with self.subTest(mdot=mdot):
                heat = flux * area
                code, from_flux, err = run(
                    SCRIPTS["coolant"],
                    [
                        "--mdot",
                        str(mdot),
                        "--cp",
                        str(cp),
                        "--t-in",
                        str(tin),
                        "--flux",
                        str(flux),
                        "--area",
                        str(area),
                        "--t-max",
                        str(tin + 400.0),
                    ],
                )
                self.assertEqual(code, 0, err)
                code, from_q, err = run(
                    SCRIPTS["coolant"],
                    [
                        "--mdot",
                        str(mdot),
                        "--cp",
                        str(cp),
                        "--t-in",
                        str(tin),
                        "--q-dot",
                        str(heat),
                        "--t-max",
                        str(tin + 400.0),
                    ],
                )
                self.assertEqual(code, 0, err)
                tout = tin + heat / (mdot * cp)
                self.assertTrue(close(num(from_flux, "Q_W"), heat))
                self.assertTrue(close(num(from_flux, "T_out_K"), num(from_q, "T_out_K")))
                self.assertTrue(close(num(from_flux, "T_out_K"), tout))
                self.assertTrue(close(num(from_flux, "dT_K"), tout - tin))
                self.assertEqual(from_flux["limit"], "pass" if tout <= tin + 400.0 else "fail")
                self.assertTrue(close(num(from_flux, "mdot_min_kg_s"), heat / (cp * 400.0)))

    def test_limit_boundary(self) -> None:
        code, data, err = run(
            SCRIPTS["coolant"],
            ["--mdot", "2", "--cp", "2000", "--t-in", "300", "--q-dot", "400000", "--t-max", "400"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(data["limit"], "pass")
        self.assertTrue(close(num(data, "mdot_min_kg_s"), 2.0))
        code, data, err = run(
            SCRIPTS["coolant"],
            ["--mdot", "2", "--cp", "2000", "--t-in", "300", "--q-dot", "400000", "--t-max", "350"],
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(data["limit"], "fail")
        self.assertGreater(num(data, "mdot_min_kg_s"), 2.0)
        self.assertTrue(close(num(data, "Q_capacity_W"), 2.0 * 2000.0 * 50.0))

    def test_rejects_bad_inputs(self) -> None:
        cases = [
            (["--mdot", "1", "--cp", "1000"], "missing"),
            (["--mdot", "1", "--cp", "1000", "--t-in", "300"], "q-dot"),
            (["--mdot", "1", "--cp", "1000", "--t-in", "300", "--q-dot", "10", "--flux", "1", "--area", "1"], "not both"),
            (["--mdot", "1", "--cp", "1000", "--t-in", "300", "--flux", "10"], "both required"),
            (["--mdot", "1", "--cp", "1000", "--t-in", "300", "--q-dot", "0"], "heat rate"),
            (["--mdot", "1", "--cp", "1000", "--t-in", "300", "--q-dot", "10", "--t-max", "300"], "t-max"),
            (["--mdot", "1", "--cp", "1000", "--t-in", "300", "--q-dot", "nan"], "finite"),
            (["--mdot", "1e-300", "--cp", "1e-300", "--t-in", "300", "--q-dot", "1e308"], "finite"),
        ]
        for args, needle in cases:
            with self.subTest(args=args):
                code, _data, err = run(SCRIPTS["coolant"], args)
                self.assertEqual(code, 2, err)
                self.assertIn(needle, err)

    def test_png_header(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "coolant.png"
            code, _data, err = run(
                SCRIPTS["coolant"],
                [
                    "--mdot",
                    "2",
                    "--cp",
                    "2000",
                    "--t-in",
                    "300",
                    "--q-dot",
                    "400000",
                    "--t-max",
                    "450",
                    "--out",
                    str(path),
                ],
            )
            self.assertEqual(code, 0, err)
            self.assertTrue(path.read_bytes().startswith(b"\x89PNG"))


class ChainTests(unittest.TestCase):
    def test_pressure_fed_chain_three_cases(self) -> None:
        cases = [
            dict(thrust=1500.0, cf=1.5, pc=2.0e6, cstar=1600.0, rho=1000.0, cd=0.75, dp=2.0e5, r=2.3, tb=10.0, rho_ox=1141.0, rho_fuel=810.0, height=1.0, jacket=1.0e5, tw=800.0, gamma=1.22, mw=22.0, tc=3400.0, recovery=0.95, area=0.002, cp=2000.0, tin=300.0, tmax=500.0),
            dict(thrust=50000.0, cf=1.6, pc=7.0e6, cstar=1800.0, rho=1141.0, cd=0.7, dp=8.0e5, r=2.7, tb=40.0, rho_ox=1141.0, rho_fuel=70.0, height=-2.0, jacket=2.0e5, tw=600.0, gamma=1.21, mw=14.0, tc=3600.0, recovery=0.92, area=0.02, cp=14000.0, tin=25.0, tmax=200.0),
            dict(thrust=200.0, cf=1.4, pc=1.0e6, cstar=1400.0, rho=800.0, cd=0.85, dp=1.2e5, r=1.6, tb=5.0, rho_ox=1400.0, rho_fuel=800.0, height=0.0, jacket=0.0, tw=500.0, gamma=1.25, mw=24.0, tc=2800.0, recovery=1.0, area=0.001, cp=2500.0, tin=290.0, tmax=320.0),
        ]
        for case in cases:
            with self.subTest(thrust=case["thrust"], pc=case["pc"]):
                code, throat, err = run(
                    ROOT / "skills" / "ROCKET - ThroatSizingandMassFlow" / "throat_sizing.py",
                    ["--thrust", str(case["thrust"]), "--cf", str(case["cf"]), "--pc", str(case["pc"]), "--cstar", str(case["cstar"])],
                )
                self.assertEqual(code, 0, err)
                mdot = num(throat, "mdot_kg_s")
                code, inj, err = run(
                    SCRIPTS["injector"],
                    ["--mdot", str(mdot), "--rho", str(case["rho"]), "--cd", str(case["cd"]), "--dp", str(case["dp"])],
                )
                self.assertEqual(code, 0, err)
                code, feed, err = run(
                    SCRIPTS["feed"],
                    [
                        "--pc",
                        str(case["pc"]),
                        "--dp-injector",
                        inj["dp_Pa"],
                        "--dp",
                        f"jacket={case['jacket']}",
                        "--rho",
                        str(case["rho"]),
                        "--height",
                        str(case["height"]),
                    ],
                )
                self.assertEqual(code, 0, err)
                expected_supply = case["pc"] + case["dp"] + case["jacket"] + case["rho"] * G0 * case["height"]
                self.assertTrue(close(num(feed, "p_supply_Pa"), expected_supply))
                self.assertTrue(close(num(feed, "meop_Pa"), num(feed, "p_supply_Pa")))
                code, heat, err = run(
                    SCRIPTS["heat"],
                    [
                        "--pc",
                        str(case["pc"]),
                        "--Tc",
                        str(case["tc"]),
                        "--cstar",
                        str(case["cstar"]),
                        "--throat",
                        throat["Dt_m"],
                        "--curvature",
                        str(0.8 * num(throat, "Dt_m")),
                        "--tw",
                        str(case["tw"]),
                        "--mw",
                        str(case["mw"]),
                        "--gamma",
                        str(case["gamma"]),
                        "--recovery",
                        str(case["recovery"]),
                        "--sigma",
                        "1",
                    ],
                )
                self.assertEqual(code, 0, err)
                self.assertGreater(num(heat, "q_dot_W_m2"), 0.0)
                code, cool, err = run(
                    SCRIPTS["coolant"],
                    [
                        "--mdot",
                        str(mdot / (case["r"] + 1.0)),
                        "--cp",
                        str(case["cp"]),
                        "--t-in",
                        str(case["tin"]),
                        "--flux",
                        heat["q_dot_W_m2"],
                        "--area",
                        str(case["area"]),
                        "--t-max",
                        str(case["tmax"]),
                    ],
                )
                self.assertEqual(code, 0, err)
                heat_rate = num(heat, "q_dot_W_m2") * case["area"]
                self.assertTrue(close(num(cool, "Q_W"), heat_rate))
                tout = case["tin"] + heat_rate / ((mdot / (case["r"] + 1.0)) * case["cp"])
                self.assertTrue(close(num(cool, "T_out_K"), tout))
                self.assertEqual(cool["limit"], "pass" if tout <= case["tmax"] else "fail")


class CatalogTests(unittest.TestCase):
    def test_tools_are_registered_with_required_flags(self) -> None:
        tools = load_catalog(ROOT)
        expected = {
            "injector_orifice_flow": ["--mdot", "--rho", "--cd"],
            "feed_system_pressure_budget": ["--pc"],
            "pump_hydraulic_power": ["--mdot", "--rho", "--dp", "--eta"],
            "throat_gas_side_heat_flux": ["--pc", "--Tc", "--cstar", "--curvature", "--tw"],
            "regenerative_coolant_heat_pickup": ["--mdot", "--cp", "--t-in"],
        }
        for name, required in expected.items():
            with self.subTest(tool=name):
                tool = tool_by_name(tools, name)
                self.assertIsNotNone(tool)
                assert tool is not None
                self.assertEqual(tool.required_options(), required)
                self.assertNotIn("--check", {flag.option for flag in tool.flags})
                self.assertNotIn("--out", {flag.option for flag in tool.flags})

    def test_feed_drops_repeat_and_runner_collects_png(self) -> None:
        tools = load_catalog(ROOT)
        feed = tool_by_name(tools, "feed_system_pressure_budget")
        assert feed is not None
        drop = next(flag for flag in feed.flags if flag.option == "--dp")
        self.assertTrue(drop.repeat)
        injector = tool_by_name(tools, "injector_orifice_flow")
        assert injector is not None
        result = run_tool(
            injector,
            {"mdot": 2.0, "rho": 1000.0, "cd": 0.75, "dp": 2.0e5},
            repo_root=ROOT,
        )
        self.assertEqual(result.exit_code, 0, result.text)
        self.assertTrue(result.files)
        self.assertTrue(result.files[0].read_bytes().startswith(b"\x89PNG"))
        self.assertIn("graph:", result.text)
        missing = run_tool(injector, {"mdot": 1.0}, repo_root=ROOT)
        self.assertNotEqual(missing.exit_code, 0)
        self.assertTrue(missing.missing_input)


if __name__ == "__main__":
    unittest.main()
