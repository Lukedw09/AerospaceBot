#!/usr/bin/env python3
"""Elastic Euler column buckling load, stress, and slenderness.

euler_critical_load is P_cr = pi**2*E*I/(K*L)**2.
euler_critical_load_fixity is P_cr = C*pi**2*E*I/L**2 with C = 1/K**2.
effective_column_length is L' = K*L.
end_fixity_coefficient is C = 1/K**2.
radius_of_gyration is rho = sqrt(I/A).
column_slenderness is K*L/rho.
euler_critical_stress is sigma_cr = P_cr/A = pi**2*E/(K*L/rho)**2.
Optional compressive yield compares sigma_cr to yield for Euler validity.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Euler column buckling"
PLOT_LENGTH_START = 0.5
PLOT_LENGTH_END = 1.5
PLOT_Y_PAD = 1.1
N_CURVE = 201
DEFAULT_K = 1.0

SKILL_DIR = Path(__file__).resolve().parent

# Classical ideal ends: K = L'/L = 1/sqrt(C). Fixed-pinned uses C = 2
# (AFFDL table lists 2.05 for the exact transcendental root).
CLASSICAL_K = {
    "pinned-pinned": 1.0,
    "fixed-fixed": 0.5,
    "fixed-pinned": 1.0 / math.sqrt(2.0),
    "fixed-free": 2.0,
}

ASSUMPTIONS = (
    "elastic Euler only; concentric axial compression; initially straight "
    "prismatic member; stable cross section (no local crippling); "
    "homogeneous isotropic linear-elastic material; "
    "euler_critical_load P_cr = pi**2*E*I/(K*L)**2; "
    "euler_critical_load_fixity P_cr = C*pi**2*E*I/L**2 with "
    "end_fixity_coefficient C = 1/K**2; "
    "effective_column_length L_eff = K*L; "
    "optional radius_of_gyration rho = sqrt(I/A), "
    "column_slenderness K*L/rho, and "
    "euler_critical_stress sigma_cr = P_cr/A; "
    "optional compressive yield: euler_valid when sigma_cr < yield, else "
    "yield_first; short-column, tangent-modulus, Johnson, and eccentricity "
    "formulas are omitted; "
    f"default end-fix factor K = {DEFAULT_K:g} (pinned-pinned)"
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


def resolve_k(k: float | None, ends: str | None) -> tuple[float, str]:
    if ends is not None:
        key = ends.strip().lower()
        if key not in CLASSICAL_K:
            allowed = ", ".join(sorted(CLASSICAL_K))
            raise ValueError(f"unknown --ends {ends!r}; use one of: {allowed}")
        classical = CLASSICAL_K[key]
        if k is not None and not close(float(k), classical):
            raise ValueError(
                f"--k {k:g} disagrees with --ends {key} (K = {classical:g})"
            )
        return classical, key
    if k is None:
        return DEFAULT_K, "pinned-pinned"
    require_positive("end-fix factor", k)
    for name, value in CLASSICAL_K.items():
        if close(float(k), value):
            return float(k), name
    return float(k), "custom"


def effective_length(k: float, length: float) -> float:
    """effective_column_length: L' = K*L."""
    return k * length


def end_fixity_coefficient(k: float) -> float:
    """end_fixity_coefficient: C = 1/K**2."""
    return 1.0 / (k * k)


def euler_load(modulus: float, inertia: float, k: float, length: float) -> float:
    """euler_critical_load: P_cr = pi**2*E*I/(K*L)**2."""
    leff = effective_length(k, length)
    return (math.pi ** 2) * modulus * inertia / (leff * leff)


def euler_load_fixity(
    fixity: float, modulus: float, inertia: float, length: float
) -> float:
    """euler_critical_load_fixity: P_cr = C*pi**2*E*I/L**2."""
    return fixity * (math.pi ** 2) * modulus * inertia / (length * length)


def radius_of_gyration(inertia: float, area: float) -> float:
    """radius_of_gyration: rho = sqrt(I/A)."""
    return math.sqrt(inertia / area)


def column_slenderness(
    k: float, length: float, inertia: float, area: float
) -> float:
    """column_slenderness: K*L/rho."""
    return effective_length(k, length) / radius_of_gyration(inertia, area)


def euler_stress(
    modulus: float, k: float, length: float, inertia: float, area: float
) -> float:
    """euler_critical_stress: pi**2*E/(K*L/rho)**2."""
    slender = column_slenderness(k, length, inertia, area)
    return (math.pi ** 2) * modulus / (slender * slender)


def evaluate(
    modulus: float,
    inertia: float,
    length: float,
    k: float | None,
    ends: str | None,
    area: float | None,
    yield_stress: float | None,
) -> dict[str, float | str]:
    require_positive("Young's modulus", modulus)
    require_positive("second moment of area", inertia)
    require_positive("unsupported length", length)
    k_use, end_name = resolve_k(k, ends)
    fixity = end_fixity_coefficient(k_use)
    leff = effective_length(k_use, length)
    load = euler_load(modulus, inertia, k_use, length)
    load_c = euler_load_fixity(fixity, modulus, inertia, length)
    if not close(load, load_c):
        raise ValueError("K-form and C-form Euler loads disagree")

    result: dict[str, float | str] = {
        "E_Pa": modulus,
        "I_m4": inertia,
        "L_m": length,
        "K": k_use,
        "ends": end_name,
        "C": fixity,
        "L_eff_m": leff,
        "P_cr_N": load,
    }

    if area is not None:
        require_positive("cross-sectional area", area)
        rho = radius_of_gyration(inertia, area)
        slender = column_slenderness(k_use, length, inertia, area)
        stress = euler_stress(modulus, k_use, length, inertia, area)
        stress_from_load = load / area
        if not close(stress, stress_from_load):
            raise ValueError("P_cr/A and Euler stress disagree")
        result["A_m2"] = area
        result["rho_m"] = rho
        result["slenderness"] = slender
        result["sigma_cr_Pa"] = stress

    if yield_stress is not None:
        if area is None:
            raise ValueError("compressive yield requires --area")
        require_positive("compressive yield", yield_stress)
        stress = float(result["sigma_cr_Pa"])
        result["yield_Pa"] = yield_stress
        if stress < yield_stress:
            result["euler_regime"] = "valid_euler"
        else:
            result["euler_regime"] = "yield_first"

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
        raise ValueError("matplotlib is required to plot Euler buckling") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    modulus = float(result["E_Pa"])
    inertia = float(result["I_m4"])
    length = float(result["L_m"])
    k = float(result["K"])
    load = float(result["P_cr_N"])
    # Window around the operating length so 1/L**2 does not dominate near L = 0.
    l_min = PLOT_LENGTH_START * length
    l_max = PLOT_LENGTH_END * length
    lengths = linspace(l_min, l_max, N_CURVE)
    loads = [euler_load(modulus, inertia, k, L) for L in lengths]
    y_top = PLOT_Y_PAD * max(max(loads), load)

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(
        lengths,
        loads,
        color="#1a5276",
        linewidth=1.8,
        label=r"$P_{\mathrm{cr}}=\pi^{2}EI/(KL)^{2}$",
    )
    ax.plot(
        length,
        load,
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    if "yield_Pa" in result and "A_m2" in result:
        yield_load = float(result["yield_Pa"]) * float(result["A_m2"])
        ax.axhline(
            yield_load,
            color="#c0392b",
            linestyle="--",
            linewidth=1.5,
            label=r"$A\,\sigma_y$",
        )
        if yield_load <= y_top * 2.0:
            y_top = max(y_top, PLOT_Y_PAD * yield_load)
    ax.set_xlabel("unsupported length (m)")
    ax.set_ylabel("critical load (N)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(l_min, l_max)
    ax.set_ylim(0.0, y_top)
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
    print_kv("E_Pa", result["E_Pa"])
    print_kv("I_m4", result["I_m4"])
    print_kv("L_m", result["L_m"])
    print_kv("K", result["K"])
    print_kv("ends", result["ends"])
    print_kv("C", result["C"])
    print_kv("L_eff_m", result["L_eff_m"])
    print_kv("P_cr_N", result["P_cr_N"])
    if "A_m2" in result:
        print_kv("A_m2", result["A_m2"])
        print_kv("rho_m", result["rho_m"])
        print_kv("slenderness", result["slenderness"])
        print_kv("sigma_cr_Pa", result["sigma_cr_Pa"])
    if "yield_Pa" in result:
        print_kv("yield_Pa", result["yield_Pa"])
        print_kv("euler_regime", result["euler_regime"])
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    if not close(euler_load(1.0, 1.0, 1.0, 1.0), math.pi ** 2):
        return fail("unit pinned Euler load is not pi**2")
    if not close(euler_load_fixity(1.0, 1.0, 1.0, 1.0), math.pi ** 2):
        return fail("unit fixity Euler load is not pi**2")
    if not close(euler_load(1.0, 1.0, 0.5, 1.0), 4.0 * math.pi ** 2):
        return fail("fixed-fixed load is not 4*pi**2")
    if not close(end_fixity_coefficient(0.5), 4.0):
        return fail("fixed-fixed C is not 4")
    if not close(effective_length(0.5, 2.0), 1.0):
        return fail("effective length K*L mismatch")

    modulus = 2.0e11
    inertia = 1.0e-6
    length = 2.0
    area = 1.0e-3
    expected_load = (math.pi ** 2) * 5.0e4
    if not close(euler_load(modulus, inertia, 1.0, length), expected_load):
        return fail("steel sample load mismatch")
    rho = radius_of_gyration(inertia, area)
    if not close(rho, math.sqrt(1.0e-3)):
        return fail("radius of gyration mismatch")
    slender = column_slenderness(1.0, length, inertia, area)
    if not close(slender, length / rho):
        return fail("slenderness mismatch")
    stress = euler_stress(modulus, 1.0, length, inertia, area)
    if not close(stress, expected_load / area):
        return fail("critical stress mismatch")

    valid = evaluate(modulus, inertia, length, 1.0, None, area, 6.0e8)
    if valid["euler_regime"] != "valid_euler":
        return fail("high yield was not valid_euler")
    first = evaluate(modulus, inertia, length, 1.0, None, area, 2.5e8)
    if first["euler_regime"] != "yield_first":
        return fail("low yield was not yield_first")

    fixed = evaluate(modulus, inertia, length, None, "fixed-fixed", None, None)
    if not close(float(fixed["K"]), 0.5) or not close(float(fixed["C"]), 4.0):
        return fail("fixed-fixed ends did not set K and C")
    if not close(float(fixed["P_cr_N"]), 4.0 * expected_load):
        return fail("fixed-fixed load is not four times pinned")

    try:
        evaluate(modulus, inertia, length, 1.0, "fixed-fixed", None, None)
        return fail("disagreeing --k and --ends were accepted")
    except ValueError:
        pass
    try:
        evaluate(modulus, inertia, length, 1.0, None, None, 2.5e8)
        return fail("yield without area was accepted")
    except ValueError:
        pass
    try:
        evaluate(0.0, inertia, length, 1.0, None, None, None)
        return fail("zero modulus was accepted")
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
        out = str(Path(tmp) / "euler.png")
        code, text, err = capture(
            [
                "--E",
                "2e11",
                "--inertia",
                "1e-6",
                "--length",
                "2",
                "--area",
                "1e-3",
                "--yield",
                "6e8",
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
            "title: Euler column buckling",
            "P_cr_N:",
            "slenderness:",
            "sigma_cr_Pa:",
            "euler_regime: valid_euler",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            [
                "--E",
                "2e11",
                "--inertia",
                "1e-6",
                "--length",
                "2",
                "--ends",
                "fixed-free",
            ]
        )
        if code != 0:
            return fail(f"fixed-free returned {code}: {err}")
        if "ends: fixed-free" not in text or "K: 2" not in text:
            return fail("fixed-free ends were not applied")
        if "slenderness:" in text:
            return fail("run without area printed slenderness")

        code, _text, err = capture(
            ["--E", "2e11", "--inertia", "1e-6", "--length", "2", "--yield", "2.5e8"]
        )
        if code != 2 or "area" not in err:
            return fail("yield without area was accepted on the CLI")
        code, _text, _err = capture(["--E", "2e11", "--inertia", "1e-6"])
        if code != 2:
            return fail("missing length was accepted")

    print("check: pass")
    print_kv("P_cr_N", expected_load)
    print_kv("sigma_cr_Pa", expected_load / area)
    print_kv("slenderness", slender)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Elastic Euler critical buckling load for a concentrically loaded "
            "prismatic column, with optional area, yield transition check, "
            "and PNG of critical load versus length."
        )
    )
    parser.add_argument("--E", type=float, default=None, help="Young's modulus E [Pa]")
    parser.add_argument(
        "--inertia",
        type=float,
        default=None,
        help="second moment of area I [m^4]",
    )
    parser.add_argument(
        "--length",
        type=float,
        default=None,
        help="unsupported length L [m]",
    )
    parser.add_argument(
        "--k",
        type=float,
        default=None,
        help=f"end-fix factor K (default {DEFAULT_K:g}, pinned-pinned)",
    )
    parser.add_argument(
        "--ends",
        type=str,
        default=None,
        choices=sorted(CLASSICAL_K),
        help="classical end condition that sets K",
    )
    parser.add_argument(
        "--area",
        type=float,
        default=None,
        help="cross-sectional area A [m^2] for stress and slenderness",
    )
    parser.add_argument(
        "--yield",
        dest="yield_stress",
        type=float,
        default=None,
        help="compressive yield stress [Pa] for Euler versus yield check",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.E is None or args.inertia is None or args.length is None:
        print(
            "error: requires --E, --inertia, and --length",
            file=sys.stderr,
        )
        return 2

    try:
        result = evaluate(
            args.E,
            args.inertia,
            args.length,
            args.k,
            args.ends,
            args.area,
            args.yield_stress,
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

    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
