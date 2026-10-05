#!/usr/bin/env python3
"""Flat-plate spacecraft solar-array power (BOL, EOL, orbit average).

Ideal packed power is solar_array_ideal_power. Instantaneous BOL power is
solar_array_bol_power or solar_array_bol_power_from_specific. Life remaining
is solar_array_life_degradation. EOL is solar_array_eol_power. Orbit average
is solar_array_orbit_average_power with circular_orbit_eclipse_fraction when
orbit radius and beta are given. Cosine irradiance is
flat_plate_solar_irradiance.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Solar array output"
N_CURVE = 181
S_1AU = 1361.6
R0_EARTH = 6.378137e6
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "flat-plate solar array; cosine incidence only "
    "(flat_plate_solar_irradiance G = S*cos(theta); edge effects beyond "
    "about 40 deg from NASA SP-8074 are omitted); "
    "ideal packed power is solar_array_ideal_power P0 = S*A*eta*Fp; "
    "BOL power is solar_array_bol_power "
    "P_BOL = S*A*eta*Fp*Id*cos(theta), or "
    "solar_array_bol_power_from_specific when --specific-power replaces "
    "S*eta*Fp; "
    "life remaining is solar_array_life_degradation Ld = (1 - d)**L; "
    "EOL is solar_array_eol_power P_EOL = P_BOL*Ld; "
    "orbit average is solar_array_orbit_average_power "
    "P_avg = P*(1 - fe) with constant sunlit power and zero in eclipse; "
    "circular cylindrical-umbra eclipse fraction is "
    "circular_orbit_eclipse_fraction "
    "fe = acos(sqrt(1-(re/r)**2)/cos(beta))/pi when "
    "|beta| < asin(re/r), else fe = 0; "
    f"default 1 AU solar constant S = {S_1AU:g} W/m^2 (NASA GSFC / TSIS-1); "
    f"default planet radius R0 = {R0_EARTH:g} m (WGS 84 equatorial); "
    "no temperature, spectral, albedo, or penumbra model"
)


@dataclass(frozen=True)
class Solution:
    area: float
    solar_constant: float
    incidence: float
    packing: float
    inherent: float
    life_rate: float
    years: float
    life_factor: float
    power_source: str
    efficiency: float | None
    specific_power: float | None
    p0: float
    p_bol: float
    p_eol: float
    eclipse_fraction: float
    eclipse_source: str
    p_avg_bol: float
    p_avg_eol: float
    orbit_radius: float | None
    planet_radius: float | None
    beta: float | None
    irradiance: float


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def require_positive(name: str, value: float) -> None:
    require_finite(name, value)
    if value <= 0.0:
        raise ValueError(f"{name} must be > 0")


def require_unit_interval(name: str, value: float) -> None:
    require_finite(name, value)
    if value <= 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1]")


def cosine_factor(theta: float) -> float:
    """Non-negative cosine for a lit flat plate; dark when |theta| > pi/2."""
    require_finite("incidence angle", theta)
    factor = math.cos(theta)
    return factor if factor > 0.0 else 0.0


def flat_plate_solar_irradiance(solar_constant: float, theta: float) -> float:
    """flat_plate_solar_irradiance."""
    return solar_constant * cosine_factor(theta)


def solar_array_ideal_power(
    solar_constant: float, area: float, efficiency: float, packing: float
) -> float:
    """solar_array_ideal_power."""
    return solar_constant * area * efficiency * packing


def solar_array_bol_power(
    solar_constant: float,
    area: float,
    efficiency: float,
    packing: float,
    inherent: float,
    theta: float,
) -> float:
    """solar_array_bol_power."""
    return (
        solar_constant
        * area
        * efficiency
        * packing
        * inherent
        * cosine_factor(theta)
    )


def solar_array_bol_power_from_specific(
    specific_power: float, area: float, inherent: float, theta: float
) -> float:
    """solar_array_bol_power_from_specific."""
    return specific_power * area * inherent * cosine_factor(theta)


def solar_array_life_degradation(rate: float, years: float) -> float:
    """solar_array_life_degradation."""
    return (1.0 - rate) ** years


def solar_array_eol_power(bol_power: float, life_factor: float) -> float:
    """solar_array_eol_power."""
    return bol_power * life_factor


def solar_array_orbit_average_power(power: float, eclipse_fraction: float) -> float:
    """solar_array_orbit_average_power."""
    return power * (1.0 - eclipse_fraction)


def circular_orbit_eclipse_fraction(
    planet_radius: float, orbit_radius: float, beta: float
) -> float:
    """circular_orbit_eclipse_fraction when an eclipse exists; else 0."""
    require_positive("planet radius", planet_radius)
    require_positive("orbit radius", orbit_radius)
    require_finite("beta angle", beta)
    if orbit_radius <= planet_radius:
        raise ValueError("orbit radius must exceed the planet radius")
    ratio = planet_radius / orbit_radius
    beta_star = math.asin(ratio)
    if abs(beta) >= beta_star:
        return 0.0
    argument = math.sqrt(1.0 - ratio * ratio) / math.cos(beta)
    if argument > 1.0:
        argument = 1.0
    if argument < -1.0:
        argument = -1.0
    return math.acos(argument) / math.pi


def evaluate(
    area: float,
    solar_constant: float,
    theta: float,
    packing: float,
    inherent: float,
    life_rate: float,
    years: float,
    efficiency: float | None,
    specific_power: float | None,
    eclipse_fraction: float | None,
    orbit_radius: float | None,
    planet_radius: float | None,
    beta: float | None,
) -> Solution:
    require_positive("array area", area)
    require_positive("solar constant", solar_constant)
    require_unit_interval("packing factor", packing)
    require_unit_interval("inherent degradation", inherent)
    require_finite("life degradation rate", life_rate)
    if life_rate < 0.0 or life_rate >= 1.0:
        raise ValueError("life degradation rate must be in [0, 1)")
    require_finite("mission years", years)
    if years < 0.0:
        raise ValueError("mission years must be >= 0")

    if efficiency is not None and specific_power is not None:
        raise ValueError("pass --efficiency or --specific-power, not both")
    if efficiency is None and specific_power is None:
        raise ValueError("requires --efficiency or --specific-power")

    if efficiency is not None:
        require_unit_interval("cell efficiency", efficiency)
        power_source = "efficiency"
        p0 = solar_array_ideal_power(solar_constant, area, efficiency, packing)
        p_bol = solar_array_bol_power(
            solar_constant, area, efficiency, packing, inherent, theta
        )
        psa = None
    else:
        assert specific_power is not None
        require_positive("specific power", specific_power)
        if abs(packing - 1.0) > CHECK_TOL:
            raise ValueError(
                "--packing applies only with --efficiency; "
                "--specific-power already includes packing"
            )
        power_source = "specific_power"
        p0 = specific_power * area
        p_bol = solar_array_bol_power_from_specific(
            specific_power, area, inherent, theta
        )
        psa = specific_power
        efficiency = None

    life_factor = solar_array_life_degradation(life_rate, years)
    p_eol = solar_array_eol_power(p_bol, life_factor)

    if eclipse_fraction is not None and (
        orbit_radius is not None or beta is not None
    ):
        raise ValueError(
            "pass --eclipse-fraction, or orbit radius with --beta, not both"
        )

    if eclipse_fraction is not None:
        require_finite("eclipse fraction", eclipse_fraction)
        if eclipse_fraction < 0.0 or eclipse_fraction >= 1.0:
            raise ValueError("eclipse fraction must be in [0, 1)")
        fe = eclipse_fraction
        eclipse_source = "input"
        used_r = None
        used_re = None
        used_beta = None
    elif orbit_radius is not None or beta is not None:
        if orbit_radius is None or beta is None:
            raise ValueError("orbit eclipse path requires orbit radius and --beta")
        re = planet_radius if planet_radius is not None else R0_EARTH
        fe = circular_orbit_eclipse_fraction(re, orbit_radius, beta)
        eclipse_source = "orbit"
        used_r = orbit_radius
        used_re = re
        used_beta = beta
    else:
        fe = 0.0
        eclipse_source = "none"
        used_r = None
        used_re = None
        used_beta = None

    return Solution(
        area=area,
        solar_constant=solar_constant,
        incidence=theta,
        packing=packing,
        inherent=inherent,
        life_rate=life_rate,
        years=years,
        life_factor=life_factor,
        power_source=power_source,
        efficiency=efficiency,
        specific_power=psa,
        p0=p0,
        p_bol=p_bol,
        p_eol=p_eol,
        eclipse_fraction=fe,
        eclipse_source=eclipse_source,
        p_avg_bol=solar_array_orbit_average_power(p_bol, fe),
        p_avg_eol=solar_array_orbit_average_power(p_eol, fe),
        orbit_radius=used_r,
        planet_radius=used_re,
        beta=used_beta,
        irradiance=flat_plate_solar_irradiance(solar_constant, theta),
    )


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
        raise ValueError("matplotlib is required to plot solar array output") from exc
    return plt


def write_plot(result: Solution, out_path: Path) -> None:
    plt = ensure_matplotlib()
    angles = linspace(0.0, 0.5 * math.pi, N_CURVE)
    if result.power_source == "efficiency":
        assert result.efficiency is not None
        bol = [
            solar_array_bol_power(
                result.solar_constant,
                result.area,
                result.efficiency,
                result.packing,
                result.inherent,
                angle,
            )
            for angle in angles
        ]
    else:
        assert result.specific_power is not None
        bol = [
            solar_array_bol_power_from_specific(
                result.specific_power,
                result.area,
                result.inherent,
                angle,
            )
            for angle in angles
        ]
    eol = [solar_array_eol_power(power, result.life_factor) for power in bol]
    deg = [math.degrees(angle) for angle in angles]

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(deg, bol, color="#1a5276", linewidth=1.8, label=r"$P_{\mathrm{BOL}}$")
    ax.plot(deg, eol, color="#922b21", linewidth=1.6, linestyle="--", label=r"$P_{\mathrm{EOL}}$")
    ax.plot(
        math.degrees(result.incidence),
        result.p_bol,
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="Beginning-of-life operating point",
    )
    ax.plot(
        math.degrees(result.incidence),
        result.p_eol,
        "o",
        color="#922b21",
        markersize=6,
        zorder=5,
        label="End-of-life operating point",
    )
    ax.set_xlabel("sun incidence angle (deg)")
    ax.set_ylabel("array power (W)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(0.0, 90.0)
    ax.set_ylim(bottom=0.0)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: Solution, graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("power_source", result.power_source)
    print_kv("A_m2", result.area)
    print_kv("S_W_m2", result.solar_constant)
    print_kv("theta_rad", result.incidence)
    print_kv("theta_deg", math.degrees(result.incidence))
    print_kv("G_W_m2", result.irradiance)
    print_kv("Fp", result.packing)
    print_kv("Id", result.inherent)
    if result.efficiency is not None:
        print_kv("eta", result.efficiency)
    if result.specific_power is not None:
        print_kv("psa_W_m2", result.specific_power)
    print_kv("P0_W", result.p0)
    print_kv("P_BOL_W", result.p_bol)
    print_kv("d_per_year", result.life_rate)
    print_kv("L_year", result.years)
    print_kv("Ld", result.life_factor)
    print_kv("P_EOL_W", result.p_eol)
    print_kv("eclipse_source", result.eclipse_source)
    print_kv("fe", result.eclipse_fraction)
    if result.orbit_radius is not None:
        print_kv("r_m", result.orbit_radius)
        print_kv("re_m", result.planet_radius)
        print_kv("beta_rad", result.beta)
        print_kv("beta_deg", math.degrees(float(result.beta)))
    print_kv("P_avg_BOL_W", result.p_avg_bol)
    print_kv("P_avg_EOL_W", result.p_avg_eol)
    if result.eclipse_source == "none":
        print_kv(
            "warning",
            "eclipse fraction was not supplied; orbit-average power equals "
            "instantaneous sunlit power (fe = 0)",
        )
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def capture(argv: list[str]) -> tuple[int, str, str]:
    from io import StringIO

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def run_check() -> int:
    if not close(flat_plate_solar_irradiance(1000.0, math.pi / 3.0), 500.0):
        return fail("cosine irradiance at 60 deg")
    if not close(solar_array_ideal_power(1000.0, 2.0, 0.5, 0.8), 800.0):
        return fail("ideal packed power")
    if not close(
        solar_array_bol_power(1000.0, 1.0, 1.0, 1.0, 1.0, math.pi / 3.0), 500.0
    ):
        return fail("BOL cosine power")
    if not close(solar_array_life_degradation(0.0, 10.0), 1.0):
        return fail("zero degradation life factor")
    if not close(solar_array_life_degradation(0.005, 5.0), 0.995**5):
        return fail("compound life degradation")
    if not close(solar_array_eol_power(1000.0, 0.9), 900.0):
        return fail("EOL power")
    if not close(solar_array_orbit_average_power(100.0, 0.35), 65.0):
        return fail("orbit-average power")

    # Unit geometry: re=3, r=5, beta=0 => fe = acos(0.8)/pi
    fe = circular_orbit_eclipse_fraction(3.0, 5.0, 0.0)
    if not close(fe, math.acos(0.8) / math.pi):
        return fail("eclipse fraction unit case")
    if not close(circular_orbit_eclipse_fraction(3.0, 5.0, math.asin(3.0 / 5.0)), 0.0):
        return fail("critical beta did not clear eclipse")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "solar.png"
        code, text, err = capture(
            [
                "--area",
                "1",
                "--efficiency",
                "0.3",
                "--incidence",
                "0",
                "--packing",
                "0.85",
                "--inherent",
                "0.9",
                "--life-degradation",
                "0.005",
                "--years",
                "5",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"efficiency run failed: {err}")
        if "P_BOL_W:" not in text or "P_EOL_W:" not in text:
            return fail("efficiency run omitted BOL/EOL")
        if "P_avg_EOL_W:" not in text:
            return fail("efficiency run omitted orbit-average EOL")
        if "eclipse_source: none" not in text:
            return fail("default eclipse source was not none")
        if "graph:" not in text:
            return fail("efficiency run with --out omitted graph")
        if not png.is_file() or not png.read_bytes().startswith(b"\x89PNG"):
            return fail("efficiency run did not write a PNG")

        code, text, err = capture(
            [
                "--area",
                "2",
                "--specific-power",
                "300",
                "--incidence",
                str(math.pi / 3.0),
                "--inherent",
                "1",
                "--eclipse-fraction",
                "0.35",
            ]
        )
        if code != 0:
            return fail(f"specific-power run failed: {err}")
        if "power_source: specific_power" not in text:
            return fail("specific-power path not marked")
        if "fe: 0.35" not in text:
            return fail("eclipse fraction input not printed")
        # 300*2*1*0.5*(1-0.35) = 195
        if "P_avg_BOL_W: 195" not in text:
            return fail("specific-power orbit average was not 195")
        if "graph:" in text:
            return fail("run without --out still printed graph")

        code, text, err = capture(
            [
                "--area",
                "1",
                "--efficiency",
                "0.28",
                "--incidence",
                "0",
                "--a",
                str(R0_EARTH + 400000.0),
                "--beta",
                "0",
            ]
        )
        if code != 0:
            return fail(f"orbit eclipse run failed: {err}")
        if "eclipse_source: orbit" not in text:
            return fail("orbit path did not mark eclipse_source")
        if "fe:" not in text:
            return fail("orbit path omitted fe")

        code, _text, err = capture(
            ["--area", "1", "--efficiency", "0.3", "--specific-power", "300", "--incidence", "0"]
        )
        if code == 0:
            return fail("accepted both efficiency and specific power")

        code, _text, err = capture(
            [
                "--area",
                "1",
                "--efficiency",
                "0.3",
                "--incidence",
                "0",
                "--eclipse-fraction",
                "0.2",
                "--a",
                "7000000",
                "--beta",
                "0",
            ]
        )
        if code == 0:
            return fail("accepted eclipse fraction with orbit inputs")

    print("check: pass")
    print_kv("unit_fe", fe)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flat-plate solar-array instantaneous BOL/EOL power and "
            "orbit-average power, with optional cosine-law PNG."
        )
    )
    parser.add_argument("--area", type=float, default=None, help="array substrate area A [m^2]")
    parser.add_argument(
        "--efficiency",
        type=float,
        default=None,
        help="cell conversion efficiency eta (0, 1]",
    )
    parser.add_argument(
        "--specific-power",
        type=float,
        default=None,
        help="BOL specific power before inherent degradation [W/m^2]",
    )
    parser.add_argument(
        "--solar-constant",
        type=float,
        default=S_1AU,
        help=f"solar irradiance at the orbit, normal to the Sun [W/m^2]; default {S_1AU:g}",
    )
    parser.add_argument(
        "--incidence",
        type=float,
        default=None,
        help="sun incidence angle from the plate normal [rad]",
    )
    parser.add_argument(
        "--packing",
        type=float,
        default=1.0,
        help="packing factor Fp in (0, 1]; default 1",
    )
    parser.add_argument(
        "--inherent",
        type=float,
        default=1.0,
        help="inherent degradation Id in (0, 1]; default 1",
    )
    parser.add_argument(
        "--life-degradation",
        type=float,
        default=0.0,
        help="fractional degradation per year d in [0, 1); default 0",
    )
    parser.add_argument(
        "--years",
        type=float,
        default=0.0,
        help="mission life L [year]; default 0",
    )
    parser.add_argument(
        "--eclipse-fraction",
        type=float,
        default=None,
        help="eclipse time fraction fe in [0, 1)",
    )
    parser.add_argument(
        "--a",
        type=float,
        default=None,
        help="circular-orbit radius from planet center [m] (from OrbitalParameters)",
    )
    parser.add_argument(
        "--alt",
        type=float,
        default=None,
        help="circular-orbit geometric altitude [m]; orbit radius is R0 + alt",
    )
    parser.add_argument(
        "--R0",
        type=float,
        default=None,
        help=f"planet radius [m]; default Earth WGS 84 {R0_EARTH:g}",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=None,
        help="orbit beta angle [rad] for cylindrical-umbra eclipse fraction",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional PNG path for power versus sun incidence angle",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def resolve_orbit_radius(args: argparse.Namespace) -> float | None:
    if args.a is not None and args.alt is not None:
        raise ValueError("pass --a or --alt, not both")
    if args.a is not None:
        require_positive("--a", args.a)
        return float(args.a)
    if args.alt is not None:
        require_finite("--alt", args.alt)
        if args.alt < 0.0:
            raise ValueError("--alt must be >= 0")
        re = float(args.R0) if args.R0 is not None else R0_EARTH
        require_positive("planet radius", re)
        return re + float(args.alt)
    return None


def run(args: argparse.Namespace) -> int:
    if args.area is None:
        raise ValueError("--area is required")
    if args.incidence is None:
        raise ValueError("--incidence is required")
    orbit_radius = resolve_orbit_radius(args)
    planet_radius = float(args.R0) if args.R0 is not None else None
    if planet_radius is not None:
        require_positive("--R0", planet_radius)
    result = evaluate(
        area=float(args.area),
        solar_constant=float(args.solar_constant),
        theta=float(args.incidence),
        packing=float(args.packing),
        inherent=float(args.inherent),
        life_rate=float(args.life_degradation),
        years=float(args.years),
        efficiency=args.efficiency,
        specific_power=args.specific_power,
        eclipse_fraction=args.eclipse_fraction,
        orbit_radius=orbit_radius,
        planet_radius=planet_radius,
        beta=args.beta,
    )
    path: Path | None = None
    if args.out is not None:
        path = Path(args.out).resolve()
        write_plot(result, path)
    emit(result, path)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        return run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
