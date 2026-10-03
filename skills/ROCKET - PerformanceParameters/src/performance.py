#!/usr/bin/env python3
"""Frozen-CEA performance: c*, ideal Cf, Isp, density impulse, and X-vs-Y plots.

Nozzle Me, pe, Cf, and the expansion flag come from the Area-Mach program.
CEA is not called here.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from load_table import (
    TableError,
    canonical_pair,
    interpolate_row,
    pair_spec,
    pc_bar_from_pa,
    pc_pa_from_bar,
    pick_table,
    tables_for_pair,
)

SKILL_DIR = Path(__file__).resolve().parent.parent
AREA_MACH_DIR = SKILL_DIR.parent / "ROCKET - Area-Mach Graph"

# Standard gravity used to turn effective exhaust velocity into seconds.
G0 = 9.80665
N_SAMPLES = 201

SWEEP_AXES = ("mixture ratio", "pc", "eps", "pa")
SWEEP_INPUT = {
    "mixture ratio": "r",
    "pc": "pc",
    "eps": "eps",
    "pa": "pa",
}

# chamber: frozen table. nozzle: Me, pe, vacuum Cf. ambient: Cf at pa.
# density: liquid densities from pairs.json.
NEEDS = {
    "c*": frozenset({"chamber"}),
    "Tc": frozenset({"chamber"}),
    "gamma_throat": frozenset({"chamber"}),
    "gamma_chamber": frozenset({"chamber"}),
    "Cf": frozenset({"chamber", "nozzle", "ambient"}),
    "Isp sea level": frozenset({"chamber", "nozzle", "ambient"}),
    "Isp vacuum": frozenset({"chamber", "nozzle"}),
    "density Isp": frozenset({"chamber", "nozzle", "ambient", "density"}),
    "density Isp vacuum": frozenset({"chamber", "nozzle", "density"}),
    "bulk density": frozenset({"density"}),
}

AXIS_NAMES = {
    "mixture ratio": "mixture ratio",
    "pc": "pc",
    "eps": "eps",
    "pa": "pa",
    "c*": "c*",
    "tc": "Tc",
    "gamma_throat": "gamma_throat",
    "gamma_chamber": "gamma_chamber",
    "cf": "Cf",
    "isp sea level": "Isp sea level",
    "isp vacuum": "Isp vacuum",
    "density isp": "density Isp",
    "density isp vacuum": "density Isp vacuum",
    "bulk density": "bulk density",
}

LABELS = {
    "mixture ratio": "mixture ratio r (ox/fuel)",
    "pc": "chamber pressure pc (Pa)",
    "eps": "area ratio eps (Ae/At)",
    "pa": "ambient pressure pa (Pa)",
    "c*": "c* (m/s)",
    "Tc": "Tc (K)",
    "gamma_throat": "gamma_throat",
    "gamma_chamber": "gamma_chamber",
    "Cf": "Cf",
    "Isp sea level": "Isp at pa (s)",
    "Isp vacuum": "Isp vacuum (s)",
    "density Isp": "density Isp (kg s/m^3)",
    "density Isp vacuum": "density Isp vacuum (kg s/m^3)",
    "bulk density": "bulk density (kg/m^3)",
}

QUANTITY_KEY = {
    "c*": "cstar_m_s",
    "Tc": "Tc_K",
    "gamma_throat": "gamma_throat",
    "gamma_chamber": "gamma_chamber",
    "Cf": "Cf",
    "Isp sea level": "Isp_s",
    "Isp vacuum": "Isp_vac_s",
    "density Isp": "density_isp",
    "density Isp vacuum": "density_isp_vac",
    "bulk density": "rho_b",
}

COLORS = ("#1a5276", "#c0392b", "#1e8449", "#b9770e", "#6c3483", "#0e6655")

_PYPLOT = None
_NOZZLE = None


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def fmt_num(value: float) -> str:
    return f"{value:.8g}"


def bulk_density(r: float, rho_ox: float, rho_fuel: float) -> float:
    """1/rho_b = r/((r+1)*rho_ox) + 1/((r+1)*rho_fuel)."""
    if r <= 0:
        raise ValueError("--r must be > 0")
    if rho_ox <= 0 or rho_fuel <= 0:
        raise ValueError("densities must be positive")
    return 1.0 / (r / ((r + 1.0) * rho_ox) + 1.0 / ((r + 1.0) * rho_fuel))


def ensure_matplotlib():
    global _PYPLOT
    if _PYPLOT is None:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        _PYPLOT = plt
    return _PYPLOT


def nozzle_funcs():
    """Area-Mach identities. Imported lazily so a missing plot stack fails at use."""
    global _NOZZLE
    if _NOZZLE is None:
        ensure_matplotlib()
        folder = str(AREA_MACH_DIR)
        if folder not in sys.path:
            sys.path.insert(0, folder)
        from area_mach import (
            exit_pressure,
            expansion_flag,
            invert_supersonic_mach,
            thrust_coefficient_ideal,
        )

        _NOZZLE = (
            invert_supersonic_mach,
            exit_pressure,
            thrust_coefficient_ideal,
            expansion_flag,
        )
    return _NOZZLE


def gamma_source_name(flag: str) -> str:
    if flag == "throat":
        return "gamma_throat"
    if flag == "chamber":
        return "gamma_chamber"
    raise ValueError("--gamma-source must be throat or chamber")


def evaluate(
    pair: str,
    *,
    r: float,
    pc_Pa: float | None,
    eps: float | None,
    pa: float | None,
    gamma_source: str,
    needs: frozenset[str],
) -> dict:
    """One operating point. The frozen table supplies c*, Tc, Mw, and gamma.

    Exit pressure and ideal Cf use the requested chamber pressure in Pa.
    """
    key = canonical_pair(pair)
    if "chamber" in needs or "density" in needs:
        if r is None or r <= 0:
            raise ValueError("--r must be > 0")
    if "chamber" in needs:
        if pc_Pa is None or pc_Pa <= 0:
            raise ValueError("--pc must be > 0 Pa")
    if "nozzle" in needs:
        if eps is None or eps < 1.0:
            raise ValueError("--eps must be >= 1")
    if "ambient" in needs:
        if pa is None or pa < 0:
            raise ValueError("--pa must be >= 0 Pa")

    state: dict = {"pair": key, "r": r, "warning": None}
    if "density" in needs:
        spec = pair_spec(key)
        state["rho_ox_kg_m3"] = spec.rho_ox_kg_m3
        state["rho_ox_T_K"] = spec.rho_ox_T_K
        state["rho_fuel_kg_m3"] = spec.rho_fuel_kg_m3
        state["rho_fuel_T_K"] = spec.rho_fuel_T_K
        state["rho_b"] = bulk_density(r, spec.rho_ox_kg_m3, spec.rho_fuel_kg_m3)

    if "chamber" in needs:
        assert pc_Pa is not None
        pick = pick_table(key, pc_bar_from_pa(pc_Pa))
        row = interpolate_row(pick.table, r)
        source = gamma_source_name(gamma_source)
        gamma = row[source]
        if gamma <= 1.0:
            raise ValueError(f"{source} must be > 1")
        state.update(
            {
                "cstar_m_s": row["cstar_m_s"],
                "Tc_K": row["Tc_K"],
                "Mw": row["Mw"],
                "gamma_chamber": row["gamma_chamber"],
                "gamma_throat": row["gamma_throat"],
                "cstar_rel_diff": row["cstar_rel_diff"],
                "pc_Pa": pc_Pa,
                "pc_table_bar": pick.table["pc_bar"],
                "pc_offset_bar": pick.offset_bar,
                "warning": pick.warning,
                "gamma_source": source,
                "gamma": gamma,
            }
        )

    if "nozzle" in needs:
        assert pc_Pa is not None and eps is not None
        invert, exit_p, cf_ideal, _flag = nozzle_funcs()
        gamma = state["gamma"]
        # Ae/At = eps with At = 1. Vacuum Cf uses pa = 0.
        me = invert(eps, gamma)
        pe = exit_p(pc_Pa, me, gamma)
        cf_vac = cf_ideal(gamma, pe, pc_Pa, 0.0, eps, 1.0)
        state["Me"] = me
        state["pe_Pa"] = pe
        state["eps"] = eps
        state["Cf_vac"] = cf_vac
        state["Isp_vac_s"] = state["cstar_m_s"] * cf_vac / G0
        if "density" in needs:
            state["density_isp_vac"] = state["rho_b"] * state["Isp_vac_s"]
        if "ambient" in needs:
            assert pa is not None
            cf = cf_ideal(gamma, pe, pc_Pa, pa, eps, 1.0)
            state["Cf"] = cf
            state["pa_Pa"] = pa
            state["Isp_s"] = state["cstar_m_s"] * cf / G0
            state["expansion"] = _flag(pe, pa)
            if "density" in needs:
                state["density_isp"] = state["rho_b"] * state["Isp_s"]
    return state


def emit_point(state: dict) -> None:
    rows = (
        ("pair", state["pair"]),
        ("r", state["r"]),
        ("pc_Pa", state["pc_Pa"]),
        ("eps", state["eps"]),
        ("cstar_m_s", state["cstar_m_s"]),
        ("Tc_K", state["Tc_K"]),
        ("Mw_kg_kmol", state["Mw"]),
        ("gamma_chamber", state["gamma_chamber"]),
        ("gamma_throat", state["gamma_throat"]),
        ("gamma_source", state["gamma_source"]),
        ("gamma", state["gamma"]),
        ("Me", state["Me"]),
        ("pe_Pa", state["pe_Pa"]),
        ("Cf", state["Cf"]),
        ("Cf_vac", state["Cf_vac"]),
        ("Isp_s", state["Isp_s"]),
        ("pa_Pa", state["pa_Pa"]),
        ("Isp_vac_s", state["Isp_vac_s"]),
        ("rho_ox_kg_m3", state["rho_ox_kg_m3"]),
        ("rho_ox_T_K", state["rho_ox_T_K"]),
        ("rho_fuel_kg_m3", state["rho_fuel_kg_m3"]),
        ("rho_fuel_T_K", state["rho_fuel_T_K"]),
        ("rho_b_kg_m3", state["rho_b"]),
        ("density_isp", state["density_isp"]),
        ("density_isp_vac", state["density_isp_vac"]),
        ("pc_table_bar", state["pc_table_bar"]),
        ("pc_offset_bar", state["pc_offset_bar"]),
        ("cstar_rel_diff", state["cstar_rel_diff"]),
        ("expansion", state["expansion"]),
    )
    for key, value in rows:
        print_kv(key, value)
    if state.get("warning"):
        print_kv("warning", state["warning"])


POINT_NEEDS = frozenset({"chamber", "nozzle", "ambient", "density"})


def run_point(args: argparse.Namespace) -> int:
    if not args.pair:
        raise ValueError("point request requires --pair, --pc, --eps, --pa, and --r; missing --pair")
    missing = []
    if args.pc is None:
        missing.append("--pc")
    if args.eps is None:
        missing.append("--eps")
    if args.pa is None:
        missing.append("--pa")
    if args.r is None:
        missing.append("--r")
    if missing:
        raise ValueError(
            "point request requires --pair, --pc, --eps, --pa, and --r; "
            f"missing {', '.join(missing)}"
        )
    if args.pc <= 0:
        raise ValueError("--pc must be > 0 Pa")
    if args.eps < 1:
        raise ValueError("--eps must be >= 1")
    if args.pa < 0:
        raise ValueError("--pa must be >= 0 Pa")
    if args.r <= 0:
        raise ValueError("--r must be > 0")

    results = [
        evaluate(
            raw,
            r=args.r,
            pc_Pa=args.pc,
            eps=args.eps,
            pa=args.pa,
            gamma_source=args.gamma_source,
            needs=POINT_NEEDS,
        )
        for raw in args.pair
    ]
    for i, state in enumerate(results):
        if i:
            print()
        emit_point(state)
    return 0


def canon_name(text: str) -> str:
    key = " ".join(text.strip().lower().split())
    if key not in AXIS_NAMES:
        known = (
            "mixture ratio, pc, eps, pa, c*, Tc, gamma_throat, gamma_chamber, "
            "Cf, Isp sea level, Isp vacuum, density Isp, density Isp vacuum, bulk density"
        )
        raise ValueError(f"unknown plot axis {text!r}; accepted names: {known}")
    return AXIS_NAMES[key]


def parse_plot(spec: str) -> tuple[str, str]:
    """Return (vertical, horizontal). The name before vs is the vertical axis."""
    parts = re.split(r"\s+vs\s+", spec.strip(), maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise ValueError(f'plot must be "Y vs X", got {spec!r}')
    return canon_name(parts[0]), canon_name(parts[1])


def required_fixed(quantity: str, sweep: str) -> list[str]:
    needs = NEEDS[quantity]
    required: list[str] = []
    if "chamber" in needs or "density" in needs:
        required.append("r")
    if "chamber" in needs:
        required.append("pc")
    if "nozzle" in needs:
        required.append("eps")
    if "ambient" in needs:
        required.append("pa")
    skip = SWEEP_INPUT[sweep]
    return [item for item in required if item != skip]


def linspace(lo: float, hi: float, n: int = N_SAMPLES) -> list[float]:
    if not hi > lo:
        raise ValueError("sweep range must have min < max")
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n - 1)] + [hi]


def dedupe_sorted(values: list[float]) -> list[float]:
    ordered = sorted(values)
    out: list[float] = []
    for value in ordered:
        if not out or abs(value - out[-1]) > 1e-9 * max(1.0, abs(value)):
            out.append(value)
    return out


def check_span(axis: str, lo: float, hi: float) -> None:
    if not hi > lo:
        raise ValueError(f"{axis} sweep range must have min < max")
    if axis == "pc" and not lo > 0:
        raise ValueError("pc sweep min must be > 0 Pa")
    if axis == "eps" and lo < 1.0:
        raise ValueError("eps sweep min must be >= 1")
    if axis == "pa" and lo < 0:
        raise ValueError("pa sweep min must be >= 0 Pa")
    if axis == "mixture ratio" and not lo > 0:
        raise ValueError("mixture-ratio sweep min must be > 0")


@dataclass
class SweepRange:
    lo: float
    hi: float
    assumed: bool
    text: str
    nodes: list[float] = field(default_factory=list)


def resolve_shared_range(axis: str, args: argparse.Namespace) -> SweepRange:
    defaults = {
        "pc": (1.0e6, 4.0e6),
        "eps": (5.0, 40.0),
        "pa": (0.0, 101325.0),
    }
    flags = {
        "pc": (args.pc_min, args.pc_max),
        "eps": (args.eps_min, args.eps_max),
        "pa": (args.pa_min, args.pa_max),
    }
    dlo, dhi = defaults[axis]
    flo, fhi = flags[axis]
    lo = dlo if flo is None else flo
    hi = dhi if fhi is None else fhi
    check_span(axis, lo, hi)
    if axis == "pc":
        text = f"pc {fmt_num(lo)} to {fmt_num(hi)} Pa"
    elif axis == "eps":
        text = f"eps {fmt_num(lo)} to {fmt_num(hi)}"
    else:
        text = f"pa {fmt_num(lo)} to {fmt_num(hi)} Pa"
    return SweepRange(lo=lo, hi=hi, assumed=flo is None or fhi is None, text=text)


def mixture_bounds(pair: str, *, need_chamber: bool, pc_Pa: float | None) -> tuple[float, float, list[float]]:
    if need_chamber:
        if pc_Pa is None:
            raise ValueError("--pc must be > 0 Pa")
        pick = pick_table(pair, pc_bar_from_pa(pc_Pa))
        columns = pick.table["columns"]
        r_index = columns.index("r")
        nodes = [row[r_index] for row in pick.table["rows"]]
        return nodes[0], nodes[-1], nodes
    spec = pair_spec(pair)
    return spec.of_min, spec.of_max, []


def resolve_mixture(pair: str, args: argparse.Namespace, *, need_chamber: bool, pc_Pa: float | None) -> SweepRange:
    dlo, dhi, nodes = mixture_bounds(pair, need_chamber=need_chamber, pc_Pa=pc_Pa)
    lo = dlo if args.r_min is None else args.r_min
    hi = dhi if args.r_max is None else args.r_max
    check_span("mixture ratio", lo, hi)
    text = f"{pair} mixture ratio {fmt_num(lo)} to {fmt_num(hi)}"
    inside = [node for node in nodes if lo <= node <= hi]
    return SweepRange(
        lo=lo,
        hi=hi,
        assumed=args.r_min is None or args.r_max is None,
        text=text,
        nodes=inside,
    )


def sample_axis(span: SweepRange, *, bars: list[float] | None = None) -> list[float]:
    extra = list(span.nodes)
    if bars:
        ordered = sorted(bars)
        for i, bar in enumerate(ordered):
            extra.append(pc_pa_from_bar(bar))
            if i + 1 < len(ordered):
                mid_pa = pc_pa_from_bar(0.5 * (bar + ordered[i + 1]))
                extra.append(mid_pa)
                extra.append(mid_pa - 1.0)
    inside = [value for value in extra if span.lo <= value <= span.hi]
    return dedupe_sorted(linspace(span.lo, span.hi) + inside)


def quantity_of(state: dict, name: str) -> float:
    value = state.get(QUANTITY_KEY[name])
    if value is None:
        raise ValueError(f"could not compute {name}")
    return float(value)


@dataclass
class Curve:
    pair: str
    sweep_values: list[float]
    quantity_values: list[float]
    pc_table_bar: float | None
    pc_offset_bar: float | None
    gamma: float | None
    warnings: list[str]


def build_curve(
    pair: str,
    quantity: str,
    sweep: str,
    samples: list[float],
    fixed: dict,
    gamma_source: str,
) -> Curve:
    needs = NEEDS[quantity]
    sweep_values: list[float] = []
    quantity_values: list[float] = []
    gammas: list[float] = []
    tables: list[float] = []
    offsets: list[float] = []
    worst_warning: tuple[float, str] | None = None
    for sample in samples:
        local = dict(fixed)
        if sweep == "mixture ratio":
            local["r"] = sample
        elif sweep == "pc":
            local["pc_Pa"] = sample
        elif sweep == "eps":
            local["eps"] = sample
        elif sweep == "pa":
            local["pa"] = sample
        state = evaluate(pair, gamma_source=gamma_source, needs=needs, **local)
        sweep_values.append(sample)
        quantity_values.append(quantity_of(state, quantity))
        if state.get("gamma") is not None:
            gammas.append(float(state["gamma"]))
        if state.get("pc_table_bar") is not None:
            tables.append(float(state["pc_table_bar"]))
            offsets.append(float(state["pc_offset_bar"]))
        warning = state.get("warning")
        if warning:
            off = abs(float(state["pc_offset_bar"]))
            if worst_warning is None or off > worst_warning[0]:
                worst_warning = (off, warning)
    gamma = gammas[0] if gammas and (max(gammas) - min(gammas)) <= 1e-9 else None
    same_table = bool(tables) and all(abs(item - tables[0]) <= 1e-9 for item in tables)
    return Curve(
        pair=canonical_pair(pair),
        sweep_values=sweep_values,
        quantity_values=quantity_values,
        pc_table_bar=tables[0] if same_table else None,
        pc_offset_bar=offsets[0] if same_table else None,
        gamma=gamma,
        warnings=[worst_warning[1]] if worst_warning else [],
    )


def slug(text: str) -> str:
    raw = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    while "__" in raw:
        raw = raw.replace("__", "_")
    return raw.strip("_") or "plot"


def draw_plot(
    path: Path,
    x_name: str,
    y_name: str,
    sweep: str,
    quantity: str,
    curves: list[Curve],
    mark_r: float | None,
    mark_peak: bool,
    mark_states: list[tuple[str, float, float]],
) -> list[str]:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 5))
    peaks: list[str] = []
    r_drawn = False
    for i, curve in enumerate(curves):
        color = COLORS[i % len(COLORS)]
        if x_name == sweep:
            xs = curve.sweep_values
            ys = curve.quantity_values
        else:
            xs = curve.quantity_values
            ys = curve.sweep_values
        ax.plot(xs, ys, color=color, linewidth=1.8, label=curve.pair)
        if mark_peak and curve.quantity_values:
            idx = max(range(len(curve.quantity_values)), key=lambda k: curve.quantity_values[k])
            ax.plot(
                xs[idx],
                ys[idx],
                marker="*",
                color=color,
                markersize=12,
                linestyle="None",
                label=f"{curve.pair} peak",
            )
            peaks.append(
                f"{curve.pair} {sweep} {fmt_num(curve.sweep_values[idx])}, "
                f"{quantity} {fmt_num(curve.quantity_values[idx])}"
            )
    if mark_r is not None and sweep == "mixture ratio":
        for pair_name, px, py in mark_states:
            color = COLORS[[c.pair for c in curves].index(pair_name) % len(COLORS)]
            ax.plot(px, py, "o", color=color, markersize=6, linestyle="None")
            r_drawn = True
        if r_drawn:
            if x_name == "mixture ratio":
                ax.axvline(
                    mark_r,
                    color="#7f8c8d",
                    linestyle="--",
                    linewidth=1.0,
                    label=f"r={fmt_num(mark_r)}",
                )
            else:
                ax.axhline(
                    mark_r,
                    color="#7f8c8d",
                    linestyle="--",
                    linewidth=1.0,
                    label=f"r={fmt_num(mark_r)}",
                )
    ax.set_xlabel(LABELS[x_name])
    ax.set_ylabel(LABELS[y_name])
    ax.set_title(f"{y_name} vs {x_name}")
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return peaks


def fixed_inputs(args: argparse.Namespace, required: list[str]) -> dict:
    """Copy only the fixed inputs this plot needs. The swept axis stays unset."""
    key_for = {"r": "r", "pc": "pc_Pa", "eps": "eps", "pa": "pa"}
    limits = {
        "r": lambda v: v > 0,
        "pc": lambda v: v > 0,
        "eps": lambda v: v >= 1.0,
        "pa": lambda v: v >= 0,
    }
    messages = {
        "r": "--r must be > 0",
        "pc": "--pc must be > 0 Pa",
        "eps": "--eps must be >= 1",
        "pa": "--pa must be >= 0 Pa",
    }
    supplied = {"r": args.r, "pc": args.pc, "eps": args.eps, "pa": args.pa}
    out = {"r": None, "pc_Pa": None, "eps": None, "pa": None}
    for name in required:
        value = supplied[name]
        if value is None:
            continue
        if not limits[name](value):
            raise ValueError(messages[name])
        out[key_for[name]] = value
    return out


def run_plots(args: argparse.Namespace) -> int:
    if not args.pair:
        raise ValueError("plot request requires --pair")
    if args.out:
        out_dir = Path(args.out)
        if out_dir.exists() and not out_dir.is_dir():
            raise ValueError("--out must be a directory")
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = SKILL_DIR
    used: set[str] = set()
    for plot_i, spec in enumerate(args.plot):
        y_name, x_name = parse_plot(spec)
        sweep_count = (x_name in SWEEP_AXES) + (y_name in SWEEP_AXES)
        if sweep_count != 1:
            raise ValueError(
                'plot needs exactly one swept axis among mixture ratio, pc, eps, and pa '
                "(neither axis is one of those, or both are free inputs)"
            )
        sweep = x_name if x_name in SWEEP_AXES else y_name
        quantity = y_name if x_name == sweep else x_name
        needs = NEEDS[quantity]
        required = required_fixed(quantity, sweep)
        flags = {"r": "--r", "pc": "--pc", "eps": "--eps", "pa": "--pa"}
        present = {"r": args.r, "pc": args.pc, "eps": args.eps, "pa": args.pa}
        missing = [flags[name] for name in required if present[name] is None]
        if missing:
            raise ValueError(
                f'plot "{y_name} vs {x_name}" requires {", ".join(missing)}'
            )
        fixed = fixed_inputs(args, required)
        pairs = [canonical_pair(raw) for raw in args.pair]
        ranges: list[SweepRange] = []
        if sweep == "mixture ratio":
            for pair in pairs:
                ranges.append(
                    resolve_mixture(
                        pair,
                        args,
                        need_chamber="chamber" in needs,
                        pc_Pa=fixed.get("pc_Pa"),
                    )
                )
        else:
            shared = resolve_shared_range(sweep, args)
            ranges = [shared for _ in pairs]

        curves: list[Curve] = []
        for pair, span in zip(pairs, ranges):
            bars = None
            if sweep == "pc" and "chamber" in needs:
                tables = tables_for_pair(pair)
                if not tables:
                    raise TableError(f"no frozen table for {pair}. Run scripts/build_table.py")
                bars = [table["pc_bar"] for table in tables]
            samples = sample_axis(span, bars=bars)
            curves.append(
                build_curve(pair, quantity, sweep, samples, fixed, args.gamma_source)
            )

        mark_states: list[tuple[str, float, float]] = []
        r_on_plot = False
        if args.r is not None and sweep == "mixture ratio" and args.r > 0:
            for curve, span in zip(curves, ranges):
                if span.lo <= args.r <= span.hi:
                    state = evaluate(
                        curve.pair,
                        r=args.r,
                        pc_Pa=fixed.get("pc_Pa"),
                        eps=fixed.get("eps"),
                        pa=fixed.get("pa"),
                        gamma_source=args.gamma_source,
                        needs=needs,
                    )
                    q = quantity_of(state, quantity)
                    if x_name == "mixture ratio":
                        mark_states.append((curve.pair, args.r, q))
                    else:
                        mark_states.append((curve.pair, q, args.r))
                    r_on_plot = True

        base = slug(f"{y_name} vs {x_name}")
        filename = base + ".png"
        n = 2
        while filename in used:
            filename = f"{base}_{n}.png"
            n += 1
        used.add(filename)
        out_path = (out_dir / filename).resolve()
        peaks = draw_plot(
            out_path,
            x_name,
            y_name,
            sweep,
            quantity,
            curves,
            args.r if r_on_plot else None,
            args.mark_peak,
            mark_states,
        )

        if plot_i:
            print()
        print_kv("plot", f"{y_name} vs {x_name}")
        if sweep != "mixture ratio" and fixed.get("r") is not None:
            print_kv("r", fixed["r"])
        if sweep != "pc" and fixed.get("pc_Pa") is not None:
            print_kv("pc_Pa", fixed["pc_Pa"])
        if sweep != "eps" and fixed.get("eps") is not None:
            print_kv("eps", fixed["eps"])
        if sweep != "pa" and fixed.get("pa") is not None:
            print_kv("pa_Pa", fixed["pa"])
        if "nozzle" in needs:
            print_kv("gamma_source", gamma_source_name(args.gamma_source))
        if sweep == "pc" and "chamber" in needs:
            print_kv("pc_table", "nearest frozen table is re-picked at each chamber pressure")
        for curve in curves:
            print_kv("pair", curve.pair)
            if curve.pc_table_bar is not None:
                print_kv("pc_table_bar", curve.pc_table_bar)
                print_kv("pc_offset_bar", curve.pc_offset_bar)
            if curve.gamma is not None and "nozzle" in needs:
                print_kv("gamma", curve.gamma)
            for warning in curve.warnings:
                print_kv("warning", warning)
        if any(span.assumed for span in ranges):
            if sweep == "mixture ratio":
                print_kv("assumed_range", "; ".join(span.text for span in ranges))
            else:
                print_kv("assumed_range", ranges[0].text)
        if r_on_plot:
            print_kv("mark_r", args.r)
        for peak in peaks:
            print_kv("peak", peak)
        print_kv("graph", str(out_path))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate frozen-CEA rocket performance and optional X-vs-Y plots."
    )
    parser.add_argument("--pair", action="append", default=None, help="oxName/fuelName (repeatable)")
    parser.add_argument("--pc", type=float, default=None, help="chamber pressure [Pa]")
    parser.add_argument("--eps", type=float, default=None, help="exit-to-throat area ratio Ae/At")
    parser.add_argument("--pa", type=float, default=None, help="ambient pressure [Pa]")
    parser.add_argument("--r", type=float, default=None, help="mixture ratio ox/fuel")
    parser.add_argument(
        "--gamma-source",
        choices=("throat", "chamber"),
        default="throat",
        help="gamma used for Me, pe, and Cf (default throat)",
    )
    parser.add_argument(
        "--plot",
        action="append",
        default=None,
        help='repeatable "Y vs X"; the name before vs is the vertical axis',
    )
    parser.add_argument("--r-min", type=float, default=None, help="mixture-ratio sweep minimum")
    parser.add_argument("--r-max", type=float, default=None, help="mixture-ratio sweep maximum")
    parser.add_argument("--pc-min", type=float, default=None, help="chamber-pressure sweep minimum [Pa]")
    parser.add_argument("--pc-max", type=float, default=None, help="chamber-pressure sweep maximum [Pa]")
    parser.add_argument("--eps-min", type=float, default=None, help="area-ratio sweep minimum")
    parser.add_argument("--eps-max", type=float, default=None, help="area-ratio sweep maximum")
    parser.add_argument("--pa-min", type=float, default=None, help="ambient-pressure sweep minimum [Pa]")
    parser.add_argument("--pa-max", type=float, default=None, help="ambient-pressure sweep maximum [Pa]")
    parser.add_argument(
        "--mark-peak",
        action="store_true",
        help="mark the peak of the computed curve",
    )
    parser.add_argument("--out", type=str, default=None, help="directory for plot PNG files")
    args = parser.parse_args(argv)
    if args.pair is None:
        args.pair = []
    if args.plot is None:
        args.plot = []
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        if args.plot:
            return run_plots(args)
        return run_point(args)
    except (TableError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
