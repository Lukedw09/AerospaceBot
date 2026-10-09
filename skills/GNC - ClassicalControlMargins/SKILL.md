---
name: GNC - ClassicalControlMargins
description: >-
  Run the classical-control program and report its printed Bode margins and
  PNG. Use when the user wants gain crossover, phase margin, phase crossover,
  or gain margin of a polynomial loop transfer, with an optional series PID.
  Do not redraw the plot or recompute the numbers by hand.
---

# GNC - ClassicalControlMargins

Use this skill for the Bode gain and phase margins of a single-input loop transfer. Run the program once; quote its stdout and include its PNG. Do not redraw the plot or recompute the numbers by hand.

`bode_magnitude_db`, `bode_phase_deg`, `phase_margin_deg`, and `gain_margin_db` evaluate the complex value. `series_pid_real` and `series_pid_imag` are the optional series compensator. Step-response metrics stay on `GNC - SecondOrderResponse`. Root-locus geometry is not this program.

## When to run

1. Use this skill when the user wants the gain crossover, phase margin, phase crossover, or gain margin of \(L(s)\).
2. Pass `--num` and `--den` as real polynomial coefficients, highest power first.
3. Pass `--kp`, `--ki`, or `--kd` only when the user names a series PID. Omitted gains are zero, and \(L(s)=C(s)G(s)\) with \(C=K_d s+K_p+K_i/s\).
4. If the user does not name a compensator, omit the PID flags so \(L(s)=G(s)\).
5. Do not invent a coefficient or a gain.

## Flags

Run:

```text
python "skills/GNC - ClassicalControlMargins/classical_control_margins.py" --num <b_m> <b_0> --den <a_n> <a_0> [--kp <Kp>] [--ki <Ki>] [--kd <Kd>] [--out <png>]
```

Pass **only** flags the user supplied.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--num` | Numerator coefficients, highest power first | mixed | Required |
| `--den` | Denominator coefficients, highest power first | mixed | Required |
| `--kp` | Series proportional gain | mixed | Optional |
| `--ki` | Series integral gain | mixed | Optional |
| `--kd` | Series derivative gain | mixed | Optional |
| `--out` | PNG path | — | Optional |

Every successful run writes one PNG. The plot title is `Classical control margins`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:`. The upper curve is magnitude in dB and the lower curve is phase in degrees. A dashed line marks the gain crossover. A dotted line marks the phase crossover when one exists.
3. Report `wc` and `phase_margin_deg`. `wc: none` means the magnitude does not cross 0 dB in the sweep.
4. Report `wpc` and `gain_margin_db`. `gain_margin_db: inf` means the phase does not cross \(-180^\circ\). `wpc: 0` is the low-frequency limit. A negative gain margin means the magnitude there is already above \(0\,\mathrm{dB}\). `gain_margin_db: -inf` means that low-frequency magnitude is infinite.
5. Report `stable` and `dc_gain`. `stable` is the closed-loop characteristic polynomial.
6. Report `compensator` as `plant` or `series_pid`.
7. If a polynomial is missing, say so. Do not fill it in.
