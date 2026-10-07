#!/usr/bin/env python3
"""Design ideal delta-v for a circular LEO.

leo_design_delta_v = v_circ - rotation assist + gravity + drag + steering
+ circularization + margin. v_circ is sqrt(mu/r).
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

G0 = 9.80665
R0 = 6.3742e6
SKILL_DIR = Path(__file__).resolve().parent
CHART_DIR = SKILL_DIR.parents[1] / "app" / "tests"
if str(CHART_DIR) not in sys.path:
    sys.path.insert(0, str(CHART_DIR))
import leo_chart  # noqa: E402

PLOT_TITLE = "LEO delta-v budget"
ASSUMPTIONS = (
    "leo_design_delta_v; circular speed sqrt(mu/r); "
    f"default R0 = {R0:.6g} m and g0 = {G0} m/s^2 so mu = g0*R0^2; "
    "rotation assist, losses, circularization, and margin are inputs "
    "(zero when omitted); margin-fraction applies to the sum before margin; "
    "the result is an ideal vacuum delta-v for PayloadtoDeltaV, not a trajectory"
)


def print_kv(key: str, value: object) -> None:
    text = f"{value:.8g}" if isinstance(value, float) else str(value)
    print(f"{key}: {text}")


def design_delta_v(vcirc: float, vrot: float, gravity: float, drag: float, steering: float, circ: float, margin: float) -> float:
    return vcirc - vrot + gravity + drag + steering + circ + margin


def run(args: argparse.Namespace) -> int:
    if args.alt is None and args.r is None:
        raise ValueError("pass --alt or --r")
    if args.alt is not None and args.r is not None:
        raise ValueError("pass --alt or --r, not both")
    radius_body = R0 if args.radius is None else args.radius
    if radius_body <= 0.0:
        raise ValueError("radius must be > 0")
    if args.mu is None:
        mu = G0 * radius_body * radius_body
        mu_source = "g0_R2"
    else:
        mu = args.mu
        mu_source = "input"
    if mu <= 0.0:
        raise ValueError("mu must be > 0")
    if args.alt is not None:
        if args.alt < 0.0:
            raise ValueError("altitude must be >= 0")
        radius = radius_body + args.alt
        alt = args.alt
    else:
        if args.r < radius_body:
            raise ValueError("radius is inside the body")
        radius = args.r
        alt = args.r - radius_body
    v_circ = math.sqrt(mu / radius)
    vrot = 0.0 if args.v_rot is None else args.v_rot
    gravity = 0.0 if args.gravity_loss is None else args.gravity_loss
    drag = 0.0 if args.drag_loss is None else args.drag_loss
    steering = 0.0 if args.steering_loss is None else args.steering_loss
    circ = 0.0 if args.circ is None else args.circ
    for name, value in (
        ("rotation assist", vrot),
        ("gravity loss", gravity),
        ("drag loss", drag),
        ("steering loss", steering),
        ("circularization", circ),
    ):
        if value < 0.0:
            raise ValueError(f"{name} must be >= 0")
    base = design_delta_v(v_circ, vrot, gravity, drag, steering, circ, 0.0)
    if args.margin is not None and args.margin_fraction is not None:
        raise ValueError("pass --margin or --margin-fraction, not both")
    if args.margin_fraction is not None:
        if args.margin_fraction < 0.0:
            raise ValueError("margin fraction must be >= 0")
        margin = args.margin_fraction * base
        margin_source = "fraction"
    elif args.margin is not None:
        if args.margin < 0.0:
            raise ValueError("margin must be >= 0")
        margin = args.margin
        margin_source = "absolute"
    else:
        margin = 0.0
        margin_source = "omitted"
    total = base + margin
    terms = [
        ("circular", v_circ),
        ("rotation", -vrot),
        ("gravity", gravity),
        ("drag", drag),
        ("steering", steering),
        ("circularization", circ),
        ("margin", margin),
    ]
    out = Path(args.out).resolve() if args.out else (SKILL_DIR / "leo_delta_v_budget.png")
    leo_chart.write_chart(
        out,
        PLOT_TITLE,
        {
            "kind": "waterfall",
            "unit": "m/s",
            "note": "Checked rows are included. A red bar is a credit that reduces the total.",
            "terms": [{"name": name, "value": value} for name, value in terms],
        },
        html=False,
    )
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mu_source", mu_source)
    print_kv("mu_m3_s2", mu)
    print_kv("R_body_m", radius_body)
    print_kv("r_target_m", radius)
    print_kv("h_target_m", alt)
    print_kv("v_circ_m_s", v_circ)
    print_kv("v_rot_assist_m_s", vrot)
    print_kv("gravity_loss_m_s", gravity)
    print_kv("drag_loss_m_s", drag)
    print_kv("steering_loss_m_s", steering)
    print_kv("dv_circ_m_s", circ)
    print_kv("margin_source", margin_source)
    print_kv("margin_m_s", margin)
    print_kv("dv_design_m_s", total)
    print_kv("graph", str(out))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    import io
    import tempfile

    # Equatorial due-east, zero losses: v_circ - omega*R at the surface radius used here.
    omega = 7.292115e-5
    v_circ = math.sqrt(G0 * R0 * R0 / R0)
    assist = omega * R0
    total = design_delta_v(v_circ, assist, 0.0, 0.0, 0.0, 0.0, 0.0)
    if abs(total - (v_circ - assist)) > 1e-6:
        return fail("zero-loss identity")
    stacked = design_delta_v(8000, 400, 1000, 100, 50, 200, 150)
    if abs(stacked - 9100) > 1e-9:
        return fail("term sum")
    with tempfile.TemporaryDirectory() as tmp:
        png = str(Path(tmp) / "out.png")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(["--alt", "0", "--v-rot", str(assist), "--out", png])
        finally:
            sys.stdout = old
        if code != 0 or "dv_design_m_s:" not in buf.getvalue():
            return fail("cli")
        if not Path(png).is_file():
            return fail("png")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LEO design delta-v budget.")
    parser.add_argument("--alt", type=float, default=None)
    parser.add_argument("--r", type=float, default=None)
    parser.add_argument("--radius", type=float, default=None)
    parser.add_argument("--mu", type=float, default=None)
    parser.add_argument("--v-rot", type=float, default=None)
    parser.add_argument("--gravity-loss", type=float, default=None)
    parser.add_argument("--drag-loss", type=float, default=None)
    parser.add_argument("--steering-loss", type=float, default=None)
    parser.add_argument("--circ", type=float, default=None)
    parser.add_argument("--margin", type=float, default=None)
    parser.add_argument("--margin-fraction", type=float, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
