#!/usr/bin/env python3
"""Polytropic blowdown of a pressure-fed ullage.

pressurant_blowdown_pressure is p2 = p0*(V0/V2)**n with V2 = V0 + V_expelled.
pressurant_mass is p*V/(R_specific*T). The end temperature follows the fixed-mass polytropic ratio.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Pressurant blowdown"
N_CURVE = 201
ASSUMPTIONS = (
    "fixed pressurant mass in a growing ullage; "
    "pressurant_blowdown_pressure p2 = p0*(V0/V2)**n with V2 = V0 + V_expelled; "
    "default n = 1 is isothermal perfect gas; a supplied n is used as stated and gamma is not chosen; "
    "pressurant_mass m = p*V/(R_specific*T) when both T and R are given; "
    "T2 = T*(p2/p0)**((n-1)/n) so the printed end mass matches the fixed charge; "
    "no regulator, bottle recharge, wall thickness, or tank mass"
)


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


def end_ullage(v0: float, expelled: float) -> float:
    return v0 + expelled


def blowdown_pressure(p0: float, v0: float, v2: float, n: float) -> float:
    """pressurant_blowdown_pressure."""
    return p0 * (v0 / v2) ** n


def pressurant_mass(pressure: float, volume: float, r_specific: float, temperature: float) -> float:
    """pressurant_mass."""
    return pressure * volume / (r_specific * temperature)


def end_temperature(temperature: float, p0: float, p2: float, n: float) -> float:
    """Polytropic temperature of a fixed pressurant mass. NASA SP-125."""
    return temperature * (p2 / p0) ** ((n - 1.0) / n)


def evaluate(
    p0: float,
    v0: float,
    expelled: float,
    n: float,
    p_min: float | None,
    temperature: float | None,
    r_specific: float | None,
) -> dict[str, float | str]:
    require_positive("pad pressure", p0)
    require_positive("initial ullage", v0)
    if not math.isfinite(expelled) or expelled < 0.0:
        raise ValueError("expelled volume must be finite and >= 0")
    require_positive("polytropic exponent", n)
    v2 = end_ullage(v0, expelled)
    p2 = blowdown_pressure(p0, v0, v2, n)
    result: dict[str, float | str] = {
        "p0_Pa": p0,
        "V0_m3": v0,
        "V_expelled_m3": expelled,
        "n": n,
        "V2_m3": v2,
        "p2_Pa": p2,
        "blowdown_ratio": p2 / p0,
    }
    if p_min is not None:
        if not math.isfinite(p_min) or p_min < 0.0:
            raise ValueError("pressure floor must be finite and >= 0")
        result["p_min_Pa"] = p_min
        result["above_floor"] = "yes" if p2 >= p_min else "no"
    if (temperature is None) != (r_specific is None):
        raise ValueError("pass both --temperature and --r-specific to print pressurant mass")
    if temperature is not None and r_specific is not None:
        require_positive("temperature", temperature)
        require_positive("specific gas constant", r_specific)
        result["T_K"] = temperature
        result["T2_K"] = end_temperature(temperature, p0, p2, n)
        result["R_specific_J_kgK"] = r_specific
        result["m0_kg"] = pressurant_mass(p0, v0, r_specific, temperature)
        result["m2_kg"] = pressurant_mass(p2, v2, r_specific, float(result["T2_K"]))
    return result


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot blowdown pressure") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    p0 = float(result["p0_Pa"])
    v0 = float(result["V0_m3"])
    expelled = float(result["V_expelled_m3"])
    n = float(result["n"])
    span = linspace(0.0, expelled if expelled > 0.0 else v0, N_CURVE)
    pressures = [blowdown_pressure(p0, v0, end_ullage(v0, item), n) for item in span]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(span, pressures, color="#1a5276", linewidth=1.8, label="ullage pressure")
    ax.plot(expelled, float(result["p2_Pa"]), "s", color="#1a5276", markersize=7, label="end state")
    ax.set_xlabel("expelled volume (m$^3$)")
    ax.set_ylabel("ullage pressure (Pa)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: dict[str, float | str], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "p0_Pa",
        "V0_m3",
        "V_expelled_m3",
        "n",
        "V2_m3",
        "p2_Pa",
        "blowdown_ratio",
        "p_min_Pa",
        "above_floor",
        "T_K",
        "T2_K",
        "R_specific_J_kgK",
        "m0_kg",
        "m2_kg",
    ):
        if key in result:
            print_kv(key, result[key])
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def capture(argv: list[str]) -> tuple[int, str, str]:
    from io import StringIO

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def run_check() -> int:
    p2 = blowdown_pressure(2.0e6, 0.1, 0.2, 1.0)
    if not close(p2, 1.0e6):
        return fail("isothermal pressure")
    p_ad = blowdown_pressure(1.0e6, 1.0, 2.0, 1.4)
    if not close(p_ad, 1.0e6 * (0.5**1.4)):
        return fail("polytropic pressure")
    if not close(pressurant_mass(300.0, 2.0, 3.0, 200.0), 1.0):
        return fail("mass")
    result = evaluate(2.0e6, 0.1, 0.1, 1.0, 0.5e6, 300.0, 2077.0)
    if result["above_floor"] != "yes":
        return fail("floor")
    low = evaluate(2.0e6, 0.1, 0.1, 1.0, 1.5e6, None, None)
    if low["above_floor"] != "no":
        return fail("below floor")
    adiabatic = evaluate(2.0e6, 0.1, 0.1, 1.4, None, 300.0, 2077.0)
    if not close(float(adiabatic["m0_kg"]), float(adiabatic["m2_kg"])):
        return fail("adiabatic mass is not fixed")
    if not close(float(adiabatic["T2_K"]), 300.0 * (0.5 ** 0.4)):
        return fail("adiabatic temperature")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "blowdown.png"
        code, text, err = capture(
            [
                "--p0",
                "2e6",
                "--v0",
                "0.1",
                "--v-expelled",
                "0.1",
                "--n",
                "1",
                "--p-min",
                "5e5",
                "--temperature",
                "300",
                "--r-specific",
                "2077",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"run failed: {err}")
        if "p2_Pa: 1000000" not in text or "above_floor: yes" not in text:
            return fail("stdout")
        if "m0_kg:" not in text or "blowdown_ratio: 0.5" not in text:
            return fail("mass stdout")
        if not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, _text, err = capture(["--p0", "1e6", "--v0", "0.1", "--v-expelled", "0.1", "--temperature", "300"])
        if code == 0:
            return fail("partial gas constant was accepted")

    print("check: pass")
    print_kv("p2_Pa", p2)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Polytropic pressurant blowdown pressure.")
    parser.add_argument("--p0", type=float, default=None, help="initial ullage pressure [Pa]")
    parser.add_argument("--v0", type=float, default=None, help="initial ullage volume [m^3]")
    parser.add_argument("--v-expelled", type=float, default=None, help="liquid volume that leaves [m^3]")
    parser.add_argument("--n", type=float, default=1.0, help="polytropic exponent; default 1 (isothermal)")
    parser.add_argument("--p-min", type=float, default=None, help="pressure floor [Pa]")
    parser.add_argument("--temperature", type=float, default=None, help="gas temperature for mass [K]")
    parser.add_argument("--r-specific", type=float, default=None, help="specific gas constant [J/(kg K)]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.p0 is None or args.v0 is None or args.v_expelled is None:
        print("error: requires --p0, --v0, and --v-expelled", file=sys.stderr)
        return 2
    try:
        result = evaluate(
            args.p0,
            args.v0,
            args.v_expelled,
            args.n,
            args.p_min,
            args.temperature,
            args.r_specific,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            write_plot(result, Path(args.out).resolve())
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = Path(args.out).resolve()
    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
