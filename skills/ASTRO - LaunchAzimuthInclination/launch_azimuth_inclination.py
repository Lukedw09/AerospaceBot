#!/usr/bin/env python3
"""Launch inclination, azimuth, and Earth-rotation assist.

Eastward relation launch_inclination_cosine from NASA TN D-233, continued
through azimuths whose sine is negative so a westward heading is retrograde.
Rotation assist is launch_rotation_assist. Earth rate and default radius are
WGS 84 (V33).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import webbrowser
from pathlib import Path

G0 = 9.80665
OMEGA_E = 7.292115e-5
R_WGS84 = 6378137.0
CHECK_TOL = 1e-8
PLOT_TITLE = "Launch azimuth and inclination"
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "spherical Earth; launch_inclination_cosine cos i = cos(phi)*sin(az) "
    "with azimuth clockwise from north (NASA TN D-233 eastward relation; "
    "sin(az) < 0 is a westward heading and i > pi/2); "
    "launch_azimuth_sine inverts that for a target inclination; "
    "i_min = abs(latitude); refuse a target i below i_min; "
    "earth_rotation_inertial_speed and launch_rotation_assist; "
    f"default omega_E = {OMEGA_E:.8g} rad/s and R = {R_WGS84:.8g} m (WGS 84); "
    "angles in radians"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def wrap_0_2pi(angle: float) -> float:
    turn = 2.0 * math.pi
    return angle % turn


def inclination_from_azimuth(lat: float, az: float) -> float:
    """launch_inclination_cosine, then arccos."""
    cosine = math.cos(lat) * math.sin(az)
    cosine = max(-1.0, min(1.0, cosine))
    return math.acos(cosine)


def azimuths_from_inclination(lat: float, inc: float) -> tuple[float, float]:
    """Two launch azimuths from launch_azimuth_sine."""
    if abs(lat) >= math.pi / 2.0 - 1e-12:
        raise ValueError("azimuth is undefined at the pole; pass --az")
    sine = math.cos(inc) / math.cos(lat)
    if sine > 1.0 + 1e-12 or sine < -1.0 - 1e-12:
        raise ValueError("inclination is below the site latitude")
    sine = max(-1.0, min(1.0, sine))
    primary = wrap_0_2pi(math.asin(sine))
    alternate = wrap_0_2pi(math.pi - math.asin(sine))
    return primary, alternate


def rotation_speed(omega: float, radius: float, lat: float) -> float:
    """earth_rotation_inertial_speed."""
    return omega * radius * math.cos(lat)


def rotation_assist(omega: float, radius: float, lat: float, az: float) -> float:
    """launch_rotation_assist."""
    return omega * radius * math.cos(lat) * math.sin(az)


def site_vector(lat: float) -> tuple[float, float, float]:
    return (math.cos(lat), 0.0, math.sin(lat))


def heading_vector(lat: float, az: float) -> tuple[float, float, float]:
    north = (-math.sin(lat), 0.0, math.cos(lat))
    east = (0.0, 1.0, 0.0)
    return tuple(north[i] * math.cos(az) + east[i] * math.sin(az) for i in range(3))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(v: tuple[float, float, float]) -> tuple[float, float, float]:
    mag = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    if mag <= 0.0:
        raise ValueError("zero vector")
    return (v[0] / mag, v[1] / mag, v[2] / mag)


def great_circle(normal: tuple[float, float, float], n: int = 181) -> list[list[float]]:
    nvec = norm(normal)
    trial = (1.0, 0.0, 0.0) if abs(nvec[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = norm(cross(nvec, trial))
    w = cross(nvec, u)
    points = []
    for k in range(n):
        ang = 2.0 * math.pi * k / (n - 1)
        points.append(
            [
                u[0] * math.cos(ang) + w[0] * math.sin(ang),
                u[1] * math.cos(ang) + w[1] * math.sin(ang),
                u[2] * math.cos(ang) + w[2] * math.sin(ang),
            ]
        )
    return points


def ray(origin: tuple[float, float, float], direction: tuple[float, float, float], length: float) -> list[list[float]]:
    d = norm(direction)
    return [
        [origin[0], origin[1], origin[2]],
        [origin[0] + length * d[0], origin[1] + length * d[1], origin[2] + length * d[2]],
    ]


def axis_points(length: float = 1.62, n: int = 81) -> list[list[float]]:
    return [[0.0, 0.0, -length + 2.0 * length * k / (n - 1)] for k in range(n)]


def nearest_start(points: list[list[float]], target: tuple[float, float, float]) -> list[list[float]]:
    best = 0
    best_d = float("inf")
    for index, point in enumerate(points):
        dist = (point[0] - target[0]) ** 2 + (point[1] - target[1]) ** 2 + (point[2] - target[2]) ** 2
        if dist < best_d:
            best, best_d = index, dist
    return points[best:] + points[:best]


def rotation_arrows() -> list[list[list[float]]]:
    """Four chevrons on the equator, pointing in the eastward spin direction."""
    arrows = []
    radius = 1.1
    for k in range(4):
        ang = math.pi / 2.0 * k + 0.35
        cosine, sine = math.cos(ang), math.sin(ang)
        tangent = (-sine, cosine, 0.0)
        radial = (cosine, sine, 0.0)
        base = [radius * radial[i] for i in range(3)]
        tip = [base[i] + 0.14 * tangent[i] for i in range(3)]
        tail = [base[i] - 0.07 * tangent[i] for i in range(3)]
        left = [base[i] - 0.01 * tangent[i] + 0.05 * radial[i] for i in range(3)]
        right = [base[i] - 0.01 * tangent[i] - 0.05 * radial[i] for i in range(3)]
        arrows.append([tail, tip])
        arrows.append([left, tip, right])
    return arrows


def scene_payload(lat: float, az: float, inc: float, alt_az: float) -> dict:
    site = site_vector(lat)
    head = heading_vector(lat, az)
    normal = cross(site, head)
    if normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2 < 1e-16:
        normal = (0.0, 0.0, 1.0)
    orbit = great_circle(normal)
    equator = great_circle((0.0, 0.0, 1.0))
    path = nearest_start(orbit, site)
    return {
        "units": "One Earth radius. North is up. The orbit is solid in front of Earth and dotted behind it. Arrows on the equator show the eastward spin. Drag to rotate. Scroll to zoom.",
        "planetRadius": 0.98,
        "arrows": rotation_arrows(),
        "polylines": [
            {"name": "Rotation axis", "color": "#1a365d", "points": axis_points(), "closed": False, "dashBehind": True},
            {"name": "Equator", "color": "#1a5276", "points": equator, "closed": True, "dashBehind": True},
            {"name": "Orbit plane", "color": "#b9770e", "points": orbit, "closed": True, "dashBehind": True},
            {"name": "Launch azimuth", "color": "#c0392b", "points": ray(site, head, 0.55), "closed": False},
            {
                "name": "Alternate azimuth",
                "color": "#1e8449",
                "points": ray(site, heading_vector(lat, alt_az), 0.42),
                "closed": False,
            },
        ],
        "spheres": [
            {"name": "Earth", "center": [0.0, 0.0, 0.0], "radius": 0.98, "color": "#a9cce3", "opacity": 0.55},
            {"name": "North", "center": [0.0, 0.0, 1.08], "radius": 0.04, "color": "#1a365d", "opacity": 1.0},
            {"name": "Launch site", "center": list(site), "radius": 0.045, "color": "#6c3483", "opacity": 1.0},
        ],
        "path": path,
        "markerLabel": "Along the orbit",
        "markerRadius": 0.04,
        "markerColor": "#c0392b",
        "camera": {"position": [2.3, 1.35, 1.7], "target": [0.0, 0.0, 0.0]},
        "inclination_rad": inc,
        "azimuth_rad": az,
    }


def write_viewer(path: Path, payload: dict) -> None:
    viewer = SKILL_DIR / "viewer"
    template = (viewer / "template.html").read_text(encoding="utf-8")
    three = (viewer / "three.min.js").read_text(encoding="utf-8")
    three = three.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":")).replace("<", "\\u003c")
    html = (
        template.replace("__TITLE__", PLOT_TITLE)
        .replace("__THREE_SOURCE__", three)
        .replace("__SCENE_JSON__", encoded)
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def camera_outward(elev_deg: float, azim_deg: float) -> tuple[float, float, float]:
    elev = math.radians(elev_deg)
    azim = math.radians(azim_deg)
    return (math.cos(elev) * math.cos(azim), math.cos(elev) * math.sin(azim), math.sin(elev))


def behind_planet(x: float, y: float, z: float, outward: tuple[float, float, float], radius: float) -> bool:
    depth = x * outward[0] + y * outward[1] + z * outward[2]
    radial = x * x + y * y + z * z
    off_axis = radial - depth * depth
    hide = radius * radius
    if 0.81 < radial < 1.44:
        hide = max(hide, radial * 0.998)
    if off_axis >= hide:
        return False
    return depth < math.sqrt(hide - off_axis)


def split_runs(points: list[list[float]], hidden: list[bool]) -> tuple[list[list[list[float]]], list[list[list[float]]]]:
    near: list[list[list[float]]] = []
    far: list[list[list[float]]] = []
    near_run: list[list[float]] = []
    far_run: list[list[float]] = []

    def flush() -> None:
        nonlocal near_run, far_run
        if len(near_run) > 1:
            near.append(near_run)
        if len(far_run) > 1:
            far.append(far_run)
        near_run, far_run = [], []

    previous = None
    for flag, point in zip(hidden, points):
        if previous is not None and flag != previous:
            if flag:
                near_run.append(point)
            else:
                far_run.append(point)
            flush()
        (far_run if flag else near_run).append(point)
        previous = flag
    flush()
    return near, far


def plot_first_frame(path: Path, payload: dict) -> None:
    import matplotlib

    if "matplotlib.pyplot" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(7.4, 7.4))
    ax = fig.add_subplot(111, projection="3d")
    radius = float(payload.get("planetRadius", 0.98))
    xs, ys, zs = [], [], []
    for i in range(36):
        row_x, row_y, row_z = [], [], []
        u = 2.0 * math.pi * i / 35.0
        for j in range(18):
            v = math.pi * j / 17.0
            row_x.append(radius * math.cos(u) * math.sin(v))
            row_y.append(radius * math.sin(u) * math.sin(v))
            row_z.append(radius * math.cos(v))
        xs.append(row_x)
        ys.append(row_y)
        zs.append(row_z)
    import numpy as np

    ax.plot_surface(np.asarray(xs), np.asarray(ys), np.asarray(zs), color="#a9cce3", alpha=0.55, linewidth=0, shade=False)
    outward = camera_outward(22.0, -58.0)
    labeled: set[str] = set()
    for line in payload["polylines"]:
        pts = line["points"]
        name = line.get("name", "")
        if line.get("dashBehind"):
            hidden = [behind_planet(p[0], p[1], p[2], outward, radius) for p in pts]
            near, far = split_runs(pts, hidden)
            for run in near:
                label = name if name and name not in labeled else None
                if name:
                    labeled.add(name)
                ax.plot([p[0] for p in run], [p[1] for p in run], [p[2] for p in run], color=line["color"], linewidth=1.5, label=label)
            for run in far:
                ax.plot(
                    [p[0] for p in run],
                    [p[1] for p in run],
                    [p[2] for p in run],
                    color=line["color"],
                    linewidth=1.1,
                    linestyle=(0, (1.2, 1.6)),
                )
        else:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts], color=line["color"], linewidth=1.5, label=name)
    arrow_labeled = False
    for arrow in payload.get("arrows", []):
        ax.plot(
            [p[0] for p in arrow],
            [p[1] for p in arrow],
            [p[2] for p in arrow],
            color="#1a365d",
            linewidth=1.4,
            label=None if arrow_labeled else "Earth rotation",
        )
        arrow_labeled = True
    if payload["path"]:
        p0 = payload["path"][0]
        ax.scatter([p0[0]], [p0[1]], [p0[2]], color="#c0392b", s=28, label="Along the orbit")
    ax.legend(loc="upper left", fontsize=8)
    ax.view_init(elev=22, azim=-58)
    ax.set_title(PLOT_TITLE)
    limit = 1.9
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.set_box_aspect((1, 1, 1), zoom=1.15)
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.92)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run(args: argparse.Namespace) -> int:
    require_finite("latitude", args.lat)
    if abs(args.lat) > math.pi / 2.0:
        raise ValueError("latitude must lie in [-pi/2, pi/2]")
    radius = R_WGS84 if args.radius is None else args.radius
    omega = OMEGA_E if args.omega is None else args.omega
    if radius <= 0.0 or omega <= 0.0:
        raise ValueError("radius and omega must be > 0")
    if args.az is None and args.i is None:
        raise ValueError("pass --az or --i")
    if args.az is not None:
        require_finite("azimuth", args.az)
        az = wrap_0_2pi(args.az)
        inc = inclination_from_azimuth(args.lat, az)
        alt = wrap_0_2pi(math.pi - math.asin(max(-1.0, min(1.0, math.sin(az)))))
        source = "azimuth"
    else:
        require_finite("inclination", args.i)
        if args.i < 0.0 or args.i > math.pi:
            raise ValueError("inclination must lie in [0, pi]")
        if args.i + 1e-12 < abs(args.lat):
            raise ValueError("inclination is below the site latitude")
        az, alt = azimuths_from_inclination(args.lat, args.i)
        inc = inclination_from_azimuth(args.lat, az)
        source = "inclination"
    v_east = rotation_speed(omega, radius, args.lat)
    v_assist = rotation_assist(omega, radius, args.lat, az)
    out = Path(args.out) if args.out else SKILL_DIR / "launch_azimuth_inclination.png"
    out = out.resolve()
    html_path = out.with_suffix(".html")
    payload = scene_payload(args.lat, az, inc, alt)
    plot_first_frame(out, payload)
    write_viewer(html_path, payload)
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("lat_rad", args.lat)
    print_kv("az_source", source)
    print_kv("az_rad", az)
    print_kv("az_alt_rad", alt)
    print_kv("i_rad", inc)
    print_kv("i_min_rad", abs(args.lat))
    print_kv("R_m", radius)
    print_kv("omega_rad_s", omega)
    print_kv("v_rot_m_s", v_east)
    print_kv("v_rot_assist_m_s", v_assist)
    print_kv("graph", str(out))
    print_kv("viewer", str(html_path))
    if args.open:
        webbrowser.open(html_path.as_uri())
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    import io
    import tempfile

    lat = 28.5 * math.pi / 180.0
    inc = 51.6 * math.pi / 180.0
    az, alt = azimuths_from_inclination(lat, inc)
    sine = math.cos(inc) / math.cos(lat)
    if near(math.sin(az), sine, "cape sine"):
        return 1
    if near(inclination_from_azimuth(lat, az), math.acos(math.cos(lat) * math.sin(az)), "cape i"):
        return 1
    # Published northeast azimuth is about 44.98 deg.
    if abs(az * 180.0 / math.pi - 44.98) > 0.05:
        return fail(f"cape azimuth deg = {az * 180 / math.pi}")
    if abs(alt * 180.0 / math.pi - (180.0 - 44.98)) > 0.05:
        return fail("cape alternate azimuth")
    pole_i = inclination_from_azimuth(math.pi / 2.0, 0.3)
    if near(pole_i, math.pi / 2.0, "pole inclination"):
        return 1
    if near(rotation_assist(OMEGA_E, R_WGS84, math.pi / 2.0, math.pi / 2.0), 0.0, "pole assist"):
        return 1
    east = rotation_speed(OMEGA_E, R_WGS84, 0.0)
    if near(rotation_assist(OMEGA_E, R_WGS84, 0.0, math.pi / 2.0), east, "equator due east"):
        return 1
    if near(east, OMEGA_E * R_WGS84, "equator speed"):
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        png = str(Path(tmp) / "out.png")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(["--lat", str(lat), "--i", str(inc), "--out", png])
        finally:
            sys.stdout = old
        if code != 0:
            return fail("cli failed")
        text = buf.getvalue()
        if "graph:" not in text or "viewer:" not in text:
            return fail("missing graph or viewer")
        if not Path(png).is_file() or not Path(png).with_suffix(".html").is_file():
            return fail("png or html missing")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch azimuth, inclination, and rotation assist.")
    parser.add_argument("--lat", type=float, help="Geocentric latitude, rad")
    parser.add_argument("--az", type=float, default=None, help="Launch azimuth clockwise from north, rad")
    parser.add_argument("--i", type=float, default=None, dest="i", help="Target inclination, rad")
    parser.add_argument("--radius", type=float, default=None, help="Earth radius, m")
    parser.add_argument("--omega", type=float, default=None, help="Earth rotation rate, rad/s")
    parser.add_argument("--out", default=None, help="PNG path")
    parser.add_argument("--open", action="store_true", help="Open the HTML viewer")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.lat is None:
        print("latitude is required", file=sys.stderr)
        return 2
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
