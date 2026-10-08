"""Catalog, runner, formula allow-list, and the local plugin cases."""

from __future__ import annotations

import asyncio
import json
import math
import os
import shutil
import unittest
from pathlib import Path
from unittest import mock

os.environ["AUTH_DISABLED"] = "1"

from app.catalog import load_catalog, repo_root_from, tool_by_name
from app.config import Settings
from app.formulas import lookup_formula
from app.runner import _output_path, result_root_for, run_tool
from app.server import (
    INSTRUCTIONS,
    _Guard,
    build_server,
    dispatch_calculation,
    dispatch_formula,
    dispatch_list,
)

ROOT = repo_root_from(Path(__file__).resolve())


class CatalogTests(unittest.TestCase):
    def test_throat_sizing_is_listed_and_builder_is_not(self) -> None:
        tools = load_catalog(ROOT)
        names = {tool.name for tool in tools}
        self.assertIn("throat_sizing", names)
        self.assertNotIn("build_table", names)
        self.assertNotIn("check_formulas", names)
        throat = tool_by_name(tools, "throat_sizing")
        self.assertIsNotNone(throat)
        assert throat is not None
        self.assertEqual(throat.required_options(), ["--thrust", "--cf", "--pc", "--cstar"])
        options = {flag.option for flag in throat.flags}
        self.assertNotIn("--check", options)
        self.assertNotIn("--out", options)
        grain = tool_by_name(tools, "circular_port_grain_history")
        assert grain is not None
        grain_options = {flag.option for flag in grain.flags}
        self.assertIn("--outer", grain_options)
        self.assertNotIn("--out", grain_options)
        self.assertIn("--outer", grain.required_options())

    def test_propellant_load_density_paths_are_optional(self) -> None:
        tools = load_catalog(ROOT)
        tool = tool_by_name(tools, "propellant_load")
        assert tool is not None
        self.assertEqual(tool.required_options(), ["--mdot", "--tb", "--r"])
        optional = {flag.option for flag in tool.flags if not flag.required}
        self.assertEqual(optional, {"--pair", "--rho-ox", "--rho-fuel"})
        loss = tool_by_name(tools, "loss_stack")
        assert loss is not None
        self.assertNotIn("--throat", loss.required_options())
        self.assertNotIn("--pc", loss.required_options())
        solid = tool_by_name(tools, "solid_motor_parameters")
        assert solid is not None
        self.assertIn("--n", solid.required_options())

    def test_append_flags_keep_numeric_item_types(self) -> None:
        tools = load_catalog(ROOT)
        duty = tool_by_name(tools, "duty_cycle_load")
        assert duty is not None
        power = next(flag for flag in duty.flags if flag.option == "--power")
        self.assertTrue(power.repeat)
        self.assertEqual(power.type_name, "float")
        vacuum = tool_by_name(tools, "vacuum_propellant_mass")
        assert vacuum is not None
        dv = next(flag for flag in vacuum.flags if flag.option == "--dv")
        self.assertEqual(dv.type_name, "float")
        feed = tool_by_name(tools, "feed_system_pressure_budget")
        assert feed is not None
        drop = next(flag for flag in feed.flags if flag.option == "--dp")
        self.assertTrue(drop.repeat)
        self.assertEqual(drop.type_name, "string")
        server = build_server()
        power_schema = server._tool_manager._tools["duty_cycle_load"].parameters["properties"]["power"]
        self.assertEqual(power_schema["type"], "array")
        self.assertEqual(power_schema["items"]["type"], "number")
        coast_schema = server._tool_manager._tools["kick_stage_feasibility"].parameters["properties"]["coast"]
        self.assertEqual(coast_schema["items"]["type"], "number")


class RunnerTests(unittest.TestCase):
    def test_throat_sizing_known_values(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "throat_sizing")
        assert tool is not None
        result = run_tool(
            tool,
            {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600},
            repo_root=ROOT,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("At_m2: 0.0005", result.text)
        self.assertIn("mdot_kg_s: 0.625", result.text)

    def test_throat_sizing_missing_cstar(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "throat_sizing")
        assert tool is not None
        result = run_tool(
            tool,
            {"thrust": 1500, "cf": 1.5, "pc": 2e6},
            repo_root=ROOT,
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertTrue(result.missing_input)
        self.assertIn("missing", result.text.lower())
        self.assertNotIn("At_m2", result.text)

    def test_lambda_writes_under_tmp(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "throat_sizing")
        assert tool is not None
        with mock.patch.dict(os.environ, {"AWS_LAMBDA_FUNCTION_NAME": "aerospace"}):
            root = result_root_for(ROOT)
            result = run_tool(
                tool,
                {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600},
                repo_root=ROOT,
            )
        self.assertEqual(root, Path("/tmp/aerospace-results"))
        self.assertEqual(result.exit_code, 0)
        assert result.job_dir is not None
        self.assertEqual(result.job_dir.parent, root)
        self.assertTrue(result.job_dir.is_dir())
        shutil.rmtree(result.job_dir, ignore_errors=True)

    def test_outer_radius_is_not_the_plot_path(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "circular_port_grain_history")
        assert tool is not None
        result = run_tool(
            tool,
            {
                "a": 1e-5,
                "n": 0.5,
                "port": 0.02,
                "length": 0.4,
                "outer": 0.05,
                "throat": 0.0005,
                "rho": 1800,
                "cstar": 1550,
            },
            repo_root=ROOT,
        )
        self.assertEqual(result.exit_code, 0, result.text)
        self.assertNotIn("invalid float", result.text)
        self.assertIn("graph:", result.text)

    def test_expansion_point_does_not_receive_a_sweep_plot(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "expansion_match")
        assert tool is not None
        result = run_tool(
            tool,
            {"pc": 2e6, "alt": 0},
            repo_root=ROOT,
        )
        self.assertEqual(result.exit_code, 0, result.text)
        self.assertIn("mode: point", result.text)
        self.assertNotIn("graph:", result.text)

    def test_payload_point_does_not_receive_a_sweep_plot(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "payload_to_deltav")
        assert tool is not None
        result = run_tool(
            tool,
            {"stages": 1, "stage": ["mp=100,inert=10,isp-vac=300"], "payload": 5},
            repo_root=ROOT,
        )
        self.assertEqual(result.exit_code, 0, result.text)
        self.assertIn("mode: deltav", result.text)
        self.assertNotIn("graph:", result.text)

    def test_orbit_plot_stays_a_png_when_the_help_mentions_html(self) -> None:
        path = _output_path(
            Path("/tmp/aerospace-results/job"),
            "--out",
            "PNG path; the HTML viewer uses the same stem",
        )
        self.assertEqual(path.suffix, ".png")

    def test_naca_publishes_coeff_polar_and_ordinates(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "naca_four_digit_section")
        assert tool is not None
        result = run_tool(
            tool,
            {"naca": "0012", "chord": 1, "alpha": 0.06981317, "re": 3e6},
            repo_root=ROOT,
        )
        self.assertEqual(result.exit_code, 0, result.text)
        names = {path.name for path in result.files}
        self.assertEqual(
            names,
            {"out.png", "out_coeff.png", "out_polar.png", "out_ordinates.txt"},
        )
        for key in (
            "graph:",
            "coefficients_graph:",
            "polar_graph:",
            "ordinates:",
        ):
            line = next(row for row in result.text.splitlines() if row.startswith(key))
            path = Path(line.split(":", 1)[1].strip())
            self.assertTrue(path.is_file(), line)
            self.assertIn(path, result.files)
        pngs = [path for path in result.files if path.suffix == ".png"]
        self.assertEqual(len(pngs), 3)
        for path in pngs:
            self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        ordinates = next(path for path in result.files if path.name == "out_ordinates.txt")
        self.assertIn("xi yc_m yt_m", ordinates.read_text(encoding="utf-8").splitlines()[0])
        shutil.rmtree(result.job_dir, ignore_errors=True)

class FormulaTests(unittest.TestCase):
    def test_unknown_id_is_refused(self) -> None:
        text = lookup_formula(
            ROOT / "skills" / "FormulaCatalouge" / "formulas.md",
            ROOT / "skills" / "FormulaCatalouge" / "checks" / "check.md",
            "not_a_real_formula",
        )
        self.assertEqual(text, "that formula is not allowed")

    def test_perfect_gas_evaluates_when_symbols_are_present(self) -> None:
        text = lookup_formula(
            ROOT / "skills" / "FormulaCatalouge" / "formulas.md",
            ROOT / "skills" / "FormulaCatalouge" / "checks" / "check.md",
            "perfect_gas",
            '{"rho": 1.2, "R": 287, "T": 288.15}',
        )
        self.assertIn("result:", text)
        self.assertNotIn("not allowed", text)

    def test_perfect_gas_evaluates_from_an_object(self) -> None:
        text = lookup_formula(
            ROOT / "skills" / "FormulaCatalouge" / "formulas.md",
            ROOT / "skills" / "FormulaCatalouge" / "checks" / "check.md",
            "perfect_gas",
            {"rho": 1.2, "R": 287, "T": 288.15},
        )
        self.assertIn("result:", text)
        self.assertNotIn("not allowed", text)


class PluginCases(unittest.TestCase):
    def test_five_cases(self) -> None:
        full = dispatch_calculation(
            "throat_sizing",
            {"thrust": 1500, "cf": 1.5, "pc": 2e6, "cstar": 1600},
        )
        self.assertIn("At_m2: 0.0005", full)
        self.assertIn("mdot_kg_s: 0.625", full)

        missing = dispatch_calculation(
            "throat_sizing",
            {"thrust": 1500, "cf": 1.5, "pc": 2e6},
        )
        self.assertIn("missing", missing.lower())
        self.assertNotIn("At_m2", missing)

        gas = dispatch_formula(
            "perfect_gas",
            {"rho": 1.2, "R": 287, "T": 288.15},
        )
        self.assertIn("result:", gas)

        turn = dispatch_calculation(
            "incompressible_level_turn",
            {
                "speed": 50,
                "weight": 10000,
                "area": 16,
                "clmax": 1.6,
                "rho": 1.225,
                "bank": math.pi / 3,
            },
        )
        self.assertIn("graph:", turn)
        graph_line = next(line for line in turn.splitlines() if line.startswith("graph:"))
        graph_path = Path(graph_line.split(":", 1)[1].strip())
        self.assertTrue(graph_path.is_file())
        self.assertEqual(graph_path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertIn("app", graph_path.parts)
        self.assertIn("results", graph_path.parts)

        refused = dispatch_calculation("not_a_real_tool", {})
        self.assertEqual(refused, "that tool is not in the library")
        self.assertIn("Do not invent a formula.", INSTRUCTIONS)

    def test_server_registers_tools_without_cognito(self) -> None:
        server = build_server()
        names = set(server._tool_manager._tools)
        self.assertIn("throat_sizing", names)
        self.assertIn("lookup_formula", names)
        self.assertIn("list_tools", names)
        values_schema = server._tool_manager._tools["lookup_formula"].parameters["properties"]["values_json"]
        kinds = values_schema.get("anyOf", [values_schema])
        self.assertTrue(any(item.get("type") == "object" for item in kinds))
        self.assertNotIn("build_table", names)
        self.assertNotIn("check_formulas", names)

    def test_payload_to_deltav_documents_stage_keys(self) -> None:
        from app.catalog import load_catalog, tool_by_name

        tool = tool_by_name(load_catalog(ROOT), "payload_to_deltav")
        assert tool is not None
        self.assertIn("mp", tool.description)
        self.assertIn("inert", tool.description)
        self.assertIn("isp-vac", tool.description)
        self.assertIn("Do not invent keys such as `mstruct`", tool.description)
        stage_help = next(flag.help for flag in tool.flags if flag.option == "--stage")
        self.assertIn("mp", stage_help)
        self.assertIn("inert", stage_help)
        server = build_server()
        stage_schema = server._tool_manager._tools["payload_to_deltav"].parameters["properties"]["stage"]
        self.assertIn("mp", stage_schema.get("description", ""))
        self.assertIn("inert", stage_schema.get("description", ""))

    def test_performance_accepts_split_pair_array(self) -> None:
        import sys

        skill_src = ROOT / "skills" / "ROCKET - PerformanceParameters" / "src"
        sys.path.insert(0, str(skill_src))
        try:
            from load_table import normalize_pair_args
        finally:
            sys.path.remove(str(skill_src))

        self.assertEqual(normalize_pair_args(["LOX/RP1"]), ["LOX/RP1"])
        self.assertEqual(normalize_pair_args(["LOX", "RP1"]), ["LOX/RP1"])
        self.assertEqual(
            normalize_pair_args(["LOX", "RP1", "LOX", "CH4"]),
            ["LOX/RP1", "LOX/CH4"],
        )
        tool = tool_by_name(load_catalog(ROOT), "performance")
        assert tool is not None
        self.assertIn('["LOX/RP1"]', tool.description)
        joined = run_tool(
            tool,
            {"pair": ["LOX", "RP1"], "pc": 7e6, "eps": 40, "pa": 101325, "r": 2.3},
            repo_root=ROOT,
        )
        self.assertEqual(joined.exit_code, 0, joined.text)
        self.assertIn("pair: LOX/RP1", joined.text)
        single = run_tool(
            tool,
            {"pair": ["LOX/RP1"], "pc": 7e6, "eps": 40, "pa": 101325, "r": 2.3},
            repo_root=ROOT,
        )
        self.assertEqual(single.exit_code, 0, single.text)
        self.assertIn("pair: LOX/RP1", single.text)
        shutil.rmtree(joined.job_dir, ignore_errors=True)
        shutil.rmtree(single.job_dir, ignore_errors=True)

    def test_proportional_navigation_mode1_does_not_require_a_plot(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "proportional_navigation")
        assert tool is not None
        result = run_tool(
            tool,
            {"n_prime": 3, "vc": 1000, "los_rate": 0.01},
            repo_root=ROOT,
        )
        try:
            self.assertEqual(result.exit_code, 0, result.text)
            self.assertIn("mode: instantaneous", result.text)
            self.assertIn("a_c_m_s2: 30", result.text)
            self.assertNotIn("graph:", result.text)
            self.assertFalse(result.files)
        finally:
            if result.job_dir is not None:
                shutil.rmtree(result.job_dir, ignore_errors=True)

    def test_doppler_radial_path_does_not_require_a_plot(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "doppler_shift_budget")
        assert tool is not None
        result = run_tool(
            tool,
            {"freq": 2.2e9, "v_radial": 7000},
            repo_root=ROOT,
        )
        try:
            self.assertEqual(result.exit_code, 0, result.text)
            self.assertIn("path: radial", result.text)
            self.assertIn("fd_Hz:", result.text)
            self.assertIn("span_Hz:", result.text)
            self.assertNotIn("graph:", result.text)
            self.assertFalse(result.files)
        finally:
            if result.job_dir is not None:
                shutil.rmtree(result.job_dir, ignore_errors=True)

    def test_multi_stage_ascent_publishes_table_for_max_q(self) -> None:
        ascent_tool = tool_by_name(load_catalog(ROOT), "multi_stage_ascent")
        max_q_tool = tool_by_name(load_catalog(ROOT), "max_q_and_aero_load")
        assert ascent_tool is not None
        assert max_q_tool is not None
        ascent = run_tool(
            ascent_tool,
            {
                "stages": 2,
                "stage": [
                    "mp=100,inert=20,isp=250,tb=10",
                    "mp=40,inert=10,isp=300,tb=8",
                ],
                "payload": 10,
                "gamma": 1.2,
            },
            repo_root=ROOT,
        )
        try:
            self.assertEqual(ascent.exit_code, 0, ascent.text)
            table_line = next(
                row for row in ascent.text.splitlines() if row.startswith("table:")
            )
            table_path = Path(table_line.split(":", 1)[1].strip())
            self.assertTrue(table_path.is_file(), table_line)
            self.assertIn(table_path, ascent.files)
            self.assertEqual(table_path.suffix.lower(), ".csv")
            max_q = run_tool(
                max_q_tool,
                {"table": str(table_path), "alpha": 0.05},
                repo_root=ROOT,
            )
            try:
                self.assertEqual(max_q.exit_code, 0, max_q.text)
                self.assertIn("q_max_Pa:", max_q.text)
                self.assertIn("t_maxq_s:", max_q.text)
            finally:
                if max_q.job_dir is not None:
                    shutil.rmtree(max_q.job_dir, ignore_errors=True)
        finally:
            if ascent.job_dir is not None:
                shutil.rmtree(ascent.job_dir, ignore_errors=True)

    def test_missing_bearer_is_rejected(self) -> None:
        settings = Settings(
            auth_disabled=False,
            repo_root="",
            usage_table="",
            picture_bucket="",
            daily_tool_cap=20,
            tool_timeout_sec=60,
            result_link_hours=24,
            usage_timezone="America/New_York",
            cognito_user_pool_id="pool",
            cognito_client_id="client",
            cognito_region="us-east-1",
            public_base_url="",
            account_site_url="",
        )

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message):
            sent.append(message)

        async def inner(scope, receive, send):
            raise AssertionError("the program must not run")

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/mcp",
            "headers": [
                (b"x-forwarded-host", b"plugin.example"),
                (b"x-forwarded-proto", b"https"),
            ],
        }
        asyncio.run(_Guard(inner, settings)(scope, receive, send))
        self.assertEqual(sent[0]["status"], 401)
        headers = dict(sent[0]["headers"])
        self.assertIn(b"resource_metadata", headers[b"www-authenticate"])
        self.assertIn(b"https://plugin.example/.well-known/oauth-protected-resource", headers[b"www-authenticate"])

    def test_get_mcp_does_not_open_a_stream(self) -> None:
        settings = Settings(
            auth_disabled=False,
            repo_root="",
            usage_table="",
            picture_bucket="",
            daily_tool_cap=20,
            tool_timeout_sec=60,
            result_link_hours=24,
            usage_timezone="America/New_York",
            cognito_user_pool_id="pool",
            cognito_client_id="client",
            cognito_region="us-east-1",
            public_base_url="",
            account_site_url="",
        )

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        sent: list[dict] = []

        async def send(message):
            sent.append(message)

        async def inner(scope, receive, send):
            raise AssertionError("GET /mcp must not open a stream")

        scope = {"type": "http", "method": "GET", "path": "/mcp", "headers": []}
        asyncio.run(_Guard(inner, settings)(scope, receive, send))
        self.assertEqual(sent[0]["status"], 405)
        headers = dict(sent[0]["headers"])
        self.assertIn(b"POST", headers[b"allow"])


class LiftingEntrySchemaTests(unittest.TestCase):
    def test_bank_schedule_accepts_a_list_and_unknown_fields_fail(self) -> None:
        from mcp.server.mcpserver.exceptions import ToolError

        server = build_server()
        registered = server._tool_manager._tools["lifting_entry_trajectory"]
        self.assertIs(registered.parameters.get("additionalProperties"), False)
        bank = registered.parameters["properties"]["bank_schedule"]
        encoded = json.dumps(bank)
        self.assertIn("array", encoded)
        self.assertIn("t_s", encoded)
        self.assertIn("bank_deg", encoded)
        self.assertIn("out", registered.parameters["properties"])
        description = registered.description
        self.assertIn("inertial heading from north", description)
        self.assertIn("heading_air_deg", description)
        self.assertIn("lifting_entry_trajectory", dispatch_list())

        async def reject():
            await registered.run(
                {
                    "speed": 11032.1,
                    "gamma": 0.113097,
                    "altitude": 121920,
                    "lod": 0.30076,
                    "beta": 355.70326,
                    "bank_deg": 0,
                    "integrator": "rk4",
                },
                context=None,
            )

        with self.assertRaises(ToolError) as caught:
            asyncio.run(reject())
        message = str(caught.exception)
        self.assertIn("integrator", message)
        self.assertIn("valid parameters", message)
        self.assertIn("beta", message)
        self.assertIn("bank_schedule", message)

        direct = dispatch_calculation(
            "lifting_entry_trajectory",
            {
                "speed": 11032.1,
                "gamma": 0.113097,
                "altitude": 121920,
                "lod": 0.30076,
                "beta": 355.70326,
                "bank_deg": 0,
                "integrator": "rk4",
            },
        )
        self.assertIn("integrator", direct)
        self.assertIn("valid parameters", direct)
        self.assertNotIn("peak_g", direct)

    def test_graph_is_returned_only_when_out_is_passed(self) -> None:
        tool = tool_by_name(load_catalog(ROOT), "lifting_entry_trajectory")
        assert tool is not None
        self.assertIn("--out", {flag.option for flag in tool.flags})
        common = {
            "speed": 7000,
            "gamma": 0.1,
            "altitude": 80000,
            "lod": 0,
            "beta": 1e18,
            "bank_deg": 0,
            "max_time_s": 4,
            "dt": 1,
        }
        quiet = run_tool(tool, common, repo_root=ROOT)
        requested = run_tool(tool, {**common, "out": "lifting.png"}, repo_root=ROOT)
        try:
            self.assertEqual(quiet.exit_code, 0, quiet.text)
            self.assertNotIn("graph:", quiet.text)
            self.assertFalse(quiet.files)
            self.assertEqual(requested.exit_code, 0, requested.text)
            self.assertIn("graph:", requested.text)
            self.assertTrue(requested.files)
            self.assertTrue(requested.files[0].read_bytes().startswith(b"\x89PNG"))
        finally:
            shutil.rmtree(quiet.job_dir, ignore_errors=True)
            shutil.rmtree(requested.job_dir, ignore_errors=True)

        listed = run_tool(
            tool,
            {
                "speed": 11032.1,
                "gamma": 0.113097,
                "altitude": 121920,
                "lod": 0.30076,
                "beta": 355.70326,
                "bank_schedule": [
                    {"t_s": 0, "bank_deg": 0},
                    {"t_s": 60, "bank_deg": 0},
                    {"t_s": 61, "bank_deg": 90},
                ],
            },
            repo_root=ROOT,
        )
        try:
            self.assertEqual(listed.exit_code, 0, listed.text)
            self.assertIn("peak_g: 14.7008", listed.text)
            self.assertNotIn("graph:", listed.text)
        finally:
            shutil.rmtree(listed.job_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
