#!/usr/bin/env python3
"""Vacuum free-space radio link budget (Friis).

free_space_path_loss is Lfs = (4*pi*R/lam)**2. friis_received_power is
Pr = Pt*Gt*Gr*(lam/(4*pi*R))**2. Circular-aperture gains use
antenna_gain_circular_aperture. Optional noise gives
carrier_to_noise_density and carrier_to_noise_ratio. Optional required
Eb/N0 and bit rate give eb_n0_from_cn0 and link_margin_eb_n0.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

CHECK_TOL = 1e-9
PLOT_TITLE = "Free-space link budget"
N_CURVE = 201
PLOT_END_FACTOR = 2.0
C_LIGHT = 299792458.0
K_BOLTZMANN = 1.380649e-23
SKILL_DIR = Path(__file__).resolve().parent

ASSUMPTIONS = (
    "vacuum free-space Friis link; no atmosphere, rain, pointing, or "
    "polarization loss; "
    f"c = {C_LIGHT:g} m/s and k = {K_BOLTZMANN:g} J/K (NIST CODATA 2022); "
    "wavelength_from_frequency lam = c/f; "
    "free_space_path_loss Lfs = (4*pi*R/lam)**2; "
    "friis_received_power Pr = Pt*Gt*Gr*(lam/(4*pi*R))**2; "
    "antenna_gain_circular_aperture G = eta*(pi*D/lam)**2 when diameters "
    "are supplied; "
    "eirp = Pt*Gt; "
    "optional thermal_noise_power Pn = k*Ts*B and "
    "noise_spectral_density N0 = k*Ts; "
    "carrier_to_noise_density CN0 = Pr/(k*Ts); "
    "carrier_to_noise_ratio CN = Pr/(k*Ts*B); "
    "eb_n0_from_cn0 EbN0 = CN0/Rb; "
    "link_margin_eb_n0 M = EbN0/EbN0req; "
    "modulation details beyond the supplied Eb/N0 requirement are omitted"
)


@dataclass(frozen=True)
class Solution:
    pt: float
    gt: float
    gr: float
    range_m: float
    frequency: float
    wavelength: float
    lfs: float
    eirp: float
    pr: float
    gt_source: str
    gr_source: str
    dt: float | None
    dr: float | None
    eta_t: float | None
    eta_r: float | None
    ts: float | None
    bandwidth: float | None
    n0: float | None
    cn0: float | None
    cn: float | None
    pn: float | None
    bitrate: float | None
    eb_n0: float | None
    eb_n0_req: float | None
    margin: float | None


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


def require_unit_interval(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite and in (0, 1]")


def to_db(ratio: float) -> float:
    """10*log10(ratio)."""
    return 10.0 * math.log10(ratio)


def wavelength_from_frequency(frequency: float, c_light: float = C_LIGHT) -> float:
    """wavelength_from_frequency."""
    return c_light / frequency


def frequency_from_wavelength(wavelength: float, c_light: float = C_LIGHT) -> float:
    """frequency_from_wavelength."""
    return c_light / wavelength


def free_space_path_loss(range_m: float, wavelength: float) -> float:
    """free_space_path_loss."""
    return (4.0 * math.pi * range_m / wavelength) ** 2


def free_space_path_loss_db(range_m: float, wavelength: float) -> float:
    """free_space_path_loss_db."""
    return to_db(free_space_path_loss(range_m, wavelength))


def antenna_gain_from_effective_aperture(area_e: float, wavelength: float) -> float:
    """antenna_gain_from_effective_aperture."""
    return 4.0 * math.pi * area_e / (wavelength * wavelength)


def antenna_gain_circular_aperture(
    diameter: float, wavelength: float, efficiency: float
) -> float:
    """antenna_gain_circular_aperture."""
    return efficiency * (math.pi * diameter / wavelength) ** 2


def eirp(pt: float, gt: float) -> float:
    """eirp."""
    return pt * gt


def friis_received_power(
    pt: float, gt: float, gr: float, wavelength: float, range_m: float
) -> float:
    """friis_received_power."""
    return pt * gt * gr * (wavelength / (4.0 * math.pi * range_m)) ** 2


def thermal_noise_power(ts: float, bandwidth: float, k_b: float = K_BOLTZMANN) -> float:
    """thermal_noise_power."""
    return k_b * ts * bandwidth


def noise_spectral_density(ts: float, k_b: float = K_BOLTZMANN) -> float:
    """noise_spectral_density."""
    return k_b * ts


def carrier_to_noise_density(pr: float, ts: float, k_b: float = K_BOLTZMANN) -> float:
    """carrier_to_noise_density."""
    return pr / (k_b * ts)


def carrier_to_noise_ratio(
    pr: float, ts: float, bandwidth: float, k_b: float = K_BOLTZMANN
) -> float:
    """carrier_to_noise_ratio."""
    return pr / (k_b * ts * bandwidth)


def eb_n0_from_cn0(cn0: float, bitrate: float) -> float:
    """eb_n0_from_cn0."""
    return cn0 / bitrate


def link_margin_eb_n0(eb_n0: float, eb_n0_req: float) -> float:
    """link_margin_eb_n0."""
    return eb_n0 / eb_n0_req


def resolve_gain(
    gain: float | None,
    diameter: float | None,
    efficiency: float | None,
    wavelength: float,
    *,
    gain_flag: str,
    diameter_flag: str,
    efficiency_flag: str,
) -> tuple[float, str, float | None, float | None]:
    has_gain = gain is not None
    has_dish = diameter is not None or efficiency is not None
    if has_gain and has_dish:
        raise ValueError(
            f"pass {gain_flag}, or {diameter_flag} with {efficiency_flag}, not both"
        )
    if has_gain:
        assert gain is not None
        require_positive(gain_flag, gain)
        return gain, "gain", None, None
    if diameter is None or efficiency is None:
        raise ValueError(f"requires {gain_flag}, or {diameter_flag} with {efficiency_flag}")
    require_positive(diameter_flag, diameter)
    require_unit_interval(efficiency_flag, efficiency)
    value = antenna_gain_circular_aperture(diameter, wavelength, efficiency)
    return value, "diameter", diameter, efficiency


def evaluate(
    pt: float,
    range_m: float,
    frequency: float | None,
    wavelength: float | None,
    gt: float | None,
    gr: float | None,
    dt: float | None,
    dr: float | None,
    eta_t: float | None,
    eta_r: float | None,
    ts: float | None,
    bandwidth: float | None,
    bitrate: float | None,
    eb_n0_req: float | None,
) -> Solution:
    require_positive("transmit power", pt)
    require_positive("range", range_m)

    if frequency is not None and wavelength is not None:
        raise ValueError("pass --freq or --wavelength, not both")
    if frequency is None and wavelength is None:
        raise ValueError("requires --freq or --wavelength")
    if frequency is not None:
        require_positive("frequency", frequency)
        lam = wavelength_from_frequency(frequency)
        freq = frequency
    else:
        assert wavelength is not None
        require_positive("wavelength", wavelength)
        lam = wavelength
        freq = frequency_from_wavelength(lam)

    gt_val, gt_source, dt_used, eta_t_used = resolve_gain(
        gt,
        dt,
        eta_t,
        lam,
        gain_flag="--gt",
        diameter_flag="--dt",
        efficiency_flag="--eta-t",
    )
    gr_val, gr_source, dr_used, eta_r_used = resolve_gain(
        gr,
        dr,
        eta_r,
        lam,
        gain_flag="--gr",
        diameter_flag="--dr",
        efficiency_flag="--eta-r",
    )

    lfs = free_space_path_loss(range_m, lam)
    pr = friis_received_power(pt, gt_val, gr_val, lam, range_m)
    eirp_w = eirp(pt, gt_val)

    if bandwidth is not None and ts is None:
        raise ValueError("--bandwidth requires --ts")
    if bitrate is not None and ts is None:
        raise ValueError("--bitrate requires --ts")
    if eb_n0_req is not None and (ts is None or bitrate is None):
        raise ValueError("--ebn0-req requires --ts and --bitrate")

    n0 = cn0 = cn = pn = eb_n0 = margin = None
    if ts is not None:
        require_positive("system noise temperature", ts)
        n0 = noise_spectral_density(ts)
        cn0 = carrier_to_noise_density(pr, ts)
        if bandwidth is not None:
            require_positive("bandwidth", bandwidth)
            pn = thermal_noise_power(ts, bandwidth)
            cn = carrier_to_noise_ratio(pr, ts, bandwidth)
        if bitrate is not None:
            require_positive("bit rate", bitrate)
            eb_n0 = eb_n0_from_cn0(cn0, bitrate)
            if eb_n0_req is not None:
                require_positive("required Eb/N0", eb_n0_req)
                margin = link_margin_eb_n0(eb_n0, eb_n0_req)

    return Solution(
        pt=pt,
        gt=gt_val,
        gr=gr_val,
        range_m=range_m,
        frequency=freq,
        wavelength=lam,
        lfs=lfs,
        eirp=eirp_w,
        pr=pr,
        gt_source=gt_source,
        gr_source=gr_source,
        dt=dt_used,
        dr=dr_used,
        eta_t=eta_t_used,
        eta_r=eta_r_used,
        ts=ts,
        bandwidth=bandwidth,
        n0=n0,
        cn0=cn0,
        cn=cn,
        pn=pn,
        bitrate=bitrate,
        eb_n0=eb_n0,
        eb_n0_req=eb_n0_req,
        margin=margin,
    )


def linspace(start: float, stop: float, count: int) -> list[float]:
    if count == 1:
        return [start]
    step = (stop - start) / (count - 1)
    return [start + step * i for i in range(count)]


def ensure_matplotlib():
    try:
        import matplotlib

        if "matplotlib.pyplot" not in sys.modules:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ValueError("matplotlib is required to plot received power versus range") from exc
    return plt


def write_plot(result: Solution, out_path: Path) -> None:
    plt = ensure_matplotlib()
    r_max = PLOT_END_FACTOR * result.range_m
    r_min = max(result.range_m * 0.05, result.wavelength)
    ranges = linspace(r_min, r_max, N_CURVE)
    powers = [
        friis_received_power(result.pt, result.gt, result.gr, result.wavelength, r)
        for r in ranges
    ]
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.0))
    ax.loglog(ranges, powers, color="#1a5276", linewidth=1.8, label=r"$P_r\propto 1/R^{2}$")
    ax.plot(
        result.range_m,
        result.pr,
        "s",
        color="#1a5276",
        markersize=7,
        zorder=5,
        label="operating point",
    )
    ax.set_xlabel("range (m)")
    ax.set_ylabel("received power (W)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, which="both", alpha=0.35)
    ax.legend(loc="best", fontsize=8)
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
    print_kv("c_m_s", C_LIGHT)
    print_kv("k_J_K", K_BOLTZMANN)
    print_kv("Pt_W", result.pt)
    print_kv("Gt", result.gt)
    print_kv("Gt_dBi", to_db(result.gt))
    print_kv("Gt_source", result.gt_source)
    if result.dt is not None:
        print_kv("Dt_m", result.dt)
        print_kv("eta_t", result.eta_t)
    print_kv("Gr", result.gr)
    print_kv("Gr_dBi", to_db(result.gr))
    print_kv("Gr_source", result.gr_source)
    if result.dr is not None:
        print_kv("Dr_m", result.dr)
        print_kv("eta_r", result.eta_r)
    print_kv("R_m", result.range_m)
    print_kv("f_Hz", result.frequency)
    print_kv("lam_m", result.wavelength)
    print_kv("EIRP_W", result.eirp)
    print_kv("EIRP_dBW", to_db(result.eirp))
    print_kv("Lfs", result.lfs)
    print_kv("Lfs_dB", to_db(result.lfs))
    print_kv("Pr_W", result.pr)
    print_kv("Pr_dBW", to_db(result.pr))
    if result.ts is not None:
        print_kv("Ts_K", result.ts)
        print_kv("N0_W_Hz", result.n0)
        print_kv("N0_dBW_Hz", to_db(float(result.n0)))
        print_kv("CN0_Hz", result.cn0)
        print_kv("CN0_dBHz", to_db(float(result.cn0)))
    if result.bandwidth is not None:
        print_kv("B_Hz", result.bandwidth)
        print_kv("Pn_W", result.pn)
        print_kv("CN", result.cn)
        print_kv("CN_dB", to_db(float(result.cn)))
    if result.bitrate is not None:
        print_kv("Rb_bit_s", result.bitrate)
        print_kv("EbN0", result.eb_n0)
        print_kv("EbN0_dB", to_db(float(result.eb_n0)))
    if result.eb_n0_req is not None:
        print_kv("EbN0_req", result.eb_n0_req)
        print_kv("EbN0_req_dB", to_db(float(result.eb_n0_req)))
        print_kv("margin", result.margin)
        print_kv("margin_dB", to_db(float(result.margin)))
    print_kv(
        "warning",
        "vacuum free space only; no atmosphere, rain, pointing, or "
        "polarization loss; no modulation model beyond the supplied Eb/N0",
    )
    if graph is not None:
        print_kv("graph", str(graph))


def fail(message: str) -> int:
    print(f"CHECK FAIL: {message}", file=sys.stderr)
    return 1


def run_check() -> int:
    if not close(wavelength_from_frequency(C_LIGHT), 1.0):
        return fail("wavelength at f=c is not 1 m")
    if not close(frequency_from_wavelength(1.0), C_LIGHT):
        return fail("frequency at lam=1 is not c")
    if not close(free_space_path_loss(1.0, 4.0 * math.pi), 1.0):
        return fail("unit free-space path loss is not 1")
    if not close(free_space_path_loss_db(1.0, 4.0 * math.pi), 0.0):
        return fail("unit free-space path loss dB is not 0")
    if not close(antenna_gain_circular_aperture(2.0, math.pi, 0.5), 2.0):
        return fail("circular aperture gain half-efficiency case")
    ae = 0.5 * math.pi
    if not close(
        antenna_gain_from_effective_aperture(ae, math.pi),
        antenna_gain_circular_aperture(2.0, math.pi, 0.5),
    ):
        return fail("effective aperture and circular gain disagree")
    if not close(friis_received_power(16.0, 1.0, 1.0, 4.0 * math.pi, 1.0), 16.0):
        return fail("unit Friis received power")
    if not close(carrier_to_noise_density(K_BOLTZMANN * 100.0, 100.0), 1.0):
        return fail("unit C/N0")
    if not close(eb_n0_from_cn0(1.0e7, 1.0e6), 10.0):
        return fail("Eb/N0 from C/N0")
    if not close(link_margin_eb_n0(20.0, 10.0), 2.0):
        return fail("link margin")

    class _Capture:
        def __init__(self) -> None:
            self.parts: list[str] = []

        def write(self, text: str) -> None:
            self.parts.append(text)

        def flush(self) -> None:
            return None

    def capture(argv: list[str]) -> tuple[int, str, str]:
        out = _Capture()
        err = _Capture()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = main(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return code, "".join(out.parts), "".join(err.parts)

    with tempfile.TemporaryDirectory() as tmp:
        out = str(Path(tmp) / "link.png")
        code, text, err = capture(
            [
                "--pt",
                "10",
                "--gt",
                "100",
                "--gr",
                "1000",
                "--freq",
                "2.2e9",
                "--range",
                "1000e3",
                "--ts",
                "290",
                "--bandwidth",
                "1e6",
                "--bitrate",
                "1e6",
                "--ebn0-req",
                "10",
                "--out",
                out,
            ]
        )
        if code != 0:
            return fail(f"main returned {code}: {err}")
        data = Path(out).read_bytes()
        if not data.startswith(b"\x89PNG"):
            return fail("run did not write a PNG")
        for key in (
            "title: Free-space link budget",
            "Lfs:",
            "Pr_W:",
            "CN0_Hz:",
            "EbN0:",
            "margin:",
            "graph:",
            "warning:",
        ):
            if key not in text:
                return fail(f"stdout missing {key}")

        code, text, err = capture(
            [
                "--pt",
                "1",
                "--dt",
                "1",
                "--eta-t",
                "0.55",
                "--dr",
                "2",
                "--eta-r",
                "0.6",
                "--wavelength",
                "0.03",
                "--range",
                "50000",
            ]
        )
        if code != 0:
            return fail(f"diameter path returned {code}: {err}")
        if "Gt_source: diameter" not in text or "Gr_source: diameter" not in text:
            return fail("diameter path did not mark gain sources")
        if "CN0_Hz:" in text:
            return fail("noise outputs appeared without --ts")
        if "graph:" in text:
            return fail("plot appeared without --out")

        code, _text, err = capture(
            ["--pt", "1", "--gt", "1", "--gr", "1", "--freq", "1e9", "--wavelength", "0.3", "--range", "1"]
        )
        if code != 2 or "not both" not in err:
            return fail("freq and wavelength together were accepted")

        code, _text, err = capture(
            ["--pt", "1", "--gt", "1", "--dt", "1", "--eta-t", "0.5", "--gr", "1", "--freq", "1e9", "--range", "1"]
        )
        if code != 2 or "not both" not in err:
            return fail("gt and diameter together were accepted")

        code, _text, err = capture(
            ["--pt", "1", "--gt", "1", "--gr", "1", "--freq", "1e9", "--range", "1", "--bandwidth", "1e6"]
        )
        if code != 2 or "--ts" not in err:
            return fail("bandwidth without ts was accepted")

        code, _text, err = capture(["--pt", "1", "--gt", "1", "--gr", "1", "--range", "1"])
        if code != 2 or "requires --freq or --wavelength" not in err:
            return fail("missing RF path was not rejected")

    print("check: pass")
    print_kv("Lfs_unit", 1.0)
    print_kv("Pr_W_unit", 16.0)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Vacuum free-space Friis link budget: path loss, received power, "
            "and optional C/N0, Eb/N0, and link margin."
        )
    )
    parser.add_argument("--pt", type=float, default=None, help="transmit power Pt [W]")
    parser.add_argument("--gt", type=float, default=None, help="transmit antenna gain (linear)")
    parser.add_argument("--gr", type=float, default=None, help="receive antenna gain (linear)")
    parser.add_argument("--dt", type=float, default=None, help="transmit antenna diameter [m]")
    parser.add_argument("--dr", type=float, default=None, help="receive antenna diameter [m]")
    parser.add_argument(
        "--eta-t",
        type=float,
        default=None,
        help="transmit aperture efficiency (0, 1]",
    )
    parser.add_argument(
        "--eta-r",
        type=float,
        default=None,
        help="receive aperture efficiency (0, 1]",
    )
    parser.add_argument("--freq", type=float, default=None, help="carrier frequency [Hz]")
    parser.add_argument("--wavelength", type=float, default=None, help="wavelength [m]")
    parser.add_argument("--range", type=float, default=None, help="slant range R [m]")
    parser.add_argument("--ts", type=float, default=None, help="system noise temperature Ts [K]")
    parser.add_argument("--bandwidth", type=float, default=None, help="noise bandwidth B [Hz]")
    parser.add_argument("--bitrate", type=float, default=None, help="information bit rate Rb [bit/s]")
    parser.add_argument(
        "--ebn0-req",
        type=float,
        default=None,
        help="required Eb/N0 (linear power ratio)",
    )
    parser.add_argument("--out", type=Path, default=None, help="PNG path for Pr vs range")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()

    if args.pt is None or args.range is None:
        print("error: requires --pt and --range", file=sys.stderr)
        return 2

    try:
        result = evaluate(
            args.pt,
            args.range,
            args.freq,
            args.wavelength,
            args.gt,
            args.gr,
            args.dt,
            args.dr,
            args.eta_t,
            args.eta_r,
            args.ts,
            args.bandwidth,
            args.bitrate,
            args.ebn0_req,
        )
        graph: Path | None = None
        if args.out is not None:
            graph = Path(args.out).resolve()
            write_plot(result, graph)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    emit(result, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
