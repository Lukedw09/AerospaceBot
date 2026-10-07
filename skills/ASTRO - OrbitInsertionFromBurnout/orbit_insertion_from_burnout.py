#!/usr/bin/env python3
"""Burnout state to a parking orbit and an apoapsis circularization burn.

Uses specific_orbital_energy_from_speed, specific_angular_momentum_flight_path,
semimajor_axis_from_energy, eccentricity_from_energy, periapsis_radius,
apoapsis_radius, and circularization_delta_v.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import webbrowser
from pathlib import Path

G0 = 9.80665
R0 = 6.3742e6
ATM_ALT = 120000.0
PLOT_TITLE = "Orbit insertion from burnout"
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "two-body coast after burnout; no drag; "
    "specific energy v^2/2 - mu/r; angular momentum r*v*cos(gamma); "
    "default mu = g0*R0^2 with R0 = 6.3742e6 m and g0 = 9.80665; "
    "atmosphere intersection when periapsis altitude is below 120 km; "
    "circularization_delta_v at apoapsis, or at burnout when the orbit is already nearly circular; "
    "a non-negative energy is not a closed parking orbit"
)


def print_kv(key: str, value: object) -> None:
    text = f"{value:.8g}" if isinstance(value, float) else str(value)
    print(f"{key}: {text}")


def wrap_pi(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def kepler_time(mu: float, a: float, e: float, nu0: float, nu1: float) -> float:
    def eccentric(nu: float) -> float:
        return math.atan2(math.sqrt(1.0 - e * e) * math.sin(nu), e + math.cos(nu))

    def mean(nu: float) -> float:
        ea = eccentric(nu)
        return ea - e * math.sin(ea)

    return math.sqrt(a ** 3 / mu) * wrap_pi(mean(nu1) - mean(nu0))


def run(args: argparse.Namespace) -> int:
    radius_body = R0 if args.radius is None else args.radius
    if args.mu is None:
        mu = G0 * radius_body * radius_body
    else:
        mu = args.mu
    if args.r <= 0.0 or args.v < 0.0 or mu <= 0.0:
        raise ValueError("radius, speed, and mu must be physical")
    if args.gamma < -math.pi / 2.0 or args.gamma > math.pi / 2.0:
        raise ValueError("flight-path angle must lie in [-pi/2, pi/2]")
    energy = args.v ** 2 / 2.0 - mu / args.r
    h = args.r * args.v * math.cos(args.gamma)
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mu_m3_s2", mu)
    print_kv("R_body_m", radius_body)
    print_kv("r_bo_m", args.r)
    print_kv("V_bo_m_s", args.v)
    print_kv("gamma_bo_rad", args.gamma)
    print_kv("energy_m2_s2", energy)
    print_kv("h_m2_s", h)
    # A radial trajectory has no area and is not a closed parking orbit.
    closed = energy < 0.0 and h > 1.0
    nu = 0.0
    r_circ = args.r
    if not closed:
        print_kv("closed_orbit", "no")
        print_kv("warning", "burnout energy is not a closed parking orbit")
        dv = float("nan")
        rp = ra = e = a = float("nan")
    else:
        a = -mu / (2.0 * energy)
        e = math.sqrt(max(0.0, 1.0 + 2.0 * energy * h * h / (mu * mu)))
        rp = a * (1.0 - e)
        ra = a * (1.0 + e)
        print_kv("closed_orbit", "yes")
        print_kv("a_m", a)
        print_kv("e", e)
        print_kv("rp_m", rp)
        print_kv("ra_m", ra)
        print_kv("hp_m", rp - radius_body)
        print_kv("ha_m", ra - radius_body)
        if rp < radius_body + ATM_ALT:
            print_kv("atmosphere_intersection", "yes")
            print_kv("warning", "periapsis is inside the 120 km atmosphere")
        else:
            print_kv("atmosphere_intersection", "no")
        nu = 0.0
        if e > 1e-8:
            cos_nu = (h * h / (mu * args.r) - 1.0) / e
            sin_nu = (args.v * math.sin(args.gamma) * h) / (mu * e)
            nu = math.atan2(sin_nu, max(-1.0, min(1.0, cos_nu)))
            print_kv("nu_bo_rad", nu)
        nearly = e < 1e-4 and abs(args.gamma) < 1e-3
        if nearly:
            dv = math.sqrt(mu / args.r) - args.v
            r_circ = args.r
            print_kv("circularization_where", "burnout")
            print_kv("r_circ_m", args.r)
        else:
            v_a = math.sqrt(mu * (2.0 / ra - 1.0 / a))
            dv = math.sqrt(mu / ra) - v_a
            r_circ = ra
            print_kv("circularization_where", "apoapsis")
            print_kv("r_circ_m", ra)
            print_kv("v_apo_m_s", v_a)
            if e > 1e-8:
                tof = kepler_time(mu, a, min(e, 0.999999), nu, math.pi)
                if tof < 0.0:
                    tof += 2.0 * math.pi * math.sqrt(a ** 3 / mu)
                print_kv("tof_to_apoapsis_s", tof)
        print_kv("dv_circ_m_s", dv)
    requested = Path(args.out).resolve() if args.out else (SKILL_DIR / "orbit_insertion_from_burnout.html")
    html = requested if requested.suffix.lower() == ".html" else requested.with_suffix(".html")
    payload = scene(
        radius_body,
        args.r,
        rp if closed else args.r,
        ra if closed else args.r,
        e if closed else 0.0,
        closed,
        nu,
        r_circ,
        args.gamma,
    )
    write_viewer(html, payload)
    print_kv("viewer", str(html))
    if args.open:
        webbrowser.open(html.as_uri())
    return 0


def outside_segments(rp: float, ra: float, ecc: float, r_min: float, scale: float) -> list[list[list[float]]]:
    """Kepler arc in kilometres, broken wherever it would enter the body."""
    if ra <= 0.0 or rp <= 0.0:
        return []
    a = 0.5 * (ra + rp)
    segments: list[list[list[float]]] = []
    current: list[list[float]] = []
    for k in range(241):
        angle = -math.pi + 2.0 * math.pi * k / 240.0
        denom = 1.0 + ecc * math.cos(angle)
        if denom <= 1e-8:
            if current:
                segments.append(current)
                current = []
            continue
        rad = a * (1.0 - ecc * ecc) / denom
        if rad >= r_min:
            current.append([rad * scale * math.cos(angle), 0.0, rad * scale * math.sin(angle)])
        elif current:
            segments.append(current)
            current = []
    if current:
        segments.append(current)
    return [seg for seg in segments if len(seg) > 1]


def scene(
    radius_body: float,
    r_bo: float,
    rp: float,
    ra: float,
    ecc: float,
    closed: bool,
    nu: float,
    r_circ: float,
    gamma: float,
) -> dict:
    scale = 1.0 / 1000.0
    earth = radius_body * scale
    atm = (radius_body + ATM_ALT) * scale
    marker = [r_bo * scale * math.cos(nu), 0.0, r_bo * scale * math.sin(nu)]
    if closed and ra > 0.0 and rp > 0.0:
        coast = outside_segments(rp, ra, ecc, radius_body, scale)
        span = max(earth, r_circ * scale, r_bo * scale)
        final_alt = r_circ - radius_body
        final_name = "LEO" if ATM_ALT <= final_alt <= 2.0e6 else "Circular orbit"
    else:
        # Departure stays outside the body. A positive flight-path angle climbs away from the center.
        heading = gamma if math.isfinite(gamma) else math.pi / 2.0
        reach = r_bo * scale * 1.35
        coast = [[
            marker,
            [
                marker[0] + (reach - r_bo * scale) * math.cos(heading),
                0.0,
                marker[2] + (reach - r_bo * scale) * math.sin(heading),
            ],
        ]]
        span = max(earth, reach)
        final_name = "Not a closed orbit"
    path = coast[0] if coast else [marker]
    mark = max(40.0, 0.018 * span)
    return {
        "units": "Kilometres. The coast stays outside Earth, then the orbit rises into a circle. Drag to rotate. Scroll to zoom.",
        "R": earth,
        "atm": atm,
        "closed": closed,
        "rp": rp * scale if closed else earth,
        "ra": ra * scale if closed else r_bo * scale,
        "e": ecc if closed else 0.0,
        "nu": nu,
        "rCirc": r_circ * scale if closed else r_bo * scale,
        "finalName": final_name,
        "coast": coast,
        "marker": marker,
        "markerRadius": mark,
        "path": path,
        "camera": {
            "position": [-0.2 * span + 2.4 * span, 1.55 * span, 2.15 * span],
            "target": [-0.2 * span, 0.0, 0.0],
        },
    }


def write_viewer(path: Path, payload: dict) -> None:
    viewer = SKILL_DIR / "viewer"
    template = (viewer / "template.html").read_text(encoding="utf-8")
    three = (viewer / "three.min.js").read_text(encoding="utf-8")
    three = three.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    encoded = json.dumps(payload).replace("<", "\\u003c")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        template.replace("__TITLE__", PLOT_TITLE).replace("__THREE_SOURCE__", three).replace("__SCENE_JSON__", encoded),
        encoding="utf-8",
    )


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    import io
    import tempfile

    mu = G0 * R0 * R0
    r = R0 + 200000.0
    v = math.sqrt(mu / r)
    with tempfile.TemporaryDirectory() as tmp:
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(["--r", str(r), "--v", str(v), "--gamma", "0", "--out", str(Path(tmp) / "circ.png")])
        finally:
            sys.stdout = old
        text = buf.getvalue()
        if code != 0:
            return fail(text)
        dv = float(next(line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("dv_circ_m_s:")))
        if abs(dv) > 1e-6:
            return fail(f"circular dv {dv}")
        if "closed_orbit: yes" not in text:
            return fail("expected closed")
        buf2 = io.StringIO()
        sys.stdout = buf2
        try:
            code = main(["--r", str(R0), "--v", "100", "--gamma", str(math.pi / 2), "--out", str(Path(tmp) / "up.png")])
        finally:
            sys.stdout = old
        text2 = buf2.getvalue()
        if code != 0:
            return fail(text2)
        if "closed_orbit: no" not in text2:
            return fail("vertical burnout should not close")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Orbit insertion from a burnout state.")
    parser.add_argument("--r", type=float)
    parser.add_argument("--v", type=float)
    parser.add_argument("--gamma", type=float)
    parser.add_argument("--mu", type=float, default=None)
    parser.add_argument("--radius", type=float, default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.r is None or args.v is None or args.gamma is None:
        print("r, v, and gamma are required", file=sys.stderr)
        return 2
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
