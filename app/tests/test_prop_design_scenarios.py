"""Physical scenarios for the design-point air-breathing PROP skills.

Identities are checked against an independent normal-shock derivation and
against the ideal turbojet. Flight states come from the 1976 atmosphere.
"""

from __future__ import annotations

import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"


def load(folder: str, module: str):
    path = str(SKILLS / folder)
    if path not in sys.path:
        sys.path.insert(0, path)
    return __import__(module)


inlet = load("PROP - InletRecovery", "inlet_recovery")
turbo = load("PROP - NonidealTurbojet", "nonideal_turbojet")
ideal = load("PROP - IdealTurboJet", "ideal_turbojet")
reheat = load("PROP - AfterburningTurbojet", "afterburning_turbojet")
fan = load("PROP - SeparateStreamTurbofan", "separate_stream_turbofan")
sizing = load("PROP - EngineAirflowSizing", "engine_airflow_sizing")
atmos = load("ATMOS - Standard1976", "standard_1976")

G = 1.4
R = turbo.R_AIR
CP = turbo.default_cp(G)
Q = turbo.DEFAULT_HEATING_VALUE
REL = 1e-9


def near(got: float, want: float, label: str, rel: float = REL) -> None:
    scale = max(1.0, abs(want))
    if not math.isfinite(got) or abs(got - want) > rel * scale:
        raise AssertionError(f"{label}: got {got}, want {want}")


def shock_recovery(mach: float, gamma: float) -> float:
    """Pitot total-pressure ratio from the downstream-Mach form, not the skill formula."""
    if mach <= 1.0:
        return 1.0
    m2_sq = (1.0 + 0.5 * (gamma - 1.0) * mach * mach) / (gamma * mach * mach - 0.5 * (gamma - 1.0))
    p_ratio = 1.0 + 2.0 * gamma / (gamma + 1.0) * (mach * mach - 1.0)

    def total_over_static(m_sq: float) -> float:
        return (1.0 + 0.5 * (gamma - 1.0) * m_sq) ** (gamma / (gamma - 1.0))

    return p_ratio * total_over_static(m2_sq) / total_over_static(mach * mach)


def isa(altitude_m: float) -> tuple[float, float, float, float]:
    state = atmos.atmosphere(altitude_m)
    return float(state["T"]), float(state["p"]), float(state["rho"]), float(state["cs"])


def cruise_turbo(**overrides):
    temperature, pressure, _rho, _sound = isa(11000.0)
    args = dict(
        mach=0.85,
        temperature=temperature,
        pressure=pressure,
        tit=1580.0,
        opr=24.0,
        gamma=G,
        cp=CP,
        heating_value=Q,
        gas_constant=R,
        pi_d=0.98,
        eta_c=0.87,
        eta_t=0.90,
        eta_m=0.99,
        eta_b=0.995,
        pi_b=0.96,
        eta_n=0.98,
        match_fuel=True,
    )
    args.update(overrides)
    return turbo.solution(**args)


class InletScenarios(unittest.TestCase):
    def test_static_user_recovery_is_adiabatic(self) -> None:
        point = inlet.solution(0.0, 288.15, 101325.0, G, R, 0.97, False, 1.0)
        near(float(point["V0_m_s"]), 0.0, "static speed")
        near(float(point["Tt2_K"]), 288.15, "static total temperature")
        near(float(point["pt2_Pa"]), 0.97 * 101325.0, "static face pressure")
        near(float(point["a0_m_s"]), math.sqrt(G * R * 288.15), "sea-level sound speed")
        self.assertTrue(330.0 < float(point["a0_m_s"]) < 350.0)
        self.assertEqual(point["recovery_source"], "user")

    def test_subsonic_pitot_has_no_shock_loss(self) -> None:
        for mach in (0.0, 0.3, 0.85, 1.0):
            point = inlet.solution(mach, 216.65, 22632.0, G, R, None, True, 0.97)
            near(float(point["pi_ns"]), 1.0, f"M={mach} shock ratio")
            near(float(point["pi_d"]), 0.97, f"M={mach} recovery")
            near(float(point["Tt2_K"]), float(point["Tt0_K"]), f"M={mach} adiabatic")

    def test_supersonic_pitot_matches_downstream_mach_form(self) -> None:
        published = {1.5: 0.9298, 2.0: 0.7209, 2.5: 0.4990, 3.0: 0.3283}
        temperature, pressure, _rho, sound = isa(15000.0)
        previous = 1.0
        for mach in (1.2, 1.5, 2.0, 2.5, 3.0, 3.5):
            point = inlet.solution(mach, temperature, pressure, G, R, None, True, 0.95)
            expected = shock_recovery(mach, G)
            near(float(point["pi_ns"]), expected, f"M={mach} shock")
            near(float(point["pi_d"]), expected * 0.95, f"M={mach} pitot product")
            near(float(point["pt2_Pa"]), float(point["pi_d"]) * float(point["pt0_Pa"]), f"M={mach} face pressure")
            near(float(point["V0_m_s"]), mach * sound, f"M={mach} flight speed", rel=1e-6)
            self.assertLess(float(point["pi_ns"]), previous)
            previous = float(point["pi_ns"])
            if mach in published:
                near(float(point["pi_ns"]), published[mach], f"M={mach} published", rel=2e-4)

    def test_gamma_changes_shock_recovery(self) -> None:
        air = inlet.solution(2.2, 216.65, 12000.0, 1.4, R, None, True, 1.0)
        hot = inlet.solution(2.2, 216.65, 12000.0, 1.3, R, None, True, 1.0)
        near(float(air["pi_ns"]), shock_recovery(2.2, 1.4), "gamma 1.4")
        near(float(hot["pi_ns"]), shock_recovery(2.2, 1.3), "gamma 1.3")
        self.assertNotAlmostEqual(float(air["pi_ns"]), float(hot["pi_ns"]), places=3)

    def test_supplied_recovery_ignores_mach(self) -> None:
        slow = inlet.solution(0.4, 288.15, 101325.0, G, R, 0.96, False, 1.0)
        fast = inlet.solution(2.4, 216.65, 5474.0, G, R, 0.96, False, 1.0)
        near(float(slow["pi_d"]), 0.96, "slow supplied")
        near(float(fast["pi_d"]), 0.96, "fast supplied")
        self.assertGreater(float(fast["Tt2_K"]), float(slow["Tt2_K"]))

    def test_altitude_matches_explicit_1976_state(self) -> None:
        for altitude in (0.0, 11000.0, 20000.0, 32000.0):
            temperature, pressure, rho, sound = isa(altitude)
            code, data, err = run_cli(
                SKILLS / "PROP - InletRecovery" / "inlet_recovery.py",
                ["--mach", "0.8", "--alt", str(altitude), "--pi-d", "0.99"],
            )
            self.assertEqual(code, 0, err)
            near(num(data, "T0_K"), temperature, f"{altitude} K", rel=1e-6)
            near(num(data, "p0_Pa"), pressure, f"{altitude} Pa", rel=1e-6)
            near(num(data, "rho0_kg_m3"), rho, f"{altitude} density", rel=1e-6)
            near(num(data, "a0_m_s"), sound, f"{altitude} sound", rel=1e-6)
            near(num(data, "Tt2_K"), num(data, "Tt0_K"), f"{altitude} adiabatic")
            near(num(data, "pt2_Pa") / num(data, "pt0_Pa"), 0.99, f"{altitude} face", rel=1e-6)

    def test_bad_recovery_inputs_fail(self) -> None:
        with self.assertRaises(ValueError):
            inlet.solution(2.0, 216.65, 20000.0, G, R, 1.2, False, 1.0)
        with self.assertRaises(ValueError):
            inlet.solution(-0.1, 216.65, 20000.0, G, R, 0.9, False, 1.0)
        code, _data, err = run_cli(
            SKILLS / "PROP - InletRecovery" / "inlet_recovery.py",
            ["--mach", "2", "--alt", "11000", "--pi-d", "0.9", "--pitot"],
        )
        self.assertEqual(code, 2, err)
        self.assertIn("not both", err)


class TurbojetScenarios(unittest.TestCase):
    def test_ideal_limit_matches_ideal_turbojet(self) -> None:
        cases = [
            (0.0, 288.15, 101325.0, 1700.0, 8.0),
            (0.8, 216.65, 19330.0, 1600.0, 20.0),
            (2.0, 216.65, 12111.0, 1900.0, 6.0),
        ]
        for mach, temperature, pressure, tit, opr in cases:
            perfect = turbo.solution(
                mach, temperature, pressure, tit, opr, G, CP, Q, R, match_fuel=False
            )
            reference = ideal.solution(mach, temperature, pressure, tit, opr, G, CP, Q, R)
            for key in ("f", "Tt3_K", "tau_t", "pi_t", "NPR", "Ve_m_s", "Fs_m_s", "TSFC_kg_N_s", "eta_th"):
                near(float(perfect[key]), float(reference[key]), f"M={mach} {key}")

    def test_fuel_in_the_shaft_match_reduces_the_turbine_drop(self) -> None:
        common = dict(mach=0.8, temperature=216.65, pressure=19330.0, tit=1600.0, opr=20.0, gamma=G, cp=CP, heating_value=Q, gas_constant=R)
        with_fuel = turbo.solution(match_fuel=True, **common)
        without = turbo.solution(match_fuel=False, **common)
        self.assertGreater(float(with_fuel["tau_t"]), float(without["tau_t"]))
        self.assertGreater(float(with_fuel["Tt5_K"]), float(without["Tt5_K"]))
        near(float(with_fuel["f"]), float(without["f"]), "fuel ratio independent of shaft match")

    def test_station_and_shaft_balance_at_three_flight_points(self) -> None:
        points = [
            cruise_turbo(),
            turbo.solution(0.0, 288.15, 101325.0, 1650.0, 14.0, G, CP, Q, R, pi_d=0.97, eta_c=0.85, eta_t=0.89, eta_m=0.99, eta_b=0.98, pi_b=0.95, eta_n=0.97),
            turbo.solution(1.6, *isa(18000.0)[:2], 1750.0, 10.0, G, CP, Q, R, pi_d=shock_recovery(1.6, G) * 0.96, eta_c=0.84, eta_t=0.88, eta_b=0.97, pi_b=0.94, eta_n=0.96),
        ]
        for point in points:
            self.assert_cycle(point)

    def assert_cycle(self, point: dict) -> None:
        mach = float(point["M"])
        near(float(point["w_c_J_kg"]), CP * (float(point["Tt3_K"]) - float(point["Tt2_K"])), f"M={mach} compressor work")
        fuel_match = float(point["f"]) if float(point["match_fuel"]) else 0.0
        turbine_work = (1.0 + fuel_match) * float(point["eta_m"]) * CP * (float(point["Tt4_K"]) - float(point["Tt5_K"]))
        near(turbine_work, float(point["w_c_J_kg"]), f"M={mach} shaft balance")
        te = float(point["Te_K"])
        ve_energy = 0.5 * float(point["Ve_m_s"]) ** 2
        ideal_drop = CP * (float(point["Tt5_K"]) - te)
        near(ve_energy, float(point["eta_n"]) * ideal_drop, f"M={mach} nozzle")
        near(float(point["Fs_m_s"]), (1.0 + float(point["f"])) * float(point["Ve_m_s"]) - float(point["V0_m_s"]), f"M={mach} thrust")
        near(float(point["TSFC_kg_N_s"]), float(point["f"]) / float(point["Fs_m_s"]), f"M={mach} TSFC")
        near(float(point["pt2_Pa"]), float(point["pi_d"]) * float(point["pt0_Pa"]), f"M={mach} inlet")
        near(float(point["pt3_Pa"]), float(point["pi_c"]) * float(point["pt2_Pa"]), f"M={mach} compressor pressure")
        self.assertGreater(float(point["Tt3_K"]), float(point["Tt2_K"]))
        self.assertGreater(float(point["Tt4_K"]), float(point["Tt3_K"]))
        self.assertLess(float(point["Tt5_K"]), float(point["Tt4_K"]))
        self.assertGreater(float(point["Fs_m_s"]), 0.0)
        self.assertGreater(float(point["eta_th"]), 0.0)
        self.assertLess(float(point["eta_th"]), 1.0)
        if float(point["V0_m_s"]) == 0.0:
            near(float(point["eta_p"]), 0.0, "static propulsive")
            near(float(point["eta_o"]), 0.0, "static overall")
        else:
            near(float(point["eta_o"]), float(point["eta_th"]) * float(point["eta_p"]), f"M={mach} efficiency product")
            self.assertGreater(float(point["eta_p"]), 0.0)
            self.assertLess(float(point["eta_o"]), float(point["eta_th"]))

    def test_realistic_magnitudes(self) -> None:
        takeoff = turbo.solution(0.0, 288.15, 101325.0, 1650.0, 14.0, G, CP, Q, R, pi_d=0.97, eta_c=0.85, eta_t=0.89, eta_m=0.99, eta_b=0.98, pi_b=0.95, eta_n=0.97)
        cruise = cruise_turbo()
        for name, point, fs_band, tsfc_band in (
            ("takeoff", takeoff, (550.0, 1100.0), (1.8e-5, 3.5e-5)),
            ("cruise", cruise, (400.0, 1000.0), (2.0e-5, 4.0e-5)),
        ):
            self.assertTrue(fs_band[0] < float(point["Fs_m_s"]) < fs_band[1], f"{name} Fs={point['Fs_m_s']}")
            self.assertTrue(tsfc_band[0] < float(point["TSFC_kg_N_s"]) < tsfc_band[1], f"{name} TSFC={point['TSFC_kg_N_s']}")
            self.assertTrue(0.015 < float(point["f"]) < 0.04, f"{name} f={point['f']}")

    def test_hot_day_makes_less_thrust_than_a_cold_day(self) -> None:
        common = dict(mach=0.0, pressure=101325.0, tit=1700.0, opr=16.0, gamma=G, cp=CP, heating_value=Q, gas_constant=R, eta_c=0.86, eta_t=0.90, pi_d=0.98)
        cold = turbo.solution(temperature=233.15, **common)
        standard = turbo.solution(temperature=288.15, **common)
        hot = turbo.solution(temperature=322.15, **common)
        self.assertGreater(float(cold["Fs_m_s"]), float(standard["Fs_m_s"]))
        self.assertGreater(float(standard["Fs_m_s"]), float(hot["Fs_m_s"]))
        self.assertGreater(float(cold["f"]), float(hot["f"]))
        self.assertGreater(float(hot["Tt3_K"]), float(cold["Tt3_K"]))

    def test_worse_compressor_and_inlet_cost_thrust(self) -> None:
        base = cruise_turbo(eta_c=1.0, pi_d=1.0)
        leaky = cruise_turbo(eta_c=0.8, pi_d=1.0)
        blocked = cruise_turbo(eta_c=1.0, pi_d=0.90)
        self.assertGreater(float(leaky["Tt3_K"]), float(base["Tt3_K"]))
        self.assertLess(float(leaky["Fs_m_s"]), float(base["Fs_m_s"]))
        near(float(blocked["pt2_Pa"]), 0.90 * float(blocked["pt0_Pa"]), "blocked inlet")
        self.assertLess(float(blocked["Fs_m_s"]), float(base["Fs_m_s"]))

    def test_impossible_cycles_raise(self) -> None:
        with self.assertRaises(ValueError):
            turbo.solution(0.8, 216.65, 19330.0, 500.0, 20.0, G, CP, Q, R)
        with self.assertRaises(ValueError):
            turbo.solution(0.85, 216.65, 22632.0, 900.0, 40.0, G, CP, Q, R, eta_c=0.8, eta_t=0.85, eta_n=0.95, pi_d=0.97)
        ram = turbo.solution(3.2, 216.65, 5474.9, 1200.0, 4.0, G, CP, Q, R)
        self.assertGreater(float(ram["Fs_m_s"]), 0.0)
        with self.assertRaises(ValueError):
            turbo.solution(4.5, 216.65, 20000.0, 1400.0, 2.0, G, CP, Q, R, eta_c=0.8, eta_t=0.8, eta_n=0.9, pi_d=0.7)

    def test_custom_gamma_still_balances(self) -> None:
        gamma = 1.33
        cp = turbo.default_cp(gamma)
        point = turbo.solution(0.9, 220.0, 20000.0, 1700.0, 18.0, gamma, cp, Q, R, eta_c=0.86, eta_t=0.89, eta_n=0.97, pi_b=0.95)
        near(float(point["w_c_J_kg"]), cp * (float(point["Tt3_K"]) - float(point["Tt2_K"])), "custom gamma work")
        near(float(point["eta_o"]), float(point["eta_th"]) * float(point["eta_p"]), "custom gamma efficiencies")


class AfterburnerScenarios(unittest.TestCase):
    def cycle(self, **overrides):
        temperature, pressure, _rho, _sound = isa(11000.0)
        args = dict(
            mach=0.9,
            temperature=temperature,
            pressure=pressure,
            tit=1600.0,
            opr=16.0,
            tt7=2100.0,
            gamma=G,
            cp=CP,
            heating_value=Q,
            gas_constant=R,
            pi_d=0.97,
            eta_c=0.86,
            eta_t=0.89,
            eta_m=0.99,
            eta_b=0.99,
            pi_b=0.96,
            eta_n=0.97,
            eta_ab=0.95,
            pi_ab=0.97,
        )
        args.update(overrides)
        return reheat.solution(**args)

    def test_reheat_adds_fuel_and_thrust(self) -> None:
        point = self.cycle()
        dry = turbo.solution(
            point["M"], point["T0_K"], point["p0_Pa"], point["Tt4_K"], point["pi_c"], G, CP, Q, R,
            pi_d=point["pi_d"], eta_c=point["eta_c"], eta_t=point["eta_t"], eta_m=point["eta_m"],
            eta_b=point["eta_b"], pi_b=point["pi_b"], eta_n=point["eta_n"],
        )
        near(float(point["Fs_dry_m_s"]), float(dry["Fs_m_s"]), "dry thrust handoff")
        near(float(point["f_total"]), float(point["f"]) + float(point["f_ab"]), "fuel sum")
        self.assertGreater(float(point["f_ab"]), 0.0)
        hotter = self.cycle(tt7=2400.0, eta_ab=1.0, pi_ab=1.0)
        self.assertGreater(float(hotter["f_ab"]), float(hotter["f"]))
        self.assertGreater(float(point["Fs_m_s"]), float(point["Fs_dry_m_s"]))
        self.assertGreater(float(point["thrust_ratio"]), 1.3)
        self.assertLess(float(point["thrust_ratio"]), 2.2)
        self.assertGreater(float(point["TSFC_kg_N_s"]), float(point["TSFC_dry_kg_N_s"]))
        near(float(point["pt7_Pa"]), float(point["pi_ab"]) * float(point["pt6_Pa"]), "afterburner pressure")
        near(
            float(point["f_ab"]),
            (1.0 + float(point["f"])) * CP * (float(point["Tt7_K"]) - float(point["Tt6_K"])) / (0.95 * Q - CP * float(point["Tt7_K"])),
            "afterburner fuel",
        )
        near(float(point["eta_o"]), float(point["eta_th"]) * float(point["eta_p"]), "reheat efficiency product")
        self.assertTrue(1.5e-5 < float(point["TSFC_dry_kg_N_s"]) < 4e-5)
        self.assertTrue(3e-5 < float(point["TSFC_kg_N_s"]) < 8e-5)

    def test_thrust_rises_smoothly_with_afterburner_temperature(self) -> None:
        temperatures = (1800.0, 2000.0, 2200.0)
        thrusts = [float(self.cycle(tt7=temperature)["Fs_m_s"]) for temperature in temperatures]
        fuels = [float(self.cycle(tt7=temperature)["f_ab"]) for temperature in temperatures]
        self.assertLess(thrusts[0], thrusts[1])
        self.assertLess(thrusts[1], thrusts[2])
        self.assertLess(fuels[0], fuels[1])
        self.assertLess(fuels[1], fuels[2])

    def test_reheat_collapses_to_the_dry_engine(self) -> None:
        dry = self.cycle()
        tt6 = float(dry["Tt6_K"])
        near_dry = self.cycle(tt7=tt6 + 0.5, eta_ab=1.0, pi_ab=1.0)
        self.assertLess(float(near_dry["f_ab"]), 1e-4)
        near(float(near_dry["Fs_m_s"]), float(near_dry["Fs_dry_m_s"]), "near-dry thrust", rel=5e-3)

    def test_sea_level_static_convergent_nozzle_is_choked(self) -> None:
        expanded = reheat.solution(0.0, 288.15, 101325.0, 1800.0, 12.0, 2200.0, G, CP, Q, R, nozzle="expanded")
        choked = reheat.solution(0.0, 288.15, 101325.0, 1800.0, 12.0, 2200.0, G, CP, Q, R, nozzle="convergent")
        self.assertEqual(choked["choked"], "yes")
        self.assertGreater(float(choked["pe_Pa"]), 101325.0)
        self.assertGreater(float(choked["As_m_s_kg"]), 0.0)
        sonic = (2.0 / (G + 1.0)) ** (G / (G - 1.0))
        near(float(choked["pe_Pa"]), float(choked["pt7_Pa"]) * sonic, "sonic exit pressure")
        near(float(choked["Te_K"]), float(choked["Tt7_K"]) * 2.0 / (G + 1.0), "sonic exit temperature")
        momentum = float(choked["Fs_momentum_m_s"])
        pressure_thrust = (float(choked["pe_Pa"]) - 101325.0) * float(choked["As_m_s_kg"])
        near(float(choked["Fs_m_s"]), momentum + pressure_thrust, "net thrust")
        rho_e = float(choked["pe_Pa"]) / (R * float(choked["Te_K"]))
        near((1.0 + float(choked["f_total"])) , rho_e * float(choked["Ve_m_s"]) * float(choked["As_m_s_kg"]), "continuity")
        self.assertGreater(float(expanded["Ve_m_s"]), float(choked["Ve_m_s"]))
        near(float(expanded["pe_Pa"]), 101325.0, "expanded exit pressure")

    def test_low_pressure_convergent_nozzle_is_not_choked(self) -> None:
        expanded = reheat.solution(0.0, 288.15, 101325.0, 1400.0, 1.8, 1800.0, G, CP, Q, R, nozzle="expanded")
        convergent = reheat.solution(0.0, 288.15, 101325.0, 1400.0, 1.8, 1800.0, G, CP, Q, R, nozzle="convergent")
        self.assertLess(float(expanded["NPR"]), 1.0 / ((2.0 / (G + 1.0)) ** (G / (G - 1.0))))
        self.assertEqual(convergent["choked"], "no")
        near(float(convergent["Fs_m_s"]), float(expanded["Fs_m_s"]), "unchoked thrust")
        near(float(convergent["pe_Pa"]), 101325.0, "unchoked exit pressure")

    def test_component_losses_move_fuel_and_thrust_the_right_way(self) -> None:
        base = self.cycle(eta_ab=1.0, pi_ab=1.0)
        lossy_burn = self.cycle(eta_ab=0.85, pi_ab=1.0)
        lossy_pressure = self.cycle(eta_ab=1.0, pi_ab=0.92)
        self.assertGreater(float(lossy_burn["f_ab"]), float(base["f_ab"]))
        self.assertGreater(float(lossy_burn["TSFC_kg_N_s"]), float(base["TSFC_kg_N_s"]))
        self.assertLess(float(lossy_pressure["Fs_m_s"]), float(base["Fs_m_s"]))

    def test_rejects_a_cold_afterburner(self) -> None:
        with self.assertRaises(ValueError):
            self.cycle(tt7=800.0)


class TurbofanScenarios(unittest.TestCase):
    def test_zero_bypass_ideal_fan_matches_the_turbojet(self) -> None:
        common = dict(mach=0.8, temperature=216.65, pressure=19330.0, tit=1600.0, opr=25.0, gamma=G, cp=CP, heating_value=Q, gas_constant=R, pi_d=0.98, eta_n=0.98, pi_b=0.97)
        turbojet = turbo.solution(**common)
        turbofan = fan.solution(bpr=0.0, pi_f=1.8, eta_f=1.0, eta_c=1.0, **common)
        for key in ("f", "Tt3_K", "Tt5_K", "Ve_m_s", "Fs_m_s", "TSFC_kg_N_s"):
            near(float(turbofan[key]), float(turbojet[key]), f"zero bypass {key}")
        near(float(turbofan["pi_core"]), 25.0 / 1.8, "core pressure ratio")
        near(float(turbofan["pt3_Pa"]), 25.0 * float(turbofan["pt2_Pa"]), "overall pressure")

    def test_high_bypass_cruise_and_low_bypass_dash(self) -> None:
        temperature, pressure, _rho, _sound = isa(10668.0)
        cruise = fan.solution(
            0.82, temperature, pressure, 1650.0, 42.0, 8.0, 1.55, G, CP, Q, R,
            pi_d=0.995, eta_f=0.91, eta_c=0.88, eta_t=0.91, eta_m=0.99, eta_b=0.995, pi_b=0.96, eta_n=0.98,
        )
        dash_t, dash_p, _rho, _sound = isa(12000.0)
        dash = fan.solution(
            1.6, dash_t, dash_p, 1850.0, 22.0, 0.45, 3.2, G, CP, Q, R,
            pi_d=shock_recovery(1.6, G) * 0.96, eta_f=0.86, eta_c=0.85, eta_t=0.88, eta_m=0.99, eta_b=0.98, pi_b=0.95, eta_n=0.97,
        )
        for name, point in (("cruise", cruise), ("dash", dash)):
            self.assert_fan(point)
        self.assertTrue(150.0 < float(cruise["Fs_m_s"]) < 400.0, cruise["Fs_m_s"])
        self.assertTrue(1.2e-5 < float(cruise["TSFC_kg_N_s"]) < 2.2e-5, cruise["TSFC_kg_N_s"])
        self.assertGreater(float(dash["Fs_m_s"]), float(cruise["Fs_m_s"]))
        self.assertGreater(float(dash["TSFC_kg_N_s"]), float(cruise["TSFC_kg_N_s"]))
        self.assertGreater(float(cruise["V0_m_s"]), 200.0)
        self.assertLess(float(cruise["V0_m_s"]), float(cruise["Vf_m_s"]))
        self.assertLess(float(cruise["Vf_m_s"]), float(cruise["Ve_m_s"]))
        self.assertGreater(float(cruise["eta_p"]), 0.55)
        self.assertLess(float(cruise["eta_p"]), 0.9)

    def assert_fan(self, point: dict) -> None:
        bpr = float(point["bpr"])
        near(float(point["w_fan_J_kg"]), CP * (float(point["Tt13_K"]) - float(point["Tt2_K"])), "fan work")
        near(float(point["w_core_J_kg"]), CP * (float(point["Tt3_K"]) - float(point["Tt2_K"])), "core work")
        near(float(point["w_shaft_J_kg"]), float(point["w_core_J_kg"]) + bpr * float(point["w_fan_J_kg"]), "shaft sum")
        fuel_match = float(point["f"]) if float(point["match_fuel"]) else 0.0
        delivered = (1.0 + fuel_match) * float(point["eta_m"]) * CP * (float(point["Tt4_K"]) - float(point["Tt5_K"]))
        near(delivered, float(point["w_shaft_J_kg"]), "turbine delivery")
        split = (float(point["Fs_core_m_s"]) + bpr * float(point["Fs_fan_m_s"])) / (1.0 + bpr)
        near(float(point["Fs_m_s"]), split, "thrust split")
        near(float(point["TSFC_kg_N_s"]), float(point["f"]) / (float(point["Fs_m_s"]) * (1.0 + bpr)), "fan TSFC")
        near(float(point["eta_o"]), float(point["eta_th"]) * float(point["eta_p"]), "fan efficiency product")
        near(float(point["pt13_Pa"]), float(point["pi_f"]) * float(point["pt2_Pa"]), "fan face")
        self.assertGreater(float(point["Tt3_K"]), float(point["Tt13_K"]))
        self.assertGreater(float(point["Fs_m_s"]), 0.0)

    def test_more_bypass_lowers_specific_thrust_and_tsfc(self) -> None:
        temperature, pressure, _rho, _sound = isa(11000.0)
        common = dict(
            mach=0.8, temperature=temperature, pressure=pressure, tit=1600.0, opr=30.0, pi_f=1.6,
            gamma=G, cp=CP, heating_value=Q, gas_constant=R, eta_f=0.90, eta_c=0.87, eta_t=0.90, eta_b=0.99, pi_b=0.96,
        )
        low = fan.solution(bpr=1.5, **common)
        mid = fan.solution(bpr=4.0, **common)
        high = fan.solution(bpr=7.0, **common)
        self.assertGreater(float(low["Fs_m_s"]), float(mid["Fs_m_s"]))
        self.assertGreater(float(mid["Fs_m_s"]), float(high["Fs_m_s"]))
        self.assertGreater(float(low["TSFC_kg_N_s"]), float(mid["TSFC_kg_N_s"]))
        self.assertGreater(float(mid["TSFC_kg_N_s"]), float(high["TSFC_kg_N_s"]))

    def test_too_much_bypass_cannot_be_driven(self) -> None:
        with self.assertRaises(ValueError):
            fan.solution(0.8, 216.65, 19330.0, 1400.0, 20.0, 30.0, 2.5, G, CP, Q, R)
        with self.assertRaises(ValueError):
            fan.solution(0.8, 216.65, 19330.0, 1600.0, 5.0, 2.0, 6.0, G, CP, Q, R)


class DesignPathScenarios(unittest.TestCase):
    def test_inlet_turbojet_and_sizing_chain_at_cruise(self) -> None:
        temperature, pressure, rho, sound = isa(11000.0)
        mach = 0.84
        face = inlet.solution(mach, temperature, pressure, G, R, None, True, 0.985)
        engine = turbo.solution(
            mach, temperature, pressure, 1560.0, 22.0, G, CP, Q, R,
            pi_d=float(face["pi_d"]), eta_c=0.87, eta_t=0.90, eta_m=0.99, eta_b=0.995, pi_b=0.96, eta_n=0.98,
        )
        near(float(engine["Tt2_K"]), float(face["Tt2_K"]), "face temperature handoff")
        near(float(engine["pt2_Pa"]), float(face["pt2_Pa"]), "face pressure handoff")
        thrust = 75000.0
        sized = sizing.solution(
            thrust, float(engine["Fs_m_s"]), rho, mach * sound, 0.5, float(face["pt2_Pa"]), float(face["Tt2_K"]), 22.0, 1.35, G, R,
        )
        near(float(sized["mdot_kg_s"]) * float(engine["Fs_m_s"]), thrust, "thrust closure")
        near(rho * float(sized["V_m_s"]) * float(sized["A_capture_m2"]), float(sized["mdot_kg_s"]), "capture continuity")
        near(float(sized["D_capture_m"]), math.sqrt(4.0 * float(sized["A_capture_m2"]) / math.pi), "capture diameter")
        mfp = float(sized["mfp"])
        rebuilt = float(sized["pt_face_Pa"]) * float(sized["A_face_m2"]) * mfp / math.sqrt(float(sized["Tt_face_K"]))
        near(rebuilt, float(sized["mdot_kg_s"]), "face continuity")
        near(float(sized["N_stages"]), math.log(22.0) / math.log(1.35), "stage count")
        self.assertEqual(sized["sizing_diameter"], "capture")
        self.assertTrue(0.8 < float(sized["D_capture_m"]) < 2.5, sized["D_capture_m"])
        self.assertTrue(80.0 < float(sized["mdot_kg_s"]) < 250.0, sized["mdot_kg_s"])

    def test_afterburning_dash_sizes_a_larger_inlet_than_dry(self) -> None:
        temperature, pressure, rho, sound = isa(9000.0)
        mach = 1.4
        recovery = shock_recovery(mach, G) * 0.95
        wet = reheat.solution(
            mach, temperature, pressure, 1700.0, 12.0, 2000.0, G, CP, Q, R,
            pi_d=recovery, eta_c=0.85, eta_t=0.88, eta_n=0.96, eta_ab=0.94, pi_ab=0.96,
        )
        thrust = 60000.0
        dry_size = sizing.solution(thrust, float(wet["Fs_dry_m_s"]), rho, mach * sound, None, None, None, None, None, G, R)
        wet_size = sizing.solution(thrust, float(wet["Fs_m_s"]), rho, mach * sound, None, None, None, None, None, G, R)
        self.assertLess(float(wet_size["mdot_kg_s"]), float(dry_size["mdot_kg_s"]))
        self.assertLess(float(wet_size["D_capture_m"]), float(dry_size["D_capture_m"]))

    def test_static_turbofan_sizes_the_face_and_scales_with_thrust(self) -> None:
        temperature, pressure, rho, _sound = isa(0.0)
        engine = fan.solution(
            0.0, temperature, pressure, 1700.0, 28.0, 6.0, 1.5, G, CP, Q, R,
            eta_f=0.90, eta_c=0.87, eta_t=0.90, eta_b=0.99, pi_b=0.95, eta_n=0.98,
        )
        near(float(engine["eta_p"]), 0.0, "static propulsive efficiency")
        one = sizing.solution(100000.0, float(engine["Fs_m_s"]), rho, 0.0, 0.55, float(engine["pt2_Pa"]), float(engine["Tt2_K"]), 28.0, 1.4, G, R)
        two = sizing.solution(200000.0, float(engine["Fs_m_s"]), rho, 0.0, 0.55, float(engine["pt2_Pa"]), float(engine["Tt2_K"]), 28.0, 1.4, G, R)
        self.assertEqual(one["sizing_diameter"], "face")
        self.assertNotIn("A_capture_m2", one)
        near(float(two["mdot_kg_s"]), 2.0 * float(one["mdot_kg_s"]), "thrust scaling")
        near(float(two["A_face_m2"]), 2.0 * float(one["A_face_m2"]), "area scaling")
        self.assertTrue(1.0 < float(one["D_face_m"]) < 3.5, one["D_face_m"])

    def test_static_without_a_face_and_split_flags_fail(self) -> None:
        with self.assertRaises(ValueError):
            sizing.solution(1000.0, 500.0, 1.2, 0.0, None, None, None, None, None, G, R)
        with self.assertRaises(ValueError):
            sizing.solution(1000.0, 500.0, 1.2, 80.0, 0.5, None, 300.0, None, None, G, R)
        with self.assertRaises(ValueError):
            sizing.solution(1000.0, 500.0, 1.2, 80.0, None, None, None, 20.0, None, G, R)

    def test_command_line_path_matches_the_libraries(self) -> None:
        temperature, pressure, rho, sound = isa(11000.0)
        mach = 0.8
        code, inlet_out, err = run_cli(
            SKILLS / "PROP - InletRecovery" / "inlet_recovery.py",
            ["--mach", "0.8", "--alt", "11000", "--pitot", "--pi-ds", "0.98"],
        )
        self.assertEqual(code, 0, err)
        library_inlet = inlet.solution(mach, temperature, pressure, G, R, None, True, 0.98)
        near(num(inlet_out, "pi_d"), float(library_inlet["pi_d"]), "cli inlet", rel=1e-6)
        code, engine_out, err = run_cli(
            SKILLS / "PROP - NonidealTurbojet" / "nonideal_turbojet.py",
            ["--mach", "0.8", "--alt", "11000", "--tit", "1600", "--opr", "20", "--pi-d", inlet_out["pi_d"], "--eta-c", "0.88", "--eta-t", "0.9"],
        )
        self.assertEqual(code, 0, err)
        near(num(engine_out, "pt2_Pa"), num(inlet_out, "pt2_Pa"), "cli face pressure", rel=1e-6)
        code, fan_out, err = run_cli(
            SKILLS / "PROP - SeparateStreamTurbofan" / "separate_stream_turbofan.py",
            ["--mach", "0.8", "--alt", "11000", "--tit", "1600", "--opr", "30", "--bpr", "5", "--fpr", "1.5", "--pi-d", inlet_out["pi_d"]],
        )
        self.assertEqual(code, 0, err)
        self.assertGreater(num(fan_out, "Fs_m_s"), 0.0)
        code, heat_out, err = run_cli(
            SKILLS / "PROP - AfterburningTurbojet" / "afterburning_turbojet.py",
            ["--mach", "0.8", "--alt", "11000", "--tit", "1600", "--opr", "15", "--t7", "2050", "--nozzle", "convergent", "--pi-d", inlet_out["pi_d"]],
        )
        self.assertEqual(code, 0, err)
        self.assertIn("warning_convergent_nozzle", heat_out)
        code, size_out, err = run_cli(
            SKILLS / "PROP - EngineAirflowSizing" / "engine_airflow_sizing.py",
            ["--thrust", "50000", "--fs", engine_out["Fs_m_s"], "--alt", "11000", "--mach", "0.8", "--opr", "20", "--stage-pr", "1.4"],
        )
        self.assertEqual(code, 0, err)
        near(num(size_out, "mdot_kg_s"), 50000.0 / num(engine_out, "Fs_m_s"), "cli airflow", rel=1e-6)
        near(num(size_out, "V_m_s"), mach * sound, "cli speed", rel=1e-6)
        near(num(size_out, "rho_kg_m3"), rho, "cli density", rel=1e-6)
        near(num(size_out, "A_capture_m2") * rho * num(size_out, "V_m_s"), num(size_out, "mdot_kg_s"), "cli capture", rel=1e-6)


def run_cli(script: Path, args: list[str]) -> tuple[int, dict[str, str], str]:
    with tempfile.TemporaryDirectory() as folder:
        proc = subprocess.run(
            [sys.executable, str(script), *args, "--out", str(Path(folder) / "plot.png")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            plot = Path(folder) / "plot.png"
            if not plot.is_file() or plot.stat().st_size < 1000:
                return 1, {}, "PNG was not written"
    data: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        data[key] = value
    return proc.returncode, data, proc.stderr


def num(data: dict[str, str], key: str) -> float:
    return float(data[key])


if __name__ == "__main__":
    unittest.main(verbosity=2)
