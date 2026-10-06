#!/usr/bin/env python3
"""Planar true proportional navigation.

true_pn_commanded_acceleration is a_c = N_prime * V_c * lambda_dot.
closing_speed is V_c = -R_dot (positive when range decreases).
los_rate is lambda_dot = (Rx*Vy - Ry*Vx)/R**2 for relative state
R = r_t - r_m and V = v_t - v_m.
Mode 1: instantaneous a_c from N', V_c, and LOS rate.
Mode 2: constant-speed planar engagement with true-PN steering
(command normal to the LOS; speed held by removing the along-track
component) and optional constant target lateral acceleration.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-9
ENGAGE_TOL = 1e-3
PLOT_TITLE = "Proportional navigation"
DEFAULT_DT = 0.01
DEFAULT_T_MAX = 300.0
DEFAULT_HIT_RADIUS = 1.0
DEFAULT_AT_LAT = 0.0
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "planar true proportional navigation; "
    "true_pn_commanded_acceleration a_c = N_prime*V_c*lambda_dot; "
    "N_prime is the effective navigation ratio (dimensionless); "
    "closing_speed V_c = -R_dot > 0 when range decreases; "
    "LOS angle lambda = atan2(Ry, Rx) from interceptor to target "
    "with R = r_t - r_m; "
    "los_rate lambda_dot = (Rx*Vy - Ry*Vx)/R**2 for relative velocity "
    "V = v_t - v_m; "
    "true-PN acceleration of the interceptor is a_c*(-sin(lambda), "
    "cos(lambda)), normal to the LOS; "
    "Mode 1 is instantaneous a_c only; "
    "Mode 2 is constant-speed planar kinematics: interceptor and target "
    "speeds are held fixed by dropping the along-track part of each "
    "commanded acceleration; optional constant target lateral "
    "acceleration (default 0) is normal to the target velocity; "
    "no gravity, atmosphere, seeker noise, filters, autopilot lag, "
    "3D PN, pursuit, or APN"
)


@dataclass(frozen=True)
class InstantResult:
    n_prime: float
    vc: float
    los_rate: float
    a_c: float


@dataclass(frozen=True)
class EngageResult:
    n_prime: float
    a_c0: float
    vc0: float
    los_rate0: float
    range0: float
    los_angle0: float
    vm: float
    vt: float
    at_lat: float
    dt: float
    t_max: float
    hit_radius: float
    outcome: str
    t_final: float
    range_final: float
    miss_distance: float
    t_intercept: float | None
    interceptor_path: list[tuple[float, float]]
    target_path: list[tuple[float, float]]


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def true_pn_commanded_acceleration(
    n_prime: float, closing_speed: float, los_rate: float
) -> float:
    """true_pn_commanded_acceleration: a_c = N_prime * V_c * lambda_dot."""
    return n_prime * closing_speed * los_rate


def closing_speed(range_rate: float) -> float:
    """closing_speed: V_c = -R_dot."""
    return -range_rate


def relative_geometry(
    rx: float, ry: float, vx: float, vy: float
) -> tuple[float, float, float, float, float]:
    """Return (R, lambda, R_dot, V_c, lambda_dot) for R and V relative."""
    r2 = rx * rx + ry * ry
    if r2 <= 0.0:
        raise ValueError("range must be > 0")
    r = math.sqrt(r2)
    lam = math.atan2(ry, rx)
    r_dot = (rx * vx + ry * vy) / r
    vc = closing_speed(r_dot)
    lam_dot = (rx * vy - ry * vx) / r2
    return r, lam, r_dot, vc, lam_dot


def unit_los_normal(lam: float) -> tuple[float, float]:
    """Unit vector in the direction of increasing LOS angle."""
    return (-math.sin(lam), math.cos(lam))


def drop_along_track(
    ax: float, ay: float, vx: float, vy: float
) -> tuple[float, float]:
    """Remove the acceleration component along velocity (constant speed)."""
    speed2 = vx * vx + vy * vy
    if speed2 <= 0.0:
        return 0.0, 0.0
    proj = (ax * vx + ay * vy) / speed2
    return ax - proj * vx, ay - proj * vy


def lateral_acceleration(
    speed: float, heading: float, a_lat: float
) -> tuple[float, float]:
    """Acceleration of magnitude a_lat normal to heading (left positive)."""
    # Left normal to velocity direction (cos h, sin h) is (-sin h, cos h).
    return (-a_lat * math.sin(heading), a_lat * math.cos(heading))


def evaluate_instant(
    n_prime: float, vc: float, los_rate: float
) -> InstantResult:
    require_finite("N_prime", n_prime)
    require_finite("closing speed", vc)
    require_finite("LOS rate", los_rate)
    if n_prime <= 0.0:
        raise ValueError("N_prime must be > 0")
    a_c = true_pn_commanded_acceleration(n_prime, vc, los_rate)
    return InstantResult(n_prime=n_prime, vc=vc, los_rate=los_rate, a_c=a_c)


def resolve_velocities(
    vm: float | None,
    hm: float | None,
    vt: float | None,
    ht: float | None,
    vmx: float | None,
    vmy: float | None,
    vtx: float | None,
    vty: float | None,
) -> tuple[float, float, float, float, float, float]:
    """Return (vmx, vmy, vtx, vty, vm, vt)."""
    heading_path = any(v is not None for v in (vm, hm, vt, ht))
    component_path = any(v is not None for v in (vmx, vmy, vtx, vty))
    if heading_path and component_path:
        raise ValueError(
            "pass speed/heading (--vm --hm --vt --ht) or velocity "
            "components (--vmx --vmy --vtx --vty), not both"
        )
    if heading_path:
        if None in (vm, hm, vt, ht):
            raise ValueError(
                "speed/heading path requires --vm, --hm, --vt, and --ht"
            )
        require_positive("interceptor speed", float(vm))
        require_positive("target speed", float(vt))
        require_finite("interceptor heading", float(hm))
        require_finite("target heading", float(ht))
        vmx_v = float(vm) * math.cos(float(hm))
        vmy_v = float(vm) * math.sin(float(hm))
        vtx_v = float(vt) * math.cos(float(ht))
        vty_v = float(vt) * math.sin(float(ht))
        return vmx_v, vmy_v, vtx_v, vty_v, float(vm), float(vt)
    if component_path:
        if None in (vmx, vmy, vtx, vty):
            raise ValueError(
                "component path requires --vmx, --vmy, --vtx, and --vty"
            )
        for name, value in (
            ("vmx", vmx),
            ("vmy", vmy),
            ("vtx", vtx),
            ("vty", vty),
        ):
            require_finite(name, float(value))
        vm_s = math.hypot(float(vmx), float(vmy))
        vt_s = math.hypot(float(vtx), float(vty))
        require_positive("interceptor speed", vm_s)
        require_positive("target speed", vt_s)
        return float(vmx), float(vmy), float(vtx), float(vty), vm_s, vt_s
    raise ValueError(
        "engagement requires --vm --hm --vt --ht, or --vmx --vmy --vtx --vty"
    )


def evaluate_engage(
    n_prime: float,
    range0: float,
    los_angle0: float,
    vm: float | None,
    hm: float | None,
    vt: float | None,
    ht: float | None,
    vmx: float | None,
    vmy: float | None,
    vtx: float | None,
    vty: float | None,
    at_lat: float,
    dt: float,
    t_max: float,
    hit_radius: float,
) -> EngageResult:
    require_finite("N_prime", n_prime)
    if n_prime <= 0.0:
        raise ValueError("N_prime must be > 0")
    require_positive("initial range", range0)
    require_finite("initial LOS angle", los_angle0)
    require_finite("target lateral acceleration", at_lat)
    require_positive("dt", dt)
    require_positive("t_max", t_max)
    require_positive("hit radius", hit_radius)

    vmx_v, vmy_v, vtx_v, vty_v, vm_s, vt_s = resolve_velocities(
        vm, hm, vt, ht, vmx, vmy, vtx, vty
    )

    xm, ym = 0.0, 0.0
    xt = range0 * math.cos(los_angle0)
    yt = range0 * math.sin(los_angle0)

    rx0 = xt - xm
    ry0 = yt - ym
    vx0 = vtx_v - vmx_v
    vy0 = vty_v - vmy_v
    r0, lam0, _rd0, vc0, lam_dot0 = relative_geometry(rx0, ry0, vx0, vy0)
    a_c0 = true_pn_commanded_acceleration(n_prime, vc0, lam_dot0)

    interceptor_path: list[tuple[float, float]] = [(xm, ym)]
    target_path: list[tuple[float, float]] = [(xt, yt)]

    t = 0.0
    miss = r0
    t_at_miss = 0.0
    outcome = "timeout"
    t_intercept: float | None = None

    # Store speed magnitudes; directions follow integrated velocities.
    while t < t_max - 0.5 * dt:
        rx = xt - xm
        ry = yt - ym
        vx = vtx_v - vmx_v
        vy = vty_v - vmy_v
        try:
            r, lam, _rd, vc, lam_dot = relative_geometry(rx, ry, vx, vy)
        except ValueError:
            outcome = "intercept"
            t_intercept = t
            miss = 0.0
            t_at_miss = t
            break

        if r < miss:
            miss = r
            t_at_miss = t
        if r <= hit_radius:
            outcome = "intercept"
            t_intercept = t
            miss = r
            t_at_miss = t
            break
        # After closest approach while still separating, report a miss.
        if t > 0.0 and vc < 0.0 and r > miss + hit_radius:
            outcome = "miss"
            break

        a_c = true_pn_commanded_acceleration(n_prime, vc, lam_dot)
        nx, ny = unit_los_normal(lam)
        amx_cmd = a_c * nx
        amy_cmd = a_c * ny
        amx, amy = drop_along_track(amx_cmd, amy_cmd, vmx_v, vmy_v)

        # Target lateral accel is left-normal to its velocity; keep speed.
        ht_now = math.atan2(vty_v, vtx_v)
        atx_cmd, aty_cmd = lateral_acceleration(vt_s, ht_now, at_lat)
        atx, aty = drop_along_track(atx_cmd, aty_cmd, vtx_v, vty_v)

        # Semi-implicit Euler: advance velocity, then position.
        vmx_v += amx * dt
        vmy_v += amy * dt
        vtx_v += atx * dt
        vty_v += aty * dt
        # Renormalize to exact constant speeds (numerical drift).
        sm = math.hypot(vmx_v, vmy_v)
        st = math.hypot(vtx_v, vty_v)
        if sm > 0.0:
            vmx_v *= vm_s / sm
            vmy_v *= vm_s / sm
        if st > 0.0:
            vtx_v *= vt_s / st
            vty_v *= vt_s / st

        xm += vmx_v * dt
        ym += vmy_v * dt
        xt += vtx_v * dt
        yt += vty_v * dt
        t += dt
        interceptor_path.append((xm, ym))
        target_path.append((xt, yt))

    range_final = math.hypot(xt - xm, yt - ym)
    if outcome == "timeout":
        # Prefer miss distance at closest approach if it occurred.
        if miss < r0:
            outcome = "miss"

    return EngageResult(
        n_prime=n_prime,
        a_c0=a_c0,
        vc0=vc0,
        los_rate0=lam_dot0,
        range0=range0,
        los_angle0=los_angle0,
        vm=vm_s,
        vt=vt_s,
        at_lat=at_lat,
        dt=dt,
        t_max=t_max,
        hit_radius=hit_radius,
        outcome=outcome,
        t_final=t_at_miss if outcome == "miss" else t,
        range_final=range_final if outcome != "miss" else miss,
        miss_distance=miss,
        t_intercept=t_intercept,
        interceptor_path=interceptor_path,
        target_path=target_path,
    )


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the engagement") from exc
    return plt


def write_plot(result: EngageResult, out_path: Path) -> None:
    plt = ensure_matplotlib()
    xi = [p[0] for p in result.interceptor_path]
    yi = [p[1] for p in result.interceptor_path]
    xt = [p[0] for p in result.target_path]
    yt = [p[1] for p in result.target_path]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.5))
    ax.plot(xi, yi, color="#1a5276", linewidth=1.8, label="interceptor")
    ax.plot(xt, yt, color="#c0392b", linewidth=1.8, label="target")
    ax.plot(xi[0], yi[0], "o", color="#1a5276", markersize=6)
    ax.plot(xt[0], yt[0], "o", color="#c0392b", markersize=6)
    ax.plot(xi[-1], yi[-1], "s", color="#1a5276", markersize=6)
    ax.plot(xt[-1], yt[-1], "s", color="#c0392b", markersize=6)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(PLOT_TITLE)
    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit_instant(result: InstantResult) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", "instantaneous")
    print_kv("N_prime", result.n_prime)
    print_kv("Vc_m_s", result.vc)
    print_kv("lambda_dot_rad_s", result.los_rate)
    print_kv("a_c_m_s2", result.a_c)
    print_kv("a_c_units", "m/s^2")


def emit_engage(result: EngageResult, graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", "engagement")
    print_kv("N_prime", result.n_prime)
    print_kv("a_c_m_s2", result.a_c0)
    print_kv("a_c_units", "m/s^2")
    print_kv("Vc0_m_s", result.vc0)
    print_kv("lambda_dot0_rad_s", result.los_rate0)
    print_kv("range0_m", result.range0)
    print_kv("lambda0_rad", result.los_angle0)
    print_kv("Vm_m_s", result.vm)
    print_kv("Vt_m_s", result.vt)
    print_kv("at_lat_m_s2", result.at_lat)
    print_kv("dt_s", result.dt)
    print_kv("t_max_s", result.t_max)
    print_kv("hit_radius_m", result.hit_radius)
    print_kv("outcome", result.outcome)
    if result.t_intercept is not None:
        print_kv("t_intercept_s", result.t_intercept)
    else:
        print_kv("miss_distance_m", result.miss_distance)
    print_kv("range_final_m", result.range_final)
    print_kv("t_final_s", result.t_final)
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    # Mode 1 identity: a_c = N' * V_c * lambda_dot.
    if not close(true_pn_commanded_acceleration(3.0, 1000.0, 0.01), 30.0):
        return fail("Mode 1 identity 3*1000*0.01 is not 30")
    if not close(true_pn_commanded_acceleration(4.0, 500.0, -0.02), -40.0):
        return fail("signed Mode 1 identity mismatch")
    if not close(closing_speed(-250.0), 250.0):
        return fail("closing speed from R_dot=-250 is not 250")

    instant = evaluate_instant(3.0, 1000.0, 0.01)
    if not close(instant.a_c, 30.0):
        return fail("evaluate_instant a_c mismatch")

    # Relative geometry on a simple right-angle LOS.
    r, lam, r_dot, vc, lam_dot = relative_geometry(3.0, 4.0, -1.0, 0.0)
    if not close(r, 5.0):
        return fail("range of (3,4) is not 5")
    if not close(lam, math.atan2(4.0, 3.0)):
        return fail("LOS angle mismatch")
    if not close(r_dot, -3.0 / 5.0):
        return fail("range rate mismatch")
    if not close(vc, 3.0 / 5.0):
        return fail("closing speed from geometry mismatch")
    if not close(lam_dot, (3.0 * 0.0 - 4.0 * (-1.0)) / 25.0):
        return fail("LOS rate mismatch")

    # Engagement regression: head-on collision course, lambda_dot = 0.
    # Interceptor at origin heading +x at 300 m/s; target at (10000,0)
    # heading -x at 200 m/s. Closing speed 500 m/s; t_go = 20 s.
    engage = evaluate_engage(
        n_prime=3.0,
        range0=10000.0,
        los_angle0=0.0,
        vm=300.0,
        hm=0.0,
        vt=200.0,
        ht=math.pi,
        vmx=None,
        vmy=None,
        vtx=None,
        vty=None,
        at_lat=0.0,
        dt=0.01,
        t_max=30.0,
        hit_radius=1.0,
    )
    if abs(engage.los_rate0) > 1e-12:
        return fail("head-on case initial LOS rate is not ~0")
    if not close(engage.vc0, 500.0):
        return fail("head-on closing speed is not 500")
    if not close(engage.a_c0, 0.0):
        return fail("head-on initial a_c is not 0")
    if engage.outcome != "intercept" or engage.t_intercept is None:
        return fail("head-on engagement did not intercept")
    expected_t = 10000.0 / 500.0
    if not close(engage.t_intercept, expected_t, tol=ENGAGE_TOL):
        return fail(
            f"head-on t_intercept {engage.t_intercept} != {expected_t}"
        )
    if engage.miss_distance > engage.hit_radius:
        return fail("head-on miss exceeds hit radius")

    # Off-axis non-maneuvering engagement should still close under PN.
    offset = evaluate_engage(
        n_prime=4.0,
        range0=8000.0,
        los_angle0=0.2,
        vm=350.0,
        hm=0.05,
        vt=250.0,
        ht=math.pi - 0.05,
        vmx=None,
        vmy=None,
        vtx=None,
        vty=None,
        at_lat=0.0,
        dt=0.01,
        t_max=60.0,
        hit_radius=5.0,
    )
    if offset.outcome not in ("intercept", "miss"):
        return fail("offset engagement timed out")
    if offset.miss_distance > 50.0:
        return fail("offset PN miss distance unexpectedly large")

    try:
        evaluate_instant(0.0, 1000.0, 0.01)
        return fail("non-positive N_prime was accepted")
    except ValueError:
        pass
    try:
        evaluate_engage(
            3.0,
            1000.0,
            0.0,
            300.0,
            0.0,
            200.0,
            math.pi,
            1.0,
            0.0,
            -1.0,
            0.0,
            0.0,
            0.01,
            10.0,
            1.0,
        )
        return fail("mixed velocity APIs were accepted")
    except ValueError:
        pass

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out = _Capture()
        err = _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "pn.png")
        code, text, err = capture(
            ["--n-prime", "3", "--vc", "1000", "--los-rate", "0.01"]
        )
        if code != 0:
            return fail(f"Mode 1 main returned {code}: {err}")
        for key in (
            "mode: instantaneous",
            "N_prime: 3",
            "a_c_m_s2: 30",
            "a_c_units: m/s^2",
        ):
            if key not in text:
                return fail(f"Mode 1 stdout missing {key}")

        code, text, err = capture(
            [
                "--n-prime",
                "3",
                "--range",
                "10000",
                "--los-angle",
                "0",
                "--vm",
                "300",
                "--hm",
                "0",
                "--vt",
                "200",
                "--ht",
                str(math.pi),
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"Mode 2 main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("engagement run did not write a PNG")
        for key in (
            "mode: engagement",
            "t_intercept_s:",
            "title: Proportional navigation",
            "graph:",
        ):
            if key not in text:
                return fail(f"Mode 2 stdout missing {key}")

        code, _text, err = capture(
            ["--n-prime", "3", "--vc", "1000", "--range", "1000"]
        )
        if code != 2:
            return fail("mixed Mode 1/2 inputs were accepted")
        code, _text, _err = capture(["--n-prime", "3"])
        if code != 2:
            return fail("incomplete inputs were accepted")
        code, _text, _err = capture([])
        if code != 2:
            return fail("empty args were accepted")

    print("check: pass")
    print_kv("a_c_m_s2", 30.0)
    print_kv("t_intercept_s", expected_t)
    print_kv("miss_distance_m", engage.miss_distance)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Planar true proportional navigation: instantaneous commanded "
            "acceleration and/or a constant-speed planar engagement."
        )
    )
    parser.add_argument(
        "--n-prime",
        type=float,
        default=None,
        help="effective navigation ratio N' [-]",
    )
    parser.add_argument(
        "--vc",
        type=float,
        default=None,
        help="closing speed V_c [m/s] (Mode 1)",
    )
    parser.add_argument(
        "--los-rate",
        type=float,
        default=None,
        help="LOS rate lambda_dot [rad/s] (Mode 1)",
    )
    parser.add_argument(
        "--range",
        type=float,
        default=None,
        help="initial range R0 [m] (Mode 2)",
    )
    parser.add_argument(
        "--los-angle",
        type=float,
        default=None,
        help="initial LOS angle lambda0 [rad] (Mode 2)",
    )
    parser.add_argument("--vm", type=float, default=None, help="interceptor speed [m/s]")
    parser.add_argument(
        "--hm", type=float, default=None, help="interceptor heading [rad from +x]"
    )
    parser.add_argument("--vt", type=float, default=None, help="target speed [m/s]")
    parser.add_argument(
        "--ht", type=float, default=None, help="target heading [rad from +x]"
    )
    parser.add_argument("--vmx", type=float, default=None, help="interceptor vx [m/s]")
    parser.add_argument("--vmy", type=float, default=None, help="interceptor vy [m/s]")
    parser.add_argument("--vtx", type=float, default=None, help="target vx [m/s]")
    parser.add_argument("--vty", type=float, default=None, help="target vy [m/s]")
    parser.add_argument(
        "--at-lat",
        type=float,
        default=DEFAULT_AT_LAT,
        help=f"constant target lateral acceleration [m/s^2] (default {DEFAULT_AT_LAT:g})",
    )
    parser.add_argument(
        "--dt",
        type=float,
        default=DEFAULT_DT,
        help=f"integrator step [s] (default {DEFAULT_DT:g})",
    )
    parser.add_argument(
        "--t-max",
        type=float,
        default=DEFAULT_T_MAX,
        help=f"maximum engagement time [s] (default {DEFAULT_T_MAX:g})",
    )
    parser.add_argument(
        "--hit-radius",
        type=float,
        default=DEFAULT_HIT_RADIUS,
        help=f"intercept range threshold [m] (default {DEFAULT_HIT_RADIUS:g})",
    )
    parser.add_argument("--out", type=str, default=None, help="optional engagement PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.n_prime is None:
        print(
            "error: requires --n-prime and either Mode 1 (--vc --los-rate) "
            "or Mode 2 (--range --los-angle and velocity state)",
            file=sys.stderr,
        )
        return 2

    mode1 = args.vc is not None or args.los_rate is not None
    mode2 = (
        args.range is not None
        or args.los_angle is not None
        or any(
            v is not None
            for v in (
                args.vm,
                args.hm,
                args.vt,
                args.ht,
                args.vmx,
                args.vmy,
                args.vtx,
                args.vty,
            )
        )
    )
    if mode1 and mode2:
        print(
            "error: pass Mode 1 (--vc --los-rate) or Mode 2 "
            "(--range --los-angle and velocities), not both",
            file=sys.stderr,
        )
        return 2

    if mode1:
        if args.vc is None or args.los_rate is None:
            print("error: Mode 1 requires --vc and --los-rate", file=sys.stderr)
            return 2
        if args.out is not None:
            print("error: --out is only valid for Mode 2 engagement", file=sys.stderr)
            return 2
        try:
            result = evaluate_instant(args.n_prime, args.vc, args.los_rate)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        emit_instant(result)
        return 0

    if args.range is None or args.los_angle is None:
        print(
            "error: Mode 2 requires --range, --los-angle, and velocity state",
            file=sys.stderr,
        )
        return 2

    try:
        result = evaluate_engage(
            args.n_prime,
            args.range,
            args.los_angle,
            args.vm,
            args.hm,
            args.vt,
            args.ht,
            args.vmx,
            args.vmy,
            args.vtx,
            args.vty,
            args.at_lat,
            args.dt,
            args.t_max,
            args.hit_radius,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    graph: Path | None = None
    if args.out is not None:
        out_path = Path(args.out).resolve()
        try:
            write_plot(result, out_path)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = out_path

    emit_engage(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
