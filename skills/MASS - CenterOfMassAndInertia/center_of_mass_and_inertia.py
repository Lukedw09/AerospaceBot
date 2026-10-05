#!/usr/bin/env python3
"""Center of mass and inertia tensor of a rigid assembly of parts.

total_mass sums the part masses. center_of_mass_coordinate is Mx/m on each
axis from mass_first_moment. Point-mass contributions use point_mass_moment
and point_mass_product. Optional own-CG inertias use parallel_axis_moment and
parallel_axis_product when parallel-axis transfer is on. Inertia about the
user origin can be shifted to the CG with inertia_shift_to_cg.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Center of mass and inertia"

SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "rigid non-rotating assembly in one body frame; "
    "no fuel slosh; no time-varying CG; "
    "total_mass is the sum of part masses; "
    "center_of_mass_coordinate is Mx/m on each axis from mass_first_moment; "
    "point masses use point_mass_moment and point_mass_product; "
    "optional own-CG principal (or full) inertias use parallel_axis_moment "
    "and parallel_axis_product when --parallel is on for that part; "
    "with --parallel off, only the own-CG inertias are summed (no m*d^2); "
    "inertia about the user origin is also reported when --about-origin; "
    "inertia_shift_to_cg relates origin and CG tensors; "
    "tensor off-diagonals are -Pxy, -Pxz, -Pyz (TM X-1754)"
)

PALETTE = {
    "mass": "#1a5276",
    "cg": "#c0392b",
    "axis": "#566573",
    "grid": "#d5d8dc",
    "text": "#1b2631",
}


@dataclass(frozen=True)
class Part:
    mass: float
    x: float
    y: float
    z: float
    ixx: float
    iyy: float
    izz: float
    ixy: float
    ixz: float
    iyz: float
    parallel: bool
    has_own_inertia: bool


@dataclass(frozen=True)
class Inertia:
    ixx: float
    iyy: float
    izz: float
    ixy: float
    ixz: float
    iyz: float

    def tensor(self) -> tuple[tuple[float, float, float], ...]:
        return (
            (self.ixx, -self.ixy, -self.ixz),
            (-self.ixy, self.iyy, -self.iyz),
            (-self.ixz, -self.iyz, self.izz),
        )


@dataclass(frozen=True)
class Solution:
    parts: tuple[Part, ...]
    total_mass: float
    x_cg: float
    y_cg: float
    z_cg: float
    about_cg: Inertia
    about_origin: Inertia | None


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def require_positive(name: str, value: float) -> None:
    require_finite(name, value)
    if value <= 0.0:
        raise ValueError(f"{name} must be > 0")


def total_mass(m1: float, m2: float) -> float:
    """total_mass."""
    return m1 + m2


def mass_first_moment(mass: float, coordinate: float) -> float:
    """mass_first_moment."""
    return mass * coordinate


def center_of_mass_coordinate(first_moment: float, mass: float) -> float:
    """center_of_mass_coordinate."""
    return first_moment / mass


def point_mass_moment(mass: float, d1: float, d2: float) -> float:
    """point_mass_moment."""
    return mass * (d1 * d1 + d2 * d2)


def point_mass_product(mass: float, d1: float, d2: float) -> float:
    """point_mass_product."""
    return mass * d1 * d2


def parallel_axis_moment(icg: float, mass: float, d1: float, d2: float) -> float:
    """parallel_axis_moment."""
    return icg + mass * (d1 * d1 + d2 * d2)


def parallel_axis_product(pcg: float, mass: float, d1: float, d2: float) -> float:
    """parallel_axis_product."""
    return pcg + mass * d1 * d2


def inertia_shift_to_cg(io: float, mass: float, d1: float, d2: float) -> float:
    """inertia_shift_to_cg."""
    return io - mass * (d1 * d1 + d2 * d2)


def parse_bool_token(token: str) -> bool:
    lowered = token.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"parallel flag must be 0/1 or true/false, got {token!r}")


def parse_part(spec: str) -> Part:
    """Parse m,x,y,z[,Ixx,Iyy,Izz[,Ixy,Ixz,Iyz]][,parallel]."""
    pieces = [part.strip() for part in spec.split(",")]
    if len(pieces) < 4:
        raise ValueError(
            "each --part needs at least m,x,y,z "
            "(optional Ixx,Iyy,Izz[,Ixy,Ixz,Iyz][,parallel])"
        )
    try:
        mass = float(pieces[0])
        x = float(pieces[1])
        y = float(pieces[2])
        z = float(pieces[3])
    except ValueError as exc:
        raise ValueError(f"could not parse mass/position in {spec!r}") from exc
    require_positive("part mass", mass)
    require_finite("x", x)
    require_finite("y", y)
    require_finite("z", z)

    rest = pieces[4:]
    ixx = iyy = izz = 0.0
    ixy = ixz = iyz = 0.0
    has_own = False
    parallel = True

    if not rest:
        return Part(mass, x, y, z, ixx, iyy, izz, ixy, ixz, iyz, parallel, has_own)

    # Trailing parallel flag may be present with 3, 6, or (odd) counts.
    if len(rest) in {1, 4, 7}:
        parallel = parse_bool_token(rest[-1])
        rest = rest[:-1]

    if len(rest) == 0:
        return Part(mass, x, y, z, ixx, iyy, izz, ixy, ixz, iyz, parallel, has_own)

    if len(rest) == 3:
        try:
            ixx, iyy, izz = (float(rest[0]), float(rest[1]), float(rest[2]))
        except ValueError as exc:
            raise ValueError(f"could not parse Ixx,Iyy,Izz in {spec!r}") from exc
        has_own = True
    elif len(rest) == 6:
        try:
            ixx, iyy, izz, ixy, ixz, iyz = (float(v) for v in rest)
        except ValueError as exc:
            raise ValueError(
                f"could not parse Ixx,Iyy,Izz,Ixy,Ixz,Iyz in {spec!r}"
            ) from exc
        has_own = True
    else:
        raise ValueError(
            "optional inertia fields are Ixx,Iyy,Izz or "
            "Ixx,Iyy,Izz,Ixy,Ixz,Iyz, with optional trailing parallel flag"
        )

    for name, value in (
        ("Ixx", ixx),
        ("Iyy", iyy),
        ("Izz", izz),
        ("Ixy", ixy),
        ("Ixz", ixz),
        ("Iyz", iyz),
    ):
        require_finite(name, value)
    if ixx < 0.0 or iyy < 0.0 or izz < 0.0:
        raise ValueError("principal moments Ixx, Iyy, Izz must be >= 0")

    return Part(mass, x, y, z, ixx, iyy, izz, ixy, ixz, iyz, parallel, has_own)


def sum_mass(parts: tuple[Part, ...] | list[Part]) -> float:
    mass = 0.0
    for index, part in enumerate(parts):
        if index == 0:
            mass = part.mass
        else:
            mass = total_mass(mass, part.mass)
    return mass


def accumulate_inertia(
    parts: tuple[Part, ...] | list[Part],
    ox: float,
    oy: float,
    oz: float,
    force_parallel: bool | None = None,
) -> Inertia:
    ixx = iyy = izz = 0.0
    ixy = ixz = iyz = 0.0
    for part in parts:
        dx = part.x - ox
        dy = part.y - oy
        dz = part.z - oz
        use_parallel = part.parallel if force_parallel is None else force_parallel
        if part.has_own_inertia and not use_parallel:
            ixx += part.ixx
            iyy += part.iyy
            izz += part.izz
            ixy += part.ixy
            ixz += part.ixz
            iyz += part.iyz
            continue
        own_xx = part.ixx if part.has_own_inertia else 0.0
        own_yy = part.iyy if part.has_own_inertia else 0.0
        own_zz = part.izz if part.has_own_inertia else 0.0
        own_xy = part.ixy if part.has_own_inertia else 0.0
        own_xz = part.ixz if part.has_own_inertia else 0.0
        own_yz = part.iyz if part.has_own_inertia else 0.0
        if part.has_own_inertia:
            ixx += parallel_axis_moment(own_xx, part.mass, dy, dz)
            iyy += parallel_axis_moment(own_yy, part.mass, dx, dz)
            izz += parallel_axis_moment(own_zz, part.mass, dx, dy)
            ixy += parallel_axis_product(own_xy, part.mass, dx, dy)
            ixz += parallel_axis_product(own_xz, part.mass, dx, dz)
            iyz += parallel_axis_product(own_yz, part.mass, dy, dz)
        else:
            ixx += point_mass_moment(part.mass, dy, dz)
            iyy += point_mass_moment(part.mass, dx, dz)
            izz += point_mass_moment(part.mass, dx, dy)
            ixy += point_mass_product(part.mass, dx, dy)
            ixz += point_mass_product(part.mass, dx, dz)
            iyz += point_mass_product(part.mass, dy, dz)
    return Inertia(ixx, iyy, izz, ixy, ixz, iyz)


def evaluate(parts: list[Part], about_origin: bool) -> Solution:
    if not parts:
        raise ValueError("requires one or more --part entries")
    mass = sum_mass(parts)
    mx = sum(mass_first_moment(part.mass, part.x) for part in parts)
    my = sum(mass_first_moment(part.mass, part.y) for part in parts)
    mz = sum(mass_first_moment(part.mass, part.z) for part in parts)
    x_cg = center_of_mass_coordinate(mx, mass)
    y_cg = center_of_mass_coordinate(my, mass)
    z_cg = center_of_mass_coordinate(mz, mass)
    about_cg = accumulate_inertia(parts, x_cg, y_cg, z_cg)
    origin_inertia: Inertia | None = None
    if about_origin:
        origin_inertia = accumulate_inertia(parts, 0.0, 0.0, 0.0)
        # Consistency: shifting origin moments to the CG must match about_cg
        # when every contributing part used parallel-axis (or was a point mass).
        if all((not part.has_own_inertia) or part.parallel for part in parts):
            shifted = Inertia(
                inertia_shift_to_cg(origin_inertia.ixx, mass, y_cg, z_cg),
                inertia_shift_to_cg(origin_inertia.iyy, mass, x_cg, z_cg),
                inertia_shift_to_cg(origin_inertia.izz, mass, x_cg, y_cg),
                origin_inertia.ixy - mass * x_cg * y_cg,
                origin_inertia.ixz - mass * x_cg * z_cg,
                origin_inertia.iyz - mass * y_cg * z_cg,
            )
            for name, actual, expected in (
                ("Ixx", about_cg.ixx, shifted.ixx),
                ("Iyy", about_cg.iyy, shifted.iyy),
                ("Izz", about_cg.izz, shifted.izz),
                ("Ixy", about_cg.ixy, shifted.ixy),
                ("Ixz", about_cg.ixz, shifted.ixz),
                ("Iyz", about_cg.iyz, shifted.iyz),
            ):
                if not close(actual, expected):
                    raise ValueError(
                        f"CG and origin-shifted {name} disagree "
                        f"({actual} vs {expected})"
                    )
    return Solution(
        parts=tuple(parts),
        total_mass=mass,
        x_cg=x_cg,
        y_cg=y_cg,
        z_cg=z_cg,
        about_cg=about_cg,
        about_origin=origin_inertia,
    )


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot mass properties") from exc
    return plt


def write_plot(solution: Solution, out_path: Path) -> None:
    plt = ensure_matplotlib()
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    xs = [part.x for part in solution.parts]
    ys = [part.y for part in solution.parts]
    zs = [part.z for part in solution.parts]
    masses = [part.mass for part in solution.parts]
    max_mass = max(masses)
    sizes = [40.0 + 160.0 * (mass / max_mass) for mass in masses]

    fig = plt.figure(figsize=(7.5, 6.0))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(
        xs,
        ys,
        zs,
        s=sizes,
        c=PALETTE["mass"],
        depthshade=True,
        label="part mass",
        zorder=3,
    )
    ax.scatter(
        [solution.x_cg],
        [solution.y_cg],
        [solution.z_cg],
        s=120,
        c=PALETTE["cg"],
        marker="*",
        label="CG",
        zorder=5,
    )

    # Light extent padding so a single point still draws.
    coords = xs + ys + zs + [solution.x_cg, solution.y_cg, solution.z_cg]
    span = max(coords) - min(coords)
    pad = 0.15 * span if span > 0.0 else 1.0
    lo = min(coords) - pad
    hi = max(coords) + pad
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_zlim(lo, hi)

    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_title(PLOT_TITLE)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(solution: Solution, graph: Path) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("n_parts", len(solution.parts))
    print_kv("m_kg", solution.total_mass)
    print_kv("x_cg_m", solution.x_cg)
    print_kv("y_cg_m", solution.y_cg)
    print_kv("z_cg_m", solution.z_cg)
    cg = solution.about_cg
    print_kv("Ixx_cg_kg_m2", cg.ixx)
    print_kv("Iyy_cg_kg_m2", cg.iyy)
    print_kv("Izz_cg_kg_m2", cg.izz)
    print_kv("Ixy_cg_kg_m2", cg.ixy)
    print_kv("Ixz_cg_kg_m2", cg.ixz)
    print_kv("Iyz_cg_kg_m2", cg.iyz)
    t = cg.tensor()
    print_kv("tensor_cg_00", t[0][0])
    print_kv("tensor_cg_01", t[0][1])
    print_kv("tensor_cg_02", t[0][2])
    print_kv("tensor_cg_10", t[1][0])
    print_kv("tensor_cg_11", t[1][1])
    print_kv("tensor_cg_12", t[1][2])
    print_kv("tensor_cg_20", t[2][0])
    print_kv("tensor_cg_21", t[2][1])
    print_kv("tensor_cg_22", t[2][2])
    if solution.about_origin is not None:
        origin = solution.about_origin
        print_kv("Ixx_O_kg_m2", origin.ixx)
        print_kv("Iyy_O_kg_m2", origin.iyy)
        print_kv("Izz_O_kg_m2", origin.izz)
        print_kv("Ixy_O_kg_m2", origin.ixy)
        print_kv("Ixz_O_kg_m2", origin.ixz)
        print_kv("Iyz_O_kg_m2", origin.iyz)
    for index, part in enumerate(solution.parts, start=1):
        print_kv(f"part_{index}_m_kg", part.mass)
        print_kv(f"part_{index}_x_m", part.x)
        print_kv(f"part_{index}_y_m", part.y)
        print_kv(f"part_{index}_z_m", part.z)
        if part.has_own_inertia:
            print_kv(f"part_{index}_Ixx_kg_m2", part.ixx)
            print_kv(f"part_{index}_Iyy_kg_m2", part.iyy)
            print_kv(f"part_{index}_Izz_kg_m2", part.izz)
            print_kv(f"part_{index}_Ixy_kg_m2", part.ixy)
            print_kv(f"part_{index}_Ixz_kg_m2", part.ixz)
            print_kv(f"part_{index}_Iyz_kg_m2", part.iyz)
            print_kv(f"part_{index}_parallel_axis", part.parallel)
    print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    if not close(total_mass(2.0, 3.0), 5.0):
        return fail("total_mass 2+3 is not 5")
    if not close(mass_first_moment(2.0, 0.5), 1.0):
        return fail("mass_first_moment mismatch")
    if not close(center_of_mass_coordinate(2.0, 4.0), 0.5):
        return fail("center_of_mass_coordinate mismatch")
    if not close(point_mass_moment(2.0, 3.0, 4.0), 50.0):
        return fail("point_mass_moment mismatch")
    if not close(point_mass_product(2.0, 3.0, -1.0), -6.0):
        return fail("point_mass_product mismatch")
    if not close(parallel_axis_moment(2.0, 3.0, 1.0, 2.0), 17.0):
        return fail("parallel_axis_moment mismatch")
    if not close(parallel_axis_product(1.0, 2.0, -1.0, 4.0), -7.0):
        return fail("parallel_axis_product mismatch")
    if not close(inertia_shift_to_cg(50.0, 2.0, 3.0, 4.0), 0.0):
        return fail("inertia_shift_to_cg mismatch")

    # Two equal point masses on +x and -x: CG at origin, Iyy=Izz=2*m*(L)^2.
    parts = [
        parse_part("1,-1,0,0"),
        parse_part("1,1,0,0"),
    ]
    sol = evaluate(parts, about_origin=True)
    if not close(sol.total_mass, 2.0):
        return fail("two-mass total is not 2")
    if not close(sol.x_cg, 0.0) or not close(sol.y_cg, 0.0) or not close(sol.z_cg, 0.0):
        return fail("symmetric pair CG is not at origin")
    if not close(sol.about_cg.ixx, 0.0):
        return fail("Ixx about CG should be 0 for collinear x masses")
    if not close(sol.about_cg.iyy, 2.0) or not close(sol.about_cg.izz, 2.0):
        return fail("Iyy/Izz about CG should be 2")
    if sol.about_origin is None:
        return fail("about-origin inertia missing")
    if not close(sol.about_origin.iyy, 2.0):
        return fail("origin Iyy mismatch")

    # Own inertia with parallel axis: unit mass at (0,1,0) with Izz_cg = 2.
    # About system CG (= part CG here): Izz = 2. About origin: 2 + m*1^2 = 3.
    one = [parse_part("1,0,1,0,0,0,2")]
    sol_one = evaluate(one, about_origin=True)
    if not close(sol_one.y_cg, 1.0):
        return fail("single-part CG y is not 1")
    if not close(sol_one.about_cg.izz, 2.0):
        return fail("own Izz about CG is not 2")
    assert sol_one.about_origin is not None
    if not close(sol_one.about_origin.izz, 3.0):
        return fail("parallel-axis Izz about origin is not 3")

    # parallel off: only own inertia, no m*d^2 about CG (still at part CG).
    no_par = [parse_part("1,0,1,0,0,0,2,0")]
    sol_np = evaluate(no_par, about_origin=True)
    if not close(sol_np.about_cg.izz, 2.0):
        return fail("parallel-off about CG should keep own Izz")
    assert sol_np.about_origin is not None
    if not close(sol_np.about_origin.izz, 2.0):
        return fail("parallel-off about origin should not add m*d^2")

    try:
        parse_part("0,0,0,0")
        return fail("zero mass was accepted")
    except ValueError:
        pass
    try:
        parse_part("1,0,0")
        return fail("short part was accepted")
    except ValueError:
        pass

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
        out = str(Path(tmp) / "com.png")
        code, text, err = capture(
            [
                "--part",
                "2,0,0,0",
                "--part",
                "2,2,0,0",
                "--about-origin",
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
            "title: Center of mass and inertia",
            "m_kg:",
            "x_cg_m:",
            "Ixx_cg_kg_m2:",
            "Ixx_O_kg_m2:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if "x_cg_m: 1" not in text and "x_cg_m: 1.0" not in text:
            # Accept 1 or 1.0000000 formatting from .8g -> "1"
            if "x_cg_m: 1" not in text:
                return fail(f"expected CG at x=1, got:\n{text}")

        code, _text, err = capture([])
        if code != 2:
            return fail("missing parts was accepted")
        code, _text, err = capture(["--part", "1,0,0,0,1,1"])
        if code != 2:
            return fail("bad inertia field count was accepted")

    print("check: pass")
    print_kv("m_kg", sol.total_mass)
    print_kv("Iyy_cg_kg_m2", sol.about_cg.iyy)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Center of mass and inertia tensor of a rigid assembly of point "
            "masses or parts with optional own-CG inertias."
        )
    )
    parser.add_argument(
        "--part",
        action="append",
        default=None,
        help=(
            "part as m,x,y,z[,Ixx,Iyy,Izz[,Ixy,Ixz,Iyz]][,parallel]; "
            "repeat for each part. parallel is 0/1 (default 1 when inertias given)"
        ),
    )
    parser.add_argument(
        "--about-origin",
        action="store_true",
        help="also print the inertia tensor about the body-frame origin",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG path")
    parser.add_argument("--check", action="store_true", help="run built-in checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if not args.part:
        print(
            "error: requires one or more --part m,x,y,z[,Ixx,Iyy,Izz[,Ixy,Ixz,Iyz]][,parallel]",
            file=sys.stderr,
        )
        return 2

    try:
        parts = [parse_part(spec) for spec in args.part]
        solution = evaluate(parts, about_origin=args.about_origin)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    out_path = Path(args.out).resolve() if args.out else SKILL_DIR / "center_of_mass_and_inertia.png"
    try:
        write_plot(solution, out_path)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(solution, out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
