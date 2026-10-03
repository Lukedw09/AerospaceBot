#!/usr/bin/env python3
"""Trapezoidal wing planform and a plan-view sketch.

Area is trapezoidal_wing_area. Aspect ratio is aspect_ratio. Taper is
taper_ratio. The mean aerodynamic chord and its station are
mean_aerodynamic_chord and mac_spanwise_station. A sweep given on a chord
fraction is moved to the leading edge with leading_edge_from_chord_sweep,
and the quarter-chord and trailing-edge sweeps come back through
chord_fraction_sweep. The leading edge at the mean chord is
mac_leading_edge_x.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Wing geometry"
SWEEP_LIMIT = math.pi / 2.0
# An omitted chord station is the quarter chord, the usual sweep reference.
DEFAULT_SWEEP_AT = 0.25
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "straight-tapered planform with streamwise chords; "
    "S = b*(cr+ct)/2 from trapezoidal_wing_area; "
    "AR = b**2/S from aspect_ratio; "
    "lambda = ct/cr from taper_ratio; "
    "MAC from mean_aerodynamic_chord; "
    "y_MAC from mac_spanwise_station, measured from the centerline; "
    "sweep is from the spanwise axis toward the rear; "
    "an omitted sweep draws an unswept leading edge; "
    "an omitted sweep station is the quarter chord; "
    "chord-fraction sweep uses chord_fraction_sweep and "
    "leading_edge_from_chord_sweep; "
    "x_LE at the MAC is mac_leading_edge_x; "
    "x is positive aft of the root leading edge and y is positive starboard; "
    "the port side is the mirror image"
)


@dataclass(frozen=True)
class Planform:
    span: float
    root: float
    tip: float
    sweep_input: float | None
    sweep_at: float | None
    sweep_at_source: str
    sweep_le: float
    area: float
    aspect_ratio: float
    taper: float
    mac: float
    y_mac: float
    sweep_c4: float
    sweep_te: float
    x_le_mac: float


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def wing_area(span: float, root: float, tip: float) -> float:
    """S = b*(cr + ct)/2."""
    return span * (root + tip) / 2.0


def taper_ratio(tip: float, root: float) -> float:
    """lambda = ct/cr."""
    return tip / root


def aspect_ratio(span: float, area: float) -> float:
    """AR = b**2/S."""
    return span**2 / area


def mean_aerodynamic_chord(root: float, taper: float) -> float:
    """MAC = (2/3)*cr*(1 + lambda + lambda**2)/(1 + lambda)."""
    return (2.0 / 3.0) * root * (1.0 + taper + taper**2) / (1.0 + taper)


def mac_spanwise_station(span: float, taper: float) -> float:
    """y_MAC = (b/6)*(1 + 2*lambda)/(1 + lambda)."""
    return (span / 6.0) * (1.0 + 2.0 * taper) / (1.0 + taper)


def chord_fraction_sweep(sweep_le: float, fraction: float, taper: float, ar: float) -> float:
    """Sweep of the line at fraction n of the local streamwise chord."""
    shift = 4.0 * fraction * (1.0 - taper) / (ar * (1.0 + taper))
    return math.atan(math.tan(sweep_le) - shift)


def leading_edge_sweep(sweep_n: float, fraction: float, taper: float, ar: float) -> float:
    """Leading-edge sweep that puts sweep_n on chord fraction n."""
    shift = 4.0 * fraction * (1.0 - taper) / (ar * (1.0 + taper))
    return math.atan(math.tan(sweep_n) + shift)


def mac_leading_edge_x(y_mac: float, sweep_le: float) -> float:
    """Streamwise station of the starboard MAC leading edge. Positive is aft."""
    return y_mac * math.tan(sweep_le)


def streamwise_chord(y: float, span: float, root: float, tip: float) -> float:
    """Linear taper. y is measured from the centerline."""
    return root + (tip - root) * (2.0 * abs(y) / span)


def planform_from(
    span: float,
    root: float,
    tip: float,
    sweep: float | None,
    sweep_at: float | None,
    sweep_at_given: bool,
) -> Planform:
    area = wing_area(span, root, tip)
    taper = taper_ratio(tip, root)
    ar = aspect_ratio(span, area)
    if sweep is None:
        sweep_le = 0.0
        station = None
        station_source = "omitted"
    else:
        if sweep_at_given:
            if sweep_at is None:
                raise ValueError("sweep station is missing")
            station = sweep_at
            station_source = "given"
        else:
            station = DEFAULT_SWEEP_AT
            station_source = "default-quarter-chord"
        sweep_le = leading_edge_sweep(sweep, station, taper, ar)
    if not -SWEEP_LIMIT < sweep_le < SWEEP_LIMIT:
        raise ValueError("leading-edge sweep must lie strictly between -pi/2 and pi/2")
    y_mac = mac_spanwise_station(span, taper)
    return Planform(
        span=span,
        root=root,
        tip=tip,
        sweep_input=sweep,
        sweep_at=station,
        sweep_at_source=station_source,
        sweep_le=sweep_le,
        area=area,
        aspect_ratio=ar,
        taper=taper,
        mac=mean_aerodynamic_chord(root, taper),
        y_mac=y_mac,
        sweep_c4=chord_fraction_sweep(sweep_le, 0.25, taper, ar),
        sweep_te=chord_fraction_sweep(sweep_le, 1.0, taper, ar),
        x_le_mac=mac_leading_edge_x(y_mac, sweep_le),
    )


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to sketch the wing") from exc
    return plt


def _edge_x(y: float, sweep_le: float, chord: float) -> tuple[float, float]:
    """Leading-edge and trailing-edge streamwise stations at spanwise y."""
    leading = abs(y) * math.tan(sweep_le)
    return leading, leading + chord


def plot_wing(path: Path, wing: Planform) -> None:
    """Plan view. x is aft, y is starboard, and the leading edge is toward the top."""
    plt = ensure_matplotlib()
    span = wing.span
    half = span / 2.0
    tip_le, tip_te = _edge_x(half, wing.sweep_le, wing.tip)
    # y, then x. The trailing edge closes the trapezoid.
    outline_y = [0.0, half, half, 0.0, -half, -half, 0.0]
    outline_x = [0.0, tip_le, tip_te, wing.root, tip_te, tip_le, 0.0]
    x_min = min(outline_x)
    x_max = max(outline_x)
    gap = 0.10 * span
    chord_scale = max(wing.root, gap)
    forward = x_min - 0.22 * chord_scale
    aft = x_max + 0.72 * chord_scale
    side = half + 0.34 * span
    # Room above the span arrow so its label stays off the title.
    top = forward - 0.20 * chord_scale

    fig_w = 9.2
    data_w = 2.0 * side
    data_h = max((aft + 0.28 * chord_scale) - top, 0.35 * span)
    fig_h = min(8.0, max(4.6, fig_w * data_h / data_w))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.fill(outline_y, outline_x, color="#d6eaf8", zorder=1)
    ax.plot(outline_y, outline_x, color="#1a5276", linewidth=1.6, zorder=2)

    # Quarter-chord line, root to both tips.
    root_c4 = 0.25 * wing.root
    tip_c4 = tip_le + 0.25 * wing.tip
    ax.plot(
        [-half, 0.0, half],
        [tip_c4, root_c4, tip_c4],
        color="#1a5276",
        linestyle=":",
        linewidth=1.0,
        zorder=3,
    )
    ax.plot([0.0, 0.0], [0.0, wing.root], color="#1a5276", linestyle="--", linewidth=0.9, zorder=3)

    for sign in (1.0, -1.0):
        y_mac = sign * wing.y_mac
        chord = streamwise_chord(y_mac, span, wing.root, wing.tip)
        le, te = _edge_x(y_mac, wing.sweep_le, chord)
        ax.plot([y_mac, y_mac], [le, te], color="#c0392b", linewidth=2.2, zorder=4)
    le_mac, te_mac = _edge_x(wing.y_mac, wing.sweep_le, wing.mac)
    ax.plot(wing.y_mac, 0.5 * (le_mac + te_mac), "o", color="#c0392b", markersize=4, zorder=5)
    ax.annotate(
        "MAC",
        xy=(wing.y_mac, 0.5 * (le_mac + te_mac)),
        xytext=(-10, 0),
        textcoords="offset points",
        color="#c0392b",
        fontsize=8,
        ha="right",
        va="center",
        zorder=6,
    )

    _dimension(ax, -half, forward, half, forward)
    ax.annotate(
        f"b = {span:.4g} m",
        xy=(0.0, forward),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#1c2833",
        zorder=6,
        bbox=_label_bbox(),
    )
    ax.plot([-half, -half], [tip_le, forward], color="#7f8c8d", linewidth=0.6, zorder=3)
    ax.plot([half, half], [tip_le, forward], color="#7f8c8d", linewidth=0.6, zorder=3)

    _dimension(ax, 0.0, aft, wing.y_mac, aft)
    ax.annotate(
        f"y = {wing.y_mac:.4g} m",
        xy=(wing.y_mac, aft),
        xytext=(6, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=8,
        color="#1c2833",
        clip_on=False,
        zorder=6,
        bbox=_label_bbox(),
    )
    _extension_aft(ax, 0.0, wing.root, aft)
    mac_te = le_mac + wing.mac
    _extension_aft(ax, wing.y_mac, mac_te, aft)

    ax.annotate(
        f"c_r = {wing.root:.4g} m",
        xy=(0.0, wing.root),
        xytext=(0, -6),
        textcoords="offset points",
        ha="center",
        va="top",
        fontsize=8,
        color="#1c2833",
        zorder=6,
        bbox=_label_bbox(),
    )
    ax.annotate(
        f"c_t = {wing.tip:.4g} m",
        xy=(half, 0.5 * (tip_le + tip_te)),
        xytext=(8, 0),
        textcoords="offset points",
        ha="left",
        va="center",
        fontsize=8,
        color="#1c2833",
        clip_on=False,
        zorder=6,
        bbox=_label_bbox(),
    )

    if abs(wing.sweep_le) > math.radians(0.5):
        _sweep_arc(ax, half, wing.sweep_le)

    ax.text(
        1.02,
        0.98,
        "\n".join(
            (
                f"S = {wing.area:.4g} m²",
                f"AR = {wing.aspect_ratio:.4g}",
                f"λ = {wing.taper:.4g}",
                f"MAC = {wing.mac:.4g} m",
                f"y_MAC = {wing.y_mac:.4g} m",
                f"Λ_LE = {math.degrees(wing.sweep_le):.4g}°",
            )
        ),
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color="#1c2833",
        clip_on=False,
        bbox={
            "boxstyle": "round",
            "facecolor": "white",
            "alpha": 0.92,
            "edgecolor": "#d5d8dc",
        },
        zorder=7,
    )

    ax.set_xlim(-side, side)
    ax.set_ylim(aft + 0.28 * chord_scale, top)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("y, starboard (m)")
    ax.set_ylabel("x, aft (m)")
    ax.set_title(PLOT_TITLE, pad=10)
    ax.grid(True, alpha=0.25)
    fig.tight_layout(rect=(0.0, 0.0, 0.78, 1.0))
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def _label_bbox() -> dict[str, object]:
    return {
        "boxstyle": "round,pad=0.15",
        "facecolor": "white",
        "edgecolor": "none",
        "alpha": 0.92,
    }


def _extension_aft(ax, y: float, x_from: float, x_to: float) -> None:
    ax.plot([y, y], [x_from, x_to], color="#7f8c8d", linewidth=0.6, zorder=3)


def _dimension(ax, y0: float, x0: float, y1: float, x1: float) -> None:
    ax.annotate(
        "",
        xy=(y1, x1),
        xytext=(y0, x0),
        arrowprops={
            "arrowstyle": "<->",
            "color": "#34495e",
            "lw": 0.9,
            "shrinkA": 0,
            "shrinkB": 0,
        },
        zorder=5,
    )


def _sweep_arc(ax, half: float, sweep_le: float) -> None:
    radius = 0.16 * half
    steps = 32
    ys: list[float] = []
    xs: list[float] = []
    count = steps + 1
    for index in range(count):
        angle = sweep_le * index / steps
        ys.append(radius * math.cos(angle))
        xs.append(radius * math.sin(angle))
    ax.plot(ys, xs, color="#1a5276", linewidth=1.0, zorder=5)
    mid = sweep_le / 2.0
    label_r = radius * 1.35
    ax.text(
        label_r * math.cos(mid),
        label_r * math.sin(mid),
        f"Λ_LE = {math.degrees(sweep_le):.4g}°",
        ha="left",
        va="center",
        fontsize=8,
        color="#1a5276",
        zorder=6,
    )


def emit(wing: Planform, path: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("span_m", wing.span)
    print_kv("root_chord_m", wing.root)
    print_kv("tip_chord_m", wing.tip)
    print_kv("sweep_le_source", "given" if wing.sweep_input is not None else "omitted")
    if wing.sweep_input is not None and wing.sweep_at is not None:
        print_kv("sweep_rad", wing.sweep_input)
        print_kv("sweep_deg", math.degrees(wing.sweep_input))
        print_kv("sweep_at", wing.sweep_at)
        print_kv("sweep_at_source", wing.sweep_at_source)
    print_kv("sweep_le_rad", wing.sweep_le)
    print_kv("sweep_le_deg", math.degrees(wing.sweep_le))
    print_kv("area_m2", wing.area)
    print_kv("AR", wing.aspect_ratio)
    print_kv("taper", wing.taper)
    print_kv("mac_m", wing.mac)
    print_kv("y_mac_m", wing.y_mac)
    print_kv("sweep_c4_rad", wing.sweep_c4)
    print_kv("sweep_c4_deg", math.degrees(wing.sweep_c4))
    print_kv("sweep_te_rad", wing.sweep_te)
    print_kv("sweep_te_deg", math.degrees(wing.sweep_te))
    print_kv("x_le_mac_m", wing.x_le_mac)
    print_kv("graph", str(path))


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def validate(span: float, root: float, tip: float, sweep: float | None, sweep_at: float | None, sweep_at_given: bool) -> None:
    require_positive("span", span)
    require_positive("root chord", root)
    if not math.isfinite(tip) or tip < 0.0:
        raise ValueError("tip chord must be finite and >= 0")
    if sweep is None:
        if sweep_at_given:
            raise ValueError("--sweep-at requires --sweep")
        return
    if not math.isfinite(sweep) or not -SWEEP_LIMIT < sweep < SWEEP_LIMIT:
        raise ValueError("sweep must be finite and strictly between -pi/2 and pi/2")
    if not sweep_at_given:
        return
    if sweep_at is None or not math.isfinite(sweep_at) or not 0.0 <= sweep_at <= 1.0:
        raise ValueError("--sweep-at must be from 0 at the leading edge to 1 at the trailing edge")


def half_span_integrals(span: float, root: float, tip: float) -> tuple[float, float]:
    """int_0^(b/2) c^2 dy and int_0^(b/2) y c dy for a linear taper.

    c(y) = cr + k y, with k = 2(ct - cr)/b. These are the integral definitions
    of the mean aerodynamic chord and its station, expanded apart from the
    closed forms.
    """
    half = span / 2.0
    slope = 2.0 * (tip - root) / span
    chord_sq = (
        root**2 * half
        + root * slope * half**2
        + slope**2 * half**3 / 3.0
    )
    first_moment = root * half**2 / 2.0 + slope * half**3 / 3.0
    return chord_sq, first_moment


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    # taper_half identities: b = 10, cr = 2, ct = 1, lambda = 1/2, S = 15, AR = 20/3.
    wing = planform_from(10.0, 2.0, 1.0, None, None, False)
    if wing.sweep_at_source != "omitted" or wing.sweep_le != 0.0:
        return fail("omitted sweep did not leave the leading edge unswept")
    if not close_enough(wing.taper, 0.5, 1.0):
        return fail("taper")
    if not close_enough(wing.area, 15.0, 15.0):
        return fail("area")
    if not close_enough(wing.aspect_ratio, 20.0 / 3.0, 10.0):
        return fail("aspect ratio")
    if not close_enough(wing.mac, 14.0 / 9.0, 1.0):
        return fail("mean aerodynamic chord")
    if not close_enough(wing.y_mac, 20.0 / 9.0, 1.0):
        return fail("spanwise station")
    if not close_enough(wing.x_le_mac, 0.0, 1.0):
        return fail("unswept MAC leading edge")
    if not close_enough(wing.sweep_c4, math.atan(-1.0 / 20.0), 1.0):
        return fail("quarter-chord sweep")
    if not close_enough(wing.sweep_te, math.atan(-0.2), 1.0):
        return fail("trailing-edge sweep")

    chord_sq, first_moment = half_span_integrals(10.0, 2.0, 1.0)
    if not close_enough(2.0 * chord_sq / wing.area, wing.mac, 1.0):
        return fail("MAC integral")
    if not close_enough(2.0 * first_moment / wing.area, wing.y_mac, 1.0):
        return fail("station integral")

    # Rectangular: MAC is the chord, the station is b/4, and every sweep matches.
    rectangular = planform_from(10.0, 2.0, 2.0, math.pi / 6.0, 0.25, True)
    if rectangular.sweep_at_source != "given":
        return fail("given sweep station")
    if not close_enough(rectangular.area, 20.0, 20.0):
        return fail("rectangular area")
    if not close_enough(rectangular.aspect_ratio, rectangular.span / rectangular.root, 1.0):
        return fail("rectangular aspect ratio is not span/chord")
    if not close_enough(rectangular.mac, 2.0, 1.0):
        return fail("rectangular MAC")
    if not close_enough(rectangular.y_mac, 2.5, 1.0):
        return fail("rectangular station")
    if not close_enough(rectangular.sweep_le, math.pi / 6.0, 1.0):
        return fail("rectangular leading-edge sweep")
    if not close_enough(rectangular.sweep_c4, math.pi / 6.0, 1.0):
        return fail("rectangular quarter-chord sweep")
    if not close_enough(rectangular.sweep_te, math.pi / 6.0, 1.0):
        return fail("rectangular trailing-edge sweep")
    if not close_enough(rectangular.x_le_mac, 2.5 * math.tan(math.pi / 6.0), 1.0):
        return fail("rectangular MAC leading edge")

    # Pointed tip, and a quarter-chord sweep of zero on the tapered wing.
    pointed = planform_from(10.0, 2.0, 0.0, None, None, False)
    if not close_enough(pointed.taper, 0.0, 1.0):
        return fail("pointed taper")
    if not close_enough(pointed.area, 10.0, 10.0):
        return fail("pointed area")
    if not close_enough(pointed.mac, 4.0 / 3.0, 1.0):
        return fail("pointed MAC")
    if not close_enough(pointed.y_mac, 5.0 / 3.0, 1.0):
        return fail("pointed station")

    matched = planform_from(10.0, 2.0, 1.0, 0.0, 0.25, True)
    expected_le = math.atan((1.0 - 0.5) / (matched.aspect_ratio * (1.0 + 0.5)))
    if not close_enough(matched.sweep_le, expected_le, 1.0):
        return fail("zero quarter-chord sweep did not recover the leading edge")
    if not close_enough(matched.sweep_c4, 0.0, 1.0):
        return fail("quarter-chord sweep was not zero")

    # Forty-five degree leading edge: x = y.
    swept = planform_from(10.0, 2.0, 1.0, math.pi / 4.0, 0.0, True)
    if not close_enough(swept.x_le_mac, swept.y_mac, 1.0):
        return fail("45 degree leading edge")
    if swept.sweep_at_source != "given":
        return fail("leading-edge station source")

    try:
        validate(10.0, 2.0, 1.0, None, 0.25, True)
    except ValueError:
        pass
    else:
        return fail("sweep station without a sweep was accepted")
    try:
        validate(-1.0, 2.0, 1.0, None, None, False)
    except ValueError:
        pass
    else:
        return fail("negative span was accepted")
    try:
        validate(10.0, 2.0, -0.1, None, None, False)
    except ValueError:
        pass
    else:
        return fail("negative tip chord was accepted")
    try:
        validate(10.0, 2.0, 1.0, math.pi / 2.0, None, False)
    except ValueError:
        pass
    else:
        return fail("sweep of pi/2 was accepted")

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "wing.png")
        captured: list[str] = []

        class _Capture:
            def write(self, text: str) -> None:
                captured.append(text)

            def flush(self) -> None:
                return None

        old_out = sys.stdout
        sys.stdout = _Capture()
        try:
            code = main(
                [
                    "--span",
                    "10",
                    "--root",
                    "2",
                    "--tip",
                    "1",
                    "--sweep",
                    str(math.pi / 6.0),
                    "--out",
                    out,
                ]
            )
        finally:
            sys.stdout = old_out
        if code != 0:
            return fail(f"main returned {code}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        text = "".join(captured)
        for key in (
            "title: Wing geometry",
            "sweep_at_source: default-quarter-chord",
            "area_m2:",
            "AR:",
            "taper:",
            "mac_m:",
            "y_mac_m:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

    sink = sys.stderr
    sys.stderr = tempfile.TemporaryFile(mode="w+")
    try:
        missing = main([])
    finally:
        sys.stderr.close()
        sys.stderr = sink
    if missing != 2:
        return fail("missing inputs were accepted")

    print("check: pass")
    print_kv("area_m2", wing.area)
    print_kv("AR", wing.aspect_ratio)
    print_kv("taper", wing.taper)
    print_kv("mac_m", wing.mac)
    print_kv("y_mac_m", wing.y_mac)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Trapezoidal wing area, taper, mean aerodynamic chord, and a plan view."
    )
    parser.add_argument("--span", type=float, default=None, help="span b, tip to tip [m]")
    parser.add_argument("--root", type=float, default=None, help="streamwise root chord cr [m]")
    parser.add_argument("--tip", type=float, default=None, help="streamwise tip chord ct [m]")
    parser.add_argument(
        "--sweep",
        type=float,
        default=None,
        help="sweep of the chord line given by --sweep-at [rad]",
    )
    parser.add_argument(
        "--sweep-at",
        type=float,
        default=None,
        help="chord fraction of --sweep: 0 leading edge, 0.25 quarter chord, 1 trailing edge",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {"--span": args.span, "--root": args.root, "--tip": args.tip}
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --span, --root, and --tip; missing " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2

    sweep_at_given = args.sweep_at is not None
    try:
        validate(args.span, args.root, args.tip, args.sweep, args.sweep_at, sweep_at_given)
        wing = planform_from(args.span, args.root, args.tip, args.sweep, args.sweep_at, sweep_at_given)
        out_path = Path(args.out) if args.out else SKILL_DIR / "wing_geometry.png"
        out_path = out_path.resolve()
        plot_wing(out_path, wing)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(wing, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
