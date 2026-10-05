#!/usr/bin/env python3
"""Spacecraft battery energy budget (DoD, charge/discharge efficiency).

Nameplate energy is battery_energy_from_capacity_ah when amp-hours and voltage
are given. Usable energy is battery_usable_energy. Time at a continuous load is
battery_time_at_continuous_load. Eclipse or peak chemical energy is
battery_discharge_energy. Required nameplate energy is
battery_required_nameplate_energy. Orbit recharge uses battery_charge_energy,
battery_recharge_power, and battery_orbit_source_power. Optional SoC-versus-time
plot closes one orbit with optional solar orbit-average power.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Battery energy budget"
N_CURVE = 401
J_PER_WH = 3600.0
SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "spacecraft battery energy budget from NASA MSFC Electrical Power Systems "
    "for Cubesats (NTRS 20180007969); "
    "nameplate energy is battery_energy_from_capacity_ah E = 3600*C_Ah*V "
    "when amp-hours and bus voltage are given, or E = 3600*E_Wh when "
    "watt-hours are given; "
    "usable energy at the load is battery_usable_energy Eu = E*DOD*eta_d; "
    "time at continuous load is battery_time_at_continuous_load t = Eu/P; "
    "chemical energy removed for a load interval is battery_discharge_energy "
    "Es = P*te/eta_d; "
    "required nameplate energy is battery_required_nameplate_energy "
    "Ereq = P*te/(eta_d*DOD); "
    "required amp-hours are battery_required_capacity_ah "
    "C_Ah = Ereq/(3600*V); "
    "array-side recharge energy is battery_charge_energy Ec = Es/eta_c; "
    "sunlit recharge power is battery_recharge_power "
    "PR = P*te/(eta_c*eta_d*td); "
    "sunlit array power for energy balance is battery_orbit_source_power "
    "Psa = P*(1 + te/(eta_c*eta_d*td)); "
    "orbit-average array power from POWER - SolarArrayOutput is "
    "P_avg = Psa*(1 - fe) with fe = te/(te + td); "
    "surplus sunlit power (Psa - P) charges the battery at eta_c; "
    "when Psa is below the load the battery supplies (P - Psa) at eta_d "
    "for the rest of the sunlit interval; "
    "no cell electrochemistry, no thermal runaway, and no Peukert model "
    "beyond the single charge and discharge efficiency factors supplied"
)


@dataclass(frozen=True)
class PeakPulse:
    power: float
    duration: float


@dataclass(frozen=True)
class Solution:
    mode: str
    energy_j: float | None
    energy_wh: float | None
    capacity_ah: float | None
    voltage: float | None
    capacity_source: str
    dod: float
    eta_c: float
    eta_d: float
    usable_j: float | None
    usable_wh: float | None
    load_w: float | None
    time_at_load_s: float | None
    eclipse_s: float | None
    day_s: float | None
    orbit_s: float | None
    eclipse_fraction: float | None
    discharge_energy_j: float | None
    discharge_energy_wh: float | None
    achieved_dod: float | None
    eclipse_fits: str | None
    peak: PeakPulse | None
    peak_energy_j: float | None
    peak_fits: str | None
    required_energy_j: float | None
    required_energy_wh: float | None
    required_ah: float | None
    charge_energy_j: float | None
    recharge_power_w: float | None
    required_psa_w: float | None
    required_pavg_w: float | None
    pavg_w: float | None
    psa_w: float | None
    energy_balance: str | None
    balance_margin_j: float | None
    soc_min: float | None
    soc_end: float | None
    soc_times: tuple[float, ...] | None
    soc_values: tuple[float, ...] | None


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_finite(name: str, value: float) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def require_positive(name: str, value: float) -> None:
    require_finite(name, value)
    if value <= 0.0:
        raise ValueError(f"{name} must be > 0")


def require_unit_interval(name: str, value: float) -> None:
    require_finite(name, value)
    if value <= 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1]")


def close(actual: float, expected: float, tol: float = CHECK_TOL) -> bool:
    scale = max(abs(expected), 1.0)
    return abs(actual - expected) <= tol * scale


def battery_energy_from_capacity_ah(capacity_ah: float, voltage: float) -> float:
    """battery_energy_from_capacity_ah."""
    return J_PER_WH * capacity_ah * voltage


def battery_energy_from_watt_hours(energy_wh: float) -> float:
    """Nameplate energy from watt-hours (3600 J per Wh)."""
    return J_PER_WH * energy_wh


def battery_depth_of_discharge(energy_removed: float, energy: float) -> float:
    """battery_depth_of_discharge."""
    return energy_removed / energy


def battery_usable_energy(energy: float, dod: float, eta_d: float) -> float:
    """battery_usable_energy."""
    return energy * dod * eta_d


def battery_time_at_continuous_load(usable_energy: float, power: float) -> float:
    """battery_time_at_continuous_load."""
    return usable_energy / power


def battery_discharge_energy(power: float, duration: float, eta_d: float) -> float:
    """battery_discharge_energy."""
    return power * duration / eta_d


def battery_required_nameplate_energy(
    power: float, duration: float, eta_d: float, dod: float
) -> float:
    """battery_required_nameplate_energy."""
    return power * duration / (eta_d * dod)


def battery_required_capacity_ah(energy_req: float, voltage: float) -> float:
    """battery_required_capacity_ah."""
    return energy_req / (J_PER_WH * voltage)


def battery_charge_energy(discharge_energy: float, eta_c: float) -> float:
    """battery_charge_energy."""
    return discharge_energy / eta_c


def battery_recharge_power(
    power: float, eclipse: float, eta_c: float, eta_d: float, day: float
) -> float:
    """battery_recharge_power."""
    return power * eclipse / (eta_c * eta_d * day)


def battery_orbit_source_power(
    power: float, eclipse: float, eta_c: float, eta_d: float, day: float
) -> float:
    """battery_orbit_source_power."""
    return power * (1.0 + eclipse / (eta_c * eta_d * day))


def fits_label(required_chemical: float, available_chemical: float) -> str:
    if required_chemical <= available_chemical * (1.0 + CHECK_TOL):
        return "yes"
    return "no"


def resolve_orbit_times(
    eclipse: float | None,
    day: float | None,
    orbit: float | None,
    eclipse_fraction: float | None,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Return te, td, T, fe when enough timing inputs are present."""
    has_te = eclipse is not None
    has_td = day is not None
    has_t = orbit is not None
    has_fe = eclipse_fraction is not None

    if has_fe:
        assert eclipse_fraction is not None
        require_finite("eclipse fraction", eclipse_fraction)
        if eclipse_fraction < 0.0 or eclipse_fraction >= 1.0:
            raise ValueError("eclipse fraction must be in [0, 1)")

    if has_te and has_td:
        assert eclipse is not None and day is not None
        require_positive("eclipse duration", eclipse)
        require_positive("day duration", day)
        te = eclipse
        td = day
        period = te + td
        fe = te / period
        if has_t and not close(float(orbit), period):
            raise ValueError("--orbit must equal --eclipse + --day when all three are set")
        if has_fe and not close(float(eclipse_fraction), fe):
            raise ValueError("--eclipse-fraction disagrees with --eclipse and --day")
        return te, td, period, fe

    if has_te and has_t:
        assert eclipse is not None and orbit is not None
        require_positive("eclipse duration", eclipse)
        require_positive("orbit period", orbit)
        if eclipse >= orbit:
            raise ValueError("eclipse duration must be < orbit period")
        te = eclipse
        td = orbit - eclipse
        fe = te / orbit
        if has_fe and not close(float(eclipse_fraction), fe):
            raise ValueError("--eclipse-fraction disagrees with --eclipse and --orbit")
        return te, td, orbit, fe

    if has_fe and has_t:
        assert eclipse_fraction is not None and orbit is not None
        require_positive("orbit period", orbit)
        te = eclipse_fraction * orbit
        td = orbit - te
        return te, td, orbit, eclipse_fraction

    if has_fe and has_td:
        assert eclipse_fraction is not None and day is not None
        require_positive("day duration", day)
        if eclipse_fraction <= 0.0:
            te = 0.0
            td = day
            return te, td, td, 0.0
        td = day
        te = eclipse_fraction * td / (1.0 - eclipse_fraction)
        period = te + td
        return te, td, period, eclipse_fraction

    if has_te:
        assert eclipse is not None
        require_positive("eclipse duration", eclipse)
        return eclipse, None, None, None

    return None, None, None, eclipse_fraction


def soc_trajectory(
    energy: float,
    dod: float,
    eta_c: float,
    eta_d: float,
    load: float,
    te: float,
    td: float,
    psa: float | None,
    peak: PeakPulse | None,
) -> tuple[tuple[float, ...], tuple[float, ...], float, float]:
    """Piecewise-linear SoC over one orbit starting fully charged at eclipse entry."""
    period = te + td
    times = [i * period / (N_CURVE - 1) for i in range(N_CURVE)]
    # Insert segment boundaries and optional peak end for exact corners.
    for mark in (0.0, te, period):
        if mark not in times:
            times.append(mark)
    peak_end = None
    if peak is not None:
        if peak.duration > te + CHECK_TOL:
            raise ValueError("peak duration must not exceed the eclipse duration")
        peak_end = peak.duration
        if peak_end not in times:
            times.append(peak_end)
    times = sorted(t for t in times if 0.0 <= t <= period)

    chemical = energy
    soc_floor = 1.0 - dod
    values: list[float] = []
    soc_min = 1.0

    for index, t in enumerate(times):
        if index == 0:
            values.append(chemical / energy)
            soc_min = min(soc_min, values[-1])
            continue
        dt = t - times[index - 1]
        t_mid = 0.5 * (t + times[index - 1])
        if t_mid <= te:
            power_load = load
            if peak is not None and t_mid <= peak.duration:
                power_load = peak.power
            chemical -= battery_discharge_energy(power_load, dt, eta_d)
        else:
            if psa is None:
                # Just-enough average charge to restore the continuous eclipse drain.
                # The implied array also carries the sunlit load, so only PR enters the battery.
                pr = battery_recharge_power(load, te, eta_c, eta_d, td)
                chemical += pr * eta_c * dt
            else:
                surplus = psa - load
                if surplus >= 0.0:
                    chemical += surplus * eta_c * dt
                else:
                    chemical -= battery_discharge_energy(-surplus, dt, eta_d)
            if chemical > energy:
                chemical = energy
        if chemical < 0.0:
            chemical = 0.0
        soc = chemical / energy
        values.append(soc)
        soc_min = min(soc_min, soc)

    # Warn via soc_min vs floor; caller prints fit.
    _ = soc_floor
    return tuple(times), tuple(values), soc_min, values[-1]


def evaluate(
    energy_wh: float | None,
    capacity_ah: float | None,
    voltage: float | None,
    dod: float,
    eta_c: float,
    eta_d: float,
    load: float | None,
    eclipse: float | None,
    day: float | None,
    orbit: float | None,
    eclipse_fraction: float | None,
    peak_power: float | None,
    peak_duration: float | None,
    pavg: float | None,
) -> Solution:
    require_unit_interval("depth of discharge", dod)
    require_unit_interval("charge efficiency", eta_c)
    require_unit_interval("discharge efficiency", eta_d)

    has_wh = energy_wh is not None
    has_ah = capacity_ah is not None
    if has_wh and has_ah:
        raise ValueError("pass --energy or --ah with --voltage, not both")
    if has_ah and voltage is None:
        raise ValueError("--ah requires --voltage")
    if voltage is not None:
        require_positive("bus voltage", voltage)

    energy_j: float | None = None
    energy_wh_out: float | None = None
    capacity_out: float | None = None
    capacity_source = "none"
    if has_wh:
        assert energy_wh is not None
        require_positive("battery energy", energy_wh)
        energy_j = battery_energy_from_watt_hours(energy_wh)
        energy_wh_out = energy_wh
        capacity_source = "watt_hours"
        if voltage is not None:
            capacity_out = energy_wh / voltage
    elif has_ah:
        assert capacity_ah is not None and voltage is not None
        require_positive("amp-hour capacity", capacity_ah)
        energy_j = battery_energy_from_capacity_ah(capacity_ah, voltage)
        energy_wh_out = capacity_ah * voltage
        capacity_out = capacity_ah
        capacity_source = "amp_hours"

    te, td, period, fe = resolve_orbit_times(eclipse, day, orbit, eclipse_fraction)

    peak: PeakPulse | None = None
    if peak_power is not None or peak_duration is not None:
        if peak_power is None or peak_duration is None:
            raise ValueError("peak path requires both --peak and --peak-duration")
        require_positive("peak load", peak_power)
        require_positive("peak duration", peak_duration)
        peak = PeakPulse(power=peak_power, duration=peak_duration)

    if load is not None:
        require_positive("continuous load", load)

    if pavg is not None:
        require_finite("orbit-average array power", pavg)
        if pavg < 0.0:
            raise ValueError("orbit-average array power must be >= 0")

    usable_j = None
    usable_wh = None
    time_at_load = None
    if energy_j is not None:
        usable_j = battery_usable_energy(energy_j, dod, eta_d)
        usable_wh = usable_j / J_PER_WH
        if load is not None:
            time_at_load = battery_time_at_continuous_load(usable_j, load)

    discharge_j = None
    discharge_wh = None
    achieved_dod = None
    eclipse_fits = None
    if load is not None and te is not None and te > 0.0:
        discharge_j = battery_discharge_energy(load, te, eta_d)
        discharge_wh = discharge_j / J_PER_WH
        if energy_j is not None:
            achieved_dod = battery_depth_of_discharge(discharge_j, energy_j)
            eclipse_fits = fits_label(discharge_j, energy_j * dod)

    peak_energy_j = None
    peak_fits = None
    if peak is not None:
        peak_energy_j = battery_discharge_energy(peak.power, peak.duration, eta_d)
        if energy_j is not None:
            peak_fits = fits_label(peak_energy_j, energy_j * dod)

    required_j = None
    required_wh = None
    required_ah = None
    mode = "capacity"
    if energy_j is None:
        if load is None or te is None:
            raise ValueError(
                "without --energy/--ah, pass --load and an eclipse duration "
                "(--eclipse, or --eclipse-fraction with --orbit or --day)"
            )
        required_j = battery_required_nameplate_energy(load, te, eta_d, dod)
        required_wh = required_j / J_PER_WH
        if voltage is not None:
            required_ah = battery_required_capacity_ah(required_j, voltage)
        mode = "required_capacity"
        energy_j = required_j
        energy_wh_out = required_wh
        capacity_source = "required"
        usable_j = battery_usable_energy(energy_j, dod, eta_d)
        usable_wh = usable_j / J_PER_WH
        time_at_load = battery_time_at_continuous_load(usable_j, load)
        discharge_j = battery_discharge_energy(load, te, eta_d)
        discharge_wh = discharge_j / J_PER_WH
        achieved_dod = dod
        eclipse_fits = "yes"

    charge_j = None
    recharge_w = None
    required_psa = None
    required_pavg = None
    psa = None
    energy_balance = None
    balance_margin = None
    soc_times = None
    soc_values = None
    soc_min = None
    soc_end = None

    if load is not None and te is not None and td is not None and td > 0.0:
        assert discharge_j is not None
        charge_j = battery_charge_energy(discharge_j, eta_c)
        recharge_w = battery_recharge_power(load, te, eta_c, eta_d, td)
        required_psa = battery_orbit_source_power(load, te, eta_c, eta_d, td)
        assert fe is not None
        required_pavg = required_psa * (1.0 - fe)
        if pavg is not None:
            if fe >= 1.0:
                raise ValueError("eclipse fraction must be < 1 for array power")
            psa = pavg / (1.0 - fe) if fe < 1.0 else 0.0
            # Chemical change over sunlight: surplus charges, a shortfall discharges.
            if psa >= load:
                day_chemical = (psa - load) * td * eta_c
            else:
                day_chemical = -battery_discharge_energy(load - psa, td, eta_d)
            balance_margin = day_chemical - discharge_j
            energy_balance = "closed" if balance_margin >= -CHECK_TOL * max(discharge_j, 1.0) else "short"
        else:
            psa = required_psa
            energy_balance = "sized"
            balance_margin = 0.0

        if energy_j is not None and energy_j > 0.0:
            soc_times, soc_values, soc_min, soc_end = soc_trajectory(
                energy=energy_j,
                dod=dod,
                eta_c=eta_c,
                eta_d=eta_d,
                load=load,
                te=te,
                td=td,
                psa=psa if pavg is not None else None,
                peak=peak,
            )
            # Eclipse fit includes a peak inside the eclipse. A sunlit shortfall
            # is an orbit-balance result, not a second eclipse.
            eclipse_soc = min(
                soc for time, soc in zip(soc_times, soc_values) if time <= te + 1e-9
            )
            if eclipse_soc + CHECK_TOL < 1.0 - dod:
                if eclipse_fits == "yes":
                    eclipse_fits = "no"
            mode = "orbit" if pavg is not None or mode == "required_capacity" else "capacity"

    return Solution(
        mode=mode,
        energy_j=energy_j,
        energy_wh=energy_wh_out,
        capacity_ah=capacity_out if capacity_out is not None else required_ah,
        voltage=voltage,
        capacity_source=capacity_source,
        dod=dod,
        eta_c=eta_c,
        eta_d=eta_d,
        usable_j=usable_j,
        usable_wh=usable_wh,
        load_w=load,
        time_at_load_s=time_at_load,
        eclipse_s=te,
        day_s=td,
        orbit_s=period,
        eclipse_fraction=fe,
        discharge_energy_j=discharge_j,
        discharge_energy_wh=discharge_wh,
        achieved_dod=achieved_dod,
        eclipse_fits=eclipse_fits,
        peak=peak,
        peak_energy_j=peak_energy_j,
        peak_fits=peak_fits,
        required_energy_j=required_j,
        required_energy_wh=required_wh,
        required_ah=required_ah,
        charge_energy_j=charge_j,
        recharge_power_w=recharge_w,
        required_psa_w=required_psa,
        required_pavg_w=required_pavg,
        pavg_w=pavg,
        psa_w=psa,
        energy_balance=energy_balance,
        balance_margin_j=balance_margin,
        soc_min=soc_min,
        soc_end=soc_end,
        soc_times=soc_times,
        soc_values=soc_values,
    )


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot battery energy budget") from exc
    return plt


def write_plot(result: Solution, out_path: Path) -> None:
    if result.soc_times is None or result.soc_values is None:
        raise ValueError(
            "SoC plot needs --load and orbit timing (--eclipse with --day or --orbit, "
            "or --eclipse-fraction with --orbit or --day)"
        )
    plt = ensure_matplotlib()
    times_min = [t / 60.0 for t in result.soc_times]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.plot(times_min, result.soc_values, color="#1a5276", linewidth=1.8, label="state of charge")
    floor = 1.0 - result.dod
    ax.axhline(floor, color="#922b21", linestyle="--", linewidth=1.2, label=r"$1-\mathrm{DOD}$ floor")
    ax.axhline(1.0, color="#566573", linestyle=":", linewidth=1.0, label="full charge")
    if result.eclipse_s is not None:
        ax.axvline(result.eclipse_s / 60.0, color="#b9770e", linestyle="-.", linewidth=1.0, label="eclipse end")
    ax.set_xlabel("time from eclipse entry (min)")
    ax.set_ylabel("state of charge")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, alpha=0.35)
    ax.legend(loc="best", fontsize=8)
    ax.set_xlim(0.0, times_min[-1] if times_min else 1.0)
    ax.set_ylim(0.0, 1.05)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(out_path, dpi=150)
    except OSError as exc:
        plt.close(fig)
        raise ValueError(f"could not write the plot: {exc}") from exc
    plt.close(fig)


def emit(result: Solution, graph: Path | None) -> None:
    print_kv("title", PLOT_TITLE)
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("mode", result.mode)
    print_kv("capacity_source", result.capacity_source)
    print_kv("DOD", result.dod)
    print_kv("eta_c", result.eta_c)
    print_kv("eta_d", result.eta_d)
    if result.voltage is not None:
        print_kv("V_V", result.voltage)
    if result.capacity_ah is not None:
        print_kv("C_Ah", result.capacity_ah)
    if result.energy_j is not None:
        print_kv("E_J", result.energy_j)
        print_kv("E_Wh", result.energy_wh)
    if result.usable_j is not None:
        print_kv("Eu_J", result.usable_j)
        print_kv("Eu_Wh", result.usable_wh)
    if result.load_w is not None:
        print_kv("P_W", result.load_w)
    if result.time_at_load_s is not None:
        print_kv("t_load_s", result.time_at_load_s)
        print_kv("t_load_h", result.time_at_load_s / 3600.0)
    if result.eclipse_s is not None:
        print_kv("te_s", result.eclipse_s)
    if result.day_s is not None:
        print_kv("td_s", result.day_s)
    if result.orbit_s is not None:
        print_kv("T_s", result.orbit_s)
    if result.eclipse_fraction is not None:
        print_kv("fe", result.eclipse_fraction)
    if result.discharge_energy_j is not None:
        print_kv("Es_J", result.discharge_energy_j)
        print_kv("Es_Wh", result.discharge_energy_wh)
    if result.achieved_dod is not None:
        print_kv("DOD_achieved", result.achieved_dod)
    if result.eclipse_fits is not None:
        print_kv("eclipse_fits", result.eclipse_fits)
    if result.peak is not None:
        print_kv("P_peak_W", result.peak.power)
        print_kv("t_peak_s", result.peak.duration)
        print_kv("E_peak_J", result.peak_energy_j)
        print_kv("peak_fits", result.peak_fits)
    if result.required_energy_j is not None:
        print_kv("Ereq_J", result.required_energy_j)
        print_kv("Ereq_Wh", result.required_energy_wh)
    if result.required_ah is not None:
        print_kv("C_Ah_req", result.required_ah)
    if result.charge_energy_j is not None:
        print_kv("Ec_J", result.charge_energy_j)
        print_kv("Ec_Wh", result.charge_energy_j / J_PER_WH)
    if result.recharge_power_w is not None:
        print_kv("PR_W", result.recharge_power_w)
    if result.required_psa_w is not None:
        print_kv("Psa_req_W", result.required_psa_w)
    if result.required_pavg_w is not None:
        print_kv("Pavg_req_W", result.required_pavg_w)
    if result.pavg_w is not None:
        print_kv("Pavg_W", result.pavg_w)
    if result.psa_w is not None:
        print_kv("Psa_W", result.psa_w)
    if result.energy_balance is not None:
        print_kv("energy_balance", result.energy_balance)
    if result.balance_margin_j is not None:
        print_kv("balance_margin_J", result.balance_margin_j)
        print_kv("balance_margin_Wh", result.balance_margin_j / J_PER_WH)
    if result.soc_min is not None:
        print_kv("SoC_min", result.soc_min)
        print_kv("SoC_end", result.soc_end)
    print_kv(
        "warning",
        "no cell electrochemistry, thermal runaway, or Peukert model beyond "
        "the supplied charge and discharge efficiencies",
    )
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def capture(argv: list[str]) -> tuple[int, str, str]:
    from io import StringIO

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, out.getvalue(), err.getvalue()


def run_check() -> int:
    if not close(battery_energy_from_capacity_ah(1.0, 1.0), 3600.0):
        return fail("1 Ah at 1 V is not 3600 J")
    if not close(battery_usable_energy(100000.0, 0.5, 0.9), 45000.0):
        return fail("usable energy")
    if not close(battery_time_at_continuous_load(45000.0, 50.0), 900.0):
        return fail("time at load")
    if not close(battery_discharge_energy(100.0, 1800.0, 0.88), 100.0 * 1800.0 / 0.88):
        return fail("discharge energy")
    if not close(
        battery_required_nameplate_energy(100.0, 1800.0, 0.88, 0.2),
        100.0 * 1800.0 / (0.88 * 0.2),
    ):
        return fail("required nameplate energy")
    if not close(
        battery_orbit_source_power(1000.0, 1800.0, 0.92, 0.88, 3600.0),
        1000.0 * (1.0 + 1800.0 / (0.92 * 0.88 * 3600.0)),
    ):
        return fail("orbit source power")

    # Sunlit array below the load must keep discharging, not hold SoC flat.
    short = evaluate(
        energy_wh=100.0,
        capacity_ah=None,
        voltage=None,
        dod=0.8,
        eta_c=0.9,
        eta_d=0.9,
        load=100.0,
        eclipse=1000.0,
        day=1000.0,
        orbit=None,
        eclipse_fraction=None,
        peak_power=None,
        peak_duration=None,
        pavg=10.0,
    )
    eclipse_chem = battery_discharge_energy(100.0, 1000.0, 0.9)
    day_chem = battery_discharge_energy(80.0, 1000.0, 0.9)
    expect_end = 1.0 - (eclipse_chem + day_chem) / (100.0 * J_PER_WH)
    if short.soc_end is None or not close(short.soc_end, expect_end, tol=1e-6):
        return fail(f"sunlit shortfall SoC end {short.soc_end} expected {expect_end}")
    if short.energy_balance != "short":
        return fail("sunlit shortfall was not marked short")
    if short.balance_margin_j is None or not close(
        short.balance_margin_j, -(eclipse_chem + day_chem), tol=1e-9
    ):
        return fail("sunlit shortfall margin omitted the daylight drain")
    if short.eclipse_fits != "yes":
        return fail("eclipse that fits was rejected because sunlight was short")

    with tempfile.TemporaryDirectory() as folder:
        png = Path(folder) / "battery.png"
        code, text, err = capture(
            [
                "--energy",
                "100",
                "--dod",
                "0.3",
                "--eta-c",
                "0.9",
                "--eta-d",
                "0.9",
                "--load",
                "50",
                "--eclipse",
                "1800",
                "--day",
                "3600",
                "--out",
                str(png),
            ]
        )
        if code != 0:
            return fail(f"capacity orbit run failed: {err}")
        if "Eu_Wh:" not in text:
            return fail("capacity run omitted usable energy")
        if "eclipse_fits:" not in text:
            return fail("capacity run omitted eclipse_fits")
        if "graph:" not in text:
            return fail("capacity run with --out omitted graph")
        if not png.is_file() or not png.read_bytes().startswith(b"\x89PNG"):
            return fail("capacity run did not write a PNG")

        code, text, err = capture(
            [
                "--load",
                "100",
                "--eclipse",
                "1800",
                "--dod",
                "0.2",
                "--eta-c",
                "0.92",
                "--eta-d",
                "0.88",
                "--voltage",
                "28",
            ]
        )
        if code != 0:
            return fail(f"required-capacity run failed: {err}")
        if "mode: required_capacity" not in text and "Ereq_Wh:" not in text:
            return fail("required-capacity run omitted Ereq")
        if "C_Ah_req:" not in text:
            return fail("required-capacity run omitted C_Ah_req")

        code, text, err = capture(
            [
                "--ah",
                "12",
                "--voltage",
                "28",
                "--dod",
                "0.25",
                "--eta-c",
                "0.95",
                "--eta-d",
                "0.9",
                "--load",
                "40",
                "--peak",
                "120",
                "--peak-duration",
                "60",
            ]
        )
        if code != 0:
            return fail(f"peak run failed: {err}")
        if "peak_fits:" not in text:
            return fail("peak run omitted peak_fits")
        if "t_load_s:" not in text:
            return fail("peak run omitted time at load")

        code, text, err = capture(
            [
                "--energy",
                "200",
                "--dod",
                "0.35",
                "--eta-c",
                "0.9",
                "--eta-d",
                "0.9",
                "--load",
                "80",
                "--eclipse",
                "2100",
                "--orbit",
                "5400",
                "--p-avg",
                "150",
            ]
        )
        if code != 0:
            return fail(f"solar balance run failed: {err}")
        if "energy_balance:" not in text:
            return fail("solar balance run omitted energy_balance")
        if "Psa_W:" not in text:
            return fail("solar balance run omitted sunlit array power")

        code, _text, err = capture(
            ["--energy", "100", "--ah", "10", "--voltage", "28", "--dod", "0.2", "--eta-c", "0.9", "--eta-d", "0.9"]
        )
        if code == 0:
            return fail("accepted both --energy and --ah")

        code, _text, err = capture(
            ["--dod", "0.2", "--eta-c", "0.9", "--eta-d", "0.9"]
        )
        if code == 0:
            return fail("accepted run with neither capacity nor load/eclipse")

    print("check: pass")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Spacecraft battery usable energy, eclipse/peak fit, required "
            "capacity, and optional one-orbit SoC PNG."
        )
    )
    parser.add_argument(
        "--energy",
        type=float,
        default=None,
        help="nameplate battery energy [W·h]",
    )
    parser.add_argument(
        "--ah",
        type=float,
        default=None,
        help="nameplate ampere-hour capacity [A·h]; requires --voltage",
    )
    parser.add_argument(
        "--voltage",
        type=float,
        default=None,
        help="bus or average discharge voltage [V]",
    )
    parser.add_argument(
        "--dod",
        type=float,
        required=False,
        default=None,
        help="allowed depth of discharge DOD in (0, 1]",
    )
    parser.add_argument(
        "--eta-c",
        type=float,
        default=None,
        help="charge (charger) efficiency eta_c in (0, 1]",
    )
    parser.add_argument(
        "--eta-d",
        type=float,
        default=None,
        help="discharge efficiency eta_d in (0, 1]",
    )
    parser.add_argument(
        "--load",
        type=float,
        default=None,
        help="continuous load power [W]",
    )
    parser.add_argument(
        "--eclipse",
        type=float,
        default=None,
        help="eclipse duration te [s]",
    )
    parser.add_argument(
        "--day",
        type=float,
        default=None,
        help="sunlit duration td [s]",
    )
    parser.add_argument(
        "--orbit",
        type=float,
        default=None,
        help="orbit period T [s]",
    )
    parser.add_argument(
        "--eclipse-fraction",
        type=float,
        default=None,
        help="eclipse fraction fe in [0, 1)",
    )
    parser.add_argument(
        "--peak",
        type=float,
        default=None,
        help="peak load power [W]",
    )
    parser.add_argument(
        "--peak-duration",
        type=float,
        default=None,
        help="peak load duration [s]",
    )
    parser.add_argument(
        "--p-avg",
        type=float,
        default=None,
        help="orbit-average solar-array power from POWER - SolarArrayOutput [W]",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="optional PNG path for state of charge versus time over one orbit",
    )
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    if args.dod is None:
        raise ValueError("--dod is required")
    if args.eta_c is None:
        raise ValueError("--eta-c is required")
    if args.eta_d is None:
        raise ValueError("--eta-d is required")
    result = evaluate(
        energy_wh=args.energy,
        capacity_ah=args.ah,
        voltage=args.voltage,
        dod=float(args.dod),
        eta_c=float(args.eta_c),
        eta_d=float(args.eta_d),
        load=args.load,
        eclipse=args.eclipse,
        day=args.day,
        orbit=args.orbit,
        eclipse_fraction=args.eclipse_fraction,
        peak_power=args.peak,
        peak_duration=args.peak_duration,
        pavg=args.p_avg,
    )
    path: Path | None = None
    if args.out is not None:
        path = Path(args.out).resolve()
        write_plot(result, path)
    emit(result, path)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    try:
        return run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
