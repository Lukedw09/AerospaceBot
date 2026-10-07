#!/usr/bin/env python3
"""Dynamic pressure and a preliminary alpha-q load from an ascent table.

q is freestream_dynamic_pressure, 1/2 rho V^2.
"""

from __future__ import annotations

import argparse
import csv
import sys
import webbrowser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
if str(SKILL_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR.parent))
import leo_chart  # noqa: E402

PLOT_TITLE = "Max-q"
ASSUMPTIONS = (
    "freestream dynamic pressure q = 0.5*rho*V^2; "
    "the table supplies time, speed, and density, or time, speed, and altitude "
    "with the 1976 atmosphere below 86 km; "
    "alpha_q is angle of attack in radians times q; "
    "axial load factor n = thrust/(m*g0) when thrust and mass are both present; "
    "g0 = 9.80665 m/s^2"
)


def print_kv(key: str, value: object) -> None:
    text = f"{value:.8g}" if isinstance(value, float) else str(value)
    print(f"{key}: {text}")


def load_rows(path: Path) -> list[dict[str, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("table has no header")
        rows = []
        for raw in reader:
            row = {}
            for key, value in raw.items():
                if value is None or value == "":
                    continue
                row[key.strip()] = float(value)
            rows.append(row)
    if len(rows) < 2:
        raise ValueError("table needs at least two rows")
    return rows


def density_from_1976(altitude: float) -> float:
    folder = SKILL_DIR.parent / "ATMOS - Standard1976"
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    from standard_1976 import atmosphere, require_altitude

    if altitude > 86000.0:
        return 0.0
    if altitude < 0.0:
        altitude = 0.0
    return atmosphere(require_altitude(altitude, "altitude"))["rho"]


def run(args: argparse.Namespace) -> int:
    rows = load_rows(Path(args.table))
    times = []
    qs = []
    alts = []
    q_max = -1.0
    index = 0
    alpha = args.alpha
    n_max = None
    n_at = None
    for i, row in enumerate(rows):
        if "V_m_s" not in row and "V" not in row:
            raise ValueError("table needs V_m_s")
        speed = row.get("V_m_s", row.get("V"))
        if "rho_kg_m3" in row:
            rho = row["rho_kg_m3"]
        elif "Z_m" in row:
            rho = density_from_1976(row["Z_m"])
        else:
            raise ValueError("table needs rho_kg_m3 or Z_m")
        q = 0.5 * rho * speed * speed
        t = row.get("t_s", float(i))
        z = row.get("Z_m", float("nan"))
        times.append(t)
        qs.append(q)
        alts.append(z)
        if q > q_max:
            q_max = q
            index = i
        if "thrust_N" in row and "m_kg" in row and row["m_kg"] > 0.0:
            n = row["thrust_N"] / (row["m_kg"] * 9.80665)
            if n_max is None or n > n_max:
                n_max = n
                n_at = t
    out = Path(args.out).resolve() if args.out else (SKILL_DIR / "max_q_and_aero_load.png")
    html = leo_chart.write_chart(
        out,
        PLOT_TITLE,
        {
            "kind": "series",
            "xs": times,
            "ys": qs,
            "mark": index,
            "xlabel": "time (s)",
            "ylabel": "dynamic pressure (Pa)",
            "seriesName": "dynamic pressure",
            "markName": "peak",
            "note": "Drag the slider to move along the ascent. The red point is the scrubber.",
        },
    )
    peak = rows[index]
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("rows", len(rows))
    print_kv("q_max_Pa", q_max)
    print_kv("t_maxq_s", times[index])
    if times[0] < times[index] < times[-1]:
        print_kv("q_max_interior", "yes")
    else:
        print_kv("q_max_interior", "no")
    if "Z_m" in peak:
        print_kv("Z_maxq_m", peak["Z_m"])
    print_kv("V_maxq_m_s", peak.get("V_m_s", peak.get("V")))
    if alpha is not None:
        print_kv("alpha_rad", alpha)
        print_kv("alpha_q_max", alpha * q_max)
    if n_max is not None:
        print_kv("n_axial_max", n_max)
        print_kv("t_n_max_s", n_at)
    print_kv("graph", str(out))
    print_kv("viewer", str(html))
    if args.open:
        webbrowser.open(html.as_uri())
    return 0


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    import io
    import tempfile

    # Constant density, speed = a*t, q = 0.5*rho*a^2*t^2 peaks at the last interior sample before the end if we put the peak in the middle.
    with tempfile.TemporaryDirectory() as tmp:
        table = Path(tmp) / "traj.csv"
        with table.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["t_s", "V_m_s", "rho_kg_m3", "Z_m"])
            for k, speed in enumerate((0.0, 10.0, 30.0, 20.0, 5.0)):
                writer.writerow([k, speed, 1.0, k * 100.0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(["--table", str(table), "--alpha", "0.1", "--out", str(Path(tmp) / "q.png")])
        finally:
            sys.stdout = old
        text = buf.getvalue()
        if code != 0:
            return fail(text)
        # q max at V=30, q=0.5*1*900=450
        if "q_max_Pa: 450" not in text:
            return fail(text)
        if "t_maxq_s: 2" not in text:
            return fail("peak index")
        if "alpha_q_max: 45" not in text:
            return fail("alpha q")
        if "q_max_interior: yes" not in text:
            return fail("interior")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Max-q from an ascent table.")
    parser.add_argument("--table")
    parser.add_argument("--alpha", type=float, default=None, help="Angle of attack, rad")
    parser.add_argument("--out", default=None)
    parser.add_argument("--open", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if not args.table:
        print("table is required", file=sys.stderr)
        return 2
    try:
        return run(args)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
