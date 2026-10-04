#!/usr/bin/env python3
"""Circular-port solid-grain histories of pc, K, and remaining web.

Ab is circular_port_burning_area: Ab = 2*pi*r*L, ends inhibited.
Remaining web is remaining_web: wrem = Ro - r.
K is burning_area_ratio. pc is equilibrium_chamber_pressure.
Time is remaining_web_time along the local burning_rate.
A prescribed sliver_volume_fraction stops the history at sliver_port_radius.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
N_CURVE = 201
PLOT_TITLE = "Circular-port grain history"

SKILL_DIR = Path(__file__).resolve().parent
SOLID_DIR = SKILL_DIR.parent / "ROCKET - SolidMotorParameters"

ASSUMPTIONS = (
    "concentric circular port, inhibited ends; "
    "circular_port_burning_area Ab = 2*pi*r*L; "
    "initial_web w0 = Ro - Rp; remaining_web wrem = Ro - r; "
    "K = Ab/At; rburn = a*pc**n; "
    "pc = (K*a*rho_b*c*)**(1/(1-n)); "
    "remaining_web_time t = integral(wrem, w0, 1/rburn) with rburn from "
    "the instantaneous port; constant a, n, rho_b, and c*; "
    "quasi-steady mass balance; no erosive burning; n < 1; "
    "web burnout only, with optional sliver_volume_fraction s in [0, 1) "
    "stopping at sliver_port_radius; a concentric circular case has "
    "geometric sliver 0"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= CHECK_TOL * scale


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def load_solid():
    folder = str(SOLID_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from solid_motor_parameters import (
            burn_rate,
            burning_area_ratio,
            equilibrium_chamber_pressure,
        )
    except ImportError as exc:
        raise ValueError(
            "ROCKET - SolidMotorParameters must be importable"
        ) from exc
    return burning_area_ratio, equilibrium_chamber_pressure, burn_rate


def circular_port_burning_area(radius: float, length: float) -> float:
    """circular_port_burning_area."""
    return 2.0 * math.pi * radius * length


def circular_port_radius(ab: float, length: float) -> float:
    """circular_port_radius."""
    return ab / (2.0 * math.pi * length)


def circular_grain_length(ab: float, radius: float) -> float:
    """circular_grain_length."""
    return ab / (2.0 * math.pi * radius)


def initial_web(outer: float, port: float) -> float:
    """initial_web."""
    return outer - port


def remaining_web(outer: float, radius: float) -> float:
    """remaining_web."""
    return outer - radius


def circular_port_from_remaining_web(outer: float, wrem: float) -> float:
    """circular_port_from_remaining_web."""
    return outer - wrem


def circular_grain_volume(outer: float, port: float, length: float) -> float:
    """circular_grain_volume."""
    return math.pi * (outer * outer - port * port) * length


def circular_remaining_volume(outer: float, radius: float, length: float) -> float:
    """circular_remaining_volume."""
    return math.pi * (outer * outer - radius * radius) * length


def sliver_volume_fraction(vsliver: float, volume0: float) -> float:
    """sliver_volume_fraction."""
    return vsliver / volume0


def sliver_port_radius(outer: float, sliver: float, port: float) -> float:
    """sliver_port_radius. sliver is the volume fraction s."""
    return math.sqrt(outer * outer - sliver * (outer * outer - port * port))


def rate_law(a: float, n: float, length: float, throat: float, rho: float, cstar: float) -> tuple[float, float]:
    """rburn = C * r**alpha from Saint Robert plus circular_port_burning_area."""
    alpha = n / (1.0 - n)
    scale = (2.0 * math.pi * length / throat) * a * rho * cstar
    prefactor = a * scale**alpha
    return alpha, prefactor


def remaining_web_time_constant(wrem: float, web0: float, rburn: float) -> float:
    """remaining_web_time at constant rburn."""
    return (web0 - wrem) / rburn


def time_from_port(radius: float, port: float, alpha: float, prefactor: float) -> float:
    """remaining_web_time with rburn = C * r**alpha."""
    if radius < port:
        raise ValueError("port radius cannot shrink")
    if radius == port:
        return 0.0
    if abs(alpha - 1.0) <= 1e-14:
        return math.log(radius / port) / prefactor
    return (radius ** (1.0 - alpha) - port ** (1.0 - alpha)) / (
        prefactor * (1.0 - alpha)
    )


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def resolve_geometry(
    ab: float | None,
    port: float | None,
    length: float | None,
    outer: float,
) -> tuple[float, float, float]:
    """Return (Rp, L, Ab0) from the allowed input combinations."""
    require_positive("outer propellant radius", outer)
    if ab is not None:
        require_positive("burning area", ab)
    if port is not None:
        require_positive("port radius", port)
    if length is not None:
        require_positive("grain length", length)

    if ab is not None and port is not None and length is not None:
        ab_geom = circular_port_burning_area(port, length)
        if not close(ab, ab_geom):
            raise ValueError(
                "burning area must match circular_port_burning_area 2*pi*Rp*L"
            )
        rp, grain_length, ab0 = port, length, ab
    elif port is not None and length is not None and ab is None:
        rp, grain_length = port, length
        ab0 = circular_port_burning_area(rp, grain_length)
    elif ab is not None and length is not None and port is None:
        grain_length = length
        ab0 = ab
        rp = circular_port_radius(ab0, grain_length)
    elif ab is not None and port is not None and length is None:
        rp = port
        ab0 = ab
        grain_length = circular_grain_length(ab0, rp)
    else:
        raise ValueError(
            "give --ab with --port or --length, or --port and --length"
        )

    if not math.isfinite(rp) or rp <= 0.0:
        raise ValueError("port radius must be finite and > 0 m")
    if outer <= rp:
        raise ValueError("outer propellant radius must be > port radius")
    return rp, grain_length, ab0


def validate_ballistics(a: float, n: float, throat: float, rho: float, cstar: float) -> None:
    require_positive("burn-rate coefficient", a)
    require_positive("throat area", throat)
    require_positive("propellant density", rho)
    require_positive("c*", cstar)
    if not math.isfinite(n) or n >= 1.0:
        raise ValueError("burn-rate exponent n must be finite and < 1")


def validate_sliver(sliver_percent: float) -> float:
    if not math.isfinite(sliver_percent) or sliver_percent < 0.0 or sliver_percent >= 100.0:
        raise ValueError("sliver percent must be finite and in [0, 100)")
    return sliver_percent / 100.0


def history(
    a: float,
    n: float,
    throat: float,
    rho: float,
    cstar: float,
    port: float,
    length: float,
    outer: float,
    sliver: float,
    burning_area_ratio,
    equilibrium_chamber_pressure,
    burn_rate,
) -> dict[str, object]:
    web0 = initial_web(outer, port)
    volume0 = circular_grain_volume(outer, port, length)
    r_end = sliver_port_radius(outer, sliver, port)
    w_end = remaining_web(outer, r_end)
    if r_end <= port:
        raise ValueError("sliver fraction leaves no web to burn")
    v_end = circular_remaining_volume(outer, r_end, length)
    s_check = sliver_volume_fraction(v_end, volume0)
    if sliver == 0.0:
        if not close(s_check, 0.0):
            raise ValueError("zero sliver did not reach web burnout")
    elif not close(s_check, sliver):
        raise ValueError("sliver port radius does not match remaining volume")

    alpha, prefactor = rate_law(a, n, length, throat, rho, cstar)
    if not math.isfinite(prefactor) or prefactor <= 0.0:
        raise ValueError("burn-rate prefactor must be finite and > 0")
    t_burn = time_from_port(r_end, port, alpha, prefactor)

    times: list[float] = []
    k_hist: list[float] = []
    pc_hist: list[float] = []
    wrem_hist: list[float] = []
    ab_hist: list[float] = []
    radius_hist: list[float] = []
    for i in range(N_CURVE):
        wrem = web0 + (w_end - web0) * i / (N_CURVE - 1)
        radius = circular_port_from_remaining_web(outer, wrem)
        ab = circular_port_burning_area(radius, length)
        k = burning_area_ratio(ab, throat)
        pc = equilibrium_chamber_pressure(k, a, rho, cstar, n)
        rburn = burn_rate(a, pc, n)
        t = time_from_port(radius, port, alpha, prefactor)
        expected_rburn = prefactor * radius**alpha
        if not close(rburn, expected_rburn):
            raise ValueError("composed burn rate does not match Saint Robert at this port")
        times.append(t)
        k_hist.append(k)
        pc_hist.append(pc)
        wrem_hist.append(wrem)
        ab_hist.append(ab)
        radius_hist.append(radius)

    return {
        "Rp_m": port,
        "L_m": length,
        "Ro_m": outer,
        "Ab0_m2": ab_hist[0],
        "w0_m": web0,
        "V0_m3": volume0,
        "s": sliver,
        "s_percent": 100.0 * sliver,
        "r_end_m": r_end,
        "wrem_end_m": w_end,
        "t_burn_s": t_burn,
        "K_initial": k_hist[0],
        "K_burnout": k_hist[-1],
        "pc_initial_Pa": pc_hist[0],
        "pc_burnout_Pa": pc_hist[-1],
        "Ab_burnout_m2": ab_hist[-1],
        "times": times,
        "K": k_hist,
        "pc": pc_hist,
        "wrem": wrem_hist,
        "Ab": ab_hist,
        "radius": radius_hist,
    }


def plot_history(out_path: Path, result: dict[str, object]) -> None:
    import matplotlib

    if "matplotlib.pyplot" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    times = result["times"]
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(8, 8))
    axes[0].plot(times, result["pc"], color="#1a5276", linewidth=1.8)
    axes[0].set_ylabel(r"Chamber pressure $p_1$ (Pa)")
    axes[0].grid(True, alpha=0.35)
    axes[1].plot(times, result["K"], color="#117a65", linewidth=1.8)
    axes[1].set_ylabel(r"Burning-area ratio $K$")
    axes[1].grid(True, alpha=0.35)
    axes[2].plot(times, result["wrem"], color="#a04000", linewidth=1.8)
    axes[2].set_ylabel(r"Remaining web $w_{\mathrm{rem}}$ (m)")
    axes[2].set_xlabel("Time $t$ (s)")
    axes[2].grid(True, alpha=0.35)
    axes[0].set_title(PLOT_TITLE)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def emit(
    a: float,
    n: float,
    throat: float,
    rho: float,
    cstar: float,
    result: dict[str, object],
    out_path: Path,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("a", a)
    print_kv("n", n)
    print_kv("At_m2", throat)
    print_kv("rho_b_kg_m3", rho)
    print_kv("cstar_m_s", cstar)
    print_kv("Rp_m", result["Rp_m"])
    print_kv("L_m", result["L_m"])
    print_kv("Ro_m", result["Ro_m"])
    print_kv("Ab0_m2", result["Ab0_m2"])
    print_kv("w0_m", result["w0_m"])
    print_kv("V0_m3", result["V0_m3"])
    print_kv("sliver_fraction", result["s"])
    print_kv("sliver_percent", result["s_percent"])
    print_kv("r_end_m", result["r_end_m"])
    print_kv("wrem_initial_m", result["w0_m"])
    print_kv("wrem_burnout_m", result["wrem_end_m"])
    print_kv("t_burn_s", result["t_burn_s"])
    print_kv("K_initial", result["K_initial"])
    print_kv("K_burnout", result["K_burnout"])
    print_kv("pc_initial_Pa", result["pc_initial_Pa"])
    print_kv("pc_burnout_Pa", result["pc_burnout_Pa"])
    print_kv("Ab_burnout_m2", result["Ab_burnout_m2"])
    print_kv("n_samples", N_CURVE)
    print_kv("graph", str(out_path))


def run_check() -> int:
    burning_area_ratio, equilibrium_chamber_pressure, burn_rate = load_solid()

    if not close(circular_port_burning_area(1.0, 1.0), 2.0 * math.pi):
        return fail("CHECK FAIL: circular_port_burning_area")
    if not close(circular_port_radius(2.0 * math.pi, 1.0), 1.0):
        return fail("CHECK FAIL: circular_port_radius")
    if not close(circular_grain_length(2.0 * math.pi, 1.0), 1.0):
        return fail("CHECK FAIL: circular_grain_length")
    if not close(initial_web(0.05, 0.03), 0.02):
        return fail("CHECK FAIL: initial_web")
    if not close(remaining_web(0.05, 0.04), 0.01):
        return fail("CHECK FAIL: remaining_web")
    if not close(circular_port_from_remaining_web(0.05, 0.01), 0.04):
        return fail("CHECK FAIL: circular_port_from_remaining_web")
    if not close(circular_grain_volume(2.0, 1.0, 1.0), 3.0 * math.pi):
        return fail("CHECK FAIL: circular_grain_volume")
    if not close(circular_remaining_volume(2.0, math.sqrt(2.0), 1.0), 2.0 * math.pi):
        return fail("CHECK FAIL: circular_remaining_volume")
    if not close(sliver_volume_fraction(1.0, 20.0), 0.05):
        return fail("CHECK FAIL: sliver_volume_fraction")
    if not close(sliver_port_radius(5.0, 0.0, 3.0), 5.0):
        return fail("CHECK FAIL: sliver_port_radius no sliver")
    if not close(sliver_port_radius(5.0, 1.0, 3.0), 3.0):
        return fail("CHECK FAIL: sliver_port_radius all sliver")
    if not close(remaining_web_time_constant(0.01, 0.05, 0.02), 2.0):
        return fail("CHECK FAIL: remaining_web_time constant rate")

    a = 1.0 / 100000.0
    n = 0.5
    length = 1.0
    port = 1.0 / (5.0 * math.pi)
    ab0 = circular_port_burning_area(port, length)
    if not close(ab0, 0.4):
        return fail(f"CHECK FAIL: Ab0 = {ab0}, expected 0.4")
    throat = 1.0 / 500.0
    rho = 1800.0
    cstar = 5000.0 / 9.0
    k0 = burning_area_ratio(ab0, throat)
    if not close(k0, 200.0):
        return fail(f"CHECK FAIL: K = {k0}, expected 200")
    pc0 = equilibrium_chamber_pressure(k0, a, rho, cstar, n)
    if not close(pc0, 4000000.0):
        return fail(f"CHECK FAIL: pc = {pc0}, expected 4000000")
    r0 = burn_rate(a, pc0, n)
    if not close(r0, 0.02):
        return fail(f"CHECK FAIL: rburn = {r0}, expected 0.02")

    outer = 2.0 * port
    result = history(
        a,
        n,
        throat,
        rho,
        cstar,
        port,
        length,
        outer,
        0.0,
        burning_area_ratio,
        equilibrium_chamber_pressure,
        burn_rate,
    )
    alpha, prefactor = rate_law(a, n, length, throat, rho, cstar)
    t_closed = math.log(outer / port) / prefactor
    if not close(result["t_burn_s"], t_closed):
        return fail("CHECK FAIL: n=1/2 burn time")
    if not close(result["wrem_end_m"], 0.0):
        return fail("CHECK FAIL: remaining web at burnout")
    if not close(result["pc_initial_Pa"], 4000000.0):
        return fail("CHECK FAIL: initial pc")
    if result["times"][0] != 0.0:
        return fail("CHECK FAIL: history must start at t = 0")
    if not close(result["times"][-1], result["t_burn_s"]):
        return fail("CHECK FAIL: last sample is not burnout time")
    if not close(result["K_burnout"], burning_area_ratio(circular_port_burning_area(outer, length), throat)):
        return fail("CHECK FAIL: burnout K")

    n_zero = 0.0
    a_zero = 0.02
    result_n0 = history(
        a_zero,
        n_zero,
        throat,
        rho,
        cstar,
        port,
        length,
        outer,
        0.0,
        burning_area_ratio,
        equilibrium_chamber_pressure,
        burn_rate,
    )
    t_n0 = remaining_web_time_constant(0.0, initial_web(outer, port), a_zero)
    if not close(result_n0["t_burn_s"], t_n0):
        return fail("CHECK FAIL: n=0 remaining_web_time")

    sliver = 0.25
    r_s = sliver_port_radius(outer, sliver, port)
    v0 = circular_grain_volume(outer, port, length)
    vred = circular_remaining_volume(outer, r_s, length)
    if not close(sliver_volume_fraction(vred, v0), sliver):
        return fail("CHECK FAIL: sliver remaining volume")
    result_s = history(
        a,
        n,
        throat,
        rho,
        cstar,
        port,
        length,
        outer,
        sliver,
        burning_area_ratio,
        equilibrium_chamber_pressure,
        burn_rate,
    )
    if not close(result_s["r_end_m"], r_s):
        return fail("CHECK FAIL: history sliver port")
    if not close(result_s["wrem_end_m"], remaining_web(outer, r_s)):
        return fail("CHECK FAIL: history remaining web at sliver")
    if result_s["t_burn_s"] >= result["t_burn_s"]:
        return fail("CHECK FAIL: sliver must shorten the burn")

    rp, grain_length, ab_res = resolve_geometry(None, port, length, outer)
    if not close(rp, port) or not close(ab_res, ab0) or not close(grain_length, length):
        return fail("CHECK FAIL: geometry from port and length")
    rp2, l2, ab2 = resolve_geometry(ab0, None, length, outer)
    if not close(rp2, port) or not close(ab2, ab0) or not close(l2, length):
        return fail("CHECK FAIL: geometry from area and length")
    rp3, l3, ab3 = resolve_geometry(ab0, port, None, outer)
    if not close(rp3, port) or not close(ab3, ab0) or not close(l3, length):
        return fail("CHECK FAIL: geometry from area and port")

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
        out = str(Path(tmp) / "grain.png")
        code, text, err = capture(
            [
                "--a",
                str(a),
                "--n",
                str(n),
                "--port",
                str(port),
                "--length",
                str(length),
                "--outer",
                str(outer),
                "--throat",
                str(throat),
                "--rho",
                str(rho),
                "--cstar",
                str(cstar),
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        if not Path(out).is_file() or Path(out).stat().st_size < 8:
            return fail("run did not write a PNG")
        for key in (
            "title: Circular-port grain history",
            "t_burn_s:",
            "K_initial:",
            "pc_initial_Pa:",
            "wrem_burnout_m:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

    code, _text, err = capture(
        [
            "--a",
            str(a),
            "--n",
            str(n),
            "--outer",
            str(outer),
            "--throat",
            str(throat),
            "--rho",
            str(rho),
            "--cstar",
            str(cstar),
        ]
    )
    if code != 2:
        return fail("missing grain geometry was accepted")
    code, _text, _err = capture([])
    if code != 2:
        return fail("missing inputs were accepted")
    code, _text, err = capture(
        [
            "--a",
            str(a),
            "--n",
            "1",
            "--port",
            str(port),
            "--length",
            str(length),
            "--outer",
            str(outer),
            "--throat",
            str(throat),
            "--rho",
            str(rho),
            "--cstar",
            str(cstar),
        ]
    )
    if code != 2:
        return fail("n >= 1 was accepted")
    code, _text, err = capture(
        [
            "--a",
            str(a),
            "--n",
            str(n),
            "--ab",
            str(ab0 * 1.1),
            "--port",
            str(port),
            "--length",
            str(length),
            "--outer",
            str(outer),
            "--throat",
            str(throat),
            "--rho",
            str(rho),
            "--cstar",
            str(cstar),
        ]
    )
    if code != 2:
        return fail("inconsistent Ab, port, and length were accepted")
    code, _text, err = capture(
        [
            "--a",
            str(a),
            "--n",
            str(n),
            "--port",
            str(port),
            "--length",
            str(length),
            "--outer",
            str(outer),
            "--throat",
            str(throat),
            "--rho",
            str(rho),
            "--cstar",
            str(cstar),
            "--sliver",
            "100",
        ]
    )
    if code != 2:
        return fail("100 percent sliver was accepted")

    print("check: pass")
    print_kv("K_initial", result["K_initial"])
    print_kv("pc_initial_Pa", result["pc_initial_Pa"])
    print_kv("t_burn_s", result["t_burn_s"])
    print_kv("wrem_burnout_m", result["wrem_end_m"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Circular-port grain histories of chamber pressure, burning-area "
            "ratio, and remaining web."
        )
    )
    parser.add_argument("--a", type=float, default=None, help="burn-rate coefficient a [m/(s·Pa^n)]")
    parser.add_argument("--n", type=float, default=None, help="burn-rate pressure exponent n")
    parser.add_argument("--ab", type=float, default=None, help="initial burning area Ab [m^2]")
    parser.add_argument("--port", type=float, default=None, help="initial port radius Rp [m]")
    parser.add_argument("--length", type=float, default=None, help="grain length L [m]")
    parser.add_argument("--outer", type=float, default=None, help="outer propellant radius Ro [m]")
    parser.add_argument("--throat", type=float, default=None, help="throat area At [m^2]")
    parser.add_argument("--rho", type=float, default=None, help="solid propellant density rho_b [kg/m^3]")
    parser.add_argument("--cstar", type=float, default=None, help="characteristic velocity c* [m/s]")
    parser.add_argument(
        "--sliver",
        type=float,
        default=0.0,
        help="sliver volume percent in [0, 100), default 0",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--a": args.a,
        "--n": args.n,
        "--outer": args.outer,
        "--throat": args.throat,
        "--rho": args.rho,
        "--cstar": args.cstar,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --a, --n, --outer, --throat, --rho, and --cstar; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    try:
        validate_ballistics(args.a, args.n, args.throat, args.rho, args.cstar)
        sliver = validate_sliver(args.sliver)
        port, length, _ab0 = resolve_geometry(args.ab, args.port, args.length, args.outer)
        burning_area_ratio, equilibrium_chamber_pressure, burn_rate = load_solid()
        result = history(
            args.a,
            args.n,
            args.throat,
            args.rho,
            args.cstar,
            port,
            length,
            args.outer,
            sliver,
            burning_area_ratio,
            equilibrium_chamber_pressure,
            burn_rate,
        )
        out_path = Path(args.out) if args.out else SKILL_DIR / "circular_port_grain_history.png"
        out_path = out_path.resolve()
        plot_history(out_path, result)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(args.a, args.n, args.throat, args.rho, args.cstar, result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
