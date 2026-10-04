#!/usr/bin/env python3
"""Symmetric diamond airfoil by shock-expansion theory.

Inputs are freestream Mach, diamond half-angle, angle of attack, and gamma.
Leading-edge turns use oblique_shock_deflection or prandtl_meyer. Each
shoulder expands through twice the half-angle. Panel pressures become
pressure_coefficient values. Section normal and axial coefficients are the
frictionless diamond case of section_normal_coefficient and
section_axial_coefficient. Lift and drag use section_lift_from_normal and
section_drag_from_normal. Shock and Prandtl-Meyer numerics come from
AERO - PrandtlMeyerAndShocks.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

PLOT_TITLE = "Diamond airfoil shock-expansion"
DEFAULT_GAMMA = 1.4
MACH_MAX = 1.0e6
DETACH_TOL = 1.0e-10
ROOT_SPLIT = 1.0e-8
TURN_TOL = 1.0e-15

ASSUMPTIONS = (
    "calorically perfect gas; steady two-dimensional inviscid flow; "
    "symmetric diamond with maximum thickness at mid-chord; "
    "epsilon is the half-angle between the chord and each face; "
    "alpha is the angle of attack of the chord; "
    "upper LE turn is epsilon-alpha and lower LE turn is epsilon+alpha; "
    "a positive turn is a weak oblique shock from "
    "oblique_shock_deflection, oblique_shock_normal_mach, and "
    "normal_shock_pressure; a negative turn is a Prandtl-Meyer expansion; "
    "zero turn is a Mach wave; each shoulder expands through 2*epsilon; "
    "panel pressure coefficients use pressure_coefficient with "
    "q_inf = (gamma/2)*p_inf*M_inf**2 from dynamic_pressure; "
    "skin friction is omitted; cn and ca are the piecewise-constant "
    "diamond case of section_normal_coefficient and "
    "section_axial_coefficient; cl and cd use section_lift_from_normal "
    "and section_drag_from_normal; trailing-edge wake matching is not "
    "modeled; a detached LE shock or an impossible expansion stops the "
    "force coefficients"
)

SKILL_DIR = Path(__file__).resolve().parent
_PM = None


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def pm_mod():
    """Shock and Prandtl-Meyer helpers from AERO - PrandtlMeyerAndShocks."""
    global _PM
    if _PM is None:
        folder = str(SKILL_DIR.parent / "AERO - PrandtlMeyerAndShocks")
        if folder not in sys.path:
            sys.path.insert(0, folder)
        import prandtl_meyer_and_shocks as imported

        _PM = imported
    return _PM


def pressure_coefficient(p_over_pinf: float, mach: float, gamma: float) -> float:
    """Cp from pressure_coefficient and dynamic_pressure."""
    return (2.0 / (gamma * mach * mach)) * (p_over_pinf - 1.0)


def weak_oblique_shock(mach: float, gamma: float, delta: float) -> dict:
    """Weak attached oblique shock for deflection delta >= 0."""
    pm = pm_mod()
    mu = pm.mach_angle(mach)
    theta_star, delta_max = pm.maximum_deflection(mach, gamma)
    if delta <= TURN_TOL:
        down = pm.shock_downstream(mach, gamma, mu, 0.0)
        return {
            "ok": True,
            "wave": "mach-wave",
            "theta": mu,
            "M": down["M2"],
            "p_ratio": down["p_ratio"],
            "delta_max": delta_max,
        }
    if delta > delta_max + DETACH_TOL:
        return {
            "ok": False,
            "wave": "detached",
            "theta": None,
            "M": None,
            "p_ratio": None,
            "delta_max": delta_max,
        }
    if delta >= delta_max - DETACH_TOL:
        theta = theta_star
    else:
        theta = pm._bisect(mu, theta_star, delta, mach, gamma, decreasing=False)
        strong = pm._bisect(
            theta_star, math.pi / 2.0 - 1e-14, delta, mach, gamma, decreasing=True
        )
        if strong - theta < ROOT_SPLIT:
            theta = theta_star
    solved = pm.deflection_angle(theta, mach, gamma)
    down = pm.shock_downstream(mach, gamma, theta, solved)
    return {
        "ok": True,
        "wave": "shock",
        "theta": theta,
        "M": down["M2"],
        "p_ratio": down["p_ratio"],
        "delta_max": delta_max,
    }


def expand_flow(mach: float, gamma: float, turn: float) -> dict:
    """Prandtl-Meyer expansion through turn >= 0. Returns p2/p1 and M2."""
    pm = pm_mod()
    if mach <= 1.0:
        return {"ok": False, "wave": "subsonic", "M": None, "p_ratio": None}
    if turn <= TURN_TOL:
        return {"ok": True, "wave": "mach-wave", "M": mach, "p_ratio": 1.0}
    nu1 = pm.prandtl_meyer(mach, gamma)
    limit = pm.nu_max(gamma)
    if turn > limit - nu1 - 1e-12:
        return {"ok": False, "wave": "exceeds-maximum-turn", "M": None, "p_ratio": None}
    m2 = pm.invert_prandtl_meyer(nu1 + turn, gamma)
    return {
        "ok": True,
        "wave": "expansion",
        "M": m2,
        "p_ratio": pm.isentropic_pressure_ratio(mach, m2, gamma),
    }


def apply_surface_turn(
    mach: float, p_over_pinf: float, gamma: float, turn: float
) -> dict:
    """Turn the local stream. Positive turn compresses; negative expands."""
    if turn >= -TURN_TOL:
        shock = weak_oblique_shock(mach, gamma, max(0.0, turn))
        if not shock["ok"]:
            return {
                "ok": False,
                "wave": shock["wave"],
                "M": None,
                "p_over_pinf": None,
                "theta": None,
                "delta_max": shock.get("delta_max"),
            }
        return {
            "ok": True,
            "wave": shock["wave"],
            "M": shock["M"],
            "p_over_pinf": p_over_pinf * shock["p_ratio"],
            "theta": shock["theta"],
            "delta_max": shock["delta_max"],
        }
    expansion = expand_flow(mach, gamma, -turn)
    if not expansion["ok"]:
        return {
            "ok": False,
            "wave": expansion["wave"],
            "M": None,
            "p_over_pinf": None,
            "theta": None,
            "delta_max": None,
        }
    return {
        "ok": True,
        "wave": expansion["wave"],
        "M": expansion["M"],
        "p_over_pinf": p_over_pinf * expansion["p_ratio"],
        "theta": None,
        "delta_max": None,
    }


def evaluate(mach: float, gamma: float, epsilon: float, alpha: float) -> dict:
    """Four panel states and section coefficients for a diamond airfoil."""
    delta_u1 = epsilon - alpha
    delta_l1 = epsilon + alpha
    shoulder = 2.0 * epsilon

    upper_le = apply_surface_turn(mach, 1.0, gamma, delta_u1)
    lower_le = apply_surface_turn(mach, 1.0, gamma, delta_l1)

    state: dict = {
        "mach": mach,
        "gamma": gamma,
        "epsilon": epsilon,
        "alpha": alpha,
        "delta_u1": delta_u1,
        "delta_l1": delta_l1,
        "shoulder": shoulder,
        "solution": "ok",
        "u1": upper_le,
        "l1": lower_le,
        "u2": None,
        "l2": None,
        "Cp_u1": None,
        "Cp_u2": None,
        "Cp_l1": None,
        "Cp_l2": None,
        "cn": None,
        "ca": None,
        "cl": None,
        "cd": None,
    }

    if not upper_le["ok"]:
        state["solution"] = f"upper-le-{upper_le['wave']}"
        return state
    if not lower_le["ok"]:
        state["solution"] = f"lower-le-{lower_le['wave']}"
        return state

    upper_te = apply_surface_turn(
        upper_le["M"], upper_le["p_over_pinf"], gamma, -shoulder
    )
    lower_te = apply_surface_turn(
        lower_le["M"], lower_le["p_over_pinf"], gamma, -shoulder
    )
    state["u2"] = upper_te
    state["l2"] = lower_te
    if not upper_te["ok"]:
        state["solution"] = f"upper-te-{upper_te['wave']}"
        return state
    if not lower_te["ok"]:
        state["solution"] = f"lower-te-{lower_te['wave']}"
        return state

    cp_u1 = pressure_coefficient(upper_le["p_over_pinf"], mach, gamma)
    cp_u2 = pressure_coefficient(upper_te["p_over_pinf"], mach, gamma)
    cp_l1 = pressure_coefficient(lower_le["p_over_pinf"], mach, gamma)
    cp_l2 = pressure_coefficient(lower_te["p_over_pinf"], mach, gamma)
    cn = 0.5 * (cp_l1 + cp_l2 - cp_u1 - cp_u2)
    ca = 0.5 * math.tan(epsilon) * (cp_u1 + cp_l1 - cp_u2 - cp_l2)
    cl = cn * math.cos(alpha) - ca * math.sin(alpha)
    cd = cn * math.sin(alpha) + ca * math.cos(alpha)
    state.update(
        Cp_u1=cp_u1,
        Cp_u2=cp_u2,
        Cp_l1=cp_l1,
        Cp_l2=cp_l2,
        cn=cn,
        ca=ca,
        cl=cl,
        cd=cd,
        solution="ok",
    )
    return state


def require_inputs(mach: float, gamma: float, epsilon: float, alpha: float) -> None:
    if not math.isfinite(mach) or mach <= 1.0 or mach > MACH_MAX:
        raise ValueError(f"--mach must be greater than 1 and at most {MACH_MAX:g}")
    if not math.isfinite(gamma) or gamma <= 1.0:
        raise ValueError("--gamma must be greater than 1")
    if not math.isfinite(epsilon) or epsilon <= 0.0 or epsilon >= math.pi / 2.0:
        raise ValueError(
            "--epsilon must be a diamond half-angle in radians, "
            "strictly between 0 and pi/2 (convert degrees with pi/180)"
        )
    if not math.isfinite(alpha) or abs(alpha) >= math.pi / 2.0:
        raise ValueError(
            "--alpha must be an angle of attack in radians with absolute "
            "value less than pi/2 (convert degrees with pi/180)"
        )


def _panel_keys(prefix: str, panel: dict | None) -> None:
    if panel is None:
        return
    print_kv(f"wave_{prefix}", panel["wave"])
    if panel.get("M") is not None:
        print_kv(f"M_{prefix}", panel["M"])
    if panel.get("p_over_pinf") is not None:
        print_kv(f"p_{prefix}_over_pinf", panel["p_over_pinf"])
    if panel.get("theta") is not None:
        print_kv(f"theta_{prefix}_rad", panel["theta"])
        print_kv(f"theta_{prefix}_deg", math.degrees(panel["theta"]))
    if panel.get("delta_max") is not None and panel["wave"] == "detached":
        print_kv(f"delta_max_{prefix}_rad", panel["delta_max"])
        print_kv(f"delta_max_{prefix}_deg", math.degrees(panel["delta_max"]))


def emit(state: dict, gamma_source: str, graph: str) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("gamma", state["gamma"])
    print_kv("gamma_source", gamma_source)
    print_kv("M_inf", state["mach"])
    print_kv("epsilon_rad", state["epsilon"])
    print_kv("epsilon_deg", math.degrees(state["epsilon"]))
    print_kv("alpha_rad", state["alpha"])
    print_kv("alpha_deg", math.degrees(state["alpha"]))
    print_kv("delta_u1_rad", state["delta_u1"])
    print_kv("delta_u1_deg", math.degrees(state["delta_u1"]))
    print_kv("delta_l1_rad", state["delta_l1"])
    print_kv("delta_l1_deg", math.degrees(state["delta_l1"]))
    print_kv("shoulder_rad", state["shoulder"])
    print_kv("shoulder_deg", math.degrees(state["shoulder"]))
    print_kv("solution", state["solution"])
    _panel_keys("u1", state["u1"])
    _panel_keys("u2", state["u2"])
    _panel_keys("l1", state["l1"])
    _panel_keys("l2", state["l2"])
    if state["solution"] == "ok":
        print_kv("Cp_u1", state["Cp_u1"])
        print_kv("Cp_u2", state["Cp_u2"])
        print_kv("Cp_l1", state["Cp_l1"])
        print_kv("Cp_l2", state["Cp_l2"])
        print_kv("cn", state["cn"])
        print_kv("ca", state["ca"])
        print_kv("cl", state["cl"])
        print_kv("cd", state["cd"])
    print_kv("graph", graph)


def _fmt(value: float) -> str:
    return f"{value:.4g}"


def _rotate(x: float, y: float, angle: float) -> tuple[float, float]:
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return x * cosine - y * sine, x * sine + y * cosine


def _diamond_points(epsilon: float, alpha: float, chord: float = 1.0) -> dict[str, tuple[float, float]]:
    """Airfoil vertices in freestream axes with freestream to +x.

    Positive alpha is nose-up. The body is rotated by -alpha so the upper LE
    face lies at +(epsilon - alpha) to the freestream, matching delta_u1.
    """
    half = 0.5 * chord
    height = half * math.tan(epsilon)
    body = {
        "le": (0.0, 0.0),
        "upper": (half, height),
        "te": (chord, 0.0),
        "lower": (half, -height),
    }
    return {name: _rotate(x, y, -alpha) for name, (x, y) in body.items()}


def _ray(
    ax,
    origin: tuple[float, float],
    angle: float,
    length: float,
    color: str,
    style: str = "-",
    width: float = 1.6,
) -> None:
    ax.plot(
        [origin[0], origin[0] + length * math.cos(angle)],
        [origin[1], origin[1] + length * math.sin(angle)],
        color=color,
        lw=width,
        ls=style,
        zorder=4,
    )


def _fan_rays(
    ax,
    origin: tuple[float, float],
    wall_in: float,
    mach_in: float,
    gamma: float,
    turn: float,
    side: float,
    length: float,
) -> None:
    """Draw a Prandtl-Meyer fan. side=+1 is above; side=-1 is below."""
    pm = pm_mod()
    rays = 6
    nu0 = pm.prandtl_meyer(mach_in, gamma)
    for index in range(rays + 1):
        fraction = index / rays
        # Flow turns away from the body: upper side decreases wall angle.
        turned = wall_in - side * fraction * turn
        local_mach = pm.invert_prandtl_meyer(nu0 + fraction * turn, gamma)
        mu = pm.mach_angle(local_mach)
        angle = turned + side * mu
        width = 2.0 if index in (0, rays) else 0.9
        _ray(ax, origin, angle, length, "#1a5276", width=width)


def _draw_le_wave(ax, origin: tuple[float, float], state: dict, surface: str) -> None:
    """Leading-edge shock, expansion, or Mach wave on one surface."""
    panel = state[surface]
    delta = state["delta_u1"] if surface == "u1" else state["delta_l1"]
    side = 1.0 if surface == "u1" else -1.0
    if not panel["ok"]:
        if panel["wave"] == "detached":
            y = 0.55 if surface == "u1" else -0.6
            label = "upper" if surface == "u1" else "lower"
            ax.text(0.05, y, f"{label} LE detached", color="#c0392b", fontsize=9)
        return
    if panel["wave"] == "shock" and panel["theta"] is not None:
        _ray(ax, origin, side * panel["theta"], 0.95, "#c0392b")
    elif panel["wave"] == "expansion":
        wall_in = 0.0
        _fan_rays(
            ax,
            origin,
            wall_in,
            state["mach"],
            state["gamma"],
            abs(delta),
            side=side,
            length=0.75,
        )
    elif panel["wave"] == "mach-wave":
        mu = pm_mod().mach_angle(state["mach"])
        _ray(ax, origin, side * mu, 0.9, "#1a5276", style="--")


def write_figure(state: dict, out_path: Path) -> None:
    import matplotlib

    if "matplotlib.pyplot" not in sys.modules:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon

    epsilon = state["epsilon"]
    alpha = state["alpha"]
    pts = _diamond_points(epsilon, alpha)
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#d5d8dc")

    body = [pts["le"], pts["upper"], pts["te"], pts["lower"]]
    ax.add_patch(
        Polygon(
            body,
            closed=True,
            facecolor="#d5d8dc",
            edgecolor="#1c2833",
            lw=1.8,
            zorder=3,
        )
    )
    for y_pos in (-0.35, 0.0, 0.35):
        ax.annotate(
            "",
            xy=(-0.08, y_pos),
            xytext=(-0.55, y_pos),
            arrowprops={"arrowstyle": "-|>", "color": "#1a5276", "lw": 1.2},
        )
    ax.text(-0.52, 0.42, r"$M_\infty$", color="#1a5276", fontsize=11)

    chord_end = _rotate(1.15, 0.0, -alpha)
    ax.plot(
        [0.0, chord_end[0]],
        [0.0, chord_end[1]],
        color="#aab7b8",
        lw=0.8,
        ls="--",
        zorder=2,
    )

    _draw_le_wave(ax, pts["le"], state, "u1")
    _draw_le_wave(ax, pts["le"], state, "l1")

    # Shoulder fans. Wall_in is the surface inclination to the freestream.
    if state["u1"]["ok"] and state["u2"] is not None and state["u2"]["ok"]:
        _fan_rays(
            ax,
            pts["upper"],
            state["delta_u1"],
            state["u1"]["M"],
            state["gamma"],
            state["shoulder"],
            side=+1.0,
            length=0.7,
        )
    if state["l1"]["ok"] and state["l2"] is not None and state["l2"]["ok"]:
        _fan_rays(
            ax,
            pts["lower"],
            -state["delta_l1"],
            state["l1"]["M"],
            state["gamma"],
            state["shoulder"],
            side=-1.0,
            length=0.7,
        )

    if state["solution"] == "ok":
        detail = rf"$c_l={_fmt(state['cl'])}$,  $c_d={_fmt(state['cd'])}$"
    else:
        detail = f"solution: {state['solution']}"

    ax.set_xlim(-0.65, 1.55)
    ax.set_ylim(-0.95, 0.95)
    ax.set_title(
        PLOT_TITLE
        + "\n"
        + (
            f"M = {_fmt(state['mach'])},  "
            f"gamma = {_fmt(state['gamma'])},  "
            f"epsilon = {_fmt(math.degrees(epsilon))}\u00b0,  "
            f"alpha = {_fmt(math.degrees(alpha))}\u00b0\n"
            + detail
        ),
        fontsize=11,
    )
    fig.text(
        0.5,
        0.02,
        "Red: oblique shocks. Blue: Prandtl-Meyer fans. Wave angles are drawn to scale.",
        ha="center",
        fontsize=8,
        color="#566573",
    )
    fig.tight_layout(rect=(0.0, 0.04, 1.0, 0.98))
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"CHECK FAIL: {message}", file=sys.stderr)
        return 1

    def near(got: float, expected: float, label: str, tol: float = 1e-9) -> int | None:
        if abs(got - expected) > tol * max(1.0, abs(expected)):
            return fail(f"{label} is {got}, expected {expected}")
        return None

    gamma = 1.4
    mach = 2.0
    epsilon = math.radians(10.0)
    alpha0 = 0.0
    zero = evaluate(mach, gamma, epsilon, alpha0)
    if zero["solution"] != "ok":
        return fail(f"alpha=0 solution was {zero['solution']}")
    if near(zero["cl"], 0.0, "zero-alpha lift", tol=1e-12):
        return 1
    if not (zero["cd"] > 0.0):
        return fail("zero-alpha drag was not positive")
    if near(zero["u1"]["p_over_pinf"], zero["l1"]["p_over_pinf"], "LE pressure symmetry", tol=1e-12):
        return 1
    if near(zero["u2"]["p_over_pinf"], zero["l2"]["p_over_pinf"], "TE pressure symmetry", tol=1e-12):
        return 1
    if zero["u1"]["wave"] != "shock" or zero["u2"]["wave"] != "expansion":
        return fail("alpha=0 waves were not shock then expansion")

    # LE shock at 10 deg must match the wedge program.
    pm = pm_mod()
    wedge = pm.evaluate(mach, gamma, epsilon)
    if near(zero["u1"]["p_over_pinf"], wedge["p2_over_p1"], "LE pressure vs wedge", tol=1e-10):
        return 1
    if near(zero["u1"]["M"], wedge["M2"], "LE Mach vs wedge", tol=1e-10):
        return 1

    # Shoulder expands post-shock flow through 2*epsilon.
    fan_turn = pm.prandtl_meyer(zero["u2"]["M"], gamma) - pm.prandtl_meyer(zero["u1"]["M"], gamma)
    if near(fan_turn, 2.0 * epsilon, "shoulder turning", tol=1e-8):
        return 1
    if not (zero["u2"]["p_over_pinf"] < zero["u1"]["p_over_pinf"]):
        return fail("shoulder did not drop the pressure")

    # Diamond integral identities with artificial Cp.
    cp_u1, cp_u2, cp_l1, cp_l2 = 0.2, -0.1, 0.4, 0.0
    cn = 0.5 * (cp_l1 + cp_l2 - cp_u1 - cp_u2)
    ca = 0.5 * math.tan(epsilon) * (cp_u1 + cp_l1 - cp_u2 - cp_l2)
    if near(cn, 0.5 * (0.4 + 0.0 - 0.2 + 0.1), "cn identity"):
        return 1
    if near(ca, 0.5 * math.tan(epsilon) * (0.2 + 0.4 + 0.1 - 0.0), "ca identity"):
        return 1
    alpha = math.radians(5.0)
    cl = cn * math.cos(alpha) - ca * math.sin(alpha)
    cd = cn * math.sin(alpha) + ca * math.cos(alpha)
    if near(cl, cn * math.cos(alpha) - ca * math.sin(alpha), "cl identity"):
        return 1
    if near(cd, cn * math.sin(alpha) + ca * math.cos(alpha), "cd identity"):
        return 1

    lifted = evaluate(mach, gamma, epsilon, alpha)
    if lifted["solution"] != "ok":
        return fail(f"alpha=5 deg solution was {lifted['solution']}")
    if not (lifted["cl"] > 0.0):
        return fail("positive alpha did not produce positive lift")
    if not (lifted["l1"]["p_over_pinf"] > lifted["u1"]["p_over_pinf"]):
        return fail("lower LE was not higher pressure than upper LE")
    if near(
        pressure_coefficient(lifted["u1"]["p_over_pinf"], mach, gamma),
        lifted["Cp_u1"],
        "Cp_u1 chain",
        tol=1e-12,
    ):
        return 1

    # Upper LE expands when alpha > epsilon; keep lower LE attached at Mach 2.
    expanded = evaluate(mach, gamma, epsilon, math.radians(12.0))
    if expanded["solution"] != "ok":
        return fail(f"alpha>epsilon solution was {expanded['solution']}")
    if expanded["u1"]["wave"] != "expansion":
        return fail("upper LE was not an expansion when alpha > epsilon")
    if not (expanded["u1"]["p_over_pinf"] < 1.0):
        return fail("upper LE expansion pressure was not below freestream")

    detached = evaluate(2.0, gamma, math.radians(30.0), 0.0)
    if detached["solution"] != "upper-le-detached" and detached["solution"] != "lower-le-detached":
        # At alpha=0 both detach together; upper is checked first.
        if "detached" not in detached["solution"]:
            return fail(f"30 deg half-angle at Mach 2 did not detach: {detached['solution']}")
    if detached["cl"] is not None:
        return fail("detached case invented lift")

    # Cp composition: p/pinf = 1 -> Cp = 0.
    if near(pressure_coefficient(1.0, 2.0, 1.4), 0.0, "freestream Cp"):
        return 1
    # dynamic_pressure: q/p = gamma/2 * M^2; Cp = (p/pinf-1)/(q/pinf).
    if near(pressure_coefficient(2.0, 2.0, 1.4), 2.0 / (1.4 * 4.0), "Cp from p-ratio"):
        return 1

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

    with tempfile.TemporaryDirectory() as folder:
        out_path = str(Path(folder) / "diamond.png")
        code, text, err = capture(
            [
                "--mach",
                "2",
                "--epsilon",
                str(epsilon),
                "--alpha",
                "0",
                "--gamma",
                "1.4",
                "--out",
                out_path,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        for key in (
            "solution: ok",
            "p_u1_over_pinf:",
            "p_u2_over_pinf:",
            "p_l1_over_pinf:",
            "p_l2_over_pinf:",
            "cl:",
            "cd:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")
        if not Path(out_path).is_file() or Path(out_path).read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
            return fail("run did not write a PNG")

        code, text, err = capture(
            ["--mach", "2", "--epsilon", str(epsilon), "--alpha", "0"]
        )
        if code != 0 or "gamma_source: default" not in text:
            return fail("omitted gamma was not marked default")

        code, _text, err = capture(
            ["--mach", "0.8", "--epsilon", str(epsilon), "--alpha", "0"]
        )
        if code != 2 or "error:" not in err:
            return fail("subsonic Mach was accepted")
        code, _text, err = capture(["--mach", "2", "--alpha", "0"])
        if code != 2:
            return fail("missing epsilon was accepted")
        code, _text, err = capture(
            ["--mach", "2", "--epsilon", str(math.radians(30.0)), "--alpha", "0"]
        )
        if code != 0 or "solution: upper-le-detached" not in _text:
            return fail(f"detached stdout failed: {err or _text}")
        if "cl:" in _text.split("solution:")[0] or "\ncl:" in _text:
            # cl should not appear after a failed solution
            if any(line.startswith("cl:") for line in _text.splitlines()):
                return fail("detached stdout printed cl")

    print("check: pass")
    print_kv("cl_alpha0", zero["cl"])
    print_kv("cd_alpha0", zero["cd"])
    print_kv("cl_alpha5", lifted["cl"])
    print_kv("cd_alpha5", lifted["cd"])
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Symmetric diamond airfoil by shock-expansion theory."
    )
    parser.add_argument("--mach", type=float, default=None, help="freestream Mach, greater than 1")
    parser.add_argument(
        "--epsilon",
        type=float,
        default=None,
        help="diamond half-angle in radians, strictly between 0 and pi/2",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        help="angle of attack in radians, absolute value less than pi/2",
    )
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help=f"ratio of specific heats (default {DEFAULT_GAMMA})",
    )
    parser.add_argument("--out", type=str, default=None, help="PNG output path")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.mach is None or args.epsilon is None or args.alpha is None:
        print("error: requires --mach, --epsilon, and --alpha", file=sys.stderr)
        return 2
    gamma = DEFAULT_GAMMA if args.gamma is None else args.gamma
    gamma_source = "default" if args.gamma is None else "supplied"
    try:
        require_inputs(args.mach, gamma, args.epsilon, args.alpha)
        state = evaluate(args.mach, gamma, args.epsilon, args.alpha)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    out_path = (
        Path(args.out)
        if args.out
        else Path(__file__).resolve().parent / "diamond_airfoil_shock_expansion.png"
    )
    out_path = out_path.resolve()
    if not out_path.parent.is_dir():
        print(f"error: PNG directory does not exist: {out_path.parent}", file=sys.stderr)
        return 2
    try:
        write_figure(state, out_path)
    except Exception as exc:
        print(f"error: could not write the wave figure: {exc}", file=sys.stderr)
        return 2
    emit(state, gamma_source, str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
