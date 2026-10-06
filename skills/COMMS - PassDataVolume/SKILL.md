---
name: COMMS - PassDataVolume
description: >-
  Run the pass data-volume program and report its printed results and optional
  PNG. Use when the user wants the bit rate a stored volume requires over a
  pass, or the volume a bit rate delivers, with a coding overhead. Hand the
  required rate to COMMS - FreeSpaceLinkBudget. Do not recompute the numbers
  by hand. No atmosphere, rain, or modulation curve.
---

# COMMS - PassDataVolume

Use this skill for the bits moved in one pass and the information rate that volume requires. Either direction uses the same relation. Run the program once; quote its stdout and include the PNG when `graph:` is printed.

Required rate is `required_pass_bit_rate`, \(R = N_{\mathrm{bits}}\,k / t\). Volume is `pass_data_volume`, \(N_{\mathrm{bits}} = R t / k\). Overhead \(k\) defaults to 1.

The printed `R_bps` is the bit rate `COMMS - FreeSpaceLinkBudget` already takes for \(E_b/N_0\). No atmosphere, rain, or modulation curve.

## When to run

1. Use this skill when the user has a stored volume and a pass duration, or a rate and a pass duration.
2. Convert bits, bit rate, and duration to bits, bit/s, and seconds. Do not invent them.
3. Pass `--duration` and exactly one of `--bits` or `--rate`.
4. Pass `--overhead` only when the user stated a coding factor at or above 1.
5. Pass `--out` only when the user wants required rate versus pass duration. That plot needs a stored volume, so pass `--bits` for the figure.
6. Hand `R_bps` to `COMMS - FreeSpaceLinkBudget` as the bit rate.

## Flags

```text
python "skills/COMMS - PassDataVolume/pass_data_volume.py" (--bits <bit> | --rate <bit/s>) --duration <s> [--overhead <1>] [--out <png>]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--bits` | Stored information bits | bit, \(> 0\) | Exactly one of `--bits` or `--rate` |
| `--rate` | Information bit rate | bit/s, \(> 0\) | Exactly one of `--bits` or `--rate` |
| `--duration` | Pass duration | s, \(> 0\) | Required |
| `--overhead` | Coding overhead | \(\ge 1\) | Optional. Default 1 |
| `--out` | PNG path | — | Optional |

The plot title is `Pass data volume`. The curve is required rate in Mbit/s versus pass duration.

## What to report

1. Quote the printed `key: value` stdout.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `R_bps` and `bits`.
4. If the volume or the rate, or the pass duration, is missing, say so. Do not fill it in.
