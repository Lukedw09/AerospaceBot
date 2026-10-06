#!/usr/bin/env python3
"""Lumped thermal capacitance transient under convection to a fixed ambient.

lumped_thermal_time_constant is tau = m*c/(h*A).
lumped_capacitance_temperature is T(t) = T_inf + (Ti - T_inf)*exp(-t/tau).
lumped_capacitance_time_to_temperature is t = -tau*ln((T - T_inf)/(Ti - T_inf)).
lumped_capacitance_heat_transferred is Q = m*c*(Ti - T(t)).
biot_number is Bi = h*Lc/k. Warn when Bi > 0.1 (not ≪ 1).
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Lumped capacitance transient"
N_CURVE = 401
PLOT_TAU_SPAN = 4.0
BIOT_WARN = 0.1

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "lumped thermal capacitance (spatially uniform solid temperature); "
    "valid when Biot number Bi = h*Lc/k << 1 (warn if Bi > 0.1); "
    "constant properties m, c, A, h; fixed ambient T_inf; "
    "surface convection only (no radiation unless the user already "
    "linearized it into an effective h); no internal heat generation; "
    "lumped_thermal_time_constant tau = m*c/(h*A); "
    "lumped_capacitance_temperature T(t)-T_inf = (Ti-T_inf)*exp(-t/tau); "
    "lumped_capacitance_time_to_temperature "
    "t = -tau*ln((T-T_inf)/(Ti-T_inf)); "
    "lumped_capacitance_heat_transferred Q = m*c*(Ti-T(t)); "
    "optional biot_number Bi = h*Lc/k when k and Lc are both supplied; "
    "does not invent m, c, A, h, Ti, T_inf, k, or Lc"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def require_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def lumped_thermal_time_constant(
    mass: float, specific_heat: float, h: float, area: float
) -> float:
    """lumped_thermal_time_constant: tau = m*c/(h*A)."""
    return mass * specific_heat / (h * area)


def lumped_capacitance_temperature(
    ti: float, t_inf: float, time: float, tau: float
) -> float:
    """lumped_capacitance_temperature: T = T_inf + (Ti-T_inf)*exp(-t/tau)."""
    return t_inf + (ti - t_inf) * math.exp(-time / tau)


def lumped_capacitance_time_to_temperature(
    ti: float, t_inf: float, target: float, tau: float
) -> float:
    """lumped_capacitance_time_to_temperature: t = -tau*ln((T-T_inf)/(Ti-T_inf))."""
    if ti == t_inf:
        if target == ti:
            return 0.0
        raise ValueError(
            "target temperature is unreachable when Ti equals T_inf"
        )
    ratio = (target - t_inf) / (ti - t_inf)
    if ratio <= 0.0 or ratio > 1.0:
        raise ValueError(
            "target temperature must lie strictly between Ti and T_inf, "
            "or equal Ti (t = 0)"
        )
    if ratio == 1.0:
        return 0.0
    return -tau * math.log(ratio)


def lumped_capacitance_heat_transferred(
    mass: float, specific_heat: float, ti: float, temperature: float
) -> float:
    """lumped_capacitance_heat_transferred: Q = m*c*(Ti - T)."""
    return mass * specific_heat * (ti - temperature)


def biot_number(h: float, char_length: float, conductivity: float) -> float:
    """biot_number: Bi = h*Lc/k."""
    return h * char_length / conductivity


def between_inclusive(value: float, a: float, b: float) -> bool:
    lo, hi = (a, b) if a <= b else (b, a)
    return lo <= value <= hi


def evaluate(
    mass: float,
    specific_heat: float,
    area: float,
    h: float,
    ti: float,
    t_inf: float,
    time: float | None,
    target_temp: float | None,
    conductivity: float | None,
    char_length: float | None,
) -> dict[str, float | str | None]:
    require_positive("mass", mass)
    require_positive("specific heat", specific_heat)
    require_positive("surface area", area)
    require_positive("convection coefficient", h)
    require_finite("initial temperature", ti)
    require_finite("ambient temperature", t_inf)

    has_time = time is not None
    has_target = target_temp is not None
    if has_time == has_target:
        raise ValueError("pass exactly one of --time or --target-temp")
    if has_time:
        require_nonnegative_time(float(time))

    has_k = conductivity is not None
    has_lc = char_length is not None
    if has_k != has_lc:
        raise ValueError(
            "pass both --k and --char-length for Biot, or neither"
        )

    tau = lumped_thermal_time_constant(mass, specific_heat, h, area)
    result: dict[str, float | str | None] = {
        "m_kg": mass,
        "c_J_kg_K": specific_heat,
        "A_m2": area,
        "h_W_m2_K": h,
        "Ti_K": ti,
        "T_inf_K": t_inf,
        "tau_s": tau,
        "assumptions": ASSUMPTIONS,
    }

    bi: float | None = None
    if has_k and has_lc:
        require_positive("thermal conductivity", float(conductivity))
        require_positive("characteristic length", float(char_length))
        bi = biot_number(h, float(char_length), float(conductivity))
        result["k_W_m_K"] = float(conductivity)
        result["Lc_m"] = float(char_length)
        result["Bi"] = bi
        if bi > BIOT_WARN:
            result["warning"] = (
                f"Bi = {bi:.8g} is not << 1 (threshold {BIOT_WARN:g}); "
                "spatial gradients may matter (Heisler / distributed "
                "transient conduction). Lumped capacitance is approximate"
            )
    else:
        result["Bi"] = None

    if has_time:
        t_val = float(time)
        temperature = lumped_capacitance_temperature(ti, t_inf, t_val, tau)
        q = lumped_capacitance_heat_transferred(
            mass, specific_heat, ti, temperature
        )
        result["mode"] = "time"
        result["t_s"] = t_val
        result["T_K"] = temperature
        result["Q_J"] = q
    else:
        target = float(target_temp)
        require_finite("target temperature", target)
        if target == ti:
            t_reach = 0.0
        elif not between_inclusive(target, ti, t_inf) or target == t_inf:
            # Strictly between Ti and T_inf (exclude ambient asymptote).
            if target == t_inf:
                raise ValueError(
                    "target temperature equal to T_inf is only reached as t→∞"
                )
            raise ValueError(
                "target temperature must lie between Ti and T_inf "
                "(inclusive of Ti, exclusive of T_inf unless Ti = T_inf)"
            )
        else:
            t_reach = lumped_capacitance_time_to_temperature(
                ti, t_inf, target, tau
            )
        result["mode"] = "target_temp"
        result["T_K"] = target
        result["t_s"] = t_reach
        result["Q_J"] = None

    return result


def require_nonnegative_time(value: float) -> None:
    if not math.isfinite(value) or value < 0.0:
        raise ValueError("time must be finite and >= 0")


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
        raise ValueError(
            "matplotlib is required to plot lumped capacitance transient"
        ) from exc
    return plt


def write_plot(result: dict[str, float | str | None], out_path: Path) -> None:
    plt = ensure_matplotlib()
    tau = float(result["tau_s"])
    ti = float(result["Ti_K"])
    t_inf = float(result["T_inf_K"])
    mode = str(result["mode"])
    t_mark = float(result["t_s"])
    t_end = max(PLOT_TAU_SPAN * tau, t_mark * 1.05 if t_mark > 0.0 else 0.0)
    if t_end <= 0.0:
        t_end = 1.0
    times = linspace(0.0, t_end, N_CURVE)
    temps = [
        lumped_capacitance_temperature(ti, t_inf, t, tau) for t in times
    ]

    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    ax.plot(times, temps, color="#1f4e79", linewidth=2.0)
    ax.axhline(t_inf, color="#888888", linestyle="--", linewidth=1.0, label="T∞")
    t_op = t_mark
    if mode == "time":
        t_op = float(result["t_s"])
        temp_op = float(result["T_K"])
    else:
        temp_op = float(result["T_K"])
    ax.plot(
        [t_op],
        [temp_op],
        marker="s",
        markersize=8,
        color="#c45c26",
        linestyle="None",
        label="operating point",
    )
    ax.set_xlabel("time t [s]")
    ax.set_ylabel("temperature T [K]")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def emit(result: dict[str, float | str | None], graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("mode", result["mode"])
    print_kv("m_kg", float(result["m_kg"]))
    print_kv("c_J_kg_K", float(result["c_J_kg_K"]))
    print_kv("A_m2", float(result["A_m2"]))
    print_kv("h_W_m2_K", float(result["h_W_m2_K"]))
    print_kv("Ti_K", float(result["Ti_K"]))
    print_kv("T_inf_K", float(result["T_inf_K"]))
    print_kv("tau_s", float(result["tau_s"]))
    if result["Bi"] is None:
        print_kv("Bi", "none")
    else:
        print_kv("Bi", float(result["Bi"]))
        print_kv("k_W_m_K", float(result["k_W_m_K"]))
        print_kv("Lc_m", float(result["Lc_m"]))
    if result["mode"] == "time":
        print_kv("t_s", float(result["t_s"]))
        print_kv("T_K", float(result["T_K"]))
        print_kv("Q_J", float(result["Q_J"]))
    else:
        print_kv("T_K", float(result["T_K"]))
        print_kv("t_s", float(result["t_s"]))
    if result.get("warning"):
        print_kv("warning", result["warning"])
    print_kv("assumptions", result["assumptions"])
    if graph is not None:
        print_kv("graph", str(graph))


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"check: fail: {message}", file=sys.stderr)
        return 1

    # tau = m c / (h A) = 2*500/(10*5) = 20 s
    mass, c, area, h = 2.0, 500.0, 5.0, 10.0
    ti, t_inf = 400.0, 300.0
    tau = lumped_thermal_time_constant(mass, c, h, area)
    if not close(tau, 20.0):
        return fail(f"time constant {tau} != 20")

    # At t = tau, (T - T_inf)/(Ti - T_inf) = 1/e
    t_at = tau
    temperature = lumped_capacitance_temperature(ti, t_inf, t_at, tau)
    expected_t = t_inf + (ti - t_inf) / math.e
    if not close(temperature, expected_t):
        return fail(f"T(tau) {temperature} != {expected_t}")

    q = lumped_capacitance_heat_transferred(mass, c, ti, temperature)
    expected_q = mass * c * (ti - expected_t)
    if not close(q, expected_q):
        return fail(f"Q {q} != {expected_q}")

    t_back = lumped_capacitance_time_to_temperature(
        ti, t_inf, expected_t, tau
    )
    if not close(t_back, tau):
        return fail(f"time-to-temp invert {t_back} != {tau}")

    bi = biot_number(10.0, 0.01, 200.0)
    if not close(bi, 0.0005):
        return fail(f"Bi {bi} != 0.0005")

    result_time = evaluate(
        mass, c, area, h, ti, t_inf, tau, None, 200.0, 0.01
    )
    if result_time["mode"] != "time":
        return fail("time mode not set")
    if not close(float(result_time["T_K"]), expected_t):
        return fail("evaluate time mode T mismatch")
    if not close(float(result_time["Q_J"]), expected_q):
        return fail("evaluate time mode Q mismatch")
    if result_time["Bi"] is None or not close(float(result_time["Bi"]), 0.0005):
        return fail("evaluate Biot mismatch")

    result_target = evaluate(
        mass, c, area, h, ti, t_inf, None, expected_t, None, None
    )
    if result_target["mode"] != "target_temp":
        return fail("target mode not set")
    if not close(float(result_target["t_s"]), tau):
        return fail("evaluate target mode t mismatch")
    if result_target["Bi"] is not None:
        return fail("Bi should be none without k and Lc")

    try:
        evaluate(mass, c, area, h, ti, t_inf, tau, expected_t, None, None)
        return fail("both time and target were accepted")
    except ValueError:
        pass
    try:
        evaluate(mass, c, area, h, ti, t_inf, None, None, None, None)
        return fail("neither time nor target was rejected")
    except ValueError:
        pass
    try:
        evaluate(mass, c, area, h, ti, t_inf, tau, None, 200.0, None)
        return fail("k without Lc was accepted")
    except ValueError:
        pass
    try:
        evaluate(mass, c, area, h, ti, t_inf, None, t_inf, None, None)
        return fail("target equal to T_inf was accepted")
    except ValueError:
        pass
    try:
        evaluate(mass, c, area, h, ti, t_inf, None, 500.0, None, None)
        return fail("target outside Ti..T_inf was accepted")
    except ValueError:
        pass

    # High Bi should warn.
    warned = evaluate(mass, c, area, h, ti, t_inf, tau, None, 1.0, 0.05)
    if "warning" not in warned:
        return fail("Bi > 0.1 did not warn")
    if float(warned["Bi"]) <= BIOT_WARN:
        return fail("expected Bi > 0.1 for warning case")

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

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "lumped.png")
        code, text, err = capture(
            [
                "--mass",
                "2",
                "--c",
                "500",
                "--area",
                "5",
                "--h",
                "10",
                "--ti",
                "400",
                "--t-inf",
                "300",
                "--time",
                "20",
                "--k",
                "200",
                "--char-length",
                "0.01",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Lumped capacitance transient",
            "mode: time",
            "tau_s:",
            "T_K:",
            "Q_J:",
            "Bi:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            [
                "--mass",
                "2",
                "--c",
                "500",
                "--area",
                "5",
                "--h",
                "10",
                "--ti",
                "400",
                "--t-inf",
                "300",
                "--target-temp",
                str(expected_t),
            ]
        )
        if code != 0:
            return fail(f"target mode returned {code}: {err}")
        if "mode: target_temp" not in text:
            return fail("target mode missing mode key")
        if "t_s:" not in text:
            return fail("target mode missing t_s")
        if "Q_J:" in text:
            return fail("target mode should not print Q_J")
        if "graph:" in text:
            return fail("run without --out printed graph")
        if "Bi: none" not in text:
            return fail("missing Bi: none without k/Lc")

        code, _text, err = capture(
            [
                "--mass",
                "2",
                "--c",
                "500",
                "--area",
                "5",
                "--h",
                "10",
                "--ti",
                "400",
                "--t-inf",
                "300",
                "--time",
                "20",
                "--target-temp",
                "350",
            ]
        )
        if code != 2 or "exactly one" not in err:
            return fail("both modes were accepted on the CLI")
        code, _text, err = capture(
            [
                "--mass",
                "2",
                "--c",
                "500",
                "--area",
                "5",
                "--h",
                "10",
                "--ti",
                "400",
                "--t-inf",
                "300",
            ]
        )
        if code != 2:
            return fail("missing mode was accepted")
        code, _text, _err = capture([])
        if code != 2:
            return fail("empty args were accepted")

    print("check: pass")
    print_kv("tau_s", tau)
    print_kv("T_K", expected_t)
    print_kv("Q_J", expected_q)
    print_kv("Bi", bi)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lumped thermal capacitance transient: T(t) under convection "
            "to fixed ambient, or time to a target temperature. Optional "
            "Biot check when k and characteristic length are given."
        )
    )
    parser.add_argument("--mass", type=float, default=None, help="mass m [kg]")
    parser.add_argument(
        "--c", type=float, default=None, help="specific heat c [J/(kg*K)]"
    )
    parser.add_argument(
        "--area", type=float, default=None, help="surface area A [m^2]"
    )
    parser.add_argument(
        "--h",
        type=float,
        default=None,
        help="convection coefficient h [W/(m^2*K)]",
    )
    parser.add_argument(
        "--ti", type=float, default=None, help="initial temperature Ti [K]"
    )
    parser.add_argument(
        "--t-inf",
        type=float,
        default=None,
        help="ambient temperature T_inf [K]",
    )
    parser.add_argument(
        "--time", type=float, default=None, help="elapsed time t [s] (mode A)"
    )
    parser.add_argument(
        "--target-temp",
        type=float,
        default=None,
        help="target temperature T [K] (mode B)",
    )
    parser.add_argument(
        "--k",
        type=float,
        default=None,
        help="thermal conductivity k [W/(m*K)] for Biot",
    )
    parser.add_argument(
        "--char-length",
        type=float,
        default=None,
        help="characteristic length Lc [m] for Biot (often V/A)",
    )
    parser.add_argument("--out", type=str, default=None, help="optional PNG path")
    parser.add_argument(
        "--check", action="store_true", help="run built-in consistency checks"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    required = {
        "--mass": args.mass,
        "--c": args.c,
        "--area": args.area,
        "--h": args.h,
        "--ti": args.ti,
        "--t-inf": args.t_inf,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        print(
            "error: requires "
            + ", ".join(missing)
            + ", and exactly one of --time or --target-temp",
            file=sys.stderr,
        )
        return 2

    try:
        result = evaluate(
            float(args.mass),
            float(args.c),
            float(args.area),
            float(args.h),
            float(args.ti),
            float(args.t_inf),
            args.time,
            args.target_temp,
            args.k,
            args.char_length,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    graph: Path | None = None
    if args.out is not None:
        out_path = Path(args.out).resolve()
        try:
            write_plot(result, out_path)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = out_path

    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
