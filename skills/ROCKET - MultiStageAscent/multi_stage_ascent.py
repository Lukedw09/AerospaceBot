#!/usr/bin/env python3
"""Multi-stage powered ascent with mass drops.

Reuses ROCKET - BasicTrajectoryLossesFromBodySurface path physics. A single
stage with constant flight-path angle and no speed-dependent drag calls that
program's closed form so the burnout state matches.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import sys
import webbrowser
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent
PLOT_TITLE = "Multi-stage ascent"
ASSUMPTIONS = (
    "same powered-ascent model as BasicTrajectoryLossesFromBodySurface; "
    "stage 1 burns first from rest; each stage inert is dropped at burnout; "
    "optional jettison drops a named mass at an altitude or time; "
    "vacuum thrust; steering loss is zero while thrust is along the path "
    "or the flight-path angle is held; "
    "a one-stage constant-angle case with no quadratic drag uses the closed form"
)


def print_kv(key: str, value: object) -> None:
    text = f"{value:.8g}" if isinstance(value, float) else str(value)
    print(f"{key}: {text}")


def load_basic():
    path = (
        SKILL_DIR.parent
        / "ROCKET - BasicTrajectoryLossesFromBodySurface"
        / "basic_trajectory_losses_from_body_surface.py"
    )
    spec = importlib.util.spec_from_file_location("basic_trajectory_losses", path)
    if spec is None or spec.loader is None:
        raise ValueError("could not load the powered-ascent program")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_stage(text: str) -> dict:
    keys = {}
    for piece in text.split(","):
        key, raw = piece.split("=", 1)
        keys[key.strip()] = float(raw)
    for name in ("mp", "inert", "isp"):
        if name not in keys or keys[name] <= 0.0 and name != "inert":
            raise ValueError(f"stage needs {name}")
    if keys["inert"] < 0.0:
        raise ValueError("inert must be >= 0")
    if "tb" not in keys and "mdot" not in keys:
        raise ValueError("stage needs tb or mdot")
    return keys


def parse_jettison(text: str) -> dict:
    keys = {}
    for piece in text.split(","):
        key, raw = piece.split("=", 1)
        keys[key.strip()] = float(raw)
    if "mass" not in keys or keys["mass"] <= 0.0:
        raise ValueError("jettison needs mass > 0")
    if ("alt" in keys) == ("time" in keys):
        raise ValueError("jettison needs alt or time")
    return keys


def ode_stage(bt, **kw):
    dt = kw["tb"] / bt.N_STEP
    radius, phi, ur, ut = kw["state"]
    state = (radius, phi, ur, ut, 0.0, 0.0)
    m0_live = kw["m0"]
    dropped = False
    times = [kw["t0"]]
    rows = []
    theta_ref = kw["theta0"]
    t_local = 0.0
    horizontal = False

    def sample(local_t, st, theta):
        rad, ph, vr, vt, _lg, _ld = st
        speed = math.hypot(vr, vt)
        alt = rad - kw["radius_body"]
        rho = 0.0 if kw["density_at"] is None else kw["density_at"](alt)
        mass = m0_live - kw["mdot"] * local_t
        rows.append((kw["t0"] + local_t, alt, speed, theta, rho, 0.5 * rho * speed * speed, mass))

    sample(0.0, state, kw["theta0"])
    for _ in range(bt.N_STEP):
        if kw["hold_theta"]:
            theta_ref = kw["theta0"]
        deriv_kw = {
            "m0": m0_live,
            "mdot": kw["mdot"],
            "thrust": kw["thrust"],
            "mu": kw["mu"],
            "radius_body": kw["radius_body"],
            "theta_ref": theta_ref,
            "drag_value": kw["drag_value"],
            "cd": kw["cd"],
            "area": kw["area"],
            "density_at": kw["density_at"],
            "hold_theta": kw["hold_theta"],
        }
        state = bt.rk4_step(t_local, state, dt, deriv_kw)
        t_local += dt
        rad, ph, vr, vt, lg, ld = state
        if rad < kw["radius_body"]:
            rad = kw["radius_body"]
            if vr < 0.0:
                vr = 0.0
            state = (rad, ph, vr, vt, lg, ld)
        speed = math.hypot(vr, vt)
        if kw["hold_theta"] and rad > kw["radius_body"] + 1e-9:
            vr = speed * math.sin(kw["theta0"])
            vt = speed * math.cos(kw["theta0"])
            state = (rad, ph, vr, vt, lg, ld)
            theta = kw["theta0"]
        elif speed > bt.V_ALIGN:
            theta = math.atan2(vr, vt)
        else:
            theta = theta_ref
        if not kw["hold_theta"] and speed > bt.V_ALIGN:
            theta_ref = theta
        if theta <= 0.0:
            horizontal = True
        alt = rad - kw["radius_body"]
        if kw["jettison"] and not dropped:
            event = kw["jettison"]
            hit = ("time" in event and kw["t0"] + t_local >= event["time"]) or (
                "alt" in event and alt >= event["alt"]
            )
            if hit:
                m0_live -= event["mass"]
                if m0_live - kw["mdot"] * t_local <= 0.0:
                    raise ValueError("jettison drops the mass through zero")
                dropped = True
                state = (rad, ph, vr, vt, lg, ld)
        times.append(kw["t0"] + t_local)
        sample(t_local, state, theta)
    rad, ph, vr, vt, lg, ld = state
    return {
        "V_bo": math.hypot(vr, vt),
        "theta_bo": math.atan2(vr, vt) if math.hypot(vr, vt) > bt.V_ALIGN else theta_ref,
        "r_bo": rad,
        "phi_bo": ph,
        "state": (rad, ph, vr, vt),
        "dvg": lg,
        "dvD": ld,
        "rows": rows,
        "horizontal": horizontal,
        "solver": "ode",
        "m0_end": m0_live,
        "dropped": dropped,
    }


def write_csv(path: Path, rows: list[tuple], stage_marks: list[int]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["t_s", "Z_m", "V_m_s", "gamma_rad", "rho_kg_m3", "q_Pa", "m_kg"])
        for row in rows:
            writer.writerow([f"{value:.8g}" for value in row])


def scene_from_rows(rows: list[tuple], radius_body: float) -> dict:
    """Globe coordinates in kilometres. The pad is on the +z limb; downrange runs toward +x."""
    step = max(1, len(rows) // 280)
    samples = []
    phi = 0.0
    prev_t = rows[0][0]
    prev_v = 0.0
    prev_g = rows[0][3]
    for t, alt, speed, gamma, _rho, _q, _m in rows[::step]:
        dt = t - prev_t
        phi += 0.5 * (prev_v * math.cos(prev_g) + speed * math.cos(gamma)) / radius_body * dt
        prev_t, prev_v, prev_g = t, speed, gamma
        radius_km = (radius_body + alt) / 1000.0
        samples.append(
            [
                radius_km * math.sin(phi),
                0.0,
                radius_km * math.cos(phi),
                t,
                alt / 1000.0,
                speed,
            ]
        )
    if not samples:
        samples = [[0.0, 0.0, radius_body / 1000.0, 0.0, 0.0, 0.0]]
    earth_km = radius_body / 1000.0
    focus = samples[max(1, len(samples) // 6)]
    look_r = math.hypot(focus[0], focus[1], focus[2]) or 1.0
    outward = (focus[0] / look_r, focus[1] / look_r, focus[2] / look_r)
    return {
        "units": "Kilometres from Earth's center. The vehicle lifts off the pad and flies to burnout. Drag to rotate. Scroll to zoom.",
        "R": earth_km,
        "atm": earth_km + 120.0,
        "samples": samples,
        "path": [[p[0], p[1], p[2]] for p in samples],
        "camera": {
            "position": [
                focus[0] + outward[0] * 0.22 * earth_km,
                focus[1] + 0.72 * earth_km,
                focus[2] + outward[2] * 0.18 * earth_km,
            ],
            "target": [focus[0], focus[1], focus[2]],
        },
    }


def write_viewer(path: Path, payload: dict) -> None:
    viewer = SKILL_DIR / "viewer"
    template = (viewer / "template.html").read_text(encoding="utf-8")
    three = (viewer / "three.min.js").read_text(encoding="utf-8")
    three = three.replace("</script>", "<\\/script>").replace("</SCRIPT>", "<\\/SCRIPT>")
    encoded = json.dumps(payload).replace("<", "\\u003c")
    html = template.replace("__TITLE__", PLOT_TITLE).replace("__THREE_SOURCE__", three).replace("__SCENE_JSON__", encoded)
    path.write_text(html, encoding="utf-8")


def plot_first_frame(path: Path, payload: dict) -> None:
    import matplotlib

    if "matplotlib.pyplot" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    earth = float(payload["R"])
    atm = float(payload["atm"])
    pts = payload["path"]
    fig = plt.figure(figsize=(8.2, 6.4))
    ax = fig.add_subplot(111, projection="3d")
    xs, ys, zs = [], [], []
    for i in range(40):
        row_x, row_y, row_z = [], [], []
        u = 2.0 * math.pi * i / 39.0
        for j in range(20):
            v = math.pi * j / 19.0
            row_x.append(earth * math.cos(u) * math.sin(v))
            row_y.append(earth * math.sin(u) * math.sin(v))
            row_z.append(earth * math.cos(v))
        xs.append(row_x)
        ys.append(row_y)
        zs.append(row_z)
    import numpy as np

    ax.plot_surface(np.asarray(xs), np.asarray(ys), np.asarray(zs), color="#85c1e9", alpha=0.92, linewidth=0, shade=False)
    ring = [2.0 * math.pi * k / 96.0 for k in range(97)]
    ax.plot(
        [atm * math.cos(a) for a in ring],
        [0.0 for _ in ring],
        [atm * math.sin(a) for a in ring],
        color="#5dade2",
        linewidth=1.0,
        label="120 km atmosphere",
    )
    ax.plot([p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts], color="#b9770e", linewidth=1.6, label="Ascent")
    pad = pts[0]
    ax.scatter([pad[0]], [pad[1]], [pad[2]], color="#c0392b", s=36, label="Vehicle on the pad")
    ax.legend(loc="upper left", fontsize=8)
    margin = 0.32 * earth
    reach = max(p[0] for p in pts)
    ceiling = max(p[2] for p in pts)
    floor = min(p[2] for p in pts)
    ax.set_xlim(-0.15 * earth, max(reach, 0.0) + margin)
    ax.set_ylim(-margin, margin)
    ax.set_zlim(min(floor, pad[2]) - 0.2 * margin, max(ceiling, pad[2]) + 0.12 * earth)
    ax.set_box_aspect((1.15, 0.7, 0.85))
    ax.view_init(elev=12, azim=-78)
    ax.set_title(PLOT_TITLE)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run(args: argparse.Namespace) -> int:
    bt = load_basic()
    if args.stages < 1 or len(args.stage) != args.stages:
        raise ValueError("pass one --stage per stage, bottom stage first")
    stages = [parse_stage(text) for text in args.stage]
    payload = 0.0 if args.payload is None else args.payload
    if payload < 0.0:
        raise ValueError("payload must be >= 0")
    if (args.gamma is None) == (args.kick is None):
        raise ValueError("pass --gamma or --kick")
    hold = args.gamma is not None
    theta0 = args.gamma if hold else bt.kick_flight_path_angle(args.kick)
    if not 0.0 <= theta0 <= math.pi / 2.0:
        raise ValueError("flight-path angle is outside 0 to pi/2")
    radius_body = bt.R_EARTH if args.radius is None else args.radius
    if args.mu is None:
        mu = 9.80665 * radius_body * radius_body
    else:
        mu = args.mu
    r_start = radius_body if args.alt is None else radius_body + args.alt
    drag_value = args.drag
    cd = args.cd
    area = args.area
    if drag_value is not None and cd is not None:
        raise ValueError("pass --drag or --cd, not both")
    if cd is not None and (area is None or area <= 0.0 or cd <= 0.0):
        raise ValueError("--cd needs --area > 0")
    jettison = parse_jettison(args.jettison) if args.jettison else None
    jet = jettison
    ns = argparse.Namespace(
        rho=args.rho,
        rho0=args.rho0,
        scale_height=args.scale_height,
        oat=None,
        rh=None,
        cd=cd,
        alt=args.alt,
    )
    density_at, density_source, _meta = bt.make_density_at(ns, radius_body, r_start)
    if cd is not None and density_at is None:
        raise ValueError("drag coefficient needs a density model")
    mass = payload + sum(stage["mp"] + stage["inert"] for stage in stages)
    state = (r_start, 0.0, 0.0, 0.0)
    t0 = 0.0
    rows: list[tuple] = []
    gravity = drag_loss = 0.0
    ideal = 0.0
    use_closed = (
        args.stages == 1
        and jettison is None
        and hold
        and cd is None
    )
    for index, stage in enumerate(stages, start=1):
        m0 = mass
        if "mdot" in stage and "tb" in stage:
            mdot = stage["mdot"]
            tb = stage["tb"]
            if abs(mdot * tb - stage["mp"]) > 1e-6 * stage["mp"]:
                raise ValueError(f"stage {index} tb and mdot disagree with mp")
        elif "tb" in stage:
            tb = stage["tb"]
            mdot = stage["mp"] / tb
        else:
            mdot = stage["mdot"]
            tb = stage["mp"] / mdot
        if tb <= 0.0 or mdot <= 0.0 or stage["mp"] >= m0:
            raise ValueError(f"stage {index} masses or burn time are not physical")
        mf = m0 - stage["mp"]
        c = stage["isp"] * 9.80665
        thrust = mdot * c
        ideal += bt.delta_v_vacuum(c, m0, mf)
        if use_closed:
            closed = bt.closed_constant_angle(
                m0=m0,
                mf=mf,
                mdot=mdot,
                tb=tb,
                c=c,
                g=bt.gravity_at_radius(mu, r_start),
                r_start=r_start,
                radius_body=radius_body,
                theta=theta0,
                drag=0.0 if drag_value is None else drag_value,
            )
            result_rows = []
            for time, rad, speed, theta in zip(closed["times"], closed["radii"], closed["speeds"], closed["thetas"]):
                alt = rad - radius_body
                rho = 0.0 if density_at is None else density_at(alt)
                result_rows.append((time, alt, speed, theta, rho, 0.5 * rho * speed * speed, m0 - mdot * time))
            piece = {
                "V_bo": closed["V_bo"],
                "theta_bo": closed["theta_bo"],
                "r_bo": closed["r_bo"],
                "phi_bo": closed["phi_bo"],
                "state": (closed["r_bo"], closed["phi_bo"], closed["V_bo"] * math.sin(theta0), closed["V_bo"] * math.cos(theta0)),
                "dvg": closed["dvg"],
                "dvD": closed["dvD"],
                "rows": result_rows,
                "solver": "closed_form",
            }
        else:
            heading = theta0 if hold or math.hypot(state[2], state[3]) < 1e-9 else state_theta(state, theta0)
            piece = ode_stage(
                bt,
                m0=m0,
                mdot=mdot,
                tb=tb,
                thrust=thrust,
                mu=mu,
                radius_body=radius_body,
                state=state,
                theta0=heading,
                hold_theta=hold,
                drag_value=drag_value,
                cd=cd,
                area=area,
                density_at=density_at,
                t0=t0,
                jettison=jet,
            )
            if piece.get("dropped"):
                jet = None
        gravity += piece["dvg"]
        drag_loss += piece["dvD"]
        rows.extend(piece["rows"])
        print_kv(f"stage_{index}_m0_kg", m0)
        print_kv(f"stage_{index}_mp_kg", stage["mp"])
        print_kv(f"stage_{index}_inert_kg", stage["inert"])
        print_kv(f"stage_{index}_tb_s", tb)
        print_kv(f"stage_{index}_gravity_loss_m_s", piece["dvg"])
        print_kv(f"stage_{index}_drag_loss_m_s", piece["dvD"])
        mass = mf - stage["inert"]
        if mass <= 0.0:
            raise ValueError("staging drops the mass through zero")
        state = piece["state"]
        t0 += tb
        theta0 = piece["theta_bo"] if not hold else theta0
    out = Path(args.out).resolve() if args.out else (SKILL_DIR / "multi_stage_ascent.png")
    table = Path(args.table).resolve() if args.table else out.with_suffix(".csv")
    write_csv(table, rows, [])
    payload_scene = scene_from_rows(rows, radius_body)
    plot_first_frame(out, payload_scene)
    html = out.with_suffix(".html")
    write_viewer(html, payload_scene)
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("stages", args.stages)
    print_kv("solver", "closed_form" if use_closed else "ode")
    print_kv("method", "constant_angle" if hold else "gravity_turn")
    print_kv("density_source", density_source)
    print_kv("dv_ideal_m_s", ideal)
    print_kv("gravity_loss_m_s", gravity)
    print_kv("drag_loss_m_s", drag_loss)
    print_kv("steering_loss_m_s", 0.0)
    print_kv("V_bo_m_s", piece["V_bo"])
    print_kv("gamma_bo_rad", piece["theta_bo"])
    print_kv("r_bo_m", piece["r_bo"])
    print_kv("Z_bo_m", piece["r_bo"] - radius_body)
    print_kv("payload_mf_kg", mass)
    print_kv("table", str(table))
    print_kv("graph", str(out))
    print_kv("viewer", str(html))
    if args.open:
        webbrowser.open(html.as_uri())
    return 0


def state_theta(state: tuple, fallback: float) -> float:
    speed = math.hypot(state[2], state[3])
    if speed < 1e-9:
        return fallback
    return math.atan2(state[2], state[3])


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    import io
    import tempfile

    bt = load_basic()
    with tempfile.TemporaryDirectory() as tmp:
        basic_png = str(Path(tmp) / "basic.png")
        ours = str(Path(tmp) / "ours.png")
        basic = [
            sys.executable,
            str(SKILL_DIR.parent / "ROCKET - BasicTrajectoryLossesFromBodySurface" / "basic_trajectory_losses_from_body_surface.py"),
            "--m0", "10000",
            "--mp", "6000",
            "--isp", "300",
            "--tb", "80",
            "--gamma", "1.0",
            "--out", basic_png,
        ]
        import subprocess
        proc = subprocess.run(basic, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            return fail(proc.stderr)
        basic_map = {}
        for line in proc.stdout.splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                basic_map[key] = value
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            code = main(
                [
                    "--stages", "1",
                    "--stage", "mp=6000,inert=1000,isp=300,tb=80",
                    "--payload", "3000",
                    "--gamma", "1.0",
                    "--out", ours,
                ]
            )
        finally:
            sys.stdout = old
        if code != 0:
            return fail(buf.getvalue())
        # m0 = 3000+6000+1000 = 10000. Matches the basic call.
        got = {}
        for line in buf.getvalue().splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                got[key] = value
        for key in ("gravity_loss_m_s", "V_bo_m_s", "Z_bo_m"):
            if abs(float(got[key]) - float(basic_map[key])) > 1e-4 * max(1.0, abs(float(basic_map[key]))):
                return fail(f"{key} {got[key]} vs {basic_map[key]}")
        # Two-stage mass drop: inert of stage 1 leaves the stack.
        buf2 = io.StringIO()
        sys.stdout = buf2
        try:
            code = main(
                [
                    "--stages", "2",
                    "--stage", "mp=100,inert=20,isp=250,tb=10",
                    "--stage", "mp=40,inert=10,isp=300,tb=8",
                    "--payload", "10",
                    "--gamma", "1.2",
                    "--out", str(Path(tmp) / "two.png"),
                ]
            )
        finally:
            sys.stdout = old
        if code != 0:
            return fail("two stage")
        text = buf2.getvalue()
        if "stage_1_m0_kg: 180" not in text:
            return fail("stage 1 ignition mass")
        if "stage_2_m0_kg:" not in text:
            return fail("stage 2 missing")
        m2 = float(next(line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("stage_2_m0_kg:")))
        # After stage 1: 180 - 100 propellant - 20 inert = 60. Upper is 40+10+10=60.
        if abs(m2 - 60.0) > 1e-6:
            return fail(f"stage 2 mass {m2}")
    print("CHECK PASS")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-stage powered ascent.")
    parser.add_argument("--stages", type=int)
    parser.add_argument("--stage", action="append", default=[])
    parser.add_argument("--payload", type=float, default=None)
    parser.add_argument("--gamma", type=float, default=None)
    parser.add_argument("--kick", type=float, default=None)
    parser.add_argument("--radius", type=float, default=None)
    parser.add_argument("--mu", type=float, default=None)
    parser.add_argument("--alt", type=float, default=None)
    parser.add_argument("--drag", type=float, default=None)
    parser.add_argument("--cd", type=float, default=None)
    parser.add_argument("--area", type=float, default=None)
    parser.add_argument("--rho", type=float, default=None)
    parser.add_argument("--rho0", type=float, default=None)
    parser.add_argument("--scale-height", type=float, default=None)
    parser.add_argument("--jettison", default=None, help="mass=<kg>,alt=<m> or mass=<kg>,time=<s>")
    parser.add_argument("--table", default=None)
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
