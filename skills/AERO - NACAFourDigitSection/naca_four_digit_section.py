#!/usr/bin/env python3
"""NACA four-digit section ordinates and measured section coefficients.

Geometry is naca4_thickness on the two-parabola mean line.
Section cl, cd, and cm are interpolated from NACA Report 824
Langley two-dimensional low-turbulence pressure-tunnel charts,
not from inviscid thin-airfoil theory.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "NACA four-digit section"
COEFF_TITLE = "NACA four-digit coefficients"
POLAR_TITLE = "NACA four-digit drag polar"
N_DRAW = 201
POLAR_FILE = "report824_polars.json"

TABLE_XI = (
    0.0,
    0.0125,
    0.025,
    0.05,
    0.075,
    0.1,
    0.15,
    0.2,
    0.25,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    0.95,
    1.0,
)

SKILL_DIR = Path(__file__).resolve().parent
DATA_PATH = SKILL_DIR / "data" / POLAR_FILE
DESIGNATION = re.compile(r"^(?:naca\s*)?(\d{4})$", re.IGNORECASE)

ASSUMPTIONS = (
    "NACA four-digit family geometry of NACA Report 460; "
    "naca4_thickness and the two-parabola mean line; "
    "thickness laid off normal to the mean line; "
    "section cl, cd, and cm_c/4 from NACA Report 824 "
    "Langley two-dimensional low-turbulence pressure-tunnel charts; "
    "smooth surface; Reynolds number of a digitized curve, or log-linear "
    "interpolation between the two neighboring digitized Reynolds numbers; "
    "no extrapolation outside the measured Re set; "
    "linear interpolation in angle of attack and in cl on the polar; "
    "no inviscid thin-airfoil lift, no d'Alembert cd = 0, and no "
    "Prandtl-Glauert Mach correction; "
    "an airfoil without a Report 824 chart in data/ is not computed; "
    "the coefficient and polar figures cover the measured angle range; "
    "those figures use degrees; CLI --alpha is radians"
)

DEFAULT_RE = 6.0e6


@dataclass(frozen=True)
class Digits:
    designation: str
    m: float
    p: float
    t: float


@dataclass(frozen=True)
class Station:
    xi: float
    yc: float
    yt: float
    theta: float
    xu: float
    yu: float
    xl: float
    yl: float


@dataclass(frozen=True)
class Polar:
    designation: str
    reynolds: float
    source: str
    surface: str
    alpha_deg: tuple[float, ...]
    cl: tuple[float, ...]
    cm_c4: tuple[float, ...]
    cl_polar: tuple[float, ...]
    cd: tuple[float, ...]
    cd_alpha: tuple[float, ...]


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close_enough(got: float, expected: float, scale: float | None = None) -> bool:
    span = scale if scale is not None else max(abs(expected), 1.0)
    return abs(got - expected) <= CHECK_TOL * span


def parse_designation(text: str) -> Digits:
    cleaned = " ".join(text.strip().split())
    match = DESIGNATION.fullmatch(cleaned)
    if match is None:
        raise ValueError("NACA designation must be four digits, optionally prefixed by NACA")
    code = match.group(1)
    m = int(code[0]) / 100.0
    p = int(code[1]) / 10.0
    t = int(code[2:]) / 100.0
    if m > 0.0 and p <= 0.0:
        raise ValueError("a cambered four-digit section needs a nonzero camber station")
    if t <= 0.0:
        raise ValueError("thickness digits must be greater than 00")
    return Digits(designation=code, m=m, p=p, t=t)


def thickness_ratio(t: float, xi: float) -> float:
    """naca4_thickness, yt/c."""
    if xi <= 0.0:
        return 0.0
    return (t / 0.2) * (
        0.2969 * xi**0.5
        - 0.1260 * xi
        - 0.3516 * xi**2
        + 0.2843 * xi**3
        - 0.1015 * xi**4
    )


def camber_ratio(m: float, p: float, xi: float) -> float:
    """naca4_camber_forward or naca4_camber_aft, yc/c."""
    if m == 0.0:
        return 0.0
    if xi <= p:
        return (m / p**2) * (2.0 * p * xi - xi**2)
    return (m / (1.0 - p) ** 2) * ((1.0 - 2.0 * p) + 2.0 * p * xi - xi**2)


def camber_slope(m: float, p: float, xi: float) -> float:
    """naca4_camber_slope_forward or naca4_camber_slope_aft."""
    if m == 0.0:
        return 0.0
    if xi <= p:
        return (2.0 * m / p**2) * (p - xi)
    return (2.0 * m / (1.0 - p) ** 2) * (p - xi)


def leading_edge_radius(t: float, chord: float) -> float:
    """naca4_leading_edge_radius."""
    return 0.5 * (0.2969 * t / 0.2) ** 2 * chord


def station_at(digits: Digits, chord: float, xi: float) -> Station:
    yt = thickness_ratio(digits.t, xi) * chord
    yc = camber_ratio(digits.m, digits.p, xi) * chord
    theta = math.atan(camber_slope(digits.m, digits.p, xi))
    x = xi * chord
    return Station(
        xi=xi,
        yc=yc,
        yt=yt,
        theta=theta,
        xu=x - yt * math.sin(theta),
        yu=yc + yt * math.cos(theta),
        xl=x + yt * math.sin(theta),
        yl=yc - yt * math.cos(theta),
    )


def cosine_stations(count: int) -> list[float]:
    if count < 2:
        raise ValueError("need at least two stations")
    n = count - 1
    return [0.5 * (1.0 - math.cos(math.pi * i / n)) for i in range(count)]


def lerp(x: float, xp: tuple[float, ...], fp: tuple[float, ...]) -> float:
    if len(xp) != len(fp) or len(xp) < 2:
        raise ValueError("interpolation tables must have at least two matching points")
    if x <= xp[0]:
        if x < xp[0]:
            raise ValueError(f"value {x:g} is below the measured table")
        return fp[0]
    if x >= xp[-1]:
        if x > xp[-1]:
            raise ValueError(f"value {x:g} is above the measured table")
        return fp[-1]
    for i in range(1, len(xp)):
        if x <= xp[i]:
            span = xp[i] - xp[i - 1]
            if span == 0.0:
                return fp[i]
            w = (x - xp[i - 1]) / span
            return fp[i - 1] + w * (fp[i] - fp[i - 1])
    return fp[-1]


def load_curve(name: str, source: str, surface: str, block: dict) -> Polar:
    if len(block["alpha_deg"]) != len(block["cl"]) or len(block["cl"]) != len(block["cm_c4"]):
        raise ValueError(f"{name} lift/moment tables are different lengths")
    if len(block["cl_polar"]) != len(block["cd"]):
        raise ValueError(f"{name} polar tables are different lengths")
    if "cd_alpha" in block:
        cd_alpha = tuple(float(v) for v in block["cd_alpha"])
        if len(cd_alpha) != len(block["alpha_deg"]):
            raise ValueError(f"{name} cd-versus-alpha table is the wrong length")
    else:
        cd_alpha = tuple(float("nan") for _ in block["alpha_deg"])
    return Polar(
        designation=name,
        reynolds=float(block["Re"]),
        source=source,
        surface=surface,
        alpha_deg=tuple(float(v) for v in block["alpha_deg"]),
        cl=tuple(float(v) for v in block["cl"]),
        cm_c4=tuple(float(v) for v in block["cm_c4"]),
        cl_polar=tuple(float(v) for v in block["cl_polar"]),
        cd=tuple(float(v) for v in block["cd"]),
        cd_alpha=cd_alpha,
    )


def load_catalog(path: Path = DATA_PATH) -> dict[str, tuple[Polar, ...]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    source = str(raw["source"])
    surface = str(raw["surface"])
    catalog: dict[str, tuple[Polar, ...]] = {}
    for name, block in raw["airfoils"].items():
        if "curves" in block:
            curves = [load_curve(name, source, surface, item) for item in block["curves"]]
        else:
            curves = [load_curve(name, source, surface, block)]
        curves.sort(key=lambda item: item.reynolds)
        catalog[name] = tuple(curves)
    return catalog


def available_names(catalog: dict[str, tuple[Polar, ...]]) -> str:
    return ", ".join(sorted(catalog))


def format_re_list(curves: tuple[Polar, ...]) -> str:
    return ", ".join(f"{item.reynolds:.8g}" for item in curves)


def mix_tables(
    weight: float,
    xa: tuple[float, ...],
    fa: tuple[float, ...],
    xb: tuple[float, ...],
    fb: tuple[float, ...],
    xq: tuple[float, ...],
) -> tuple[float, ...]:
    return tuple((1.0 - weight) * lerp(x, xa, fa) + weight * lerp(x, xb, fb) for x in xq)


def blend_polars(low: Polar, high: Polar, reynolds: float) -> Polar:
    span = math.log(high.reynolds) - math.log(low.reynolds)
    if span == 0.0:
        return low
    weight = (math.log(reynolds) - math.log(low.reynolds)) / span
    a0 = max(low.alpha_deg[0], high.alpha_deg[0])
    a1 = min(low.alpha_deg[-1], high.alpha_deg[-1])
    alphas = tuple(sorted({x for x in low.alpha_deg + high.alpha_deg if a0 <= x <= a1}))
    c0 = max(min(low.cl_polar), min(high.cl_polar))
    c1 = min(max(low.cl_polar), max(high.cl_polar))
    lifts = tuple(sorted({x for x in low.cl_polar + high.cl_polar if c0 <= x <= c1}))
    if len(alphas) < 2 or len(lifts) < 2:
        raise ValueError("neighboring Reynolds-number charts do not overlap")
    return Polar(
        designation=low.designation,
        reynolds=reynolds,
        source=low.source,
        surface=low.surface,
        alpha_deg=alphas,
        cl=mix_tables(weight, low.alpha_deg, low.cl, high.alpha_deg, high.cl, alphas),
        cm_c4=mix_tables(weight, low.alpha_deg, low.cm_c4, high.alpha_deg, high.cm_c4, alphas),
        cl_polar=lifts,
        cd=mix_tables(weight, low.cl_polar, low.cd, high.cl_polar, high.cd, lifts),
        cd_alpha=mix_tables(weight, low.alpha_deg, low.cd_alpha, high.alpha_deg, high.cd_alpha, alphas),
    )


def polar_for(
    digits: Digits,
    catalog: dict[str, tuple[Polar, ...]],
    reynolds: float | None,
) -> Polar:
    curves = catalog.get(digits.designation)
    if curves is None:
        raise ValueError(
            "NACA Report 824 section chart is not in the table for "
            f"{digits.designation}; available: {available_names(catalog)}"
        )
    if reynolds is None:
        return min(curves, key=lambda item: abs(item.reynolds - DEFAULT_RE))
    if not math.isfinite(reynolds) or reynolds <= 0.0:
        raise ValueError("Reynolds number must be finite and greater than 0")
    for item in curves:
        if abs(reynolds - item.reynolds) <= 1e-6 * item.reynolds:
            return item
    if reynolds < curves[0].reynolds or reynolds > curves[-1].reynolds:
        raise ValueError(
            f"Reynolds number {reynolds:.8g} is outside the Report 824 table for "
            f"{digits.designation}; available Re: {format_re_list(curves)}"
        )
    for low, high in zip(curves, curves[1:]):
        if low.reynolds <= reynolds <= high.reynolds:
            return blend_polars(low, high, reynolds)
    raise ValueError("could not place Reynolds number between neighboring charts")


def zero_lift_deg(polar: Polar) -> float:
    """Geometric α_L0 from the lift curve as angle increases through cl = 0.

    Post-stall hysteresis can cross zero while cl is falling; ignore those
    downward crossings so heavily cambered charts (e.g. 4412) still resolve.
    """
    cl = polar.cl
    alpha = polar.alpha_deg
    for i in range(1, len(cl)):
        lo, hi = cl[i - 1], cl[i]
        if lo == 0.0:
            return alpha[i - 1]
        if lo < 0.0 < hi:
            return lerp(0.0, (lo, hi), (alpha[i - 1], alpha[i]))
        if lo < 0.0 and hi == 0.0:
            return alpha[i]
    raise ValueError(
        f"measured lift curve for NACA {polar.designation} does not cross zero "
        "with increasing angle of attack"
    )


def _alpha_in_table(polar: Polar, alpha_deg: float) -> None:
    lo, hi = polar.alpha_deg[0], polar.alpha_deg[-1]
    if alpha_deg < lo or alpha_deg > hi:
        raise ValueError(
            f"angle of attack {alpha_deg:g} deg is outside the Report 824 table "
            f"for {polar.designation}; measured range [{lo:g}, {hi:g}] deg"
        )


def cl_at(polar: Polar, alpha_deg: float) -> float:
    _alpha_in_table(polar, alpha_deg)
    return lerp(alpha_deg, polar.alpha_deg, polar.cl)


def cm_at(polar: Polar, alpha_deg: float) -> float:
    _alpha_in_table(polar, alpha_deg)
    return lerp(alpha_deg, polar.alpha_deg, polar.cm_c4)


def cd_at_cl(polar: Polar, cl: float) -> float:
    lo, hi = polar.cl_polar[0], polar.cl_polar[-1]
    if cl < lo or cl > hi:
        raise ValueError(
            f"section lift {cl:g} is outside the Report 824 polar for "
            f"{polar.designation}; measured cl range [{lo:g}, {hi:g}]"
        )
    return lerp(cl, polar.cl_polar, polar.cd)


def cd_at(polar: Polar, alpha_deg: float) -> float:
    if polar.cd_alpha and all(math.isfinite(v) for v in polar.cd_alpha):
        _alpha_in_table(polar, alpha_deg)
        return lerp(alpha_deg, polar.alpha_deg, polar.cd_alpha)
    return cd_at_cl(polar, cl_at(polar, alpha_deg))


def clmax(polar: Polar) -> tuple[float, float]:
    peak = max(range(len(polar.cl)), key=lambda i: polar.cl[i])
    return polar.alpha_deg[peak], polar.cl[peak]


def cdmin(polar: Polar) -> tuple[float, float]:
    low = min(range(len(polar.cd)), key=lambda i: polar.cd[i])
    return polar.cl_polar[low], polar.cd[low]


def save_png(fig, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(suffix=".png", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with open(fd, "wb") as handle:
            fig.savefig(handle, dpi=140, format="png")
        try:
            os.replace(tmp, path)
        except OSError:
            fig.savefig(path, dpi=140)
            tmp.unlink(missing_ok=True)
    except Exception:
        tmp.unlink(missing_ok=True)
        fig.savefig(path, dpi=140)


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to draw the section") from exc
    return plt


def plot_section(path: Path, digits: Digits, chord: float, stations: list[Station]) -> None:
    plt = ensure_matplotlib()
    xu = [row.xu for row in stations]
    yu = [row.yu for row in stations]
    xl = [row.xl for row in reversed(stations)]
    yl = [row.yl for row in reversed(stations)]
    x_loop = xu + xl
    y_loop = yu + yl
    xc = [row.xi * chord for row in stations]
    yc = [row.yc for row in stations]
    fig, ax = plt.subplots(figsize=(9.2, 3.6))
    ax.fill(x_loop, y_loop, color="#d6eaf8", zorder=1)
    ax.plot(x_loop, y_loop, color="#1a5276", linewidth=1.6, zorder=2)
    ax.plot(xc, yc, color="#c0392b", linewidth=1.2, zorder=3, label="mean line")
    ax.plot([0.0, chord], [0.0, 0.0], color="#7f8c8d", linestyle=":", linewidth=0.9, zorder=2)
    ax.set_aspect("equal", adjustable="datalim")
    pad = 0.08 * chord
    ax.set_xlim(-pad, chord + pad)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title(PLOT_TITLE)
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    ax.text(
        0.01,
        0.04,
        f"NACA {digits.designation},  c = {chord:.4g} m",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8,
        color="#1c2833",
    )
    fig.tight_layout()
    save_png(fig, path)
    plt.close(fig)


def plot_coefficients(
    path: Path,
    digits: Digits,
    polar: Polar,
    alpha_l0_deg: float,
    alpha_mark_deg: float | None,
) -> None:
    plt = ensure_matplotlib()
    deg = list(polar.alpha_deg)
    cl = list(polar.cl)
    cm = list(polar.cm_c4)
    cd = [cd_at(polar, a) for a in deg]
    fig, axes = plt.subplots(3, 1, figsize=(7.2, 8.0), sharex=True)
    series = (
        (axes[0], cl, r"$c_l$", "#1a5276"),
        (axes[1], cm, r"$c_{m,c/4}$", "#c0392b"),
        (axes[2], cd, r"$c_d$", "#1a5276"),
    )
    for ax, values, ylabel, color in series:
        ax.plot(deg, values, color=color, linewidth=1.6)
        ax.axhline(0.0, color="#7f8c8d", linewidth=0.6)
        ax.axvline(0.0, color="#7f8c8d", linewidth=0.6)
        ax.axvline(alpha_l0_deg, color="#c0392b", linestyle="--", linewidth=0.9)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.25)
    if alpha_mark_deg is not None:
        axes[0].plot(alpha_mark_deg, cl_at(polar, alpha_mark_deg), "s", color="#c0392b", markersize=5)
        axes[1].plot(alpha_mark_deg, cm_at(polar, alpha_mark_deg), "s", color="#c0392b", markersize=5)
        axes[2].plot(alpha_mark_deg, cd_at(polar, alpha_mark_deg), "s", color="#c0392b", markersize=5)
    axes[2].set_xlabel("geometric angle of attack (deg)")
    axes[0].set_title(COEFF_TITLE)
    axes[0].text(
        0.02,
        0.92,
        f"NACA {digits.designation}\nReport 824, Re = {polar.reynolds:.2g}",
        transform=axes[0].transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )
    fig.tight_layout()
    save_png(fig, path)
    plt.close(fig)


def plot_polar(
    path: Path,
    digits: Digits,
    polar: Polar,
    alpha_mark_deg: float | None,
) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    ax.plot(polar.cd, polar.cl_polar, color="#1a5276", linewidth=1.6)
    ax.axhline(0.0, color="#7f8c8d", linewidth=0.6)
    ax.axvline(0.0, color="#7f8c8d", linewidth=0.6)
    if alpha_mark_deg is not None:
        lift = cl_at(polar, alpha_mark_deg)
        ax.plot(cd_at_cl(polar, lift), lift, "s", color="#c0392b", markersize=6)
    ax.set_xlabel(r"$c_d$")
    ax.set_ylabel(r"$c_l$")
    ax.set_title(POLAR_TITLE)
    ax.grid(True, alpha=0.25)
    ax.set_xlim(left=0.0)
    ax.text(
        0.02,
        0.98,
        f"NACA {digits.designation}\nReport 824, Re = {polar.reynolds:.2g}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=8,
    )
    fig.tight_layout()
    save_png(fig, path)
    plt.close(fig)


def write_ordinates(path: Path, rows: list[Station]) -> None:
    lines = ["xi yc_m yt_m theta_rad xu_m yu_m xl_m yl_m"]
    for row in rows:
        lines.append(
            f"{row.xi:.8g} {row.yc:.8g} {row.yt:.8g} {row.theta:.8g} "
            f"{row.xu:.8g} {row.yu:.8g} {row.xl:.8g} {row.yl:.8g}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate(digits: Digits, chord: float, alpha: float | None, reynolds: float | None) -> None:
    if not math.isfinite(chord) or chord <= 0.0:
        raise ValueError("chord must be finite and greater than 0")
    if not math.isfinite(digits.t) or not (0.0 < digits.t < 1.0):
        raise ValueError("thickness ratio must lie strictly between 0 and 1")
    if not math.isfinite(digits.m) or not (0.0 <= digits.m < 1.0):
        raise ValueError("camber ratio must lie in [0, 1)")
    if digits.m > 0.0 and not (0.0 < digits.p < 1.0):
        raise ValueError("camber station p must lie strictly between 0 and 1")
    if alpha is not None:
        if not math.isfinite(alpha):
            raise ValueError("angle of attack must be finite")
        if abs(alpha) >= math.pi / 2.0:
            raise ValueError("angle of attack must lie strictly between -pi/2 and pi/2")
    if reynolds is not None:
        if not math.isfinite(reynolds) or reynolds <= 0.0:
            raise ValueError("Reynolds number must be finite and greater than 0")


def emit(
    digits: Digits,
    chord: float,
    alpha: float | None,
    polar: Polar,
    alpha_l0_deg: float,
    rle: float,
    table: list[Station],
    section_path: Path,
    coeff_path: Path,
    polar_path: Path,
    ordinates_path: Path,
    re_table: str,
) -> None:
    stall_deg, cl_peak = clmax(polar)
    cl_at_min_d, min_d = cdmin(polar)
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("designation", digits.designation)
    print_kv("chord_m", chord)
    print_kv("m", digits.m)
    print_kv("p", 0.0 if digits.m == 0.0 else digits.p)
    print_kv("t", digits.t)
    print_kv("Rle_m", rle)
    print_kv("data_source", "NACA Report 824")
    print_kv("tunnel", "Langley 2-D low-turbulence pressure tunnel")
    print_kv("surface", polar.surface)
    print_kv("Re", polar.reynolds)
    print_kv("Re_table", re_table)
    print_kv("alpha_L0_deg", alpha_l0_deg)
    print_kv("alpha_L0_rad", math.radians(alpha_l0_deg))
    print_kv("clmax", cl_peak)
    print_kv("alpha_clmax_deg", stall_deg)
    print_kv("cdmin", min_d)
    print_kv("cl_cdmin", cl_at_min_d)
    print_kv("alpha_min_deg", polar.alpha_deg[0])
    print_kv("alpha_max_deg", polar.alpha_deg[-1])
    if alpha is not None:
        alpha_deg = math.degrees(alpha)
        print_kv("alpha_rad", alpha)
        print_kv("alpha_deg", alpha_deg)
        print_kv("cl", cl_at(polar, alpha_deg))
        print_kv("cd", cd_at(polar, alpha_deg))
        print_kv("cm", cm_at(polar, alpha_deg))
    max_camber = max(table, key=lambda row: row.yc)
    max_thick = max(table, key=lambda row: row.yt)
    print_kv("yc_max_m", max_camber.yc)
    print_kv("xi_yc_max", max_camber.xi)
    print_kv("yt_max_m", max_thick.yt)
    print_kv("xi_yt_max", max_thick.xi)
    print_kv("yt_te_m", table[-1].yt)
    print_kv("ordinates", str(ordinates_path))
    print_kv("graph", str(section_path))
    print_kv("coefficients_graph", str(coeff_path))
    print_kv("polar_graph", str(polar_path))


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    basic = parse_designation("0020")
    if not close_enough(thickness_ratio(basic.t, 1.0), 0.0021, 1.0):
        return fail("twenty-percent trailing-edge thickness")
    if not close_enough(camber_ratio(0.02, 0.4, 0.4), 0.02, 1.0):
        return fail("camber at maximum")
    if not close_enough(leading_edge_radius(0.2, 1.0), 0.5 * 0.2969**2, 1.0):
        return fail("leading-edge radius")

    catalog = load_catalog()
    foil = parse_designation("2412")
    polar = polar_for(foil, catalog, None)
    if abs(polar.reynolds - 5700000.0) > 1.0:
        return fail(f"default 2412 Re {polar.reynolds}")
    l0 = zero_lift_deg(polar)
    if not -3.0 < l0 < -1.0:
        return fail(f"2412 zero-lift angle {l0}")
    if cl_at(polar, 0.0) <= 0.0:
        return fail("2412 should lift at zero geometric angle")
    if cd_at(polar, 0.0) <= 0.0:
        return fail("2412 measured cd must be positive")
    _, min_d = cdmin(polar)
    if not 0.004 < min_d < 0.012:
        return fail("2412 cdmin out of Report 824 range")

    camber44 = polar_for(parse_designation("4412"), catalog, None)
    l0_4412 = zero_lift_deg(camber44)
    if not close_enough(l0_4412, -4.0, 1.0):
        return fail(f"4412 zero-lift angle {l0_4412}")
    if cl_at(camber44, 0.0) <= 0.0:
        return fail("4412 should lift at zero geometric angle")
    if cd_at(camber44, 0.0) <= 0.0:
        return fail("4412 measured cd must be positive")

    sym = polar_for(parse_designation("0012"), catalog, 6000000.0)
    if abs(cl_at(sym, 0.0)) > 0.02:
        return fail("0012 lift at zero angle")
    if abs(cm_at(sym, 0.0)) > 0.02:
        return fail("0012 moment at zero angle")
    if cd_at(sym, 0.0) <= 0.0:
        return fail("0012 measured cd must be positive")

    low = polar_for(foil, catalog, 3100000.0)
    high = polar_for(foil, catalog, 8900000.0)
    mid = polar_for(foil, catalog, 6000000.0)
    if not (cdmin(high)[1] < cdmin(polar)[1] < cdmin(low)[1]):
        return fail("2412 cdmin does not fall with Reynolds number")
    if not (cdmin(high)[1] < cdmin(mid)[1] < cdmin(low)[1]):
        return fail("interpolated 2412 cdmin is out of order")
    try:
        polar_for(foil, catalog, 1.0e5)
    except ValueError:
        pass
    else:
        return fail("Reynolds number below the table was accepted")

    try:
        polar_for(parse_designation("2315"), catalog, None)
    except ValueError:
        pass
    else:
        return fail("missing Report 824 chart was accepted")

    try:
        cl_at(camber44, -40.0)
    except ValueError as exc:
        if "outside the Report 824 table" not in str(exc):
            return fail(f"alpha-out-of-range message was unclear: {exc}")
    else:
        return fail("angle far below the table was accepted")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
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
                    "--naca",
                    "2412",
                    "--chord",
                    "1",
                    "--alpha",
                    "0.0872664625997",
                    "--re",
                    "5700000",
                    "--out",
                    str(base / "section.png"),
                    "--out-coeff",
                    str(base / "coeff.png"),
                    "--out-polar",
                    str(base / "polar.png"),
                    "--out-ordinates",
                    str(base / "ordinates.txt"),
                ]
            )
        finally:
            sys.stdout = old_out
        if code != 0:
            return fail(f"main returned {code}")
        for name in ("section.png", "coeff.png", "polar.png"):
            if not (base / name).read_bytes().startswith(b"\x89PNG"):
                return fail(f"{name} is not a PNG")
        text = "".join(captured)
        for key in (
            "title: NACA four-digit section",
            "designation: 2412",
            "data_source: NACA Report 824",
            "Re:",
            "cl:",
            "cd:",
            "cm:",
            "graph:",
            "coefficients_graph:",
            "polar_graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "cd: 0" in text.splitlines() or "cd: 0.0\n" in text:
            return fail("inviscid zero drag was printed")

        captured.clear()
        sys.stdout = _Capture()
        try:
            code = main(
                [
                    "--naca",
                    "4412",
                    "--chord",
                    "1",
                    "--out",
                    str(base / "section4412.png"),
                    "--out-coeff",
                    str(base / "coeff4412.png"),
                    "--out-polar",
                    str(base / "polar4412.png"),
                    "--out-ordinates",
                    str(base / "ordinates4412.txt"),
                ]
            )
        finally:
            sys.stdout = old_out
        if code != 0:
            return fail(f"4412 geometry-only main returned {code}")
        omit_text = "".join(captured)
        if "designation: 4412" not in omit_text or "alpha_L0_deg:" not in omit_text:
            return fail("4412 omit-alpha/re stdout incomplete")
        lines = omit_text.splitlines()
        if any(line.startswith("cl:") for line in lines):
            return fail("4412 omit-alpha run printed a point cl")
        if not (base / "section4412.png").read_bytes().startswith(b"\x89PNG"):
            return fail("4412 section.png is not a PNG")

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
    print_kv("alpha_L0_deg", l0)
    print_kv("cdmin", min_d)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NACA four-digit ordinates and Report 824 measured section coefficients."
    )
    parser.add_argument("--naca", type=str, default=None, help="four-digit designation, optionally prefixed by NACA")
    parser.add_argument("--chord", type=float, default=None, help="chord [m]")
    parser.add_argument("--alpha", type=float, default=None, help="geometric angle of attack [rad]")
    parser.add_argument("--re", type=float, default=None, help="chord Reynolds number [-]")
    parser.add_argument("--out", type=str, default=None, help="section PNG path")
    parser.add_argument("--out-coeff", type=str, default=None, help="coefficients-versus-alpha PNG path")
    parser.add_argument("--out-polar", type=str, default=None, help="drag-polar PNG path")
    parser.add_argument("--out-ordinates", type=str, default=None, help="ordinate table path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.naca is None or args.chord is None:
        print("error: requires --naca and --chord", file=sys.stderr)
        return 2
    try:
        digits = parse_designation(args.naca)
        validate(digits, args.chord, args.alpha, args.re)
        catalog = load_catalog()
        polar = polar_for(digits, catalog, args.re)
        re_table = format_re_list(catalog[digits.designation])
        alpha_l0_deg = zero_lift_deg(polar)
        alpha_mark_deg = None if args.alpha is None else math.degrees(args.alpha)
        if alpha_mark_deg is not None:
            cl_at(polar, alpha_mark_deg)
            cd_at(polar, alpha_mark_deg)
        rle = leading_edge_radius(digits.t, args.chord)
        draw = [station_at(digits, args.chord, xi) for xi in cosine_stations(N_DRAW)]
        table = [station_at(digits, args.chord, xi) for xi in TABLE_XI]
        section_path = Path(args.out) if args.out else SKILL_DIR / "naca_four_digit_section.png"
        coeff_path = Path(args.out_coeff) if args.out_coeff else SKILL_DIR / "naca_four_digit_coefficients.png"
        polar_path = Path(args.out_polar) if args.out_polar else SKILL_DIR / "naca_four_digit_polar.png"
        ordinates_path = (
            Path(args.out_ordinates) if args.out_ordinates else SKILL_DIR / "naca_four_digit_ordinates.txt"
        )
        section_path = section_path.resolve()
        coeff_path = coeff_path.resolve()
        polar_path = polar_path.resolve()
        ordinates_path = ordinates_path.resolve()
        plot_section(section_path, digits, args.chord, draw)
        plot_coefficients(coeff_path, digits, polar, alpha_l0_deg, alpha_mark_deg)
        plot_polar(polar_path, digits, polar, alpha_mark_deg)
        write_ordinates(ordinates_path, table)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(
        digits,
        args.chord,
        args.alpha,
        polar,
        alpha_l0_deg,
        rle,
        table,
        section_path,
        coeff_path,
        polar_path,
        ordinates_path,
        re_table,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
