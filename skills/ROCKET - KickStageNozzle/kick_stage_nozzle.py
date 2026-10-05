#!/usr/bin/env python3
"""Vacuum / high-altitude kick-stage nozzle synthesis.

There is no finite pe = pa optimum in vacuum, and the 1976 hydrostatic
atmosphere ends at 86 km, so ambient pressure is not looked up from that
table. The program synthesizes a practical nozzle from a design exit
pressure or area ratio: epsilon, length, optional shell mass, vacuum CF,
and Summerfield separation margin against a supplied ambient pressure.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

DEFAULT_GAMMA = 1.4
DEFAULT_HALF_ANGLE = math.radians(15.0)
DEFAULT_LENGTH_FRACTION = 1.0
DEFAULT_SEP_RATIO = 0.4
Z_HYDRO_MAX = 86000.0
N_SWEEP = 81
PLOT_TITLE = "Kick-stage nozzle: vacuum CF and length versus epsilon"

ASSUMPTIONS = (
    "kick-stage / vacuum nozzle synthesis; no finite pe=pa optimum when "
    "ambient pressure is zero; the 1976 U.S. Standard Atmosphere hydrostatic "
    "pressure table ends at 86 km and is not used here for ambient pressure "
    "(pass --pa when a finite ambient is known, including above 86 km); "
    "calorically perfect gas; steady one-dimensional isentropic nozzle; "
    "Me, epsilon, pe, and ideal CF from ROCKET - Area-Mach Graph; "
    "vacuum CF uses pa = 0; optional --pa evaluates CF and Summerfield "
    "separation at that ambient with pe_sep = k_sep * pa and default "
    "k_sep = 0.4; when separated_or_at_risk ambient CF and thrust are "
    "invalid_separated (CF_vac / thrust_vac_N remain); conical divergent "
    "wall with half-angle alpha; axial length "
    "L = f_L * (Re - Rt) / tan(alpha) with length fraction f_L (1 = full "
    "cone, typical 80-percent bell uses 0.8); slant length along the wall; "
    "optional shell mass is frustum lateral area times thickness times "
    "material density; throat sizing from --throat area or --rt radius; "
    "does not call CEA; does not invent pe or epsilon"
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
                invert_supersonic_mach,
                thrust_coefficient_ideal,
            )
        except ImportError as exc:
            raise ValueError(
                "numpy and matplotlib are required, and "
                "ROCKET - Area-Mach Graph must be importable"
            ) from exc
        _NOZZLE = (
            area_ratio,
            exit_pressure,
            expansion_flag,
            invert_supersonic_mach,
            thrust_coefficient_ideal,
        )
    return _NOZZLE


def require_positive(name: str, value: float) -> float:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")
    return value


def require_nonneg(name: str, value: float) -> float:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be finite and >= 0")
    return value


def resolve_gamma(raw: float | None) -> tuple[float, str]:
    if raw is None:
        return DEFAULT_GAMMA, "default"
    if not math.isfinite(raw) or raw <= 1.0:
        raise ValueError("--gamma must be > 1")
    return raw, "input"


def mach_from_pressure(pc: float, pe: float, gamma: float) -> float:
    """Inverse of exit_pressure: stagnation_pressure solved for Mach."""
    if pe <= 0.0 or pc <= 0.0:
        raise ValueError("pressures must be positive")
    if pe >= pc:
        raise ValueError("exit pressure must be below chamber pressure")
    exponent = (gamma - 1.0) / gamma
    me_sq = (2.0 / (gamma - 1.0)) * ((pc / pe) ** exponent - 1.0)
    if me_sq <= 0.0 or not math.isfinite(me_sq):
        raise ValueError("pressure ratio does not give a real Mach number")
    return math.sqrt(me_sq)


def throat_geometry(throat: float | None, rt: float | None) -> tuple[float, float]:
    """Return (At, Rt) from area and/or radius."""
    if throat is None and rt is None:
        raise ValueError("pass --throat or --rt for nozzle geometry and mass")
    if throat is not None and rt is not None:
        at = require_positive("--throat", throat)
        radius = require_positive("--rt", rt)
        implied = math.pi * radius * radius
        if abs(implied - at) / at > 1e-6:
            raise ValueError("--throat and --rt disagree on throat area")
        return at, radius
    if rt is not None:
        radius = require_positive("--rt", rt)
        return math.pi * radius * radius, radius
    at = require_positive("--throat", throat)
    return at, math.sqrt(at / math.pi)


def conical_geometry(
    rt: float,
    epsilon: float,
    half_angle: float,
    length_fraction: float,
) -> dict:
    """Conical divergent section from throat radius to exit."""
    if half_angle <= 0.0 or half_angle >= math.pi / 2.0:
        raise ValueError("--half-angle must be in (0, pi/2) rad")
    if not math.isfinite(length_fraction) or length_fraction <= 0.0:
        raise ValueError("--length-fraction must be > 0")
    re = rt * math.sqrt(epsilon)
    cone_axial = (re - rt) / math.tan(half_angle)
    axial = length_fraction * cone_axial
    # With length fraction < 1 the wall is shortened along the axis while
    # keeping the same exit radius (bell-length surrogate of an equal-epsilon cone).
    slant = math.hypot(axial, re - rt)
    return {
        "Rt": rt,
        "Re": re,
        "half_angle": half_angle,
        "length_fraction": length_fraction,
        "L_cone_m": cone_axial,
        "L_m": axial,
        "L_slant_m": slant,
   }


def shell_mass(rt: float, re: float, slant: float, thickness: float, rho_mat: float) -> float:
    """Truncated-cone lateral shell mass."""
    require_positive("--thickness", thickness)
    require_positive("--rho-mat", rho_mat)
    area = math.pi * (rt + re) * slant
    return area * thickness * rho_mat


def separation_state(pe: float, pa: float, k_sep: float) -> dict:
    """Summerfield-style separation check at a finite ambient pressure."""
    require_positive("k_sep", k_sep)
    if pa <= 0.0:
        return {
            "pa": 0.0,
            "pe_over_pa": None,
            "pe_sep": None,
            "separation_margin": None,
            "separation": "not_applicable_vacuum",
        }
    pe_over_pa = pe / pa
    pe_sep = k_sep * pa
    margin = pe / pe_sep - 1.0
    if pe >= pe_sep:
        flag = "attached"
    else:
        flag = "separated_or_at_risk"
    return {
        "pa": pa,
        "pe_over_pa": pe_over_pa,
        "pe_sep": pe_sep,
        "separation_margin": margin,
        "separation": flag,
    }


def synthesize(
    pc: float,
    gamma: float,
    *,
    epsilon: float | None,
    pe: float | None,
    pa: float,
    k_sep: float,
    throat: float | None,
    rt: float | None,
    half_angle: float,
    length_fraction: float,
    thickness: float | None,
    rho_mat: float | None,
) -> dict:
    """Build one nozzle design point."""
    area_ratio, exit_pressure, expansion_flag, invert_supersonic_mach, thrust_coefficient_ideal = (
        nozzle()
    )
    require_positive("--pc", pc)
    require_nonneg("--pa", pa)
    if (epsilon is None) == (pe is None):
        raise ValueError("pass exactly one of --epsilon or --pe")

    if pe is not None:
        pe_design = require_positive("--pe", pe)
        if pe_design >= pc:
            raise ValueError("--pe must be < --pc")
        me = mach_from_pressure(pc, pe_design, gamma)
        eps = area_ratio(me, gamma)
        design_source = "pe"
    else:
        eps = require_positive("--epsilon", epsilon)  # type: ignore[arg-type]
        if eps < 1.0:
            raise ValueError("--epsilon must be >= 1")
        me = invert_supersonic_mach(eps, gamma)
        pe_design = exit_pressure(pc, me, gamma)
        design_source = "epsilon"

    if me < 1.0 - 1e-8:
        raise ValueError("design exit is subsonic; kick-stage nozzles need Me >= 1")

    cf_vac = thrust_coefficient_ideal(gamma, pe_design, pc, 0.0, eps, 1.0)
    cf_pa = thrust_coefficient_ideal(gamma, pe_design, pc, pa, eps, 1.0)
    expansion = expansion_flag(pe_design, pa) if pa > 0.0 else "vacuum_underexpanded"
    sep = separation_state(pe_design, pa, k_sep)

    state: dict = {
        "design_source": design_source,
        "pc": pc,
        "gamma": gamma,
        "pa": pa,
        "pe": pe_design,
        "Me": me,
        "epsilon": eps,
        "CF_vac": cf_vac,
        "CF": cf_pa,
        "expansion": expansion,
        "k_sep": k_sep,
        **{k: v for k, v in sep.items() if k != "pa"},
    }

    if throat is not None or rt is not None:
        at, radius_t = throat_geometry(throat, rt)
        geom = conical_geometry(radius_t, eps, half_angle, length_fraction)
        state.update(geom)
        state["At"] = at
        state["Ae"] = eps * at
        state["thrust_vac_N"] = cf_vac * pc * at
        # Ambient CF/thrust are invalid once Summerfield predicts separation.
        if state["separation"] == "separated_or_at_risk":
            state["CF"] = None
            state["thrust_N"] = None
        else:
            state["thrust_N"] = cf_pa * pc * at
        if thickness is not None or rho_mat is not None:
            if thickness is None or rho_mat is None:
                raise ValueError("pass both --thickness and --rho-mat for nozzle mass")
            state["thickness"] = thickness
            state["rho_mat"] = rho_mat
            state["m_nozzle"] = shell_mass(
                geom["Rt"], geom["Re"], geom["L_slant_m"], thickness, rho_mat
            )
    else:
        if state["separation"] == "separated_or_at_risk":
            state["CF"] = None
        if thickness is not None or rho_mat is not None:
            raise ValueError("--thickness/--rho-mat require --throat or --rt")
        if half_angle != DEFAULT_HALF_ANGLE or length_fraction != DEFAULT_LENGTH_FRACTION:
            raise ValueError("--half-angle/--length-fraction require --throat or --rt")

    return state


def emit_state(state: dict, gamma_source: str, *, mode: str, pa_source: str) -> None:
    print_kv("title", PLOT_TITLE if mode == "sweep" else "Kick-stage nozzle synthesis")
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", mode)
    print_kv("model", "vacuum / above-86 km practical nozzle (not 1976 hydrostatic pe=pa)")
    print_kv("gamma", state["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("pc_Pa", state["pc"])
    print_kv("design_source", state["design_source"])
    print_kv("pa_Pa", state["pa"])
    print_kv("pa_source", pa_source)
    print_kv("pe_Pa", state["pe"])
    print_kv("Me", state["Me"])
    print_kv("epsilon", state["epsilon"])
    print_kv("CF_vac", state["CF_vac"])
    if state["CF"] is None:
        print_kv("CF", "invalid_separated")
    else:
        print_kv("CF", state["CF"])
    print_kv("expansion", state["expansion"])
    print_kv("k_sep", state["k_sep"])
    if state["pe_over_pa"] is None:
        print_kv("pe_over_pa", "n/a")
        print_kv("pe_sep_Pa", "n/a")
        print_kv("separation_margin", "n/a")
    else:
        print_kv("pe_over_pa", state["pe_over_pa"])
        print_kv("pe_sep_Pa", state["pe_sep"])
        print_kv("separation_margin", state["separation_margin"])
    print_kv("separation", state["separation"])
    if state["separation"] == "separated_or_at_risk":
        print_kv(
            "warning",
            "Summerfield separation risk: ambient CF and thrust are invalid; "
            "use CF_vac / thrust_vac_N only",
        )
    if "At" in state:
        print_kv("throat_m2", state["At"])
        print_kv("Rt_m", state["Rt"])
        print_kv("Re_m", state["Re"])
        print_kv("Ae_m2", state["Ae"])
        print_kv("half_angle_rad", state["half_angle"])
        print_kv("length_fraction", state["length_fraction"])
        print_kv("L_cone_m", state["L_cone_m"])
        print_kv("L_m", state["L_m"])
        print_kv("L_slant_m", state["L_slant_m"])
        print_kv("thrust_vac_N", state["thrust_vac_N"])
        if state.get("thrust_N") is None:
            print_kv("thrust_N", "invalid_separated")
        else:
            print_kv("thrust_N", state["thrust_N"])
    if "m_nozzle" in state:
        print_kv("thickness_m", state["thickness"])
        print_kv("rho_mat_kg_m3", state["rho_mat"])
        print_kv("m_nozzle_kg", state["m_nozzle"])


def ensure_matplotlib():
    nozzle()
    import matplotlib.pyplot as plt

    return plt


def plot_trade(
    path: Path,
    epsilons: list[float],
    cfs: list[float],
    lengths: list[float] | None,
    mark: dict | None,
) -> None:
    plt = ensure_matplotlib()
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(epsilons, cfs, color="#1a5276", linewidth=1.8, label=r"vacuum $C_F$")
    ax1.set_xlabel(r"area ratio $\epsilon$")
    ax1.set_ylabel(r"vacuum thrust coefficient $C_F$")
    ax1.set_title(PLOT_TITLE)
    ax1.grid(True, alpha=0.35)
    if mark is not None:
        ax1.plot(
            mark["epsilon"],
            mark["CF_vac"],
            "s",
            color="#27ae60",
            markersize=7,
            zorder=5,
            label=f"design ({mark['epsilon']:.6g}, {mark['CF_vac']:.6g})",
        )
    if lengths is not None:
        ax2 = ax1.twinx()
        ax2.plot(epsilons, lengths, color="#c0392b", linewidth=1.5, linestyle="--", label="axial length")
        ax2.set_ylabel("axial nozzle length $L$ (m)")
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="best", fontsize=9)
    else:
        ax1.legend(loc="best", fontsize=9)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def linspace(lo: float, hi: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("need at least 2 sweep samples")
    step = (hi - lo) / (count - 1)
    values = [lo + step * i for i in range(count)]
    values[-1] = hi
    return values


def run_point(ns: argparse.Namespace, gamma: float, gamma_source: str) -> int:
    if ns.out is not None:
        raise ValueError("--out applies only to an epsilon sweep")
    pa_source = "vacuum (omitted --pa)" if ns.pa is None else "input"
    state = synthesize(
        require_positive("--pc", ns.pc),
        gamma,
        epsilon=ns.epsilon,
        pe=ns.pe,
        pa=0.0 if ns.pa is None else require_nonneg("--pa", ns.pa),
        k_sep=ns.k_sep,
        throat=ns.throat,
        rt=ns.rt,
        half_angle=ns.half_angle,
        length_fraction=ns.length_fraction,
        thickness=ns.thickness,
        rho_mat=ns.rho_mat,
    )
    emit_state(state, gamma_source, mode="point", pa_source=pa_source)
    if ns.alt is not None:
        print_kv(
            "warning",
            f"geometric altitude {ns.alt:.8g} m was noted only; ambient "
            "pressure was not taken from the 1976 hydrostatic table "
            "(ends at 86 km). Use --pa for a known ambient, or omit --pa "
            "for vacuum synthesis",
        )
    if ns.alt is not None and ns.alt <= Z_HYDRO_MAX and ns.pa is None:
        print_kv(
            "hint",
            "altitude is at or below 86 km; for pe=pa matching on the "
            "1976 hydrostatic table use ROCKET - ExpansionMatchEarth",
        )
    return 0


def run_sweep(ns: argparse.Namespace, gamma: float, gamma_source: str) -> int:
    if ns.epsilon_min is None or ns.epsilon_max is None:
        raise ValueError("sweep needs --epsilon-min and --epsilon-max")
    eps_lo = require_positive("--epsilon-min", ns.epsilon_min)
    eps_hi = require_positive("--epsilon-max", ns.epsilon_max)
    if eps_lo >= eps_hi:
        raise ValueError("--epsilon-min must be < --epsilon-max")
    if eps_lo < 1.0:
        raise ValueError("--epsilon-min must be >= 1")

    pc = require_positive("--pc", ns.pc)
    pa = 0.0 if ns.pa is None else require_nonneg("--pa", ns.pa)
    pa_source = "vacuum (omitted --pa)" if ns.pa is None else "input"
    mark = None
    if ns.epsilon is not None or ns.pe is not None:
        mark = synthesize(
            pc,
            gamma,
            epsilon=ns.epsilon,
            pe=ns.pe,
            pa=pa,
            k_sep=ns.k_sep,
            throat=ns.throat,
            rt=ns.rt,
            half_angle=ns.half_angle,
            length_fraction=ns.length_fraction,
            thickness=ns.thickness,
            rho_mat=ns.rho_mat,
        )

    samples = linspace(eps_lo, eps_hi, N_SWEEP)
    cfs: list[float] = []
    lengths: list[float] | None = [] if (ns.throat is not None or ns.rt is not None) else None
    for eps in samples:
        state = synthesize(
            pc,
            gamma,
            epsilon=eps,
            pe=None,
            pa=pa,
            k_sep=ns.k_sep,
            throat=ns.throat,
            rt=ns.rt,
            half_angle=ns.half_angle,
            length_fraction=ns.length_fraction,
            thickness=None,
            rho_mat=None,
        )
        cfs.append(state["CF_vac"])
        if lengths is not None:
            lengths.append(state["L_m"])

    out_path = Path(ns.out) if ns.out else SKILL_DIR / "kick_stage_nozzle.png"
    out_path = out_path.resolve()
    plot_trade(out_path, samples, cfs, lengths, mark)

    if mark is not None:
        emit_state(mark, gamma_source, mode="sweep", pa_source=pa_source)
    else:
        # Report ends without inventing a design point.
        lo_state = synthesize(
            pc,
            gamma,
            epsilon=eps_lo,
            pe=None,
            pa=pa,
            k_sep=ns.k_sep,
            throat=ns.throat,
            rt=ns.rt,
            half_angle=ns.half_angle,
            length_fraction=ns.length_fraction,
            thickness=ns.thickness,
            rho_mat=ns.rho_mat,
        )
        hi_state = synthesize(
            pc,
            gamma,
            epsilon=eps_hi,
            pe=None,
            pa=pa,
            k_sep=ns.k_sep,
            throat=ns.throat,
            rt=ns.rt,
            half_angle=ns.half_angle,
            length_fraction=ns.length_fraction,
            thickness=ns.thickness,
            rho_mat=ns.rho_mat,
        )
        print_kv("title", PLOT_TITLE)
        print_kv("assumptions", ASSUMPTIONS)
        print_kv("mode", "sweep")
        print_kv("model", "vacuum / above-86 km practical nozzle (not 1976 hydrostatic pe=pa)")
        print_kv("gamma", gamma)
        print_kv("gamma_source", gamma_source)
        print_kv("pc_Pa", pc)
        print_kv("pa_Pa", pa)
        print_kv("pa_source", pa_source)
        print_kv("epsilon_min", eps_lo)
        print_kv("epsilon_max", eps_hi)
        print_kv("CF_vac_at_epsilon_min", lo_state["CF_vac"])
        print_kv("CF_vac_at_epsilon_max", hi_state["CF_vac"])
        if "L_m" in lo_state:
            print_kv("L_at_epsilon_min_m", lo_state["L_m"])
            print_kv("L_at_epsilon_max_m", hi_state["L_m"])
        if "m_nozzle" in lo_state:
            print_kv("m_nozzle_at_epsilon_min_kg", lo_state["m_nozzle"])
            print_kv("m_nozzle_at_epsilon_max_kg", hi_state["m_nozzle"])

    if ns.alt is not None:
        print_kv(
            "warning",
            f"geometric altitude {ns.alt:.8g} m was noted only; ambient "
            "pressure was not taken from the 1976 hydrostatic table "
            "(ends at 86 km)",
        )
    print_kv("graph", str(out_path))
    return 0


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    area_ratio, exit_pressure, _flag, invert, thrust_coefficient_ideal = nozzle()
    gamma = 1.25
    pc = 2.0e6
    pe = 5000.0
    me = mach_from_pressure(pc, pe, gamma)
    eps = area_ratio(me, gamma)
    pe_back = exit_pressure(pc, me, gamma)
    if abs(pe_back - pe) / pe > 1e-8:
        return fail("pe round-trip")
    me_inv = invert(eps, gamma)
    if abs(me_inv - me) > 1e-6:
        return fail(f"epsilon invert Me = {me_inv}")

    state = synthesize(
        pc,
        gamma,
        epsilon=None,
        pe=pe,
        pa=0.0,
        k_sep=DEFAULT_SEP_RATIO,
        throat=1.0e-3,
        rt=None,
        half_angle=DEFAULT_HALF_ANGLE,
        length_fraction=1.0,
        thickness=0.002,
        rho_mat=2700.0,
    )
    if state["design_source"] != "pe":
        return fail("design_source")
    if abs(state["pe"] - pe) > 1e-9:
        return fail("stored pe")
    if abs(state["CF_vac"] - thrust_coefficient_ideal(gamma, pe, pc, 0.0, eps, 1.0)) > 1e-12:
        return fail("CF_vac")
    if state["separation"] != "not_applicable_vacuum":
        return fail("vacuum separation flag")
    expected_re = state["Rt"] * math.sqrt(state["epsilon"])
    if abs(state["Re"] - expected_re) > 1e-12:
        return fail("Re")
    expected_l = (state["Re"] - state["Rt"]) / math.tan(DEFAULT_HALF_ANGLE)
    if abs(state["L_m"] - expected_l) > 1e-9:
        return fail("conical length")
    expected_m = (
        math.pi
        * (state["Rt"] + state["Re"])
        * state["L_slant_m"]
        * 0.002
        * 2700.0
    )
    if abs(state["m_nozzle"] - expected_m) / expected_m > 1e-9:
        return fail("shell mass")

    short = synthesize(
        pc,
        gamma,
        epsilon=state["epsilon"],
        pe=None,
        pa=0.0,
        k_sep=DEFAULT_SEP_RATIO,
        throat=1.0e-3,
        rt=None,
        half_angle=DEFAULT_HALF_ANGLE,
        length_fraction=0.8,
        thickness=None,
        rho_mat=None,
    )
    if abs(short["L_m"] - 0.8 * expected_l) > 1e-9:
        return fail("length fraction")

    sep = synthesize(
        pc,
        gamma,
        epsilon=None,
        pe=pe,
        pa=pe / 0.5,
        k_sep=0.4,
        throat=None,
        rt=None,
        half_angle=DEFAULT_HALF_ANGLE,
        length_fraction=1.0,
        thickness=None,
        rho_mat=None,
    )
    # pe/pa = 0.5 > 0.4 => attached, margin = 0.5/0.4 - 1 = 0.25
    if abs(sep["pe_over_pa"] - 0.5) > 1e-12:
        return fail("pe_over_pa")
    if abs(sep["separation_margin"] - 0.25) > 1e-12:
        return fail("separation_margin")
    if sep["separation"] != "attached":
        return fail("attached flag")

    risk = synthesize(
        pc,
        gamma,
        epsilon=None,
        pe=pe,
        pa=pe / 0.3,
        k_sep=0.4,
        throat=None,
        rt=None,
        half_angle=DEFAULT_HALF_ANGLE,
        length_fraction=1.0,
        thickness=None,
        rho_mat=None,
    )
    if risk["separation"] != "separated_or_at_risk":
        return fail("separation risk flag")
    if risk["CF"] is not None:
        return fail("separated design must invalidate ambient CF")

    risk_geom = synthesize(
        pc,
        gamma,
        epsilon=None,
        pe=pe,
        pa=pe / 0.3,
        k_sep=0.4,
        throat=1.0e-3,
        rt=None,
        half_angle=DEFAULT_HALF_ANGLE,
        length_fraction=1.0,
        thickness=None,
        rho_mat=None,
    )
    if risk_geom["thrust_N"] is not None or risk_geom["CF"] is not None:
        return fail("separated design must invalidate ambient thrust/CF")
    if "thrust_vac_N" not in risk_geom:
        return fail("vacuum thrust should remain when separated")

    try:
        synthesize(
            pc,
            gamma,
            epsilon=20.0,
            pe=pe,
            pa=0.0,
            k_sep=0.4,
            throat=None,
            rt=None,
            half_angle=DEFAULT_HALF_ANGLE,
            length_fraction=1.0,
            thickness=None,
            rho_mat=None,
        )
    except ValueError:
        pass
    else:
        return fail("accepted both epsilon and pe")

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "trade.png")
        old = sys.stdout
        sys.stdout = tempfile.TemporaryFile(mode="w+")
        try:
            code = main(
                [
                    "--pc",
                    "2e6",
                    "--gamma",
                    "1.25",
                    "--epsilon-min",
                    "10",
                    "--epsilon-max",
                    "80",
                    "--epsilon",
                    "40",
                    "--throat",
                    "0.001",
                    "--out",
                    out,
                ]
            )
        finally:
            sys.stdout.close()
            sys.stdout = old
        if code != 0:
            return fail(f"sweep main returned {code}")
        if not Path(out).read_bytes().startswith(b"\x89PNG"):
            return fail("sweep PNG")

    sink = sys.stderr
    sys.stderr = tempfile.TemporaryFile(mode="w+")
    try:
        missing = main(["--epsilon", "40"])
    finally:
        sys.stderr.close()
        sys.stderr = sink
    if missing != 2:
        return fail("missing pc accepted")

    print("check: pass")
    print_kv("check_epsilon", state["epsilon"])
    print_kv("check_Me", state["Me"])
    print_kv("check_CF_vac", state["CF_vac"])
    print_kv("check_L_m", state["L_m"])
    print_kv("check_m_nozzle_kg", state["m_nozzle"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vacuum / above-86 km kick-stage nozzle synthesis."
    )
    parser.add_argument("--pc", type=float, default=None, help="chamber pressure p1 [Pa]")
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help=f"ratio of specific heats (default {DEFAULT_GAMMA})",
    )
    parser.add_argument("--epsilon", type=float, default=None, help="design Ae/At")
    parser.add_argument("--pe", type=float, default=None, help="design exit pressure [Pa]")
    parser.add_argument(
        "--pa",
        type=float,
        default=None,
        help="ambient pressure for CF and separation [Pa]; omit for vacuum",
    )
    parser.add_argument(
        "--alt",
        type=float,
        default=None,
        help="geometric altitude note only [m]; does not set pa from 1976",
    )
    parser.add_argument("--throat", type=float, default=None, help="throat area At [m^2]")
    parser.add_argument("--rt", type=float, default=None, help="throat radius Rt [m]")
    parser.add_argument(
        "--half-angle",
        type=float,
        default=DEFAULT_HALF_ANGLE,
        help=f"conical half-angle [rad] (default {DEFAULT_HALF_ANGLE})",
    )
    parser.add_argument(
        "--length-fraction",
        type=float,
        default=DEFAULT_LENGTH_FRACTION,
        help="axial length / equivalent-cone length (default 1; 0.8 for 80% bell)",
    )
    parser.add_argument("--thickness", type=float, default=None, help="wall thickness [m]")
    parser.add_argument("--rho-mat", type=float, default=None, help="wall material density [kg/m^3]")
    parser.add_argument(
        "--k-sep",
        type=float,
        default=DEFAULT_SEP_RATIO,
        help=f"Summerfield pe_sep/pa (default {DEFAULT_SEP_RATIO})",
    )
    parser.add_argument("--epsilon-min", type=float, default=None, help="sweep low epsilon")
    parser.add_argument("--epsilon-max", type=float, default=None, help="sweep high epsilon")
    parser.add_argument("--out", type=str, default=None, help="PNG path for an epsilon sweep")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        if args.pc is None:
            raise ValueError("--pc must be > 0 Pa")
        if args.k_sep is None or not math.isfinite(args.k_sep) or args.k_sep <= 0.0:
            raise ValueError("--k-sep must be > 0")
        if args.alt is not None and (
            not math.isfinite(args.alt) or args.alt < 0.0
        ):
            raise ValueError("--alt must be >= 0 m geometric")
        gamma, source = resolve_gamma(args.gamma)
        if args.epsilon_min is not None or args.epsilon_max is not None or args.out is not None:
            return run_sweep(args, gamma, source)
        if args.epsilon is None and args.pe is None:
            raise ValueError("pass --epsilon or --pe (vacuum has no pe=pa match)")
        return run_point(args, gamma, source)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
