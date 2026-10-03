#!/usr/bin/env python3
"""Optimal nozzle expansion ratio on the 1976 U.S. Standard Atmosphere.

Exit pressure is matched to ambient pressure at geometric altitude.
Me, epsilon, pe, and ideal CF come from the Area-Mach program.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

# 1976 U.S. Standard Atmosphere constants (formulas.md, Atmosphere).
G0 = 9.80665
P0 = 101325.0
R0 = 6.356766e6
M0 = 28.9644
RSTAR = 8.31432e3
H_MAX = 84852.0
Z_MAX = 86000.0
DEFAULT_GAMMA = 1.4
N_SAMPLES = 201
PLOT_TITLE = "Optimal expansion ratio versus altitude"

# Geopotential bases in metres, lapse in K/m, base molecular-scale temperature in K.
# Layer b runs from Hb[b] to the next base. The last layer ends at H_MAX.
LAYERS = (
    (0.0, -6.5e-3, 288.15),
    (11000.0, 0.0, 216.65),
    (20000.0, 1.0e-3, 216.65),
    (32000.0, 2.8e-3, 228.65),
    (47000.0, 0.0, 270.65),
    (51000.0, -2.8e-3, 270.65),
    (71000.0, -2.0e-3, 214.65),
)

ASSUMPTIONS = (
    "optimal expansion sets nozzle exit pressure equal to ambient pressure, "
    "where thrust_coefficient_ideal is maximum at a fixed chamber-to-ambient "
    "pressure ratio; ambient pressure is the 1976 U.S. Standard Atmosphere "
    "hydrostatic pressure at geometric altitude Z from 0 to 86000 m, using "
    "geopotential altitude H = r0*Z/(r0+Z) with r0 = 6356766 m and the seven "
    "constant-lapse layers through H = 84852 m; calorically perfect gas; "
    "steady one-dimensional isentropic nozzle; Me is the inverse of exit "
    "pressure (stagnation_pressure with chamber pressure as stagnation "
    "pressure); epsilon is area_mach at that Me; a choked throat (Me >= 1) "
    "has epsilon = Ae/At and ideal CF from thrust_coefficient_ideal; an "
    "unchoked exit (Me < 1) reports the sonic area ratio A/A* and omits "
    "ideal CF; the expansion flag is an ideal pressure comparison and does "
    "not model separation"
)

SKILL_DIR = Path(__file__).resolve().parent
AREA_MACH_DIR = SKILL_DIR.parent / "ROCKET - Area-Mach Graph"
_NOZZLE = None


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def nozzle():
    """Area-Mach identities. Matplotlib is set to a file backend before import."""
    global _NOZZLE
    if _NOZZLE is None:
        try:
            import matplotlib

            if "matplotlib.pyplot" not in sys.modules:
                matplotlib.use("Agg")
            folder = str(AREA_MACH_DIR)
            if folder not in sys.path:
                sys.path.insert(0, folder)
            from area_mach import (
                area_ratio,
                exit_pressure,
                expansion_flag,
                thrust_coefficient_ideal,
            )
        except ImportError as exc:
            raise ValueError(
                "numpy and matplotlib are required, and "
                "ROCKET - Area-Mach Graph must be importable"
            ) from exc
        _NOZZLE = (area_ratio, exit_pressure, expansion_flag, thrust_coefficient_ideal)
    return _NOZZLE


def build_base_pressures() -> tuple[float, ...]:
    """Pressure at each layer base, starting from p0 and the layer integrals."""
    bases = [P0]
    pressure = P0
    for i, (hb, lapse, temp) in enumerate(LAYERS[:-1]):
        h_top = LAYERS[i + 1][0]
        t_top = temp + lapse * (h_top - hb)
        if lapse == 0.0:
            pressure = pressure * math.exp(-G0 * M0 * (h_top - hb) / (RSTAR * temp))
        else:
            pressure = pressure * (temp / t_top) ** (G0 * M0 / (RSTAR * lapse))
        bases.append(pressure)
    return tuple(bases)


BASE_P = build_base_pressures()


def require_altitude(value: float, flag: str) -> float:
    if not math.isfinite(value) or value < 0.0 or value > Z_MAX:
        raise ValueError(
            f"{flag} must be from 0 to 86000 m geometric; "
            "the 1976 hydrostatic model ends at 86 km"
        )
    return value


def geopotential_altitude(z_m: float) -> float:
    """H = r0*Z/(r0+Z). H is limited to the hydrostatic top at 84852 m."""
    h_m = R0 * z_m / (R0 + z_m)
    if h_m > H_MAX:
        return H_MAX
    return h_m


def layer_index(h_m: float) -> int:
    for index in range(len(LAYERS) - 1, -1, -1):
        if h_m >= LAYERS[index][0]:
            return index
    return 0


def atmosphere(z_m: float) -> dict:
    """1976 hydrostatic pressure below 86 km geometric."""
    h_m = geopotential_altitude(z_m)
    index = layer_index(h_m)
    hb, lapse, temp_b = LAYERS[index]
    pressure_b = BASE_P[index]
    temp = temp_b if lapse == 0.0 else temp_b + lapse * (h_m - hb)
    if temp <= 0.0:
        raise ValueError("molecular-scale temperature is not positive")
    if lapse == 0.0:
        pressure = pressure_b * math.exp(-G0 * M0 * (h_m - hb) / (RSTAR * temp_b))
    else:
        pressure = pressure_b * (temp_b / temp) ** (G0 * M0 / (RSTAR * lapse))
    if not math.isfinite(pressure) or pressure <= 0.0:
        raise ValueError("ambient pressure is not positive")
    return {
        "Z": z_m,
        "H": h_m,
        "TM": temp,
        "layer_Hb": hb,
        "pa": pressure,
    }


def sonic_pressure_ratio(gamma: float) -> float:
    """p*/pc for a choked throat. Me = 1 when pe/pc equals this ratio."""
    return (2.0 / (gamma + 1.0)) ** (gamma / (gamma - 1.0))


def mach_from_pressure(pc: float, pe: float, gamma: float) -> float:
    """Inverse of exit_pressure: stagnation_pressure solved for Mach."""
    if pe <= 0.0 or pc <= 0.0:
        raise ValueError("pressures must be positive")
    if pe >= pc:
        raise ValueError("ambient pressure must be below chamber pressure")
    exponent = (gamma - 1.0) / gamma
    me_sq = (2.0 / (gamma - 1.0)) * ((pc / pe) ** exponent - 1.0)
    if me_sq <= 0.0 or not math.isfinite(me_sq):
        raise ValueError("pressure ratio does not give a real Mach number")
    return math.sqrt(me_sq)


def match_nozzle(pc: float, gamma: float, z_m: float) -> dict:
    """Perfectly expanded nozzle at geometric altitude z_m."""
    area_ratio, exit_pressure, expansion_flag, thrust_coefficient_ideal = nozzle()
    air = atmosphere(z_m)
    pa = air["pa"]
    if not pa < pc:
        raise ValueError(
            f"chamber pressure must be above ambient pressure at {z_m:.8g} m "
            f"(pa = {pa:.8g} Pa)"
        )
    me = mach_from_pressure(pc, pa, gamma)
    epsilon = area_ratio(me, gamma)
    pe = exit_pressure(pc, me, gamma)
    if not math.isfinite(epsilon) or epsilon < 1.0:
        raise ValueError("area ratio is not finite")
    if abs(me - 1.0) <= 1e-8:
        branch = "sonic"
    elif me > 1.0:
        branch = "supersonic"
    else:
        branch = "subsonic"
    choked = me >= 1.0 - 1e-8
    state = {
        "Z": z_m,
        "H": air["H"],
        "TM": air["TM"],
        "layer_Hb": air["layer_Hb"],
        "pa": pa,
        "pe": pe,
        "Me": me,
        "epsilon": epsilon,
        "branch": branch,
        "choked": choked,
        "expansion": expansion_flag(pe, pa),
        "pc": pc,
        "gamma": gamma,
    }
    if choked:
        state["CF"] = thrust_coefficient_ideal(gamma, pe, pc, pa, epsilon, 1.0)
    return state


def annotate(state: dict, throat: float | None) -> dict:
    """Add exit area and thrust when the throat is choked."""
    out = dict(state)
    if throat is not None and state["choked"]:
        out["Ae"] = state["epsilon"] * throat
        out["thrust"] = state["CF"] * state["pc"] * throat
    return out


def linspace(lo: float, hi: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("need at least 2 altitude samples")
    step = (hi - lo) / (count - 1)
    values = [lo + step * i for i in range(count)]
    values[-1] = hi
    return values


def sample_altitudes(z_min: float, z_max: float) -> list[float]:
    """Uniform samples plus the geometric altitude of each layer boundary in range."""
    extra = []
    for hb, _lapse, _temp in LAYERS:
        z_b = R0 * hb / (R0 - hb) if hb > 0.0 else 0.0
        if z_min <= z_b <= z_max:
            extra.append(z_b)
    if z_min <= Z_MAX <= z_max:
        extra.append(Z_MAX)
    values = linspace(z_min, z_max, N_SAMPLES) + extra
    values.sort()
    out: list[float] = []
    for value in values:
        if not out or abs(value - out[-1]) > 1e-6:
            out.append(value)
    return out


def altitude_for_pressure(target: float, z_lo: float, z_hi: float) -> float:
    """Geometric altitude where ambient pressure equals target. Pressure falls with Z."""
    if atmosphere(z_lo)["pa"] < target or atmosphere(z_hi)["pa"] > target:
        raise ValueError("pressure is outside the altitude bracket")
    lo = z_lo
    hi = z_hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if atmosphere(mid)["pa"] > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sonic_altitude(pc: float, gamma: float, z_min: float, z_max: float) -> float | None:
    """Altitude in the sweep where the matched exit is exactly sonic, if any."""
    p_sonic = pc * sonic_pressure_ratio(gamma)
    pa_lo = atmosphere(z_min)["pa"]
    pa_hi = atmosphere(z_max)["pa"]
    if math.isclose(pa_lo, p_sonic, rel_tol=1e-10, abs_tol=0.0):
        return z_min
    if math.isclose(pa_hi, p_sonic, rel_tol=1e-10, abs_tol=0.0):
        return z_max
    if pa_hi < p_sonic < pa_lo:
        return altitude_for_pressure(p_sonic, z_min, z_max)
    return None


def print_header(mode: str, gamma: float | None, gamma_source: str | None, pc: float | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", mode)
    print_kv("model", "U.S. Standard Atmosphere, 1976")
    if gamma is not None:
        print_kv("gamma", gamma)
    if gamma_source is not None:
        print_kv("gamma_source", gamma_source)
    if pc is not None:
        print_kv("pc_Pa", pc)
    print_kv("g0_m_s2", G0)
    print_kv("p0_Pa", P0)
    print_kv("r0_m", R0)
    print_kv("Z_limit_m", Z_MAX)
    print_kv("H_limit_m", H_MAX)


def emit_match(prefix: str, state: dict) -> None:
    rows: list[tuple[str, object]] = [
        ("Z_m", state["Z"]),
        ("H_m", state["H"]),
        ("TM_K", state["TM"]),
        ("layer_Hb_m", state["layer_Hb"]),
        ("pa_Pa", state["pa"]),
        ("pe_Pa", state["pe"]),
        ("Me", state["Me"]),
        ("epsilon", state["epsilon"]),
        ("branch", state["branch"]),
        ("choked", "yes" if state["choked"] else "no"),
        ("expansion", state["expansion"]),
    ]
    if state["choked"]:
        rows.append(("CF", state["CF"]))
    if "thrust" in state:
        rows.append(("Ae_m2", state["Ae"]))
        rows.append(("thrust_N", state["thrust"]))
    for key, value in rows:
        print_kv(prefix + key, value)


def emit_end(tag: str, state: dict) -> None:
    """tag is Z_min or Z_max. Names stay epsilon_at_Z_min, not a curve minimum."""
    print_kv(f"{tag}_m", state["Z"])
    print_kv(f"H_at_{tag}_m", state["H"])
    print_kv(f"pa_at_{tag}_Pa", state["pa"])
    print_kv(f"pe_at_{tag}_Pa", state["pe"])
    print_kv(f"Me_at_{tag}", state["Me"])
    print_kv(f"epsilon_at_{tag}", state["epsilon"])
    print_kv(f"branch_at_{tag}", state["branch"])
    print_kv(f"choked_at_{tag}", "yes" if state["choked"] else "no")
    print_kv(f"expansion_at_{tag}", state["expansion"])
    if state["choked"]:
        print_kv(f"CF_at_{tag}", state["CF"])
        if "thrust" in state:
            print_kv(f"Ae_at_{tag}_m2", state["Ae"])
            print_kv(f"thrust_at_{tag}_N", state["thrust"])


def ensure_matplotlib():
    nozzle()
    import matplotlib.pyplot as plt

    return plt


def plot_curve(
    path: Path,
    altitudes: list[float],
    epsilons: list[float],
    *,
    mark: dict | None,
    sonic_z: float | None,
) -> str:
    plt = ensure_matplotlib()
    lo = min(epsilons)
    hi = max(epsilons)
    scale = "log" if hi / lo >= 10.0 else "linear"
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        altitudes,
        epsilons,
        color="#1a5276",
        linewidth=1.8,
        label="optimal expansion ratio",
    )
    if sonic_z is not None:
        ax.axvline(
            sonic_z,
            color="#7f8c8d",
            linestyle="--",
            linewidth=1.0,
            label="sonic exit",
        )
    if mark is not None:
        ax.plot(
            mark["Z"],
            mark["epsilon"],
            "s",
            color="#27ae60",
            markersize=7,
            zorder=5,
            label=f"match ({mark['Z']:.6g} m, {mark['epsilon']:.6g})",
        )
    ax.set_xlabel("geometric altitude $Z$ (m)")
    ax.set_ylabel(r"optimal area ratio $\epsilon$")
    ax.set_title(PLOT_TITLE)
    ax.set_xlim(altitudes[0], altitudes[-1])
    if scale == "log":
        ax.set_yscale("log")
        ax.set_ylim(lo / 1.15, hi * 1.15)
    else:
        pad = (hi - lo) * 0.08
        if pad == 0.0:
            pad = hi * 0.05 if hi > 0.0 else 1.0
        ax.set_ylim(max(0.0, lo - pad), hi + pad)
    ax.grid(True, alpha=0.35, which="both")
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return scale


def choke_warning(states: list[dict]) -> str | None:
    choked = [state["choked"] for state in states]
    if all(choked):
        return None
    if not any(choked):
        return (
            "the altitude range is unchoked (Me < 1); epsilon is the sonic "
            "area ratio A/A* and ideal CF is omitted"
        )
    return (
        "part of the altitude range is unchoked (Me < 1); epsilon there is "
        "the sonic area ratio A/A* and ideal CF is omitted"
    )


def resolve_gamma(ns: argparse.Namespace) -> tuple[float, str]:
    if ns.gamma is None:
        return DEFAULT_GAMMA, "default"
    if not math.isfinite(ns.gamma) or ns.gamma <= 1.0:
        raise ValueError("--gamma must be > 1")
    return ns.gamma, "input"


def require_pc(pc: float | None) -> float:
    if pc is None or not math.isfinite(pc) or pc <= 0.0:
        raise ValueError("--pc must be > 0 Pa")
    return pc


def optional_positive(value: float | None, flag: str) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{flag} must be > 0")
    return value


def run_point(ns: argparse.Namespace, gamma: float, gamma_source: str) -> int:
    if ns.out is not None:
        raise ValueError("--out applies only to an altitude sweep")
    pc = require_pc(ns.pc)
    alt = require_altitude(ns.alt, "--alt")
    throat = optional_positive(ns.throat, "--throat")
    state = annotate(match_nozzle(pc, gamma, alt), throat)
    print_header("point", gamma, gamma_source, pc)
    if throat is not None:
        print_kv("throat_m2", throat)
    emit_match("", state)
    if not state["choked"]:
        print_kv(
            "warning",
            "unchoked exit (Me < 1); epsilon is the sonic area ratio A/A* "
            "and ideal CF is omitted",
        )
    return 0


def run_sweep(ns: argparse.Namespace, gamma: float, gamma_source: str) -> int:
    pc = require_pc(ns.pc)
    assumed: list[str] = []
    if ns.alt_min is None:
        z_min = 0.0
        assumed.append("low end is sea level")
    else:
        z_min = require_altitude(ns.alt_min, "--alt-min")
    if ns.alt_max is None:
        z_max = Z_MAX
        assumed.append("high end is the 1976 hydrostatic limit at 86 km")
    else:
        z_max = require_altitude(ns.alt_max, "--alt-max")
    if z_min >= z_max:
        raise ValueError("--alt-min must be < --alt-max")
    mark_z = None
    if ns.alt is not None:
        mark_z = require_altitude(ns.alt, "--alt")
        if mark_z < z_min or mark_z > z_max:
            raise ValueError("--alt must lie inside the altitude sweep")
    throat = optional_positive(ns.throat, "--throat")
    samples = sample_altitudes(z_min, z_max)
    states = [annotate(match_nozzle(pc, gamma, z), throat) for z in samples]
    sonic_z = sonic_altitude(pc, gamma, z_min, z_max)
    script_dir = Path(__file__).resolve().parent
    out_path = Path(ns.out) if ns.out else script_dir / "optimal_expansion_ratio.png"
    out_path = out_path.resolve()
    mark_state = None
    if mark_z is not None:
        mark_state = annotate(match_nozzle(pc, gamma, mark_z), throat)
    scale = plot_curve(
        out_path,
        [state["Z"] for state in states],
        [state["epsilon"] for state in states],
        mark=mark_state,
        sonic_z=sonic_z,
    )
    print_header("sweep", gamma, gamma_source, pc)
    if throat is not None:
        print_kv("throat_m2", throat)
    emit_end("Z_min", states[0])
    emit_end("Z_max", states[-1])
    if mark_state is not None:
        emit_match("mark_", mark_state)
    if sonic_z is not None:
        print_kv("sonic_Z_m", sonic_z)
    print_kv("y_scale", scale)
    if assumed:
        print_kv(
            "assumed_range",
            f"geometric altitude {z_min:.8g} to {z_max:.8g} m; " + "; ".join(assumed),
        )
    warning = choke_warning(states)
    if warning:
        print_kv("warning", warning)
    print_kv("graph", str(out_path))
    return 0


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    if abs(atmosphere(0.0)["pa"] - P0) > 1e-9:
        return fail("sea-level pressure")
    if abs(atmosphere(0.0)["H"]) > 1e-12:
        return fail("sea-level geopotential")
    if abs(atmosphere(0.0)["TM"] - 288.15) > 1e-9:
        return fail("sea-level temperature")

    published = (
        (11000.0, 22632.06),
        (20000.0, 5474.889),
        (32000.0, 868.019),
        (47000.0, 110.906),
        (51000.0, 66.9389),
        (71000.0, 3.95642),
        (84852.0, 0.373384),
    )
    for h_m, expected in published:
        z_m = 0.0 if h_m == 0.0 else R0 * h_m / (R0 - h_m)
        got = atmosphere(z_m)["pa"]
        if abs(got - expected) / expected > 5e-6:
            return fail(f"pressure at H={h_m} is {got}, expected about {expected}")

    top = atmosphere(Z_MAX)
    if abs(top["H"] - H_MAX) > 1e-6:
        return fail(f"86 km geopotential clamped to {top['H']}")
    if abs(top["TM"] - 186.946) > 1e-6:
        return fail(f"temperature at 86 km is {top['TM']}")

    area_ratio, exit_pressure, expansion_flag, thrust_coefficient_ideal = nozzle()
    gamma = 1.4
    pc = 1.0e6
    me = 2.0
    pe = exit_pressure(pc, me, gamma)
    me_back = mach_from_pressure(pc, pe, gamma)
    if abs(me_back - 2.0) > 1e-10:
        return fail(f"Mach inverse returned {me_back}")
    if abs(area_ratio(me_back, gamma) - 1.6875) > 1e-6:
        return fail("area ratio at Mach 2")
    if expansion_flag(pe, pe) != "perfectly expanded":
        return fail("equal pressures were not perfectly expanded")

    sea = match_nozzle(2.0e6, 1.25, 0.0)
    if sea["branch"] != "supersonic" or not sea["choked"]:
        return fail("20 bar, gamma 1.25 should choke at sea level")
    if sea["expansion"] != "perfectly expanded":
        return fail(f"sea-level expansion flag is {sea['expansion']}")
    if abs(sea["pe"] - sea["pa"]) / sea["pa"] > 1e-8:
        return fail("exit pressure did not match sea-level ambient")
    if abs(sea["Me"] - 2.5546470501439704) > 1e-8:
        return fail(f"sea-level Me = {sea['Me']}")
    if abs(sea["epsilon"] - 3.3749301391586863) > 1e-8:
        return fail(f"sea-level epsilon = {sea['epsilon']}")
    k = 1.25
    momentum = math.sqrt(
        (2.0 * k**2 / (k - 1.0))
        * ((2.0 / (k + 1.0)) ** ((k + 1.0) / (k - 1.0)))
        * (1.0 - (sea["pa"] / 2.0e6) ** ((k - 1.0) / k))
    )
    if abs(sea["CF"] - momentum) > 1e-6:
        return fail("matched CF is not the momentum term at pe = pa")
    if abs(sea["CF"] - thrust_coefficient_ideal(k, sea["pe"], 2.0e6, sea["pa"], sea["epsilon"], 1.0)) > 1e-12:
        return fail("CF did not match thrust_coefficient_ideal")

    higher = match_nozzle(2.0e6, 1.25, 20000.0)
    if not higher["epsilon"] > sea["epsilon"]:
        return fail("epsilon did not rise from sea level to 20 km")

    soft = match_nozzle(1.5 * P0, 1.4, 0.0)
    if soft["choked"]:
        return fail("pc = 1.5 atm should be unchoked at sea level")
    if "CF" in soft:
        return fail("unchoked match stored CF")

    try:
        require_altitude(Z_MAX + 1.0, "--alt")
    except ValueError:
        pass
    else:
        return fail("altitude above 86 km was accepted")

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "curve.png")
        old_out = sys.stdout
        sys.stdout = tempfile.TemporaryFile(mode="w+")
        try:
            code = main(
                [
                    "--pc",
                    "2e6",
                    "--gamma",
                    "1.25",
                    "--alt-min",
                    "0",
                    "--alt-max",
                    "10000",
                    "--alt",
                    "1000",
                    "--out",
                    out,
                ]
            )
        finally:
            sys.stdout.close()
            sys.stdout = old_out
        if code != 0:
            return fail(f"sweep main returned {code}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("sweep did not write a PNG")

    sink = sys.stderr
    sys.stderr = tempfile.TemporaryFile(mode="w+")
    try:
        missing = main(["--alt", "0"])
    finally:
        sys.stderr.close()
        sys.stderr = sink
    if missing != 2:
        return fail("missing chamber pressure was accepted")

    point_out = []

    class _Capture:
        def write(self, text: str) -> None:
            point_out.append(text)

        def flush(self) -> None:
            return None

    old_out = sys.stdout
    sys.stdout = _Capture()
    try:
        point_code = main(["--pc", "2e6", "--alt", "0"])
    finally:
        sys.stdout = old_out
    if point_code != 0:
        return fail("default-gamma point failed")
    text = "".join(point_out)
    if "gamma_source: default" not in text or "gamma: 1.4" not in text:
        return fail("default gamma was not reported")
    if "mode: point" not in text:
        return fail("point mode was not reported")

    print("check: pass")
    print_kv("sea_level_epsilon", sea["epsilon"])
    print_kv("sea_level_Me", sea["Me"])
    print_kv("sea_level_CF", sea["CF"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optimal expansion ratio versus geometric altitude."
    )
    parser.add_argument("--pc", type=float, default=None, help="chamber pressure p1 [Pa]")
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help=f"ratio of specific heats (default {DEFAULT_GAMMA})",
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--alt-min", type=float, default=None, help="sweep minimum geometric altitude [m]")
    parser.add_argument("--alt-max", type=float, default=None, help="sweep maximum geometric altitude [m]")
    parser.add_argument("--throat", type=float, default=None, help="throat area At [m^2]")
    parser.add_argument("--out", type=str, default=None, help="PNG path for the altitude sweep")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        gamma, source = resolve_gamma(args)
        if args.alt is not None and args.alt_min is None and args.alt_max is None:
            return run_point(args, gamma, source)
        return run_sweep(args, gamma, source)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
