#!/usr/bin/env python3
"""Steady unpowered glide on a parabolic drag polar.

Best L/D is max_lift_to_drag. Glide angle is glide_angle,
a = atan(D/L). Speed is glide_speed with glide_lift L = W*cos(a).
Sink rate is sink_rate vs = V*sin(a). Range from a height is
glide_range d = h/tan(a), equal to glide_range_from_ld.
Density is the 1976 atmosphere at geometric --alt.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-8
PLOT_TITLE = "Steady glide"
PLOT_END_FACTOR = 1.5
N_PLOT = 201
MACH_WARN = 0.3
GOLDEN = 0.5 * (3.0 - math.sqrt(5.0))

SKILL_DIR = Path(__file__).resolve().parent
ATMOS_DIR = SKILL_DIR.parent / "ATMOS - Standard1976"

ASSUMPTIONS = (
    "steady unpowered unaccelerated glide; parabolic polar CD = CD0 + "
    "CL**2/(pi*AR*e) from drag_polar and induced_drag_coefficient; "
    "0 < e <= 1; LD_max is max_lift_to_drag, 0.5*sqrt(pi*AR*e/CD0), "
    "at CL = sqrt(CD0/k) and CD = 2*CD0 with k = 1/(pi*AR*e); "
    "glide_angle a = atan(D/L) = atan(CD/CL); glide_lift L = W*cos(a) "
    "and glide_drag D = W*sin(a) from the Glenn force balance; "
    "glide_speed V = sqrt(2*W*cos(a)/(rho*S*CL)); sink_rate vs = V*sin(a); "
    "glide_range d = h/tan(a) = h*(L/D); still air; constant density at "
    "the 1976 geometric --alt over the height drop; incompressible "
    "freestream_dynamic_pressure; the shallowest path is best L/D "
    "(best-range glide); minimum sink is a higher CL on the same polar; "
    f"the plot end is {PLOT_END_FACTOR:g} times the best-L/D true "
    "airspeed; weight is a force, so g0 is not applied to W"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def load_atmosphere():
    folder = str(ATMOS_DIR)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    try:
        from standard_1976 import atmosphere, require_altitude
    except ImportError as exc:
        raise ValueError(
            "ATMOS - Standard1976 must be importable for density at --alt"
        ) from exc
    return atmosphere, require_altitude


def induced_factor(aspect_ratio: float, oswald: float) -> float:
    return 1.0 / (math.pi * aspect_ratio * oswald)


def polar_cd(cd0: float, k: float, cl: float) -> float:
    return cd0 + k * cl * cl


def max_lift_to_drag(aspect_ratio: float, oswald: float, cd0: float) -> float:
    """max_lift_to_drag."""
    return 0.5 * math.sqrt(math.pi * aspect_ratio * oswald / cd0)


def glide_angle(drag: float, lift: float) -> float:
    """glide_angle."""
    return math.atan(drag / lift)


def glide_speed(weight: float, gamma: float, rho: float, area: float, cl: float) -> float:
    """glide_speed."""
    return math.sqrt(2.0 * weight * math.cos(gamma) / (rho * area * cl))


def sink_rate(speed: float, gamma: float) -> float:
    """sink_rate."""
    return speed * math.sin(gamma)


def glide_range(height: float, gamma: float) -> float:
    """glide_range."""
    return height / math.tan(gamma)


def polar_ld(cd0: float, aspect_ratio: float, oswald: float) -> dict[str, float]:
    k = induced_factor(aspect_ratio, oswald)
    cl = math.sqrt(cd0 / k)
    cd = 2.0 * cd0
    ld = cl / cd
    return {
        "k": k,
        "CL_LDmax": cl,
        "CD_LDmax": cd,
        "LD_max": ld,
    }


def at_cl(
    cl: float,
    weight: float,
    area: float,
    cd0: float,
    k: float,
    rho: float,
) -> dict[str, float]:
    cd = polar_cd(cd0, k, cl)
    gamma = glide_angle(cd, cl)
    speed = glide_speed(weight, gamma, rho, area, cl)
    return {
        "CL": cl,
        "CD": cd,
        "LD": cl / cd,
        "gamma_rad": gamma,
        "V_m_s": speed,
        "vs_m_s": sink_rate(speed, gamma),
    }


def minimize_sink(
    weight: float,
    area: float,
    cd0: float,
    k: float,
    rho: float,
    cl_lo: float,
    cl_hi: float,
) -> dict[str, float]:
    """Golden-section search for the CL of minimum sink_rate on the polar."""
    lo = cl_lo
    hi = cl_hi
    x1 = lo + GOLDEN * (hi - lo)
    x2 = hi - GOLDEN * (hi - lo)
    f1 = at_cl(x1, weight, area, cd0, k, rho)["vs_m_s"]
    f2 = at_cl(x2, weight, area, cd0, k, rho)["vs_m_s"]
    for _ in range(80):
        if abs(hi - lo) <= 1e-12 * max(1.0, abs(hi)):
            break
        if f1 < f2:
            hi = x2
            x2 = x1
            f2 = f1
            x1 = lo + GOLDEN * (hi - lo)
            f1 = at_cl(x1, weight, area, cd0, k, rho)["vs_m_s"]
        else:
            lo = x1
            x1 = x2
            f1 = f2
            x2 = hi - GOLDEN * (hi - lo)
            f2 = at_cl(x2, weight, area, cd0, k, rho)["vs_m_s"]
    cl = 0.5 * (lo + hi)
    return at_cl(cl, weight, area, cd0, k, rho)


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def polar_curve(
    weight: float,
    area: float,
    cd0: float,
    k: float,
    rho: float,
    cl_start: float,
    cl_end: float,
) -> tuple[list[float], list[float], list[float]]:
    high = max(cl_start, cl_end)
    low = min(cl_start, cl_end)
    if not (high > low > 0.0):
        raise ValueError("lift-coefficient sweep must be a positive interval")
    coefficients = linspace(high, low, N_PLOT)
    speeds: list[float] = []
    sinks: list[float] = []
    for cl in coefficients:
        point = at_cl(cl, weight, area, cd0, k, rho)
        speeds.append(point["V_m_s"])
        sinks.append(point["vs_m_s"])
    return speeds, sinks, coefficients


def cl_for_speed(
    speed: float,
    weight: float,
    area: float,
    cd0: float,
    k: float,
    rho: float,
    cl_guess: float,
) -> float:
    cl = cl_guess
    for _ in range(40):
        point = at_cl(cl, weight, area, cd0, k, rho)
        target = 2.0 * weight * math.cos(point["gamma_rad"]) / (rho * area * speed * speed)
        if target <= 0.0:
            break
        nxt = 0.5 * (cl + target)
        if abs(nxt - cl) <= 1e-12 * max(1.0, abs(cl)):
            cl = nxt
            break
        cl = nxt
    return cl


def warnings_for(
    points: dict[str, float],
    clmax: float | None,
    sound_speed: float,
) -> list[str]:
    notes: list[str] = []
    if clmax is not None:
        for key, label in (
            ("CL_LDmax", "best L/D"),
            ("CL_min_sink", "minimum sink"),
        ):
            cl = points[key]
            if cl > clmax:
                notes.append(
                    f"{label} needs CL {cl:.6g}, above CLmax {clmax:.6g}; "
                    "that speed is below stall"
                )
    fastest = max(points["V_LDmax_m_s"], points["V_min_sink_m_s"])
    if "V_plot_max_m_s" in points:
        fastest = max(fastest, points["V_plot_max_m_s"])
    if sound_speed > 0.0:
        mach = fastest / sound_speed
        if mach > MACH_WARN:
            notes.append(
                f"incompressible polar at Mach {mach:.6g}; "
                f"the checked model is used above Mach {MACH_WARN}"
            )
    return notes


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the glide polar") from exc
    return plt


def plot_glide(
    path: Path,
    speeds: list[float],
    sinks: list[float],
    best: dict[str, float],
    minsink: dict[str, float],
    stall_speed: float | None,
) -> None:
    plt = ensure_matplotlib()
    v_max = best["V_plot_max_m_s"]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(speeds, sinks, color="#1a5276", linewidth=1.8, label="sink polar")
    ax.plot(
        best["V_LDmax_m_s"],
        best["vs_LDmax_m_s"],
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="best L/D",
    )
    ax.plot(
        minsink["V_m_s"],
        minsink["vs_m_s"],
        "o",
        color="#117a65",
        markersize=7,
        zorder=5,
        label="minimum sink",
    )
    if stall_speed is not None:
        ax.axvline(
            stall_speed,
            color="#c0392b",
            linestyle="--",
            linewidth=1.4,
            label="glide stall",
        )
    ax.set_xlim(0.0, v_max)
    ax.set_ylim(bottom=0.0)
    ax.set_xlabel("true airspeed (m/s)")
    ax.set_ylabel("sink rate (m/s)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(
    weight: float,
    area: float,
    cd0: float,
    aspect_ratio: float,
    oswald: float,
    altitude: float,
    rho: float,
    sound_speed: float,
    clmax: float | None,
    height: float | None,
    best: dict[str, float],
    minsink: dict[str, float],
    notes: list[str],
    path: Path,
) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("weight_N", weight)
    print_kv("area_m2", area)
    print_kv("CD0", cd0)
    print_kv("AR", aspect_ratio)
    print_kv("e", oswald)
    print_kv("k", best["k"])
    print_kv("Z_m", altitude)
    print_kv("rho_kg_m3", rho)
    print_kv("cs_m_s", sound_speed)
    print_kv("LD_max", best["LD_max"])
    print_kv("CL_LDmax", best["CL_LDmax"])
    print_kv("CD_LDmax", best["CD_LDmax"])
    print_kv("gamma_rad", best["gamma_rad"])
    print_kv("V_LDmax_m_s", best["V_LDmax_m_s"])
    print_kv("vs_LDmax_m_s", best["vs_LDmax_m_s"])
    print_kv("CL_min_sink", minsink["CL"])
    print_kv("CD_min_sink", minsink["CD"])
    print_kv("LD_min_sink", minsink["LD"])
    print_kv("gamma_min_sink_rad", minsink["gamma_rad"])
    print_kv("V_min_sink_m_s", minsink["V_m_s"])
    print_kv("vs_min_m_s", minsink["vs_m_s"])
    if clmax is not None:
        print_kv("CLmax", clmax)
        print_kv("V_stall_glide_m_s", best["V_stall_glide_m_s"])
    if height is not None:
        print_kv("h_m", height)
        print_kv("R_m", best["R_m"])
        print_kv("R_min_sink_m", minsink["R_m"])
    print_kv("plot_end_factor", PLOT_END_FACTOR)
    print_kv("V_plot_max_m_s", best["V_plot_max_m_s"])
    print_kv("graph", str(path))
    if notes:
        print_kv("warning", "; ".join(notes))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def near(got: float, want: float, label: str) -> int | None:
    if abs(got - want) > CHECK_TOL * max(1.0, abs(want)):
        return fail(f"{label} = {got}, expected {want}")
    return None


def run_check() -> int:
    atmosphere, require_altitude = load_atmosphere()
    sea = atmosphere(0.0)
    rho = sea["rho"]
    weight = 10000.0
    area = 16.0
    cd0 = 0.02
    aspect_ratio = 8.0
    oswald = 0.8
    clmax = 1.6
    height = 1000.0
    polar = polar_ld(cd0, aspect_ratio, oswald)
    k = polar["k"]
    if near(k, 1.0 / (math.pi * aspect_ratio * oswald), "k"):
        return 1
    ld_closed = max_lift_to_drag(aspect_ratio, oswald, cd0)
    if near(polar["LD_max"], ld_closed, "LD_max"):
        return 1
    if near(polar["CL_LDmax"], math.sqrt(cd0 / k), "CL at max L/D"):
        return 1
    if near(polar["CD_LDmax"], 2.0 * cd0, "CD at max L/D"):
        return 1
    best_pt = at_cl(polar["CL_LDmax"], weight, area, cd0, k, rho)
    if near(best_pt["gamma_rad"], math.atan(1.0 / polar["LD_max"]), "glide angle"):
        return 1
    if near(best_pt["gamma_rad"], math.atan(best_pt["CD"] / best_pt["CL"]), "atan CD/CL"):
        return 1
    lift = weight * math.cos(best_pt["gamma_rad"])
    drag = weight * math.sin(best_pt["gamma_rad"])
    if near(lift / drag, polar["LD_max"], "L/D from W cos/sin"):
        return 1
    q = 0.5 * rho * best_pt["V_m_s"] ** 2
    if near(lift, polar["CL_LDmax"] * q * area, "lift_force"):
        return 1
    if near(best_pt["vs_m_s"], best_pt["V_m_s"] * math.sin(best_pt["gamma_rad"]), "sink"):
        return 1
    if near(glide_range(height, best_pt["gamma_rad"]), height * polar["LD_max"], "range"):
        return 1

    cl_power = math.sqrt(3.0 * cd0 / k)
    minsink = minimize_sink(weight, area, cd0, k, rho, polar["CL_LDmax"], 2.5 * cl_power)
    if minsink["vs_m_s"] + CHECK_TOL < 0.0:
        return fail("minimum sink was negative")
    if not minsink["vs_m_s"] < best_pt["vs_m_s"]:
        return fail("minimum sink was not below the best-L/D sink")
    if not minsink["V_m_s"] < best_pt["V_m_s"]:
        return fail("minimum-sink speed was not below the best-L/D speed")
    if abs(minsink["CL"] - cl_power) / cl_power > 0.05:
        return fail(f"min-sink CL {minsink['CL']} far from sqrt(3 CD0/k) {cl_power}")

    stall = at_cl(clmax, weight, area, cd0, k, rho)
    level_stall = math.sqrt(2.0 * weight / (rho * area * clmax))
    if not stall["V_m_s"] < level_stall:
        return fail("glide stall was not below the L = W stall speed")

    high = atmosphere(11000.0)
    high_pt = at_cl(polar["CL_LDmax"], weight, area, cd0, k, high["rho"])
    if near(high_pt["LD"], polar["LD_max"], "L/D independent of altitude"):
        return 1
    if near(high_pt["gamma_rad"], best_pt["gamma_rad"], "glide angle independent of altitude"):
        return 1
    if not high_pt["V_m_s"] > best_pt["V_m_s"]:
        return fail("true airspeed did not rise at 11 km")
    if not high_pt["vs_m_s"] > best_pt["vs_m_s"]:
        return fail("sink rate did not rise at 11 km")

    try:
        require_altitude(86000.0 + 1.0, "--alt")
    except ValueError:
        pass
    else:
        return fail("altitude above 86 km was accepted")

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out = _Capture()
        err = _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    base = [
        "--weight",
        "10000",
        "--area",
        "16",
        "--cd0",
        "0.02",
        "--ar",
        "8",
        "--e",
        "0.8",
        "--alt",
        "0",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "glide.png")
        code, text, err = capture(base + ["--clmax", "1.6", "--height", "1000", "--out", out])
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Steady glide",
            "LD_max:",
            "gamma_rad:",
            "V_LDmax_m_s:",
            "vs_LDmax_m_s:",
            "vs_min_m_s:",
            "R_m:",
            "V_stall_glide_m_s:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "warning:" in text:
            return fail("clean sea-level case printed a warning")

        code, text, err = capture(base + ["--clmax", "0.4", "--out", out])
        if code != 0 or "warning:" not in text:
            return fail("CL above CLmax produced no stall warning")
        if "R_m:" in text:
            return fail("range was printed without --height")

    code, _text, err = capture(
        ["--weight", "10000", "--area", "16", "--cd0", "0.02", "--ar", "8", "--e", "0.8"]
    )
    if code != 2 or "--alt" not in err:
        return fail("missing altitude was accepted")
    code, _text, err = capture(base + ["--height", "0"])
    if code != 2:
        return fail("zero height was accepted")
    code, _text, err = capture(base + ["--clmax", "-1"])
    if code != 2:
        return fail("negative CLmax was accepted")

    print("check: pass")
    print_kv("LD_max", polar["LD_max"])
    print_kv("gamma_rad", best_pt["gamma_rad"])
    print_kv("V_LDmax_m_s", best_pt["V_m_s"])
    print_kv("vs_LDmax_m_s", best_pt["vs_m_s"])
    print_kv("vs_min_m_s", minsink["vs_m_s"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Best L/D, sink rate, glide angle, and optional range from height "
            "for a steady unpowered glide on a parabolic drag polar."
        )
    )
    parser.add_argument("--weight", type=float, default=None, help="weight W [N]")
    parser.add_argument("--area", type=float, default=None, help="wing planform area S [m^2]")
    parser.add_argument("--cd0", type=float, default=None, help="zero-lift drag coefficient CD0")
    parser.add_argument("--ar", type=float, default=None, help="aspect ratio AR")
    parser.add_argument("--e", type=float, default=None, help="Oswald efficiency e, 0 < e <= 1")
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--clmax", type=float, default=None, help="maximum lift coefficient CLmax")
    parser.add_argument("--height", type=float, default=None, help="height drop for range [m]")
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    supplied = {
        "--weight": args.weight,
        "--area": args.area,
        "--cd0": args.cd0,
        "--ar": args.ar,
        "--e": args.e,
        "--alt": args.alt,
    }
    missing = [flag for flag, value in supplied.items() if value is None]
    if missing:
        print(
            "error: requires --weight, --area, --cd0, --ar, --e, and --alt; "
            f"missing {', '.join(missing)}",
            file=sys.stderr,
        )
        return 2

    try:
        require_positive("weight", args.weight)
        require_positive("wing area", args.area)
        require_positive("CD0", args.cd0)
        require_positive("aspect ratio", args.ar)
        if not math.isfinite(args.e) or args.e <= 0.0 or args.e > 1.0:
            raise ValueError("Oswald efficiency must be finite, > 0, and <= 1")
        if args.clmax is not None:
            require_positive("CLmax", args.clmax)
        if args.height is not None:
            require_positive("height", args.height)
        atmosphere, require_altitude = load_atmosphere()
        state = atmosphere(require_altitude(args.alt, "--alt"))
        rho = state["rho"]
        sound_speed = state["cs"]
        polar = polar_ld(args.cd0, args.ar, args.e)
        k = polar["k"]
        best_pt = at_cl(polar["CL_LDmax"], args.weight, args.area, args.cd0, k, rho)
        cl_power = math.sqrt(3.0 * args.cd0 / k)
        cl_hi = max(polar["CL_LDmax"] * 2.5, cl_power * 1.5)
        if args.clmax is not None:
            cl_hi = max(cl_hi, args.clmax)
        minsink = minimize_sink(
            args.weight, args.area, args.cd0, k, rho, polar["CL_LDmax"], cl_hi
        )
        v_plot_max = PLOT_END_FACTOR * best_pt["V_m_s"]
        cl_end = cl_for_speed(
            v_plot_max,
            args.weight,
            args.area,
            args.cd0,
            k,
            rho,
            polar["CL_LDmax"] / (PLOT_END_FACTOR ** 2),
        )
        cl_start = cl_hi
        if args.clmax is not None:
            cl_start = max(args.clmax, cl_end * 1.05)
        speeds, sinks, _cls = polar_curve(
            args.weight, args.area, args.cd0, k, rho, cl_start, cl_end
        )
        result = dict(polar)
        result["gamma_rad"] = best_pt["gamma_rad"]
        result["V_LDmax_m_s"] = best_pt["V_m_s"]
        result["vs_LDmax_m_s"] = best_pt["vs_m_s"]
        result["V_plot_max_m_s"] = v_plot_max
        stall_speed = None
        if args.clmax is not None:
            stall = at_cl(args.clmax, args.weight, args.area, args.cd0, k, rho)
            result["V_stall_glide_m_s"] = stall["V_m_s"]
            stall_speed = stall["V_m_s"]
        if args.height is not None:
            result["R_m"] = glide_range(args.height, best_pt["gamma_rad"])
            minsink = dict(minsink)
            minsink["R_m"] = glide_range(args.height, minsink["gamma_rad"])
        out_path = Path(args.out) if args.out else SKILL_DIR / "steady_glide.png"
        out_path = out_path.resolve()
        plot_glide(out_path, speeds, sinks, result, minsink, stall_speed)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    notes = warnings_for(
        {
            **result,
            "CL_min_sink": minsink["CL"],
            "V_min_sink_m_s": minsink["V_m_s"],
        },
        args.clmax,
        sound_speed,
    )
    emit(
        args.weight,
        args.area,
        args.cd0,
        args.ar,
        args.e,
        args.alt,
        rho,
        sound_speed,
        args.clmax,
        args.height,
        result,
        minsink,
        notes,
        out_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
