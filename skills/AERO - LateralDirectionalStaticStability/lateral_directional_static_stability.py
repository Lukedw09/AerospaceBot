#!/usr/bin/env python3
"""Weathercock and geometric-dihedral static derivatives.

vertical_tail_volume is Sv*lv/(S*b).
cn_beta_vertical_tail is av*Vv*eta.
cl_beta_geometric_dihedral is -aw*gamma*(1+2*lam)/(6*(1+lam)).
Positive Cn_beta is weathercock stable. Negative Cl_beta is positive
effective dihedral.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "vertical_tail_volume Vv = Sv*lv/(S*b); "
    "cn_beta_vertical_tail Cn_beta = av*Vv*eta; "
    "eta defaults to 1 at zero attack when omitted (eta_source default_unity); "
    "cl_beta_geometric_dihedral for an unswept wing; "
    "taper defaults to 1 (rectangular factor 1/4); "
    "gamma in radians; positive Cn_beta weathervanes; "
    "negative Cl_beta is positive effective dihedral; "
    "fuselage, sweep, and Dutch-roll dynamics are omitted"
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


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def vertical_tail_volume(sv: float, lv: float, area: float, span: float) -> float:
    return sv * lv / (area * span)


def cn_beta_vertical_tail(av: float, volume: float, eta: float) -> float:
    return av * volume * eta


def cl_beta_geometric_dihedral(aw: float, gamma: float, taper: float) -> float:
    return -aw * gamma * (1.0 + 2.0 * taper) / (6.0 * (1.0 + taper))


def flags(cn_beta: float, cl_beta: float) -> dict[str, str]:
    if cn_beta > 0.0:
        weather = "stable"
    elif cn_beta < 0.0:
        weather = "unstable"
    else:
        weather = "neutral"
    if cl_beta < 0.0:
        dihedral = "stable"
    elif cl_beta > 0.0:
        dihedral = "unstable"
    else:
        dihedral = "neutral"
    return {"weathercock": weather, "effective_dihedral": dihedral}


def estimate(args: argparse.Namespace) -> dict[str, object]:
    for name in ("span", "area", "cl_alpha", "sv", "lv", "av", "gamma"):
        value = getattr(args, name)
        if value is None:
            raise ValueError(f"estimate path needs --{name.replace('_', '-')}")
        if name == "gamma":
            require_finite(name, value)
        else:
            require_positive(name, value)
    taper = 1.0 if args.taper is None else args.taper
    if taper < 0.0 or not math.isfinite(taper):
        raise ValueError("taper must be finite and >= 0")
    if args.eta_v is None:
        eta = 1.0
        eta_source = "default_unity"
    else:
        require_positive("eta-v", args.eta_v)
        eta = args.eta_v
        eta_source = "supplied"
    volume = vertical_tail_volume(args.sv, args.lv, args.area, args.span)
    cn_beta = cn_beta_vertical_tail(args.av, volume, eta)
    cl_beta = cl_beta_geometric_dihedral(args.cl_alpha, args.gamma, taper)
    result: dict[str, object] = {
        "path": "estimate",
        "Vv": volume,
        "eta": eta,
        "eta_source": eta_source,
        "taper": taper,
        "Cn_beta_per_rad": cn_beta,
        "Cl_beta_per_rad": cl_beta,
    }
    result.update(flags(cn_beta, cl_beta))
    return result


def supplied(args: argparse.Namespace) -> dict[str, object]:
    require_finite("cn-beta", args.cn_beta)
    require_finite("cl-beta", args.cl_beta)
    result: dict[str, object] = {
        "path": "supplied",
        "Cn_beta_per_rad": args.cn_beta,
        "Cl_beta_per_rad": args.cl_beta,
    }
    result.update(flags(args.cn_beta, args.cl_beta))
    return result


def from_args(args: argparse.Namespace) -> dict[str, object]:
    estimate_names = ("span", "area", "cl_alpha", "sv", "lv", "av", "gamma", "eta_v", "taper")
    has_estimate = any(getattr(args, name) is not None for name in estimate_names)
    has_supplied = args.cn_beta is not None or args.cl_beta is not None
    if has_estimate and has_supplied:
        raise ValueError("do not mix geometry with --cn-beta/--cl-beta")
    if has_supplied:
        if args.cn_beta is None or args.cl_beta is None:
            raise ValueError("--cn-beta and --cl-beta are a pair")
        return supplied(args)
    if has_estimate:
        return estimate(args)
    raise ValueError("pass geometry, or --cn-beta and --cl-beta")


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "path",
        "Vv",
        "eta",
        "eta_source",
        "taper",
        "Cn_beta_per_rad",
        "Cl_beta_per_rad",
        "weathercock",
        "effective_dihedral",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    labels = [r"$C_{n\beta}$", r"$C_{l\beta}$"]
    values = [float(result["Cn_beta_per_rad"]), float(result["Cl_beta_per_rad"])]
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.bar(labels, values, color=["C0", "C1"])
    ax.axhline(0.0, color="0.5", lw=0.6)
    ax.set_ylabel("per radian")
    ax.set_title("Lateral-directional static derivatives")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    volume = vertical_tail_volume(2.0, 5.0, 20.0, 10.0)
    if not close(volume, 0.05):
        return fail("volume")
    if not close(cn_beta_vertical_tail(2.0, volume, 1.0), 0.1):
        return fail("cn")
    if not close(cl_beta_geometric_dihedral(4.0, 0.1, 1.0), -0.1):
        return fail("cl")
    state = estimate(
        argparse.Namespace(
            span=10.0,
            area=20.0,
            cl_alpha=4.0,
            sv=2.0,
            lv=5.0,
            av=2.0,
            gamma=0.1,
            eta_v=None,
            taper=None,
        )
    )
    if state["weathercock"] != "stable" or state["effective_dihedral"] != "stable":
        return fail("signs")
    if state["eta_source"] != "default_unity":
        return fail("eta source")
    given = supplied(argparse.Namespace(cn_beta=-0.2, cl_beta=0.1))
    if given["weathercock"] != "unstable" or given["effective_dihedral"] != "unstable":
        return fail("supplied signs")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(state, path)
        if path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("Cn_beta_per_rad", float(state["Cn_beta_per_rad"]))
    print_kv("Cl_beta_per_rad", float(state["Cl_beta_per_rad"]))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vertical-tail weathercock and unswept geometric dihedral."
    )
    parser.add_argument("--span", type=float, default=None, help="wing span b [m]")
    parser.add_argument("--area", type=float, default=None, help="wing area S [m^2]")
    parser.add_argument("--cl-alpha", type=float, default=None, help="wing lift-curve slope [1/rad]")
    parser.add_argument("--sv", type=float, default=None, help="vertical-tail area [m^2]")
    parser.add_argument("--lv", type=float, default=None, help="vertical-tail length [m]")
    parser.add_argument("--av", type=float, default=None, help="vertical-tail lift-curve slope [1/rad]")
    parser.add_argument("--gamma", type=float, default=None, help="geometric dihedral [rad]")
    parser.add_argument("--eta-v", type=float, default=None, help="vertical-tail dynamic-pressure ratio")
    parser.add_argument("--taper", type=float, default=None, help="wing taper ratio")
    parser.add_argument("--cn-beta", type=float, default=None, help="supplied Cn_beta [1/rad]")
    parser.add_argument("--cl-beta", type=float, default=None, help="supplied Cl_beta [1/rad]")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        result = from_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "lateral_directional_static_stability.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
