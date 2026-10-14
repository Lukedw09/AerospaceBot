"""Safe calculate tool: arithmetic, units, and rejection of unsafe expressions."""

from __future__ import annotations

import math
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

from app.calculate import (
    CalcError,
    _NAMES,
    _SYMBOLS,
    _TEMPERATURE,
    _canonical,
    calculate_request,
    evaluate,
)
from app.server import CALCULATE_DESCRIPTION

ROOT = Path(__file__).resolve().parents[2]


def _fields(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            found[key.strip()] = value.strip()
    return found


class CalculateTests(unittest.TestCase):
    def test_description_limits_temperature_to_absolute_readings(self) -> None:
        self.assertIn(
            "Temperature conversions convert absolute readings only. "
            "A temperature difference such as a 10 °C rise is 18 °F, not 50 °F, "
            "so a difference should be scaled by 9/5 by hand and not passed as a °C to °F conversion.",
            CALCULATE_DESCRIPTION,
        )

    def test_seconds_to_minutes(self) -> None:
        fields = _fields(calculate_request(value=120, from_unit="s", to_unit="min"))
        self.assertEqual(fields["input"], "120 s")
        self.assertEqual(fields["result"], "2")
        self.assertEqual(fields["units"], "min")

    def test_km_per_s_to_ft_per_s(self) -> None:
        fields = _fields(calculate_request(value=1, from_unit="km/s", to_unit="ft/s"))
        self.assertEqual(fields["units"], "ft/s")
        self.assertAlmostEqual(float(fields["result"]), 1000.0 / 0.3048, places=6)

    def test_degrees_and_radians(self) -> None:
        to_rad = _fields(calculate_request(value=180, from_unit="deg", to_unit="rad"))
        self.assertEqual(to_rad["units"], "rad")
        self.assertAlmostEqual(float(to_rad["result"]), math.pi, places=9)
        to_deg = _fields(calculate_request(value=math.pi, from_unit="rad", to_unit="degrees"))
        self.assertEqual(to_deg["units"], "degrees")
        self.assertEqual(to_deg["result"], "180")

    def test_expression_and_common_functions(self) -> None:
        added = _fields(calculate_request(expression="2 + 2 * 3"))
        self.assertEqual(added["input"], "2 + 2 * 3")
        self.assertEqual(added["result"], "8")
        self.assertEqual(added["units"], "dimensionless")
        self.assertEqual(_fields(calculate_request(expression="sqrt(4)"))["result"], "2")
        self.assertEqual(_fields(calculate_request(expression="log10(1000)"))["result"], "3")
        sine = float(_fields(calculate_request(expression="sin(radians(90))"))["result"])
        self.assertAlmostEqual(sine, 1.0, places=9)
        self.assertEqual(_fields(calculate_request(expression="degrees(pi)"))["result"], "180")

    def test_expression_result_can_be_converted(self) -> None:
        fields = _fields(calculate_request(expression="3 * 60", from_unit="s", to_unit="min"))
        self.assertEqual(fields["result"], "3")
        self.assertEqual(fields["units"], "min")

    def test_divide_by_zero(self) -> None:
        text = calculate_request(expression="1/0")
        self.assertIn("division by zero", text)
        self.assertNotIn("result:", text)

    def test_dunder_import_is_rejected(self) -> None:
        sentinel = "CALCULATE_IMPORT_SENTINEL"
        os.environ.pop(sentinel, None)
        text = calculate_request(expression="__import__('os')")
        self.assertIn("__import__", text)
        self.assertIn("not allowed", text)
        chained = calculate_request(
            expression="__import__('os').environ.update(CALCULATE_IMPORT_SENTINEL='pwned')"
        )
        self.assertTrue(chained.startswith("error:"))
        self.assertNotEqual(os.environ.get(sentinel), "pwned")
        self.assertTrue(calculate_request(expression="().__class__").startswith("error:"))

    def test_power_tower_is_rejected_without_hanging(self) -> None:
        script = (
            "import time\n"
            "from app.calculate import calculate_request\n"
            "started = time.perf_counter()\n"
            "print(calculate_request(expression='9**9**9'))\n"
            "print(f'elapsed {time.perf_counter() - started:.6f}')\n"
        )
        try:
            completed = subprocess.run(
                [sys.executable, "-c", script],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            self.fail(f"9**9**9 hung: {exc}")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("exponent is too large", completed.stdout)
        elapsed_line = next(line for line in completed.stdout.splitlines() if line.startswith("elapsed "))
        elapsed = float(elapsed_line.split()[1])
        self.assertLess(elapsed, 1.0)
        self.assertNotIn("result:", completed.stdout)

    def test_si_prefix_case_pairs(self) -> None:
        cases = (
            ("mPa", "Pa", 0.001),
            ("MPa", "Pa", 1_000_000.0),
            ("mm", "m", 0.001),
            ("Mm", "km", 1000.0),
            ("ms", "s", 0.001),
            ("Ms", "s", 1_000_000.0),
            ("mN", "N", 0.001),
            ("MN", "N", 1_000_000.0),
            ("mg", "kg", 1e-6),
            ("Mg", "kg", 1000.0),
        )
        for src, dst, expected in cases:
            with self.subTest(src=src, dst=dst):
                fields = _fields(calculate_request(value=1, from_unit=src, to_unit=dst))
                self.assertAlmostEqual(float(fields["result"]), expected, places=9)
        for left, right in (("mPa", "MPa"), ("mm", "Mm"), ("ms", "Ms"), ("mN", "MN"), ("mg", "Mg")):
            self.assertNotEqual(_canonical(left), _canonical(right))

    def test_symbol_keys_do_not_collapse(self) -> None:
        seen: dict[str, str] = {}
        for symbol in (*_SYMBOLS, *_TEMPERATURE):
            key = _canonical(symbol)
            self.assertNotIn(key, seen, f"{symbol} and {seen.get(key)} collapse to {key}")
            seen[key] = symbol
        for name, target in _NAMES.items():
            self.assertIn(target, seen, name)
        folded: dict[str, list[str]] = {}
        for symbol in seen:
            folded.setdefault(symbol.casefold(), []).append(symbol)
        collisions = {key: values for key, values in folded.items() if len(values) > 1}
        self.assertGreaterEqual(len(collisions), 5)
        for values in collisions.values():
            self.assertEqual(len({_canonical(value) for value in values}), len(values))

    def test_ambiguous_spellings_do_not_guess(self) -> None:
        for spelling in ("MM", "mpa", "MS", "mn", "MG", "KN"):
            with self.subTest(spelling=spelling):
                text = calculate_request(value=1, from_unit=spelling, to_unit="m")
                self.assertIn("ambiguous unit", text)
                self.assertNotIn("result:", text)

    def test_whole_word_names_ignore_case(self) -> None:
        for name in ("meters", "Meters", "METERS"):
            with self.subTest(name=name):
                fields = _fields(calculate_request(value=2, from_unit=name, to_unit="m"))
                self.assertEqual(fields["result"], "2")
                self.assertEqual(fields["units"], "m")

    def test_kelvin_below_absolute_zero_errors(self) -> None:
        text = calculate_request(value=-5, from_unit="K", to_unit="C")
        self.assertIn("absolute zero", text)
        self.assertNotIn("result:", text)
        zero = _fields(calculate_request(value=0, from_unit="K", to_unit="C"))
        self.assertEqual(zero["result"], "-273.15")

    def test_fahrenheit_below_absolute_zero_errors(self) -> None:
        text = calculate_request(value=-500, from_unit="F", to_unit="C")
        self.assertIn("absolute zero", text)
        self.assertNotIn("result:", text)

    def test_added_units_match_published_factors(self) -> None:
        exact = {
            ("ft/s^2", "m/s^2"): 0.3048,
            ("g0", "m/s^2"): 9.80665,
            ("GPa", "Pa"): 1_000_000_000.0,
            ("MN", "N"): 1_000_000.0,
            ("mN", "N"): 0.001,
            ("g", "kg"): 0.001,
            ("mg", "g"): 0.001,
            ("AU", "m"): 149_597_870_700.0,
            ("kJ", "J"): 1000.0,
            ("MJ", "J"): 1_000_000.0,
            ("kW", "W"): 1000.0,
            ("MW", "W"): 1_000_000.0,
            ("rpm", "deg/s"): 6.0,
        }
        for (src, dst), expected in exact.items():
            with self.subTest(src=src, dst=dst):
                fields = _fields(calculate_request(value=1, from_unit=src, to_unit=dst))
                self.assertEqual(float(fields["result"]), expected)
        close = {
            ("m/s^2", "ft/s^2"): 1.0 / 0.3048,
            ("kts", "m/s"): 1852.0 / 3600.0,
            ("kn", "m/s"): 1852.0 / 3600.0,
            ("J", "kJ"): 0.001,
            ("W", "kW"): 0.001,
            ("deg/s", "rad/s"): math.pi / 180.0,
            ("rad/s", "deg/s"): 180.0 / math.pi,
            ("rpm", "rad/s"): 2.0 * math.pi / 60.0,
        }
        for (src, dst), expected in close.items():
            with self.subTest(src=src, dst=dst):
                fields = _fields(calculate_request(value=1, from_unit=src, to_unit=dst))
                self.assertAlmostEqual(float(fields["result"]), expected, places=9)

    def test_gram_and_standard_gravity_are_different(self) -> None:
        gram = _fields(calculate_request(value=1, from_unit="g", to_unit="kg"))
        self.assertEqual(gram["result"], "0.001")
        gravity = _fields(calculate_request(value=1, from_unit="g0", to_unit="m/s^2"))
        self.assertEqual(gravity["result"], "9.80665")
        crossed = calculate_request(value=1, from_unit="g", to_unit="m/s^2")
        self.assertIn("cannot convert", crossed)
        self.assertNotIn("result:", crossed)
        capital = calculate_request(value=1, from_unit="G", to_unit="kg")
        self.assertTrue(capital.startswith("error:"))
        self.assertNotIn("result:", capital)

    def test_deadline_rejects_before_evaluating(self) -> None:
        with self.assertRaises(CalcError) as caught:
            evaluate("1+1", deadline=time.monotonic() - 1)
        self.assertIn("timed out", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
