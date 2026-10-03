---
name: ROCKET - PayloadtoDeltaV
description: >-
  Run the payload-to-delta-v program and report its printed results and PNG.
  Use when the user wants useful payload for a given ideal delta-v, or the
  ideal delta-v a rocket produces for a given payload, for one or more stages.
  Do not redraw the curve or recompute the numbers by hand.
---

# ROCKET - PayloadtoDeltaV

Use this skill for useful payload from ideal delta-v, or ideal delta-v from useful payload. Run the program once; quote its stdout and include its PNG when `graph:` is printed. Do not redraw the curve or recompute the numbers by hand.

Assumptions (also printed by the program): gravity-free, drag-free ideal delta-v at constant effective exhaust velocity (`delta_v_vacuum`). \(c = I_s g_0\). Stage 1 burns first. Each modeled stage above stage 1 is inside the payload of the stages below it, and that stage's inert mass is dropped after it burns. The useful payload is only the mass above the last modeled stage. An upper stage the user does not break out is part of that useful payload, not an extra `--stage`. Residual propellant is part of inert mass. One ambient pressure per stage is held constant over that burn. Specific impulse at that pressure follows `specific_impulse_exit`: it is linear in ambient pressure between the vacuum and sea-level values. \(g_0 = 9.80665\,\mathrm{m/s}^2\). Sea-level pressure is \(101325\,\mathrm{Pa}\).

This program does not apply gravity loss or drag loss, and it does not integrate a trajectory.

## When to run

1. Use this skill when the user asks for payload mass from delta-v, delta-v from payload mass, or a payload-versus-delta-v curve for a staged rocket.
2. Convert all inputs to SI before the call (kg, s, Pa, m/s). State the converted units in the reply. Do not invent values the user did not give.
3. Pass `--stages` equal to the number of stages the user broke out. Pass one `--stage` per stage, bottom stage first (stage 1 burns first).
4. Specific impulse is in seconds. Label sea level as `isp-sl` and vacuum as `isp-vac`. If the user gives both and an ambient pressure, pass `pa`. If the user gives only sea-level impulse, do not also invent a vacuum value or an altitude. If the user gives only vacuum impulse, do not invent a sea-level value.
5. If the user gives a delta-v and no payload, pass `--dv` and do not pass `--payload`. If the user gives a payload and no delta-v, pass `--payload` and do not pass `--dv`. If the user gives neither, omit both so the program sweeps delta-v. If the user gives both, pass both.

## Flags

Run:

```text
python "skills/ROCKET - PayloadtoDeltaV/payload_to_deltav.py" --stages <N> --stage mp=<kg>,inert=<kg>[,isp-sl=<s>][,isp-vac=<s>][,pa=<Pa>] [--stage ...] [--dv <m/s>] [--payload <kg>]
```

Pass **only** flags the user supplied (after SI conversion). Repeat `--stage` once per modeled stage. Do **not** copy one stage's mass or impulse onto another stage.

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--stages` | Number of modeled stages | integer, \(\ge 1\) | Required |
| `--stage` | One stage, bottom stage first. Keys: `mp`, `inert`, and `isp-sl` and/or `isp-vac`, and `pa` when both impulses are given | kg, kg, s, s, Pa | Required once per stage |
| `--dv` | Ideal delta-v. The program solves useful payload. | m/s | Optional |
| `--payload` | Useful payload above the last modeled stage. The program solves ideal delta-v. | kg | Optional |
| `--dv-min`, `--dv-max` | Delta-v sweep limits. Used only when `--dv` and `--payload` are both omitted. | m/s | Optional |
| `--out` | PNG path for the sweep | — | Optional |

`--stage` keys:

| Key | Meaning | Unit |
| --- | --- | --- |
| `mp` | Usable propellant mass of that stage | kg |
| `inert` | Inert mass of that stage, including residual propellant. Dropped after the stage burns. | kg |
| `isp-sl` | Sea-level specific impulse | s |
| `isp-vac` | Vacuum specific impulse | s |
| `pa` | Ambient pressure held during that burn | Pa |

A bare number for `pa` is pascals. Use `pa_Pa = pa_bar * 1e5`, `1 atm = 101325 Pa`, and `1 psi = 6894.757293168361 Pa`. Mass in pounds-mass uses `1 lbm = 0.45359237 kg`. Delta-v in feet per second uses `1 ft/s = 0.3048 m/s`. Specific impulse is already in seconds; do not scale it. If the user gives effective exhaust velocity \(c\) in m/s, pass \(I_s = c / g_0\) with \(g_0 = 9.80665\,\mathrm{m/s}^2\) and say so. Do not put \(c\) in `isp-sl` or `isp-vac`.

Impulse and ambient pressure:

- `isp-vac` only, `pa` omitted: vacuum, \(p_3 = 0\).
- `isp-sl` only, `pa` omitted: sea level, \(p_3 = 101325\,\mathrm{Pa}\).
- Both `isp-sl` and `isp-vac`: pass the user's `pa`. The program will not pick an ambient. \(I_s(p_3) = I_{s,\mathrm{vac}} - (I_{s,\mathrm{vac}} - I_{s,\mathrm{sl}})\,p_3/p_0\).
- Do not move a single impulse to a different ambient. The program rejects that, because the pressure term needs both impulses.

If the user gives no sweep range, the program prints `assumed_range`. The low end is the ideal delta-v at a payload equal to the sum of modeled propellant and inert mass. The high end is the ideal delta-v at zero useful payload. Repeat `assumed_range` in the reply when it is present.

A point request (`--dv`, `--payload`, or both) does not write a PNG. A sweep writes one PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG only when `graph:` is printed. The plot title is `Payload mass versus delta-v`.
3. Always report `stages`, \(g_0\), and each stage's operating \(I_s\), `isp_condition`, \(c\), and `pa_Pa` with `pa_source`.
4. `payload_kg` is the useful mass above the last modeled stage. `stage_k_payload_kg` is the mass that stage lifts, including every modeled stage above it.
5. When `dv_m_s` is printed, report it with `dv_source`. `input` is the user's delta-v. `solved` is the ideal delta-v the rocket produces with the given payload.
6. When `payload_kg` is printed, report `payload_source` the same way. On `mode: both`, also report `dv_at_payload_m_s` and `payload_at_dv_kg`.
7. Report `dv_zero_payload_m_s` when it is printed. That is the ideal delta-v at zero useful payload.
8. Report `MR` as final mass over initial mass for that stage, \(m_f/m_0\), which is less than 1.
9. Repeat `assumed_range` when it is present. Report `stacked_mass_kg` when it is printed.
10. If `warning` is printed, include it. A negative payload means the requested delta-v is above the ideal delta-v at zero payload.
11. If stage count, a stage mass, specific impulse, or a required ambient pressure is missing, say so. Do not fill in a mass, an impulse, or a pressure.
