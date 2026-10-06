#!/usr/bin/env python3
"""1976 mass density, pressure, and species number densities above 86 km.

Temperature reuses the four kinetic-temperature segments. Species number
densities are integrated from the 86 km boundary values in NASA TR R-459.
"""

from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

# 1976 constants (formulas.md, Atmosphere, and TR R-459).
G0 = 9.80665
R0 = 6.356766e6
RSTAR = 8.31432e3
KB = 1.380622e-23
NA = 6.022169e26
M0 = 28.9644
T_REF = 273.15

Z_MIN = 86000.0
Z_MAX = 1000000.0
Z7 = 86000.0
Z8 = 91000.0
Z9 = 110000.0
Z_MIX = 100000.0
Z10 = 120000.0
Z_H_MIN = 150000.0
Z_H_REF = 500000.0

T7 = 186.8673
T9 = 240.0
T10 = 360.0
TINF = 1000.0
LK9 = 12.0 / 1000.0
TC = 263.1905
A_ELLIPSE = -76.3232
A_SEMI = -19.9429 * 1000.0
LAMBDA = LK9 / (TINF - T10)

# Molar masses, kg/kmol. TR R-459 table 2.
M_N2 = 28.0134
M_O = 15.9994
M_O2 = 31.9988
M_AR = 39.948
M_HE = 4.0026
M_H = 1.00794

# Number densities at 86 km, 1/m^3. TR R-459.
N7_N2 = 1.129794e20
N7_O = 8.6e16
N7_O2 = 3.030898e19
N7_AR = 1.351400e18
N7_HE = 7.5817e14

# Atomic hydrogen anchor. TR R-459.
N_H_500 = 8.0e10
FLUX_H = 7.2e11
ALPHA_H = -0.25
A_H = 3.305e21
B_H = 0.5

# Molecular diffusion through N2. a in m^-1 s^-1, b dimensionless, alpha dimensionless.
# Order used below 150 km: O, O2, Ar, He.
DIFF = {
    "O": (0.0, 6.986e20, 0.750),
    "O2": (0.0, 4.863e20, 0.750),
    "Ar": (0.0, 4.487e20, 0.870),
    "He": (-0.40, 1.700e21, 0.691),
}

# Flux-term coefficients. Lengths in km. TR R-459 table 6 as printed in the
# companion computational discussion of the same model (NASA SP-398 table 5),
# which resolves superscripts that do not survive in the R-459 scan.
# v/(D+K) = -Q*(Z-U)^2*exp(-W*(Z-U)^3) + q*(u-Z)^2*exp(-w*(u-Z)^3), per km.
FLUX = {
    "O": {
        "q": -3.416248e-3,
        "Q": -5.809644e-4,
        "u": 97.0,
        "U": 56.90311,
        "w": 5.008765e-4,
        "W": 2.706246e-5,
        "q_below_km": 97.0,
    },
    "O2": {
        "q": 0.0,
        "Q": 1.366312e-4,
        "u": 0.0,
        "U": 86.0,
        "w": 0.0,
        "W": 8.333333e-5,
        "q_below_km": 0.0,
    },
    "Ar": {
        "q": 0.0,
        "Q": 9.434079e-5,
        "u": 0.0,
        "U": 86.0,
        "w": 0.0,
        "W": 8.333333e-5,
        "q_below_km": 0.0,
    },
    "He": {
        "q": 0.0,
        "Q": -2.457369e-4,
        "u": 0.0,
        "U": 86.0,
        "w": 0.0,
        "W": 6.666667e-4,
        "q_below_km": 0.0,
    },
}

K7 = 120.0
DZ = 50.0
PLOT_TITLE = "Density above 86 km"
CHECK_TOL = 1e-9
# Abbreviated TR R-459 table 13 densities, four significant figures.
TABLE_RHO = {
    86000.0: 6.958e-6,
    91000.0: 2.860e-6,
    110000.0: 9.708e-8,
    120000.0: 2.222e-8,
    150000.0: 2.076e-9,
    200000.0: 2.541e-10,
    300000.0: 1.916e-11,
    400000.0: 2.802e-12,
    500000.0: 5.215e-13,
    600000.0: 1.137e-13,
    700000.0: 3.069e-14,
    800000.0: 1.136e-14,
    900000.0: 5.759e-15,
    1000000.0: 3.561e-15,
}

SKILL_DIR = Path(__file__).resolve().parent
ASSUMPTIONS = (
    "1976 U.S. Standard Atmosphere above 86 km geometric; mean solar activity "
    "with exospheric temperature 1000 K; kinetic temperature from the four "
    "segments kinetic_temperature_linear, mesosphere_ellipse_temperature, and "
    "exospheric_temperature; species N2, O, O2, Ar, and He integrated from the "
    "86 km number densities in NASA TR R-459; atomic hydrogen from 150 km with "
    "the 500 km anchor and escape flux of that report; mass density is the "
    "species sum n_i*M_i/N_A; not NRLMSISE-00 and not Earth-GRAM; altitudes at "
    "or below 86 km belong to ATMOS - Standard1976"
)

_GRID: dict[str, list[float]] | None = None


def print_kv(key: str, value: object) -> None:
    if isinstance(value, float):
        text = f"{value:.8g}"
    else:
        text = str(value)
    print(f"{key}: {text}")


def require_altitude(value: float, flag: str) -> float:
    if not math.isfinite(value) or value <= Z_MIN or value > Z_MAX:
        raise ValueError(
            f"{flag} must be greater than 86000 m and at most 1000000 m geometric; "
            "86 km and below belong to ATMOS - Standard1976"
        )
    return value


def geometric_gravity(z_m: float) -> float:
    """geometric_gravity: g = g0*(r0/(r0+Z))**2."""
    return G0 * (R0 / (R0 + z_m)) ** 2


def segment_name(z_m: float) -> str:
    if z_m >= Z10:
        return "exosphere"
    if z_m >= Z9:
        return "thermosphere_linear"
    if z_m >= Z8:
        return "mesosphere_ellipse"
    return "mesopause"


def kinetic_temperature(z_m: float) -> float:
    if z_m < Z8:
        return T7
    if z_m < Z9:
        ratio = (z_m - Z8) / A_SEMI
        inside = 1.0 - ratio * ratio
        if inside < 0.0:
            inside = 0.0
        return TC + A_ELLIPSE * math.sqrt(inside)
    if z_m < Z10:
        return T9 + LK9 * (z_m - Z9)
    xi = (z_m - Z10) * (R0 + Z10) / (R0 + z_m)
    return TINF - (TINF - T10) * math.exp(-LAMBDA * xi)


def temperature_gradient(z_m: float) -> float:
    if z_m < Z8 or z_m >= Z_MAX:
        return 0.0
    if z_m < Z9:
        ratio = (z_m - Z8) / A_SEMI
        inside = 1.0 - ratio * ratio
        if inside <= 0.0:
            return 0.0
        return A_ELLIPSE * (-ratio) / (math.sqrt(inside) * A_SEMI)
    if z_m < Z10:
        return LK9
    xi = (z_m - Z10) * (R0 + Z10) / (R0 + z_m)
    dxi = (R0 + Z10) ** 2 / (R0 + z_m) ** 2
    return (TINF - T10) * math.exp(-LAMBDA * xi) * LAMBDA * dxi


def eddy_diffusion(z_m: float) -> float:
    """eddy_diffusion. K is 120 m^2/s below 95 km and 0 at and above 115 km."""
    z_km = z_m / 1000.0
    if z_km < 95.0:
        return K7
    if z_km >= 115.0:
        return 0.0
    gap = 400.0 - (z_km - 95.0) ** 2
    if gap <= 1.0e-9:
        return 0.0
    return K7 * math.exp(1.0 - 400.0 / gap)


def molecular_diffusion(a_coeff: float, b_coeff: float, temp: float, number: float) -> float:
    """molecular_diffusion_coefficient: D = (a/N)*(T/273.15)**b."""
    if number <= 0.0 or temp <= 0.0:
        raise ValueError("molecular diffusion needs positive temperature and number density")
    return (a_coeff / number) * (temp / T_REF) ** b_coeff


def flux_per_metre(species: str, z_m: float) -> float:
    coeff = FLUX[species]
    z_km = z_m / 1000.0
    delta = z_km - coeff["U"]
    # Q already carries the sign. TR R-459 equation (37) as clarified by the
    # same coefficients in NASA SP-398 equation (16): the Q term is not
    # prefixed by an extra minus.
    term = coeff["Q"] * delta * delta * math.exp(-coeff["W"] * delta ** 3)
    if coeff["q"] != 0.0 and z_km < coeff["q_below_km"]:
        gap = coeff["u"] - z_km
        term += coeff["q"] * gap * gap * math.exp(-coeff["w"] * gap ** 3)
    return term / 1000.0


def background_molar_mass(z_m: float, species_for_mean: dict[str, float] | None) -> float:
    if z_m <= Z_MIX:
        return M0
    if species_for_mean is None:
        return M_N2
    total_n = species_for_mean["N2"] + species_for_mean["O"] + species_for_mean["O2"]
    if total_n <= 0.0:
        return M_N2
    return (
        species_for_mean["N2"] * M_N2
        + species_for_mean["O"] * M_O
        + species_for_mean["O2"] * M_O2
    ) / total_n


def weight_integrand(molar: float, z_m: float, temp: float) -> float:
    return molar * geometric_gravity(z_m) / (RSTAR * temp)


def _grid() -> dict[str, list[float]]:
    global _GRID
    if _GRID is not None:
        return _GRID
    n_steps = int(round((Z_MAX - Z_MIN) / DZ))
    z = [Z_MIN + i * DZ for i in range(n_steps + 1)]
    z[-1] = Z_MAX
    n = len(z)
    temp = [kinetic_temperature(zi) for zi in z]
    ln_n2 = [0.0] * n
    ln_o = [0.0] * n
    ln_o2 = [0.0] * n
    ln_ar = [0.0] * n
    ln_he = [0.0] * n
    n2 = N7_N2
    no = N7_O
    no2 = N7_O2
    nar = N7_AR
    nhe = N7_HE
    minors = ("O", "O2", "Ar", "He")
    logs = {"O": ln_o, "O2": ln_o2, "Ar": ln_ar, "He": ln_he}
    values = {"O": no, "O2": no2, "Ar": nar, "He": nhe}
    bases = {"O": N7_O, "O2": N7_O2, "Ar": N7_AR, "He": N7_HE}
    for i in range(1, n):
        z0 = z[i - 1]
        z1 = z[i]
        step = z1 - z0
        t0 = temp[i - 1]
        t1 = temp[i]
        # N2: static, M = M0 through 100 km and M(N2) above.
        m0 = M0 if z0 <= Z_MIX else M_N2
        m1 = M0 if z1 <= Z_MIX else M_N2
        integ = 0.5 * (weight_integrand(m0, z0, t0) + weight_integrand(m1, z1, t1)) * step
        ln_n2[i] = ln_n2[i - 1] - math.log(t1 / t0) - integ
        n2 = N7_N2 * math.exp(ln_n2[i])
        # Minor species in the published order. O and O2 diffuse through N2.
        # Ar and He diffuse through N2+O+O2.
        current = {"N2": n2, "O": values["O"], "O2": values["O2"], "Ar": values["Ar"], "He": values["He"]}
        for name in minors:
            alpha, a_coeff, b_coeff = DIFF[name]
            if name in ("O", "O2"):
                n_back_0 = N7_N2 * math.exp(ln_n2[i - 1])
                n_back_1 = n2
                molar0 = M0 if z0 <= Z_MIX else M_N2
                molar1 = M0 if z1 <= Z_MIX else M_N2
            else:
                prev = {
                    "N2": N7_N2 * math.exp(ln_n2[i - 1]),
                    "O": bases["O"] * math.exp(ln_o[i - 1]),
                    "O2": bases["O2"] * math.exp(ln_o2[i - 1]),
                }
                n_back_0 = prev["N2"] + prev["O"] + prev["O2"]
                n_back_1 = current["N2"] + current["O"] + current["O2"]
                molar0 = background_molar_mass(z0, prev)
                molar1 = background_molar_mass(z1, current)
            d0 = molecular_diffusion(a_coeff, b_coeff, t0, n_back_0)
            d1 = molecular_diffusion(a_coeff, b_coeff, t1, n_back_1)
            k0 = eddy_diffusion(z0)
            k1 = eddy_diffusion(z1)

            def extra(d_i: float, k_i: float, molar: float, zz: float, tt: float) -> float:
                mix = d_i + k_i
                if mix <= 0.0:
                    raise ValueError("diffusion denominator is not positive")
                thermal = 0.0
                if alpha != 0.0:
                    thermal = (alpha * d_i / (mix * tt)) * temperature_gradient(zz)
                heavy = (d_i / mix) * weight_integrand(DIFF_M[name], zz, tt)
                light = (k_i / mix) * weight_integrand(molar, zz, tt)
                return thermal + heavy + light + flux_per_metre(name, zz)

            f_bar = 0.5 * (
                extra(d0, k0, molar0, z0, t0) + extra(d1, k1, molar1, z1, t1)
            )
            logs[name][i] = logs[name][i - 1] - math.log(t1 / t0) - f_bar * step
            values[name] = bases[name] * math.exp(logs[name][i])
            current[name] = values[name]
    n_h = [0.0] * n
    # One pass each way from the 500 km hydrogen anchor. Queries then interpolate.
    i_ref = min(range(n), key=lambda i: abs(z[i] - Z_H_REF))
    y_ref = N_H_500 * temp[i_ref] ** (1.0 + ALPHA_H)
    n_h[i_ref] = y_ref / temp[i_ref] ** (1.0 + ALPHA_H)

    def hydrogen_step(i_from: int, i_to: int, y_in: float) -> float:
        z0 = z[i_from]
        z1 = z[i_to]
        step = z1 - z0
        t0 = temp[i_from]
        t1 = temp[i_to]

        def rhs(zz: float, tt: float, yy: float, idx: int) -> float:
            others_n = (
                N7_N2 * math.exp(ln_n2[idx])
                + N7_O * math.exp(ln_o[idx])
                + N7_O2 * math.exp(ln_o2[idx])
                + N7_AR * math.exp(ln_ar[idx])
                + N7_HE * math.exp(ln_he[idx])
            )
            diff = molecular_diffusion(A_H, B_H, tt, max(others_n, 1.0))
            return -yy * weight_integrand(M_H, zz, tt) - (FLUX_H / diff) * tt ** (1.0 + ALPHA_H)

        k1 = rhs(z0, t0, y_in, i_from)
        y_mid = y_in + 0.5 * step * k1
        k2 = rhs(0.5 * (z0 + z1), 0.5 * (t0 + t1), y_mid, i_to)
        k3 = rhs(0.5 * (z0 + z1), 0.5 * (t0 + t1), y_in + 0.5 * step * k2, i_to)
        k4 = rhs(z1, t1, y_in + step * k3, i_to)
        return y_in + (step / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    y_run = y_ref
    for i in range(i_ref + 1, n):
        y_run = hydrogen_step(i - 1, i, y_run)
        if y_run < 0.0:
            y_run = 0.0
        if z[i] >= Z_H_MIN:
            n_h[i] = y_run / temp[i] ** (1.0 + ALPHA_H)
    y_run = y_ref
    for i in range(i_ref - 1, -1, -1):
        y_run = hydrogen_step(i + 1, i, y_run)
        if y_run < 0.0:
            y_run = 0.0
        if z[i] >= Z_H_MIN:
            n_h[i] = y_run / temp[i] ** (1.0 + ALPHA_H)
    _GRID = {
        "z": z,
        "T": temp,
        "ln_N2": ln_n2,
        "ln_O": ln_o,
        "ln_O2": ln_o2,
        "ln_Ar": ln_ar,
        "ln_He": ln_he,
        "n_H": n_h,
    }
    return _GRID


DIFF_M = {"O": M_O, "O2": M_O2, "Ar": M_AR, "He": M_HE}


def _interp_log(z_m: float, z_grid: list[float], ln_grid: list[float], base: float) -> float:
    if z_m <= z_grid[0]:
        return base
    if z_m >= z_grid[-1]:
        return base * math.exp(ln_grid[-1])
    frac = (z_m - Z_MIN) / DZ
    i0 = int(frac)
    if i0 >= len(z_grid) - 1:
        i0 = len(z_grid) - 2
    span = z_grid[i0 + 1] - z_grid[i0]
    w = 0.0 if span == 0.0 else (z_m - z_grid[i0]) / span
    ln_v = ln_grid[i0] * (1.0 - w) + ln_grid[i0 + 1] * w
    return base * math.exp(ln_v)


def five_species(z_m: float) -> dict[str, float]:
    grid = _grid()
    return {
        "N2": _interp_log(z_m, grid["z"], grid["ln_N2"], N7_N2),
        "O": _interp_log(z_m, grid["z"], grid["ln_O"], N7_O),
        "O2": _interp_log(z_m, grid["z"], grid["ln_O2"], N7_O2),
        "Ar": _interp_log(z_m, grid["z"], grid["ln_Ar"], N7_AR),
        "He": _interp_log(z_m, grid["z"], grid["ln_He"], N7_HE),
    }


def hydrogen_number_density(z_m: float) -> float:
    """Atomic hydrogen from the cached 500 km integration. Zero below 150 km."""
    if z_m < Z_H_MIN:
        return 0.0
    grid = _grid()
    z_grid = grid["z"]
    n_h = grid["n_H"]
    if z_m >= z_grid[-1]:
        return n_h[-1]
    frac = (z_m - Z_MIN) / DZ
    i0 = int(frac)
    if i0 >= len(z_grid) - 1:
        i0 = len(z_grid) - 2
    span = z_grid[i0 + 1] - z_grid[i0]
    w = 0.0 if span == 0.0 else (z_m - z_grid[i0]) / span
    return n_h[i0] * (1.0 - w) + n_h[i0 + 1] * w


def state_at(z_m: float) -> dict[str, float | str]:
    species = five_species(z_m)
    n_h = hydrogen_number_density(z_m)
    species["H"] = n_h
    temp = kinetic_temperature(z_m)
    number = species["N2"] + species["O"] + species["O2"] + species["Ar"] + species["He"] + species["H"]
    rho = (
        species["N2"] * M_N2
        + species["O"] * M_O
        + species["O2"] * M_O2
        + species["Ar"] * M_AR
        + species["He"] * M_HE
        + species["H"] * M_H
    ) / NA
    pressure = number * KB * temp
    molar = rho * NA / number if number > 0.0 else M0
    return {
        "Z": z_m,
        "T": temp,
        "segment": segment_name(z_m),
        "g": geometric_gravity(z_m),
        "N": number,
        "rho": rho,
        "p": pressure,
        "M": molar,
        "n_N2": species["N2"],
        "n_O": species["O"],
        "n_O2": species["O2"],
        "n_Ar": species["Ar"],
        "n_He": species["He"],
        "n_H": species["H"],
    }


def emit(state: dict[str, float | str], graph: Path | None) -> None:
    print_kv("assumptions", ASSUMPTIONS)
    print_kv("model", "1976 U.S. Standard Atmosphere density above 86 km")
    print_kv("Z_m", state["Z"])
    print_kv("T_K", state["T"])
    print_kv("segment", state["segment"])
    print_kv("g_m_s2", state["g"])
    print_kv("N_m3", state["N"])
    print_kv("rho_kg_m3", state["rho"])
    print_kv("p_Pa", state["p"])
    print_kv("M_kg_kmol", state["M"])
    print_kv("n_N2_m3", state["n_N2"])
    print_kv("n_O_m3", state["n_O"])
    print_kv("n_O2_m3", state["n_O2"])
    print_kv("n_Ar_m3", state["n_Ar"])
    print_kv("n_He_m3", state["n_He"])
    print_kv("n_H_m3", state["n_H"])
    if graph is not None:
        print_kv("graph", str(graph))


def write_plot(state: dict[str, float | str], out_path: Path) -> None:
    import matplotlib.pyplot as plt

    z_km = []
    rho = []
    z_plot = Z_MIN + 1000.0
    while z_plot <= Z_MAX:
        z_km.append(z_plot / 1000.0)
        rho.append(float(state_at(z_plot)["rho"]))
        z_plot += 5000.0
    fig, ax = plt.subplots(figsize=(6.5, 7.0))
    ax.semilogx(rho, z_km, color="C0", label=r"$\rho(Z)$")
    ax.plot(float(state["rho"]), float(state["Z"]) / 1000.0, "s", color="C1", label="operating point")
    ax.set_xlabel(r"mass density (kg/m$^3$)")
    ax.set_ylabel("geometric altitude (km)")
    ax.set_title(PLOT_TITLE)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def run_check() -> int:
    def fail(msg: str) -> int:
        print(f"check: fail: {msg}", file=sys.stderr)
        return 1

    base = state_at(86000.0 + 1.0e-6)
    if abs(float(base["T"]) - T7) > 1.0e-6:
        return fail("temperature at 86 km")
    point = state_at(200000.0)
    if abs(float(point["T"]) - 854.559) > 0.05:
        return fail(f"200 km temperature {point['T']}")
    if abs(float(point["g"]) - 9.2175) > 0.002:
        return fail(f"200 km gravity {point['g']}")
    if abs(float(point["n_O"]) - 4.050e15) / 4.050e15 > 1.0e-3:
        return fail(f"200 km atomic oxygen {point['n_O']}")
    if abs(float(point["p"]) - 8.4732e-5) / 8.4732e-5 > 1.0e-3:
        return fail(f"200 km pressure {point['p']}")
    hydrogen = state_at(500000.0)
    if abs(float(hydrogen["n_H"]) - 8.0e10) / 8.0e10 > 1.0e-3:
        return fail(f"500 km hydrogen {hydrogen['n_H']}")
    worst = 0.0
    worst_z = 0.0
    for z_m, expected in TABLE_RHO.items():
        # The table value at 86.0 km is the lower boundary. The skill domain
        # starts just above 86 km; the first tabulated interior points are the check.
        if z_m <= Z_MIN:
            got = float(state_at(Z_MIN + 1.0)["rho"])
        else:
            got = float(state_at(z_m)["rho"])
        rel = abs(got - expected) / expected
        if rel > worst:
            worst = rel
            worst_z = z_m
        # TR R-459 table 13 is printed to four figures. The integrator stays inside 0.1%.
        if rel > 1.0e-3:
            return fail(f"density at {z_m:.0f} m is {got:.6e}, table {expected:.6e}, rel {rel:.3e}")
    if point["segment"] != "exosphere":
        return fail("200 km segment")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "density.png"
        if main(["--alt", "200000", "--out", str(path)]) != 0:
            return fail("plot run failed")
        if not path.is_file() or path.stat().st_size < 1000:
            return fail("plot missing")
    err = sys.stderr
    sys.stderr = _Capture()
    try:
        code = main([])
    finally:
        sys.stderr = err
    if code != 2:
        return fail("missing altitude was accepted")
    print("check: pass")
    print_kv("worst_rel", worst)
    print_kv("worst_Z_m", worst_z)
    print_kv("rho_200km", point["rho"])
    return 0


class _Capture:
    def write(self, _text: str) -> None:
        return

    def flush(self) -> None:
        return


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="1976 mass density at one geometric altitude from just above 86 km through 1000 km."
    )
    parser.add_argument("--alt", type=float, default=None, help="geometric altitude [m]")
    parser.add_argument("--out", type=Path, default=None, help="optional PNG of density versus altitude")
    parser.add_argument("--check", action="store_true", help="run built-in consistency checks")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.check:
        return run_check()
    if args.alt is None:
        print("error: requires --alt", file=sys.stderr)
        return 2
    try:
        z_m = require_altitude(args.alt, "--alt")
        state = state_at(z_m)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    graph: Path | None = None
    if args.out is not None:
        try:
            write_plot(state, args.out)
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        graph = args.out
    emit(state, graph)
    return 0


if __name__ == "__main__":
    sys.exit(main())
