"""Start-to-finish LEO design checks.

Each scenario runs the real programs and parses ``key: value`` stdout.
A failure of any scenario fails the test. The summary JSON lists every scenario.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["AUTH_DISABLED"] = "1"

from app.catalog import load_catalog

ROOT = Path(__file__).resolve().parents[2]
G0 = 9.80665
R_ASCENT = 6.356766e6
MU_ASCENT = G0 * R_ASCENT * R_ASCENT
R0 = 6.3742e6
SUMMARY = Path(tempfile.gettempdir()) / "ground_to_leo_summary.json"

NEW_TOOLS = (
    "launch_azimuth_inclination",
    "fairing_and_interstage_mass",
    "vehicle_mass_budget",
    "leo_delta_v_budget",
    "stage_propellant_split",
    "multi_stage_ascent",
    "max_q_and_aero_load",
    "orbit_insertion_from_burnout",
)


def script(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def run(program: Path, args: list[str]) -> dict[str, str]:
    proc = subprocess.run(
        [sys.executable, str(program), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    data: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        data[key] = value
    if proc.returncode != 0:
        raise AssertionError(
            f"{program.name} exited {proc.returncode}\n{proc.stderr}\n{proc.stdout}"
        )
    return data


def num(data: dict[str, str], key: str) -> float:
    if key not in data:
        raise AssertionError(f"missing {key} in {sorted(data)}")
    return float(data[key])


def require_figure(data: dict[str, str]) -> None:
    for key in ("graph", "viewer"):
        path = Path(data[key])
        if not path.is_file() or path.stat().st_size < 32:
            raise AssertionError(f"{key} was not written: {path}")


def require_html(data: dict[str, str]) -> None:
    path = Path(data["viewer"])
    if not path.is_file() or path.stat().st_size < 32:
        raise AssertionError(f"viewer was not written: {path}")
    if "graph" in data:
        raise AssertionError("HTML-only figure printed a graph")


def require_png(data: dict[str, str]) -> None:
    path = Path(data["graph"])
    if not path.is_file() or path.stat().st_size < 32:
        raise AssertionError(f"graph was not written: {path}")
    if "viewer" in data:
        raise AssertionError("PNG-only figure printed a viewer")


class GroundToLeoTests(unittest.TestCase):
    def test_scenarios(self) -> None:
        results: list[dict[str, object]] = []
        errors: list[str] = []
        scenarios = (
            ("small_two_stage_leo", self.scenario_small_two_stage),
            ("high_inclination", self.scenario_high_inclination),
            ("three_stage_vacuum", self.scenario_three_stage),
            ("single_stage_matches_basic", self.scenario_single_stage),
            ("insertion_edges", self.scenario_insertion_edges),
        )
        try:
            self.prepare_engine()
            for name, fn in scenarios:
                try:
                    fn()
                except Exception as exc:
                    results.append({"scenario": name, "pass": False, "error": str(exc)})
                    errors.append(f"{name}: {exc}")
                else:
                    results.append({"scenario": name, "pass": True})
        except Exception as exc:
            results.append({"scenario": "engine_chain", "pass": False, "error": str(exc)})
            errors.append(f"engine_chain: {exc}")
        finally:
            SUMMARY.write_text(json.dumps({"scenarios": results}, indent=2), encoding="utf-8")
        self.assertFalse(errors, "\n".join(errors))

    def prepare_engine(self) -> None:
        names = {tool.name for tool in load_catalog(ROOT)}
        missing = [name for name in NEW_TOOLS if name not in names]
        if missing:
            raise AssertionError(f"catalog missing {missing}")
        tmp = Path(tempfile.mkdtemp(prefix="leo-engine-"))
        self.tmp = tmp
        pc = 2.0e6
        thrust = 2.5e5
        eps_nozzle = 16.0
        mixture = 2.3
        perf = run(
            script("skills", "ROCKET - PerformanceParameters", "src", "performance.py"),
            ["--pair", "LOX/RP1", "--pc", str(pc), "--eps", str(eps_nozzle), "--pa", "101325", "--r", str(mixture)],
        )
        vac = run(
            script("skills", "ROCKET - PerformanceParameters", "src", "performance.py"),
            ["--pair", "LOX/RP1", "--pc", str(pc), "--eps", str(eps_nozzle), "--pa", "0", "--r", str(mixture)],
        )
        throat = run(
            script("skills", "ROCKET - ThroatSizingandMassFlow", "throat_sizing.py"),
            ["--thrust", str(thrust), "--cf", perf["Cf"], "--pc", str(pc), "--cstar", perf["cstar_m_s"]],
        )
        delivered = run(
            script("skills", "ROCKET - LossStack", "loss_stack.py"),
            [
                "--cf", perf["Cf"],
                "--cstar", perf["cstar_m_s"],
                "--throat", throat["At_m2"],
                "--pc", str(pc),
                "--eta", "combustion=0.98",
                "--eta", "nozzle=0.97",
            ],
        )
        vacuum_delivered = run(
            script("skills", "ROCKET - LossStack", "loss_stack.py"),
            [
                "--cf", vac["Cf_vac"],
                "--cstar", vac["cstar_m_s"],
                "--eta", "combustion=0.98",
                "--eta", "nozzle=0.97",
            ],
        )
        gamma = perf["gamma"]
        run(
            script("skills", "ROCKET - ChamberVolumeAndCaseHoopStress", "chamber_case.py"),
            [
                "--throat", throat["At_m2"],
                "--lstar", "1.0",
                "--pc", str(pc),
                "--radius", str(max(0.2, float(throat["Dt_m"]))),
                "--thickness", "0.006",
                "--allowable", "4e8",
            ],
        )
        run(
            script("skills", "ROCKET - Area-Mach Graph", "area_mach.py"),
            [
                "--gamma", gamma,
                "--pc", str(pc),
                "--epsilon", str(eps_nozzle),
                "--pa", "101325",
                "--throat", throat["At_m2"],
                "--out", str(tmp / "area_mach.png"),
            ],
        )
        run(
            script("skills", "ROCKET - ExpansionMatchEarth", "expansion_match.py"),
            ["--pc", str(pc), "--gamma", gamma, "--alt", "0", "--throat", throat["At_m2"]],
        )
        nozzle = run(
            script("skills", "ROCKET - KickStageNozzle", "kick_stage_nozzle.py"),
            [
                "--pc", str(pc),
                "--gamma", gamma,
                "--pe", "5000",
                "--throat", throat["At_m2"],
                "--thickness", "0.004",
                "--rho-mat", "2700",
            ],
        )
        tb = 80.0
        prop = run(
            script("skills", "ROCKET - PropellantLoad", "propellant_load.py"),
            ["--mdot", delivered["mdot_kg_s"], "--tb", str(tb), "--r", perf["r"], "--pair", "LOX/RP1"],
        )
        run(
            script("skills", "ROCKET - InjectorOrificeFlow", "injector_orifice_flow.py"),
            ["--mdot", delivered["mdot_kg_s"], "--rho", perf["rho_b_kg_m3"], "--cd", "0.75", "--dp", "4e5", "--count", "80"],
        )
        feed = run(
            script("skills", "ROCKET - FeedSystemPressureBudget", "feed_system_pressure_budget.py"),
            [
                "--pc", str(pc),
                "--dp-injector", "4e5",
                "--dp", "jacket=1e5",
                "--rho", perf["rho_b_kg_m3"],
                "--height", "2",
            ],
        )
        tank = run(
            script("skills", "ROCKET - TankStructureMass", "tank_structure_mass.py"),
            [
                "--volume", prop["V_p_m3"],
                "--rho", prop["rho_b_kg_m3"],
                "--residuals", "0.02",
                "--meop", feed["meop_Pa"],
                "--allowable", "9e8",
                "--rho-mat", "4430",
            ],
        )
        heat = run(
            script("skills", "ROCKET - ThroatGasSideHeatFlux", "throat_gas_side_heat_flux.py"),
            [
                "--pc", str(pc),
                "--Tc", perf["Tc_K"],
                "--cstar", perf["cstar_m_s"],
                "--throat", throat["Dt_m"],
                "--curvature", str(max(0.05, 0.8 * float(throat["Dt_m"]))),
                "--tw", "800",
                "--mw", perf["Mw_kg_kmol"],
                "--gamma", gamma,
                "--recovery", "0.9",
            ],
        )
        run(
            script("skills", "ROCKET - RegenerativeCoolantHeatPickUp", "regenerative_coolant_heat_pickup.py"),
            [
                "--mdot", prop["mdot_f_kg_s"],
                "--cp", "2000",
                "--t-in", "300",
                "--flux", heat["q_dot_W_m2"],
                "--area", "0.02",
                "--t-max", "500",
            ],
        )
        pump = run(
            script("skills", "ROCKET - PumpHydraulicPower", "pump_hydraulic_power.py"),
            ["--mdot", prop["mdot_f_kg_s"], "--rho", perf["rho_fuel_kg_m3"], "--dp", "3e6", "--eta", "0.7"],
        )
        if num(pump, "P_shaft_W") <= 0.0:
            raise AssertionError("pump shaft power")
        solid = run(
            script("skills", "ROCKET - SolidMotorParameters", "solid_motor_parameters.py"),
            ["--a", "1e-5", "--n", "0.5", "--ab", "0.4", "--throat", "0.002", "--rho", "1800", "--cstar", perf["cstar_m_s"]],
        )
        run(
            script("skills", "ROCKET - CircularPortGrainHistory", "circular_port_grain_history.py"),
            [
                "--a", "1e-5",
                "--n", "0.5",
                "--port", "0.02",
                "--length", "0.4",
                "--outer", "0.05",
                "--throat", "0.0005",
                "--rho", "1800",
                "--cstar", perf["cstar_m_s"],
                "--out", str(tmp / "grain.png"),
            ],
        )
        if num(solid, "mdot_kg_s") <= 0.0:
            raise AssertionError("solid mass flow")
        self.isp_sl = num(delivered, "Isp_s")
        self.isp_vac = num(vacuum_delivered, "Isp_s")
        if self.isp_vac <= self.isp_sl:
            raise AssertionError(f"vacuum Isp {self.isp_vac} is not above sea-level {self.isp_sl}")
        self.mp_motor = num(prop, "m_p_kg")
        self.tank_kg = num(tank, "m_tank_kg")
        self.residual_kg = num(tank, "m_residual_kg")
        self.engine_kg = num(nozzle, "m_nozzle_kg")
        self.fairing_diameter = 1.2

    def scenario_small_two_stage(self) -> None:
        tmp = self.tmp
        lat = 28.5 * math.pi / 180.0
        east = run(
            script("skills", "ASTRO - LaunchAzimuthInclination", "launch_azimuth_inclination.py"),
            ["--lat", str(lat), "--az", str(math.pi / 2.0), "--out", str(tmp / "east.png")],
        )
        require_figure(east)
        if num(east, "i_rad") + 1e-8 < abs(lat):
            raise AssertionError("inclination below the site latitude")
        if num(east, "i_min_rad") > abs(lat) + 1e-6:
            raise AssertionError("minimum inclination")
        self.east_assist = num(east, "v_rot_assist_m_s")
        self.lat = lat
        fairing = run(
            script("skills", "ROCKET - FairingAndInterstageMass", "fairing_and_interstage_mass.py"),
            [
                "--fairing-diameter", str(self.fairing_diameter),
                "--cylinder-length", "2.5",
                "--nose-length", "0.8",
                "--nose", "ogive",
                "--interstage-diameter", str(self.fairing_diameter),
                "--interstage-length", "0.5",
                "--thickness", "0.003",
                "--rho", "2700",
                "--out", str(tmp / "fairing.png"),
            ],
        )
        if "graph" in fairing or "viewer" in fairing:
            raise AssertionError("fairing printed a figure")
        self.jettison_kg = num(fairing, "jettison_kg")
        budget = run(
            script("skills", "ROCKET - VehicleMassBudget", "vehicle_mass_budget.py"),
            [
                "--stages", "1",
                "--stage",
                (
                    f"mp={self.mp_motor:.8g},tank={self.tank_kg:.8g},"
                    f"engine-mass={self.engine_kg:.8g},engine-count=1,"
                    f"fairing={fairing['fairing_kg']},interstage={fairing['interstage_kg']},"
                    f"residuals={self.residual_kg:.8g}"
                ),
                "--payload", "50",
                "--out", str(tmp / "budget.png"),
            ],
        )
        require_png(budget)
        inert = num(budget, "stage_1_inert_kg")
        mp = num(budget, "stage_1_mp_kg")
        if not (0.0 < inert and mp < num(budget, "stacked_mass_kg")):
            raise AssertionError("mass budget continuity")
        self.eps = inert / (inert + mp)
        if not 0.0 < self.eps < 0.2:
            raise AssertionError(f"structural coefficient {self.eps} is outside a two-stage LEO range")
        losses = {
            "gravity": 900.0,
            "drag": 40.0,
            "steering": 0.0,
            "circ": 80.0,
            "margin": 150.0,
        }
        design = self.leo_budget(self.east_assist, losses, tmp / "leo.png")
        self.dv_design = num(design, "dv_design_m_s")
        if self.dv_design <= num(design, "v_circ_m_s") - self.east_assist:
            raise AssertionError("design delta-v does not exceed circular speed minus rotation")
        self.losses = losses
        # Payload is large enough that the computed fairing is a small fraction of upper-stage dry mass.
        split = self.split(2, (self.isp_sl, self.isp_vac), self.dv_design, payload=1500.0, mode="equal_dv", out=tmp / "split.png")
        solved = run(
            script("skills", "ROCKET - PayloadtoDeltaV", "payload_to_deltav.py"),
            [
                "--stages", "2",
                "--stage", split["payload_to_deltav_stage_1"],
                "--stage", split["payload_to_deltav_stage_2"],
                "--dv", f"{self.dv_design:.8g}",
            ],
        )
        payload = num(solved, "payload_kg")
        if payload < 0.0:
            raise AssertionError("payload at the design delta-v is negative")
        if abs(payload - num(split, "payload_kg")) > 1e-3 * max(1.0, payload):
            raise AssertionError(f"payload {payload} disagrees with the split {split['payload_kg']}")
        area = math.pi * (0.5 * self.fairing_diameter) ** 2
        m0 = num(split, "stacked_mass_kg")
        tb1 = num(split, "stage_1_mp_kg") * self.isp_sl / (m0 * 1.55)
        m02 = num(split, "payload_kg") + num(split, "stage_2_mp_kg") + num(split, "stage_2_inert_kg")
        tb2 = num(split, "stage_2_mp_kg") * self.isp_vac / (m02 * 1.35)
        ascent = run(
            script("skills", "ROCKET - MultiStageAscent", "multi_stage_ascent.py"),
            [
                "--stages", "2",
                "--stage", self.stage_burn(split, 1, tb1),
                "--stage", self.stage_burn(split, 2, tb2),
                "--payload", split["payload_kg"],
                "--gamma", "1.05",
                "--cd", "0.3",
                "--area", f"{area:.8g}",
                "--jettison", f"mass={self.jettison_kg:.8g},alt=80000",
                "--radius", str(R_ASCENT),
                "--mu", f"{MU_ASCENT:.8g}",
                "--out", str(tmp / "ascent.png"),
            ],
        )
        require_figure(ascent)
        if num(ascent, "stage_1_mp_kg") >= num(ascent, "stage_1_m0_kg"):
            raise AssertionError("stage propellant exceeds ignition mass")
        if abs(num(ascent, "stage_2_m0_kg") - m02) > 1e-3 * m02:
            raise AssertionError("stage 2 ignition mass")
        if num(ascent, "Z_bo_m") <= 0.0 or num(ascent, "V_bo_m_s") <= 0.0:
            raise AssertionError("burnout state")
        self.assert_jettison(Path(ascent["table"]), self.jettison_kg)
        q = run(
            script("skills", "ROCKET - MaxQAndAeroLoad", "max_q_and_aero_load.py"),
            ["--table", ascent["table"], "--alpha", "0.05", "--out", str(tmp / "q.png")],
        )
        require_figure(q)
        if num(q, "q_max_Pa") <= 0.0 or q.get("q_max_interior") != "yes":
            raise AssertionError(f"q_max {q.get('q_max_Pa')} interior {q.get('q_max_interior')}")
        moment = num(q, "alpha_q_max") * area * 1.5
        beam = run(
            script("skills", "STRUCT - BeamBendingStress", "beam_bending_stress.py"),
            ["--moment", f"{moment:.8g}", "--section-modulus", "0.002", "--allowable", "4e8", "--out", str(tmp / "beam.png")],
        )
        if num(beam, "sigma_Pa") <= 0.0:
            raise AssertionError("bending stress")
        column = run(
            script("skills", "STRUCT - EulerColumnBuckling", "euler_column_buckling.py"),
            ["--E", "7e10", "--inertia", "1e-4", "--length", "1.5", "--out", str(tmp / "column.png")],
        )
        if num(column, "P_cr_N") <= num(q, "q_max_Pa") * area:
            raise AssertionError("Euler load is below the dynamic-pressure force")
        air = run(script("skills", "ATMOS - Standard1976", "standard_1976.py"), ["--alt", "11000"])
        if num(air, "rho_kg_m3") <= 0.0:
            raise AssertionError("standard atmosphere")
        off = run(
            script("skills", "AERO - DensityAndPressureAltitude", "density_and_pressure_altitude.py"),
            ["--pressure", "90000", "--oat", "290"],
        )
        if num(off, "rho_kg_m3") <= 0.0:
            raise AssertionError("off-nominal density")
        insertion = run(
            script("skills", "ASTRO - OrbitInsertionFromBurnout", "orbit_insertion_from_burnout.py"),
            [
                "--r", ascent["r_bo_m"],
                "--v", ascent["V_bo_m_s"],
                "--gamma", ascent["gamma_bo_rad"],
                "--radius", str(R_ASCENT),
                "--mu", f"{MU_ASCENT:.8g}",
                "--out", str(tmp / "insert.png"),
            ],
        )
        require_html(insertion)
        if insertion.get("closed_orbit") != "yes":
            raise AssertionError(
                "burnout is not closed: "
                f"V={ascent.get('V_bo_m_s')} Z={ascent.get('Z_bo_m')} "
                f"gamma={ascent.get('gamma_bo_rad')} warning={insertion.get('warning')}"
            )
        if num(insertion, "dv_circ_m_s") < 0.0:
            raise AssertionError("circularization delta-v")
        if insertion.get("atmosphere_intersection") == "no" and num(insertion, "hp_m") < 120000.0:
            raise AssertionError("parking claim with periapsis in the atmosphere")

    def scenario_high_inclination(self) -> None:
        polar = run(
            script("skills", "ASTRO - LaunchAzimuthInclination", "launch_azimuth_inclination.py"),
            ["--lat", str(self.lat), "--i", str(math.pi / 2.0), "--out", str(self.tmp / "polar.png")],
        )
        require_figure(polar)
        assist = num(polar, "v_rot_assist_m_s")
        if abs(assist) >= self.east_assist - 1.0:
            raise AssertionError(f"polar assist {assist} did not shrink versus due east {self.east_assist}")
        if num(polar, "i_rad") + 1e-6 < abs(self.lat):
            raise AssertionError("polar inclination")
        design = self.leo_budget(assist, self.losses, self.tmp / "leo_polar.png")
        if num(design, "dv_design_m_s") <= self.dv_design:
            raise AssertionError("polar design delta-v did not increase")

    def scenario_three_stage(self) -> None:
        isps = (self.isp_sl, 0.5 * (self.isp_sl + self.isp_vac), self.isp_vac)
        split = self.split(3, isps, self.dv_design, payload=40.0, mode="equal_dv", out=self.tmp / "split3.png")
        args = ["--stages", "3", "--dv", f"{self.dv_design:.8g}"]
        for index in range(1, 4):
            args.extend(["--stage", split[f"payload_to_deltav_stage_{index}"]])
        solved = run(script("skills", "ROCKET - PayloadtoDeltaV", "payload_to_deltav.py"), args)
        payload = num(solved, "payload_kg")
        if abs(payload - num(split, "payload_kg")) > 1e-3 * max(1.0, payload):
            raise AssertionError("three-stage payload disagrees with PayloadtoDeltaV")
        glow = num(split, "stacked_mass_kg")
        best = self.split(3, isps, self.dv_design, glow=glow, mode="max_payload", out=self.tmp / "split3max.png")
        stacked = num(best, "payload_kg") + sum(num(best, f"stage_{i}_mp_kg") + num(best, f"stage_{i}_inert_kg") for i in range(1, 4))
        if abs(stacked - glow) > 1e-3 * glow:
            raise AssertionError("three-stage mass continuity")
        if num(best, "payload_kg") + 1e-6 < num(split, "payload_kg"):
            raise AssertionError("max_payload is below the equal split")

    def scenario_single_stage(self) -> None:
        basic = run(
            script("skills", "ROCKET - BasicTrajectoryLossesFromBodySurface", "basic_trajectory_losses_from_body_surface.py"),
            ["--m0", "10000", "--mp", "6000", "--isp", "300", "--tb", "80", "--gamma", "1.0", "--out", str(self.tmp / "basic.png")],
        )
        multi = run(
            script("skills", "ROCKET - MultiStageAscent", "multi_stage_ascent.py"),
            [
                "--stages", "1",
                "--stage", "mp=6000,inert=1000,isp=300,tb=80",
                "--payload", "3000",
                "--gamma", "1.0",
                "--out", str(self.tmp / "one.png"),
            ],
        )
        for key in ("gravity_loss_m_s", "V_bo_m_s", "Z_bo_m"):
            if abs(num(multi, key) - num(basic, key)) > 1e-4 * max(1.0, abs(num(basic, key))):
                raise AssertionError(f"{key} {multi[key]} vs {basic[key]}")

    def scenario_insertion_edges(self) -> None:
        mu = G0 * R0 * R0
        radius = R0 + 400000.0
        speed = math.sqrt(mu / radius)
        circular = run(
            script("skills", "ASTRO - OrbitInsertionFromBurnout", "orbit_insertion_from_burnout.py"),
            [
                "--r", f"{radius:.8g}",
                "--v", f"{speed:.8g}",
                "--gamma", "0",
                "--radius", str(R0),
                "--mu", f"{mu:.8g}",
                "--out", str(self.tmp / "circ.png"),
            ],
        )
        if circular.get("closed_orbit") != "yes" or circular.get("atmosphere_intersection") != "no":
            raise AssertionError("horizontal circular burnout is not a parking orbit")
        if abs(num(circular, "dv_circ_m_s")) > 1.0:
            raise AssertionError(f"circularization {circular['dv_circ_m_s']}")
        if num(circular, "hp_m") < 120000.0:
            raise AssertionError("parking periapsis")
        vertical = run(
            script("skills", "ASTRO - OrbitInsertionFromBurnout", "orbit_insertion_from_burnout.py"),
            ["--r", str(R0 + 50000.0), "--v", "800", "--gamma", str(math.pi / 2.0), "--radius", str(R0), "--mu", f"{mu:.8g}", "--out", str(self.tmp / "vert.png")],
        )
        if vertical.get("closed_orbit") != "no":
            raise AssertionError("vertical burnout closed")
        escape = math.sqrt(2.0 * mu / radius)
        hyperbolic = run(
            script("skills", "ASTRO - OrbitInsertionFromBurnout", "orbit_insertion_from_burnout.py"),
            ["--r", f"{radius:.8g}", "--v", f"{escape + 500:.8g}", "--gamma", "0.2", "--radius", str(R0), "--mu", f"{mu:.8g}", "--out", str(self.tmp / "hyper.png")],
        )
        if hyperbolic.get("closed_orbit") != "no":
            raise AssertionError("hyperbolic burnout closed")
        hohmann = run(
            script("skills", "ASTRO - HohmannTransfer", "hohmann_transfer.py"),
            ["--r1", f"{radius:.8g}", "--r2", f"{radius + 200000:.8g}", "--out", str(self.tmp / "hohmann.png")],
        )
        if num(hohmann, "dv_m_s") <= 0.0:
            raise AssertionError("Hohmann delta-v")
        raise_dv = run(
            script("skills", "ASTRO - MultiBurnLeoRaise", "multi_burn_leo_raise.py"),
            [
                "--a", f"{radius:.8g}",
                "--e", "0",
                "--i", "0.5",
                "--raan", "0.2",
                "--aop", "0",
                "--nu", "0",
                "--alt-target", "500000",
                "--thrust", "5000",
                "--isp", f"{self.isp_vac:.8g}",
                "--m0", "800",
                "--mp", "200",
                "--burns", "2",
                "--out", str(self.tmp / "raise.png"),
            ],
        )
        if num(raise_dv, "dv_total_m_s") <= 0.0:
            raise AssertionError("multi-burn delta-v")
        plane = run(
            script("skills", "ASTRO - PlaneChangeImpulse", "plane_change_impulse.py"),
            [
                "--a", f"{radius:.8g}",
                "--e", "0",
                "--i", "0.6",
                "--raan", "0.2",
                "--aop", "0",
                "--nu", "0",
                "--di", "0.05",
                "--out", str(self.tmp / "plane.png"),
            ],
        )
        plane_key = "dv_m_s" if "dv_m_s" in plane else next(key for key in plane if key.startswith("dv_"))
        if num(plane, plane_key) <= 0.0:
            raise AssertionError("plane-change delta-v")
        vacuum = run(
            script("skills", "ASTRO - VacuumPropellantMass", "vacuum_propellant_mass.py"),
            ["--dry", "200", "--isp", f"{self.isp_vac:.8g}", "--dv", hohmann["dv_m_s"], "--name", "raise"],
        )
        if num(vacuum, "m_propellant_kg") <= 0.0:
            raise AssertionError("vacuum propellant")
        drag = run(
            script("skills", "ASTRO - AerodynamicDragDeltaV", "aerodynamic_drag_delta_v.py"),
            ["--alt", "400000", "--mass", "200", "--cd", "2.2", "--area", "1.1"],
        )
        if num(drag, "dv_per_rev_m_s") < 0.0:
            raise AssertionError("drag delta-v")
        kick = run(
            script("skills", "ROCKET - KickStageFeasibility", "kick_stage_feasibility.py"),
            [
                "--thrust", "5000",
                "--isp", f"{self.isp_vac:.8g}",
                "--m0", "800",
                "--mp", "200",
                "--tb-max", "400",
                "--restarts-max", "3",
                "--out", str(self.tmp / "kickfeas.png"),
            ],
        )
        if kick.get("feasible") not in {"yes", "no"}:
            raise AssertionError("kick feasibility was not reported")

    def leo_budget(self, assist: float, losses: dict[str, float], out: Path) -> dict[str, str]:
        data = run(
            script("skills", "ROCKET - LeoDeltaVBudget", "leo_delta_v_budget.py"),
            [
                "--alt", "300000",
                "--v-rot", f"{assist:.8g}",
                "--gravity-loss", str(losses["gravity"]),
                "--drag-loss", str(losses["drag"]),
                "--steering-loss", str(losses["steering"]),
                "--circ", str(losses["circ"]),
                "--margin", str(losses["margin"]),
                "--out", str(out),
            ],
        )
        require_png(data)
        return data

    def split(
        self,
        stages: int,
        isps: tuple[float, ...],
        dv: float,
        out: Path,
        payload: float | None = None,
        glow: float | None = None,
        mode: str = "equal_dv",
    ) -> dict[str, str]:
        args = ["--stages", str(stages), "--dv", f"{dv:.8g}", "--mode", mode, "--out", str(out)]
        for isp in isps:
            args.extend(["--stage", f"isp={isp:.8g},eps={self.eps:.8g}"])
        if payload is not None:
            args.extend(["--payload", f"{payload:.8g}"])
        if glow is not None:
            args.extend(["--glow", f"{glow:.8g}"])
        data = run(script("skills", "ROCKET - StagePropellantSplit", "stage_propellant_split.py"), args)
        require_png(data)
        for index in range(1, stages + 1):
            ratio = num(data, f"stage_{index}_MR")
            if not 0.0 < ratio < 1.0:
                raise AssertionError(f"stage {index} mass ratio {ratio}")
            if num(data, f"stage_{index}_mp_kg") <= 0.0 or num(data, f"stage_{index}_inert_kg") <= 0.0:
                raise AssertionError(f"stage {index} masses")
        return data

    def stage_burn(self, split: dict[str, str], index: int, tb: float) -> str:
        return (
            f"mp={split[f'stage_{index}_mp_kg']},inert={split[f'stage_{index}_inert_kg']},"
            f"isp={split[f'stage_{index}_isp_s']},tb={tb:.8g}"
        )

    def assert_jettison(self, table: Path, mass: float) -> None:
        lines = table.read_text(encoding="utf-8").splitlines()[1:]
        drops: list[float] = []
        previous = None
        for line in lines:
            now = float(line.split(",")[6])
            if previous is not None:
                drops.append(previous - now)
            previous = now
        # Staging inert is a much larger step than the fairing. Propellant flow is the baseline.
        steps = [drop for drop in drops if 0.0 < drop < mass * 8.0]
        if len(steps) < 10:
            raise AssertionError("ascent table has no fairing-scale mass steps")
        baseline = sorted(steps)[len(steps) // 2]
        excess = max(step - baseline for step in steps)
        if abs(excess - mass) > 0.25 * mass + 5.0:
            raise AssertionError(f"fairing drop excess {excess} vs jettison {mass}")


if __name__ == "__main__":
    unittest.main()
