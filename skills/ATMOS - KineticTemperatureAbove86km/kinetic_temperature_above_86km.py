#!/usr/bin/env python3
"""1976 kinetic temperature above 86 km geometric.

Four-segment profile from formulas.md (Atmosphere): isothermal mesopause,
mesosphere ellipse, linear thermosphere ramp, and Bates exospheric layer.
Does not print pressure or density.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

# 1976 U.S. Standard Atmosphere constants (formulas.md, Atmosphere).
R0 = 6.356766e6
Z_MIN = 86000.0
Z_MAX = 1000000.0

Z7 = 86000.0
Z8 = 91000.0
Z9 = 110000.0
Z10 = 120000.0

T7 = 186.8673
T9 = 240.0
T10 = 360.0
TINF = 1000.0

# Linear kinetic-temperature gradient on 110-120 km, K/m.
LK9 = 12.0 / 1000.0

# Ellipse constants; a stored in metres (formulas.md uses -19.9429 km).
TC = 263.1905
A_ELLIPSE = -76.3232
A_SEMI = -19.9429 * 1000.0

# Bates inverse length: LK9 / (TINF - T10) = 0.01875 / km = 1.875e-5 / m.
LAMBDA = LK9 / (TINF - T10)

PLOT_TITLE = "Kinetic temperature above 86 km"
N_CURVE = 600
CHECK_TOL = 1e-9

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "1976 U.S. Standard Atmosphere kinetic-temperature profile at geometric "
    "altitude Z from 86000 m through 1000000 m; four continuous segments with "
    "continuous first derivative; mesopause isothermal T7 = 186.8673 K from "
    "86 to 91 km (kinetic_temperature_linear with LKb = 0); "
    "mesosphere_ellipse_temperature from 91 to 110 km with Tc = 263.1905 K, "
    "A = -76.3232 K, a = -19942.9 m, Z8 = 91000 m; kinetic_temperature_linear "
    "from 110 to 120 km with Tb = 240 K and LKb = 0.012 K/m; "
    "exospheric_temperature from 120 to 1000 km with Tinf = 1000 K (mean solar "
    "activity), Tb = 360 K, reduced_geopotential xi, and lam = 1.875e-5 1/m; "
    "r0 = 6356766 m; pressure and density are omitted (they need species "
    "number densities above 86 km); not the NASA Glenn three-zone fit; "
    "not the hydrostatic molecular-scale layers below 86 km"
)

SEGMENT_MESOPAUSE = "mesopause"
SEGMENT_ELLIPSE = "mesosphere_ellipse"
SEGMENT_LINEAR = "thermosphere_linear"
SEGMENT_EXOSPHERE = "exosphere"


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def require_altitude(value: float, flag: str) -> float:
    if not math.isfinite(value) or value < Z_MIN or value > Z_MAX:
        raise ValueError(
            f"{flag} must be from 86000 to 1000000 m geometric; "
            "the kinetic-temperature segments run from 86 km through 1000 km"
        )
    return value


def segment_name(z_m: float) -> str:
    if z_m >= Z10:
        return SEGMENT_EXOSPHERE
    if z_m >= Z9:
        return SEGMENT_LINEAR
    if z_m >= Z8:
        return SEGMENT_ELLIPSE
    return SEGMENT_MESOPAUSE


def reduced_geopotential(z_m: float, zb_m: float) -> float:
    """reduced_geopotential: xi = (Z - Zb)*(r0 + Zb)/(r0 + Z)."""
    return (z_m - zb_m) * (R0 + zb_m) / (R0 + z_m)


def kinetic_temperature_linear(tb: float, lkb: float, z_m: float, zb_m: float) -> float:
    """kinetic_temperature_linear: T = Tb + LKb*(Z - Zb)."""
    return tb + lkb * (z_m - zb_m)


def mesosphere_ellipse_temperature(z_m: float) -> float:
    """mesosphere_ellipse_temperature on 91-110 km."""
    ratio = (z_m - Z8) / A_SEMI
    inside = 1.0 - ratio * ratio
    if inside < 0.0:
        # Roundoff only; the published ellipse stays non-negative on [Z8, Z9].
        inside = 0.0
    return TC + A_ELLIPSE * math.sqrt(inside)


def exospheric_temperature(z_m: float) -> float:
    """exospheric_temperature from reduced_geopotential above Z10."""
    xi = reduced_geopotential(z_m, Z10)
    return TINF - (TINF - T10) * math.exp(-LAMBDA * xi)


def kinetic_temperature(z_m: float) -> float:
    """Kinetic temperature on the four-segment 1976 profile."""
    name = segment_name(z_m)
    if name == SEGMENT_MESOPAUSE:
        return kinetic_temperature_linear(T7, 0.0, z_m, Z7)
    if name == SEGMENT_ELLIPSE:
        return mesosphere_ellipse_temperature(z_m)
    if name == SEGMENT_LINEAR:
        return kinetic_temperature_linear(T9, LK9, z_m, Z9)
    return exospheric_temperature(z_m)


def atmosphere(z_m: float) -> dict[str, float | str]:
    temp = kinetic_temperature(z_m)
    if not math.isfinite(temp) or temp <= 0.0:
        raise ValueError("kinetic temperature is not positive")
    return {
        "Z": z_m,
        "T": temp,
        "segment": segment_name(z_m),
    }


def emit(state: dict[str, float | str], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "1976 U.S. Standard Atmosphere kinetic temperature")
    print_kv("Z_m", state["Z"])
    print_kv("T_K", state["T"])
    print_kv("segment", state["segment"])
    if graph is not None:
        print_kv("graph", str(graph))


def profile_grid() -> list[float]:
    """Geometric altitudes spanning 86-1000 km, denser below 200 km."""
    points: list[float] = []
    for i in range(N_CURVE):
        # Piecewise-linear mapping: half the samples below 200 km.
        frac = i / (N_CURVE - 1)
        if frac <= 0.5:
            local = frac / 0.5
            z_m = Z_MIN + local * (200000.0 - Z_MIN)
        else:
            local = (frac - 0.5) / 0.5
            z_m = 200000.0 + local * (Z_MAX - 200000.0)
        points.append(z_m)
    if points[0] != Z_MIN:
        points[0] = Z_MIN
    if points[-1] != Z_MAX:
        points[-1] = Z_MAX
    # Exact breakpoints so the curve hits the published joins.
    for zb in (Z7, Z8, Z9, Z10):
        if zb not in points:
            points.append(zb)
    points.sort()
    return points


def write_plot(state: dict[str, float | str], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    z_grid = profile_grid()
    t_grid = [kinetic_temperature(z) for z in z_grid]
    z_km = [z / 1000.0 for z in z_grid]
    z_user = float(state["Z"]) / 1000.0
    t_user = float(state["T"])

    fig, ax = plt.subplots(1, 1, figsize=(6.5, 7.0))
    ax.plot(t_grid, z_km, color="C0", label=r"$T(Z)$")
    for zb_km, label in (
        (Z8 / 1000.0, "91 km"),
        (Z9 / 1000.0, "110 km"),
        (Z10 / 1000.0, "120 km"),
    ):
        ax.axhline(zb_km, color="0.75", linestyle="--", linewidth=0.8)
        ax.text(
            TINF - 40.0,
            zb_km,
            label,
            va="bottom",
            ha="right",
            fontsize=8,
            color="0.45",
        )
    ax.plot(t_user, z_user, "s", color="C3", label="input altitude")
    ax.axhline(z_user, color="0.55", linestyle=":", linewidth=0.9)
    ax.axvline(t_user, color="0.55", linestyle=":", linewidth=0.9)
    ax.set_xlabel(r"Kinetic temperature $T$ [K]")
    ax.set_ylabel(r"Geometric altitude $Z$ [km]")
    ax.set_xlim(150.0, 1050.0)
    ax.set_ylim(Z_MIN / 1000.0, Z_MAX / 1000.0)
    ax.legend(loc="upper left", frameon=False)
    ax.grid(True, alpha=0.3)
    fig.suptitle(PLOT_TITLE)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    base = atmosphere(Z_MIN)
    if not close(float(base["T"]), T7):
        return fail(f"86 km temperature is {base['T']}, expected {T7}")
    if base["segment"] != SEGMENT_MESOPAUSE:
        return fail("86 km is not mesopause")

    mid_meso = atmosphere(88500.0)
    if not close(float(mid_meso["T"]), T7):
        return fail("mesopause is not isothermal")
    if mid_meso["segment"] != SEGMENT_MESOPAUSE:
        return fail("88.5 km is not mesopause")

    join8 = atmosphere(Z8)
    if not close(float(join8["T"]), T7):
        return fail(f"91 km temperature is {join8['T']}, expected {T7}")
    if join8["segment"] != SEGMENT_ELLIPSE:
        return fail("91 km is not mesosphere_ellipse")

    # Ellipse identity at layer base: Tc + A = T7.
    if not close(TC + A_ELLIPSE, T7):
        return fail("ellipse constants do not recover T7 at Z8")

    join9 = atmosphere(Z9)
    if not close(float(join9["T"]), T9, tol=1e-6):
        return fail(f"110 km temperature is {join9['T']}, expected {T9}")
    if join9["segment"] != SEGMENT_LINEAR:
        return fail("110 km is not thermosphere_linear")

    # Mid-ellipse continuity of first derivative is by construction in 1976;
    # check a published interior point stays between T7 and T9.
    mid_ell = atmosphere(100000.0)
    if not (T7 < float(mid_ell["T"]) < T9):
        return fail("100 km temperature left the ellipse bounds")
    if mid_ell["segment"] != SEGMENT_ELLIPSE:
        return fail("100 km is not mesosphere_ellipse")

    join10 = atmosphere(Z10)
    if not close(float(join10["T"]), T10):
        return fail(f"120 km temperature is {join10['T']}, expected {T10}")
    if join10["segment"] != SEGMENT_EXOSPHERE:
        return fail("120 km is not exosphere")

    # Linear ramp identity from formulas checks: one_hundred_twenty_km.
    ramp = kinetic_temperature_linear(T9, LK9, Z10, Z9)
    if not close(ramp, T10):
        return fail("linear ramp does not reach 360 K at 120 km")

    # Bates layer at Z10 is T10; as Z grows, T approaches TINF from below.
    high = atmosphere(500000.0)
    top = atmosphere(Z_MAX)
    if not (T10 < float(high["T"]) < float(top["T"]) < TINF):
        return fail("exosphere temperature did not rise toward Tinf")
    if high["segment"] != SEGMENT_EXOSPHERE or top["segment"] != SEGMENT_EXOSPHERE:
        return fail("high altitudes are not exosphere")
    if abs(float(top["T"]) - TINF) > 1.0:
        return fail(f"1000 km temperature {top['T']} is not near Tinf")

    # Continuity of first derivative at 120 km: linear slope equals Bates slope.
    # dT/dZ linear = LK9. Bates: dT/dZ = (Tinf-T10)*lam*dxi/dZ at xi=0.
    # dxi/dZ at Z10 = (r0+Z10)/(r0+Z10) = 1, so dT/dZ = (Tinf-T10)*lam = LK9.
    if not close((TINF - T10) * LAMBDA, LK9):
        return fail("Bates lambda does not match LK9 continuity")

    try:
        require_altitude(Z_MIN - 1.0, "--alt")
        return fail("altitude below 86 km was accepted")
    except ValueError:
        pass
    try:
        require_altitude(Z_MAX + 1.0, "--alt")
        return fail("altitude above 1000 km was accepted")
    except ValueError:
        pass

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str]:
        sink = _Capture()
        old_out = sys.stdout
        sys.stdout = sink
        try:
            code = main(argv)
        finally:
            sys.stdout = old_out
        return code, "".join(sink.parts)

    code, text = capture(["--alt", "86000"])
    if code != 0:
        return fail(f"86 km main returned {code}")
    for key in ("T_K: 186.8673", "segment: mesopause", "Z_m: 86000"):
        if key not in text:
            return fail(f"86 km stdout missing {key}")
    if "p_Pa" in text or "rho_kg_m3" in text:
        return fail("pressure or density was printed")
    if "graph:" in text:
        return fail("plot path printed without --out")

    code, text = capture(["--alt", "120000"])
    if code != 0 or "segment: exosphere" not in text or "T_K: 360" not in text:
        return fail("120 km stdout is wrong")

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        code, text = capture(["--alt", "200000", "--out", str(path)])
        if code != 0:
            return fail(f"plot run returned {code}")
        if f"graph: {path}" not in text and f"graph: {path.resolve()}" not in text:
            # Accept either printed form of the path.
            if "graph:" not in text:
                return fail("plot run did not print graph")
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
        if atmosphere(200000.0)["segment"] != SEGMENT_EXOSPHERE:
            return fail("200 km is not exosphere")

    err = sys.stderr
    sys.stderr = _Capture()
    try:
        missing = main([])
    finally:
        sys.stderr = err
    if missing != 2:
        return fail("missing altitude was accepted")

    print("check: pass")
    print_kv("T_K_86km", base["T"])
    print_kv("T_K_110km", join9["T"])
    print_kv("T_K_120km", join10["T"])
    print_kv("T_K_1000km", top["T"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "1976 kinetic temperature at a geometric altitude from 86 km "
            "through 1000 km."
        )
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional PNG path for temperature versus altitude",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.alt is None:
        print("error: requires --alt", file=sys.stderr)
        return 2
    try:
        state = atmosphere(require_altitude(args.alt, "--alt"))
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    graph: Path | None = None
    if args.out is not None:
        out_path = args.out
        try:
            write_plot(state, out_path)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = out_path

    emit(state, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
