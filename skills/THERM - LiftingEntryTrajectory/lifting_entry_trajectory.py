#!/usr/bin/env python3
"""Planar point-mass lifting entry with constant ballistic coefficient and L/D.

gamma is positive below the local horizontal. Optional Earth rotation converts
an inertial entry state to air-relative speed and flight-path angle, then
integrates in the rotating frame with Coriolis and centrifugal terms.
Latitude and heading are held constant.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Lifting entry trajectory"
G0 = 9.80665
R0_EARTH = 6.3742e6
MU_EARTH = G0 * R0_EARTH * R0_EARTH
OMEGA_EARTH = 7.2921159e-5
DEFAULT_RTOL = 1e-6
DEFAULT_MAX_TIME = 3000.0
DEFAULT_END_ALTITUDE = 0.0
H_MAX = 5.0
H_MIN = 1e-8
ATOL = (1e-4, 1e-10, 1e-3, 1e-2)

# NACA TN 4047 Earth fit, same conversion as THERM - BallisticEntryPeakLoad.
SLUG_FT3_TO_KG_M3 = 515.3788184
FT_TO_M = 0.3048
DEFAULT_RHO_REF = 0.0034 * SLUG_FT3_TO_KG_M3
DEFAULT_H = 22000.0 * FT_TO_M
DEFAULT_Z_REF = 0.0

SKILL_DIR = Path(__file__).resolve().parent
SKILLS = SKILL_DIR.parent

# Dormand-Prince 5(4). Row i (0-based, stage i+1) multiplies earlier k's.
_C = (0.0, 0.2, 0.3, 0.8, 8.0 / 9.0, 1.0, 1.0)
_A = (
    (),
    (0.2,),
    (3.0 / 40.0, 9.0 / 40.0),
    (44.0 / 45.0, -56.0 / 15.0, 32.0 / 9.0),
    (19372.0 / 6561.0, -25360.0 / 2187.0, 64448.0 / 6561.0, -212.0 / 729.0),
    (9017.0 / 3168.0, -355.0 / 33.0, 46732.0 / 5247.0, 49.0 / 176.0, -5103.0 / 18656.0),
    (35.0 / 384.0, 0.0, 500.0 / 1113.0, 125.0 / 192.0, -2187.0 / 6784.0, 11.0 / 84.0),
)
_B5 = (35.0 / 384.0, 0.0, 500.0 / 1113.0, 125.0 / 192.0, -2187.0 / 6784.0, 11.0 / 84.0, 0.0)
_B4 = (
    5179.0 / 57600.0,
    0.0,
    7571.0 / 16695.0,
    393.0 / 640.0,
    -92097.0 / 339200.0,
    187.0 / 2100.0,
    1.0 / 40.0,
)

_US1976: tuple[object, object] | None = None


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


def ballistic_coefficient(mass: float, cd: float, area: float) -> float:
    """ballistic_coefficient: B = m/(Cd*A)."""
    return mass / (cd * area)


def resolve_ballistic(
    beta: float | None,
    mass: float | None,
    cd: float | None,
    area: float | None,
) -> tuple[float, str]:
    parts = (mass is not None, cd is not None, area is not None)
    if beta is not None:
        require_positive("beta", beta)
        if any(parts):
            if not all(parts):
                raise ValueError(
                    "pass all of mass, cd, and area when checking against beta"
                )
            built = ballistic_coefficient(mass, cd, area)
            if not close(float(beta), built):
                raise ValueError(
                    f"beta {beta:g} disagrees with m/(Cd*A) = {built:g}"
                )
        return float(beta), "flag"
    if all(parts):
        require_positive("mass", mass)
        require_positive("drag coefficient", cd)
        require_positive("reference area", area)
        return ballistic_coefficient(mass, cd, area), "mass_cd_area"
    if any(parts):
        raise ValueError("pass mass, cd, and area together, or pass beta")
    raise ValueError("pass beta, or mass with cd and area")


def resolve_atmosphere(
    kind: str,
    scale_height: float | None,
    rho_ref: float | None,
    z_ref: float | None,
) -> tuple[str, float, float, float]:
    supplied = (
        scale_height is not None,
        rho_ref is not None,
        z_ref is not None,
    )
    if kind not in ("exponential", "us1976"):
        raise ValueError("atmosphere must be exponential or us1976")
    if kind == "us1976":
        if any(supplied):
            raise ValueError(
                "scale_height, rho_ref, and z_ref apply only when atmosphere is exponential"
            )
        return "us1976", math.nan, math.nan, math.nan
    if not any(supplied):
        return "exponential", DEFAULT_H, DEFAULT_RHO_REF, DEFAULT_Z_REF
    if not all(supplied):
        raise ValueError(
            "pass scale_height, rho_ref, and z_ref together to override "
            "the Allen-Eggers Earth default"
        )
    require_positive("scale_height", scale_height)
    require_positive("rho_ref", rho_ref)
    require_finite("z_ref", z_ref)
    return "exponential", float(scale_height), float(rho_ref), float(z_ref)


def exponential_density(
    altitude: float, rho_ref: float, z_ref: float, scale_height: float
) -> float:
    """exponential_atmosphere_density."""
    return rho_ref * math.exp(-(altitude - z_ref) / scale_height)


def _load_module(folder: str, filename: str, name: str):
    path = SKILLS / folder / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def us1976_density(altitude: float) -> float:
    """1976 density: Standard1976 at or below 86 km, DensityAbove86km above."""
    global _US1976
    if _US1976 is None:
        standard = _load_module("ATMOS - Standard1976", "standard_1976.py", "standard1976_entry")
        dense = _load_module("ATMOS - DensityAbove86km", "density_above_86km.py", "density86_entry")
        _US1976 = (standard, dense)
    standard, dense = _US1976
    z = altitude
    if z < 0.0:
        z = 0.0
    if z <= 86000.0:
        return float(standard.atmosphere(z)["rho"])
    if z > 1_000_000.0:
        z = 1_000_000.0
    return float(dense.state_at(z)["rho"])


def bank_schedule_argument(text: str) -> str:
    """Argparse marker so the MCP schema accepts a list or a JSON string."""
    return text


def parse_bank_schedule(text: str | list) -> list[tuple[float, float]]:
    if isinstance(text, str):
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "bank_schedule must be a JSON list of objects with t_s and bank_deg"
            ) from exc
    elif isinstance(text, list):
        raw = text
    else:
        raise ValueError(
            "bank_schedule must be a list of objects with t_s and bank_deg"
        )
    if not isinstance(raw, list) or not raw:
        raise ValueError("bank_schedule must be a non-empty list of objects")
    points: list[tuple[float, float]] = []
    for item in raw:
        if isinstance(item, (list, tuple)):
            raise ValueError(
                "bank_schedule must be objects with t_s and bank_deg, not pair arrays"
            )
        if not isinstance(item, dict):
            raise ValueError("bank_schedule entries must be objects with t_s and bank_deg")
        if "t_s" not in item or "bank_deg" not in item:
            raise ValueError("bank_schedule entries need t_s and bank_deg")
        try:
            t_s = float(item["t_s"])
            bank_deg = float(item["bank_deg"])
        except (TypeError, ValueError) as exc:
            raise ValueError("bank_schedule t_s and bank_deg must be numbers") from exc
        require_finite("bank_schedule t_s", t_s)
        require_finite("bank_schedule bank_deg", bank_deg)
        points.append((t_s, bank_deg))
    for earlier, later in zip(points, points[1:]):
        if later[0] <= earlier[0]:
            raise ValueError("bank_schedule must be sorted by increasing t_s")
    return points


def bank_deg_at(t: float, points: list[tuple[float, float]]) -> float:
    if t <= points[0][0]:
        return points[0][1]
    if t >= points[-1][0]:
        return points[-1][1]
    for (t0, b0), (t1, b1) in zip(points, points[1:]):
        if t <= t1:
            weight = (t - t0) / (t1 - t0)
            return b0 + weight * (b1 - b0)
    return points[-1][1]


def air_relative_entry(
    speed: float,
    gamma: float,
    radius_m: float,
    latitude_rad: float,
    heading_rad: float,
    omega: float,
) -> tuple[float, float, float]:
    """Inertial V, gamma, heading to air-relative V, gamma, heading.

    heading_rad is the inertial azimuth from north. The returned heading is
    the air-relative azimuth after subtracting the planet's eastward velocity.
    The trajectory still holds the inertial heading.
    """
    horizontal = speed * math.cos(gamma)
    down = speed * math.sin(gamma)
    north = horizontal * math.cos(heading_rad)
    east = horizontal * math.sin(heading_rad) - omega * radius_m * math.cos(latitude_rad)
    speed_air = math.sqrt(north * north + east * east + down * down)
    if not math.isfinite(speed_air) or speed_air <= 0.0:
        raise ValueError("air-relative entry speed must be finite and > 0")
    sin_gamma = max(-1.0, min(1.0, down / speed_air))
    return speed_air, math.asin(sin_gamma), math.atan2(east, north)


def _axpy(y: tuple[float, ...], factor: float, k: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(yi + factor * ki for yi, ki in zip(y, k))


def _combine(
    y: tuple[float, ...],
    dt: float,
    ks: list[tuple[float, ...]],
    coeffs: tuple[float, ...],
) -> tuple[float, ...]:
    out = list(y)
    for coef, k in zip(coeffs, ks):
        if coef == 0.0:
            continue
        step = dt * coef
        for i, ki in enumerate(k):
            out[i] += step * ki
    return (out[0], out[1], out[2], out[3])


class _SpeedFloor(Exception):
    """Speed fell below 1 m/s. The samples already stored are the result."""


class _Run:
    def __init__(
        self,
        beta: float,
        lod: float,
        planet_radius: float,
        mu: float,
        density,
        bank_of_t,
        rotating: bool,
        latitude_rad: float,
        heading_rad: float,
        omega: float,
        end_altitude: float,
        skip_altitude: float,
        max_time: float,
    ) -> None:
        self.beta = beta
        self.lod = lod
        self.planet_radius = planet_radius
        self.mu = mu
        self.density = density
        self.bank_of_t = bank_of_t
        self.rotating = rotating
        self.latitude_rad = latitude_rad
        self.heading_rad = heading_rad
        self.omega = omega
        self.end_altitude = end_altitude
        self.skip_altitude = skip_altitude
        self.max_time = max_time

    def rates(self, t: float, y: tuple[float, float, float, float]) -> tuple[tuple[float, float, float, float], float]:
        speed, gamma, altitude, _downrange = y
        if not math.isfinite(speed) or speed < 1.0:
            if math.isfinite(speed):
                raise _SpeedFloor()
            raise ValueError("speed collapsed below 1 m/s before an end condition")
        radius = self.planet_radius + altitude
        if radius <= 0.0:
            raise ValueError("radius must stay positive")
        gravity = self.mu / (radius * radius)
        rho = self.density(altitude)
        if rho < 0.0 or not math.isfinite(rho):
            raise ValueError("density must be finite and >= 0")
        drag_over_m = rho * speed * speed / (2.0 * self.beta)
        lift_over_m = self.lod * drag_over_m
        bank = math.radians(self.bank_of_t(t))
        d_speed = -drag_over_m + gravity * math.sin(gamma)
        d_gamma = -(
            lift_over_m * math.cos(bank) - (gravity - speed * speed / radius) * math.cos(gamma)
        ) / speed
        d_alt = -speed * math.sin(gamma)
        d_range = speed * math.cos(gamma) * self.planet_radius / radius
        if self.rotating:
            cos_lat = math.cos(self.latitude_rad)
            sin_lat = math.sin(self.latitude_rad)
            cos_g = math.cos(gamma)
            sin_g = math.sin(gamma)
            cos_psi = math.cos(self.heading_rad)
            sin_psi = math.sin(self.heading_rad)
            omega = self.omega
            d_speed += -omega * omega * radius * cos_lat * (
                cos_lat * sin_g + sin_lat * cos_g * cos_psi
            )
            d_gamma += -(
                2.0 * omega * speed * cos_lat * sin_psi
                + omega
                * omega
                * radius
                * cos_lat
                * (cos_lat * cos_g - sin_lat * sin_g * cos_psi)
            ) / speed
        load_g = drag_over_m * math.sqrt(1.0 + self.lod * self.lod) / G0
        return (d_speed, d_gamma, d_alt, d_range), load_g


def _rk4(run: _Run, t: float, y: tuple[float, ...], dt: float) -> tuple[float, ...]:
    k1 = run.rates(t, y)[0]
    k2 = run.rates(t + 0.5 * dt, _axpy(y, 0.5 * dt, k1))[0]
    k3 = run.rates(t + 0.5 * dt, _axpy(y, 0.5 * dt, k2))[0]
    k4 = run.rates(t + dt, _axpy(y, dt, k3))[0]
    out = list(y)
    for i in range(4):
        out[i] += (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
    return (out[0], out[1], out[2], out[3])


def _rk45(
    run: _Run, t: float, y: tuple[float, ...], dt: float
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    ks: list[tuple[float, ...]] = []
    for stage, coeffs in enumerate(_A):
        yt = y
        if coeffs:
            yt = _combine(y, dt, ks, coeffs)
        ks.append(run.rates(t + _C[stage] * dt, yt)[0])
    y5 = _combine(y, dt, ks, _B5)
    y4 = _combine(y, dt, ks, _B4)
    return y5, y4


def _rk45_error(y: tuple[float, ...], y5: tuple[float, ...], y4: tuple[float, ...], rtol: float, atol_scale: float) -> float:
    total = 0.0
    for i in range(4):
        scale = atol_scale * ATOL[i] + rtol * max(abs(y5[i]), abs(y[i]))
        diff = (y5[i] - y4[i]) / scale
        total += diff * diff
    return math.sqrt(total / 4.0)


def _event_fraction(
    h0: float,
    h1: float,
    end_altitude: float,
    skip_altitude: float,
    seen_below: bool,
) -> tuple[float | None, str | None]:
    """Fraction of the step to the first stop, if this step crosses one."""
    hits: list[tuple[float, str]] = []
    if h0 > end_altitude >= h1 and h0 != h1:
        hits.append(((h0 - end_altitude) / (h0 - h1), "end_altitude"))
    if seen_below and h0 < skip_altitude <= h1 and h1 != h0:
        hits.append(((skip_altitude - h0) / (h1 - h0), "skip_out"))
    if not hits:
        return None, None
    frac, reason = min(hits, key=lambda item: item[0])
    return frac, reason


def _advance(run: _Run, t: float, y: tuple[float, ...], dt: float, integrator: str) -> tuple[float, ...]:
    if integrator == "rk4":
        return _rk4(run, t, y, dt)
    return _rk45(run, t, y, dt)[0]


def _locate_event(
    run: _Run,
    t: float,
    y: tuple[float, ...],
    dt: float,
    integrator: str,
    end_altitude: float,
    skip_altitude: float,
    seen_below: bool,
) -> tuple[float, tuple[float, ...], str]:
    lo = 0.0
    hi = dt
    y_hi = _advance(run, t, y, dt, integrator)
    reason = "end_altitude"
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        y_mid = _advance(run, t, y, mid, integrator)
        frac, hit = _event_fraction(
            y[2], y_mid[2], end_altitude, skip_altitude, seen_below
        )
        if hit is not None:
            hi = mid
            y_hi = y_mid
            reason = hit
        else:
            lo = mid
        if hi - lo <= max(1e-6, 1e-8 * dt):
            break
    if reason == "end_altitude" and y_hi[2] > end_altitude:
        y_hi = _advance(run, t, y, hi, integrator)
    return t + hi, y_hi, reason


def _parabola_vertex(
    t0: float, g0: float, t1: float, g1: float, t2: float, g2: float
) -> tuple[float, float] | None:
    """Time and load of a quadratic maximum through three samples."""
    dt0 = t0 - t1
    dt2 = t2 - t1
    det = dt0 * dt0 * dt2 - dt2 * dt2 * dt0
    if det == 0.0:
        return None
    a_loc = (dt2 * (g0 - g1) - dt0 * (g2 - g1)) / det
    b_loc = (dt0 * dt0 * (g2 - g1) - dt2 * dt2 * (g0 - g1)) / det
    if a_loc >= 0.0:
        return None
    t_star = t1 - b_loc / (2.0 * a_loc)
    if t_star < min(t0, t2) or t_star > max(t0, t2):
        return None
    load = g1 + b_loc * (t_star - t1) + a_loc * (t_star - t1) ** 2
    return t_star, load


def _interp(samples: list[dict[str, float]], t: float) -> dict[str, float]:
    if t <= samples[0]["t"]:
        return samples[0]
    if t >= samples[-1]["t"]:
        return samples[-1]
    for left, right in zip(samples, samples[1:]):
        if left["t"] <= t <= right["t"] and right["t"] > left["t"]:
            w = (t - left["t"]) / (right["t"] - left["t"])
            return {
                key: left[key] + w * (right[key] - left[key])
                for key in ("t", "V", "gamma", "h", "load_g")
            }
    return samples[-1]


def _local_peaks(samples: list[dict[str, float]]) -> list[dict[str, float]]:
    peaks: list[dict[str, float]] = []
    for i in range(1, len(samples) - 1):
        g0 = samples[i - 1]["load_g"]
        g1 = samples[i]["load_g"]
        g2 = samples[i + 1]["load_g"]
        if g1 >= g0 and g1 > g2 and g1 > g0:
            vertex = _parabola_vertex(
                samples[i - 1]["t"],
                g0,
                samples[i]["t"],
                g1,
                samples[i + 1]["t"],
                g2,
            )
            if vertex is None:
                peaks.append(samples[i])
            else:
                t_star, load = vertex
                refined = _interp(samples, t_star)
                refined["t"] = t_star
                refined["load_g"] = load
                peaks.append(refined)
    return peaks


def _format_peaks(peaks: list[dict[str, float]]) -> str:
    if not peaks:
        return "none"
    parts = []
    for peak in peaks:
        parts.append(
            "t_s={:.8g},g={:.8g},Z_m={:.8g},V_m_s={:.8g}".format(
                peak["t"], peak["load_g"], peak["h"], peak["V"]
            )
        )
    return " | ".join(parts)


def _record(run: _Run, t: float, y: tuple[float, ...]) -> dict[str, float]:
    _rates, load_g = run.rates(t, y)
    return {
        "t": t,
        "V": y[0],
        "gamma": y[1],
        "h": y[2],
        "x": y[3],
        "load_g": load_g,
    }


def integrate(
    run: _Run,
    y0: tuple[float, float, float, float],
    integrator: str,
    rtol: float,
    dt: float | None,
) -> dict[str, object]:
    t = 0.0
    y = y0
    try:
        samples = [_record(run, t, y)]
    except _SpeedFloor as exc:
        raise ValueError("speed collapsed below 1 m/s before an end condition") from exc
    seen_below = y[2] < run.skip_altitude
    end_reason = "max_time"
    step = 0.05 if dt is None else dt
    atol_scale = 1.0
    steps = 0
    max_steps = 2_000_000
    while t < run.max_time - 1e-12:
        steps += 1
        if steps > max_steps:
            raise ValueError("integrator exceeded the step limit before an end condition")
        dt_try = step if dt is None else dt
        dt_try = min(dt_try, run.max_time - t)
        if dt_try <= 0.0:
            break
        try:
            if integrator == "rk4":
                y1 = _rk4(run, t, y, dt_try)
                err = 0.0
            else:
                accepted = False
                y1 = y
                err = 0.0
                for _ in range(40):
                    y5, y4 = _rk45(run, t, y, dt_try)
                    err = _rk45_error(y, y5, y4, rtol, atol_scale)
                    y1 = y5
                    if err <= 1.0 or dt_try <= H_MIN * 1.01:
                        accepted = True
                        break
                    dt_try = max(H_MIN, dt_try * min(0.2, 0.9 * err ** -0.25))
                if not accepted and err > 1.0:
                    raise ValueError("RK45 could not meet the tolerance; increase rtol or max_time_s")
                if err < 1e-16:
                    factor = 5.0
                else:
                    factor = min(5.0, max(0.2, 0.9 * err ** -0.2))
                step = min(H_MAX, max(H_MIN, dt_try * factor))
            if y[2] < run.skip_altitude:
                seen_below = True
            frac, hit = _event_fraction(
                y[2], y1[2], run.end_altitude, run.skip_altitude, seen_below
            )
            if hit is not None and frac is not None and frac < 1.0:
                t, y, end_reason = _locate_event(
                    run,
                    t,
                    y,
                    dt_try,
                    integrator,
                    run.end_altitude,
                    run.skip_altitude,
                    seen_below,
                )
                samples.append(_record(run, t, y))
                break
            t = t + dt_try
            y = y1
            if y[2] < run.skip_altitude:
                seen_below = True
            samples.append(_record(run, t, y))
        except _SpeedFloor:
            end_reason = "speed_floor"
            break
        if t >= run.max_time - 1e-9:
            end_reason = "max_time"
            break
    else:
        end_reason = "max_time"

    if not samples:
        raise ValueError("integrator produced no samples")
    peaks = _local_peaks(samples)
    richest = max(samples, key=lambda row: row["load_g"])
    interior_peak = False
    if peaks:
        best = max(peaks, key=lambda row: row["load_g"])
        if best["load_g"] >= richest["load_g"]:
            richest = best
            interior_peak = True
    final = samples[-1]
    t_skip = final["t"] if end_reason == "skip_out" else None
    return {
        "samples": samples,
        "peaks": peaks,
        "peak": richest,
        "final": final,
        "end_reason": end_reason,
        "min_altitude_m": min(row["h"] for row in samples),
        "skip_out": end_reason == "skip_out",
        "interior_peak": interior_peak,
        "t_skip_s": t_skip,
        "downrange_m": final["x"],
        "flight_time_s": final["t"],
    }


def _density_fn(kind: str, scale_height: float, rho_ref: float, z_ref: float):
    if kind == "us1976":
        return us1976_density
    return lambda altitude: exponential_density(altitude, rho_ref, z_ref, scale_height)


def _assumptions(
    kind: str,
    scale_height: float,
    rho_ref: float,
    z_ref: float,
    integrator: str,
    rtol: float,
    dt: float | None,
    rotating: bool,
) -> str:
    if kind == "us1976":
        atmosphere = (
            "atmosphere=us1976 using standard_1976 at or below 86 km and "
            "density_above_86km above 86 km, clamped to 0 m and 1000000 m for the lookup"
        )
    else:
        atmosphere = (
            "atmosphere=exponential "
            "rho = rhoref*exp(-(Z - Zref)/H) "
            f"with H = {scale_height:.8g} m, rhoref = {rho_ref:.8g} kg/m^3, "
            f"Zref = {z_ref:.8g} m"
        )
    if integrator == "rk4":
        stepper = (
            f"fixed-step RK4 with dt = {dt:.8g} s; convergence rerun uses dt/2; "
            "n/a when there is no interior load peak or the tighter rerun does not move it"
        )
    else:
        stepper = (
            f"adaptive RK45 (Dormand-Prince 5(4)) with rtol = {rtol:.8g}; "
            "convergence rerun uses a 100x tighter tolerance; "
            "n/a when there is no interior load peak or the tighter rerun does not move it"
        )
    rotation = (
        "non-rotating; no Coriolis or centrifugal acceleration"
        if not rotating
        else (
            "rotating frame with V and gamma relative to the air; "
            "heading_deg is the inertial heading from north; "
            "latitude and heading held constant; "
            "heading_air_deg is the entry air-relative heading; "
            "dV/dt += -omega^2*r*cos(lat)*(cos(lat)*sin(gamma) + sin(lat)*cos(gamma)*cos(psi)); "
            "dgamma/dt += -(2*omega*V*cos(lat)*sin(psi) + omega^2*r*cos(lat)*"
            "(cos(lat)*cos(gamma) - sin(lat)*sin(gamma)*cos(psi)))/V"
        )
    )
    return (
        "spherical planet; inverse-square gravity g = mu/r^2; point mass; "
        "constant ballistic coefficient B = m/(Cd*A); constant L/D; "
        "gamma positive below the local horizontal; "
        "dV/dt = -D/m + g*sin(gamma); "
        "dgamma/dt = -(L*cos(bank)/m - (g - V^2/r)*cos(gamma))/V; "
        "dh/dt = -V*sin(gamma); dx/dt = V*cos(gamma)*R/r; "
        "peak_g = sqrt(L^2+D^2)/(m*g0) with g0 = 9.80665 m/s^2; "
        f"{atmosphere}; {stepper}; {rotation}"
    )


def _relative_peak_change(first: float, second: float) -> float:
    return abs(first - second) / max(abs(first), 1e-30)


def simulate(
    speed: float,
    gamma: float,
    altitude: float,
    lod: float,
    beta: float | None,
    mass: float | None,
    cd: float | None,
    area: float | None,
    bank_deg: float | None,
    bank_schedule: str | list | None,
    planet_radius: float,
    mu: float,
    atmosphere: str,
    scale_height: float | None,
    rho_ref: float | None,
    z_ref: float | None,
    end_altitude: float,
    max_time: float,
    skip_altitude: float | None,
    latitude_deg: float | None,
    heading_deg: float | None,
    omega: float | None,
    rtol: float,
    dt: float | None,
    converge: bool = True,
) -> dict[str, object]:
    require_positive("entry speed", speed)
    require_finite("entry flight-path angle", gamma)
    if abs(gamma) > math.pi / 2.0:
        raise ValueError("gamma must be finite and in [-pi/2, pi/2] radians")
    require_finite("altitude", altitude)
    require_finite("lift-to-drag ratio", lod)
    if lod < 0.0:
        raise ValueError("lod must be finite and >= 0")
    require_positive("planet radius", planet_radius)
    require_positive("mu", mu)
    require_finite("end_altitude", end_altitude)
    if altitude <= end_altitude:
        raise ValueError("altitude must be greater than end_altitude")
    require_positive("max_time_s", max_time)
    if skip_altitude is None:
        skip_altitude = altitude
    require_finite("skip_altitude", skip_altitude)
    if rtol <= 0.0 or not math.isfinite(rtol):
        raise ValueError("rtol must be finite and > 0")
    if dt is not None:
        require_positive("dt", dt)

    b_use, b_source = resolve_ballistic(beta, mass, cd, area)
    kind, h_use, rho_use, z_use = resolve_atmosphere(
        atmosphere, scale_height, rho_ref, z_ref
    )
    rotating = latitude_deg is not None or heading_deg is not None or (
        omega is not None and (latitude_deg is not None or heading_deg is not None)
    )
    if (latitude_deg is None) ^ (heading_deg is None):
        raise ValueError("pass latitude_deg and heading_deg together")
    if omega is not None and latitude_deg is None:
        raise ValueError("omega requires latitude_deg and heading_deg")
    if latitude_deg is not None:
        require_finite("latitude_deg", latitude_deg)
        require_finite("heading_deg", heading_deg)
        if abs(latitude_deg) > 90.0:
            raise ValueError("latitude_deg must be in [-90, 90]")
        rotating = True
        if omega is None:
            omega = OMEGA_EARTH
        require_finite("omega", omega)
    else:
        omega = 0.0
        rotating = False

    if (bank_deg is None) == (bank_schedule is None):
        raise ValueError("pass either bank_deg or bank_schedule, not both and not neither")
    if bank_deg is not None:
        require_finite("bank_deg", bank_deg)
        points = [(0.0, float(bank_deg))]
        bank_text = None
    else:
        assert bank_schedule is not None
        points = parse_bank_schedule(bank_schedule)
        bank_text = json.dumps(
            [{"t_s": t_s, "bank_deg": bank} for t_s, bank in points],
            separators=(",", ":"),
        )

    lat_rad = 0.0
    heading_rad = 0.0
    speed_air = speed
    gamma_air = gamma
    radius_entry = planet_radius + altitude
    if rotating:
        assert omega is not None and latitude_deg is not None and heading_deg is not None
        lat_rad = math.radians(latitude_deg)
        heading_rad = math.radians(heading_deg)
        speed_air, gamma_air, heading_air = air_relative_entry(
            speed, gamma, radius_entry, lat_rad, heading_rad, omega
        )

    density = _density_fn(kind, h_use, rho_use, z_use)
    integrator = "rk4" if dt is not None else "rk45"

    def make_run() -> _Run:
        return _Run(
            b_use,
            lod,
            planet_radius,
            mu,
            density,
            lambda t, pts=points: bank_deg_at(t, pts),
            rotating,
            lat_rad,
            heading_rad,
            float(omega) if omega is not None else 0.0,
            end_altitude,
            float(skip_altitude),
            max_time,
        )

    y0 = (speed_air, gamma_air, altitude, 0.0)
    primary = integrate(make_run(), y0, integrator, rtol, dt)
    peak_g = float(primary["peak"]["load_g"])
    if converge and not primary["interior_peak"]:
        convergence: float | str = "n/a (no interior aerodynamic-load peak)"
    elif converge:
        if integrator == "rk4":
            assert dt is not None
            refined = integrate(make_run(), y0, "rk4", rtol, 0.5 * dt)
        else:
            refined = integrate(make_run(), y0, "rk45", rtol / 100.0, None)
        convergence = _relative_peak_change(peak_g, float(refined["peak"]["load_g"]))
        if convergence == 0.0:
            convergence = "n/a (tighter rerun reproduced the same peak)"
    else:
        convergence = 0.0

    peak = primary["peak"]
    final = primary["final"]
    result: dict[str, object] = {
        "title": PLOT_TITLE,
        "method": "planar_point_mass_3dof",
        "assumptions": _assumptions(kind, h_use, rho_use, z_use, integrator, rtol, dt, rotating),
        "speed_m_s": speed,
        "gamma_rad": gamma,
        "gamma_deg": math.degrees(gamma),
        "altitude_m": altitude,
        "lod": lod,
        "B_kg_m2": b_use,
        "B_source": b_source,
        "radius_m": planet_radius,
        "mu_m3_s2": mu,
        "atmosphere": kind,
        "end_altitude_m": end_altitude,
        "max_time_s": max_time,
        "skip_altitude_m": float(skip_altitude),
        "integrator": integrator,
        "entry_frame": "rotating" if rotating else "nonrotating",
        "peak_g": peak_g,
        "t_peak_s": float(peak["t"]),
        "Z_peak_m": float(peak["h"]),
        "V_peak_m_s": float(peak["V"]),
        "load_peaks": _format_peaks(primary["peaks"]),
        "min_altitude_m": float(primary["min_altitude_m"]),
        "skip_out": bool(primary["skip_out"]),
        "end_reason": primary["end_reason"],
        "V_final_m_s": float(final["V"]),
        "gamma_final_rad": float(final["gamma"]),
        "altitude_final_m": float(final["h"]),
        "downrange_m": float(primary["downrange_m"]),
        "flight_time_s": float(primary["flight_time_s"]),
        "convergence_peak_g_rel": convergence,
        "samples": primary["samples"],
    }
    if kind == "exponential":
        result["H_m"] = h_use
        result["rho_ref_kg_m3"] = rho_use
        result["Z_ref_m"] = z_use
    if bank_deg is not None:
        result["bank_deg"] = float(bank_deg)
    else:
        result["bank_schedule"] = bank_text
    if integrator == "rk4":
        result["dt_s"] = float(dt)
    else:
        result["rtol"] = rtol
    if rotating:
        result["latitude_deg"] = float(latitude_deg)
        result["heading_deg"] = float(heading_deg)
        result["omega_rad_s"] = float(omega)
        result["speed_inertial_m_s"] = speed
        result["gamma_inertial_rad"] = gamma
        result["speed_air_m_s"] = speed_air
        result["gamma_air_rad"] = gamma_air
        result["heading_air_deg"] = math.degrees(heading_air)
    if primary["t_skip_s"] is not None:
        result["t_skip_s"] = float(primary["t_skip_s"])
    if mass is not None:
        result["mass_kg"] = mass
        result["cd"] = cd
        result["area_m2"] = area
    return result


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot the lifting entry") from exc
    return plt


def write_plot(result: dict[str, object], out_path: Path) -> None:
    plt = ensure_matplotlib()
    samples = result["samples"]
    times = [row["t"] for row in samples]
    loads = [row["load_g"] for row in samples]
    speeds = [row["V"] for row in samples]
    altitudes = [row["h"] / 1000.0 for row in samples]
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 7.2))
    axes[0].plot(times, loads, color="#1a5276", linewidth=1.6)
    axes[0].plot(
        [float(result["t_peak_s"])],
        [float(result["peak_g"])],
        marker="s",
        markersize=7,
        color="#c0392b",
        linestyle="none",
    )
    axes[0].set_xlabel("time (s)")
    axes[0].set_ylabel(f"aero load / g0  (g0 = {G0:g} m/s$^2$)")
    axes[0].set_title(PLOT_TITLE)
    axes[0].grid(True, alpha=0.35)
    axes[1].plot(speeds, altitudes, color="#1a5276", linewidth=1.6)
    axes[1].plot(
        [float(result["V_peak_m_s"])],
        [float(result["Z_peak_m"]) / 1000.0],
        marker="s",
        markersize=7,
        color="#c0392b",
        linestyle="none",
    )
    axes[1].set_xlabel("speed (m/s)")
    axes[1].set_ylabel("altitude (km)")
    axes[1].grid(True, alpha=0.35)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def emit(result: dict[str, object], graph: Path | None) -> None:
    print_kv("title", result["title"])
    print_kv("method", result["method"])
    print_kv("assumptions", result["assumptions"])
    keys = (
        "speed_m_s",
        "gamma_rad",
        "gamma_deg",
        "altitude_m",
        "lod",
        "bank_deg",
        "bank_schedule",
        "mass_kg",
        "cd",
        "area_m2",
        "B_kg_m2",
        "B_source",
        "radius_m",
        "mu_m3_s2",
        "atmosphere",
        "H_m",
        "rho_ref_kg_m3",
        "Z_ref_m",
        "end_altitude_m",
        "max_time_s",
        "skip_altitude_m",
        "latitude_deg",
        "heading_deg",
        "omega_rad_s",
        "entry_frame",
        "speed_inertial_m_s",
        "gamma_inertial_rad",
        "speed_air_m_s",
        "gamma_air_rad",
        "heading_air_deg",
        "integrator",
        "dt_s",
        "rtol",
        "peak_g",
        "t_peak_s",
        "Z_peak_m",
        "V_peak_m_s",
        "load_peaks",
        "min_altitude_m",
        "skip_out",
        "t_skip_s",
        "end_reason",
        "V_final_m_s",
        "gamma_final_rad",
        "altitude_final_m",
        "downrange_m",
        "flight_time_s",
        "convergence_peak_g_rel",
    )
    for key in keys:
        if key in result and key != "samples":
            value = result[key]
            if isinstance(value, bool):
                print_kv(key, "true" if value else "false")
            else:
                print_kv(key, value)
    if graph is not None:
        print_kv("graph", str(graph.resolve()))


def run_check() -> int:
    def fail(message: str) -> int:
        print(f"check: fail: {message}")
        return 1

    if not close(DEFAULT_RHO_REF, 0.0034 * SLUG_FT3_TO_KG_M3):
        return fail("Earth rho_ref conversion drifted")
    if not close(DEFAULT_H, 22000.0 * FT_TO_M):
        return fail("Earth scale-height conversion drifted")
    try:
        resolve_ballistic(100.0, 500.0, 0.5, 2.0)
        return fail("disagreeing beta was accepted")
    except ValueError:
        pass
    try:
        resolve_atmosphere("exponential", 8000.0, None, None)
        return fail("partial atmosphere override was accepted")
    except ValueError:
        pass
    try:
        parse_bank_schedule("[[0, 0], [10, 40]]")
        return fail("pair-array bank schedule was accepted")
    except ValueError:
        pass
    native = parse_bank_schedule(
        [{"t_s": 0, "bank_deg": 0}, {"t_s": 1, "bank_deg": 10}]
    )
    if native != [(0.0, 0.0), (1.0, 10.0)]:
        return fail("native bank schedule list was rejected")

    # Vacuum coast: specific energy stays put when drag is negligible.
    radius = R0_EARTH
    mu = MU_EARTH
    speed = 6000.0
    gamma = math.radians(20.0)
    altitude = 150000.0
    coast = simulate(
        speed,
        gamma,
        altitude,
        0.0,
        1.0e18,
        None,
        None,
        None,
        0.0,
        None,
        radius,
        mu,
        "exponential",
        None,
        None,
        None,
        0.0,
        15.0,
        None,
        None,
        None,
        None,
        1.0e-8,
        None,
        converge=False,
    )
    r0 = radius + altitude
    e0 = 0.5 * speed * speed - mu / r0
    e1 = 0.5 * float(coast["V_final_m_s"]) ** 2 - mu / (radius + float(coast["altitude_final_m"]))
    if abs(e1 - e0) / abs(e0) > 1e-8:
        return fail(f"vacuum energy drift {abs(e1 - e0) / abs(e0)}")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "lifting_entry_trajectory.png"

        def capture(argv: list[str]) -> tuple[int, str, str]:
            from io import StringIO

            sink = StringIO()
            err = StringIO()
            old_out, old_err = sys.stdout, sys.stderr
            try:
                sys.stdout, sys.stderr = sink, err
                code = main(argv)
            finally:
                sys.stdout, sys.stderr = old_out, old_err
            return code, sink.getvalue(), err.getvalue()

        code, text, err = capture(
            [
                "--speed",
                "6000",
                "--gamma",
                str(math.radians(20.0)),
                "--altitude",
                "150000",
                "--lod",
                "0",
                "--beta",
                "1e18",
                "--bank-deg",
                "0",
                "--max-time-s",
                "8",
                "--rtol",
                "1e-5",
                "--out",
                str(out),
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        if not out.is_file() or not out.read_bytes().startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Lifting entry trajectory",
            "method: planar_point_mass_3dof",
            "peak_g:",
            "convergence_peak_g_rel:",
            "graph:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, _text, err = capture(
            [
                "--speed",
                "7000",
                "--gamma",
                "0.1",
                "--altitude",
                "80000",
                "--lod",
                "1",
                "--beta",
                "100",
            ]
        )
        if code != 2 or "bank" not in err:
            return fail(f"missing bank was accepted: {err}")
        code, _text, err = capture(
            [
                "--speed",
                "7000",
                "--gamma",
                "0.1",
                "--altitude",
                "80000",
                "--lod",
                "1",
                "--beta",
                "100",
                "--bank-deg",
                "0",
                "--latitude-deg",
                "0",
            ]
        )
        if code != 2 or "heading" not in err:
            return fail("latitude without heading was accepted")
        code, _text, err = capture(
            [
                "--speed",
                "7000",
                "--gamma",
                "0.1",
                "--altitude",
                "80000",
                "--lod",
                "1",
                "--beta",
                "100",
                "--bank-deg",
                "0",
                "--bank-schedule",
                '[{"t_s": 0, "bank_deg": 10}]',
            ]
        )
        if code != 2 or "bank" not in err:
            return fail("both bank inputs were accepted")
        code, _text, err = capture(
            [
                "--speed",
                "7000",
                "--gamma",
                "0.1",
                "--altitude",
                "80000",
                "--lod",
                "0",
                "--beta",
                "100",
                "--bank-deg",
                "0",
                "--scale-height",
                "8000",
            ]
        )
        if code != 2 or "scale_height" not in err or "--scale-height" in err:
            return fail(f"partial atmosphere override was accepted: {err}")
        if "rho_ref" not in err or "z_ref" not in err:
            return fail(f"atmosphere error omitted MCP names: {err}")

    print("check: pass")
    print_kv("energy_rel", abs(e1 - e0) / abs(e0))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Planar point-mass lifting-entry trajectory, peak load, and skip."
    )
    parser.add_argument("--speed", type=float, default=None, help="entry speed [m/s]")
    parser.add_argument(
        "--gamma",
        type=float,
        default=None,
        help="entry flight-path angle below local horizontal [rad]",
    )
    parser.add_argument("--altitude", type=float, default=None, help="entry interface altitude [m]")
    parser.add_argument("--lod", type=float, default=None, help="lift-to-drag ratio")
    parser.add_argument("--beta", type=float, default=None, help="ballistic coefficient B = m/(Cd*A) [kg/m^2]")
    parser.add_argument("--mass", type=float, default=None, help="vehicle mass m [kg]")
    parser.add_argument("--cd", type=float, default=None, help="drag coefficient Cd")
    parser.add_argument("--area", type=float, default=None, help="reference area A [m^2]")
    parser.add_argument("--bank-deg", type=float, default=None, help="constant bank angle [deg]")
    parser.add_argument(
        "--bank-schedule",
        type=bank_schedule_argument,
        default=None,
        help="list of objects {t_s, bank_deg}, or that list as a JSON string",
    )
    parser.add_argument("--radius", type=float, default=None, help="planet radius [m]")
    parser.add_argument("--mu", type=float, default=None, help="gravitational parameter [m^3/s^2]")
    parser.add_argument(
        "--atmosphere",
        type=str,
        default=None,
        help="exponential or us1976",
    )
    parser.add_argument("--scale-height", type=float, default=None, help="density scale height H [m]")
    parser.add_argument("--rho-ref", type=float, default=None, help="reference density [kg/m^3]")
    parser.add_argument("--z-ref", type=float, default=None, help="reference altitude [m]")
    parser.add_argument("--end-altitude", type=float, default=None, help="stop altitude [m]")
    parser.add_argument("--max-time-s", type=float, default=None, help="maximum flight time [s]")
    parser.add_argument("--skip-altitude", type=float, default=None, help="skip-out altitude [m]")
    parser.add_argument("--latitude-deg", type=float, default=None, help="latitude [deg]")
    parser.add_argument(
        "--heading-deg",
        type=float,
        default=None,
        help="inertial heading from north, held constant [deg]",
    )
    parser.add_argument("--omega", type=float, default=None, help="planet rotation rate [rad/s]")
    parser.add_argument("--rtol", type=float, default=None, help="RK45 relative tolerance")
    parser.add_argument("--dt", type=float, default=None, help="fixed RK4 step [s]")
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="PNG path; omit and no figure is written",
    )
    parser.add_argument("--check", action="store_true", help="run built-in checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    missing = [
        name
        for name, value in (
            ("speed", args.speed),
            ("gamma", args.gamma),
            ("altitude", args.altitude),
            ("lod", args.lod),
        )
        if value is None
    ]
    if missing:
        print(f"error: requires {', '.join(missing)}", file=sys.stderr)
        return 2
    if args.dt is not None and args.rtol is not None:
        print("error: pass either dt or rtol, not both", file=sys.stderr)
        return 2
    try:
        result = simulate(
            args.speed,
            args.gamma,
            args.altitude,
            args.lod,
            args.beta,
            args.mass,
            args.cd,
            args.area,
            args.bank_deg,
            args.bank_schedule,
            R0_EARTH if args.radius is None else args.radius,
            MU_EARTH if args.mu is None else args.mu,
            "exponential" if args.atmosphere is None else args.atmosphere,
            args.scale_height,
            args.rho_ref,
            args.z_ref,
            DEFAULT_END_ALTITUDE if args.end_altitude is None else args.end_altitude,
            DEFAULT_MAX_TIME if args.max_time_s is None else args.max_time_s,
            args.skip_altitude,
            args.latitude_deg,
            args.heading_deg,
            args.omega,
            DEFAULT_RTOL if args.rtol is None else args.rtol,
            args.dt,
        )
        graph: Path | None = None
        if args.out is not None:
            graph = Path(args.out)
            write_plot(result, graph)
        emit(result, graph)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
