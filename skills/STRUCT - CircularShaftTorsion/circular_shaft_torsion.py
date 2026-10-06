#!/usr/bin/env python3
"""Elastic torsion of a solid or hollow circular shaft.

polar_second_moment_solid is J = pi/2*Ro**4 (= pi/32*Do**4).
polar_second_moment_hollow is J = pi/2*(Ro**4 - Ri**4)
(= pi/32*(Do**4 - Di**4)).
circular_shaft_shear is tau = T*r/J; max at the outer fiber is T*Ro/J.
circular_shaft_twist is theta = T*L/(G*J) when length and G are given.
Optional margin_of_safety is MS = allowable/tau - 1 with max shear as
the design stress.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Circular shaft torsion"
PLOT_END_FACTOR = 1.5
N_CURVE = 201

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "elastic torsion of a circular shaft only; solid or concentrically "
    "hollow prismatic section; plane sections remain plane and radii "
    "remain straight; homogeneous isotropic linear-elastic material; "
    "polar_second_moment_solid J = pi/2*Ro**4 (= pi/32*Do**4); "
    "polar_second_moment_hollow J = pi/2*(Ro**4 - Ri**4) "
    "(= pi/32*(Do**4 - Di**4)); "
    "circular_shaft_shear tau = T*r/J, max at outer fiber tau_max = T*Ro/J; "
    "optional circular_shaft_twist theta = T*L/(G*J) when length and "
    "shear modulus are both given; "
    "optional margin_of_safety MS = allowable/tau_max - 1 with max shear "
    "as the design stress; "
    "non-circular sections, open thin-wall warping, plastic torsion, and "
    "combined bending-plus-torsion are omitted"
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


def polar_second_moment_solid(outer_radius: float) -> float:
    """polar_second_moment_solid: J = pi/2*Ro**4."""
    return 0.5 * math.pi * outer_radius**4


def polar_second_moment_hollow(outer_radius: float, inner_radius: float) -> float:
    """polar_second_moment_hollow: J = pi/2*(Ro**4 - Ri**4)."""
    return 0.5 * math.pi * (outer_radius**4 - inner_radius**4)


def polar_second_moment_solid_diameter(outer_diameter: float) -> float:
    """Equivalent diameter form: J = pi/32*Do**4."""
    return (math.pi / 32.0) * outer_diameter**4


def polar_second_moment_hollow_diameter(
    outer_diameter: float, inner_diameter: float
) -> float:
    """Equivalent diameter form: J = pi/32*(Do**4 - Di**4)."""
    return (math.pi / 32.0) * (outer_diameter**4 - inner_diameter**4)


def shear_stress(torque: float, radius: float, polar: float) -> float:
    """circular_shaft_shear: tau = T*r/J."""
    return torque * radius / polar


def max_shear_stress(torque: float, outer_radius: float, polar: float) -> float:
    """Max shear at the outer fiber: tau_max = T*Ro/J."""
    return shear_stress(torque, outer_radius, polar)


def angle_of_twist(
    torque: float, length: float, shear_modulus: float, polar: float
) -> float:
    """circular_shaft_twist: theta = T*L/(G*J)."""
    return torque * length / (shear_modulus * polar)


def margin_of_safety(allowable: float, design: float) -> float:
    """margin_of_safety: MS = allowable/design - 1."""
    return allowable / design - 1.0


def resolve_section(
    radius: float | None,
    diameter: float | None,
    inner_radius: float | None,
    inner_diameter: float | None,
) -> tuple[float, float | None, str]:
    """Return (Ro, Ri or None, size_mode)."""
    has_r = radius is not None
    has_d = diameter is not None
    has_ri = inner_radius is not None
    has_di = inner_diameter is not None

    if has_r and has_d:
        raise ValueError("pass --radius or --diameter, not both")
    if not has_r and not has_d:
        raise ValueError("requires --radius or --diameter")
    if has_ri and has_di:
        raise ValueError("pass --inner-radius or --inner-diameter, not both")
    if has_r and has_di:
        raise ValueError(
            "radius API uses --inner-radius; do not mix with --inner-diameter"
        )
    if has_d and has_ri:
        raise ValueError(
            "diameter API uses --inner-diameter; do not mix with --inner-radius"
        )

    if has_r:
        require_positive("outer radius", float(radius))
        outer = float(radius)
        mode = "radius"
        if has_ri:
            require_positive("inner radius", float(inner_radius))
            inner = float(inner_radius)
            if inner >= outer:
                raise ValueError("inner radius must be < outer radius")
            return outer, inner, mode
        return outer, None, mode

    require_positive("outer diameter", float(diameter))
    outer = 0.5 * float(diameter)
    mode = "diameter"
    if has_di:
        require_positive("inner diameter", float(inner_diameter))
        inner = 0.5 * float(inner_diameter)
        if inner >= outer:
            raise ValueError("inner diameter must be < outer diameter")
        return outer, inner, mode
    return outer, None, mode


def evaluate(
    torque: float,
    radius: float | None,
    diameter: float | None,
    inner_radius: float | None,
    inner_diameter: float | None,
    length: float | None,
    shear_modulus: float | None,
    allowable: float | None,
) -> dict[str, float | str]:
    require_positive("torque", torque)
    outer, inner, mode = resolve_section(
        radius, diameter, inner_radius, inner_diameter
    )

    if inner is None:
        polar = polar_second_moment_solid(outer)
        polar_d = polar_second_moment_solid_diameter(2.0 * outer)
        section = "solid"
    else:
        polar = polar_second_moment_hollow(outer, inner)
        polar_d = polar_second_moment_hollow_diameter(2.0 * outer, 2.0 * inner)
        section = "hollow"
    if not close(polar, polar_d):
        raise ValueError("radius and diameter polar-moment forms disagree")

    tau = max_shear_stress(torque, outer, polar)
    result: dict[str, float | str] = {
        "T_N_m": torque,
        "Ro_m": outer,
        "J_m4": polar,
        "tau_max_Pa": tau,
        "section": section,
        "size_mode": mode,
    }
    if inner is not None:
        result["Ri_m"] = inner

    has_l = length is not None
    has_g = shear_modulus is not None
    if has_l ^ has_g:
        raise ValueError("angle of twist requires both --length and --G")
    if has_l and has_g:
        require_positive("length", float(length))
        require_positive("shear modulus", float(shear_modulus))
        result["L_m"] = float(length)
        result["G_Pa"] = float(shear_modulus)
        result["theta_rad"] = angle_of_twist(
            torque, float(length), float(shear_modulus), polar
        )

    if allowable is not None:
        require_positive("allowable shear stress", allowable)
        result["allowable_Pa"] = allowable
        result["margin_of_safety"] = margin_of_safety(allowable, tau)

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
        raise ValueError("matplotlib is required to plot shaft torsion") from exc
    return plt


def write_plot(result: dict[str, float | str], out_path: Path) -> None:
    plt = ensure_matplotlib()
    torque = float(result["T_N_m"])
    outer = float(result["Ro_m"])
    polar = float(result["J_m4"])
    stress = float(result["tau_max_Pa"])
    t_max = PLOT_END_FACTOR * torque
    torques = linspace(0.0, t_max, N_CURVE)
    stresses = [max_shear_stress(t, outer, polar) for t in torques]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(
        torques,
        stresses,
        color="#1a5276",
        linewidth=1.8,
        label=r"$\tau_{\mathrm{max}} = T R_o / J$",
    )
    ax.plot(
        torque,
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
    ax.set_xlabel("torque (N·m)")
    ax.set_ylabel("max shear stress (Pa)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(0.0, t_max)
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
    print_kv("T_N_m", result["T_N_m"])
    print_kv("Ro_m", result["Ro_m"])
    if "Ri_m" in result:
        print_kv("Ri_m", result["Ri_m"])
    print_kv("section", result["section"])
    print_kv("size_mode", result["size_mode"])
    print_kv("J_m4", result["J_m4"])
    print_kv("tau_max_Pa", result["tau_max_Pa"])
    if "G_Pa" in result:
        print_kv("G_Pa", result["G_Pa"])
        print_kv("L_m", result["L_m"])
        print_kv("theta_rad", result["theta_rad"])
    if "allowable_Pa" in result:
        print_kv("allowable_Pa", result["allowable_Pa"])
        print_kv("margin_of_safety", result["margin_of_safety"])
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    # Unit solid: Ro = 1, J = pi/2.
    if not close(polar_second_moment_solid(1.0), 0.5 * math.pi):
        return fail("unit solid polar moment is not pi/2")
    if not close(polar_second_moment_solid_diameter(2.0), 0.5 * math.pi):
        return fail("unit solid diameter form disagrees with radius form")

    # Hollow identity from AFFDL: Ip = pi/2*(ro^4 - ri^4).
    ro = 2.0
    ri = 1.0
    j_h = polar_second_moment_hollow(ro, ri)
    if not close(j_h, 0.5 * math.pi * (16.0 - 1.0)):
        return fail("hollow polar moment mismatch")
    if not close(
        polar_second_moment_hollow_diameter(4.0, 2.0),
        (math.pi / 32.0) * (256.0 - 16.0),
    ):
        return fail("hollow diameter form mismatch")
    if not close(j_h, polar_second_moment_hollow_diameter(4.0, 2.0)):
        return fail("hollow radius and diameter forms disagree")

    # AFFDL (1-47): fs = 2*T*r / (pi*(ro^4 - ri^4)) at r = ro.
    torque = 1000.0
    tau = max_shear_stress(torque, ro, j_h)
    expected_tau = 2.0 * torque * ro / (math.pi * (ro**4 - ri**4))
    if not close(tau, expected_tau):
        return fail("AFFDL max shear mismatch")

    # Twist: theta = T*L/(G*J) = AFFDL (1-48).
    length = 0.5
    g_mod = 8.0e10
    theta = angle_of_twist(torque, length, g_mod, j_h)
    expected_theta = (
        2.0 * torque * length / (math.pi * (ro**4 - ri**4) * g_mod)
    )
    if not close(theta, expected_theta):
        return fail("AFFDL twist mismatch")

    if not close(margin_of_safety(1.25 * tau, tau), 0.25):
        return fail("quarter margin is not 0.25")
    if not close(margin_of_safety(tau, tau), 0.0):
        return fail("zero margin is not 0")

    solid = evaluate(torque, 0.02, None, None, None, None, None, None)
    if solid["section"] != "solid" or "Ri_m" in solid:
        return fail("solid path did not omit Ri")
    j_s = float(solid["J_m4"])
    if not close(j_s, polar_second_moment_solid(0.02)):
        return fail("solid evaluate J mismatch")

    hollow_ro = 0.02
    hollow_ri = 0.01
    hollow_j = polar_second_moment_hollow(hollow_ro, hollow_ri)
    hollow_tau = max_shear_stress(torque, hollow_ro, hollow_j)
    hollow = evaluate(
        torque,
        None,
        0.04,
        None,
        0.02,
        length,
        g_mod,
        1.25 * hollow_tau,
    )
    if hollow["section"] != "hollow":
        return fail("hollow path did not set section")
    if not close(float(hollow["Ro_m"]), hollow_ro) or not close(
        float(hollow["Ri_m"]), hollow_ri
    ):
        return fail("diameter inputs did not resolve to Ro and Ri")
    if "theta_rad" not in hollow:
        return fail("twist path did not print theta")
    if not close(float(hollow["tau_max_Pa"]), hollow_tau):
        return fail("hollow evaluate tau mismatch")
    if not close(float(hollow["margin_of_safety"]), 0.25):
        return fail("evaluate margin is not 0.25")

    try:
        evaluate(torque, 0.02, 0.04, None, None, None, None, None)
        return fail("both outer size flags were accepted")
    except ValueError:
        pass
    try:
        evaluate(torque, 0.02, None, None, 0.01, None, None, None)
        return fail("mixed radius/diameter inner API was accepted")
    except ValueError:
        pass
    try:
        evaluate(torque, 0.02, None, None, None, length, None, None)
        return fail("length without G was accepted")
    except ValueError:
        pass
    try:
        evaluate(torque, 0.02, None, 0.03, None, None, None, None)
        return fail("inner radius >= outer was accepted")
    except ValueError:
        pass
    try:
        evaluate(0.0, 0.02, None, None, None, None, None, None)
        return fail("zero torque was accepted")
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
        out = str(Path(tmp) / "torsion.png")
        code, text, err = capture(
            [
                "--torque",
                "1000",
                "--diameter",
                "0.04",
                "--inner-diameter",
                "0.02",
                "--length",
                "0.5",
                "--G",
                "8e10",
                "--allowable",
                str(1.25 * hollow_tau),
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
            "title: Circular shaft torsion",
            "tau_max_Pa:",
            "J_m4:",
            "section: hollow",
            "theta_rad:",
            "margin_of_safety:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            ["--torque", "1000", "--radius", "0.02", "--out", out]
        )
        if code != 0:
            return fail(f"solid radius returned {code}: {err}")
        if "section: solid" not in text:
            return fail("solid radius did not print section")
        if "Ri_m:" in text:
            return fail("solid run printed Ri")
        if "theta_rad:" in text:
            return fail("run without G/L printed twist")
        if "margin_of_safety:" in text:
            return fail("run without allowable printed a margin")

        code, _text, err = capture(
            ["--torque", "1000", "--radius", "0.02", "--diameter", "0.04"]
        )
        if code != 2 or "not both" not in err:
            return fail("both outer size flags were accepted on the CLI")
        code, _text, err = capture(
            ["--torque", "1000", "--radius", "0.02", "--length", "0.5"]
        )
        if code != 2 or "both" not in err:
            return fail("length without G was accepted on the CLI")
        code, _text, _err = capture(["--torque", "1000"])
        if code != 2:
            return fail("missing outer size was accepted")
        code, _text, _err = capture([])
        if code != 2:
            return fail("missing torque was accepted")

    print("check: pass")
    print_kv("J_m4", j_h)
    print_kv("tau_max_Pa", expected_tau)
    print_kv("theta_rad", expected_theta)
    print_kv("margin_of_safety", 0.25)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Elastic torsion of a solid or hollow circular shaft: polar "
            "second moment, max shear stress, optional angle of twist, "
            "and optional margin of safety."
        )
    )
    parser.add_argument("--torque", type=float, default=None, help="torque T [N*m]")
    parser.add_argument(
        "--radius",
        type=float,
        default=None,
        help="outer radius Ro [m]",
    )
    parser.add_argument(
        "--diameter",
        type=float,
        default=None,
        help="outer diameter Do [m]",
    )
    parser.add_argument(
        "--inner-radius",
        type=float,
        default=None,
        help="inner radius Ri [m] for a hollow shaft (radius API)",
    )
    parser.add_argument(
        "--inner-diameter",
        type=float,
        default=None,
        help="inner diameter Di [m] for a hollow shaft (diameter API)",
    )
    parser.add_argument(
        "--length",
        type=float,
        default=None,
        help="shaft length L [m]; requires --G for twist",
    )
    parser.add_argument(
        "--G",
        type=float,
        default=None,
        help="shear modulus G [Pa]; requires --length for twist",
    )
    parser.add_argument(
        "--allowable",
        type=float,
        default=None,
        help="allowable shear stress [Pa]",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.torque is None:
        print(
            "error: requires --torque and either --radius or --diameter",
            file=sys.stderr,
        )
        return 2

    try:
        result = evaluate(
            args.torque,
            args.radius,
            args.diameter,
            args.inner_radius,
            args.inner_diameter,
            args.length,
            args.G,
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
