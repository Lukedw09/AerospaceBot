"""Catalog, runner, formula allow-list, and the local plugin cases."""

from __future__ import annotations

import asyncio
import math
import os
import unittest
from pathlib import Path

os.environ["AUTH_DISABLED"] = "1"

from app.catalog import load_catalog, repo_root_from, tool_by_name
from app.config import Settings
from app.formulas import lookup_formula
from app.runner import run_tool
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


if __name__ == "__main__":
    unittest.main()
