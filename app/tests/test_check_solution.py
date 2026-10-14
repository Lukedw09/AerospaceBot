"""Development-set tests for the prototype homework checker.

The development set lives in the skill folder. It is not a scoring set.
A fully correct solution must not receive an error verdict. The 1% false-alarm
claim is not made from this sample.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
import unittest
from pathlib import Path

os.environ["AUTH_DISABLED"] = "1"

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "ASTRO - CheckSolution"
DEV_SET = SKILL / "dev_set.json"

ERROR_NOTES = {
    "dimensions are inconsistent",
    "sign disagrees with the value implied by the previous lines",
    "the two sides are not algebraically equivalent",
    "the number does not match evaluation of this line",
    "the relation does not match a checked formula for this quantity",
}


def load_checker():
    name = "astraeus_check_solution"
    spec = importlib.util.spec_from_file_location(name, SKILL / "check_solution.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CHECKER = load_checker()


def line_keys(result: dict[str, str], suffix: str) -> list[str]:
    names = [key for key in result if key.startswith("line_") and key.endswith(suffix)]
    return sorted(names, key=CHECKER._line_sort)


class DevSetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = json.loads(DEV_SET.read_text(encoding="utf-8"))
        cls.results = {case["id"]: CHECKER.run_dev_case(case) for case in cls.document["cases"]}

    def test_each_case_matches_its_expectation(self) -> None:
        for case in self.document["cases"]:
            result = self.results[case["id"]]
            self.assertEqual(result["__exit__"], "0", result.get("__stderr__"))
            self.assertEqual(result["prototype"], "yes", case["id"])
            self.assertEqual(result["banner"], "PROTOTYPE homework checker", case["id"])
            self.assertEqual(result["mode"], "hint", case["id"])
            expected = case["expect"]
            verdicts = [result[key] for key in line_keys(result, "_verdict")]
            self.assertEqual(verdicts, expected["verdicts"], case["id"])
            errors = [result[key] for key in line_keys(result, "_error_type")]
            self.assertEqual(errors, expected["error_types"], case["id"])
            self.assertEqual(result["final_check"], expected["final_check"], case["id"])
            if "note_contains" in expected:
                self.assertIn(expected["note_contains"], result["final_note"], case["id"])

    def test_correct_solutions_have_no_false_error_or_abstention(self) -> None:
        for case in self.document["cases"]:
            if not case["correct_solution"]:
                continue
            result = self.results[case["id"]]
            verdicts = [result[key] for key in line_keys(result, "_verdict")]
            self.assertNotIn("error", verdicts, case["id"])
            self.assertNotIn("can't verify", verdicts, case["id"])
            self.assertEqual(result["final_check"], "match", case["id"])

    def test_hint_notes_do_not_give_a_corrected_line(self) -> None:
        for case in self.document["cases"]:
            result = self.results[case["id"]]
            for key in line_keys(result, "_note"):
                if not key.replace("_note", "_error_type") in result and not key.endswith("_note"):
                    continue
                line_no = key.split("_")[1]
                error_key = f"line_{line_no}_error_type"
                if error_key not in result:
                    continue
                self.assertIn(result[key], ERROR_NOTES, case["id"])
                self.assertNotIn("=", result[key], case["id"])

    def test_unlocated_mismatch_does_not_name_a_line(self) -> None:
        result = self.results["hohmann_unlocated_final"]
        self.assertEqual(
            result["final_note"],
            "Final answer doesn't match. Likely a setup or formula error. Couldn't locate the line.",
        )
        self.assertNotIn("line_", result["final_note"])
        self.assertEqual(result["verdict_error"], "0")

    def test_reference_numbers_come_from_the_repo_tools(self) -> None:
        vac = CHECKER.vacuum_module()
        hoh = CHECKER.hohmann_module()
        ve = 3000.0
        mf = 200.0
        m0 = 1000.0
        dv = ve * math.log(m0 / mf)
        final, prop, wet = vac.propellant_mass(mf, 0.0, dv, ve)
        self.assertAlmostEqual(wet, m0, delta=1e-6)
        rocket = self.results["rocket_propellant_correct"]
        self.assertAlmostEqual(float(rocket["final_reference"]), prop, delta=1e-6)
        body = hoh.resolve_body(None)
        transfer = hoh.solve_transfer(body.mu, 6_774_200.0, 7_374_200.0, "radii")
        outward = self.results["hohmann_outward_correct"]
        # stdout prints .8g, so the printed reference is the tool value to 8 figures.
        self.assertAlmostEqual(float(outward["final_reference"]), transfer.dv, delta=5e-5)
        self.assertEqual(outward["final_reference_tool"], "hohmann_transfer")
        self.assertEqual(rocket["final_reference_tool"], "vacuum_propellant_mass")

    def test_dev_report_does_not_claim_the_one_percent_bar(self) -> None:
        report = dev_report(self.document["cases"], self.results)
        print(report)
        self.assertIn("false alarms", report)
        self.assertIn("95% upper bound", report)
        self.assertNotIn("≤1%", report)
        self.assertNotIn("<=1%", report)
        self.assertNotIn("at most 1%", report)
        correct = [case for case in self.document["cases"] if case["correct_solution"]]
        self.assertGreaterEqual(len(correct), 10)
        self.assertLessEqual(len(self.document["cases"]), 20)
        false_alarms = 0
        for case in correct:
            verdicts = [self.results[case["id"]][key] for key in line_keys(self.results[case["id"]], "_verdict")]
            if "error" in verdicts:
                false_alarms += 1
        self.assertEqual(false_alarms, 0)
        self.assertIn(f"0 false alarms in {len(correct)} correct solutions", report)


class SchemaTests(unittest.TestCase):
    def test_tool_is_registered_with_enums_and_rejects_unknown_fields(self) -> None:
        from app.catalog import load_catalog, tool_by_name
        from app.server import build_server, dispatch_calculation

        tool = tool_by_name(load_catalog(ROOT), "check_solution")
        self.assertIsNotNone(tool)
        assert tool is not None
        self.assertEqual(tool.required_options(), ["--family", "--target", "--solution"])
        options = {flag.option for flag in tool.flags}
        self.assertNotIn("--check", options)
        family = next(flag for flag in tool.flags if flag.option == "--family")
        target = next(flag for flag in tool.flags if flag.option == "--target")
        mode = next(flag for flag in tool.flags if flag.option == "--mode")
        self.assertEqual(family.choices, ("rocket_equation", "hohmann"))
        self.assertIn("delta_v", target.choices or ())
        self.assertIn("dv_total", target.choices or ())
        self.assertEqual(mode.choices, ("hint",))

        server = build_server()
        registered = server._tool_manager._tools["check_solution"]
        self.assertIs(registered.parameters.get("additionalProperties"), False)
        self.assertEqual(
            registered.parameters["properties"]["family"]["enum"],
            ["rocket_equation", "hohmann"],
        )
        self.assertIn("time_of_flight", registered.parameters["properties"]["target"]["enum"])
        mode_schema = registered.parameters["properties"]["mode"]
        self.assertEqual(mode_schema["const"], "hint")
        self.assertIn("Allowed values: hint.", mode_schema["description"])
        self.assertIn("vacuum_propellant_mass", server._tool_manager._tools)
        self.assertIn("hohmann_transfer", server._tool_manager._tools)

        rejected = dispatch_calculation(
            "check_solution",
            {
                "family": "rocket_equation",
                "target": "delta_v",
                "solution": "dv = ve*ln(m0/mf)",
                "m0_kg": 1000,
                "mf_kg": 200,
                "ve_m_s": 3000,
                "nope": 1,
            },
        )
        self.assertIn("unknown parameter", rejected)
        self.assertIn("nope", rejected)
        self.assertNotIn("final_check", rejected)

    def test_wrong_family_target_lists_allowed_values(self) -> None:
        code, _stdout, stderr = CHECKER.run_dict(
            {
                "family": "rocket_equation",
                "target": "dv_total",
                "solution": "dv = 1",
                "m0_kg": 10,
            }
        )
        self.assertEqual(code, 2)
        self.assertIn("allowed targets", stderr)
        self.assertIn("delta_v", stderr)
        self.assertNotIn("dv_total", stderr.split("allowed targets:", 1)[-1])

    def test_empty_solution_is_missing_input(self) -> None:
        code, _stdout, stderr = CHECKER.run_dict(
            {"family": "hohmann", "target": "dv_total", "solution": "   ", "r1_m": 7000000, "r2_m": 8000000}
        )
        self.assertEqual(code, 2)
        self.assertIn("missing", stderr.lower())


def dev_report(cases: list[dict], results: dict[str, dict[str, str]]) -> str:
    correct = [case for case in cases if case.get("correct_solution")]
    false_alarms = 0
    for case in correct:
        verdicts = [results[case["id"]][key] for key in line_keys(results[case["id"]], "_verdict")]
        if "error" in verdicts:
            false_alarms += 1
    n_correct = len(correct)
    if false_alarms == 0:
        bound = f"0 false alarms in {n_correct} correct solutions, 95% upper bound ≈ {3 / n_correct:.4f} (3/N)"
    else:
        # Clopper-Pearson upper bound via the beta-binomial relation, no scipy.
        # P(X <= k) = 1 - I_p(k+1, n-k); invert by bisection on the survival function.
        bound_value = _binomial_upper(false_alarms, n_correct, 0.95)
        bound = (
            f"{false_alarms} false alarms in {n_correct} correct solutions, "
            f"95% upper bound = {bound_value:.4f}"
        )

    checked = 0
    cant = 0
    correct_checked = 0
    correct_cant = 0
    for case in cases:
        result = results[case["id"]]
        checked += int(result["checked_line_count"])
        cant += int(result["verdict_cant_verify"])
        if case.get("correct_solution"):
            correct_checked += int(result["checked_line_count"])
            correct_cant += int(result["verdict_cant_verify"])

    planted_hits: dict[str, list[bool]] = {}
    for case in cases:
        planted = case.get("planted")
        if not planted:
            continue
        result = results[case["id"]]
        errors = [result[key] for key in line_keys(result, "_error_type")]
        verdicts = [result[key] for key in line_keys(result, "_verdict")]
        if planted == "unlocated":
            hit = (
                "Couldn't locate the line." in result.get("final_note", "")
                and "error" not in verdicts
            )
        elif planted == "approximation":
            hit = "approximation" in verdicts and "error" not in verdicts
        elif planted == "can't verify":
            hit = "can't verify" in verdicts and "error" not in verdicts
        else:
            hit = planted in errors
        planted_hits.setdefault(planted, []).append(hit)

    lines = [
        "PROTOTYPE dev set (not a scoring set).",
        bound + ".",
        "This sample does not support the locked false-alarm ship bar. That bar needs N >= 300 correct solutions with zero false alarms.",
        f"can't verify: {cant} of {checked} checked lines ({(cant / checked) if checked else 0:.4f}).",
        f"can't verify on fully correct solutions: {correct_cant} of {correct_checked}.",
        "catch rate by planted label (dev set only, no ship bar):",
    ]
    for label, hits in planted_hits.items():
        caught = sum(1 for hit in hits if hit)
        lines.append(f"  {label}: {caught}/{len(hits)}")
    return "\n".join(lines)


def _binomial_upper(k: int, n: int, confidence: float) -> float:
    """Clopper-Pearson upper bound. Exact for the false-alarm count."""
    if k >= n:
        return 1.0
    alpha = 1.0 - confidence
    lo, hi = 0.0, 1.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        # Survival P(X <= k) = regularized beta; compare the binomial tail.
        if _binom_cdf(k, n, mid) > alpha:
            lo = mid
        else:
            hi = mid
    return hi


def _binom_cdf(k: int, n: int, p: float) -> float:
    total = 0.0
    term = (1.0 - p) ** n
    for i in range(k + 1):
        total += term
        if i == n:
            break
        term *= (n - i) / (i + 1) * p / (1.0 - p)
    return min(1.0, total)


if __name__ == "__main__":
    unittest.main()
