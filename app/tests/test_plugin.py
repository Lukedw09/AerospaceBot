ï»¿"""Catalog, runner, formula allow-list, and the local plugin cases."""

from __future__ import annotations

import asyncio
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
from app.server import INSTRUCTIONS, _Guard, build_server, dispatch_calculation, dispatch_formula

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
            ROOT / "skills" / "aero-formulas" / "formulas.md",
            ROOT / "skills" / "aero-formulas" / "checks" / "check.md",
            "not_a_real_formula",
        )
        self.assertEqual(text, "that formula is not allowed")

    def test_perfect_gas_evaluates_when_symbols_are_present(self) -> None:
        text = lookup_formula(
            ROOT / "skills" / "aero-formulas" / "formulas.md",
            ROOT / "skills" / "aero-formulas" / "checks" / "check.md",
            "perfect_gas",
            '{"rho": 1.2, "R": 287, "T": 288.15}',
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
            '{"rho": 1.2, "R": 287, "T": 288.15}',
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
        self.assertNotIn("build_table", names)
        self.assertNotIn("check_formulas", names)

    def test_payload_to_deltav_documents_stage_keys(self) -> None:
        from app.catalog import load_catalog, tool_by_name

        tool = tool_by_name(load_catalog(ROOT), "payload_to_deltav")
        assert tool is not None
        self.assertIn("mp", tool.description)
        self.assertIn("inert", tool.description)
        self.assertIn("isp-vac", tool.description)
        self.assertIn("Do not invent keys such as mstruct", tool.description)
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


if __name__ == "__main__":
    unittest.main()
