#!/usr/bin/env python3
"""Stage inert mass for PayloadtoDeltaV.

structure_mass_linear when k is given. Otherwise the inert is the sum of the
stated components.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
CHART_DIR = SKILL_DIR.parents[1] / "app" / "tests"
if str(CHART_DIR) not in sys.path:
    sys.path.insert(0, str(CHART_DIR))
import leo_chart  # noqa: E402

PLOT_TITLE = "Vehicle mass budget"
CHECK_TOL = 1e-9
ASSUMPTIONS = (
    "stage 1 is the bottom stage; "
    "if k is set, structure_mass_linear ms = mH + k*mp and explicit component "
    "masses are not added; "
    "otherwise inert is tank + engines + fairing + interstage + other + mH + "
    "residuals; "
    "residuals are inert; "
    "stacked mass is useful payload plus every stage propellant and inert; "
    "payload_to_deltav_stage is the mp,inert string for ROCKET - PayloadtoDeltaV"
)


@dataclass
class Stage:
    mp: float
    inert: float
    parts: list[tuple[str, float]]
    law: str


def print_kv(key: str, value: object) -> None:
    text = f"{value:.8g}" if isinstance(value, float) else str(value)
    print(f"{key}: {text}")


def parse_stage(text: str) -> Stage:
    keys: dict[str, float] = {}
    for piece in text.split(","):
        if "=" not in piece:
            raise ValueError(f"stage entry {piece!r} needs key=value")
        key, raw = piece.split("=", 1)
        key = key.strip()
        allowed = {
            "mp", "tank", "engine-mass", "engine-count", "fairing", "interstage",
            "other", "mH", "k", "residuals",
        }
        if key not in allowed:
            raise ValueError(f"unknown stage key {key}")
        keys[key] = float(raw)
    if "mp" not in keys or keys["mp"] <= 0.0:
        raise ValueError("each stage needs mp > 0")
    residuals = keys.get("residuals", 0.0)
    if residuals < 0.0:
        raise ValueError("residuals must be >= 0")
    if "k" in keys:
        extra = [name for name in ("tank", "engine-mass", "engine-count", "fairing", "interstage", "other") if name in keys]
        if extra:
            raise ValueError("k cannot be combined with " + ", ".join(extra))
        m_h = keys.get("mH", 0.0)
        if m_h < 0.0 or keys["k"] < 0.0:
            raise ValueError("mH and k must be >= 0")
        structure = m_h + keys["k"] * keys["mp"]
        inert = structure + residuals
        parts = [("structure", structure), ("residuals", residuals), ("propellant", keys["mp"])]
        return Stage(keys["mp"], inert, parts, "linear")
    def get(name: str) -> float:
        value = keys.get(name, 0.0)
        if value < 0.0:
            raise ValueError(f"{name} must be >= 0")
        return value
    engines = get("engine-mass") * (keys.get("engine-count", 1.0) if "engine-mass" in keys else 0.0)
    if "engine-count" in keys and "engine-mass" not in keys:
        raise ValueError("engine-count requires engine-mass")
    tank = get("tank")
    fairing = get("fairing")
    interstage = get("interstage")
    other = get("other")
    hardware = get("mH")
    inert = tank + engines + fairing + interstage + other + hardware + residuals
    parts = [
        ("tanks", tank),
        ("engines", engines),
        ("fairing", fairing),
        ("interstage", interstage),
        ("other", other + hardware + residuals),
        ("propellant", keys["mp"]),
    ]
    return Stage(keys["mp"], inert, parts, "explicit")


def run(args: argparse.Namespace) -> int:
    if args.stages < 1:
        raise ValueError("stages must be >= 1")
    if len(args.stage) != args.stages:
        raise ValueError("pass one --stage per stage, bottom stage first")
    stages = [parse_stage(text) for text in args.stage]
    payload = 0.0 if args.payload is None else args.payload
    if payload < 0.0:
        raise ValueError("payload must be >= 0")
    stacked = payload + sum(stage.mp + stage.inert for stage in stages)
    out = Path(args.out).resolve() if args.out else (SKILL_DIR / "vehicle_mass_budget.png")
    chart_stages = []
    for index, stage in enumerate(stages, start=1):
        chart_stages.append(
            {
                "name": f"stage {index}",
                "parts": [{"name": name, "value": value} for name, value in stage.parts if value > 0.0],
            }
        )
    if payload > 0.0:
        chart_stages.append({"name": "payload", "parts": [{"name": "payload", "value": payload}]})
    leo_chart.write_chart(
        out,
        PLOT_TITLE,
        {
            "kind": "stack",
            "stages": chart_stages,
            "unit": "kg",
            "note": "Each color is one mass item. Empty items are omitted.",
        },
        html=False,
    )
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("stages", args.stages)
    print_kv("payload_kg", payload)
    above = payload
    for index, stage in enumerate(stages, start=1):
        print_kv(f"stage_{index}_law", stage.law)
        print_kv(f"stage_{index}_mp_kg", stage.mp)
        print_kv(f"stage_{index}_inert_kg", stage.inert)
        print_kv(f"stage_{index}_m0_kg", above + stage.mp + stage.inert)
        print_kv(f"payload_to_deltav_stage_{index}", f"mp={stage.mp:.8g},inert={stage.inert:.8g}")
        above += stage.mp + stage.inert
    print_kv("stacked_mass_kg", stacked)
    print_kv("graph", str(out))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    import io
    import tempfile

    linear = parse_stage("mp=100,k=0.1,mH=10,residuals=2")
    if abs(linear.inert - 22.0) > CHECK_TOL:
        return fail("linear inert")
    explicit = parse_stage("mp=50,tank=5,engine-mass=2,engine-count=2,fairing=1,interstage=1,other=1,residuals=0.5")
    if abs(explicit.inert - (5 + 4 + 1 + 1 + 1 + 0.5)) > CHECK_TOL:
        return fail("explicit inert")
    with tempfile.TemporaryDirectory() as tmp:
        png = str(Path(tmp) / "out.png")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(["--stages", "1", "--stage", "mp=100,k=0.1,mH=10", "--payload", "5", "--out", png])
        finally:
            sys.stdout = old
        text = buf.getvalue()
        if code != 0 or "stacked_mass_kg: 125" not in text:
            return fail(text or "cli")
        if not Path(png).is_file():
            return fail("png")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vehicle mass budget.")
    parser.add_argument("--stages", type=int)
    parser.add_argument("--stage", action="append", default=[])
    parser.add_argument("--payload", type=float, default=None)
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
