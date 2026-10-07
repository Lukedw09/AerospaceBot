#!/usr/bin/env python3
"""Propellant split across stages for an ideal delta-v.

Uses structural_coefficient, mass_ratio_from_payload_and_structure, and
delta_v_vacuum. Modes: equal_dv, equal_mr, max_payload.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

G0 = 9.80665
SKILL_DIR = Path(__file__).resolve().parent
if str(SKILL_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR.parent))
import leo_chart  # noqa: E402

PLOT_TITLE = "Stage propellant split"
ASSUMPTIONS = (
    "gravity-free delta_v_vacuum; c = Isp * g0 with g0 = 9.80665 m/s^2; "
    "structural_coefficient eps = ms/(ms+mp); "
    "Glenn mass_ratio_from_payload_and_structure is m0/mf; "
    "catalogue mass_ratio mf/m0 is the reciprocal; "
    "stage 1 burns first; equal_dv shares the ideal delta-v equally; "
    "equal_mr uses one m0/mf for every stage; "
    "max_payload searches the delta-v split at fixed glow; "
    "payload mode sizes upward from the useful payload; glow mode sizes downward"
)


def print_kv(key: str, value: object) -> None:
    text = f"{value:.8g}" if isinstance(value, float) else str(value)
    print(f"{key}: {text}")


def sigma_of(eps: float) -> float:
    if eps < 0.0 or eps >= 1.0:
        raise ValueError("structural coefficient must lie in [0, 1)")
    return eps / (1.0 - eps)


def size_from_payload(payload: float, dv: float, c: float, eps: float) -> tuple[float, float]:
    if dv <= 0.0 or c <= 0.0 or payload < 0.0:
        raise ValueError("delta-v, exhaust speed, and payload must be positive")
    ratio = math.exp(dv / c)
    sigma = sigma_of(eps)
    denom = 1.0 - (ratio - 1.0) * sigma
    if denom <= 0.0:
        raise ValueError("structural coefficient cannot meet this delta-v")
    mp = (ratio - 1.0) * payload / denom
    return mp, sigma * mp


def payload_from_glow(glow: float, dv: float, c: float, eps: float) -> tuple[float, float, float]:
    ratio = math.exp(dv / c)
    mf = glow / ratio
    mp = glow - mf
    ms = sigma_of(eps) * mp
    return mf - ms, mp, ms


def parse_stage(text: str) -> tuple[float, float]:
    isp = None
    eps = None
    for piece in text.split(","):
        key, raw = piece.split("=", 1)
        if key.strip() == "isp":
            isp = float(raw)
        elif key.strip() == "eps":
            eps = float(raw)
        else:
            raise ValueError(f"unknown stage key {key}")
    if isp is None or eps is None or isp <= 0.0:
        raise ValueError("each stage needs isp and eps")
    return isp * G0, eps


def stack_from_payload(payload: float, dvs: list[float], stages: list[tuple[float, float]]) -> list[dict]:
    rows = []
    carried = payload
    for dv, (c, eps) in zip(reversed(dvs), reversed(stages)):
        mp, inert = size_from_payload(carried, dv, c, eps)
        rows.append({"dv": dv, "c": c, "eps": eps, "mp": mp, "inert": inert, "payload": carried})
        carried = carried + mp + inert
    rows.reverse()
    return rows


def stack_from_glow(glow: float, dvs: list[float], stages: list[tuple[float, float]]) -> list[dict]:
    rows = []
    mass = glow
    for dv, (c, eps) in zip(dvs, stages):
        payload, mp, inert = payload_from_glow(mass, dv, c, eps)
        if payload <= 0.0:
            raise ValueError("glow cannot meet this delta-v")
        rows.append({"dv": dv, "c": c, "eps": eps, "mp": mp, "inert": inert, "payload": payload, "m0": mass})
        mass = payload
    return rows


def max_payload_fractions(glow: float, dv: float, stages: list[tuple[float, float]]) -> list[float]:
    n = len(stages)
    fracs = [1.0 / n] * n

    def score(trial: list[float]) -> float:
        try:
            rows = stack_from_glow(glow, [f * dv for f in trial], stages)
        except ValueError:
            return -1.0
        return rows[-1]["payload"]

    # Coordinate search on the first n-1 fractions.
    for _ in range(4):
        for index in range(n - 1):
            best_f = fracs[index]
            best_s = score(fracs)
            for step in (i / 40.0 for i in range(1, 40)):
                trial = fracs[:]
                trial[index] = step
                remain = 1.0 - step
                others = [j for j in range(n) if j != index]
                share = sum(fracs[j] for j in others)
                if share <= 0.0:
                    for j in others:
                        trial[j] = remain / len(others)
                else:
                    for j in others:
                        trial[j] = fracs[j] / share * remain
                value = score(trial)
                if value > best_s:
                    best_s = value
                    best_f = step
                    fracs = trial
            fracs[index] = best_f
    total = sum(fracs)
    return [f / total for f in fracs]


def run(args: argparse.Namespace) -> int:
    if args.stages < 1 or len(args.stage) != args.stages:
        raise ValueError("pass --stages and one --stage per stage, bottom stage first")
    if args.dv is None or args.dv <= 0.0:
        raise ValueError("delta-v must be > 0")
    if (args.payload is None) == (args.glow is None):
        raise ValueError("pass --payload or --glow, not both")
    stages = [parse_stage(text) for text in args.stage]
    if args.mode == "equal_dv":
        dvs = [args.dv / args.stages] * args.stages
    elif args.mode == "equal_mr":
        # One m0/mf. Sum of c_i * ln(MR) = dv => ln(MR) = dv / sum(c).
        ratio = math.exp(args.dv / sum(c for c, _ in stages))
        dvs = [c * math.log(ratio) for c, _ in stages]
    elif args.mode == "max_payload":
        if args.glow is None:
            raise ValueError("max_payload needs --glow")
        fracs = max_payload_fractions(args.glow, args.dv, stages)
        dvs = [f * args.dv for f in fracs]
    else:
        raise ValueError("unknown mode")
    if args.payload is not None:
        rows = stack_from_payload(args.payload, dvs, stages)
        glow = args.payload + sum(row["mp"] + row["inert"] for row in rows)
        payload = args.payload
    else:
        rows = stack_from_glow(args.glow, dvs, stages)
        glow = args.glow
        payload = rows[-1]["payload"]
    out = Path(args.out).resolve() if args.out else (SKILL_DIR / "stage_propellant_split.png")
    xs = []
    ys = []
    if args.stages == 2 and args.glow is not None:
        for k in range(1, 40):
            frac = k / 40.0
            try:
                sample = stack_from_glow(args.glow, [frac * args.dv, (1.0 - frac) * args.dv], stages)
                xs.append(frac)
                ys.append(sample[-1]["payload"])
            except ValueError:
                continue
    sweep = args.stages == 2 and args.glow is not None and bool(xs)
    if sweep:
        target = dvs[0] / args.dv
        mark = min(range(len(xs)), key=lambda i: abs(xs[i] - target))
        chart = {
            "kind": "series",
            "xs": xs,
            "ys": ys,
            "mark": mark,
            "xlabel": "stage-1 share of ideal delta-v",
            "ylabel": "payload (kg)",
            "seriesName": "payload",
            "markName": "chosen split",
            "note": "The curve is payload against how the ideal delta-v is shared. The red point is this design.",
        }
    else:
        chart_stages = []
        for index, row in enumerate(rows, start=1):
            chart_stages.append(
                {
                    "name": f"stage {index}",
                    "parts": [
                        {"name": "propellant", "value": row["mp"]},
                        {"name": "inert", "value": row["inert"]},
                    ],
                }
            )
        if payload > 0.0:
            chart_stages.append({"name": "payload", "parts": [{"name": "payload", "value": payload}]})
        chart = {
            "kind": "stack",
            "stages": chart_stages,
            "unit": "kg",
            "note": "Propellant and inert for each stage, then the useful payload.",
        }
    leo_chart.write_chart(out, PLOT_TITLE, chart, html=False)
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", args.mode)
    print_kv("g0_m_s2", G0)
    print_kv("dv_m_s", args.dv)
    print_kv("payload_kg", payload)
    print_kv("stacked_mass_kg", glow)
    for index, row in enumerate(rows, start=1):
        mr = math.exp(-row["dv"] / row["c"])
        print_kv(f"stage_{index}_dv_m_s", row["dv"])
        print_kv(f"stage_{index}_isp_s", row["c"] / G0)
        print_kv(f"stage_{index}_eps", row["eps"])
        print_kv(f"stage_{index}_mp_kg", row["mp"])
        print_kv(f"stage_{index}_inert_kg", row["inert"])
        print_kv(f"stage_{index}_MR", mr)
        print_kv(f"payload_to_deltav_stage_{index}", f"mp={row['mp']:.8g},inert={row['inert']:.8g},isp-vac={row['c'] / G0:.8g}")
    print_kv("graph", str(out))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    c = 3000.0
    mp, ms = size_from_payload(100.0, 3000.0, c, 0.1)
    m0 = mp + ms + 100.0
    if abs(c * math.log(m0 / (ms + 100.0)) - 3000.0) > 1e-6:
        return fail("single stage rocket equation")
    payload, mp2, ms2 = payload_from_glow(m0, 3000.0, c, 0.1)
    if abs(payload - 100.0) > 1e-6 or abs(mp2 - mp) > 1e-6:
        return fail("glow inverse")
    rows = stack_from_payload(100.0, [1500.0, 1500.0], [(c, 0.1), (c, 0.1)])
    if abs(rows[0]["dv"] - rows[1]["dv"]) > 1e-9:
        return fail("equal dv")
    import io
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        png = str(Path(tmp) / "out.png")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(
                [
                    "--stages", "1",
                    "--stage", "isp=300,eps=0.1",
                    "--dv", "3000",
                    "--payload", "100",
                    "--mode", "equal_dv",
                    "--out", png,
                ]
            )
        finally:
            sys.stdout = old
        if code != 0 or "payload_kg:" not in buf.getvalue():
            return fail("cli")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stage propellant split.")
    parser.add_argument("--stages", type=int)
    parser.add_argument("--stage", action="append", default=[])
    parser.add_argument("--dv", type=float)
    parser.add_argument("--payload", type=float, default=None)
    parser.add_argument("--glow", type=float, default=None)
    parser.add_argument("--mode", choices=("equal_dv", "equal_mr", "max_payload"), default="equal_dv")
    parser.add_argument("--out", default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.stages is None:
        print("stages is required", file=sys.stderr)
        return 2
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
