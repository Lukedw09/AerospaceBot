#!/usr/bin/env python3
"""Rest-to-rest slew impulse, or disturbance momentum storage. Not both at once."""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

PLOT_TITLE = "Slew momentum"
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "slew mode is a rest-to-rest turn with equal acceleration and deceleration "
    "times about one principal axis, tau = 4*I*theta/t^2 and angular impulse "
    "2*I*theta/t, from dH/dt = L in NASA SP-8024; disturbance mode stores "
    "H = T*tau for one constant torque held over the stated duration; the two "
    "modes are separate runs"
)


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def slew_torque(inertia: float, angle: float, time_s: float) -> float:
    """rest_to_rest_slew_torque."""
    return 4.0 * inertia * angle / time_s ** 2


def slew_impulse(inertia: float, angle: float, time_s: float) -> float:
    """rest_to_rest_slew_impulse. Magnitude of one half-maneuver, I*delta_omega."""
    return 2.0 * inertia * angle / time_s


def disturbance_momentum(torque: float, duration_s: float) -> float:
    """disturbance_momentum_storage: H = T*tau."""
    return torque * duration_s


def emit(rows: list[tuple[str, float | str]], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key, value in rows:
        print_kv(key, value)
    if graph is not None:
        print_kv("graph", str(graph))


def write_slew_plot(inertia: float, angle: float, time_s: float, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    times = [time_s * (0.4 + 0.04 * i) for i in range(40)]
    torques = [slew_torque(inertia, angle, t) for t in times]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(times, torques, color="C0", label=r"$\tau$")
    ax.plot(time_s, slew_torque(inertia, angle, time_s), "s", color="C1", label="operating point")
    ax.set_xlabel("slew time (s)")
    ax.set_ylabel("torque (N·m)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def write_disturbance_plot(torque: float, duration_s: float, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    durations = [duration_s * (0.2 + 0.05 * i) for i in range(30)]
    stored = [disturbance_momentum(torque, t) for t in durations]
    fig, ax = plt.subplots(figsize=(7.0, 4.5))
    ax.plot(durations, stored, color="C0", label=r"$H$")
    ax.plot(duration_s, disturbance_momentum(torque, duration_s), "s", color="C1", label="operating point")
    ax.set_xlabel("duration (s)")
    ax.set_ylabel("stored momentum (N·m·s)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    def fail(msg: str) -> int:
        print(f"check: fail: {msg}", file=sys.stderr)
        return 1

    # 90 deg in 60 s with I = 2 kg m^2.
    inertia = 2.0
    angle = math.pi / 2.0
    time_s = 60.0
    tau = slew_torque(inertia, angle, time_s)
    impulse = slew_impulse(inertia, angle, time_s)
    if abs(tau - 4.0 * inertia * angle / time_s ** 2) > 1e-12:
        return fail("slew torque")
    if abs(impulse - tau * time_s / 2.0) > 1e-12:
        return fail("impulse is torque times half the slew time")
    # Peak rate is 2*theta/t, so impulse = I * peak rate.
    if abs(impulse - inertia * (2.0 * angle / time_s)) > 1e-12:
        return fail("impulse equals I times peak rate")
    # Disturbance: 1e-4 N m for one 5400 s orbit.
    stored = disturbance_momentum(1.0e-4, 5400.0)
    if abs(stored - 0.54) > 1e-12:
        return fail("disturbance momentum")
    code = main(["--inertia", "2", "--angle", "1", "--time", "10", "--torque", "1e-4", "--duration", "100"])
    if code == 0:
        return fail("mixed modes were accepted")
    with tempfile.TemporaryDirectory() as tmp:
        slew_path = Path(tmp) / "slew.png"
        dist_path = Path(tmp) / "dist.png"
        if main(["--inertia", "2", "--angle", str(angle), "--time", "60", "--out", str(slew_path)]) != 0:
            return fail("slew plot run")
        if main(["--torque", "1e-4", "--duration", "5400", "--out", str(dist_path)]) != 0:
            return fail("disturbance plot run")
        if slew_path.stat().st_size < 1000 or dist_path.stat().st_size < 1000:
            return fail("plot missing")
    print("check: pass")
    print_kv("tau_N_m", tau)
    print_kv("H_slew_N_m_s", impulse)
    print_kv("H_dist_N_m_s", stored)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Slew impulse or disturbance momentum. One mode per run.")
    parser.add_argument("--inertia", type=float, default=None)
    parser.add_argument("--angle", type=float, default=None, help="slew angle [rad]")
    parser.add_argument("--time", type=float, default=None, help="slew time [s]")
    parser.add_argument("--torque", type=float, default=None, help="disturbance torque [N*m]")
    parser.add_argument("--duration", type=float, default=None, help="disturbance duration [s]")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    slew_on = args.inertia is not None or args.angle is not None or args.time is not None
    dist_on = args.torque is not None or args.duration is not None
    if slew_on and dist_on:
        print("error: slew mode and disturbance mode are separate runs", file=sys.stderr)
        return 2
    if not slew_on and not dist_on:
        print("error: pass slew inputs or disturbance inputs", file=sys.stderr)
        return 2
    try:
        if slew_on:
            if None in (args.inertia, args.angle, args.time):
                raise ValueError("slew mode needs --inertia, --angle, and --time")
            if args.inertia <= 0.0 or args.angle <= 0.0 or args.time <= 0.0:
                raise ValueError("inertia, angle, and time must be positive")
            tau = slew_torque(args.inertia, args.angle, args.time)
            impulse = slew_impulse(args.inertia, args.angle, args.time)
            rows: list[tuple[str, float | str]] = [
                ("mode", "slew"),
                ("I_kg_m2", args.inertia),
                ("theta_rad", args.angle),
                ("t_s", args.time),
                ("tau_N_m", tau),
                ("H_N_m_s", impulse),
            ]
        else:
            if None in (args.torque, args.duration):
                raise ValueError("disturbance mode needs --torque and --duration")
            if args.duration <= 0.0:
                raise ValueError("--duration must be positive")
            stored = disturbance_momentum(args.torque, args.duration)
            rows = [
                ("mode", "disturbance"),
                ("T_N_m", args.torque),
                ("tau_s", args.duration),
                ("H_N_m_s", stored),
            ]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph = None
    if args.out is not None:
        try:
            if slew_on:
                write_slew_plot(args.inertia, args.angle, args.time, args.out)
            else:
                write_disturbance_plot(args.torque, args.duration, args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    emit(rows, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
