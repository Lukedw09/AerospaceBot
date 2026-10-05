#!/usr/bin/env python3
"""Pure elastic bending stress for a beam, spar, longeron, or boom.

beam_bending_stress is sigma = M/Z. beam_bending_stress_inertia is
sigma = M*c/I. section_modulus is Z = I/c. Optional margin_of_safety is
MS = allowable/sigma - 1 with bending stress as the design stress.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Beam bending stress"
PLOT_END_FACTOR = 1.5
N_CURVE = 201

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "elastic pure bending only; no axial force, shear, or torsion; "
    "plane sections remain plane; moment about a principal neutral axis; "
    "prismatic cross section at the station; "
    "beam_bending_stress sigma = M/Z; "
    "beam_bending_stress_inertia sigma = M*c/I; "
    "section_modulus Z = I/c; "
    "optional margin_of_safety MS = allowable/sigma - 1 with bending "
    "stress as the design stress; "
    "sigma is the extreme-fiber normal-stress magnitude; tension versus "
    "compression sign is left to the user; "
    "elastic (not plastic) section modulus"
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


def section_modulus(inertia: float, fiber: float) -> float:
    """section_modulus: Z = I/c."""
    return inertia / fiber


def bending_stress(moment: float, modulus: float) -> float:
    """beam_bending_stress: sigma = M/Z."""
    return moment / modulus


def bending_stress_inertia(moment: float, fiber: float, inertia: float) -> float:
    """beam_bending_stress_inertia: sigma = M*c/I."""
    return moment * fiber / inertia


def margin_of_safety(allowable: float, design: float) -> float:
    """margin_of_safety: MS = allowable/design - 1."""
    return allowable / design - 1.0


def evaluate(
    moment: float,
    modulus: float | None,
    inertia: float | None,
    fiber: float | None,
    allowable: float | None,
) -> dict[str, float | str]:
    require_positive("bending moment", moment)
    has_z = modulus is not None
    has_i = inertia is not None
    has_c = fiber is not None
    if has_z and (has_i or has_c):
        raise ValueError(
            "pass --section-modulus, or --inertia with --fiber, not both"
        )
    if has_z:
        require_positive("section modulus", modulus)
        z = float(modulus)
        source = "section_modulus"
        sigma = bending_stress(moment, z)
        result: dict[str, float | str] = {
            "M_N_m": moment,
            "Z_m3": z,
            "sigma_Pa": sigma,
            "section_source": source,
        }
    elif has_i and has_c:
        require_positive("second moment of area", inertia)
        require_positive("fiber distance", fiber)
        z = section_modulus(float(inertia), float(fiber))
        sigma_i = bending_stress_inertia(moment, float(fiber), float(inertia))
        sigma = bending_stress(moment, z)
        if not close(sigma, sigma_i):
            raise ValueError("M/Z and M*c/I disagree")
        result = {
            "M_N_m": moment,
            "I_m4": float(inertia),
            "c_m": float(fiber),
            "Z_m3": z,
            "sigma_Pa": sigma,
            "section_source": "inertia",
        }
    else:
        raise ValueError(
            "requires --section-modulus, or both --inertia and --fiber"
        )
    if allowable is not None:
        require_positive("allowable stress", allowable)
        result["allowable_Pa"] = allowable
        result["margin_of_safety"] = margin_of_safety(allowable, float(result["sigma_Pa"]))
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
        raise ValueError("matplotlib is required to plot bending stress") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    moment = float(result["M_N_m"])
    modulus = float(result["Z_m3"])
    stress = float(result["sigma_Pa"])
    m_max = PLOT_END_FACTOR * moment
    moments = linspace(0.0, m_max, N_CURVE)
    stresses = [bending_stress(m, modulus) for m in moments]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(moments, stresses, color="#1a5276", linewidth=1.8, label=r"$\sigma = M/Z$")
    ax.plot(
        moment,
        stress,
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    if "allowable_Pa" in result:
        ax.axhline(
            float(result["allowable_Pa"]),
            color="#c0392b",
            linestyle="--",
            linewidth=1.5,
            label="allowable",
        )
    ax.set_xlabel("bending moment (N·m)")
    ax.set_ylabel("bending stress (Pa)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(0.0, m_max)
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
    print_kv("M_N_m", result["M_N_m"])
    if "I_m4" in result:
        print_kv("I_m4", result["I_m4"])
        print_kv("c_m", result["c_m"])
    print_kv("Z_m3", result["Z_m3"])
    print_kv("section_source", result["section_source"])
    print_kv("sigma_Pa", result["sigma_Pa"])
    if "allowable_Pa" in result:
        print_kv("allowable_Pa", result["allowable_Pa"])
        print_kv("margin_of_safety", result["margin_of_safety"])
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    if not close(section_modulus(1.0, 1.0), 1.0):
        return fail("unit section modulus is not 1")
    if not close(bending_stress(1.0, 1.0), 1.0):
        return fail("unit M/Z is not 1")
    if not close(bending_stress_inertia(1.0, 1.0, 1.0), 1.0):
        return fail("unit M*c/I is not 1")

    # Report 82 spar sample: sb = M/Z = 856/1.16.
    if not close(bending_stress(856.0, 1.16), 856.0 / 1.16):
        return fail("Report 82 spar sample M/Z mismatch")

    # Z = I/c and M/Z = M*c/I on a consistent SI point.
    inertia = 9.0e-5
    fiber = 0.03
    moment = 1200.0
    z = section_modulus(inertia, fiber)
    if not close(z, 0.003):
        return fail(f"Z = {z}, expected 0.003")
    sigma_z = bending_stress(moment, z)
    sigma_i = bending_stress_inertia(moment, fiber, inertia)
    if not close(sigma_z, 4.0e5) or not close(sigma_i, 4.0e5):
        return fail("inertia and section-modulus stresses disagree")

    if not close(margin_of_safety(5.0e5, 4.0e5), 0.25):
        return fail("quarter margin is not 0.25")
    if not close(margin_of_safety(4.0e5, 4.0e5), 0.0):
        return fail("zero margin is not 0")

    from_z = evaluate(moment, z, None, None, 5.0e5)
    from_i = evaluate(moment, None, inertia, fiber, 5.0e5)
    if from_z["section_source"] != "section_modulus":
        return fail("section-modulus path did not set section_source")
    if from_i["section_source"] != "inertia":
        return fail("inertia path did not set section_source")
    if not close(float(from_z["sigma_Pa"]), float(from_i["sigma_Pa"])):
        return fail("evaluate paths disagree on stress")
    if not close(float(from_i["Z_m3"]), z):
        return fail("evaluate did not recover Z from I and c")
    if not close(float(from_z["margin_of_safety"]), 0.25):
        return fail("evaluate margin is not 0.25")

    try:
        evaluate(moment, z, inertia, fiber, None)
        return fail("both section paths were accepted")
    except ValueError:
        pass
    try:
        evaluate(moment, None, inertia, None, None)
        return fail("inertia without fiber was accepted")
    except ValueError:
        pass
    try:
        evaluate(0.0, z, None, None, None)
        return fail("zero moment was accepted")
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
        out = str(Path(tmp) / "bending.png")
        code, text, err = capture(
            [
                "--moment",
                "1200",
                "--section-modulus",
                "0.003",
                "--allowable",
                "500000",
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
            "title: Beam bending stress",
            "sigma_Pa:",
            "Z_m3:",
            "section_source: section_modulus",
            "margin_of_safety:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            [
                "--moment",
                "1200",
                "--inertia",
                "9e-5",
                "--fiber",
                "0.03",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"inertia input returned {code}: {err}")
        if "section_source: inertia" not in text:
            return fail("inertia input did not print section_source")
        if "I_m4:" not in text or "c_m:" not in text:
            return fail("inertia input did not print I and c")
        if "margin_of_safety:" in text:
            return fail("run without allowable printed a margin")

        code, _text, err = capture(["--moment", "1200", "--section-modulus", "0.003", "--inertia", "9e-5"])
        if code != 2 or "not both" not in err:
            return fail("both section paths were accepted on the CLI")
        code, _text, err = capture(["--moment", "1200"])
        if code != 2:
            return fail("missing section was accepted")
        code, _text, _err = capture([])
        if code != 2:
            return fail("missing moment was accepted")

    print("check: pass")
    print_kv("sigma_Pa", from_i["sigma_Pa"])
    print_kv("Z_m3", from_i["Z_m3"])
    print_kv("margin_of_safety", from_i["margin_of_safety"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pure elastic bending stress for a beam, spar, longeron, or boom, "
            "from moment and section modulus or second moment with fiber distance."
        )
    )
    parser.add_argument("--moment", type=float, default=None, help="bending moment M [N*m]")
    parser.add_argument(
        "--section-modulus",
        type=float,
        default=None,
        help="elastic section modulus Z [m^3]",
    )
    parser.add_argument(
        "--inertia",
        type=float,
        default=None,
        help="second moment of area I [m^4]",
    )
    parser.add_argument(
        "--fiber",
        type=float,
        default=None,
        help="distance from neutral axis to extreme fiber c [m]",
    )
    parser.add_argument(
        "--allowable",
        type=float,
        default=None,
        help="allowable stress [Pa]",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.moment is None:
        print(
            "error: requires --moment and either --section-modulus or "
            "--inertia with --fiber",
            file=sys.stderr,
        )
        return 2

    try:
        result = evaluate(
            args.moment,
            args.section_modulus,
            args.inertia,
            args.fiber,
            args.allowable,
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
