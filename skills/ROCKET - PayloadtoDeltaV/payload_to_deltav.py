#!/usr/bin/env python3
"""Payload mass versus ideal delta-v for one or more rocket stages.

delta-v is delta_v_vacuum (formulas.md) at constant effective exhaust velocity.
c = Isp * g0 from specific_impulse. Ambient specific impulse follows
specific_impulse_exit: the pressure term is linear in ambient pressure between
the vacuum and sea-level values. Stage 1 burns first. Each upper stage is part
of the payload of the stages below it.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

# 1976 standard sea-level gravity and pressure (formulas.md, Atmosphere).
# g0 converts specific impulse in seconds to effective exhaust velocity.
G0 = 9.80665
P0 = 101325.0
PLOT_TITLE = "Payload mass versus delta-v"
N_SAMPLES = 201
CHECK_TOL = 1e-8
ASSUMPTIONS = (
    "ideal delta-v from delta_v_vacuum: gravity-free, drag-free, constant "
    "effective exhaust velocity, initial velocity 0; c = Isp * g0 from "
    "specific_impulse; stage 1 burns first; each upper stage is part of the "
    "payload of the stages below it and its inert mass is dropped after it "
    "burns; useful payload is the mass above the last modeled stage and is "
    "not dropped; residual propellant is part of inert mass; Isp at ambient "
    "pressure follows specific_impulse_exit and is linear in ambient pressure "
    "between the vacuum and sea-level values; one ambient pressure per stage, "
    "held constant over that burn; g0 = 9.80665 m/s^2; sea-level pressure = "
    "101325 Pa"
)


@dataclass(frozen=True)
class StageInput:
    mp: float
    inert: float
    isp_sl: float | None
    isp_vac: float | None
    pa: float | None


@dataclass(frozen=True)
class StageOperating:
    isp: float
    c: float
    pa: float
    pa_source: str
    condition: str


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def linspace(lo: float, hi: float, count: int) -> list[float]:
    if count < 2:
        raise ValueError("need at least 2 delta-v samples")
    step = (hi - lo) / (count - 1)
    values = [lo + step * i for i in range(count)]
    values[-1] = hi
    return values


def parse_stage(text: str, index: int) -> StageInput:
    """Parse mp=, inert=, and optional isp-sl=, isp-vac=, pa=."""
    found: dict[str, float] = {}
    for part in text.split(","):
        item = part.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"stage {index}: {item!r} must be key=value")
        key, raw = item.split("=", 1)
        key = key.strip().lower()
        if key not in {"mp", "inert", "isp-sl", "isp-vac", "pa"}:
            raise ValueError(f"stage {index}: unknown key {key}")
        if key in found:
            raise ValueError(f"stage {index}: repeated {key}")
        try:
            value = float(raw.strip())
        except ValueError as exc:
            raise ValueError(f"stage {index}: {key} is not a number") from exc
        if not math.isfinite(value):
            raise ValueError(f"stage {index}: {key} must be finite")
        found[key] = value

    if "mp" not in found or "inert" not in found:
        raise ValueError(f"stage {index}: mp and inert are required")
    if "isp-sl" not in found and "isp-vac" not in found:
        raise ValueError(f"stage {index}: isp-sl or isp-vac is required")
    if found["mp"] <= 0:
        raise ValueError(f"stage {index}: mp must be > 0 kg")
    if found["inert"] <= 0:
        raise ValueError(f"stage {index}: inert must be > 0 kg")
    for key in ("isp-sl", "isp-vac"):
        if key in found and found[key] <= 0:
            raise ValueError(f"stage {index}: {key} must be > 0 s")
    if "pa" in found and found["pa"] < 0:
        raise ValueError(f"stage {index}: pa must be >= 0 Pa")

    return StageInput(
        mp=found["mp"],
        inert=found["inert"],
        isp_sl=found.get("isp-sl"),
        isp_vac=found.get("isp-vac"),
        pa=found.get("pa"),
    )


def isp_at_pressure(isp_sl: float, isp_vac: float, pa: float) -> float:
    """Operating Isp from specific_impulse_exit.

    Is(p3) = Is_vac - (Is_vac - Is_sl) * (p3 / p0), because the pressure
    thrust changes linearly with ambient pressure at fixed exit pressure,
    exit area, and mass flow.
    """
    if isp_vac < isp_sl:
        raise ValueError("isp-vac must be >= isp-sl")
    return isp_vac - (isp_vac - isp_sl) * (pa / P0)


def isp_condition(pa: float) -> str:
    if pa == 0.0:
        return "vacuum"
    if math.isclose(pa, P0, rel_tol=1e-9, abs_tol=0.0):
        return "sea level"
    return "ambient"


def operating_state(stage: StageInput, index: int) -> StageOperating:
    sl = stage.isp_sl
    vac = stage.isp_vac
    pa_in = stage.pa
    if sl is not None and vac is not None:
        if vac < sl:
            raise ValueError(f"stage {index}: isp-vac must be >= isp-sl")
        if pa_in is None:
            raise ValueError(
                f"stage {index}: pa is required when both sea-level and "
                "vacuum specific impulse are given"
            )
        isp = isp_at_pressure(sl, vac, pa_in)
        pa = pa_in
        source = "input"
    elif sl is not None:
        if pa_in is None:
            pa = P0
            source = "sea-level reference"
        elif isp_condition(pa_in) == "sea level":
            pa = pa_in
            source = "input"
        else:
            raise ValueError(
                f"stage {index}: sea-level specific impulse at another "
                "ambient needs isp-vac as well"
            )
        isp = sl
    elif vac is not None:
        if pa_in is None or pa_in == 0.0:
            pa = 0.0
            source = "input" if pa_in is not None else "vacuum reference"
        else:
            raise ValueError(
                f"stage {index}: vacuum specific impulse at another ambient "
                "needs isp-sl as well"
            )
        isp = vac
    else:
        raise ValueError(f"stage {index}: isp-sl or isp-vac is required")

    if isp <= 0:
        raise ValueError(
            f"stage {index}: specific impulse is not positive at that ambient pressure"
        )
    return StageOperating(
        isp=isp,
        c=isp * G0,
        pa=pa,
        pa_source=source,
        condition=isp_condition(pa),
    )


def evaluate(stages: list[StageInput], ops: list[StageOperating], useful: float) -> tuple[float, list[dict]]:
    """Ideal stage delta-v with each upper stage inside the lower-stage payload."""
    payloads = [0.0] * len(stages)
    above = useful
    for i in reversed(range(len(stages))):
        payloads[i] = above
        above += stages[i].mp + stages[i].inert

    total = 0.0
    rows: list[dict] = []
    for i, (stage, op) in enumerate(zip(stages, ops), start=1):
        payload_i = payloads[i - 1]
        mf = stage.inert + payload_i
        if mf <= 0:
            raise ValueError(
                f"stage {i}: final mass must be positive; payload must be "
                f"greater than {-stage.inert:g} kg"
            )
        m0 = stage.mp + mf
        dv = op.c * math.log(m0 / mf)
        total += dv
        rows.append(
            {
                "index": i,
                "payload": payload_i,
                "m0": m0,
                "mf": mf,
                "mr": mf / m0,
                "dv": dv,
            }
        )
    return total, rows


def vehicle_dv(stages: list[StageInput], ops: list[StageOperating], useful: float) -> float:
    total, _rows = evaluate(stages, ops, useful)
    return total


def payload_for_dv(stages: list[StageInput], ops: list[StageOperating], dv_target: float) -> float:
    """Useful payload whose ideal delta-v equals dv_target.

    Delta-v falls as useful payload rises, so the root is unique.
    """
    if dv_target <= 0 or not math.isfinite(dv_target):
        raise ValueError("delta-v must be > 0")
    dv_zero = vehicle_dv(stages, ops, 0.0)
    if math.isclose(dv_target, dv_zero, rel_tol=1e-12, abs_tol=1e-8):
        return 0.0

    if dv_target > dv_zero:
        top_inert = stages[-1].inert
        lo = max(top_inert * 1e-12, 1e-15) - top_inert
        if lo >= 0.0:
            raise ValueError("delta-v is above the ideal delta-v at zero payload")
        if vehicle_dv(stages, ops, lo) < dv_target:
            raise ValueError(
                "delta-v is above what this rocket can reach with a positive top-stage final mass"
            )
        hi = 0.0
    else:
        lo = 0.0
        stacked = sum(stage.mp + stage.inert for stage in stages)
        hi = max(stacked, 1.0)
        guard = 0
        while vehicle_dv(stages, ops, hi) > dv_target:
            hi *= 2.0
            guard += 1
            if guard > 80 or not math.isfinite(hi):
                raise ValueError("could not bracket payload for the given delta-v")

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        dv_mid = vehicle_dv(stages, ops, mid)
        if math.isclose(dv_mid, dv_target, rel_tol=1e-12, abs_tol=1e-8):
            return mid
        if dv_mid > dv_target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def payload_closed_form(mp: float, inert: float, c: float, dv: float) -> float:
    """Single-stage payload from delta_v_vacuum and m0 = mp + mf, mf = inert + payload."""
    return mp / math.expm1(dv / c) - inert


def negative_payload(payload: float) -> bool:
    return payload < 0.0 and not math.isclose(payload, 0.0, rel_tol=1e-8, abs_tol=1e-8)


def print_stage_inputs(stages: list[StageInput], ops: list[StageOperating]) -> None:
    for i, (stage, op) in enumerate(zip(stages, ops), start=1):
        print_kv(f"stage_{i}_mp_kg", stage.mp)
        print_kv(f"stage_{i}_inert_kg", stage.inert)
        if stage.isp_sl is not None:
            print_kv(f"stage_{i}_Isp_sl_s", stage.isp_sl)
        if stage.isp_vac is not None:
            print_kv(f"stage_{i}_Isp_vac_s", stage.isp_vac)
        print_kv(f"stage_{i}_pa_Pa", op.pa)
        print_kv(f"stage_{i}_pa_source", op.pa_source)
        print_kv(f"stage_{i}_Isp_s", op.isp)
        print_kv(f"stage_{i}_isp_condition", op.condition)
        print_kv(f"stage_{i}_c_m_s", op.c)


def print_stage_results(prefix: str, rows: list[dict]) -> None:
    for row in rows:
        i = row["index"]
        base = f"{prefix}stage_{i}_"
        print_kv(f"{base}payload_kg", row["payload"])
        print_kv(f"{base}m0_kg", row["m0"])
        print_kv(f"{base}mf_kg", row["mf"])
        print_kv(f"{base}MR", row["mr"])
        print_kv(f"{base}dv_m_s", row["dv"])


def print_header(stages: list[StageInput], ops: list[StageOperating], mode: str) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", mode)
    print_kv("stages", len(stages))
    print_kv("g0_m_s2", G0)
    print_kv("p0_Pa", P0)
    print_stage_inputs(stages, ops)


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError(
            "matplotlib is required to plot payload mass versus delta-v"
        ) from exc
    return plt


def plot_curve(
    path: Path,
    dv_values: list[float],
    payload_values: list[float],
    mark_zero: bool,
) -> None:
    plt = ensure_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        dv_values,
        payload_values,
        color="#1a5276",
        linewidth=1.8,
        label="payload mass",
    )
    if mark_zero:
        ax.plot(
            dv_values[-1],
            0.0,
            "s",
            color="#27ae60",
            markersize=7,
            zorder=5,
            label="zero payload",
        )
    if any(value < 0.0 for value in payload_values):
        ax.axhline(0.0, color="#7f8c8d", linestyle="--", linewidth=1.0)
    ax.set_xlabel("delta-v (m/s)")
    ax.set_ylabel("payload mass (kg)")
    ax.set_title(PLOT_TITLE)
    ax.set_xlim(dv_values[0], dv_values[-1])
    if min(payload_values) >= 0.0:
        ymax = max(payload_values)
        ax.set_ylim(0.0, ymax * 1.05 if ymax > 0.0 else 1.0)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=9)
    fig.tight_layout()
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def load_stages(ns: argparse.Namespace) -> tuple[list[StageInput], list[StageOperating]]:
    if ns.stages is None:
        raise ValueError("--stages is required")
    if ns.stages < 1:
        raise ValueError("--stages must be >= 1")
    texts = ns.stage or []
    if len(texts) != ns.stages:
        raise ValueError(
            f"--stages is {ns.stages} but {len(texts)} --stage value(s) were given"
        )
    stages = [parse_stage(text, i) for i, text in enumerate(texts, start=1)]
    ops = [operating_state(stage, i) for i, stage in enumerate(stages, start=1)]
    return stages, ops


def reject_sweep_flags(ns: argparse.Namespace) -> None:
    used = []
    if ns.dv_min is not None:
        used.append("--dv-min")
    if ns.dv_max is not None:
        used.append("--dv-max")
    if ns.out is not None:
        used.append("--out")
    if used:
        raise ValueError(
            f"{', '.join(used)} apply only when delta-v is swept "
            "(omit --dv and --payload)"
        )


def run_point(ns: argparse.Namespace, stages: list[StageInput], ops: list[StageOperating]) -> int:
    reject_sweep_flags(ns)
    dv_zero = vehicle_dv(stages, ops, 0.0)
    have_dv = ns.dv is not None
    have_payload = ns.payload is not None
    if have_dv and (ns.dv <= 0 or not math.isfinite(ns.dv)):
        raise ValueError("--dv must be > 0")
    if have_payload and (ns.payload < 0 or not math.isfinite(ns.payload)):
        raise ValueError("--payload must be >= 0 kg")

    if have_dv and have_payload:
        mode = "both"
    elif have_dv:
        mode = "payload"
    else:
        mode = "deltav"

    print_header(stages, ops, mode)
    print_kv("dv_zero_payload_m_s", dv_zero)

    if have_payload:
        dv_at_payload, rows_payload = evaluate(stages, ops, ns.payload)
        if mode == "deltav":
            print_kv("payload_kg", ns.payload)
            print_kv("payload_source", "input")
            print_kv("dv_m_s", dv_at_payload)
            print_kv("dv_source", "solved")
            print_stage_results("", rows_payload)
        else:
            print_kv("payload_kg", ns.payload)
            print_kv("payload_source", "input")
            print_kv("dv_at_payload_m_s", dv_at_payload)
            print_stage_results("at_payload_", rows_payload)

    if have_dv:
        solved = payload_for_dv(stages, ops, ns.dv)
        _dv_back, rows_dv = evaluate(stages, ops, solved)
        if mode == "payload":
            print_kv("dv_m_s", ns.dv)
            print_kv("dv_source", "input")
            print_kv("payload_kg", solved)
            print_kv("payload_source", "solved")
            print_stage_results("", rows_dv)
        else:
            print_kv("dv_m_s", ns.dv)
            print_kv("dv_source", "input")
            print_kv("payload_at_dv_kg", solved)
            print_stage_results("at_dv_", rows_dv)
        if negative_payload(solved):
            print_kv(
                "warning",
                "payload is negative, so this delta-v is above the ideal "
                "delta-v at zero payload",
            )
    return 0


def run_sweep(ns: argparse.Namespace, stages: list[StageInput], ops: list[StageOperating]) -> int:
    dv_zero = vehicle_dv(stages, ops, 0.0)
    stacked = sum(stage.mp + stage.inert for stage in stages)
    dv_stacked = vehicle_dv(stages, ops, stacked)
    assumed_low = ns.dv_min is None
    assumed_high = ns.dv_max is None
    dv_min = dv_stacked if assumed_low else ns.dv_min
    dv_max = dv_zero if assumed_high else ns.dv_max
    if dv_min <= 0 or dv_max <= 0 or not math.isfinite(dv_min) or not math.isfinite(dv_max):
        raise ValueError("delta-v sweep limits must be > 0")
    if dv_min >= dv_max:
        raise ValueError("--dv-min must be < --dv-max")

    samples = linspace(dv_min, dv_max, N_SAMPLES)
    payloads = [payload_for_dv(stages, ops, dv) for dv in samples]
    script_dir = Path(__file__).resolve().parent
    out_path = Path(ns.out) if ns.out else script_dir / "payload_vs_deltav.png"
    out_path = out_path.resolve()
    mark_zero = math.isclose(dv_max, dv_zero, rel_tol=1e-8, abs_tol=1e-6)
    plot_curve(out_path, samples, payloads, mark_zero)

    print_header(stages, ops, "sweep")
    print_kv("dv_zero_payload_m_s", dv_zero)
    print_kv("stacked_mass_kg", stacked)
    print_kv("dv_min_m_s", dv_min)
    print_kv("dv_max_m_s", dv_max)
    print_kv("payload_at_dv_min_kg", payloads[0])
    print_kv("payload_at_dv_max_kg", payloads[-1])
    assumed_notes = []
    if assumed_low:
        assumed_notes.append(
            "low end is the ideal delta-v at a payload equal to stacked propellant plus inert"
        )
    if assumed_high:
        assumed_notes.append("high end is the ideal delta-v at zero payload")
    if assumed_notes:
        print_kv(
            "assumed_range",
            f"dv {dv_min:.8g} to {dv_max:.8g} m/s; " + "; ".join(assumed_notes),
        )
    if any(negative_payload(value) for value in payloads):
        print_kv(
            "warning",
            "part of the delta-v sweep is above the ideal delta-v at zero "
            "payload, so payload is negative there",
        )
    print_kv("graph", str(out_path))
    return 0


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    # delta_v_vacuum identity: m0/mf = e => dv = c. Payload 0, inert 1, mp = e - 1.
    c_ref = 3000.0
    isp_ref = c_ref / G0
    mp_e = math.e - 1.0
    stage_e = StageInput(mp_e, 1.0, None, isp_ref, None)
    op_e = operating_state(stage_e, 1)
    if abs(op_e.c - c_ref) > 1e-9:
        return fail(f"c = {op_e.c}, expected {c_ref}")
    if op_e.condition != "vacuum" or op_e.pa != 0.0:
        return fail("vacuum reference did not set pa = 0")
    dv_e = vehicle_dv([stage_e], [op_e], 0.0)
    if abs(dv_e - c_ref) > 1e-6:
        return fail(f"dv at m0/mf = e is {dv_e}, expected {c_ref}")
    if abs(payload_for_dv([stage_e], [op_e], c_ref)) > 1e-6:
        return fail("payload at dv = c was not 0")

    # Closed form: payload 5 kg, inert 10 kg, mp 100 kg.
    mp = 100.0
    inert = 10.0
    useful = 5.0
    stage = StageInput(mp, inert, None, isp_ref, 0.0)
    op = operating_state(stage, 1)
    dv = vehicle_dv([stage], [op], useful)
    expected_dv = c_ref * math.log((mp + inert + useful) / (inert + useful))
    if abs(dv - expected_dv) > CHECK_TOL * c_ref:
        return fail(f"single-stage dv = {dv}, expected {expected_dv}")
    closed = payload_closed_form(mp, inert, c_ref, dv)
    solved = payload_for_dv([stage], [op], dv)
    if abs(closed - useful) > 1e-8:
        return fail(f"closed-form payload = {closed}, expected {useful}")
    if abs(solved - useful) > 1e-6:
        return fail(f"solved payload = {solved}, expected {useful}")

    # specific_impulse_exit: halfway ambient is the mean of sea level and vacuum.
    half = StageInput(mp, inert, 200.0, 300.0, P0 / 2.0)
    op_half = operating_state(half, 1)
    if abs(op_half.isp - 250.0) > 1e-9:
        return fail(f"halfway Isp = {op_half.isp}, expected 250")
    if op_half.condition != "ambient":
        return fail(f"halfway condition = {op_half.condition}")
    sl = operating_state(StageInput(mp, inert, 200.0, 300.0, P0), 1)
    vac = operating_state(StageInput(mp, inert, 200.0, 300.0, 0.0), 1)
    if abs(sl.isp - 200.0) > 1e-9 or sl.condition != "sea level":
        return fail("sea-level endpoint")
    if abs(vac.isp - 300.0) > 1e-9 or vac.condition != "vacuum":
        return fail("vacuum endpoint")
    if vehicle_dv([half], [op_half], useful) >= vehicle_dv(
        [StageInput(mp, inert, None, 300.0, None)],
        [operating_state(StageInput(mp, inert, None, 300.0, None), 1)],
        useful,
    ):
        return fail("ambient delta-v was not below vacuum delta-v")

    # Two stages. Upper stage is the payload of the first stage.
    # Stage 2: mp=2, inert=1, useful=1 => m0=4, mf=2
    # Stage 1: payload=4, mp=3, inert=1 => m0=8, mf=5
    c_stage = 1000.0
    isp_stage = c_stage / G0
    lower = StageInput(3.0, 1.0, None, isp_stage, None)
    upper = StageInput(2.0, 1.0, None, isp_stage, None)
    ops = [operating_state(lower, 1), operating_state(upper, 2)]
    dv_two, rows = evaluate([lower, upper], ops, 1.0)
    expected_two = c_stage * (math.log(8.0 / 5.0) + math.log(2.0))
    if abs(rows[0]["payload"] - 4.0) > 1e-12:
        return fail("stage 1 payload is not the upper stage at ignition")
    if abs(rows[1]["payload"] - 1.0) > 1e-12:
        return fail("stage 2 payload is not the useful payload")
    if abs(dv_two - expected_two) > 1e-6:
        return fail(f"two-stage dv = {dv_two}, expected {expected_two}")
    if abs(payload_for_dv([lower, upper], ops, dv_two) - 1.0) > 1e-6:
        return fail("two-stage payload solve did not return 1 kg")
    if rows[0]["mr"] >= 1.0 or rows[1]["mr"] >= 1.0:
        return fail("mass ratio must be mf/m0 < 1")

    # Stage 1 lifts both stages above it. Useful payload is 1 kg.
    # Stage 3 payload = 1. Stage 2 payload = 1+2+1 = 4.
    # Stage 1 payload = 4+3+1 = 8.
    third = StageInput(2.0, 1.0, None, isp_stage, None)
    second = StageInput(3.0, 1.0, None, isp_stage, None)
    first = StageInput(4.0, 1.0, None, isp_stage, None)
    _dv_three, rows3 = evaluate(
        [first, second, third],
        [operating_state(first, 1), operating_state(second, 2), operating_state(third, 3)],
        1.0,
    )
    if [row["payload"] for row in rows3] != [8.0, 4.0, 1.0]:
        return fail(f"three-stage payloads = {[row['payload'] for row in rows3]}")

    # Above the zero-payload delta-v, useful payload is negative.
    over = payload_for_dv([stage_e], [op_e], c_ref * 1.05)
    if over >= 0.0:
        return fail("over-speed payload was not negative")
    if abs(vehicle_dv([stage_e], [op_e], over) - c_ref * 1.05) > 1e-4:
        return fail("negative payload did not recover the requested delta-v")

    try:
        operating_state(StageInput(1.0, 1.0, 300.0, None, 0.0), 1)
    except ValueError:
        pass
    else:
        return fail("sea-level Isp at vacuum ambient was accepted")
    try:
        operating_state(StageInput(1.0, 1.0, 300.0, 200.0, P0), 1)
    except ValueError:
        pass
    else:
        return fail("isp-vac below isp-sl was accepted")

    print("check: pass")
    print_kv("single_stage_dv_m_s", dv)
    print_kv("single_stage_payload_kg", solved)
    print_kv("two_stage_dv_m_s", dv_two)
    print_kv("halfway_Isp_s", op_half.isp)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Payload mass versus ideal delta-v, or delta-v from payload."
    )
    parser.add_argument("--stages", type=int, default=None, help="number of modeled stages")
    parser.add_argument(
        "--stage",
        action="append",
        default=None,
        help=(
            "repeatable stage string, bottom stage first; comma-separated key=value; "
            "keys: mp (kg, required), inert (kg, required), "
            "isp-sl (s), isp-vac (s; need isp-sl and/or isp-vac), "
            "pa (Pa; required when both Isp values are given); "
            "example: mp=20000,inert=2000,isp-vac=300"
        ),
    )
    parser.add_argument("--dv", type=float, default=None, help="ideal delta-v [m/s]; solve payload")
    parser.add_argument(
        "--payload",
        type=float,
        default=None,
        help="useful payload above the last stage [kg]; solve delta-v",
    )
    parser.add_argument("--dv-min", type=float, default=None, help="sweep minimum delta-v [m/s]")
    parser.add_argument("--dv-max", type=float, default=None, help="sweep maximum delta-v [m/s]")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="PNG path for the payload-versus-delta-v sweep",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    args = parser.parse_args(argv)
    if args.stage is None:
        args.stage = []
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        stages, ops = load_stages(args)
        if args.dv is None and args.payload is None:
            return run_sweep(args, stages, ops)
        return run_point(args, stages, ops)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
