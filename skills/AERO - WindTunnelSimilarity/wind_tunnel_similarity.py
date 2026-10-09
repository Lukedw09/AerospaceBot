#!/usr/bin/env python3
"""Reynolds and Mach match, and coefficient load scaling.

reynolds_number is rho*V*L/mu. reynolds_number_kinematic is V*L/nu.
mach_number is V/a. dynamic_pressure is 0.5*rho*V**2.
force_scale_dynamic_pressure is (q2*S2)/(q1*S1).
moment_scale_dynamic_pressure multiplies by c2/c1.
relative_mismatch is abs(a-b)/abs(b). A mismatch above 0.05 is not matched.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
MISMATCH = 0.05
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "reynolds_number or reynolds_number_kinematic; mach_number; "
    "dynamic_pressure; relative_mismatch abs(a-b)/abs(b); "
    "matched when that ratio is at most 0.05; "
    "force_scale_dynamic_pressure and moment_scale_dynamic_pressure "
    "assume equal coefficients; no wall correction and no "
    "Prandtl-Glauert correction"
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


def relative_mismatch(left: float, right: float) -> float:
    return abs(left - right) / abs(right)


def match_flag(ratio: float) -> str:
    return "matched" if ratio <= MISMATCH else "mismatch"


def dynamic_pressure(rho: float, speed: float) -> float:
    return 0.5 * rho * speed * speed


def solve(args: argparse.Namespace) -> dict[str, object]:
    number_path = any(v is not None for v in (args.re_m, args.re_f, args.mach_m, args.mach_f))
    flow_names = (
        "L_m",
        "L_f",
        "V_m",
        "V_f",
        "rho_m",
        "rho_f",
        "mu_m",
        "mu_f",
        "nu_m",
        "nu_f",
        "a_m",
        "a_f",
    )
    flow_path = any(getattr(args, name) is not None for name in flow_names)
    if number_path and flow_path:
        raise ValueError("do not mix --re/--mach with the flow quantities")
    if number_path:
        if None in (args.re_m, args.re_f, args.mach_m, args.mach_f):
            raise ValueError("number path needs --re-m, --re-f, --mach-m, and --mach-f")
        for name, value in (
            ("re-m", args.re_m),
            ("re-f", args.re_f),
            ("mach-m", args.mach_m),
            ("mach-f", args.mach_f),
        ):
            require_positive(name, value)
        re_m, re_f = args.re_m, args.re_f
        mach_m, mach_f = args.mach_m, args.mach_f
        path = "numbers"
    elif flow_path:
        for name in ("L_m", "L_f", "V_m", "V_f", "a_m", "a_f"):
            value = getattr(args, name)
            if value is None:
                raise ValueError(f"flow path needs --{name.replace('_', '-')}")
            require_positive(name, value)
        mu = args.mu_m is not None or args.mu_f is not None
        nu = args.nu_m is not None or args.nu_f is not None
        if mu and nu:
            raise ValueError("pass viscosity or kinematic viscosity, not both")
        if mu:
            if args.mu_m is None or args.mu_f is None or args.rho_m is None or args.rho_f is None:
                raise ValueError("--mu-m and --mu-f need --rho-m and --rho-f")
            require_positive("mu-m", args.mu_m)
            require_positive("mu-f", args.mu_f)
            require_positive("rho-m", args.rho_m)
            require_positive("rho-f", args.rho_f)
            re_m = args.rho_m * args.V_m * args.L_m / args.mu_m
            re_f = args.rho_f * args.V_f * args.L_f / args.mu_f
        elif nu:
            if args.nu_m is None or args.nu_f is None:
                raise ValueError("pass both --nu-m and --nu-f")
            require_positive("nu-m", args.nu_m)
            require_positive("nu-f", args.nu_f)
            re_m = args.V_m * args.L_m / args.nu_m
            re_f = args.V_f * args.L_f / args.nu_f
        else:
            raise ValueError("flow path needs --mu-m/--mu-f or --nu-m/--nu-f")
        mach_m = args.V_m / args.a_m
        mach_f = args.V_f / args.a_f
        path = "flow"
    else:
        raise ValueError("pass Reynolds and Mach numbers, or the flow quantities")

    re_err = relative_mismatch(re_m, re_f)
    mach_err = relative_mismatch(mach_m, mach_f)
    result: dict[str, object] = {
        "path": path,
        "Re_m": re_m,
        "Re_f": re_f,
        "Mach_m": mach_m,
        "Mach_f": mach_f,
        "Re_mismatch": re_err,
        "Mach_mismatch": mach_err,
        "Re_match": match_flag(re_err),
        "Mach_match": match_flag(mach_err),
        "mismatch_limit": MISMATCH,
    }
    q_m, q_f = dynamic_pressures(args)
    if q_m is not None:
        result["q_m_Pa"] = q_m
        result["q_f_Pa"] = q_f
    if args.force_m is not None:
        if q_m is None or args.S_m is None or args.S_f is None:
            raise ValueError("--force-m needs dynamic pressure and --S-m --S-f")
        require_positive("S-m", args.S_m)
        require_positive("S-f", args.S_f)
        scale = (q_f * args.S_f) / (q_m * args.S_m)
        result["force_m_N"] = args.force_m
        result["force_f_N"] = args.force_m * scale
    if args.moment_m is not None:
        if q_m is None or None in (args.S_m, args.S_f, args.c_m, args.c_f):
            raise ValueError("--moment-m needs q, area, and chord for both scales")
        require_positive("c-m", args.c_m)
        require_positive("c-f", args.c_f)
        scale = (q_f * args.S_f * args.c_f) / (q_m * args.S_m * args.c_m)
        result["moment_m_Nm"] = args.moment_m
        result["moment_f_Nm"] = args.moment_m * scale
    return result


def dynamic_pressures(args: argparse.Namespace) -> tuple[float | None, float | None]:
    given = args.q_m is not None or args.q_f is not None
    flow = args.rho_m is not None and args.V_m is not None and args.rho_f is not None and args.V_f is not None
    if given and (args.q_m is None or args.q_f is None):
        raise ValueError("--q-m and --q-f are a pair")
    if given:
        require_positive("q-m", args.q_m)
        require_positive("q-f", args.q_f)
        return args.q_m, args.q_f
    if flow:
        require_positive("rho-m", args.rho_m)
        require_positive("rho-f", args.rho_f)
        require_positive("V-m", args.V_m)
        require_positive("V-f", args.V_f)
        return dynamic_pressure(args.rho_m, args.V_m), dynamic_pressure(args.rho_f, args.V_f)
    return None, None


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "path",
        "Re_m",
        "Re_f",
        "Mach_m",
        "Mach_f",
        "Re_mismatch",
        "Mach_mismatch",
        "Re_match",
        "Mach_match",
        "mismatch_limit",
        "q_m_Pa",
        "q_f_Pa",
        "force_m_N",
        "force_f_N",
        "moment_m_Nm",
        "moment_f_Nm",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.2))
    axes[0].bar(["model", "full"], [float(result["Re_m"]), float(result["Re_f"])], color="C0")
    axes[0].set_ylabel("Reynolds number")
    axes[0].set_title("Reynolds number")
    axes[1].bar(["model", "full"], [float(result["Mach_m"]), float(result["Mach_f"])], color="C1")
    axes[1].set_ylabel("Mach number")
    axes[1].set_title("Mach number")
    fig.suptitle("Wind-tunnel similarity")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    ratio = relative_mismatch(1.1, 1.0)
    if not close(ratio, 0.1) or match_flag(ratio) != "mismatch":
        return fail("ten percent mismatch")
    if match_flag(0.05) != "matched":
        return fail("limit should match")
    scale = (2.0 * 3.0) / (1.0 * 2.0)
    if not close(scale, 3.0):
        return fail("force scale")
    moment = (2.0 * 3.0 * 4.0) / (1.0 * 2.0 * 2.0)
    if not close(moment, 6.0):
        return fail("moment scale")
    numbers = solve(
        argparse.Namespace(
            re_m=1.1e6,
            re_f=1.0e6,
            mach_m=0.3,
            mach_f=0.3,
            L_m=None,
            L_f=None,
            V_m=None,
            V_f=None,
            rho_m=None,
            rho_f=None,
            mu_m=None,
            mu_f=None,
            nu_m=None,
            nu_f=None,
            a_m=None,
            a_f=None,
            q_m=1.0,
            q_f=2.0,
            force_m=10.0,
            moment_m=4.0,
            S_m=2.0,
            S_f=3.0,
            c_m=2.0,
            c_f=4.0,
        )
    )
    if numbers["Re_match"] != "mismatch" or numbers["Mach_match"] != "matched":
        return fail("match flags")
    if not close(float(numbers["force_f_N"]), 30.0):
        return fail("scaled force")
    if not close(float(numbers["moment_f_Nm"]), 24.0):
        return fail("scaled moment")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(numbers, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("force_f_N", float(numbers["force_f_N"]))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wind-tunnel Reynolds and Mach match, and load scale.")
    parser.add_argument("--re-m", type=float, default=None, help="model Reynolds number")
    parser.add_argument("--re-f", type=float, default=None, help="full-scale Reynolds number")
    parser.add_argument("--mach-m", type=float, default=None, help="model Mach number")
    parser.add_argument("--mach-f", type=float, default=None, help="full-scale Mach number")
    parser.add_argument("--L-m", type=float, default=None, help="model length [m]")
    parser.add_argument("--L-f", type=float, default=None, help="full-scale length [m]")
    parser.add_argument("--V-m", type=float, default=None, help="model speed [m/s]")
    parser.add_argument("--V-f", type=float, default=None, help="full-scale speed [m/s]")
    parser.add_argument("--rho-m", type=float, default=None, help="model density [kg/m^3]")
    parser.add_argument("--rho-f", type=float, default=None, help="full-scale density [kg/m^3]")
    parser.add_argument("--mu-m", type=float, default=None, help="model viscosity [Pa s]")
    parser.add_argument("--mu-f", type=float, default=None, help="full-scale viscosity [Pa s]")
    parser.add_argument("--nu-m", type=float, default=None, help="model kinematic viscosity [m^2/s]")
    parser.add_argument("--nu-f", type=float, default=None, help="full-scale kinematic viscosity [m^2/s]")
    parser.add_argument("--a-m", type=float, default=None, help="model speed of sound [m/s]")
    parser.add_argument("--a-f", type=float, default=None, help="full-scale speed of sound [m/s]")
    parser.add_argument("--q-m", type=float, default=None, help="model dynamic pressure [Pa]")
    parser.add_argument("--q-f", type=float, default=None, help="full-scale dynamic pressure [Pa]")
    parser.add_argument("--force-m", type=float, default=None, help="measured model force [N]")
    parser.add_argument("--moment-m", type=float, default=None, help="measured model moment [N*m]")
    parser.add_argument("--S-m", type=float, default=None, help="model reference area [m^2]")
    parser.add_argument("--S-f", type=float, default=None, help="full-scale reference area [m^2]")
    parser.add_argument("--c-m", type=float, default=None, help="model reference chord [m]")
    parser.add_argument("--c-f", type=float, default=None, help="full-scale reference chord [m]")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        result = solve(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "wind_tunnel_similarity.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
