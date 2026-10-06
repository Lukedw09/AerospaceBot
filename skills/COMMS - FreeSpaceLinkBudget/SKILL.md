---
name: COMMS - FreeSpaceLinkBudget
description: >-
  Run the vacuum free-space Friis link-budget program and report its printed
  results and optional PNG. Use when the user wants free-space path loss,
  received power, EIRP, C/N0 or C/N from system noise temperature and bandwidth,
  Eb/N0 and link margin from a required Eb/N0 and bit rate, or received power
  versus range for a space link with no atmosphere. Do not redraw the plot or
  recompute the numbers by hand.
---

# COMMS - FreeSpaceLinkBudget

Use this skill for a vacuum free-space radio link budget. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand. The bit rate may be `R_bps` from `COMMS - PassDataVolume`.

Free-space path loss is `free_space_path_loss`:

\[
L_{\mathrm{fs}} = \left(\frac{4\pi R}{\lambda}\right)^{2}
\]

Received power is `friis_received_power`:

\[
P_r = P_t G_t G_r\left(\frac{\lambda}{4\pi R}\right)^{2}
\]

Wavelength is `wavelength_from_frequency`, \(\lambda=c/f\), with \(c=299792458\,\mathrm{m/s}\). Antenna gains may be given as linear ratios, or as diameters with aperture efficiencies through `antenna_gain_circular_aperture`, \(G=\eta(\pi D/\lambda)^{2}\). EIRP is `eirp`, \(P_t G_t\).

Optional `--ts` prints `carrier_to_noise_density`, \(C/N_0=P_r/(k T_s)\), with \(k=1.380649\times 10^{-23}\,\mathrm{J/K}\). With `--bandwidth` it also prints `carrier_to_noise_ratio`, \(C/N=P_r/(k T_s B)\). With `--bitrate` it prints `eb_n0_from_cn0`, \(E_b/N_0=(C/N_0)/R_b\). With `--ebn0-req` it prints `link_margin_eb_n0`, \(M=(E_b/N_0)/(E_b/N_0)_{\mathrm{req}}\).

This skill does not model atmosphere, rain, pointing, polarization mismatch, or modulation beyond the supplied \(E_b/N_0\) requirement. The printed `warning` states that limit.

## When to run

1. Use this skill when the user wants free-space path loss, Friis received power, EIRP, \(C/N_0\), \(C/N\), \(E_b/N_0\), link margin, or a received-power-versus-range figure for a vacuum space link.
2. Convert inputs to SI before the call (W, m, Hz, K, bit/s). Antenna gains are linear power ratios, not dBi. Convert dBi with \(G=10^{G_{\mathrm{dBi}}/10}\). Convert a required \(E_b/N_0\) in dB the same way. State the converted units in the reply. Do not invent power, gains, diameters, frequency, range, \(T_s\), bandwidth, bit rate, or a required \(E_b/N_0\).
3. Pass `--pt` and `--range`. Pass exactly one of `--freq` or `--wavelength`.
4. For each antenna, pass either linear gain (`--gt` / `--gr`) or diameter with aperture efficiency (`--dt` with `--eta-t`, `--dr` with `--eta-r`). Do not mix gain and diameter on the same side.
5. Pass `--ts` only when the user gave system noise temperature. Pass `--bandwidth` only with `--ts`. Pass `--bitrate` only with `--ts`. Pass `--ebn0-req` only with `--ts` and `--bitrate`.
6. Pass `--out` only when the user wants the PNG of received power versus range.
7. Do not use this skill for atmospheric attenuation, rain fade, ionospheric scintillation, or detailed BER curves.

## Flags

Run:

```text
python "skills/COMMS - FreeSpaceLinkBudget/free_space_link_budget.py" --pt <W> --range <m> (--freq <Hz> | --wavelength <m>) (--gt <G> | --dt <m> --eta-t <eta>) (--gr <G> | --dr <m> --eta-r <eta>) [--ts <K>] [--bandwidth <Hz>] [--bitrate <bit/s>] [--ebn0-req <ratio>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--pt` | Transmit power \(P_t\) | W, \(> 0\) | Required |
| `--range` | Slant range \(R\) | m, \(> 0\) | Required |
| `--freq` | Carrier frequency \(f\) | Hz, \(> 0\) | One of `--freq` or `--wavelength` |
| `--wavelength` | Wavelength \(\lambda\) | m, \(> 0\) | One of `--freq` or `--wavelength` |
| `--gt` | Transmit antenna gain (linear) | dimensionless, \(> 0\) | Or `--dt` with `--eta-t` |
| `--gr` | Receive antenna gain (linear) | dimensionless, \(> 0\) | Or `--dr` with `--eta-r` |
| `--dt` | Transmit antenna diameter | m, \(> 0\) | With `--eta-t` |
| `--dr` | Receive antenna diameter | m, \(> 0\) | With `--eta-r` |
| `--eta-t` | Transmit aperture efficiency | dimensionless, \(0 < \eta \le 1\) | With `--dt` |
| `--eta-r` | Receive aperture efficiency | dimensionless, \(0 < \eta \le 1\) | With `--dr` |
| `--ts` | System noise temperature \(T_s\) | K, \(> 0\) | Optional |
| `--bandwidth` | Noise bandwidth \(B\) | Hz, \(> 0\) | Optional with `--ts` |
| `--bitrate` | Information bit rate \(R_b\) | bit/s, \(> 0\) | Optional with `--ts` |
| `--ebn0-req` | Required \(E_b/N_0\) (linear) | dimensionless, \(> 0\) | Optional with `--ts` and `--bitrate` |
| `--out` | PNG path | — | Optional. Omit unless the user wants the figure. |

A bare length is metres. Kilometres use `1 km = 1000 m`. Frequency in GHz uses `1 GHz = 1e9 Hz`. Power in dBW uses \(P=10^{P_{\mathrm{dBW}}/10}\) watts. Gains in dBi use \(G=10^{G_{\mathrm{dBi}}/10}\).

When `--out` is passed, the program writes one PNG. The plot title is `Free-space link budget`. The curve is received power versus range at the fixed power, gains, and wavelength. The square is the operating point. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `Pt_W`, `Gt`, `Gt_dBi`, `Gt_source`, `Gr`, `Gr_dBi`, `Gr_source`, `R_m`, `f_Hz`, `lam_m`, `EIRP_W`, `Lfs`, `Lfs_dB`, `Pr_W`, and `Pr_dBW`.
4. Report `Dt_m` / `eta_t` and `Dr_m` / `eta_r` when diameters were used. `gain` means a linear gain was supplied. `diameter` means gain came from `antenna_gain_circular_aperture`.
5. Report `Ts_K`, `N0_W_Hz`, `CN0_Hz`, and `CN0_dBHz` when `--ts` was used. Report `B_Hz`, `Pn_W`, `CN`, and `CN_dB` when bandwidth was used.
6. Report `Rb_bit_s`, `EbN0`, and `EbN0_dB` when bit rate was used. Report `EbN0_req`, `margin`, and `margin_dB` when a requirement was used.
7. Include the printed `warning` about vacuum free space and omitted atmosphere or modulation detail.
8. If transmit power, range, an RF path, or either antenna path is missing, say so. Do not fill them in.
