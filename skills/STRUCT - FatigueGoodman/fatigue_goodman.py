#!/usr/bin/env python3
"""Infinite-life Goodman and Soderberg lines.

goodman_factor is 1/(sa/se + sm/sut).
soderberg_factor is 1/(sa/se + sm/sy).
goodman_allowable_alternating is se*(1 - sm/sut); Soderberg uses yield
in that same intercept.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "one cycle shape; alternating stress >= 0; tensile mean stress "
    "below the intercept; Goodman n = 1/(sa/se + sm/sut) from the "
    "straight line of NASA TN D-3883; Soderberg n = 1/(sa/se + sm/sy); "
    "sa_allow at n = 1 is se*(1 - sm/intercept); "
    "Miner sums and crack growth are omitted"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= CHECK_TOL * scale


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def factor(sa: float, se: float, sm: float, intercept: float) -> float:
    return 1.0 / (sa / se + sm / intercept)


def allowable_alternating(se: float, sm: float, intercept: float) -> float:
    return se * (1.0 - sm / intercept)


def solve(
    criterion: str,
    sa: float,
    sm: float,
    se: float,
    intercept: float,
    n_required: float | None,
) -> dict[str, object]:
    if sa < 0.0 or not math.isfinite(sa):
        raise ValueError("sigma-a must be finite and >= 0")
    if sm < 0.0 or not math.isfinite(sm):
        raise ValueError("sigma-m must be finite and >= 0")
    require_positive("se", se)
    require_positive("intercept", intercept)
    name = "sut" if criterion == "goodman" else "sy"
    equation = (
        "n = 1/(sa/se + sm/sut)"
        if criterion == "goodman"
        else "n = 1/(sa/se + sm/sy)"
    )
    if sm >= intercept:
        status = "fail"
        n_value = float("nan")
        sa_allow = float("nan")
    else:
        n_value = factor(sa, se, sm, intercept)
        sa_allow = allowable_alternating(se, sm, intercept)
        need = 1.0 if n_required is None else n_required
        status = "pass" if n_value + 1e-12 >= need else "fail"
    result: dict[str, object] = {
        "criterion": criterion,
        "equation": equation,
        "sigma_a_Pa": sa,
        "sigma_m_Pa": sm,
        "se_Pa": se,
        "intercept_name": name,
        "intercept_Pa": intercept,
        "n": n_value,
        "sa_allow_Pa": sa_allow,
        "status": status,
    }
    if n_required is not None:
        result["n_required"] = n_required
    return result


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key in (
        "criterion",
        "equation",
        "sigma_a_Pa",
        "sigma_m_Pa",
        "se_Pa",
        "intercept_name",
        "intercept_Pa",
        "n",
        "n_required",
        "sa_allow_Pa",
        "status",
    ):
        if key in result:
            print_kv(key, result[key])
    print_kv("graph", str(graph))


def write_plot(result: dict[str, object], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    se = float(result["se_Pa"])
    intercept = float(result["intercept_Pa"])
    sm = float(result["sigma_m_Pa"])
    sa = float(result["sigma_a_Pa"])
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    ax.plot([0.0, intercept], [se, 0.0], color="C0", label=str(result["criterion"]))
    ax.plot([sm], [sa], "o", color="C3", label="load")
    ax.set_xlim(0.0, intercept * 1.05)
    ax.set_ylim(0.0, max(se, sa) * 1.15)
    ax.set_xlabel(r"Mean stress $\sigma_m$ [Pa]")
    ax.set_ylabel(r"Alternating stress $\sigma_a$ [Pa]")
    ax.set_title(str(result["criterion"]))
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    goodman = solve("goodman", 100.0, 100.0, 200.0, 400.0, None)
    if not close(float(goodman["n"]), 1.0 / (0.5 + 0.25)):
        return fail(f"goodman n {goodman['n']}")
    if not close(float(goodman["sa_allow_Pa"]), 150.0):
        return fail("goodman allowable")
    if goodman["status"] != "pass":
        return fail("goodman status")
    soderberg = solve("soderberg", 100.0, 100.0, 200.0, 300.0, None)
    if not close(float(soderberg["n"]), 1.0 / (0.5 + 100.0 / 300.0)):
        return fail(f"soderberg n {soderberg['n']}")
    over = solve("goodman", 100.0, 100.0, 200.0, 400.0, 2.0)
    if over["status"] != "fail":
        return fail("required n was not enforced")
    past = solve("goodman", 10.0, 400.0, 200.0, 400.0, None)
    if past["status"] != "fail":
        return fail("mean at ultimate should fail")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(goodman, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("n_goodman", float(goodman["n"]))
    print_kv("n_soderberg", float(soderberg["n"]))
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Goodman or Soderberg infinite-life check.")
    parser.add_argument(
        "--criterion",
        choices=("goodman", "soderberg"),
        default=None,
        help="goodman or soderberg",
    )
    parser.add_argument("--sigma-a", type=float, default=None, help="alternating stress [Pa]")
    parser.add_argument("--sigma-m", type=float, default=None, help="mean stress [Pa]")
    parser.add_argument("--se", type=float, default=None, help="fully reversed endurance amplitude [Pa]")
    parser.add_argument("--sut", type=float, default=None, help="ultimate tensile strength [Pa]")
    parser.add_argument("--sy", type=float, default=None, help="yield strength [Pa]")
    parser.add_argument("--n", type=float, default=None, help="required factor of safety")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        if args.criterion is None:
            raise ValueError("requires --criterion goodman or soderberg")
        if args.sigma_a is None or args.sigma_m is None or args.se is None:
            raise ValueError("requires --sigma-a, --sigma-m, and --se")
        if args.criterion == "goodman":
            if args.sut is None:
                raise ValueError("goodman requires --sut")
            if args.sy is not None:
                raise ValueError("do not pass --sy with goodman")
            intercept = args.sut
        else:
            if args.sy is None:
                raise ValueError("soderberg requires --sy")
            if args.sut is not None:
                raise ValueError("do not pass --sut with soderberg")
            intercept = args.sy
        if args.n is not None:
            require_positive("n", args.n)
        result = solve(args.criterion, args.sigma_a, args.sigma_m, args.se, intercept, args.n)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "fatigue_goodman.png"
    try:
        write_plot(result, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
