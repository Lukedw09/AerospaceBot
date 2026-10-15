"""Circular orbit about a uniform sphere.

Expected speeds and radii are computed here from G, the preset mass and
radius, and the closed-form surface relation. They are not copied from
the program's --check.
"""

from __future__ import annotations

import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "ASTRO - BodyCircularOrbit" / "body_circular_orbit.py"
G = 6.67430e-11

sys.path.insert(0, str(SCRIPT.parent))
import body_circular_orbit as orbit  # noqa: E402


def run(args: list[str]) -> tuple[int, dict[str, str], str]:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
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
    return proc.returncode, data, proc.stderr


def run_ok(test: unittest.TestCase, args: list[str]) -> dict[str, str]:
    code, data, err = run(args)
    test.assertEqual(code, 0, err)
    return data


def num(data: dict[str, str], key: str) -> float:
    return float(data[key])


def _body_fill_blobs(path: Path) -> int:
    """Count separate disks of the custom-body fill. The inset is a second disk."""
    from PIL import Image

    image = Image.open(path).convert("RGB")
    target = (0xF5, 0xCB, 0xA7)
    width, height = image.size
    pixels = image.load()
    seen = bytearray(width * height)
    blobs = 0

    def close(x: int, y: int) -> bool:
        red, green, blue = pixels[x, y]
        return abs(red - target[0]) <= 8 and abs(green - target[1]) <= 8 and abs(blue - target[2]) <= 8

    for y in range(height):
        for x in range(width):
            index = y * width + x
            if seen[index] or not close(x, y):
                continue
            size = 0
            stack = [(x, y)]
            seen[index] = 1
            while stack:
                cx, cy = stack.pop()
                size += 1
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    neighbor = ny * width + nx
                    if seen[neighbor] or not close(nx, ny):
                        continue
                    seen[neighbor] = 1
                    stack.append((nx, ny))
            if size >= 80:
                blobs += 1
    return blobs


class PresetCitationTests(unittest.TestCase):
    def test_every_preset_has_citation_url(self) -> None:
        self.assertGreaterEqual(len(orbit.PRESETS), 8)
        names = [preset.name for preset in orbit.PRESETS]
        for required in ("moon", "phobos", "deimos", "ceres", "vesta", "enceladus", "mimas", "earth", "jupiter"):
            self.assertIn(required, names)
        for preset in orbit.PRESETS:
            self.assertTrue(preset.url.startswith("https://"), preset.name)
            host = preset.url.split("/")[2]
            self.assertTrue(host.endswith("nasa.gov") or host.endswith("jpl.nasa.gov"), preset.url)
            self.assertTrue(preset.citation.strip(), preset.name)
            self.assertGreater(preset.mass_kg, 0.0)
            self.assertGreater(preset.radius_m, 0.0)
            self.assertGreater(preset.density_kg_m3, 0.0)


class CircularOrbitTests(unittest.TestCase):
    def test_moon_surface_speed_matches_gravity(self) -> None:
        moon = orbit.PRESET_BY_NAME["moon"]
        expected = math.sqrt(G * moon.mass_kg / moon.radius_m)
        result = orbit.resolve_body(
            speed=None,
            density=None,
            mass=None,
            radius=None,
            altitude=0.0,
            body="Moon",
            compare=None,
        )
        self.assertLess(abs(result.circular_speed - expected) / expected, 1e-9)
        self.assertGreater(result.circular_speed, 1670.0)
        self.assertLess(result.circular_speed, 1690.0)
        data = run_ok(self, ["--body", "moon", "--alt", "0", "--no-plot"])
        got = num(data, "circular_speed_m_s")
        self.assertLess(abs(got - expected) / expected, 1e-9)
        self.assertEqual(data["density_source"], moon.citation)
        self.assertEqual(data["G_m3_kg_s2"], "6.67430e-11")
        self.assertEqual(data["compare_body"], "mercury")

    def test_speed_density_surface_radii(self) -> None:
        for rho, km in ((2700.0, 54.4), (1900.0, 64.9)):
            data = run_ok(self, ["--v", "47.30", "--rho", str(rho), "--no-plot"])
            radius_km = num(data, "body_radius_m") / 1000.0
            self.assertLessEqual(abs(radius_km - km), 0.1)
            closed = 47.30 / math.sqrt((4.0 / 3.0) * math.pi * G * rho)
            self.assertLess(abs(num(data, "body_radius_m") - closed) / closed, 1e-9)
            self.assertEqual(data["density_source"], "typed")
            self.assertAlmostEqual(num(data, "altitude_m"), 0.0)

    def test_altitude_round_trip(self) -> None:
        speed = 120.0
        rho = 2200.0
        alt = 15000.0
        solved = orbit.radius_from_speed_density(speed, rho, alt)
        data = run_ok(
            self,
            ["--radius", f"{solved:.16g}", "--rho", str(rho), "--alt", str(alt), "--no-plot"],
        )
        got = num(data, "circular_speed_m_s")
        self.assertLess(abs(got - speed) / speed, 1e-9)

    def test_surface_escape_is_sqrt_two_times_circular(self) -> None:
        data = run_ok(self, ["--radius", "80000", "--rho", "3000", "--alt", "0", "--no-plot"])
        circular = num(data, "circular_speed_m_s")
        escape = num(data, "escape_speed_at_orbit_m_s")
        surface = num(data, "escape_speed_surface_m_s")
        self.assertLess(abs(escape - math.sqrt(2.0) * circular) / escape, 1e-9)
        self.assertLess(abs(surface - escape) / escape, 1e-9)

    def test_surface_period_depends_only_on_density(self) -> None:
        first = run_ok(self, ["--radius", "40000", "--rho", "1900", "--no-plot"])
        second = run_ok(self, ["--radius", "90000", "--rho", "1900", "--no-plot"])
        period = num(first, "period_s")
        self.assertLess(abs(num(second, "period_s") - period) / period, 1e-9)
        expected = 2.0 * math.pi * math.sqrt(3.0 / (4.0 * math.pi * G * 1900.0))
        self.assertLess(abs(period - expected) / expected, 1e-9)

    def test_invalid_inputs_are_errors(self) -> None:
        cases = [
            ([], "missing"),
            (["--v", "10"], "missing"),
            (["--rho", "2000"], "missing"),
            (["--mass", "1e18"], "missing"),
            (["--radius", "1000"], "missing"),
            (["--alt", "10"], "missing"),
            (["--v", "10", "--mass", "1e18"], "exactly one"),
            (["--v", "10", "--radius", "1000"], "exactly one"),
            (["--v", "10", "--rho", "2000", "--mass", "1e18"], "exactly one"),
            (["--v", "10", "--rho", "2000", "--radius", "1000"], "exactly one"),
            (["--mass", "1e18", "--rho", "2000"], "exactly one"),
            (["--mass", "1e18", "--radius", "1000", "--rho", "2000"], "exactly one"),
            (["--mass", "1e18", "--radius", "1000", "--v", "10"], "exactly one"),
            (["--body", "moon", "--rho", "3344"], "both set density"),
            (["--body", "moon", "--mass", "1e22"], "both set mass"),
            (["--body", "moon", "--mass", "1e22", "--radius", "1e6"], "both set mass"),
            (["--body", "moon", "--v", "10", "--rho", "3344"], "both set density"),
            (["--radius", "1e6", "--rho", "3000", "--body", "moon"], "both set density"),
            (["--v", "0", "--rho", "2000"], "must be > 0"),
            (["--v", "-3", "--rho", "2000"], "must be > 0"),
            (["--rho", "0", "--radius", "1000"], "must be > 0"),
            (["--rho", "-1", "--v", "10"], "must be > 0"),
            (["--mass", "0", "--radius", "1000"], "must be > 0"),
            (["--mass", "-5", "--radius", "1000"], "must be > 0"),
            (["--radius", "0", "--rho", "2000"], "must be > 0"),
            (["--radius", "-10", "--mass", "1e18"], "must be > 0"),
            (["--alt", "-1", "--body", "moon"], "must be >= 0"),
            (["--v", "nan", "--rho", "2000"], "finite"),
            (["--v", "inf", "--rho", "2000"], "finite"),
            (["--body", "pluto-not-a-preset-typo"], "unknown body"),
            (["--compare", "not-a-body", "--body", "moon"], "unknown body"),
            (["--v", "1e308", "--rho", "1e-308", "--alt", "1"], "no circular-orbit radius"),
        ]
        for argv, snippet in cases:
            code, _data, err = run([*argv, "--no-plot"] if argv else argv)
            self.assertNotEqual(code, 0, argv)
            self.assertEqual(code, 2, err)
            self.assertTrue(err.startswith("error:"), err)
            self.assertIn(snippet, err)
            self.assertNotIn("Traceback", err)

    def test_one_call_returns_exactly_one_png(self) -> None:
        from app.catalog import load_catalog, tool_by_name
        from app.runner import run_tool

        tool = tool_by_name(load_catalog(ROOT), "body_circular_orbit")
        self.assertIsNotNone(tool)
        assert tool is not None
        result = run_tool(
            tool,
            {"v": 47.30, "rho": 2700},
            repo_root=ROOT,
            timeout_sec=60,
        )
        self.assertEqual(result.exit_code, 0, result.text)
        graph_lines = [line for line in result.text.splitlines() if line.startswith("graph:")]
        self.assertEqual(graph_lines, [f"graph: {result.files[0]}"] if result.files else [])
        pngs = [path for path in result.files if path.suffix.lower() == ".png"]
        self.assertEqual(len(pngs), 1)
        self.assertEqual(list(result.job_dir.glob("*.png")), pngs)
        self.assertEqual(pngs[0].read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
        self.assertIn("orbit_inset: yes", result.text)
        self.assertGreaterEqual(_body_fill_blobs(pngs[0]), 2)
        wide = run_ok(
            self,
            ["--radius", "100000", "--rho", "2700", "--alt", "400000", "--compare", "phobos", "--out", str(Path(result.job_dir) / "wide.png")],
        )
        wide_path = Path(wide["graph"])
        self.assertEqual(wide["orbit_inset"], "no")
        self.assertEqual(_body_fill_blobs(wide_path), 1)
        self.assertEqual(sorted(path.name for path in result.job_dir.glob("*.png")), ["out.png", "wide.png"])

    def test_png_for_tiny_body_and_moon(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            tiny = Path(folder) / "tiny.png"
            moon = Path(folder) / "moon.png"
            tiny_data = run_ok(self, ["--radius", "50000", "--rho", "2700", "--out", str(tiny)])
            moon_data = run_ok(self, ["--body", "moon", "--out", str(moon)])
            self.assertEqual(tiny_data["compare_body"], "mimas")
            self.assertEqual(moon_data["compare_body"], "mercury")
            self.assertIn(orbit.IDEALIZED_NOTE, "Idealized: uniform sphere, no atmosphere, no terrain")
            for path, data in ((tiny, tiny_data), (moon, moon_data)):
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size, 1000)
                self.assertEqual(path.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(data["graph"], str(path.resolve()))

    def test_catalog_lists_the_tool_without_required_flags(self) -> None:
        from app.catalog import load_catalog, tool_by_name

        tool = tool_by_name(load_catalog(ROOT), "body_circular_orbit")
        self.assertIsNotNone(tool)
        assert tool is not None
        self.assertEqual(tool.skill, "ASTRO - BodyCircularOrbit")
        self.assertEqual(tool.required_options(), [])
        options = {flag.option for flag in tool.flags}
        self.assertIn("--v", options)
        self.assertIn("--body", options)
        self.assertIn("--compare", options)
        self.assertNotIn("--check", options)
        self.assertNotIn("--out", options)
        self.assertIn("BodyCircularOrbit", tool.description)


if __name__ == "__main__":
    unittest.main()
