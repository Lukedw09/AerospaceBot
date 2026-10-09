"""Independent checks for the uncommitted skills and design labs.

Expected values are derived here from closed-form gas dynamics, two-body
propagation, Mohr's circle, the Goodman line, and Bode arithmetic. They are
not copied from each program's --check.
"""

from __future__ import annotations

import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G0 = 9.80665
R0 = 6.3742e6
MU = G0 * R0 * R0


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


def assert_close(
    test: unittest.TestCase,
    actual: float,
    expected: float,
    msg: str,
    rel: float = 1e-6,
    abs_tol: float = 1e-8,
) -> None:
    test.assertTrue(
        abs(actual - expected) <= abs_tol + rel * abs(expected),
        f"{msg}: got {actual}, expected {expected}",
    )


def png_ok(data: dict[str, str], key: str = "graph") -> None:
    path = Path(data[key])
    if not path.is_file() or not path.read_bytes().startswith(b"\x89PNG"):
        raise AssertionError(f"PNG missing at {path}")


def propagate(
    position: tuple[float, float, float],
    velocity: tuple[float, float, float],
    tof: float,
    mu: float,
    steps: int = 40000,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Two-body RK4. Independent of the Lambert solver."""

    def accel(pos: tuple[float, float, float]) -> tuple[float, float, float]:
        radius = math.sqrt(pos[0] ** 2 + pos[1] ** 2 + pos[2] ** 2)
        scale = -mu / radius**3
        return (scale * pos[0], scale * pos[1], scale * pos[2])

    def deriv(state: tuple[float, ...]) -> tuple[float, ...]:
        acc = accel((state[0], state[1], state[2]))
        return (state[3], state[4], state[5], acc[0], acc[1], acc[2])

    step = tof / steps
    state = position + velocity
    for _ in range(steps):
        k1 = deriv(state)
        s2 = tuple(state[i] + 0.5 * step * k1[i] for i in range(6))
        k2 = deriv(s2)
        s3 = tuple(state[i] + 0.5 * step * k2[i] for i in range(6))
        k3 = deriv(s3)
        s4 = tuple(state[i] + step * k3[i] for i in range(6))
        k4 = deriv(s4)
        state = tuple(
            state[i] + (step / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
            for i in range(6)
        )
    return (state[0], state[1], state[2]), (state[3], state[4], state[5])


def area_mach(mach: float, gamma: float = 1.4) -> float:
    gp = gamma + 1.0
    gm = gamma - 1.0
    return (
        (1.0 / mach)
        * ((2.0 / gp) * (1.0 + 0.5 * gm * mach * mach)) ** (gp / (2.0 * gm))
    )


def fanno_oracle(mach: float, gamma: float = 1.4) -> dict[str, float]:
    temperature = ((gamma + 1.0) / 2.0) / (1.0 + 0.5 * (gamma - 1.0) * mach * mach)
    pressure = math.sqrt(temperature) / mach
    density = 1.0 / (mach * math.sqrt(temperature))
    velocity = mach * math.sqrt(temperature)
    base = (2.0 + (gamma - 1.0) * mach * mach) / (gamma + 1.0)
    total = (1.0 / mach) * base ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))
    argument = ((gamma + 1.0) * mach * mach) / (2.0 + (gamma - 1.0) * mach * mach)
    friction = (1.0 - mach * mach) / (gamma * mach * mach) + (
        (gamma + 1.0) / (2.0 * gamma)
    ) * math.log(argument)
    return {
        "T": temperature,
        "p": pressure,
        "rho": density,
        "V": velocity,
        "pt": total,
        "fld": friction,
    }


def rayleigh_tt(mach: float, gamma: float = 1.4) -> float:
    return (
        2.0
        * (gamma + 1.0)
        * mach
        * mach
        * (1.0 + 0.5 * (gamma - 1.0) * mach * mach)
        / (1.0 + gamma * mach * mach) ** 2
    )


def mean_line_quadrature(m_camber: float, p_camber: float, n: int = 20001) -> dict[str, float]:
    """Fourier integrals of the two-parabola NACA mean-line slope."""

    def slope(theta: float) -> float:
        x_over_c = 0.5 * (1.0 - math.cos(theta))
        if x_over_c <= p_camber:
            return (2.0 * m_camber / p_camber**2) * (p_camber - x_over_c)
        return (2.0 * m_camber / (1.0 - p_camber) ** 2) * (p_camber - x_over_c)

    def trap(weight) -> float:
        total = 0.5 * (weight(0.0) + weight(math.pi))
        d_theta = math.pi / (n - 1)
        for index in range(1, n - 1):
            theta = d_theta * index
            total += weight(theta)
        return total * d_theta

    a0 = trap(slope) / math.pi
    a1 = 2.0 * trap(lambda theta: slope(theta) * math.cos(theta)) / math.pi
    a2 = 2.0 * trap(lambda theta: slope(theta) * math.cos(2.0 * theta)) / math.pi
    return {"alpha_L0": a0 - 0.5 * a1, "A1": a1, "A2": a2, "cm": math.pi / 4.0 * (a2 - a1)}


def bode_margins(num: list[float], den: list[float]) -> tuple[float, float, float, float]:
    """Independent log sweep. Returns wc, phase margin deg, wpc, gain margin dB."""

    def horner(coeffs: list[float], omega: float) -> complex:
        value = 0j
        for coeff in coeffs:
            value = value * (1j * omega) + coeff
        return value

    def response(omega: float) -> complex:
        return horner(num, omega) / horner(den, omega)

    phase = 0.0
    previous = None
    rows: list[tuple[float, float, float]] = []
    grid = 4000
    for index in range(grid):
        omega = 1.0e-3 * (1.0e7) ** (index / (grid - 1))
        value = response(omega)
        angle = math.atan2(value.imag, value.real)
        if previous is None:
            phase = angle
        else:
            phase += (angle - previous + math.pi) % (2.0 * math.pi) - math.pi
        previous = angle
        rows.append((omega, abs(value), phase))

    def crossing(kind: str) -> float | None:
        target = 1.0 if kind == "gain" else -math.pi
        for left, right in zip(rows, rows[1:]):
            y0 = left[1] if kind == "gain" else left[2]
            y1 = right[1] if kind == "gain" else right[2]
            if (y0 - target) == 0.0:
                return left[0]
            if (y0 - target) * (y1 - target) < 0.0:
                lo, hi = left[0], right[0]
                for _ in range(50):
                    mid = math.sqrt(lo * hi)
                    value = response(mid)
                    sample = abs(value) if kind == "gain" else math.atan2(value.imag, value.real)
                    # Keep the bracket's unwrapped side for the phase search.
                    if kind == "phase":
                        sample = left[2] + (sample - math.atan2(response(left[0]).imag, response(left[0]).real) + math.pi) % (
                            2.0 * math.pi
                        ) - math.pi
                    probe = sample
                    if (y0 - target) * (probe - target) <= 0.0:
                        hi = mid
                    else:
                        lo = mid
                        y0 = probe
                return math.sqrt(lo * hi)
        return None

    wc = crossing("gain")
    wpc = crossing("phase")
    if wc is None or wpc is None:
        raise AssertionError(f"crossover missing wc={wc} wpc={wpc}")
    phase_at = None
    for row in rows:
        if row[0] <= wc:
            phase_at = row[2]
    assert phase_at is not None
    # Refine phase at wc from the nearest grid phase plus a principal step.
    value = response(wc)
    nearest = min(rows, key=lambda row: abs(math.log(row[0] / wc)))
    principal = math.atan2(value.imag, value.real)
    nearest_principal = math.atan2(response(nearest[0]).imag, response(nearest[0]).real)
    phase_wc = nearest[2] + (principal - nearest_principal + math.pi) % (2.0 * math.pi) - math.pi
    gain_margin = -20.0 * math.log10(abs(response(wpc)))
    return wc, 180.0 + math.degrees(phase_wc), wpc, gain_margin


class Attitude(unittest.TestCase):
    program = script("skills", "ADCS - AttitudeKinematics", "attitude_kinematics.py")

    def test_yaw_90_and_quaternion_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "att.png")
            data = run(
                self.program,
                ["--mode", "euler_to_dcm", "--roll", "0", "--pitch", "0", "--yaw", str(math.pi / 2), "--out", out],
            )
            png_ok(data)
            assert_close(self, num(data, "c12"), 1.0, "c12")
            assert_close(self, num(data, "c21"), -1.0, "c21")
            assert_close(self, num(data, "c33"), 1.0, "c33")
            assert_close(self, num(data, "c11"), 0.0, "c11", abs_tol=1e-12)
            quat = run(
                self.program,
                [
                    "--mode",
                    "quat_to_dcm",
                    "--q0",
                    str(math.sqrt(0.5)),
                    "--q1",
                    "0",
                    "--q2",
                    "0",
                    "--q3",
                    str(math.sqrt(0.5)),
                    "--out",
                    out,
                ],
            )
            assert_close(self, num(quat, "c12"), 1.0, "quaternion yaw c12")
            rates = run(
                self.program,
                [
                    "--mode",
                    "quat_rates",
                    "--wx",
                    "0",
                    "--wy",
                    "0",
                    "--wz",
                    "1",
                    "--q0",
                    "1",
                    "--q1",
                    "0",
                    "--q2",
                    "0",
                    "--q3",
                    "0",
                    "--out",
                    out,
                ],
            )
            assert_close(self, num(rates, "q3_dot"), 0.5, "yaw rate")
            assert_close(self, num(rates, "q0_dot"), 0.0, "scalar rate", abs_tol=1e-12)

    def test_gimbal_lock_and_bad_quaternion(self) -> None:
        run_fail(
            self.program,
            ["--mode", "euler_rates", "--wx", "0", "--wy", "0", "--wz", "0", "--roll", "0", "--pitch", str(math.pi / 2), "--yaw", "0"],
        )
        run_fail(self.program, ["--mode", "quat_to_dcm", "--q0", "2", "--q1", "0", "--q2", "0", "--q3", "0"])


class FannoRayleigh(unittest.TestCase):
    program = script("skills", "AERO - FannoAndRayleighFlow", "fanno_and_rayleigh_flow.py")

    def test_mach_two_table(self) -> None:
        oracle = fanno_oracle(2.0)
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "fanno.png")
            data = run(self.program, ["--fanno", "--mach", "2", "--out", out])
            png_ok(data)
            self.assertEqual(data["gamma_source"], "default")
            assert_close(self, num(data, "T_over_Tstar"), 2.0 / 3.0, "T/T*")
            assert_close(self, num(data, "p_over_pstar"), oracle["p"], "p/p*")
            assert_close(self, num(data, "pt_over_ptstar"), 1.6875, "pt/pt*")
            assert_close(self, num(data, "four_f_Lmax_over_D"), oracle["fld"], "4fL*")
            self.assertEqual(data["choked"], "no")
            ray = run(self.program, ["--rayleigh", "--mach", "2", "--out", out])
            assert_close(self, num(ray, "p_over_pstar"), 4.0 / 11.0, "Rayleigh p")
            assert_close(self, num(ray, "V_over_Vstar"), 16.0 / 11.0, "Rayleigh V")
            assert_close(self, num(ray, "Tt_over_Ttstar"), rayleigh_tt(2.0), "Rayleigh Tt")

    def test_exit_mach_and_choke(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "fanno.png")
            sonic = run(self.program, ["--fanno", "--mach", "0.5", "--fld", "0", "--out", out])
            assert_close(self, num(sonic, "exit_mach"), 0.5, "zero length")
            remain = num(sonic, "four_f_Lmax_over_D")
            half = run(self.program, ["--fanno", "--mach", "0.5", "--fld", str(0.5 * remain), "--out", out])
            exit_mach = num(half, "exit_mach")
            self.assertGreater(exit_mach, 0.5)
            self.assertLess(exit_mach, 1.0)
            left = fanno_oracle(0.5)["fld"] - fanno_oracle(exit_mach)["fld"]
            assert_close(self, left, 0.5 * remain, "friction length", rel=1e-5)
            choked = run(
                self.program,
                ["--fanno", "--mach", "0.5", "--fld", str(remain + 0.2), "--out", out],
            )
            self.assertEqual(choked["choked_by_length"], "yes")
            self.assertNotIn("exit_mach", choked)
        run_fail(self.program, ["--fanno", "--rayleigh", "--mach", "2"])
        run_fail(self.program, ["--mach", "2"])


class FlatPlate(unittest.TestCase):
    program = script("skills", "AERO - FlatPlateBoundaryLayer", "flat_plate_boundary_layer.py")

    def test_blasius_and_seventh_power(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "bl.png")
            lam = run(
                self.program,
                ["--law", "laminar", "--rho", "1.2", "--V", "50", "--L", "1", "--mu", "1.8e-5", "--span", "0.4", "--out", out],
            )
            png_ok(data := lam)
            re = 1.2 * 50 * 1.0 / 1.8e-5
            assert_close(self, num(lam, "Re_L"), re, "Re")
            assert_close(self, num(lam, "Cf"), 1.328 / math.sqrt(re), "Cf")
            assert_close(self, num(lam, "cf"), 0.664 / math.sqrt(re), "cf")
            assert_close(self, num(lam, "delta_over_L"), 5.0 / math.sqrt(re), "delta")
            drag = (1.328 / math.sqrt(re)) * (0.5 * 1.2 * 50 * 50) * 0.4
            assert_close(self, num(lam, "Df_N"), drag, "drag")
            turb = run(self.program, ["--law", "turbulent", "--re", "1e6", "--out", out])
            assert_close(self, num(turb, "Cf"), 0.074 / 1e6**0.2, "turbulent Cf")
            assert_close(self, num(turb, "cf"), 0.0592 / 1e6**0.2, "turbulent cf")
            self.assertNotIn("delta_over_L", turb)
        _ = data
        run_fail(self.program, ["--law", "laminar", "--re", "-1"])


class LateralAndTrim(unittest.TestCase):
    lateral = script(
        "skills", "AERO - LateralDirectionalStaticStability", "lateral_directional_static_stability.py"
    )
    trim = script("skills", "AERO - LongitudinalTrim", "longitudinal_trim.py")

    def test_dihedral_and_weathercock(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "lat.png")
            data = run(
                self.lateral,
                [
                    "--span", "10", "--area", "16", "--cl-alpha", "5",
                    "--sv", "2", "--lv", "4", "--av", "3", "--gamma", "0.1",
                    "--taper", "0.5", "--out", out,
                ],
            )
            png_ok(data)
            volume = 2.0 * 4.0 / (16.0 * 10.0)
            assert_close(self, num(data, "Vv"), volume, "Vv")
            assert_close(self, num(data, "Cn_beta_per_rad"), 3.0 * volume, "Cn")
            cl_beta = -5.0 * 0.1 * (1.0 + 1.0) / (6.0 * 1.5)
            assert_close(self, num(data, "Cl_beta_per_rad"), cl_beta, "Cl")
            self.assertEqual(data["weathercock"], "stable")
            self.assertEqual(data["effective_dihedral"], "stable")
            self.assertEqual(data["eta_source"], "default_unity")

    def test_trim_elevator(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "trim.png")
            data = run(
                self.trim,
                [
                    "--a", "5", "--cm0", "0.05", "--cm-de", "-1.2",
                    "--q", "2000", "--S", "20", "--W", "8000", "--kn", "0.15",
                    "--de-max", "0.4", "--out", out,
                ],
            )
            cl = 8000.0 / (2000.0 * 20.0)
            alpha = cl / 5.0
            cm_alpha = -5.0 * 0.15
            de = -(0.05 + cm_alpha * alpha) / -1.2
            assert_close(self, num(data, "CL"), cl, "CL")
            assert_close(self, num(data, "alpha_trim_rad"), alpha, "alpha")
            assert_close(self, num(data, "de_trim_rad"), de, "elevator")
            assert_close(self, num(data, "residual_cm"), 0.0, "residual", abs_tol=1e-12)
            self.assertEqual(data["elevator_status"], "within_limit")
        run_fail(self.trim, ["--a", "5", "--cm0", "0", "--cm-de", "0", "--CL", "0.4", "--kn", "0.1"])


class ThinAirfoil(unittest.TestCase):
    program = script("skills", "AERO - ThinAirfoilTheory", "thin_airfoil_theory.py")

    def test_quadrature_and_flat_plate(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "thin.png")
            flat = run(self.program, ["--alpha", str(math.radians(5.0)), "--out", out])
            png_ok(flat)
            assert_close(self, num(flat, "cl"), 2.0 * math.pi * math.radians(5.0), "flat plate")
            quad = mean_line_quadrature(0.02, 0.4)
            line = run(self.program, ["--m", "0.02", "--p", "0.4", "--alpha", "0.05", "--out", out])
            assert_close(self, num(line, "alpha_L0"), quad["alpha_L0"], "alpha_L0", rel=1e-4, abs_tol=1e-5)
            assert_close(self, num(line, "A1"), quad["A1"], "A1", rel=1e-4, abs_tol=1e-5)
            assert_close(self, num(line, "A2"), quad["A2"], "A2", rel=1e-4, abs_tol=1e-5)
            assert_close(self, num(line, "cm_c4"), quad["cm"], "cm", rel=1e-4, abs_tol=1e-5)
            assert_close(
                self,
                num(line, "cl"),
                2.0 * math.pi * (0.05 - quad["alpha_L0"]),
                "cambered cl",
                rel=1e-4,
            )
            # Circular arc: alpha_L0 = -2 m.
            arc = run(self.program, ["--m", "0.02", "--p", "0.5", "--out", out])
            assert_close(self, num(arc, "alpha_L0"), -0.04, "circular arc")


class WindTunnel(unittest.TestCase):
    program = script("skills", "AERO - WindTunnelSimilarity", "wind_tunnel_similarity.py")

    def test_force_and_moment_scale(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "wt.png")
            data = run(
                self.program,
                [
                    "--L-m", "0.2", "--L-f", "2",
                    "--V-m", "80", "--V-f", "80",
                    "--rho-m", "1.5", "--rho-f", "1.2",
                    "--mu-m", "1.8e-5", "--mu-f", "1.8e-5",
                    "--a-m", "340", "--a-f", "340",
                    "--force-m", "12", "--moment-m", "0.4",
                    "--S-m", "0.05", "--S-f", "5",
                    "--c-m", "0.2", "--c-f", "2",
                    "--out", out,
                ],
            )
            png_ok(data)
            q_m = 0.5 * 1.5 * 80 * 80
            q_f = 0.5 * 1.2 * 80 * 80
            assert_close(self, num(data, "force_f_N"), 12.0 * (q_f * 5.0) / (q_m * 0.05), "force")
            assert_close(
                self,
                num(data, "moment_f_Nm"),
                0.4 * (q_f * 5.0 * 2.0) / (q_m * 0.05 * 0.2),
                "moment",
            )
            re_m = 1.5 * 80 * 0.2 / 1.8e-5
            re_f = 1.2 * 80 * 2.0 / 1.8e-5
            assert_close(self, num(data, "Re_mismatch"), abs(re_m - re_f) / re_f, "Re mismatch")


class ControlMargins(unittest.TestCase):
    program = script("skills", "GNC - ClassicalControlMargins", "classical_control_margins.py")

    def test_third_order_plant(self) -> None:
        # L(s) = 1 / (s(s+1)(s+2)) = 1 / (s^3 + 3 s^2 + 2 s)
        wc, pm, wpc, gm = bode_margins([1.0], [1.0, 3.0, 2.0, 0.0])
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "bode.png")
            data = run(
                self.program,
                ["--num", "1", "--den", "1", "3", "2", "0", "--out", out],
            )
            png_ok(data)
            assert_close(self, num(data, "wc"), wc, "wc", rel=2e-3)
            assert_close(self, num(data, "phase_margin_deg"), pm, "pm", rel=2e-3, abs_tol=0.05)
            assert_close(self, num(data, "wpc"), wpc, "wpc", rel=2e-3)
            assert_close(self, num(data, "gain_margin_db"), gm, "gm", rel=2e-3, abs_tol=0.05)
            self.assertEqual(data["stable"], "yes")
        run_fail(self.program, ["--num", "1"])


class Structures(unittest.TestCase):
    mohr = script("skills", "STRUCT - CombinedStressMohr", "combined_stress_mohr.py")
    fatigue = script("skills", "STRUCT - FatigueGoodman", "fatigue_goodman.py")

    def test_principals_and_shaft(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "mohr.png")
            sx, tau = 80.0e6, 30.0e6
            data = run(self.mohr, ["--sigma", str(sx), "--tau", str(tau), "--out", out])
            png_ok(data)
            center = 0.5 * sx
            radius = math.hypot(0.5 * sx, tau)
            assert_close(self, num(data, "sigma1_Pa"), center + radius, "sigma1")
            assert_close(self, num(data, "sigma2_Pa"), center - radius, "sigma2")
            assert_close(self, num(data, "tau_max_Pa"), radius, "tau")
            self.assertEqual(data["sigma_y_Pa"], "0")
            radius_m = 0.02
            moment = 80.0
            torque = 40.0
            section = math.pi * radius_m**3 / 4.0
            polar = math.pi * radius_m**4 / 2.0
            sigma = moment / section
            shear = torque * radius_m / polar
            loaded = run(
                self.mohr,
                [
                    "--moment", str(moment),
                    "--section-modulus", str(section),
                    "--torque", str(torque),
                    "--radius", str(radius_m),
                    "--out", out,
                ],
            )
            assert_close(self, num(loaded, "sigma_x_Pa"), sigma, "bending")
            assert_close(self, num(loaded, "tau_xy_Pa"), shear, "torsion")
        run_fail(self.mohr, ["--sigma", "1", "--tau", "1", "--moment", "2", "--torque", "2", "--radius", "0.01"])

    def test_goodman_and_soderberg(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "fat.png")
            data = run(
                self.fatigue,
                ["--criterion", "goodman", "--sigma-a", "80e6", "--sigma-m", "100e6", "--se", "200e6", "--sut", "500e6", "--out", out],
            )
            png_ok(data)
            expected = 1.0 / (80e6 / 200e6 + 100e6 / 500e6)
            assert_close(self, num(data, "n"), expected, "goodman n")
            assert_close(self, num(data, "sa_allow_Pa"), 200e6 * (1.0 - 100e6 / 500e6), "allowable")
            self.assertEqual(data["status"], "pass")
            sod = run(
                self.fatigue,
                ["--criterion", "soderberg", "--sigma-a", "80e6", "--sigma-m", "100e6", "--se", "200e6", "--sy", "300e6", "--out", out],
            )
            assert_close(self, num(sod, "n"), 1.0 / (0.4 + 100e6 / 300e6), "soderberg")
            past = run(
                self.fatigue,
                ["--criterion", "goodman", "--sigma-a", "10e6", "--sigma-m", "500e6", "--se", "200e6", "--sut", "500e6", "--out", out],
            )
            self.assertEqual(past["status"], "fail")
        run_fail(self.fatigue, ["--criterion", "goodman", "--sigma-a", "-1", "--sigma-m", "0", "--se", "1", "--sut", "2"])


class GravityAndLambert(unittest.TestCase):
    gravity = script("skills", "ASTRO - GravityAssistFlyby", "gravity_assist_flyby.py")
    lambert = script("skills", "ASTRO - LambertTransfer", "lambert_transfer.py")
    hohmann = script("skills", "ASTRO - HohmannTransfer", "hohmann_transfer.py")

    def test_sixty_degree_turn_pumps_energy(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "ga.png")
            data = run(
                self.gravity,
                [
                    "--mu", "1", "--rp", "1", "--vinf", "1",
                    "--ux", "1", "--uy", "0", "--vp-x", "3", "--vp-y", "0",
                    "--turn", "left", "--out", out,
                ],
            )
            png_ok(data)
            assert_close(self, num(data, "eccentricity"), 2.0, "e")
            assert_close(self, num(data, "delta_rad"), math.pi / 3.0, "delta")
            assert_close(self, num(data, "vinf_out_x_m_s"), 0.5, "vout x")
            assert_close(self, num(data, "vinf_out_y_m_s"), math.sin(math.pi / 3.0), "vout y")
            vin = 4.0
            vout = math.hypot(3.5, math.sin(math.pi / 3.0))
            assert_close(self, num(data, "ke_change_J_kg"), 0.5 * (vout * vout - vin * vin), "energy")
            assert_close(self, num(data, "dv_helio_m_s"), 1.0, "turn chord")

    def test_lambert_hits_the_target(self) -> None:
        mu = MU
        r_peri = 7000.0e3
        r_apo = 14000.0e3
        semimajor = 0.5 * (r_peri + r_apo)
        tof = math.pi * math.sqrt(semimajor**3 / mu)
        v_peri = math.sqrt(mu * (2.0 / r_peri - 1.0 / semimajor))
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "lam.png")
            data = run(
                self.lambert,
                [
                    "--r1x", str(r_peri), "--r1y", "0", "--r1z", "0",
                    "--r2x", str(-r_apo), "--r2y", "0", "--r2z", "0",
                    "--tof", str(tof), "--mu", str(mu), "--way", "short",
                    "--out", out,
                ],
            )
            png_ok(data)
            speed = math.sqrt(num(data, "v1x_m_s") ** 2 + num(data, "v1y_m_s") ** 2 + num(data, "v1z_m_s") ** 2)
            assert_close(self, speed, v_peri, "Hohmann periapsis speed", rel=1e-5)
            final, vend = propagate(
                (r_peri, 0.0, 0.0),
                (num(data, "v1x_m_s"), num(data, "v1y_m_s"), num(data, "v1z_m_s")),
                tof,
                mu,
            )
            assert_close(self, final[0], -r_apo, "arrival x", rel=1e-5, abs_tol=1.0)
            assert_close(self, final[1], 0.0, "arrival y", abs_tol=20.0)
            assert_close(self, final[2], 0.0, "arrival z", abs_tol=20.0)
            reported = math.sqrt(num(data, "v2x_m_s") ** 2 + num(data, "v2y_m_s") ** 2 + num(data, "v2z_m_s") ** 2)
            arrived = math.sqrt(vend[0] ** 2 + vend[1] ** 2 + vend[2] ** 2)
            assert_close(self, arrived, reported, "arrival speed", rel=1e-4)
            # Non-degenerate quarter orbit, mu = 1.
            quarter = math.pi / 2.0
            q = run(
                self.lambert,
                [
                    "--r1x", "1", "--r1y", "0", "--r1z", "0",
                    "--r2x", "0", "--r2y", "1", "--r2z", "0",
                    "--tof", str(quarter), "--mu", "1", "--way", "short", "--out", out,
                ],
            )
            end, _vel = propagate((1.0, 0.0, 0.0), (num(q, "v1x_m_s"), num(q, "v1y_m_s"), num(q, "v1z_m_s")), quarter, 1.0)
            assert_close(self, end[0], 0.0, "quarter x", abs_tol=1e-4)
            assert_close(self, end[1], 1.0, "quarter y", rel=1e-4)
            hoh = run(self.hohmann, ["--r1", str(r_peri), "--r2", str(r_apo), "--R0", str(R0), "--out", out])
            assert_close(self, num(hoh, "dv_m_s"), num(hoh, "dv_depart_m_s") + num(hoh, "dv_arrive_m_s"), "hohmann sum")
            assert_close(self, num(hoh, "v_depart_transfer_m_s"), v_peri, "vis-viva", rel=1e-6)


class Labs(unittest.TestCase):
    def _bake(self, program: Path, args: list[str]) -> dict[str, str]:
        data = run(program, args)
        png_ok(data)
        viewer = Path(data["viewer"])
        html = viewer.read_text(encoding="utf-8")
        self.assertTrue(viewer.is_file() and viewer.stat().st_size > 1000, data["viewer"])
        self.assertNotIn("__SEED_JSON__", html)
        self.assertNotIn("__LAB_JS__", html)
        self.assertNotIn("__THREE_SOURCE__", html)
        self.assertNotIn("<script src=", html.lower())
        return data

    def test_compressible_matches_shock_and_area(self) -> None:
        lab = script("skills", "AERO - CompressibleFlowDesignLab", "compressible_flow_lab.py")
        shock = script("skills", "AERO - NormalShock", "normal_shock.py")
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "lab.png")
            baked = self._bake(lab, ["--mode", "normal", "--mach", "2", "--out", out])
            reference = run(shock, ["--mach", "2", "--out", str(Path(folder) / "shock.png")])
            assert_close(self, num(baked, "M2"), num(reference, "M2"), "M2")
            assert_close(self, num(baked, "p2_over_p1"), 4.5, "p2/p1")
            assert_close(self, num(baked, "p2_over_p1"), num(reference, "p2_over_p1"), "shock pressure")
            assert_close(self, num(baked, "pt2_over_pt1"), num(reference, "pt2_over_pt1"), "pt")
            fanno = self._bake(lab, ["--mode", "fanno", "--mach", "2", "--out", out])
            assert_close(self, num(fanno, "T_over_Tstar"), 2.0 / 3.0, "lab Fanno")
            self.assertIn("stream function", baked["assumptions"].lower() + fanno.get("assumptions", "").lower())

    def test_wing_matches_lifting_line(self) -> None:
        lab = script("skills", "AERO - WingAirfoilDesignLab", "wing_airfoil_lab.py")
        wing = script("skills", "AERO - FiniteWingLiftCurve", "finite_wing_lift_curve.py")
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "wing.png")
            data = self._bake(
                lab,
                ["--naca", "0012", "--span", "12", "--root", "1.2", "--tip", "0.6", "--e", "0.85", "--alpha", "0.08", "--out", out],
            )
            area = 0.5 * (1.2 + 0.6) * 12.0
            aspect = 12.0**2 / area
            assert_close(self, num(data, "S_m2"), area, "area")
            assert_close(self, num(data, "AR"), aspect, "AR")
            a0 = num(data, "a0_eff_per_rad")
            expected = a0 / (1.0 + a0 / (math.pi * aspect * 0.85))
            assert_close(self, num(data, "a_per_rad"), expected, "slope")
            reference = run(
                wing,
                [
                    "--a0", str(a0),
                    "--alpha-l0", data["alpha_L0_rad"],
                    "--clmax", data["CLmax"],
                    "--ar", str(aspect),
                    "--e", "0.85",
                    "--out", str(Path(folder) / "curve.png"),
                ],
            )
            assert_close(self, num(data, "a_per_rad"), num(reference, "a_per_rad"), "finite wing")
            cl = expected * (0.08 - num(data, "alpha_L0_rad"))
            if data["stalled"] == "no":
                assert_close(self, num(data, "CL"), cl, "CL")
                assert_close(self, num(data, "CDi"), cl * cl / (math.pi * aspect * 0.85), "CDi")

    def test_orbit_lab_matches_vis_viva(self) -> None:
        lab = script("skills", "ASTRO - OrbitDesignLab", "orbit_design_lab.py")
        with tempfile.TemporaryDirectory() as folder:
            out = str(Path(folder) / "orbit.png")
            r1 = R0 + 400000.0
            r2 = R0 + 800000.0
            data = self._bake(lab, ["--r1", str(r1), "--r2", str(r2), "--strategy", "hohmann", "--out", out])
            a_transfer = 0.5 * (r1 + r2)
            dv1 = math.sqrt(MU * (2.0 / r1 - 1.0 / a_transfer)) - math.sqrt(MU / r1)
            dv2 = math.sqrt(MU / r2) - math.sqrt(MU * (2.0 / r2 - 1.0 / a_transfer))
            tof = math.pi * math.sqrt(a_transfer**3 / MU)
            assert_close(self, num(data, "hohmann_dv_m_s"), dv1 + dv2, "hohmann dv", rel=1e-6)
            assert_close(self, num(data, "hohmann_tof_s"), tof, "tof", rel=1e-6)
            self.assertEqual(data["strategy"], "hohmann")
            self.assertIn("gravity loss is 0", data["raise_note"])
            html = Path(data["viewer"]).read_text(encoding="utf-8")
            self.assertIn("THREE", html)

    def test_rocket_labs_bake_and_scale(self) -> None:
        feed = script("skills", "ROCKET - FeedTankDesignLab", "feed_tank_lab.py")
        nozzle = script("skills", "ROCKET - NozzleChamberDesignLab", "nozzle_chamber_lab.py")
        grain = script("skills", "ROCKET - SolidMotorGrainLab", "solid_motor_grain_lab.py")
        ascent = script("skills", "ROCKET - StageAscentDesignLab", "stage_ascent_lab.py")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self._bake(feed, ["--out", str(root / "feed.png")])
            nozzle_data = self._bake(nozzle, ["--out", str(root / "nozzle.png")])
            self.assertAlmostEqual(area_mach(num(nozzle_data, "Me"), num(nozzle_data, "gamma")), num(nozzle_data, "epsilon"), places=4)
            mdot = num(nozzle_data, "mdot_kg_s")
            at = num(nozzle_data, "At_m2")
            pc = num(nozzle_data, "pc_Pa")
            cstar = num(nozzle_data, "cstar_m_s")
            assert_close(self, mdot, at * pc / cstar, "throat continuity", rel=1e-6)
            thrust = num(nozzle_data, "thrust_vac_N")
            isp = thrust / (mdot * G0)
            assert_close(self, num(nozzle_data, "Isp_vac_s"), isp, "Isp", rel=1e-5)
            grain_data = self._bake(grain, ["--out", str(root / "grain.png")])
            self.assertGreater(num(grain_data, "t_burn_s"), 0.0)
            self.assertGreater(num(grain_data, "pc_max_Pa"), 0.0)
            ascent_data = self._bake(ascent, ["--out", str(root / "ascent.png")])
            self.assertGreater(num(ascent_data, "dv_design_m_s"), 0.0)
            self.assertGreater(num(ascent_data, "stage_1_mp_kg"), 0.0)
            refused = run_fail(ascent, ["--stages", "1", "--path", "gamma", "--out", str(root / "one.png")])
            self.assertIn("structural coefficient", refused)


if __name__ == "__main__":
    unittest.main()
