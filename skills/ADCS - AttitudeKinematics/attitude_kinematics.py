#!/usr/bin/env python3
"""3-2-1 attitude kinematics: direction cosines, quaternions, and rates.

Direction-cosine elements are dcm_321_c11 through dcm_321_c33.
Quaternion elements are quaternion_to_dcm_c11 through quaternion_to_dcm_c33.
Rates are quaternion_rate_0 through quaternion_rate_3 and euler_rate_roll,
euler_rate_pitch, and euler_rate_yaw. Kinematics only.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-12
SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Attitude kinematics"
MODES = (
    "euler_to_dcm",
    "dcm_to_euler",
    "quat_to_dcm",
    "dcm_to_quat",
    "euler_rates",
    "quat_rates",
)

ASSUMPTIONS = (
    "right-handed frames; 3-2-1 sequence is yaw, then pitch, then roll; "
    "the direction-cosine matrix maps inertial components into the body; "
    "quaternion is scalar-first and unit length; q and -q are the same rotation; "
    "dcm_321_c11 through dcm_321_c33; "
    "quaternion_to_dcm_c11 through quaternion_to_dcm_c33; "
    "quaternion_rate_0 through quaternion_rate_3; "
    "euler_rate_roll, euler_rate_pitch, euler_rate_yaw; "
    "3-2-1 rates are singular at pitch = +/- pi/2; "
    "no torque and no angular-momentum dynamics"
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


def require_finite(value: float, name: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def dcm_321(roll: float, pitch: float, yaw: float) -> list[list[float]]:
    for name, value in (("roll", roll), ("pitch", pitch), ("yaw", yaw)):
        require_finite(value, name)
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return [
        [cp * cy, cp * sy, -sp],
        [sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, sr * cp],
        [cr * sp * cy + sr * sy, cr * sp * sy - sr * cy, cr * cp],
    ]


def quat_to_dcm(q0: float, q1: float, q2: float, q3: float) -> list[list[float]]:
    return [
        [q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3, 2 * (q1 * q2 + q0 * q3), 2 * (q1 * q3 - q0 * q2)],
        [2 * (q1 * q2 - q0 * q3), q0 * q0 - q1 * q1 + q2 * q2 - q3 * q3, 2 * (q2 * q3 + q0 * q1)],
        [2 * (q1 * q3 + q0 * q2), 2 * (q2 * q3 - q0 * q1), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3],
    ]


def normalize_quaternion(q0: float, q1: float, q2: float, q3: float) -> tuple[float, float, float, float]:
    for name, value in (("q0", q0), ("q1", q1), ("q2", q2), ("q3", q3)):
        require_finite(value, name)
    norm = math.sqrt(q0 * q0 + q1 * q1 + q2 * q2 + q3 * q3)
    if norm <= 0.0 or abs(norm - 1.0) > 1e-4:
        raise ValueError("quaternion must have unit length")
    sign = -1.0 if q0 < 0.0 else 1.0
    return tuple(sign * value / norm for value in (q0, q1, q2, q3))  # type: ignore[return-value]


def matrix_from_elements(values: list[float]) -> list[list[float]]:
    if len(values) != 9 or any(not math.isfinite(value) for value in values):
        raise ValueError("the direction-cosine matrix needs nine finite elements")
    matrix = [values[0:3], values[3:6], values[6:9]]
    for column in range(3):
        length = math.sqrt(sum(matrix[row][column] ** 2 for row in range(3)))
        if abs(length - 1.0) > 1e-4:
            raise ValueError("direction-cosine columns must be unit length")
    det = (
        matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
    )
    if abs(det - 1.0) > 1e-3:
        raise ValueError("direction-cosine matrix must be a proper rotation")
    return matrix


def euler_from_dcm(matrix: list[list[float]]) -> tuple[float, float, float, str]:
    pitch = math.asin(max(-1.0, min(1.0, -matrix[0][2])))
    if abs(math.cos(pitch)) < 1e-8:
        roll = 0.0
        yaw = math.atan2(-matrix[1][0], matrix[1][1])
        return roll, pitch, yaw, "yes"
    roll = math.atan2(matrix[1][2], matrix[2][2])
    yaw = math.atan2(matrix[0][1], matrix[0][0])
    return roll, pitch, yaw, "no"


def dcm_to_quaternion(matrix: list[list[float]]) -> tuple[float, float, float, float]:
    trace = matrix[0][0] + matrix[1][1] + matrix[2][2]
    if trace > 0.0:
        q0 = 0.5 * math.sqrt(1.0 + trace)
        scale = 0.25 / q0
        q1 = (matrix[1][2] - matrix[2][1]) * scale
        q2 = (matrix[2][0] - matrix[0][2]) * scale
        q3 = (matrix[0][1] - matrix[1][0]) * scale
    else:
        diagonals = (matrix[0][0], matrix[1][1], matrix[2][2])
        largest = diagonals.index(max(diagonals))
        if largest == 0:
            q1 = 0.5 * math.sqrt(1.0 + matrix[0][0] - matrix[1][1] - matrix[2][2])
            scale = 0.25 / q1
            q0 = (matrix[1][2] - matrix[2][1]) * scale
            q2 = (matrix[0][1] + matrix[1][0]) * scale
            q3 = (matrix[0][2] + matrix[2][0]) * scale
        elif largest == 1:
            q2 = 0.5 * math.sqrt(1.0 + matrix[1][1] - matrix[0][0] - matrix[2][2])
            scale = 0.25 / q2
            q0 = (matrix[2][0] - matrix[0][2]) * scale
            q1 = (matrix[0][1] + matrix[1][0]) * scale
            q3 = (matrix[1][2] + matrix[2][1]) * scale
        else:
            q3 = 0.5 * math.sqrt(1.0 + matrix[2][2] - matrix[0][0] - matrix[1][1])
            scale = 0.25 / q3
            q0 = (matrix[0][1] - matrix[1][0]) * scale
            q1 = (matrix[0][2] + matrix[2][0]) * scale
            q2 = (matrix[1][2] + matrix[2][1]) * scale
    return normalize_quaternion(q0, q1, q2, q3)


def quaternion_rates(
    wx: float, wy: float, wz: float, q0: float, q1: float, q2: float, q3: float
) -> tuple[float, float, float, float]:
    for name, value in (("wx", wx), ("wy", wy), ("wz", wz)):
        require_finite(value, name)
    return (
        0.5 * (-wx * q1 - wy * q2 - wz * q3),
        0.5 * (wx * q0 + wz * q2 - wy * q3),
        0.5 * (wy * q0 - wz * q1 + wx * q3),
        0.5 * (wz * q0 + wy * q1 - wx * q2),
    )


def euler_rates(
    wx: float, wy: float, wz: float, roll: float, pitch: float
) -> tuple[float, float, float]:
    for name, value in (("wx", wx), ("wy", wy), ("wz", wz), ("roll", roll), ("pitch", pitch)):
        require_finite(value, name)
    cosine = math.cos(pitch)
    if abs(cosine) < 1e-8:
        raise ValueError("pitch is at the 3-2-1 gimbal lock")
    roll_rate = wx + math.sin(roll) * math.tan(pitch) * wy + math.cos(roll) * math.tan(pitch) * wz
    pitch_rate = math.cos(roll) * wy - math.sin(roll) * wz
    yaw_rate = math.sin(roll) * wy / cosine + math.cos(roll) * wz / cosine
    return roll_rate, pitch_rate, yaw_rate


def store_matrix(result: dict[str, object], matrix: list[list[float]]) -> None:
    for row in range(3):
        for column in range(3):
            result[f"c{row + 1}{column + 1}"] = matrix[row][column]


def emit(result: dict[str, object], graph: Path) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    for key, value in result.items():
        print_kv(key, value)
    print_kv("graph", str(graph))


def write_plot(matrix: list[list[float]], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    axes = (
        (matrix[0][0], matrix[0][1], matrix[0][2], "C0", "body x"),
        (matrix[1][0], matrix[1][1], matrix[1][2], "C1", "body y"),
        (matrix[2][0], matrix[2][1], matrix[2][2], "C3", "body z"),
    )
    fig = plt.figure(figsize=(6.4, 5.6))
    ax = fig.add_subplot(111, projection="3d")
    for x_comp, y_comp, z_comp, color, label in axes:
        ax.quiver(0.0, 0.0, 0.0, x_comp, y_comp, z_comp, color=color, arrow_length_ratio=0.12, label=label)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_zlim(-1.2, 1.2)
    ax.set_xlabel("reference x")
    ax.set_ylabel("reference y")
    ax.set_zlabel("reference z")
    ax.set_title(PLOT_TITLE)
    ax.legend(loc="upper left", frameon=False)
    fig.tight_layout()
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def solve(args: argparse.Namespace) -> tuple[dict[str, object], list[list[float]]]:
    mode = args.mode
    if mode == "euler_to_dcm":
        if None in (args.roll, args.pitch, args.yaw):
            raise ValueError("euler_to_dcm requires --roll, --pitch, and --yaw")
        matrix = dcm_321(args.roll, args.pitch, args.yaw)
        result: dict[str, object] = {
            "mode": mode,
            "roll": args.roll,
            "pitch": args.pitch,
            "yaw": args.yaw,
        }
        store_matrix(result, matrix)
        return result, matrix
    if mode in ("dcm_to_euler", "dcm_to_quat"):
        values = [getattr(args, f"c{row}{column}") for row in range(1, 4) for column in range(1, 4)]
        if any(value is None for value in values):
            raise ValueError(f"{mode} requires --c11 through --c33")
        matrix = matrix_from_elements([float(value) for value in values])
        result = {"mode": mode}
        store_matrix(result, matrix)
        if mode == "dcm_to_euler":
            roll, pitch, yaw, gimbal = euler_from_dcm(matrix)
            result.update({"roll": roll, "pitch": pitch, "yaw": yaw, "gimbal_lock": gimbal})
        else:
            q0, q1, q2, q3 = dcm_to_quaternion(matrix)
            result.update({"q0": q0, "q1": q1, "q2": q2, "q3": q3})
        return result, matrix
    if mode == "quat_to_dcm":
        if None in (args.q0, args.q1, args.q2, args.q3):
            raise ValueError("quat_to_dcm requires --q0, --q1, --q2, and --q3")
        q0, q1, q2, q3 = normalize_quaternion(args.q0, args.q1, args.q2, args.q3)
        matrix = quat_to_dcm(q0, q1, q2, q3)
        result = {"mode": mode, "q0": q0, "q1": q1, "q2": q2, "q3": q3}
        store_matrix(result, matrix)
        return result, matrix
    if mode == "euler_rates":
        if None in (args.wx, args.wy, args.wz, args.roll, args.pitch, args.yaw):
            raise ValueError("euler_rates requires --wx, --wy, --wz, --roll, --pitch, and --yaw")
        roll_rate, pitch_rate, yaw_rate = euler_rates(args.wx, args.wy, args.wz, args.roll, args.pitch)
        matrix = dcm_321(args.roll, args.pitch, args.yaw)
        return {
            "mode": mode,
            "wx": args.wx,
            "wy": args.wy,
            "wz": args.wz,
            "roll": args.roll,
            "pitch": args.pitch,
            "yaw": args.yaw,
            "roll_rate": roll_rate,
            "pitch_rate": pitch_rate,
            "yaw_rate": yaw_rate,
        }, matrix
    if mode == "quat_rates":
        if None in (args.wx, args.wy, args.wz, args.q0, args.q1, args.q2, args.q3):
            raise ValueError("quat_rates requires --wx, --wy, --wz, and --q0 through --q3")
        q0, q1, q2, q3 = normalize_quaternion(args.q0, args.q1, args.q2, args.q3)
        q0_dot, q1_dot, q2_dot, q3_dot = quaternion_rates(args.wx, args.wy, args.wz, q0, q1, q2, q3)
        return {
            "mode": mode,
            "wx": args.wx,
            "wy": args.wy,
            "wz": args.wz,
            "q0": q0,
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "q0_dot": q0_dot,
            "q1_dot": q1_dot,
            "q2_dot": q2_dot,
            "q3_dot": q3_dot,
        }, quat_to_dcm(q0, q1, q2, q3)
    raise ValueError("--mode must be a 3-2-1 kinematic conversion")


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    identity = dcm_321(0.0, 0.0, 0.0)
    if identity != [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]:
        return fail("zero angles are not the identity matrix")
    yaw = dcm_321(0.0, 0.0, math.pi / 2.0)
    if not close(yaw[0][1], 1.0) or not close(yaw[1][0], -1.0):
        return fail("yaw of pi/2 is not the expected matrix")
    half = math.sqrt(0.5)
    from_quat = quat_to_dcm(half, 0.0, 0.0, half)
    for row in range(3):
        for column in range(3):
            if not close(from_quat[row][column], yaw[row][column]):
                return fail("yaw quaternion does not match the 3-2-1 matrix")
    recovered = dcm_to_quaternion(yaw)
    if any(not close(actual, expected) for actual, expected in zip(recovered, (half, 0.0, 0.0, half))):
        return fail("yaw matrix did not return the scalar-first quaternion")
    roll, pitch, yaw_angle, gimbal = euler_from_dcm(yaw)
    if gimbal != "no" or not close(roll, 0.0) or not close(pitch, 0.0) or not close(yaw_angle, math.pi / 2.0):
        return fail("yaw matrix did not return yaw pi/2")
    q0_dot, q1_dot, q2_dot, q3_dot = quaternion_rates(2.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)
    if not close(q0_dot, 0.0) or not close(q1_dot, 1.0) or not close(q2_dot, 0.0) or not close(q3_dot, 0.0):
        return fail("identity roll rate is not (0, 1, 0, 0)")
    roll_rate, pitch_rate, yaw_rate = euler_rates(1.0, 2.0, 3.0, 0.0, 0.0)
    if not close(roll_rate, 1.0) or not close(pitch_rate, 2.0) or not close(yaw_rate, 3.0):
        return fail("level Euler rates are not the body rates")
    try:
        euler_rates(0.0, 0.0, 0.0, 0.0, math.pi / 2.0)
        return fail("gimbal lock was accepted")
    except ValueError:
        pass
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "check.png"
        write_plot(yaw, path)
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("check plot was not written")
    print("check: pass")
    print_kv("yaw_c12", yaw[0][1])
    print_kv("q0_yaw", recovered[0])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="3-2-1 direction cosines, quaternions, and kinematic rates.")
    parser.add_argument("--mode", choices=MODES, default=None, help="one kinematic conversion")
    parser.add_argument("--yaw", type=float, default=None, help="yaw about reference axis 3 [rad]")
    parser.add_argument("--pitch", type=float, default=None, help="pitch about axis 2 [rad]")
    parser.add_argument("--roll", type=float, default=None, help="roll about axis 1 [rad]")
    parser.add_argument("--q0", type=float, default=None, help="quaternion scalar")
    parser.add_argument("--q1", type=float, default=None, help="quaternion vector x")
    parser.add_argument("--q2", type=float, default=None, help="quaternion vector y")
    parser.add_argument("--q3", type=float, default=None, help="quaternion vector z")
    parser.add_argument("--wx", type=float, default=None, help="body rate about x [rad/s]")
    parser.add_argument("--wy", type=float, default=None, help="body rate about y [rad/s]")
    parser.add_argument("--wz", type=float, default=None, help="body rate about z [rad/s]")
    parser.add_argument("--c11", type=float, default=None, help="direction-cosine element c11")
    parser.add_argument("--c12", type=float, default=None, help="direction-cosine element c12")
    parser.add_argument("--c13", type=float, default=None, help="direction-cosine element c13")
    parser.add_argument("--c21", type=float, default=None, help="direction-cosine element c21")
    parser.add_argument("--c22", type=float, default=None, help="direction-cosine element c22")
    parser.add_argument("--c23", type=float, default=None, help="direction-cosine element c23")
    parser.add_argument("--c31", type=float, default=None, help="direction-cosine element c31")
    parser.add_argument("--c32", type=float, default=None, help="direction-cosine element c32")
    parser.add_argument("--c33", type=float, default=None, help="direction-cosine element c33")
    parser.add_argument("--out", type=Path, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.mode is None:
        print("error: requires --mode", file=sys.stderr)
        return 2
    try:
        result, matrix = solve(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else SKILL_DIR / "attitude_kinematics.png"
    try:
        write_plot(matrix, out_path)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    emit(result, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
