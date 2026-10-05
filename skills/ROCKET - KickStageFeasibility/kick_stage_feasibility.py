#!/usr/bin/env python3
"""T/W and burn-time feasibility for an in-space kick stage.

Vacuum constant-thrust rocket equation, continuous-burn and restart limits,
and coast attitude-control duration limits. Does not integrate a trajectory
or gravity loss.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

G0 = 9.80665
CHECK_TOL = 1e-9
PLOT_TITLE = "Kick-stage T/W and burn-time feasibility"
ASSUMPTIONS = (
    "in-space kick stage; vacuum; constant thrust and constant Isp over each "
    "powered arc; ideal rocket equation with c = Isp * g0; no gravity loss, "
    "drag, or trajectory integration; T/W = T/(m*g0) uses g0 = 9.80665 m/s^2 "
    "as the weight reference (not a lift-off constraint); T/W bounds are "
    "checked at every equal-split burn ignition mass (and burnout); total "
    "burn time is tb = (m0 - mf)*c/T; when --burns is omitted the program "
    "chooses the fewest equal-duration burns that each stay within --tb-max; "
    "restarts used are n_burns - 1; --coast-max is a per-coast duration "
    "limit checked against the peak coast; --acs-mp/--acs-mdot give a total "
    "ACS propellant budget checked against the sum of coast durations; "
    "multi-burn plans with a coast limit but no --coast are not feasible"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_finite(value: float, flag: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{flag} must be finite")


def exhaust_velocity(isp: float) -> float:
    """c = Isp * g0."""
    return isp * G0


def mass_flow(thrust: float, c: float) -> float:
    """mdot = T / c."""
    return thrust / c


def burnout_from_propellant(m0: float, mp: float) -> float:
    return m0 - mp


def propellant_from_delta_v(m0: float, dv: float, c: float) -> float:
    """mp = m0 * (1 - exp(-dv/c))."""
    return m0 * (1.0 - math.exp(-dv / c))


def delta_v_from_masses(m0: float, mf: float, c: float) -> float:
    """dv = c * ln(m0/mf)."""
    return c * math.log(m0 / mf)


def burn_time(m0: float, mf: float, thrust: float, c: float) -> float:
    """tb = (m0 - mf) * c / T."""
    return (m0 - mf) * c / thrust


def thrust_to_weight(thrust: float, mass: float) -> float:
    """T/W = T / (m * g0)."""
    return thrust / (mass * G0)


def burns_needed(tb_total: float, tb_max: float) -> int:
    """Fewest equal burns that each stay within tb_max."""
    if tb_total <= 0.0:
        return 0
    return max(1, int(math.ceil(tb_total / tb_max - 1e-15)))


def verdict(ok: bool) -> str:
    return "pass" if ok else "fail"


def run_check() -> int:
    isp = 300.0
    c = exhaust_velocity(isp)
    if abs(c - 2941.995) > 1e-6:
        print(f"CHECK FAIL: c = {c}", file=sys.stderr)
        return 1

    thrust = 1000.0
    m0 = 500.0
    dv = 500.0
    mp = propellant_from_delta_v(m0, dv, c)
    mf = burnout_from_propellant(m0, mp)
    tb = burn_time(m0, mf, thrust, c)
    mdot = mass_flow(thrust, c)
    if abs(mp - mdot * tb) > CHECK_TOL:
        print("CHECK FAIL: mp != mdot * tb", file=sys.stderr)
        return 1
    if abs(delta_v_from_masses(m0, mf, c) - dv) > 1e-9:
        print("CHECK FAIL: round-trip delta-v", file=sys.stderr)
        return 1

    tw0 = thrust_to_weight(thrust, m0)
    if abs(tw0 - thrust / (m0 * G0)) > CHECK_TOL:
        print(f"CHECK FAIL: T/W0 = {tw0}", file=sys.stderr)
        return 1

    if burns_needed(100.0, 40.0) != 3:
        print("CHECK FAIL: burns_needed(100, 40)", file=sys.stderr)
        return 1
    if burns_needed(40.0, 40.0) != 1:
        print("CHECK FAIL: burns_needed(40, 40)", file=sys.stderr)
        return 1
    if burns_needed(40.0000001, 40.0) != 2:
        print("CHECK FAIL: burns_needed just over tb_max", file=sys.stderr)
        return 1

    # ACS budget is a sum check, not peak-only.
    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "acs.png")
        sink = sys.stdout
        sys.stdout = tempfile.TemporaryFile(mode="w+")
        try:
            # Two 80 s coasts, ACS capacity 100 s: peak OK, sum fails.
            code = main(
                [
                    "--thrust",
                    "500",
                    "--isp",
                    "300",
                    "--m0",
                    "200",
                    "--mp",
                    "80",
                    "--tb-max",
                    "200",
                    "--restarts-max",
                    "2",
                    "--burns",
                    "3",
                    "--coast",
                    "80",
                    "--coast",
                    "80",
                    "--acs-mp",
                    "10",
                    "--acs-mdot",
                    "0.1",
                    "--out",
                    out,
                ]
            )
            sys.stdout.seek(0)
            text = sys.stdout.read()
        finally:
            sys.stdout.close()
            sys.stdout = sink
        if code != 0:
            print(f"CHECK FAIL: ACS sum case returned {code}", file=sys.stderr)
            return 1
        if "feasible: no" not in text:
            print("CHECK FAIL: ACS sum budget should be infeasible", file=sys.stderr)
            return 1
        if "coast_sum_s: 160" not in text and "coast_sum_s: 160.0" not in text:
            # allow .8g formatting
            if "coast_sum_s: 160" not in text:
                print("CHECK FAIL: missing coast_sum_s", file=sys.stderr)
                return 1

    print("check: pass")
    print_kv("c_m_s", c)
    print_kv("mp_kg", mp)
    print_kv("mf_kg", mf)
    print_kv("tb_s", tb)
    print_kv("TW0", tw0)
    return 0


def write_plot(
    out_path: Path,
    tw0: float,
    twf: float,
    tb_each: float,
    tb_total: float,
    tb_max: float,
    tw_min: float | None,
    tw_max: float | None,
    feasible: bool,
) -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    ax.set_title(PLOT_TITLE)
    ax.set_xlabel("Burn time per arc (s)")
    ax.set_ylabel("Thrust-to-weight T/(m g0)")

    x_hi = max(tb_max * 1.15, tb_each * 1.15, tb_total * 0.35, 1.0)
    y_lo = 0.0
    y_hi = max(twf * 1.25, (tw_max or 0.0) * 1.25, tw0 * 1.25, 0.1)

    band_lo = tw_min if tw_min is not None else y_lo
    band_hi = tw_max if tw_max is not None else y_hi
    ax.axvspan(0.0, tb_max, color="#d5f5e3", alpha=0.55, label="tb ≤ tb_max")
    if tw_min is not None or tw_max is not None:
        ax.axhspan(band_lo, band_hi, color="#d6eaf8", alpha=0.45, label="T/W band")

    ax.axvline(tb_max, color="#1e8449", linestyle="--", linewidth=1.2, label="tb_max")
    if tw_min is not None:
        ax.axhline(tw_min, color="#2874a6", linestyle="--", linewidth=1.0, label="T/W min")
    if tw_max is not None:
        ax.axhline(tw_max, color="#6c3483", linestyle="--", linewidth=1.0, label="T/W max")

    color = "#196f3d" if feasible else "#922b21"
    ax.plot([tb_each], [tw0], "o", color=color, markersize=10, label="ignition T/W")
    ax.plot([tb_each], [twf], "s", color=color, markersize=8, label="burnout T/W")
    ax.annotate(
        "ignition",
        (tb_each, tw0),
        textcoords="offset points",
        xytext=(8, 6),
        fontsize=9,
    )
    ax.annotate(
        "burnout",
        (tb_each, twf),
        textcoords="offset points",
        xytext=(8, -12),
        fontsize=9,
    )
    ax.annotate(
        f"total tb={tb_total:.4g} s",
        (tb_each, 0.5 * (tw0 + twf)),
        textcoords="offset points",
        xytext=(8, 0),
        fontsize=8,
        color="#566573",
    )

    ax.set_xlim(0.0, x_hi)
    ax.set_ylim(y_lo, y_hi)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "T/W and burn-time feasibility for a kick stage "
            "(coast ACS limits, max burn duration, restart count)."
        )
    )
    parser.add_argument("--thrust", type=float, default=None, help="vacuum thrust T [N]")
    parser.add_argument("--isp", type=float, default=None, help="vacuum specific impulse [s]")
    parser.add_argument("--m0", type=float, default=None, help="ignition mass [kg]")
    mass = parser.add_mutually_exclusive_group()
    mass.add_argument("--mf", type=float, default=None, help="burnout mass [kg]")
    mass.add_argument("--mp", type=float, default=None, help="usable propellant mass [kg]")
    mass.add_argument("--dv", type=float, default=None, help="ideal vacuum delta-v [m/s]")
    parser.add_argument(
        "--tb-max",
        type=float,
        default=None,
        help="maximum continuous burn duration per powered arc [s]",
    )
    parser.add_argument(
        "--restarts-max",
        type=int,
        default=None,
        help="maximum main-engine restarts after the first ignition",
    )
    parser.add_argument(
        "--burns",
        type=int,
        default=None,
        help="planned number of powered arcs; omit to use the fewest that fit tb-max",
    )
    parser.add_argument(
        "--coast",
        type=float,
        action="append",
        default=None,
        help="coast duration between burns [s]; repeat in order between burns",
    )
    parser.add_argument(
        "--coast-max",
        type=float,
        default=None,
        help="maximum coast duration the attitude-control system can support [s]",
    )
    parser.add_argument(
        "--acs-mp",
        type=float,
        default=None,
        help="usable ACS propellant mass for coast attitude control [kg]",
    )
    parser.add_argument(
        "--acs-mdot",
        type=float,
        default=None,
        help="ACS effective propellant mass-flow during coast control [kg/s]",
    )
    parser.add_argument(
        "--tw-min",
        type=float,
        default=None,
        help="minimum allowed ignition T/W",
    )
    parser.add_argument(
        "--tw-max",
        type=float,
        default=None,
        help="maximum allowed ignition T/W",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    required = {
        "--thrust": args.thrust,
        "--isp": args.isp,
        "--m0": args.m0,
        "--tb-max": args.tb_max,
        "--restarts-max": args.restarts_max,
    }
    missing = [flag for flag, value in required.items() if value is None]
    if args.mf is None and args.mp is None and args.dv is None:
        missing.append("--mf|--mp|--dv")
    if missing:
        print(
            "error: requires --thrust, --isp, --m0, one of --mf/--mp/--dv, "
            f"--tb-max, and --restarts-max; missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    try:
        for flag, value in (
            ("--thrust", args.thrust),
            ("--isp", args.isp),
            ("--m0", args.m0),
            ("--tb-max", args.tb_max),
        ):
            require_finite(value, flag)
        if args.mf is not None:
            require_finite(args.mf, "--mf")
        if args.mp is not None:
            require_finite(args.mp, "--mp")
        if args.dv is not None:
            require_finite(args.dv, "--dv")
        if args.tw_min is not None:
            require_finite(args.tw_min, "--tw-min")
        if args.tw_max is not None:
            require_finite(args.tw_max, "--tw-max")
        if args.coast_max is not None:
            require_finite(args.coast_max, "--coast-max")
        if args.acs_mp is not None:
            require_finite(args.acs_mp, "--acs-mp")
        if args.acs_mdot is not None:
            require_finite(args.acs_mdot, "--acs-mdot")
        if args.coast:
            for i, coast in enumerate(args.coast):
                require_finite(coast, f"--coast[{i}]")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.thrust <= 0.0:
        print("error: thrust must be > 0 N", file=sys.stderr)
        return 2
    if args.isp <= 0.0:
        print("error: Isp must be > 0 s", file=sys.stderr)
        return 2
    if args.m0 <= 0.0:
        print("error: m0 must be > 0 kg", file=sys.stderr)
        return 2
    if args.tb_max <= 0.0:
        print("error: tb-max must be > 0 s", file=sys.stderr)
        return 2
    if args.restarts_max < 0:
        print("error: restarts-max must be >= 0", file=sys.stderr)
        return 2
    if args.burns is not None and args.burns < 1:
        print("error: burns must be >= 1", file=sys.stderr)
        return 2
    if args.tw_min is not None and args.tw_min < 0.0:
        print("error: tw-min must be >= 0", file=sys.stderr)
        return 2
    if args.tw_max is not None and args.tw_max <= 0.0:
        print("error: tw-max must be > 0", file=sys.stderr)
        return 2
    if args.tw_min is not None and args.tw_max is not None and args.tw_min > args.tw_max:
        print("error: tw-min must be <= tw-max", file=sys.stderr)
        return 2
    if (args.acs_mp is None) ^ (args.acs_mdot is None):
        print("error: --acs-mp and --acs-mdot must be given together", file=sys.stderr)
        return 2
    if args.acs_mp is not None and args.acs_mp <= 0.0:
        print("error: acs-mp must be > 0 kg", file=sys.stderr)
        return 2
    if args.acs_mdot is not None and args.acs_mdot <= 0.0:
        print("error: acs-mdot must be > 0 kg/s", file=sys.stderr)
        return 2
    if args.coast_max is not None and args.coast_max <= 0.0:
        print("error: coast-max must be > 0 s", file=sys.stderr)
        return 2
    if args.coast:
        for i, coast in enumerate(args.coast):
            if coast < 0.0:
                print(f"error: --coast[{i}] must be >= 0 s", file=sys.stderr)
                return 2

    c = exhaust_velocity(args.isp)
    mdot = mass_flow(args.thrust, c)

    if args.mp is not None:
        if args.mp <= 0.0 or args.mp >= args.m0:
            print("error: mp must satisfy 0 < mp < m0", file=sys.stderr)
            return 2
        mp = args.mp
        mf = burnout_from_propellant(args.m0, mp)
        dv = delta_v_from_masses(args.m0, mf, c)
        mass_source = "mp"
    elif args.mf is not None:
        if args.mf <= 0.0 or args.mf >= args.m0:
            print("error: mf must satisfy 0 < mf < m0", file=sys.stderr)
            return 2
        mf = args.mf
        mp = args.m0 - mf
        dv = delta_v_from_masses(args.m0, mf, c)
        mass_source = "mf"
    else:
        if args.dv <= 0.0:
            print("error: dv must be > 0 m/s", file=sys.stderr)
            return 2
        mp = propellant_from_delta_v(args.m0, args.dv, c)
        if mp <= 0.0 or mp >= args.m0:
            print("error: dv implies a propellant mass outside (0, m0)", file=sys.stderr)
            return 2
        mf = burnout_from_propellant(args.m0, mp)
        dv = args.dv
        mass_source = "dv"

    tb_total = burn_time(args.m0, mf, args.thrust, c)
    tw0 = thrust_to_weight(args.thrust, args.m0)
    twf = thrust_to_weight(args.thrust, mf)

    n_min_for_tb = burns_needed(tb_total, args.tb_max)
    if args.burns is None:
        n_burns = n_min_for_tb
        burns_source = "tb_max"
    else:
        n_burns = args.burns
        burns_source = "input"

    # Equal propellant split across burns (constant mdot ⇒ equal burn times).
    tb_each = tb_total / n_burns if n_burns > 0 else 0.0
    mp_each = mp / n_burns if n_burns > 0 else 0.0
    restarts_used = max(0, n_burns - 1)
    restarts_budget = args.restarts_max
    ignitions_budget = restarts_budget + 1

    coast_duration_max = args.coast_max
    acs_capacity = None
    if args.acs_mp is not None and args.acs_mdot is not None:
        acs_capacity = args.acs_mp / args.acs_mdot

    coasts = list(args.coast) if args.coast else []
    if coasts and len(coasts) != restarts_used:
        print(
            "error: pass exactly one --coast per gap between burns "
            f"(need {restarts_used}, got {len(coasts)})",
            file=sys.stderr,
        )
        return 2

    # Equal propellant split: ignition mass for burn k (1-indexed) is m0 - (k-1)*mp_each.
    tw_ignitions: list[float] = []
    for k in range(n_burns):
        m_ign = args.m0 - k * mp_each
        if m_ign <= 0.0:
            print("error: equal burn split drives an ignition mass <= 0", file=sys.stderr)
            return 2
        tw_ignitions.append(thrust_to_weight(args.thrust, m_ign))
    tw_ignition_max = max(tw_ignitions) if tw_ignitions else tw0
    tw_ignition_min = min(tw_ignitions) if tw_ignitions else tw0

    tw_ok = True
    if args.tw_min is not None and tw_ignition_min < args.tw_min:
        tw_ok = False
    if args.tw_max is not None and tw_ignition_max > args.tw_max:
        tw_ok = False

    burn_ok = tb_each <= args.tb_max + 1e-12
    restart_ok = restarts_used <= restarts_budget
    burns_vs_min_ok = n_burns >= n_min_for_tb

    coast_limit_present = coast_duration_max is not None or acs_capacity is not None
    coast_peak = max(coasts) if coasts else None
    coast_sum = sum(coasts) if coasts else None
    peak_ok = True
    acs_ok = True
    if not coasts:
        if n_burns > 1 and coast_limit_present:
            coast_ok = False
            coast_status = "unchecked_fail"
        else:
            coast_ok = True
            coast_status = "unchecked" if not coast_limit_present else "n/a"
    else:
        if coast_duration_max is not None:
            peak_ok = coast_peak <= coast_duration_max + 1e-12
        if acs_capacity is not None:
            acs_ok = coast_sum <= acs_capacity + 1e-12
        if coast_duration_max is None and acs_capacity is None:
            coast_ok = True
            coast_status = "no_limit"
        else:
            coast_ok = peak_ok and acs_ok
            coast_status = verdict(coast_ok)

    overall = tw_ok and burn_ok and restart_ok and burns_vs_min_ok and coast_ok

    warnings: list[str] = []
    if not burns_vs_min_ok:
        warnings.append(
            f"planned burns ({n_burns}) are fewer than the minimum "
            f"({n_min_for_tb}) needed for tb-max"
        )
    if not burn_ok:
        warnings.append("at least one powered arc exceeds tb-max")
    if not restart_ok:
        warnings.append(
            f"restarts used ({restarts_used}) exceed restarts-max ({restarts_budget})"
        )
    if args.tw_min is not None and tw_ignition_min < args.tw_min:
        warnings.append("a burn ignition T/W is below tw-min")
    if args.tw_max is not None and tw_ignition_max > args.tw_max:
        warnings.append("a burn ignition T/W is above tw-max")
    if coasts and coast_duration_max is not None and not peak_ok:
        warnings.append("a coast exceeds --coast-max duration")
    if coasts and acs_capacity is not None and not acs_ok:
        warnings.append(
            "sum of coast durations exceeds ACS propellant coast capacity"
        )
    if n_burns > 1 and not coasts and coast_limit_present:
        warnings.append(
            "multi-burn plan has a coast limit but no --coast durations were given"
        )
    if tw_ignition_max >= 1.0:
        warnings.append(
            "a burn ignition T/W >= 1; unusual for a kick stage but allowed if within tw-max"
        )

    print_kv("assumptions", ASSUMPTIONS)
    print_kv("g0_m_s2", G0)
    print_kv("thrust_N", args.thrust)
    print_kv("isp_s", args.isp)
    print_kv("c_m_s", c)
    print_kv("m0_kg", args.m0)
    print_kv("mf_kg", mf)
    print_kv("mp_kg", mp)
    print_kv("mass_source", mass_source)
    print_kv("dv_ideal_m_s", dv)
    print_kv("mdot_kg_s", mdot)
    print_kv("tb_total_s", tb_total)
    print_kv("TW0", tw0)
    print_kv("TWf", twf)
    print_kv("TW_ignition_min", tw_ignition_min)
    print_kv("TW_ignition_max", tw_ignition_max)
    for i, tw_ign in enumerate(tw_ignitions, start=1):
        print_kv(f"TW_ignition_{i}", tw_ign)
    if args.tw_min is not None:
        print_kv("TW_min", args.tw_min)
    else:
        print_kv("TW_min", "none")
    if args.tw_max is not None:
        print_kv("TW_max", args.tw_max)
    else:
        print_kv("TW_max", "none")
    print_kv("TW_check", verdict(tw_ok))
    print_kv("tb_max_s", args.tb_max)
    print_kv("n_burns_min_for_tb_max", n_min_for_tb)
    print_kv("n_burns", n_burns)
    print_kv("n_burns_source", burns_source)
    print_kv("tb_each_s", tb_each)
    print_kv("mp_each_kg", mp_each)
    print_kv("burn_duration_check", verdict(burn_ok))
    print_kv("restarts_max", restarts_budget)
    print_kv("ignitions_max", ignitions_budget)
    print_kv("restarts_used", restarts_used)
    print_kv("restart_check", verdict(restart_ok))

    if args.acs_mp is not None:
        print_kv("acs_mp_kg", args.acs_mp)
        print_kv("acs_mdot_kg_s", args.acs_mdot)
        print_kv("coast_capacity_from_acs_s", acs_capacity if acs_capacity is not None else 0.0)
    else:
        print_kv("acs_mp_kg", "none")
        print_kv("acs_mdot_kg_s", "none")
        print_kv("coast_capacity_from_acs_s", "none")

    if coast_duration_max is not None:
        print_kv("coast_max_s", coast_duration_max)
        print_kv("coast_max_source", "input")
    else:
        print_kv("coast_max_s", "none")
        print_kv("coast_max_source", "none")

    if coasts:
        print_kv("n_coasts", len(coasts))
        for i, coast in enumerate(coasts, start=1):
            print_kv(f"coast_{i}_s", coast)
        print_kv("coast_peak_s", coast_peak if coast_peak is not None else 0.0)
        print_kv("coast_sum_s", coast_sum if coast_sum is not None else 0.0)
        print_kv("coast_peak_check", verdict(peak_ok) if coast_duration_max is not None else "n/a")
        print_kv("coast_acs_check", verdict(acs_ok) if acs_capacity is not None else "n/a")
        print_kv("coast_check", coast_status)
    else:
        print_kv("n_coasts", 0)
        print_kv("coast_peak_s", "none")
        print_kv("coast_sum_s", "none")
        print_kv("coast_peak_check", "n/a")
        print_kv("coast_acs_check", "n/a")
        print_kv("coast_check", coast_status)

    print_kv("feasible", "yes" if overall else "no")
    for warning in warnings:
        print_kv("warning", warning)

    out_path = Path(args.out) if args.out else Path(__file__).resolve().parent / (
        "kick_stage_feasibility.png"
    )
    # Always write a PNG for a successful run (house pattern for plot skills).
    write_plot(
        out_path,
        tw0=tw0,
        twf=twf,
        tb_each=tb_each,
        tb_total=tb_total,
        tb_max=args.tb_max,
        tw_min=args.tw_min,
        tw_max=args.tw_max,
        feasible=overall,
    )
    print_kv("graph", str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
