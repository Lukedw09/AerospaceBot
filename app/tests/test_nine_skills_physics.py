"""Independent physical checks for the nine added skills.

Expected values are derived here from orbital mechanics, the rocket equation,
membrane equilibrium, and the base-excited oscillator. They are not copied
from each program's --check.
"""

from __future__ import annotations

import importlib.util
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G0 = 9.80665
R0 = 6.3742e6
MU_EARTH = G0 * R0 * R0

# NASA TP-1770 Table 3, Marshall-Palmer, 0 C. Frequency in GHz.
RAIN_TABLE = (
    (2.0, 0.000345, 0.891),
    (4.0, 0.00147, 1.016),
    (6.0, 0.00371, 1.124),
    (12.0, 0.0215, 1.136),
    (15.0, 0.0368, 1.118),
    (20.0, 0.0719, 1.097),
    (30.0, 0.186, 1.043),
    (40.0, 0.362, 0.972),
    (94.0, 1.402, 0.744),
)


def script(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def run(program: Path, args: list[str]) -> dict[str, str]:
    proc = subprocess.run(
        [sys.executable, str(program), *args],
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
    if proc.returncode != 0:
        raise AssertionError(
            f"{program.name} exited {proc.returncode}\n{proc.stderr}\n{proc.stdout}"
        )
    return data


def run_fail(program: Path, args: list[str]) -> str:
    proc = subprocess.run(
        [sys.executable, str(program), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        raise AssertionError(f"{program.name} accepted {args}\n{proc.stdout}")
    if proc.returncode != 2 or not proc.stderr.startswith("error:"):
        raise AssertionError(
            f"{program.name} exited {proc.returncode}\n{proc.stderr}\n{proc.stdout}"
        )
    return proc.stderr


def num(data: dict[str, str], key: str) -> float:
    if key not in data:
        raise AssertionError(f"missing {key} in {sorted(data)}")
    return float(data[key])


def close(actual: float, expected: float, rel: float = 1e-6, abs_tol: float = 1e-6) -> bool:
    return abs(actual - expected) <= abs_tol + rel * abs(expected)


def assert_close(
    test: unittest.TestCase,
    actual: float,
    expected: float,
    msg: str,
    rel: float = 1e-6,
    abs_tol: float = 1e-6,
) -> None:
    test.assertTrue(
        close(actual, expected, rel=rel, abs_tol=abs_tol),
        f"{msg}: got {actual}, expected {expected}",
    )


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"phys_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def png_ok(data: dict[str, str]) -> None:
    path = Path(data["graph"])
    if not path.is_file() or not path.read_bytes().startswith(b"\x89PNG"):
        raise AssertionError(f"PNG missing at {path}")


def transmissibility(ratio: float, zeta: float) -> float:
    two = 2.0 * zeta * ratio
    return math.sqrt((1.0 + two * two) / ((1.0 - ratio * ratio) ** 2 + two * two))


def cw_rk4(
    motion: float,
    time_s: float,
    x0: float,
    z0: float,
    xd0: float,
    zd0: float,
    steps: int = 40000,
) -> tuple[float, float, float, float]:
    """Integrate x-double-dot = 2 n z-dot, z-double-dot = 3 n^2 z - 2 n x-dot."""

    def deriv(state: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
        _x, z, xd, zd = state
        return (xd, zd, 2.0 * motion * zd, 3.0 * motion * motion * z - 2.0 * motion * xd)

    if time_s == 0.0:
        return (x0, z0, xd0, zd0)
    step = time_s / steps
    state = (x0, z0, xd0, zd0)
    for _ in range(steps):
        k1 = deriv(state)
        s2 = tuple(state[i] + 0.5 * step * k1[i] for i in range(4))
        k2 = deriv(s2)
        s3 = tuple(state[i] + 0.5 * step * k2[i] for i in range(4))
        k3 = deriv(s3)
        s4 = tuple(state[i] + step * k3[i] for i in range(4))
        k4 = deriv(s4)
        state = tuple(
            state[i] + (step / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) for i in range(4)
        )
    return state


class ThinWallPhysics(unittest.TestCase):
    program = script("skills", "STRUCT - ThinWallPressureVessel", "thin_wall_pressure_vessel.py")

    def test_sp8025_ratio_and_sphere_half(self) -> None:
        # SP-8025 sample: D = 40, t = 0.1, so R/t = 200 and hoop = 200 p.
        cylinder = run(self.program, ["--p", "1000", "--radius", "20", "--thickness", "0.1", "--shape", "cylinder"])
        self.assertEqual(cylinder["governing"], "hoop")
        self.assertEqual(cylinder["title"], "Thin-wall pressure vessel")
        assert_close(self, num(cylinder, "sigma_hoop_Pa"), 200000.0, "hoop")
        assert_close(self, num(cylinder, "sigma_long_Pa"), 100000.0, "longitudinal")
        self.assertAlmostEqual(num(cylinder, "sigma_hoop_Pa"), 2.0 * num(cylinder, "sigma_long_Pa"), places=6)

        sphere = run(self.program, ["--p", "1000", "--radius", "20", "--thickness", "0.1", "--shape", "sphere"])
        self.assertEqual(sphere["governing"], "membrane")
        assert_close(self, num(sphere, "sigma_Pa"), num(cylinder, "sigma_long_Pa"), "sphere matches longitudinal")

    def test_zero_margin_wall_and_scaling(self) -> None:
        allowable = 2.5e8
        sized = run(
            self.program,
            ["--p", "2e6", "--radius", "0.4", "--allowable", str(allowable), "--shape", "cylinder"],
        )
        assert_close(self, num(sized, "t_m"), 2e6 * 0.4 / allowable, "hoop thickness")
        assert_close(self, num(sized, "sigma_hoop_Pa"), allowable, "sized hoop equals allowable")
        self.assertNotIn("margin_of_safety", sized)

        both = run(
            self.program,
            ["--p", "2e6", "--radius", "0.4", "--thickness", "0.008", "--allowable", str(allowable), "--shape", "cylinder"],
        )
        hoop = 2e6 * 0.4 / 0.008
        assert_close(self, num(both, "margin_of_safety"), allowable / hoop - 1.0, "margin")

        sphere = run(
            self.program,
            ["--p", "2e6", "--radius", "0.4", "--allowable", str(allowable), "--shape", "sphere"],
        )
        assert_close(self, num(sphere, "t_m"), 0.5 * num(sized, "t_m"), "sphere wall is half the hoop wall")

        doubled = run(self.program, ["--p", "4e6", "--radius", "0.4", "--thickness", "0.008", "--shape", "cylinder"])
        base = run(self.program, ["--p", "2e6", "--radius", "0.4", "--thickness", "0.008", "--shape", "cylinder"])
        assert_close(self, num(doubled, "sigma_hoop_Pa"), 2.0 * num(base, "sigma_hoop_Pa"), "linear in pressure")

    def test_rejects_incomplete_input(self) -> None:
        run_fail(self.program, ["--p", "1e6", "--radius", "0.5", "--shape", "cylinder"])
        run_fail(self.program, ["--p", "1e6", "--radius", "0.5", "--thickness", "0.01", "--shape", "torus"])

    def test_png(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            png = str(Path(folder) / "wall.png")
            data = run(self.program, ["--p", "1e6", "--radius", "0.5", "--thickness", "0.002", "--shape", "sphere", "--out", png])
            png_ok(data)


class BaseExcitationPhysics(unittest.TestCase):
    program = script("skills", "VIBR - BaseExcitationTransmissibility", "base_excitation_transmissibility.py")

    def test_identities_and_isolation_boundary(self) -> None:
        for zeta in (0.0, 0.05, 0.4, 0.9, 2.0):
            for ratio in (0.0, 0.5, math.sqrt(2.0), 2.0, 5.0):
                if zeta == 0.0 and math.isclose(ratio, 1.0):
                    continue
                if ratio == 0.0:
                    continue
                data = run(self.program, ["--fn", "10", "--zeta", str(zeta), "--f", str(10.0 * ratio)])
                assert_close(self, num(data, "T"), transmissibility(ratio, zeta), f"T zeta={zeta} r={ratio}")
                self.assertEqual(data["isolation"], "yes" if ratio > math.sqrt(2.0) else "no")
        corner = run(self.program, ["--fn", "8", "--zeta", "0.2", "--f", str(8.0 * math.sqrt(2.0))])
        assert_close(self, num(corner, "T"), 1.0, "T at sqrt(2)")
        self.assertEqual(corner["isolation"], "no")
        self.assertEqual(corner["title"], "Base excitation transmissibility")

    def test_peak_is_a_maximum_only_for_light_damping(self) -> None:
        light = run(self.program, ["--fn", "5", "--zeta", "0.1", "--f", "3"])
        r_peak = num(light, "r_peak")
        assert_close(self, r_peak, math.sqrt(1.0 - 2.0 * 0.1**2), "peak ratio")
        peak = transmissibility(r_peak, 0.1)
        self.assertGreater(peak, transmissibility(r_peak * 0.85, 0.1))
        self.assertGreater(peak, transmissibility(r_peak * 1.15, 0.1))
        heavy = run(self.program, ["--fn", "5", "--zeta", str(1.0 / math.sqrt(2.0)), "--f", "3"])
        self.assertNotIn("r_peak", heavy)
        heavier = run(self.program, ["--fn", "5", "--zeta", "1.2", "--f", "3"])
        self.assertNotIn("r_peak", heavier)

    def test_undamped_limits(self) -> None:
        below = run(self.program, ["--fn", "4", "--zeta", "0", "--f", "2"])
        assert_close(self, num(below, "T"), 1.0 / abs(1.0 - 0.5**2), "undamped below resonance")
        above = run(self.program, ["--fn", "4", "--zeta", "0", "--f", "8"])
        assert_close(self, num(above, "T"), 1.0 / abs(1.0 - 4.0), "undamped above resonance")
        self.assertIn("r_peak", above)
        message = run_fail(self.program, ["--fn", "4", "--zeta", "0", "--f", "4"])
        self.assertIn("undamped resonance", message)

    def test_high_frequency_decays(self) -> None:
        low = run(self.program, ["--fn", "10", "--zeta", "0.05", "--f", "30"])
        high = run(self.program, ["--fn", "10", "--zeta", "0.05", "--f", "80"])
        self.assertLess(num(high, "T"), num(low, "T"))
        self.assertLess(num(high, "T"), 1.0)


class ReactionWheelPhysics(unittest.TestCase):
    program = script("skills", "ADCS - ReactionWheelSizing", "reaction_wheel_sizing.py")
    slew = script("skills", "ADCS - SlewMomentum", "slew_momentum.py")

    def test_inertia_and_margins_from_slew(self) -> None:
        inertia = 2.0
        angle = math.pi / 2.0
        time_s = 60.0
        slew = run(self.slew, ["--inertia", str(inertia), "--angle", str(angle), "--time", str(time_s)])
        torque = 4.0 * inertia * angle / time_s**2
        stored = 2.0 * inertia * angle / time_s
        assert_close(self, num(slew, "tau_N_m"), torque, "slew torque")
        assert_close(self, num(slew, "H_N_m_s"), stored, "slew impulse")

        omega = 600.0
        wheel = run(
            self.program,
            ["--H", str(stored), "--tau", str(torque), "--omega-max", str(omega), "--H-max", "1", "--tau-max", "0.05"],
        )
        self.assertEqual(wheel["title"], "Reaction wheel sizing")
        assert_close(self, num(wheel, "I_w_kg_m2"), stored / omega, "wheel inertia")
        assert_close(self, num(wheel, "I_w_kg_m2") * omega, num(wheel, "H_N_m_s"), "H = I omega")
        assert_close(self, num(wheel, "margin_H"), 1.0 / stored - 1.0, "momentum margin")
        assert_close(self, num(wheel, "margin_tau"), 0.05 / torque - 1.0, "torque margin")

        disturbance = run(self.slew, ["--torque", "1e-4", "--duration", "5400"])
        assert_close(self, num(disturbance, "H_N_m_s"), 0.54, "disturbance storage")
        bare = run(self.program, ["--H", "0.54", "--tau", "0.01", "--omega-max", "100"])
        self.assertNotIn("margin_H", bare)
        self.assertNotIn("margin_tau", bare)
        assert_close(self, num(bare, "I_w_kg_m2"), 0.0054, "disturbance wheel")

    def test_png(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            png = str(Path(folder) / "wheel.png")
            data = run(self.program, ["--H", "1", "--tau", "0.02", "--omega-max", "200", "--out", png])
            png_ok(data)


class RendezvousPhasingPhysics(unittest.TestCase):
    program = script("skills", "ASTRO - RendezvousPhasing", "rendezvous_phasing.py")

    def _expect(self, radius: float, phase: float, lead: str, revs: int, mu: float) -> dict[str, float]:
        motion = math.sqrt(mu / radius**3)
        if lead == "target":
            wait = (2.0 * math.pi * revs - phase) / motion
        else:
            wait = (2.0 * math.pi * revs + phase) / motion
        period = wait / revs
        semimajor = (mu * (period / (2.0 * math.pi)) ** 2) ** (1.0 / 3.0)
        circular = math.sqrt(mu / radius)
        ellipse = math.sqrt(mu * (2.0 / radius - 1.0 / semimajor))
        other = 2.0 * semimajor - radius
        return {
            "n": motion,
            "wait": wait,
            "period": period,
            "a": semimajor,
            "vc": circular,
            "ve": ellipse,
            "dv": abs(circular - ellipse),
            "other": other,
        }

    def test_angular_closure_kepler_and_burns(self) -> None:
        radius = R0 + 400_000.0
        cases = (
            ("target", 0.4, 1),
            ("chaser", 0.4, 1),
            ("target", 1.2, 3),
            ("chaser", 0.8, 4),
        )
        for lead, phase, revs in cases:
            data = run(
                self.program,
                ["--radius", str(radius), "--phase", str(phase), "--lead", lead, "--revs", str(revs)],
            )
            expected = self._expect(radius, phase, lead, revs, MU_EARTH)
            self.assertEqual(data["title"], "Rendezvous phasing")
            assert_close(self, num(data, "wait_s"), expected["wait"], f"{lead} wait")
            assert_close(self, num(data, "period_s") * revs, num(data, "wait_s"), "N periods fill the wait")
            # Target, which started `phase` ahead or behind, is back at the burn point.
            if lead == "target":
                traveled = 2.0 * math.pi * revs - phase
                self.assertLess(num(data, "a_m"), radius)
                self.assertLess(num(data, "ve_m_s"), num(data, "vc_m_s"))
                assert_close(self, num(data, "ra_m"), radius, "catch burn is at apoapsis")
            else:
                traveled = 2.0 * math.pi * revs + phase
                self.assertGreater(num(data, "a_m"), radius)
                self.assertGreater(num(data, "ve_m_s"), num(data, "vc_m_s"))
                assert_close(self, num(data, "rp_m"), radius, "loiter burn is at periapsis")
            assert_close(self, num(data, "n_rad_s") * num(data, "wait_s"), traveled, "target angle")
            mu_from_period = (4.0 * math.pi**2) * num(data, "a_m") ** 3 / num(data, "period_s") ** 2
            assert_close(self, mu_from_period, MU_EARTH, "Kepler")
            energy = 0.5 * num(data, "ve_m_s") ** 2 - MU_EARTH / radius
            assert_close(self, energy, -MU_EARTH / (2.0 * num(data, "a_m")), "vis-viva energy")
            assert_close(self, num(data, "dv_in_m_s"), expected["dv"], "one burn")
            assert_close(self, num(data, "dv_out_m_s"), num(data, "dv_in_m_s"), "burns match")
            assert_close(self, num(data, "dv_total_m_s"), 2.0 * num(data, "dv_in_m_s"), "total")
            assert_close(self, num(data, "rp_m") + num(data, "ra_m"), 2.0 * num(data, "a_m"), "apsis sum")

    def test_planet_warning_uses_the_run_radius(self) -> None:
        safe = run(self.program, ["--alt", "400000", "--phase", "0.05", "--lead", "target"])
        self.assertGreater(num(safe, "rp_m"), R0)
        self.assertNotIn("warning", safe)
        deep = run(self.program, ["--alt", "400000", "--phase", "1.0", "--lead", "target"])
        self.assertLess(num(deep, "rp_m"), R0)
        self.assertIn("warning", deep)

        # A non-Earth planet must not inherit the Earth-radius warning.
        small = run(
            self.program,
            ["--radius", "1000", "--R0", "100", "--mu", "1", "--phase", "0.2", "--lead", "chaser"],
        )
        self.assertGreater(num(small, "rp_m"), 100.0)
        self.assertNotIn("warning", small)

    def test_rejects_unequal_orbits_and_huge_phase(self) -> None:
        run_fail(self.program, ["--r-target", "7000000", "--r-chaser", "8000000", "--phase", "0.2", "--lead", "target"])
        run_fail(self.program, ["--radius", "7000000", "--phase", str(2.0 * math.pi), "--lead", "target", "--revs", "1"])


class ClohessyWiltshirePhysics(unittest.TestCase):
    program = script("skills", "ASTRO - RelativeOrbitClohessyWiltshire", "relative_orbit_clohessy_wiltshire.py")

    def test_matches_integrated_hill_equations(self) -> None:
        radius = 7_000_000.0
        motion = math.sqrt(MU_EARTH / radius**3)
        period = 2.0 * math.pi / motion
        cases = (
            (0.0, 0.0, 0.0, 0.0, 100.0),
            (20.0, 0.0, 0.0, 0.0, period),
            (0.0, 250.0, 2.0 * motion * 250.0, 0.0, 0.37 * period),
            (15.0, -40.0, 0.02, -0.01, 0.2 * period),
            (-30.0, 80.0, 0.05, 0.03, period),
        )
        for x0, z0, xd0, zd0, time_s in cases:
            expected = cw_rk4(motion, time_s, x0, z0, xd0, zd0)
            data = run(
                self.program,
                [
                    "--a",
                    str(radius),
                    "--x",
                    str(x0),
                    "--z",
                    str(z0),
                    "--xdot",
                    str(xd0),
                    "--zdot",
                    str(zd0),
                    "--time",
                    str(time_s),
                ],
            )
            self.assertEqual(data["title"], "Relative orbit")
            assert_close(self, num(data, "n_rad_s"), motion, "mean motion")
            for key, value in zip(("x_m", "z_m", "xdot_m_s", "zdot_m_s"), expected, strict=True):
                assert_close(self, num(data, key), value, key, rel=1e-4, abs_tol=1e-3)
            assert_close(self, num(data, "dv_null_x_m_s"), -xd0, "null along-track")
            assert_close(self, num(data, "dv_null_z_m_s"), -zd0, "null radial")
            assert_close(self, num(data, "dv_hold_x_m_s"), 2.0 * motion * z0 - xd0, "hold along-track")
            assert_close(self, num(data, "dv_hold_z_m_s"), -zd0, "hold radial")

    def test_closed_ellipse_returns_and_drift_rate(self) -> None:
        radius = R0 + 500_000.0
        motion = math.sqrt(MU_EARTH / radius**3)
        period = 2.0 * math.pi / motion
        z0 = 200.0
        hold = run(
            self.program,
            ["--alt", "500000", "--x", "0", "--z", str(z0), "--xdot", str(2.0 * motion * z0), "--zdot", "0", "--time", str(period)],
        )
        assert_close(self, num(hold, "x_m"), 0.0, "closed ellipse x after one rev", abs_tol=1e-3)
        assert_close(self, num(hold, "z_m"), z0, "closed ellipse z after one rev", abs_tol=1e-3)
        quarter = run(
            self.program,
            [
                "--alt",
                "500000",
                "--x",
                "0",
                "--z",
                str(z0),
                "--xdot",
                str(2.0 * motion * z0),
                "--zdot",
                "0",
                "--time",
                str(0.25 * period),
            ],
        )
        assert_close(self, num(quarter, "z_m"), 0.0, "quarter-rev radial", abs_tol=1e-2)
        assert_close(self, num(quarter, "x_m"), 2.0 * z0, "quarter-rev along-track", abs_tol=1e-2)

        # Zero relative velocity at a radial offset has secular drift 6 n z.
        # At an integer number of chief revolutions the bounded terms vanish.
        one = run(
            self.program,
            ["--a", str(radius), "--x", "0", "--z", str(z0), "--xdot", "0", "--zdot", "0", "--time", str(period)],
        )
        five = run(
            self.program,
            ["--a", str(radius), "--x", "0", "--z", str(z0), "--xdot", "0", "--zdot", "0", "--time", str(5.0 * period)],
        )
        per_rev = 12.0 * math.pi * z0
        assert_close(self, num(one, "x_m"), per_rev, "one-rev drift", rel=1e-4, abs_tol=1e-2)
        assert_close(self, num(five, "x_m") - num(one, "x_m"), 4.0 * per_rev, "later drift", rel=1e-4, abs_tol=1e-2)

    def test_altitude_matches_radius_and_rejects_both(self) -> None:
        by_alt = run(self.program, ["--alt", "400000", "--x", "1", "--z", "2", "--xdot", "0", "--zdot", "0", "--time", "10"])
        by_radius = run(
            self.program,
            ["--a", str(R0 + 400000.0), "--x", "1", "--z", "2", "--xdot", "0", "--zdot", "0", "--time", "10"],
        )
        assert_close(self, num(by_alt, "x_m"), num(by_radius, "x_m"), "altitude and radius")
        run_fail(self.program, ["--a", "7000000", "--alt", "400000", "--x", "0", "--z", "0", "--xdot", "0", "--zdot", "0", "--time", "1"])


class ElectricPropulsionPhysics(unittest.TestCase):
    program = script("skills", "ROCKET - ElectricPropulsionDeltaV", "electric_propulsion_delta_v.py")
    vacuum = script("skills", "ASTRO - VacuumPropellantMass", "vacuum_propellant_mass.py")

    def test_rocket_equation_power_and_duty(self) -> None:
        dry = 80.0
        thrust = 0.04
        delta_v = 2500.0
        isp = 1600.0
        eta = 0.55
        duty = 0.8
        exhaust = isp * G0
        data = run(
            self.program,
            [
                "--dry",
                str(dry),
                "--thrust",
                str(thrust),
                "--dv",
                str(delta_v),
                "--isp",
                str(isp),
                "--eta",
                str(eta),
                "--duty",
                str(duty),
            ],
        )
        self.assertEqual(data["title"], "Electric propulsion delta-v")
        propellant = dry * (math.exp(delta_v / exhaust) - 1.0)
        wet = dry + propellant
        assert_close(self, num(data, "ve_m_s"), exhaust, "isp to exhaust speed")
        assert_close(self, num(data, "mp_kg"), propellant, "propellant")
        assert_close(self, num(data, "m0_kg"), wet, "wet")
        thrust_time = propellant * exhaust / thrust
        assert_close(self, num(data, "tb_thrust_s"), thrust_time, "thrusting time")
        assert_close(self, num(data, "tb_s"), thrust_time / duty, "calendar time")
        power = thrust * exhaust / (2.0 * eta)
        assert_close(self, num(data, "P_W"), power, "input power")
        assert_close(self, num(data, "P_W") * eta, 0.5 * thrust * exhaust, "jet power")
        assert_close(self, num(data, "specific_power_W_kg"), power / wet, "specific power")
        # Mass flow from thrust matches propellant over thrusting time.
        assert_close(self, thrust / exhaust, propellant / thrust_time, "mass flow")

        vacuum = run(self.vacuum, ["--dry", str(dry), "--isp", str(isp), "--name", "ep", "--dv", str(delta_v)])
        assert_close(self, num(data, "mp_kg"), num(vacuum, "m_propellant_kg"), "matches vacuum propellant")
        assert_close(self, num(data, "m0_kg"), num(vacuum, "m_wet_kg"), "matches vacuum wet mass")

    def test_small_delta_v_and_independence(self) -> None:
        dry = 50.0
        exhaust = 20_000.0
        delta_v = 20.0
        data = run(self.program, ["--dry", str(dry), "--thrust", "0.1", "--dv", str(delta_v), "--ve", str(exhaust)])
        linear = dry * delta_v / exhaust
        assert_close(self, num(data, "mp_kg"), linear, "small delta-v", rel=1e-3)
        self.assertAlmostEqual(num(data, "eta"), 1.0)
        self.assertAlmostEqual(num(data, "duty"), 1.0)
        other = run(self.program, ["--dry", str(dry), "--thrust", "0.1", "--dv", "4000", "--ve", str(exhaust), "--eta", "0.5"])
        self.assertAlmostEqual(num(other, "P_W"), num(data, "P_W") / 0.5)
        self.assertGreater(num(other, "mp_kg"), num(data, "mp_kg"))

    def test_rejects_both_exhaust_paths(self) -> None:
        run_fail(self.program, ["--dry", "10", "--thrust", "0.1", "--dv", "100", "--isp", "1000", "--ve", "10000"])
        run_fail(self.program, ["--dry", "10", "--thrust", "0.1", "--dv", "100"])


class RainAttenuationPhysics(unittest.TestCase):
    program = script("skills", "COMMS - RainAttenuation", "rain_attenuation.py")

    def test_table_nodes_and_published_21_db(self) -> None:
        for ghz, a_coeff, b_coeff in RAIN_TABLE:
            data = run(
                self.program,
                ["--rate", "10", "--freq", str(ghz * 1e9), "--elevation", "1", "--path", "1000"],
            )
            assert_close(self, num(data, "a_coeff"), a_coeff, f"a at {ghz} GHz")
            assert_close(self, num(data, "b_coeff"), b_coeff, f"b at {ghz} GHz")
            gamma = a_coeff * 10.0**b_coeff
            assert_close(self, num(data, "gamma_dB_per_km"), gamma, f"gamma at {ghz}")
            assert_close(self, num(data, "A_dB"), gamma * 1.0, "1 km path")
        published = run(
            self.program,
            ["--rate", "50", "--freq", "20e9", "--elevation", str(math.radians(30.0)), "--path", "4000"],
        )
        self.assertEqual(published["title"], "Rain attenuation")
        gamma = 0.0719 * 50.0**1.097
        assert_close(self, num(published, "gamma_dB_per_km"), gamma, "20 GHz specific")
        self.assertAlmostEqual(gamma, 5.25, delta=0.05)
        assert_close(self, num(published, "A_dB"), 4.0 * gamma, "4 km")
        self.assertAlmostEqual(num(published, "A_dB"), 21.0, delta=0.2)
        assert_close(self, num(published, "power_ratio"), 10.0 ** (-num(published, "A_dB") / 10.0), "power ratio")

    def test_log_frequency_interpolation_and_path_elevation(self) -> None:
        f0, a0, b0 = RAIN_TABLE[3]
        f1, a1, b1 = RAIN_TABLE[4]
        midpoint = math.sqrt(f0 * f1)
        data = run(
            self.program,
            ["--rate", "25", "--freq", str(midpoint * 1e9), "--elevation", "0.4", "--path", "2500"],
        )
        assert_close(self, num(data, "a_coeff"), math.sqrt(a0 * a1), "log interpolation of a")
        assert_close(self, num(data, "b_coeff"), 0.5 * (b0 + b1), "linear interpolation of b")
        short = run(self.program, ["--rate", "25", "--freq", str(midpoint * 1e9), "--elevation", "0.4", "--path", "1000"])
        assert_close(self, num(data, "A_dB"), 2.5 * num(short, "A_dB"), "linear in path")
        low = run(self.program, ["--rate", "25", "--freq", "12e9", "--elevation", "0.1", "--path", "1000"])
        high = run(self.program, ["--rate", "25", "--freq", "12e9", "--elevation", "1.0", "--path", "1000"])
        assert_close(self, num(low, "A_dB"), num(high, "A_dB"), "elevation does not scale attenuation")
        assert_close(self, num(low, "h_vert_m"), 1000.0 * math.sin(0.1), "vertical thickness")
        self.assertIn("warning", low)
        self.assertNotIn("warning", high)
        self.assertGreater(num(data, "A_dB"), num(short, "A_dB"))

    def test_rejects_frequency_outside_the_table(self) -> None:
        run_fail(self.program, ["--rate", "10", "--freq", "1e9", "--elevation", "1", "--path", "1000"])
        run_fail(self.program, ["--rate", "10", "--freq", "100e9", "--elevation", "1", "--path", "1000"])


class PhugoidPhysics(unittest.TestCase):
    program = script("skills", "AERO - PhugoidAndShortPeriod", "phugoid_and_short_period.py")

    def test_phugoid_depends_only_on_speed(self) -> None:
        base = ["--rho", "1.2", "--wing-loading", "3000", "--cla", "5", "--static-margin", "0.1", "--mac", "2", "--ky", "1.5"]
        slow = run(self.program, ["--speed", "80", *base])
        fast = run(self.program, ["--speed", "160", *base])
        other = run(self.program, ["--speed", "80", "--rho", "0.4", "--wing-loading", "8000", "--cla", "4", "--static-margin", "0.2", "--mac", "3", "--ky", "2"])
        self.assertEqual(slow["title"], "Phugoid and short period")
        expected = 2.0 * math.pi * 80.0 / (G0 * math.sqrt(2.0))
        assert_close(self, num(slow, "T_ph_s"), expected, "phugoid period")
        assert_close(self, num(slow, "omega_ph_rad_s") * num(slow, "T_ph_s"), 2.0 * math.pi, "phugoid 2 pi")
        assert_close(self, num(fast, "T_ph_s"), 2.0 * num(slow, "T_ph_s"), "period doubles with speed")
        assert_close(self, num(other, "T_ph_s"), num(slow, "T_ph_s"), "phugoid ignores aero inputs")
        assert_close(self, num(fast, "T_sp_s"), 0.5 * num(slow, "T_sp_s"), "short period halves with speed")

    def test_short_period_scaling(self) -> None:
        common = ["--speed", "100", "--rho", "1", "--wing-loading", "4000", "--cla", "6", "--mac", "2", "--ky", "1"]
        margin = run(self.program, [*common, "--static-margin", "0.04"])
        twice = run(self.program, [*common, "--static-margin", "0.16"])
        assert_close(self, num(twice, "omega_sp_rad_s"), 2.0 * num(margin, "omega_sp_rad_s"), "sqrt of static margin")
        heavy = run(self.program, ["--speed", "100", "--rho", "1", "--wing-loading", "16000", "--cla", "6", "--static-margin", "0.04", "--mac", "2", "--ky", "1"])
        assert_close(self, num(heavy, "omega_sp_rad_s"), 0.5 * num(margin, "omega_sp_rad_s"), "inverse sqrt of wing loading")
        formula = (100.0 / 1.0) * math.sqrt(1.0 * G0 * 2.0 * 6.0 * 0.04 / (2.0 * 4000.0))
        assert_close(self, num(margin, "omega_sp_rad_s"), formula, "static short-period formula")
        assert_close(self, num(margin, "omega_sp_rad_s") * num(margin, "T_sp_s"), 2.0 * math.pi, "short-period 2 pi")
        run_fail(self.program, [*common, "--static-margin", "0"])


class EquilibriumGlidePhysics(unittest.TestCase):
    program = script("skills", "THERM - EquilibriumGlideEntry", "equilibrium_glide_entry.py")

    def test_peak_load_is_one_over_lift_to_drag(self) -> None:
        for lod in (0.5, 1.0, 2.5):
            light = run(self.program, ["--ve", "6000", "--lod", str(lod), "--beta", "50"])
            heavy = run(self.program, ["--ve", "7500", "--lod", str(lod), "--beta", "500"])
            self.assertEqual(light["title"], "Equilibrium glide entry")
            assert_close(self, num(light, "a_peak_g"), 1.0 / lod, "peak g")
            assert_close(self, num(light, "a_peak_m_s2"), G0 / lod, "peak acceleration")
            assert_close(self, num(heavy, "a_peak_g"), num(light, "a_peak_g"), "peak ignores beta and speed")
            circular = math.sqrt(G0 * R0)
            entry = G0 * (1.0 - (6000.0 / circular) ** 2) / lod
            assert_close(self, num(light, "a_entry_m_s2"), entry, "entry deceleration")
            self.assertLess(num(light, "a_entry_m_s2"), num(light, "a_peak_m_s2"))

    def test_heating_scale_and_shared_atmosphere(self) -> None:
        ballistic = load_module(script("skills", "THERM - BallisticEntryPeakLoad", "ballistic_entry_peak_load.py"))
        lod = 1.2
        beta = 80.0
        data = run(self.program, ["--ve", "7800", "--lod", str(lod), "--beta", str(beta)])
        circular = math.sqrt(G0 * R0)
        heating_speed = circular * math.sqrt(2.0 / 3.0)
        assert_close(self, num(data, "vc_m_s"), circular, "circular speed")
        assert_close(self, num(data, "Vq_m_s"), heating_speed, "fast entry uses the 2/3 speed")
        density = beta / (R0 * lod)
        assert_close(self, num(data, "rho_q_kg_m3"), density, "heating density")
        assert_close(self, num(data, "q_scale"), math.sqrt(density) * heating_speed**3, "heat-flux scale")
        assert_close(self, num(data, "H_m"), ballistic.DEFAULT_H, "shared scale height")
        assert_close(self, num(data, "rho_ref_kg_m3"), ballistic.DEFAULT_RHO_REF, "shared reference density")
        altitude = ballistic.DEFAULT_H * math.log(ballistic.DEFAULT_RHO_REF / density)
        assert_close(self, num(data, "Zq_m"), altitude, "heating altitude")

        slow = run(self.program, ["--ve", "3000", "--lod", "1", "--beta", "100"])
        assert_close(self, num(slow, "Vq_m_s"), 3000.0, "slow entry heats at entry speed")
        doubled = run(self.program, ["--ve", "7800", "--lod", str(lod), "--beta", str(2.0 * beta)])
        assert_close(self, num(doubled, "q_scale"), math.sqrt(2.0) * num(data, "q_scale"), "scale grows with sqrt(beta)")

    def test_rejects_super_circular_and_partial_atmosphere(self) -> None:
        run_fail(self.program, ["--ve", "20000", "--lod", "1", "--beta", "100"])
        run_fail(self.program, ["--ve", "7000", "--lod", "1", "--beta", "100", "--scale-height", "8000"])


class LiftingEntryPhysics(unittest.TestCase):
    """Planar lifting entry. Cases are round physical states, not flights."""

    program = script("skills", "THERM - LiftingEntryTrajectory", "lifting_entry_trajectory.py")

    def _module(self):
        return load_module(self.program)

    def test_vacuum_energy_and_circular_orbit(self) -> None:
        lifting = self._module()
        radius = lifting.R0_EARTH
        mu = lifting.MU_EARTH
        speed = 6400.0
        gamma = math.radians(15.0)
        altitude = 180000.0
        coast = lifting.simulate(
            speed,
            gamma,
            altitude,
            0.0,
            1.0e18,
            None,
            None,
            None,
            0.0,
            None,
            radius,
            mu,
            "exponential",
            None,
            None,
            None,
            100000.0,
            80.0,
            None,
            None,
            None,
            None,
            1.0e-9,
            None,
            converge=False,
        )
        energy_0 = 0.5 * speed * speed - mu / (radius + altitude)
        energy_1 = 0.5 * float(coast["V_final_m_s"]) ** 2 - mu / (
            radius + float(coast["altitude_final_m"])
        )
        self.assertLess(abs(energy_1 - energy_0) / abs(energy_0), 1e-8)

        height = 200000.0
        circular = math.sqrt(mu / (radius + height))
        held = lifting.simulate(
            circular,
            0.0,
            height,
            0.0,
            1.0e18,
            None,
            None,
            None,
            0.0,
            None,
            radius,
            mu,
            "exponential",
            None,
            None,
            None,
            0.0,
            120.0,
            height + 50000.0,
            None,
            None,
            None,
            1.0e-9,
            None,
            converge=False,
        )
        self.assertLess(abs(float(held["altitude_final_m"]) - height) / height, 1e-8)
        self.assertLess(abs(float(held["V_final_m_s"]) - circular) / circular, 1e-8)
        self.assertLess(abs(float(held["gamma_final_rad"])), 1e-8)

    def test_steep_no_lift_matches_allen_eggers(self) -> None:
        # Allen–Eggers ignores gravity. With Earth mu the 3DOF peak sits a few
        # percent high at 7 km/s (still under 3% for this B, but not a fair
        # closed-form check). Kill gravity with a huge radius and tiny mu.
        ballistic = script("skills", "THERM - BallisticEntryPeakLoad", "ballistic_entry_peak_load.py")
        common = [
            "--altitude",
            "100000",
            "--lod",
            "0",
            "--beta",
            "5",
            "--bank-deg",
            "0",
            "--end-altitude",
            "15000",
            "--max-time-s",
            "80",
            "--radius",
            "1e12",
            "--mu",
            "1e-6",
        ]
        for speed in (7000, 11000):
            for degrees in (30, 60):
                gamma = math.radians(degrees)
                lifted = run(
                    self.program,
                    ["--speed", str(speed), "--gamma", str(gamma), *common],
                )
                closed = run(
                    ballistic,
                    ["--speed", str(speed), "--gamma", str(gamma), "--beta", "5"],
                )
                assert_close(
                    self,
                    num(lifted, "peak_g"),
                    num(closed, "a_peak_g"),
                    f"peak g at {speed} m/s, {degrees} deg",
                    rel=0.03,
                    abs_tol=0.0,
                )
                assert_close(
                    self,
                    num(lifted, "Z_peak_m"),
                    num(closed, "Z_peak_m"),
                    f"peak altitude at {speed} m/s, {degrees} deg",
                    rel=0.03,
                    abs_tol=0.0,
                )

    def test_shallow_lift_settles_on_equilibrium_glide(self) -> None:
        # Start on the lift balance. Compare drag-g at the speed of the peak
        # load to equilibrium_glide_entry_deceleration at that same speed.
        # Do not compare to a_peak = g/(L/D): that is the low-speed limit.
        lifting = self._module()
        glide = load_module(
            script("skills", "THERM - EquilibriumGlideEntry", "equilibrium_glide_entry.py")
        )
        speed = 7000.0
        beta = 200.0
        circular = math.sqrt(G0 * lifting.R0_EARTH)
        for lod in (1.0, 1.5):
            self.assertTrue(
                abs(glide.peak_deceleration(G0, lod) / G0 - 1.0 / lod) < 1e-12,
                "equilibrium peak is g/(L/D)",
            )
            rho = glide.heating_density(beta, G0, speed, circular, lod)
            altitude = lifting.DEFAULT_Z_REF + lifting.DEFAULT_H * math.log(
                lifting.DEFAULT_RHO_REF / rho
            )
            flown = lifting.simulate(
                speed,
                0.0,
                altitude,
                lod,
                beta,
                None,
                None,
                None,
                0.0,
                None,
                lifting.R0_EARTH,
                lifting.MU_EARTH,
                "exponential",
                None,
                None,
                None,
                20000.0,
                2000.0,
                None,
                None,
                None,
                None,
                1.0e-6,
                None,
                converge=False,
            )
            peak = max(flown["samples"], key=lambda row: row["load_g"])
            drag_g = peak["load_g"] / math.sqrt(1.0 + lod * lod)
            same_speed = glide.entry_deceleration(G0, peak["V"], circular, lod) / G0
            self.assertLess(
                abs(drag_g - same_speed) / same_speed,
                0.10,
                f"lod={lod}: drag {drag_g} vs same-speed equilibrium {same_speed} "
                f"at V={peak['V']}",
            )
            low_speed_limit = glide.peak_deceleration(G0, lod) / G0
            self.assertLess(
                same_speed,
                low_speed_limit,
                f"lod={lod}: peak occurs above the low-speed glide limit",
            )

    def test_bank_180_peaks_above_ballistic_above_lift_up(self) -> None:
        common = [
            "--speed",
            "7200",
            "--gamma",
            str(math.radians(8.0)),
            "--altitude",
            "90000",
            "--beta",
            "80",
            "--end-altitude",
            "30000",
            "--max-time-s",
            "200",
        ]
        lift_up = num(run(self.program, [*common, "--lod", "1", "--bank-deg", "0"]), "peak_g")
        ballistic = num(run(self.program, [*common, "--lod", "0", "--bank-deg", "0"]), "peak_g")
        lift_down = num(run(self.program, [*common, "--lod", "1", "--bank-deg", "180"]), "peak_g")
        self.assertLess(lift_up, ballistic)
        self.assertLess(ballistic, lift_down)

    def test_shallow_supercircular_lift_up_skips(self) -> None:
        data = run(
            self.program,
            [
                "--speed",
                "11000",
                "--gamma",
                str(math.radians(0.8)),
                "--altitude",
                "100000",
                "--lod",
                "1",
                "--beta",
                "200",
                "--bank-deg",
                "0",
                "--max-time-s",
                "200",
            ],
        )
        self.assertEqual(data["skip_out"], "true")
        self.assertEqual(data["end_reason"], "skip_out")
        self.assertGreater(num(data, "t_skip_s"), 0.0)
        self.assertLess(num(data, "min_altitude_m"), 100000.0)

    def test_halving_the_step_changes_peak_by_under_half_a_percent(self) -> None:
        data = run(
            self.program,
            [
                "--speed",
                "7000",
                "--gamma",
                str(math.radians(45.0)),
                "--altitude",
                "100000",
                "--lod",
                "0",
                "--beta",
                "20",
                "--bank-deg",
                "0",
                "--end-altitude",
                "30000",
                "--max-time-s",
                "80",
                "--dt",
                "0.25",
            ],
        )
        self.assertLess(num(data, "convergence_peak_g_rel"), 0.005)
        self.assertEqual(data["integrator"], "rk4")

    def test_equatorial_rotating_frame_matches_inertial_cartesian(self) -> None:
        lifting = self._module()
        speed = 7800.0
        gamma = math.radians(3.0)
        altitude = 85000.0
        lod = 0.7
        beta = 120.0
        bank_deg = 30.0
        end_altitude = 45000.0
        data = run(
            self.program,
            [
                "--speed",
                str(speed),
                "--gamma",
                str(gamma),
                "--altitude",
                str(altitude),
                "--lod",
                str(lod),
                "--beta",
                str(beta),
                "--bank-deg",
                str(bank_deg),
                "--end-altitude",
                str(end_altitude),
                "--max-time-s",
                "250",
                "--latitude-deg",
                "0",
                "--heading-deg",
                "90",
                "--rtol",
                "1e-7",
            ],
        )
        self.assertEqual(data["entry_frame"], "rotating")
        self.assertIn("latitude and heading held constant", data["assumptions"])
        self.assertLess(num(data, "speed_air_m_s"), num(data, "speed_inertial_m_s"))
        cartesian = _equatorial_cartesian_peak_rk4(
            lifting,
            speed,
            gamma,
            altitude,
            lod,
            beta,
            bank_deg,
            end_altitude,
            0.05,
        )
        assert_close(
            self,
            num(data, "peak_g"),
            cartesian,
            "rotating-frame peak versus inertial cartesian",
            rel=0.005,
            abs_tol=0.0,
        )

    def test_rejects_illegal_inputs(self) -> None:
        base = ["--speed", "7000", "--gamma", "0.1", "--altitude", "80000", "--lod", "1", "--beta", "100"]
        run_fail(self.program, base)
        run_fail(self.program, [*base, "--bank-deg", "0", "--bank-schedule", '[{"t_s": 0, "bank_deg": 5}]'])
        run_fail(self.program, [*base, "--bank-schedule", "[[0, 0], [10, 20]]"])
        run_fail(self.program, [*base, "--bank-deg", "0", "--mass", "500", "--cd", "0.5", "--area", "2"])
        atmosphere = run_fail(self.program, [*base, "--bank-deg", "0", "--scale-height", "8000"])
        self.assertIn("scale_height", atmosphere)
        self.assertIn("rho_ref", atmosphere)
        self.assertIn("z_ref", atmosphere)
        self.assertNotIn("--scale-height", atmosphere)
        self.assertNotIn("--beta", atmosphere)
        beta = run_fail(
            self.program,
            [*base, "--bank-deg", "0", "--mass", "500", "--cd", "0.5", "--area", "2"],
        )
        self.assertIn("beta", beta)
        self.assertNotIn("--beta", beta)
        run_fail(self.program, [*base, "--bank-deg", "0", "--latitude-deg", "10"])

    def test_baseline_peak_and_tighter_convergence(self) -> None:
        data = run(
            self.program,
            [
                "--speed",
                "11032.1",
                "--gamma",
                "0.113097",
                "--altitude",
                "121920",
                "--lod",
                "0.30076",
                "--beta",
                "355.70326",
                "--bank-deg",
                "0",
            ],
        )
        assert_close(self, num(data, "peak_g"), 6.7570058, "baseline peak", rel=1e-7, abs_tol=0.0)
        self.assertIn("100x tighter tolerance", data["assumptions"])
        self.assertNotIn("10x tighter", data["assumptions"])
        convergence = num(data, "convergence_peak_g_rel")
        self.assertGreater(convergence, 1.5e-4)
        self.assertLess(convergence, 2.5e-4)

    def test_bank_schedule_json_and_native_list(self) -> None:
        schedule = (
            '[{"t_s":0,"bank_deg":0},{"t_s":60,"bank_deg":0},{"t_s":61,"bank_deg":90}]'
        )
        data = run(
            self.program,
            [
                "--speed",
                "11032.1",
                "--gamma",
                "0.113097",
                "--altitude",
                "121920",
                "--lod",
                "0.30076",
                "--beta",
                "355.70326",
                "--bank-schedule",
                schedule,
            ],
        )
        assert_close(self, num(data, "peak_g"), 14.7008, "banked peak", rel=1e-4, abs_tol=0.0)
        lifting = self._module()
        native = lifting.simulate(
            11032.1,
            0.113097,
            121920.0,
            0.30076,
            355.70326,
            None,
            None,
            None,
            None,
            [
                {"t_s": 0, "bank_deg": 0},
                {"t_s": 60, "bank_deg": 0},
                {"t_s": 61, "bank_deg": 90},
            ],
            lifting.R0_EARTH,
            lifting.MU_EARTH,
            "exponential",
            None,
            None,
            None,
            0.0,
            3000.0,
            None,
            None,
            None,
            None,
            1.0e-6,
            None,
            converge=False,
        )
        assert_close(self, float(native["peak_g"]), num(data, "peak_g"), "native list matches JSON", rel=1e-8, abs_tol=0.0)

    def test_glide_without_a_measurable_peak_change_prints_na(self) -> None:
        # On the lift balance at L/D 1.5 the 100x rerun reproduces the peak
        # exactly, so the old print was 0.
        lifting = self._module()
        glide = load_module(
            script("skills", "THERM - EquilibriumGlideEntry", "equilibrium_glide_entry.py")
        )
        speed = 7000.0
        beta = 200.0
        lod = 1.5
        circular = math.sqrt(G0 * lifting.R0_EARTH)
        rho = glide.heating_density(beta, G0, speed, circular, lod)
        altitude = lifting.DEFAULT_Z_REF + lifting.DEFAULT_H * math.log(
            lifting.DEFAULT_RHO_REF / rho
        )
        data = run(
            self.program,
            [
                "--speed",
                str(speed),
                "--gamma",
                "0",
                "--altitude",
                f"{altitude:.8g}",
                "--lod",
                str(lod),
                "--beta",
                str(beta),
                "--bank-deg",
                "0",
                "--end-altitude",
                "20000",
                "--max-time-s",
                "2000",
            ],
        )
        self.assertTrue(data["convergence_peak_g_rel"].startswith("n/a"), data["convergence_peak_g_rel"])
        self.assertIn("same peak", data["convergence_peak_g_rel"])

    def test_speed_floor_returns_the_peak(self) -> None:
        data = run(
            self.program,
            [
                "--speed",
                "7000",
                "--gamma",
                "0.5235987755982988",
                "--altitude",
                "121920",
                "--lod",
                "0",
                "--beta",
                "355.70326",
                "--bank-deg",
                "0",
                "--radius",
                "1e12",
                "--mu",
                "1e-6",
            ],
        )
        self.assertEqual(data["end_reason"], "speed_floor")
        self.assertGreater(num(data, "peak_g"), 1.0)

    def test_heading_air_is_printed_for_inertial_north(self) -> None:
        lifting = self._module()
        speed = 7800.0
        gamma = 0.05
        altitude = 85000.0
        data = run(
            self.program,
            [
                "--speed",
                str(speed),
                "--gamma",
                str(gamma),
                "--altitude",
                str(altitude),
                "--lod",
                "0",
                "--beta",
                "500",
                "--bank-deg",
                "0",
                "--latitude-deg",
                "0",
                "--heading-deg",
                "0",
                "--max-time-s",
                "2",
                "--dt",
                "0.5",
            ],
        )
        self.assertIn("inertial heading from north", data["assumptions"])
        radius = lifting.R0_EARTH + altitude
        horizontal = speed * math.cos(gamma)
        east = -lifting.OMEGA_EARTH * radius
        expected = math.degrees(math.atan2(east, horizontal))
        assert_close(self, num(data, "heading_air_deg"), expected, "air-relative heading", rel=1e-6, abs_tol=0.0)
        self.assertNotEqual(data["heading_deg"], data["heading_air_deg"])


def _equatorial_cartesian_peak_rk4(
    lifting,
    speed: float,
    gamma: float,
    altitude: float,
    lod: float,
    beta: float,
    bank_deg: float,
    end_altitude: float,
    dt: float,
) -> float:
    """Inertial equatorial RK4. Drag and lift act on the air-relative velocity."""
    radius_planet = lifting.R0_EARTH
    mu = lifting.MU_EARTH
    omega = lifting.OMEGA_EARTH
    radius0 = radius_planet + altitude
    state = (radius0, 0.0, -speed * math.sin(gamma), speed * math.cos(gamma))
    bank = math.radians(bank_deg)
    peak = 0.0
    t = 0.0
    seen_below = False

    def rates(y: tuple[float, float, float, float]) -> tuple[tuple[float, float, float, float], float, float]:
        px, py, pvx, pvy = y
        radius = math.hypot(px, py)
        height = radius - radius_planet
        rho = lifting.exponential_density(
            height, lifting.DEFAULT_RHO_REF, lifting.DEFAULT_Z_REF, lifting.DEFAULT_H
        )
        vrx = pvx + omega * py
        vry = pvy - omega * px
        vrel = math.hypot(vrx, vry)
        drag = rho * vrel * vrel / (2.0 * beta)
        lift = lod * drag
        inv = 1.0 / vrel
        load = drag * math.sqrt(1.0 + lod * lod) / lifting.G0
        lx, ly = vry * inv, -vrx * inv
        ax = -mu * px / radius**3 - drag * vrx * inv + lift * math.cos(bank) * lx
        ay = -mu * py / radius**3 - drag * vry * inv + lift * math.cos(bank) * ly
        return (pvx, pvy, ax, ay), load, height

    def rk4(y: tuple[float, float, float, float]) -> tuple[tuple[float, float, float, float], float, float]:
        k1, load, height = rates(y)
        y2 = tuple(y[i] + 0.5 * dt * k1[i] for i in range(4))
        k2 = rates(y2)[0]
        y3 = tuple(y[i] + 0.5 * dt * k2[i] for i in range(4))
        k3 = rates(y3)[0]
        y4 = tuple(y[i] + dt * k3[i] for i in range(4))
        k4 = rates(y4)[0]
        nxt = tuple(y[i] + dt * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) / 6.0 for i in range(4))
        return nxt, load, height

    while t < 400.0:
        state, load, height = rk4(state)
        t += dt
        peak = max(peak, load)
        if height < altitude:
            seen_below = True
        if height <= end_altitude or (seen_below and height >= altitude and t > dt):
            break
    return peak


if __name__ == "__main__":
    unittest.main()
