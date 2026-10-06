#!/usr/bin/env python3
"""Fundamental bending natural frequency of a uniform Euler-Bernoulli cantilever.

cantilever_lambda1_L is the first fixed-free root, lambda1*L ≈ 1.875104.
cantilever_omega_bending_1 is
  omega_n = (lambda1*L)**2 * sqrt(E*I / (mu * L**4)).
cantilever_freq_hz is f_Hz = omega_n / (2*pi).
Mass per length may be given directly (primary), or as total beam mass
with mu = m_beam / L. Tip mass and other end conditions are omitted.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Cantilever natural frequency"
PLOT_LENGTH_START = 0.5
PLOT_LENGTH_END = 1.5
PLOT_Y_PAD = 1.1
N_CURVE = 201
# First root of cosh(x)*cos(x) + 1 = 0 for a uniform fixed-free beam.
# NASA TN D-2831 lists 1.87510; the six-digit classic value is used here.
LAMBDA1_L = 1.875104
MODE_NAME = "cantilever_uniform_bending_1"

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "uniform Euler-Bernoulli cantilever (fixed-free); undamped; "
    "first bending mode only; "
    f"cantilever_lambda1_L = {LAMBDA1_L:g}; "
    "cantilever_omega_bending_1 omega_n = (lambda1*L)**2 * "
    "sqrt(E*I/(mu*L**4)); "
    "cantilever_freq_hz f_Hz = omega_n/(2*pi); "
    "primary mass path is mass per length mu; "
    "alternate path is total beam mass with mu = m_beam/L; "
    "homogeneous isotropic linear-elastic material; "
    "tip mass, massless-beam tip-mass mode, higher modes, damping, "
    "forced response, and non-cantilever end conditions are omitted"
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


def mass_per_length_from_total(mass: float, length: float) -> float:
    """Alternate mass path: mu = m_beam / L."""
    return mass / length


def omega_bending_1(
    modulus: float, inertia: float, length: float, mu: float
) -> float:
    """cantilever_omega_bending_1: (lambda1*L)**2 * sqrt(E*I/(mu*L**4))."""
    return (LAMBDA1_L**2) * math.sqrt(modulus * inertia / (mu * length**4))


def freq_hz(omega: float) -> float:
    """cantilever_freq_hz: f_Hz = omega_n / (2*pi)."""
    return omega / (2.0 * math.pi)


def evaluate(
    modulus: float,
    inertia: float,
    length: float,
    mu: float | None,
    mass: float | None,
) -> dict[str, float | str]:
    require_positive("Young's modulus", modulus)
    require_positive("second moment of area", inertia)
    require_positive("length", length)

    has_mu = mu is not None
    has_mass = mass is not None
    if has_mu and has_mass:
        raise ValueError("pass --mu or --mass, not both")
    if not has_mu and not has_mass:
        raise ValueError("requires --mu or --mass")

    if has_mu:
        require_positive("mass per length", float(mu))
        mu_use = float(mu)
        source = "mu"
        result: dict[str, float | str] = {
            "E_Pa": modulus,
            "I_m4": inertia,
            "L_m": length,
            "mu_kg_m": mu_use,
            "mu_source": source,
        }
    else:
        require_positive("beam mass", float(mass))
        mu_use = mass_per_length_from_total(float(mass), length)
        source = "mass"
        result = {
            "E_Pa": modulus,
            "I_m4": inertia,
            "L_m": length,
            "mu_kg_m": mu_use,
            "mu_source": source,
            "m_beam_kg": float(mass),
        }

    omega = omega_bending_1(modulus, inertia, length, mu_use)
    result["lambda1_L"] = LAMBDA1_L
    result["omega_n_rad_s"] = omega
    result["f_Hz"] = freq_hz(omega)
    result["mode"] = MODE_NAME
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
        raise ValueError(
            "matplotlib is required to plot cantilever natural frequency"
        ) from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    modulus = float(result["E_Pa"])
    inertia = float(result["I_m4"])
    length = float(result["L_m"])
    mu = float(result["mu_kg_m"])
    f_op = float(result["f_Hz"])
    l_min = PLOT_LENGTH_START * length
    l_max = PLOT_LENGTH_END * length
    lengths = linspace(l_min, l_max, N_CURVE)
    freqs = [
        freq_hz(omega_bending_1(modulus, inertia, L, mu)) for L in lengths
    ]
    y_top = PLOT_Y_PAD * max(max(freqs), f_op)

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(
        lengths,
        freqs,
        color="#1a5276",
        linewidth=1.8,
        label=r"$f_1=(\lambda_1 L)^2\sqrt{EI/(\mu L^4)}/(2\pi)$",
    )
    ax.plot(
        length,
        f_op,
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating length",
    )
    ax.set_xlabel("length (m)")
    ax.set_ylabel("fundamental frequency (Hz)")
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
    print_kv("mu_kg_m", result["mu_kg_m"])
    print_kv("mu_source", result["mu_source"])
    if "m_beam_kg" in result:
        print_kv("m_beam_kg", result["m_beam_kg"])
    print_kv("lambda1_L", result["lambda1_L"])
    print_kv("omega_n_rad_s", result["omega_n_rad_s"])
    print_kv("f_Hz", result["f_Hz"])
    print_kv("mode", result["mode"])
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    # Unit path: E = I = mu = L = 1 => omega = (lambda1*L)**2.
    unit_omega = omega_bending_1(1.0, 1.0, 1.0, 1.0)
    if not close(unit_omega, LAMBDA1_L**2):
        return fail("unit omega is not (lambda1*L)**2")
    if not close(freq_hz(unit_omega), (LAMBDA1_L**2) / (2.0 * math.pi)):
        return fail("unit f_Hz mismatch")

    # lambda1*L squared cross-check against the classic 3.516015 value.
    if not close(LAMBDA1_L**2, 3.516015, tol=1e-6):
        return fail("(lambda1*L)**2 is not near 3.516015")

    # NASA TN D-2831 lists the first characteristic root as 1.87510.
    if abs(LAMBDA1_L - 1.87510) > 5e-6:
        return fail("lambda1*L disagree with NASA TN D-2831 1.87510")

    # Sample aluminum-like boom: E=70e9, I=1e-8, L=1, mu=0.5.
    modulus = 7.0e10
    inertia = 1.0e-8
    length = 1.0
    mu = 0.5
    expected_omega = (LAMBDA1_L**2) * math.sqrt(
        modulus * inertia / (mu * length**4)
    )
    sample = evaluate(modulus, inertia, length, mu, None)
    if sample["mode"] != MODE_NAME:
        return fail("mode name mismatch")
    if sample["mu_source"] != "mu":
        return fail("mu path did not set mu_source")
    if not close(float(sample["omega_n_rad_s"]), expected_omega):
        return fail("mu-path omega mismatch")
    if not close(float(sample["f_Hz"]), expected_omega / (2.0 * math.pi)):
        return fail("mu-path f_Hz mismatch")

    mass = mu * length
    from_mass = evaluate(modulus, inertia, length, None, mass)
    if from_mass["mu_source"] != "mass":
        return fail("mass path did not set mu_source")
    if not close(float(from_mass["mu_kg_m"]), mu):
        return fail("mass path mu = m/L mismatch")
    if not close(float(from_mass["omega_n_rad_s"]), expected_omega):
        return fail("mass-path omega disagrees with mu path")
    if "m_beam_kg" not in from_mass:
        return fail("mass path did not print m_beam_kg")

    # f scales as 1/L**2 at fixed E, I, mu.
    double_l = evaluate(modulus, inertia, 2.0 * length, mu, None)
    if not close(
        float(double_l["f_Hz"]), float(sample["f_Hz"]) / 4.0
    ):
        return fail("doubling L did not quarter f_Hz")

    try:
        evaluate(modulus, inertia, length, mu, mass)
        return fail("both --mu and --mass were accepted")
    except ValueError:
        pass
    try:
        evaluate(modulus, inertia, length, None, None)
        return fail("missing mass path was accepted")
    except ValueError:
        pass
    try:
        evaluate(0.0, inertia, length, mu, None)
        return fail("zero modulus was accepted")
    except ValueError:
        pass
    try:
        evaluate(modulus, inertia, length, 0.0, None)
        return fail("zero mu was accepted")
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
        out = str(Path(tmp) / "cantilever.png")
        code, text, err = capture(
            [
                "--E",
                "7e10",
                "--inertia",
                "1e-8",
                "--length",
                "1",
                "--mu",
                "0.5",
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
            "title: Cantilever natural frequency",
            "E_Pa:",
            "I_m4:",
            "L_m:",
            "mu_kg_m:",
            "omega_n_rad_s:",
            "f_Hz:",
            f"mode: {MODE_NAME}",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            [
                "--E",
                "7e10",
                "--inertia",
                "1e-8",
                "--length",
                "1",
                "--mass",
                "0.5",
            ]
        )
        if code != 0:
            return fail(f"mass path returned {code}: {err}")
        if "mu_source: mass" not in text:
            return fail("mass path did not print mu_source")
        if "m_beam_kg:" not in text:
            return fail("mass path did not print m_beam_kg")
        if "graph:" in text:
            return fail("run without --out printed graph")

        code, _text, err = capture(
            [
                "--E",
                "7e10",
                "--inertia",
                "1e-8",
                "--length",
                "1",
                "--mu",
                "0.5",
                "--mass",
                "0.5",
            ]
        )
        if code != 2 or "not both" not in err:
            return fail("both mass flags were accepted on the CLI")
        code, _text, _err = capture(
            ["--E", "7e10", "--inertia", "1e-8", "--length", "1"]
        )
        if code != 2:
            return fail("missing mu/mass was accepted")
        code, _text, _err = capture([])
        if code != 2:
            return fail("missing required flags were accepted")

    print("check: pass")
    print_kv("lambda1_L", LAMBDA1_L)
    print_kv("omega_n_rad_s", expected_omega)
    print_kv("f_Hz", expected_omega / (2.0 * math.pi))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Fundamental bending natural frequency of a uniform "
            "Euler-Bernoulli cantilever (fixed-free), with optional PNG "
            "of frequency versus length."
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
        help="beam length L [m]",
    )
    parser.add_argument(
        "--mu",
        type=float,
        default=None,
        help="mass per length mu [kg/m] (primary mass path)",
    )
    parser.add_argument(
        "--mass",
        type=float,
        default=None,
        help="total beam mass m_beam [kg]; sets mu = m_beam/L",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument(
        "--check", action="store_true", help="run built-in consistency checks"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.E is None or args.inertia is None or args.length is None:
        print(
            "error: requires --E, --inertia, --length, and either --mu or --mass",
            file=sys.stderr,
        )
        return 2

    try:
        result = evaluate(args.E, args.inertia, args.length, args.mu, args.mass)
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
