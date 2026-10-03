#!/usr/bin/env python3
"""Positive stall boundary and corner speed on a V-n diagram.

The positive stall boundary is stall_speed with W replaced by n*W, which is
the same statement as load_factor at lift_force with CLmax and
freestream_dynamic_pressure. The corner speed is that stall speed at the
positive limit load factor. Speeds on the plot are stall_speed at 1976
sea-level density. For incompressible dynamic pressure that speed is the
equivalent airspeed. True airspeeds use the supplied density.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "V-n diagram"
# Display end of the limit-load lines. Not a dive speed.
PLOT_END_FACTOR = 1.5
N_STALL = 201

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "unaccelerated flight; positive stall boundary is stall_speed with W "
    "replaced by n*W, equivalent to load_factor n = L/W at lift_force "
    "L = CLmax*q*S and freestream_dynamic_pressure q = 0.5*rho*V**2; "
    "corner speed is that stall speed at the positive limit load factor; "
    "equivalent airspeed is equivalent_airspeed, Ve = V*(rho/rho_sl)**0.5, "
    "which is stall_speed at 1976 sea-level density because q is unchanged "
    "when rho*V**2 = rho_sl*Ve**2; the figure uses that sea-level density; "
    "true airspeeds "
    "use the supplied density; the negative stall boundary is omitted "
    "because stall_speed has no CLmin and n*W must stay positive; the "
    "negative line is only the limit load factor; the plot ends at "
    f"{PLOT_END_FACTOR:g} times the positive corner equivalent airspeed "
    "and that end is not a dive speed; weight is a force, so g0 is not applied"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def load_atmosphere():
    folder = str(ATMOS_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from standard_1976 import atmosphere
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for sea-level density"
        ) from exc
    return atmosphere


def stall_speed(weight: float, rho: float, area: float, clmax: float, load_factor: float) -> float:
    """stall_speed with W replaced by n*W. n = 0 returns 0."""
    return math.sqrt(2.0 * load_factor * weight / (rho * area * clmax))


def dynamic_pressure(rho: float, speed: float) -> float:
    """freestream_dynamic_pressure."""
    return 0.5 * rho * speed * speed


def load_factor(lift: float, weight: float) -> float:
    """load_factor."""
    return lift / weight


def diagram(
    weight: float,
    area: float,
    clmax: float,
    n_pos: float,
    rho: float,
    rho_sl: float,
) -> dict[str, float]:
    v_stall = stall_speed(weight, rho, area, clmax, 1.0)
    v_stall_eas = stall_speed(weight, rho_sl, area, clmax, 1.0)
    v_corner = stall_speed(weight, rho, area, clmax, n_pos)
    v_corner_eas = stall_speed(weight, rho_sl, area, clmax, n_pos)
    q_corner = dynamic_pressure(rho, v_corner)
    n_corner = load_factor(clmax * q_corner * area, weight)
    return {
        "V_stall_m_s": v_stall,
        "V_stall_eas_m_s": v_stall_eas,
        "V_corner_m_s": v_corner,
        "V_corner_eas_m_s": v_corner_eas,
        "q_corner_Pa": q_corner,
        "n_corner": n_corner,
        "V_plot_max_eas_m_s": PLOT_END_FACTOR * v_corner_eas,
    }


def stall_boundary_eas(
    weight: float,
    area: float,
    clmax: float,
    n_pos: float,
    rho_sl: float,
) -> tuple[list[float], list[float]]:
    """Equivalent-airspeed stall boundary from n = 0 through n_pos."""
    speeds: list[float] = []
    loads: list[float] = []
    for i in range(N_STALL):
        n = n_pos * i / (N_STALL - 1)
        speeds.append(stall_speed(weight, rho_sl, area, clmax, n))
        loads.append(n)
    return speeds, loads


def warnings_for(n_pos: float) -> list[str]:
    notes: list[str] = []
    if n_pos < 1.0:
        notes.append(
            f"positive limit load factor {n_pos:.6g} is below 1; "
            "level flight exceeds it"
        )
    return notes


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the V-n diagram") from exc
    return plt


def plot_diagram(
    path: Path,
    weight: float,
    area: float,
    clmax: float,
    n_pos: float,
    n_neg: float,
    rho_sl: float,
    result: dict[str, float],
) -> None:
    plt = ensure_matplotlib()
    speeds, loads = stall_boundary_eas(weight, area, clmax, n_pos, rho_sl)
    v_corner = result["V_corner_eas_m_s"]
    v_max = result["V_plot_max_eas_m_s"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(speeds, loads, color="#1a5276", linewidth=1.8, label="stall boundary")
    ax.plot(
        [v_corner, v_max],
        [n_pos, n_pos],
        color="#c0392b",
        linewidth=1.6,
        label="positive limit load factor",
    )
    ax.plot(
        [0.0, v_max],
        [n_neg, n_neg],
        color="#c0392b",
        linestyle="--",
        linewidth=1.4,
        label="negative limit load factor",
    )
    ax.plot(
        v_corner,
        n_pos,
        "s",
        color="#c0392b",
        markersize=7,
        zorder=5,
        label="corner speed",
    )
    if n_pos > 1.0:
        ax.plot(
            result["V_stall_eas_m_s"],
            1.0,
            "o",
            color="#1a5276",
            markersize=6,
            zorder=5,
            label="1-g stall",
        )
    ax.axhline(1.0, color="#7f8c8d", linestyle=":", linewidth=1.0, label="level flight")
    ax.set_xlim(0.0, v_max)
    y_lo = n_neg
    y_hi = max(n_pos, 1.0)
    pad = 0.08 * (y_hi - y_lo)
    ax.set_ylim(y_lo - pad, y_hi + pad)
    ax.set_xlabel("equivalent airspeed (m/s)")
    ax.set_ylabel("load factor")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(
    weight: float,
    area: float,
    clmax: float,
    n_pos: float,
    n_neg: float,
    rho: float,
    rho_sl: float,
    result: dict[str, float],
    notes: list[str],
    path: Path,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("weight_N", weight)
    print_kv("area_m2", area)
    print_kv("CLmax", clmax)
    print_kv("n_pos", n_pos)
    print_kv("n_neg", n_neg)
    print_kv("rho_kg_m3", rho)
    print_kv("rho_sl_kg_m3", rho_sl)
    print_kv("rho_sl_source", "1976-sea-level")
    print_kv("V_stall_m_s", result["V_stall_m_s"])
    print_kv("V_stall_eas_m_s", result["V_stall_eas_m_s"])
    print_kv("V_corner_m_s", result["V_corner_m_s"])
    print_kv("V_corner_eas_m_s", result["V_corner_eas_m_s"])
    print_kv("n_corner", result["n_corner"])
    print_kv("q_corner_Pa", result["q_corner_Pa"])
    print_kv("plot_end_factor", PLOT_END_FACTOR)
    print_kv("V_plot_max_eas_m_s", result["V_plot_max_eas_m_s"])
    print_kv("graph", str(path))
    if notes:
        print_kv("warning", "; ".join(notes))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    atmosphere = load_atmosphere()
    rho_sl = atmosphere(0.0)["rho"]
    weight = 10000.0
    area = 16.0
    clmax = 1.6
    n_pos = 3.8
    n_neg = -1.52
    rho = rho_sl
    result = diagram(weight, area, clmax, n_pos, rho, rho_sl)
    v_stall = math.sqrt(2.0 * weight / (rho * area * clmax))
    v_corner = math.sqrt(2.0 * n_pos * weight / (rho * area * clmax))
    if near(result["V_stall_m_s"], v_stall, "1-g stall"):
        return 1
    if near(result["V_stall_eas_m_s"], v_stall, "sea-level equivalent stall"):
        return 1
    if near(result["V_corner_m_s"], v_corner, "corner speed"):
        return 1
    if near(result["V_corner_eas_m_s"], v_corner, "sea-level corner"):
        return 1
    if near(result["n_corner"], n_pos, "corner load factor"):
        return 1
    q = 0.5 * rho * v_corner**2
    if near(result["q_corner_Pa"], q, "corner dynamic pressure"):
        return 1
    if near(clmax * q * area / weight, n_pos, "lift over weight at corner"):
        return 1
    if near(result["V_plot_max_eas_m_s"], PLOT_END_FACTOR * v_corner, "plot end"):
        return 1

    high_rho = rho_sl * 0.3
    high = diagram(weight, area, clmax, n_pos, high_rho, rho_sl)
    if not high["V_stall_m_s"] > result["V_stall_m_s"]:
        return fail("true stall speed did not rise when density fell")
    if near(high["V_stall_eas_m_s"], result["V_stall_eas_m_s"], "EAS stall independent of density"):
        return 1
    if near(high["V_corner_eas_m_s"], result["V_corner_eas_m_s"], "EAS corner independent of density"):
        return 1
    ratio = math.sqrt(high_rho / rho_sl)
    if near(high["V_stall_eas_m_s"], high["V_stall_m_s"] * ratio, "EAS from true stall"):
        return 1
    if near(high["V_corner_eas_m_s"], high["V_corner_m_s"] * ratio, "EAS from true corner"):
        return 1
    if near(high["q_corner_Pa"], result["q_corner_Pa"], "corner dynamic pressure"):
        return 1

    speeds, loads = stall_boundary_eas(weight, area, clmax, n_pos, rho_sl)
    if len(speeds) != N_STALL or loads[0] != 0.0 or loads[-1] != n_pos:
        return fail("stall boundary did not run from n = 0 to n_pos")
    if near(speeds[0], 0.0, "stall boundary at n = 0"):
        return 1
    if near(speeds[-1], result["V_corner_eas_m_s"], "stall boundary at the corner"):
        return 1
    mid = len(speeds) // 2
    if near(loads[mid], stall_load_back(speeds[mid], rho_sl, area, clmax, weight), "boundary load"):
        return 1

    notes = warnings_for(0.8)
    if not any("below 1" in note for note in notes):
        return fail("limit below 1 produced no warning")
    if warnings_for(n_pos):
        return fail("limit above 1 produced a warning")

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
        out = str(Path(tmp) / "vn.png")
        code, text, err = capture(
            [
                "--weight",
                "10000",
                "--area",
                "16",
                "--clmax",
                "1.6",
                "--n-pos",
                "3.8",
                "--n-neg",
                "-1.52",
                "--rho",
                str(rho_sl),
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: V-n diagram",
            "V_stall_m_s:",
            "V_stall_eas_m_s:",
            "V_corner_m_s:",
            "V_corner_eas_m_s:",
            "n_corner:",
            "rho_sl_source: 1976-sea-level",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "warning:" in text:
            return fail("clean case printed a warning")

        code, text, err = capture(
            [
                "--weight",
                "10000",
                "--area",
                "16",
                "--clmax",
                "1.6",
                "--n-pos",
                "0.8",
                "--n-neg",
                "-1",
                "--rho",
                str(rho_sl),
                "--out",
                out,
            ]
        )
        if code != 0 or "warning:" not in text:
            return fail("limit below 1 did not warn on stdout")

    code, _text, err = capture(
        ["--weight", "10000", "--area", "16", "--clmax", "1.6", "--n-pos", "3.8", "--rho", "1.2"]
    )
    if code != 2 or "--n-neg" not in err:
        return fail("missing negative limit was accepted")
    code, _text, err = capture(
        [
            "--weight",
            "10000",
            "--area",
            "16",
            "--clmax",
            "1.6",
            "--n-pos",
            "-1",
            "--n-neg",
            "-1.5",
            "--rho",
            "1.2",
        ]
    )
    if code != 2:
        return fail("negative positive-limit was accepted")
    code, _text, err = capture(
        [
            "--weight",
            "10000",
            "--area",
            "16",
            "--clmax",
            "1.6",
            "--n-pos",
            "3.8",
            "--n-neg",
            "1.5",
            "--rho",
            "1.2",
        ]
    )
    if code != 2:
        return fail("positive negative-limit was accepted")
    code, _text, _err = capture([])
    if code != 2:
        return fail("missing inputs were accepted")

    print("check: pass")
    print_kv("V_stall_m_s", result["V_stall_m_s"])
    print_kv("V_corner_m_s", result["V_corner_m_s"])
    print_kv("V_corner_eas_m_s", result["V_corner_eas_m_s"])
    print_kv("n_corner", result["n_corner"])
    return 0


def stall_load_back(speed: float, rho: float, area: float, clmax: float, weight: float) -> float:
    """Load factor on the stall boundary from lift_force and load_factor."""
    return load_factor(clmax * dynamic_pressure(rho, speed) * area, weight)


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def validate(
    weight: float,
    area: float,
    clmax: float,
    n_pos: float,
    n_neg: float,
    rho: float,
) -> None:
    require_positive("weight", weight)
    require_positive("wing area", area)
    require_positive("CLmax", clmax)
    require_positive("density", rho)
    if not math.isfinite(n_pos) or n_pos <= 0.0:
        raise ValueError("positive limit load factor must be finite and > 0")
    if not math.isfinite(n_neg) or n_neg >= 0.0:
        raise ValueError("negative limit load factor must be finite and < 0")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stall boundary and corner speed, with load factor plotted "
            "against equivalent airspeed."
        )
    )
    parser.add_argument("--weight", type=float, default=None, help="weight W [N]")
    parser.add_argument("--area", type=float, default=None, help="wing planform area S [m^2]")
    parser.add_argument("--clmax", type=float, default=None, help="maximum lift coefficient CLmax")
    parser.add_argument("--n-pos", type=float, default=None, help="positive limit load factor")
    parser.add_argument("--n-neg", type=float, default=None, help="negative limit load factor")
    parser.add_argument("--rho", type=float, default=None, help="air density [kg/m^3]")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--weight": args.weight,
        "--area": args.area,
        "--clmax": args.clmax,
        "--n-pos": args.n_pos,
        "--n-neg": args.n_neg,
        "--rho": args.rho,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --weight, --area, --clmax, --n-pos, --n-neg, and --rho; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    try:
        validate(args.weight, args.area, args.clmax, args.n_pos, args.n_neg, args.rho)
        atmosphere = load_atmosphere()
        rho_sl = atmosphere(0.0)["rho"]
        result = diagram(args.weight, args.area, args.clmax, args.n_pos, args.rho, rho_sl)
        out_path = Path(args.out) if args.out else SKILL_DIR / "vn_diagram.png"
        out_path = out_path.resolve()
        plot_diagram(
            out_path,
            args.weight,
            args.area,
            args.clmax,
            args.n_pos,
            args.n_neg,
            rho_sl,
            result,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    notes = warnings_for(args.n_pos)
    emit(
        args.weight,
        args.area,
        args.clmax,
        args.n_pos,
        args.n_neg,
        args.rho,
        rho_sl,
        result,
        notes,
        out_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
