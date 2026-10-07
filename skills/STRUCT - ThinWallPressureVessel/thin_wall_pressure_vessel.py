#!/usr/bin/env python3
"""Thin-wall membrane stress for a closed cylinder or a sphere.

cylinder_hoop_stress is sigma_h = p*R/t.
cylinder_longitudinal_stress is sigma_l = p*R/(2*t).
sphere_membrane_stress is sigma = p*R/(2*t).
thin_wall_hoop_thickness and thin_wall_membrane_thickness are the walls
for zero margin on the governing stress. margin_of_safety is
allowable/design - 1.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Thin-wall pressure vessel"
N_CURVE = 201
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "thin-wall membrane theory; thickness small compared with the radius; "
    "closed ends; no openings, welds, discontinuities, or buckling; "
    "cylinder_hoop_stress sigma_h = p*R/t; "
    "cylinder_longitudinal_stress sigma_l = p*R/(2*t); "
    "sphere_membrane_stress sigma = p*R/(2*t); "
    "governing stress is hoop for a cylinder and the membrane stress for a sphere; "
    "thin_wall_hoop_thickness t = p*R/allowable; "
    "thin_wall_membrane_thickness t = p*R/(2*allowable); "
    "margin_of_safety MS = allowable/design - 1 on the governing stress"
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


def hoop_stress(pressure: float, radius: float, thickness: float) -> float:
    """cylinder_hoop_stress."""
    return pressure * radius / thickness


def longitudinal_stress(pressure: float, radius: float, thickness: float) -> float:
    """cylinder_longitudinal_stress."""
    return pressure * radius / (2.0 * thickness)


def sphere_stress(pressure: float, radius: float, thickness: float) -> float:
    """sphere_membrane_stress."""
    return pressure * radius / (2.0 * thickness)


def hoop_thickness(pressure: float, radius: float, allowable: float) -> float:
    """thin_wall_hoop_thickness."""
    return pressure * radius / allowable


def membrane_thickness(pressure: float, radius: float, allowable: float) -> float:
    """thin_wall_membrane_thickness."""
    return pressure * radius / (2.0 * allowable)


def margin_of_safety(allowable: float, design: float) -> float:
    """margin_of_safety."""
    return allowable / design - 1.0


def evaluate(
    pressure: float,
    radius: float,
    shape: str,
    thickness: float | None,
    allowable: float | None,
) -> dict[str, float | str]:
    require_positive("pressure", pressure)
    require_positive("radius", radius)
    kind = shape.strip().lower()
    if kind not in {"cylinder", "sphere"}:
        raise ValueError("--shape must be cylinder or sphere")
    if thickness is None and allowable is None:
        raise ValueError("pass --thickness, or --allowable, or both")
    if thickness is not None:
        require_positive("thickness", thickness)
    if allowable is not None:
        require_positive("allowable stress", allowable)

    if kind == "cylinder":
        t_zero = None if allowable is None else hoop_thickness(pressure, radius, allowable)
        t_use = float(thickness) if thickness is not None else float(t_zero)
        sigma_h = hoop_stress(pressure, radius, t_use)
        sigma_l = longitudinal_stress(pressure, radius, t_use)
        result: dict[str, float | str] = {
            "shape": kind,
            "p_Pa": pressure,
            "R_m": radius,
            "t_m": t_use,
            "governing": "hoop",
            "sigma_hoop_Pa": sigma_h,
            "sigma_long_Pa": sigma_l,
        }
        design = sigma_h
    else:
        t_zero = None if allowable is None else membrane_thickness(pressure, radius, allowable)
        t_use = float(thickness) if thickness is not None else float(t_zero)
        sigma = sphere_stress(pressure, radius, t_use)
        result = {
            "shape": kind,
            "p_Pa": pressure,
            "R_m": radius,
            "t_m": t_use,
            "governing": "membrane",
            "sigma_Pa": sigma,
        }
        design = sigma
    if allowable is not None:
        result["allowable_Pa"] = allowable
        result["t_zero_ms_m"] = float(t_zero)
        if thickness is not None:
            result["margin_of_safety"] = margin_of_safety(allowable, design)
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
        raise ValueError("matplotlib is required to plot thin-wall stress") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    pressure = float(result["p_Pa"])
    radius = float(result["R_m"])
    thickness = float(result["t_m"])
    radii = linspace(0.2 * radius, 1.8 * radius, N_CURVE)
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    if result["shape"] == "cylinder":
        stresses = [hoop_stress(pressure, r, thickness) for r in radii]
        ax.plot(radii, stresses, color="#1a5276", linewidth=1.8, label=r"hoop $\sigma_h$")
        ax.plot(
            radius,
            float(result["sigma_hoop_Pa"]),
            "s",
            color="#1a5276",
            markersize=7,
            zorder=5,
            label="operating point",
        )
        ax.set_ylabel("hoop stress (Pa)")
    else:
        stresses = [sphere_stress(pressure, r, thickness) for r in radii]
        ax.plot(radii, stresses, color="#1a5276", linewidth=1.8, label=r"membrane $\sigma$")
        ax.plot(
            radius,
            float(result["sigma_Pa"]),
            "s",
            color="#1a5276",
            markersize=7,
            zorder=5,
            label="operating point",
        )
        ax.set_ylabel("membrane stress (Pa)")
    if "allowable_Pa" in result:
        ax.axhline(
            float(result["allowable_Pa"]),
            color="#c0392b",
            linestyle="--",
            linewidth=1.4,
            label="allowable",
        )
    ax.set_xlabel("radius (m)")
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
    print_kv("shape", result["shape"])
    print_kv("p_Pa", result["p_Pa"])
    print_kv("R_m", result["R_m"])
    print_kv("t_m", result["t_m"])
    print_kv("governing", result["governing"])
    if result["shape"] == "cylinder":
        print_kv("sigma_hoop_Pa", result["sigma_hoop_Pa"])
        print_kv("sigma_long_Pa", result["sigma_long_Pa"])
    else:
        print_kv("sigma_Pa", result["sigma_Pa"])
    if "allowable_Pa" in result:
        print_kv("allowable_Pa", result["allowable_Pa"])
        print_kv("t_zero_ms_m", result["t_zero_ms_m"])
    if "margin_of_safety" in result:
        print_kv("margin_of_safety", result["margin_of_safety"])
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
    if not close(hoop_stress(1000.0, 0.5, 0.01), 50000.0):
        return fail("cylinder hoop")
    if not close(longitudinal_stress(1000.0, 0.5, 0.01), 25000.0):
        return fail("cylinder longitudinal is not half the hoop")
    if not close(sphere_stress(1000.0, 0.5, 0.01), 25000.0):
        return fail("sphere membrane")
    if not close(hoop_thickness(1000.0, 0.5, 50000.0), 0.01):
        return fail("zero-margin cylinder wall")
    if not close(membrane_thickness(1000.0, 0.5, 25000.0), 0.01):
        return fail("zero-margin sphere wall")
    if not close(margin_of_safety(50000.0, 40000.0), 0.25):
        return fail("margin")

    sized = evaluate(1000.0, 0.5, "cylinder", None, 50000.0)
    if not close(float(sized["t_m"]), 0.01):
        return fail("sizing did not return the zero-margin wall")
    both = evaluate(1000.0, 0.5, "cylinder", 0.01, 1.0e5)
    if not close(float(both["margin_of_safety"]), 1.0):
        return fail("cylinder margin")
    sphere = evaluate(1000.0, 0.5, "sphere", 0.01, None)
    if not close(float(sphere["sigma_Pa"]), 25000.0):
        return fail("sphere evaluate")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "wall.png"
        code, text, err = capture(
            ["--p", "1000", "--radius", "0.5", "--shape", "cylinder", "--thickness", "0.01", "--allowable", "100000", "--out", str(png)]
        )
        if code != 0:
            return fail(f"cylinder run failed: {err}")
        if "sigma_hoop_Pa: 50000" not in text or "margin_of_safety: 1" not in text:
            return fail("cylinder stdout")
        if not png.is_file() or not png.read_bytes().startswith(b"\x89PNG"):
            return fail("PNG")
        code, text, err = capture(
            ["--p", "1000", "--radius", "0.5", "--shape", "sphere", "--allowable", "25000"]
        )
        if code != 0:
            return fail(f"sphere sizing failed: {err}")
        if "t_m: 0.01" not in text:
            return fail("sphere zero-margin thickness")
        if "margin_of_safety:" in text:
            return fail("sizing without a given wall printed a margin")
        code, _text, _err = capture(["--p", "1000", "--radius", "0.5", "--shape", "cylinder"])
        if code == 0:
            return fail("accepted a run with neither thickness nor allowable")

    print("check: pass")
    print_kv("sigma_hoop_Pa", both["sigma_hoop_Pa"])
    print_kv("margin_of_safety", both["margin_of_safety"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thin-wall membrane stress for a closed cylinder or a sphere."
    )
    parser.add_argument("--p", type=float, default=None, help="internal pressure [Pa]")
    parser.add_argument("--radius", type=float, default=None, help="wall radius [m]")
    parser.add_argument("--shape", type=str, default=None, help="cylinder or sphere")
    parser.add_argument("--thickness", type=float, default=None, help="wall thickness [m]")
    parser.add_argument("--allowable", type=float, default=None, help="allowable membrane stress [Pa]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.p is None or args.radius is None or args.shape is None:
        print("error: requires --p, --radius, and --shape", file=sys.stderr)
        return 2
    try:
        result = evaluate(args.p, args.radius, args.shape, args.thickness, args.allowable)
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
