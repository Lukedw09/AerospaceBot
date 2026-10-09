#!/usr/bin/env python3
"""Planar gravity-assist patch.

hyperbolic_eccentricity_from_periapsis is 1 + rp*vinf**2/mu.
hyperbola_turning_angle is 2*asin(1/e).
planar_rotate_x and planar_rotate_y turn the inbound excess velocity.
vector_difference_speed is the heliocentric delta-v.
flyby_kinetic_change is the specific-energy change at fixed radius.
mu = g0*R0**2 with g0 = 9.80665 m/s^2 when --R0 is used.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

G0 = 9.80665
R0_EARTH = 6.3742e6
CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Gravity-assist flyby"
AXIS_UNIT_CAPTION = "X, Y, Z (km)"
ELEV_DEG = 20.0
AZIM_DEG = 35.0
HYPER_COLOR = "#c0392b"
ASYMPTOTE_COLOR = "#85929e"
COAST_WALL_S = 14.0
_OP = None

ASSUMPTIONS = (
    "planar patched conic; |v_inf| unchanged; "
    "hyperbolic_eccentricity_from_periapsis; "
    "hyperbola_turning_angle delta = 2*asin(1/e); "
    "left turn is +delta (counterclockwise); "
    "v_helio = v_planet + v_inf; "
    "vector_difference_speed; flyby_kinetic_change = 0.5*(vout**2 - vin**2); "
    "mu = g0*R0**2 with g0 = 9.80665 when --R0 is passed; "
    "B-plane targeting and propellant burns are omitted"
)


def op_mod():
    global _OP
    if _OP is None:
        folder = str(SKILL_DIR.parent / "ASTRO - OrbitalParameters")
        if folder not in sys.path:
            sys.path.insert(0, folder)
        import orbital_parameters as imported

        _OP = imported
    return _OP


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


def eccentricity(rp: float, vinf: float, mu: float) -> float:
    return 1.0 + rp * vinf * vinf / mu


def turning_angle(ecc: float) -> float:
    if ecc <= 1.0:
        raise ValueError("hyperbola eccentricity must be > 1")
    return 2.0 * math.asin(1.0 / ecc)


def rotate(vx: float, vy: float, ang: float) -> tuple[float, float]:
    return (
        vx * math.cos(ang) - vy * math.sin(ang),
        vx * math.sin(ang) + vy * math.cos(ang),
    )


def speed(vx: float, vy: float) -> float:
    return math.hypot(vx, vy)


def solve(
    mu: float,
    rp: float,
    vinf: float,
    ux: float,
    uy: float,
    vp_x: float,
    vp_y: float,
    turn: str,
) -> dict[str, object]:
    require_positive("mu", mu)
    require_positive("rp", rp)
    require_positive("vinf", vinf)
    ecc = eccentricity(rp, vinf, mu)
    delta = turning_angle(ecc)
    ang = delta if turn == "left" else -delta
    vin_x = vinf * ux
    vin_y = vinf * uy
    vout_x, vout_y = rotate(vin_x, vin_y, ang)
    helio_in = (vp_x + vin_x, vp_y + vin_y)
    helio_out = (vp_x + vout_x, vp_y + vout_y)
    vin = speed(*helio_in)
    vout = speed(*helio_out)
    return {
        "mu_m3_s2": mu,
        "rp_m": rp,
        "vinf_m_s": vinf,
        "eccentricity": ecc,
        "delta_rad": delta,
        "turn": turn,
        "vinf_in_x_m_s": vin_x,
        "vinf_in_y_m_s": vin_y,
        "vinf_out_x_m_s": vout_x,
        "vinf_out_y_m_s": vout_y,
        "v_in_x_m_s": helio_in[0],
        "v_in_y_m_s": helio_in[1],
        "v_out_x_m_s": helio_out[0],
        "v_out_y_m_s": helio_out[1],
        "dv_helio_m_s": speed(helio_out[0] - helio_in[0], helio_out[1] - helio_in[1]),
        "ke_change_J_kg": 0.5 * (vout * vout - vin * vin),
    }


def km(meters: float) -> float:
    return meters / 1000.0


def linspace(lo: float, hi: float, count: int) -> list[float]:
    step = (hi - lo) / (count - 1)
    values = [lo + step * i for i in range(count)]
    values[-1] = hi
    return values


def hyperbola_points(
    rp: float, ecc: float, turn: str, body_radius: float | None = None
) -> list[tuple[float, float]]:
    nu_inf = math.acos(-1.0 / ecc)
    parameter = rp * (1.0 + ecc)
    if body_radius is not None and body_radius > 0.0:
        limit = nu_draw(rp, ecc, body_radius)
        start = -limit
        stop = limit
    else:
        start = -nu_inf + 0.02
        stop = nu_inf - 0.02
    sign = -1.0 if turn == "right" else 1.0
    points: list[tuple[float, float]] = []
    for nu in linspace(start, stop, 181):
        radius = parameter / (1.0 + ecc * math.cos(nu))
        points.append((radius * math.cos(nu), sign * radius * math.sin(nu)))
    return points


def emit(result: dict[str, object], graph: Path, html: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "mu_m3_s2",
        "rp_m",
        "vinf_m_s",
        "eccentricity",
        "delta_rad",
        "turn",
        "vinf_in_x_m_s",
        "vinf_in_y_m_s",
        "vinf_out_x_m_s",
        "vinf_out_y_m_s",
        "v_in_x_m_s",
        "v_in_y_m_s",
        "v_out_x_m_s",
        "v_out_y_m_s",
        "dv_helio_m_s",
        "ke_change_J_kg",
    ):
        print_kv(key, result[key])
    if "body_radius_m" in result and result["body_radius_m"] is not None:
        print_kv("body_radius_m", result["body_radius_m"])
    print_kv("graph", str(graph))
    if html is not None:
        print_kv("viewer", str(html))
        print_kv("html", str(html))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    radius = result.get("body_radius_m")
    body = float(radius) if isinstance(radius, (int, float)) and radius > 0.0 else None
    points = hyperbola_points(
        float(result["rp_m"]), float(result["eccentricity"]), str(result["turn"]), body
    )
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    radius = result.get("body_radius_m")
    if isinstance(radius, (int, float)) and radius > 0.0:
        angles = linspace(0.0, 2.0 * math.pi, 181)
        earth_x = [radius * math.cos(angle) for angle in angles]
        earth_y = [radius * math.sin(angle) for angle in angles]
        ax.fill(earth_x, earth_y, color="#d4e6f1", zorder=1)
        ax.plot(earth_x, earth_y, color="#1a5276", linewidth=1.0, zorder=2)
    ax.plot([p[0] for p in points], [p[1] for p in points], color="C0")
    ax.plot(0.0, 0.0, "o", color="C3")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_title("Planet-centered flyby")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def nu_draw(rp: float, ecc: float, body_radius: float) -> float:
    """True-anomaly limit that keeps the planet large in the view."""
    nu_inf = math.acos(-1.0 / ecc)
    parameter = rp * (1.0 + ecc)
    target = 6.0 * max(rp, body_radius)
    cosine = (parameter / target - 1.0) / ecc
    cosine = min(1.0, max(cosine, -1.0 / ecc + 0.05))
    return min(0.92 * nu_inf, math.acos(cosine))


def arc_km(rp: float, ecc: float, turn: str, body_radius: float, count: int = 241) -> list[list[float]]:
    sign = -1.0 if turn == "right" else 1.0
    limit = nu_draw(rp, ecc, body_radius)
    parameter = rp * (1.0 + ecc)
    points: list[list[float]] = []
    for nu in linspace(-limit, limit, count):
        radius = parameter / (1.0 + ecc * math.cos(nu))
        points.append([km(radius * math.cos(nu)), km(sign * radius * math.sin(nu)), 0.0])
    return points


def asymptote_km(rp: float, ecc: float, turn: str, span_m: float) -> list[list[list[float]]]:
    sign = -1.0 if turn == "right" else 1.0
    semi = rp * (1.0 + ecc) / (1.0 - ecc * ecc)
    center = semi * ecc
    slope = math.sqrt(ecc * ecc - 1.0)
    lines: list[list[list[float]]] = []
    for branch in (1.0, -1.0):
        y_slope = sign * branch * slope
        x0 = center - span_m
        x1 = center + span_m
        lines.append(
            [
                [km(x0), km(y_slope * (x0 - center)), 0.0],
                [km(x1), km(y_slope * (x1 - center)), 0.0],
            ]
        )
    return lines


def planet_backdrop(body_radius: float, outer_m: float) -> dict[str, object]:
    op = op_mod()
    span = max(body_radius, outer_m)
    limit_m = op.LIMIT_SPAN_FRAC * span
    axis_len = min(max(1.35 * body_radius, 0.42 * span), 0.72 * span)
    ring_r = min(1.22 * body_radius, 0.98 * span)
    same_earth = math.isclose(body_radius, R0_EARTH, rel_tol=1e-9, abs_tol=0.0)
    flattening = op.F_EARTH if same_earth else 0.0
    polar_m = body_radius * (1.0 - flattening)
    ring_angles = linspace(0.0, 2.0 * math.pi, 181)
    ring = [[km(ring_r * math.cos(angle)), km(ring_r * math.sin(angle)), 0.0] for angle in ring_angles]
    equator = [
        [km(body_radius * math.cos(angle)), km(body_radius * math.sin(angle)), 0.0] for angle in ring_angles
    ]
    spokes: list[list[list[float]]] = []
    inner = min(body_radius, ring_r)
    if ring_r > inner * (1.0 + 1e-6):
        for spoke in range(8):
            angle = spoke * math.pi / 8.0
            spokes.append(
                [
                    [km(inner * math.cos(angle)), km(inner * math.sin(angle)), 0.0],
                    [km(ring_r * math.cos(angle)), km(ring_r * math.sin(angle)), 0.0],
                ]
            )
    axes = [
        {"label": "X", "tip_km": [km(axis_len), 0.0, 0.0], "label_km": [km(axis_len * 1.08), 0.0, 0.0]},
        {"label": "Y", "tip_km": [0.0, km(axis_len), 0.0], "label_km": [0.0, km(axis_len * 1.08), 0.0]},
        {"label": "Z", "tip_km": [0.0, 0.0, km(axis_len)], "label_km": [0.0, 0.0, km(axis_len * 1.08)]},
    ]
    return {
        "limit_km": km(limit_m),
        "axis_length_km": km(axis_len),
        "equatorial_radius_km": km(body_radius),
        "polar_radius_km": km(polar_m),
        "flattening": flattening,
        "planet_segments_u": op.PLANET_SEGMENTS_U,
        "planet_segments_v": op.PLANET_SEGMENTS_V,
        "planet_opacity": 0.92,
        "ring_km": ring,
        "spokes_km": spokes,
        "equator_km": equator,
        "axes": axes,
        "velocity_length_km": km(op.ARROW_SPAN_FRAC * span),
    }


def build_payload(result: dict[str, object]) -> dict[str, object]:
    op = op_mod()
    radius = result.get("body_radius_m")
    if not isinstance(radius, (int, float)) or radius <= 0.0:
        raise ValueError("--html needs --radius or --R0 so the planet can be drawn")
    rp = float(result["rp_m"])
    ecc = float(result["eccentricity"])
    mu = float(result["mu_m3_s2"])
    turn = str(result["turn"])
    if radius > rp and not math.isclose(radius, rp, rel_tol=1e-12, abs_tol=0.0):
        raise ValueError("periapsis is inside the planetary radius")
    arc = arc_km(rp, ecc, turn, float(radius))
    outer = max(radius, rp, max(math.hypot(point[0], point[1]) for point in arc) * 1000.0)
    scene = planet_backdrop(float(radius), outer)
    palette = dict(op.PALETTE)
    palette["hyperbola"] = HYPER_COLOR
    peri_km = [km(rp), 0.0, 0.0]
    drawn = nu_draw(rp, ecc, float(radius))
    parameter = rp * (1.0 + ecc)
    layers = [
        {"id": "hyperbola", "color": HYPER_COLOR, "faded": False, "polylines": [arc]},
        {
            "id": "asymptotes",
            "color": ASYMPTOTE_COLOR,
            "faded": True,
            "polylines": asymptote_km(rp, ecc, turn, outer * 0.35),
        },
    ]
    legend = [
        {"label": "planet", "swatch": "planet", "color": palette["planet"], "edge": palette["planet_edge"]},
        {"label": "hyperbola", "swatch": "line", "color": HYPER_COLOR, "edge": None},
        {"label": "asymptotes", "swatch": "line", "color": ASYMPTOTE_COLOR, "edge": None},
        {"label": "periapsis", "swatch": "square", "color": "#27ae60", "edge": None},
        {"label": "spacecraft", "swatch": "circle", "color": palette["craft"], "edge": None},
    ]
    sequence = [
        {
            "kind": "coast",
            "label": "flyby",
            "layer": "hyperbola",
            "wall_s": COAST_WALL_S,
            "a": parameter / (1.0 - ecc * ecc),
            "e": ecc,
            "i": math.pi if turn == "right" else 0.0,
            "Omega": 0.0,
            "omega": 0.0,
            "p": parameter,
            "h": math.sqrt(mu * parameter),
            "mu": mu,
            "nu0": -drawn,
            "nu1": drawn,
            "rp": rp,
        }
    ]
    return {
        "title": PLOT_TITLE,
        "elev_deg": ELEV_DEG,
        "azim_deg": AZIM_DEG,
        "roll_deg": op.CAMERA_ROLL_DEG,
        **scene,
        "layers": layers,
        "markers": [
            {"id": "periapsis", "label": "periapsis", "shape": "square", "color": "#27ae60", "km": peri_km},
            {"id": "spacecraft", "label": "spacecraft", "shape": "circle", "color": palette["craft"], "km": arc[0]},
        ],
        "craft_km": arc[0],
        "burns": [],
        "legend": legend,
        "palette": palette,
        "sequence": sequence,
    }


def scene_from_html(html: str) -> dict[str, object]:
    token = '<script type="application/json" id="orbital-scene">'
    start = html.find(token)
    if start < 0:
        raise ValueError("viewer is missing the scene payload")
    start += len(token)
    end = html.find("</script>", start)
    if end < 0:
        raise ValueError("viewer scene payload is not closed")
    return json.loads(html[start:end])


def write_html(result: dict[str, object], out_path: Path) -> None:
    viewer_dir = SKILL_DIR / "viewer"
    try:
        template = (viewer_dir / "template.html").read_text(encoding="utf-8")
        three_source = (viewer_dir / "three.min.js").read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"could not read the viewer template: {exc}") from exc
    if "</script>" in three_source.lower():
        three_source = three_source.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    encoded = json.dumps(build_payload(result), allow_nan=False, separators=(",", ":"))
    encoded = encoded.replace("<", "\\u003c")
    before, placeholder, after = template.partition("__THREE_SOURCE__")
    if not placeholder:
        raise ValueError("viewer template is missing the Three.js placeholder")
    before = before.replace("__TITLE__", PLOT_TITLE).replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
    after = (
        after.replace("__TITLE__", PLOT_TITLE)
        .replace("__AXIS_CAPTION__", AXIS_UNIT_CAPTION)
        .replace("__SCENE_JSON__", encoded)
    )
    html = before + three_source + after
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")


def direction(args: argparse.Namespace) -> tuple[float, float]:
    has_unit = args.ux is not None or args.uy is not None
    if has_unit and args.psi is not None:
        raise ValueError("pass --ux and --uy, or --psi, not both")
    if args.psi is not None:
        heading = math.atan2(args.vp_y, args.vp_x) + args.psi
        return math.cos(heading), math.sin(heading)
    if args.ux is None or args.uy is None:
        raise ValueError("pass --ux and --uy, or --psi")
    mag = math.hypot(args.ux, args.uy)
    if mag == 0.0 or not math.isfinite(mag):
        raise ValueError("--ux and --uy must be a finite nonzero direction")
    return args.ux / mag, args.uy / mag


def from_args(args: argparse.Namespace) -> dict[str, object]:
    if args.rp is None or args.turn is None:
        raise ValueError("requires --rp and --turn")
    if args.vp_x is None or args.vp_y is None:
        raise ValueError("requires --vp-x and --vp-y")
    if (args.mu is None) == (args.R0 is None):
        raise ValueError("pass --mu or --R0, not both and not neither")
    if (args.vinf is None) == (args.C3 is None):
        raise ValueError("pass --vinf or --C3, not both and not neither")
    mu = args.mu if args.mu is not None else G0 * args.R0 * args.R0
    if args.vinf is not None:
        vinf = args.vinf
    else:
        require_positive("C3", args.C3)
        vinf = math.sqrt(args.C3)
    ux, uy = direction(args)
    result = solve(mu, args.rp, vinf, ux, uy, args.vp_x, args.vp_y, args.turn)
    if args.radius is not None:
        require_positive("radius", args.radius)
        body_radius = args.radius
    elif args.R0 is not None:
        body_radius = args.R0
    else:
        body_radius = None
    if body_radius is not None and body_radius > args.rp and not math.isclose(body_radius, args.rp, rel_tol=1e-9, abs_tol=0.0):
        raise ValueError("periapsis is inside the planetary radius")
    if body_radius is not None:
        result["body_radius_m"] = body_radius
    return result


def hyperbolic_anomaly_from_true(nu: float, ecc: float) -> float:
    cosh_f = (ecc + math.cos(nu)) / (1.0 + ecc * math.cos(nu))
    anomaly = math.acosh(max(1.0, cosh_f))
    return -anomaly if math.sin(nu) < 0.0 else anomaly


def true_from_hyperbolic(anomaly: float, ecc: float) -> float:
    cosh_f = math.cosh(anomaly)
    sinh_f = math.sinh(anomaly)
    denominator = 1.0 - ecc * cosh_f
    cosine = (cosh_f - ecc) / denominator
    sine = -math.sqrt(ecc * ecc - 1.0) * sinh_f / denominator
    return math.atan2(sine, cosine)


def mean_from_hyperbolic(anomaly: float, ecc: float) -> float:
    return ecc * math.sinh(anomaly) - anomaly


def solve_hyperbolic_kepler(mean: float, ecc: float) -> float:
    anomaly = math.asinh(mean / ecc)
    for _ in range(40):
        residual = ecc * math.sinh(anomaly) - anomaly - mean
        slope = ecc * math.cosh(anomaly) - 1.0
        delta = residual / slope
        anomaly -= delta
        if abs(delta) <= 1e-14:
            break
    return anomaly


def nu_at_time_fraction(nu0: float, nu1: float, ecc: float, fraction: float) -> float:
    start = hyperbolic_anomaly_from_true(nu0, ecc)
    end = hyperbolic_anomaly_from_true(nu1, ecc)
    mean0 = mean_from_hyperbolic(start, ecc)
    mean1 = mean_from_hyperbolic(end, ecc)
    mean = mean0 + (mean1 - mean0) * fraction
    return true_from_hyperbolic(solve_hyperbolic_kepler(mean, ecc), ecc)


def run_check() -> int:
    if not close(true_from_hyperbolic(hyperbolic_anomaly_from_true(0.4, 2.0), 2.0), 0.4):
        return fail("hyperbolic anomaly round trip")
    if not close(nu_at_time_fraction(-1.0, 1.0, 2.0, 0.5), 0.0):
        return fail("periapsis is not the midpoint in time")
    near = nu_at_time_fraction(-1.0, 1.0, 2.0, 0.52) - nu_at_time_fraction(-1.0, 1.0, 2.0, 0.48)
    far = nu_at_time_fraction(-1.0, 1.0, 2.0, 0.04) - nu_at_time_fraction(-1.0, 1.0, 2.0, 0.0)
    if not (near > far):
        return fail("closest approach is not the fastest part of the coast")
    state = solve(1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, "left")
    if not close(float(state["eccentricity"]), 2.0):
        return fail("eccentricity")
    if not close(float(state["delta_rad"]), math.pi / 3.0):
        return fail("turning angle")
    if not close(float(state["vinf_out_x_m_s"]), 0.5):
        return fail("rotated x")
    if not close(float(state["vinf_out_y_m_s"]), math.sin(math.pi / 3.0)):
        return fail("rotated y")
    if not close(float(state["dv_helio_m_s"]), 1.0):
        return fail("delta-v")
    if not close(float(state["ke_change_J_kg"]), 0.0):
        return fail("energy")
    parked = solve(1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0, "left")
    if not close(float(parked["ke_change_J_kg"]), 0.5 * (speed(1.5, math.sin(math.pi / 3.0)) ** 2 - 4.0)):
        return fail("energy with planet velocity")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        html_path = Path(folder) / "check.html"
        state["body_radius_m"] = 0.4
        write_plot(state, path)
        write_html(state, html_path)
        html = html_path.read_text(encoding="utf-8")
        if path.stat().st_size < 1000 or len(html) < 100000:
            return fail("check figure was not written")
        if "__THREE_SOURCE__" in html or "__SCENE_JSON__" in html:
            return fail("viewer placeholders were not filled")
        if "solveHyperbolicKepler" not in html or "new THREE.OrthographicCamera" not in html or "let playing = true" not in html:
            return fail("viewer is not the animated orthographic page")
        if "SphereGeometry" not in html or "AmbientLight" not in html:
            return fail("viewer planet is missing")
        scene = scene_from_html(html)
        if not close(float(scene["equatorial_radius_km"]), 0.0004):
            return fail("viewer planet radius")
        if scene.get("sequence") is None or len(scene["sequence"]) != 1:
            return fail("viewer coast is missing")
        if abs(float(scene["elev_deg"]) - ELEV_DEG) > 1e-9:
            return fail("viewer camera")
    print("check: pass")
    print_kv("delta_rad", float(state["delta_rad"]))
    print_kv("dv_helio_m_s", float(state["dv_helio_m_s"]))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Planar gravity-assist velocity patch.")
    parser.add_argument("--mu", type=float, default=None, help="planet gravitational parameter [m^3/s^2]")
    parser.add_argument("--R0", type=float, default=None, help="reference radius for mu = g0*R0^2 [m]")
    parser.add_argument("--radius", type=float, default=None, help="planetary surface radius drawn in the viewer [m]")
    parser.add_argument("--rp", type=float, default=None, help="periapsis radius [m]")
    parser.add_argument("--vinf", type=float, default=None, help="hyperbolic excess speed [m/s]")
    parser.add_argument("--C3", type=float, default=None, help="characteristic energy [m^2/s^2]")
    parser.add_argument("--ux", type=float, default=None, help="inbound excess x component")
    parser.add_argument("--uy", type=float, default=None, help="inbound excess y component")
    parser.add_argument("--psi", type=float, default=None, help="inbound excess angle from planet velocity [rad]")
    parser.add_argument("--vp-x", type=float, default=None, help="planet heliocentric velocity x [m/s]")
    parser.add_argument("--vp-y", type=float, default=None, help="planet heliocentric velocity y [m/s]")
    parser.add_argument("--turn", choices=("left", "right"), default=None, help="left or right")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--html", action="store_true", help="write the OrbitalParameters-style HTML viewer")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        result = from_args(args)
        if args.html and result.get("body_radius_m") is None:
            raise ValueError("--html needs --radius or --R0 so the planet can be drawn")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "gravity_assist_flyby.png"
    html_path = out_path.with_suffix(".html") if args.html else None
    try:
        write_plot(result, out_path)
        if html_path is not None:
            write_html(result, html_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path, html_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
