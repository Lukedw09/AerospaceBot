---
name: ROCKET - LossStack
description: >-
  Run the loss-stack program and report its printed results. Use when the
  user wants actual thrust, specific impulse, thrust coefficient, c-star, or
  mass flow after applying named efficiencies to an ideal thrust coefficient
  and an ideal c-star. Do not recompute the numbers by hand.
---

# ROCKET - LossStack

Use this skill for delivered motor performance from ideal thrust coefficient, ideal \(c^{*}\), and named efficiencies. Run the program once and quote its stdout. Do not recompute the numbers by hand.

Ideal \(C_F\) and ideal \(c^{*}\) are inputs. This program does not compute either one. Combustion efficiency and \(c^{*}\) efficiency multiply ideal \(c^{*}\). Nozzle efficiency and divergence efficiency multiply ideal \(C_F\). Any other name the user supplies is multiplied on the side they name (`@cstar` or `@cf`). Each omitted canonical efficiency is printed as 1. Do not enter one physical loss under two names: the factors multiply.

\[
c^{*}_{\mathrm{actual}} = c^{*}_{\mathrm{ideal}} \prod \eta_{c^{*}}
\]

\[
C_{F,\mathrm{actual}} = C_{F,\mathrm{ideal}} \prod \eta_{C_F}
\]

\[
c = c^{*} C_F, \quad I_s = c / g_0, \quad g_0 = 9.80665\,\mathrm{m/s}^2
\]

When throat area and chamber pressure are both given, the program prints the theoretical thrust and mass flow with every efficiency equal to 1, and the delivered thrust and mass flow after the loss stack:

\[
F_{\mathrm{ideal}} = C_{F,\mathrm{ideal}} p_1 A_t, \quad \dot{m}_{\mathrm{ideal}} = p_1 A_t / c^{*}_{\mathrm{ideal}}
\]

\[
F = C_{F,\mathrm{actual}} p_1 A_t, \quad \dot{m} = p_1 A_t / c^{*}_{\mathrm{actual}}
\]

At fixed \(p_1\) and \(A_t\), thrust follows \(C_F\), and mass flow follows \(c^{*}\).

## When to run

1. Use this skill when the user wants actual thrust, specific impulse, thrust coefficient, \(c^{*}\), or mass flow from ideal values and efficiencies or losses.
2. Convert all inputs to SI before the call (Pa, m², m/s). State the converted units in the reply. An efficiency is a fraction: 98 percent is `0.98`. Do not invent values the user did not give.
3. Ideal \(C_F\) and ideal \(c^{*}\) are required. If the user already quoted them from another program in this conversation, pass those printed numbers. If either is missing, say so and stop. Do not invent one, and do not run another rocket program unless the user asked for that result.
4. Pass `--throat` and `--pc` only when the user gave both. If only one is known, say thrust and mass flow need both, and run without those flags.
5. Pass `--eta` only for efficiencies the user named. Do not pass a canonical efficiency just to set it to 1. The program lists every omitted canonical efficiency as 1.

## Flags

Run:

```text
python "skills/ROCKET - LossStack/loss_stack.py" --cf <CF> --cstar <m/s> [--throat <m^2> --pc <Pa>] [--eta name=value] [--eta name=value@cstar|@cf]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--cf` | Ideal thrust coefficient \(C_F\) | dimensionless | Required |
| `--cstar` | Ideal characteristic velocity \(c^{*}\) | m/s | Required |
| `--throat` | Throat area \(A_t\) | m² | Optional; required with `--pc` for thrust and mass flow |
| `--pc` | Chamber pressure \(p_1\) | Pa | Optional; required with `--throat` for thrust and mass flow |
| `--eta` | One named efficiency. Repeat for each name the user supplied. | dimensionless, \(> 0\) | Optional |

A bare number for `--pc` is pascals. Use `pc_Pa = pc_bar * 1e5`, `1 atm = 101325 Pa`, and `1 psi = 6894.757293168361 Pa`. A \(c^{*}\) in feet per second uses `1 ft/s = 0.3048 m/s`. Throat area in square inches uses `1 in² = 0.00064516 m²`.

`--eta` forms:

| Form | Meaning |
| --- | --- |
| `combustion=0.98` | Combustion efficiency. Multiplies ideal \(c^{*}\). |
| `cstar=0.99` | \(c^{*}\) efficiency. Multiplies ideal \(c^{*}\). Also `c*` and `c-star`. |
| `nozzle=0.97` | Nozzle efficiency, the \(C_F\) efficiency. Multiplies ideal \(C_F\). Also `cf-efficiency`. |
| `divergence=0.983` | Divergence efficiency \(\lambda\). Multiplies ideal \(C_F\). Also `lambda` and `thrust-efficiency`. |
| `name=value@cstar` | Any other name. Multiplies ideal \(c^{*}\). |
| `name=value@cf` | Any other name. Multiplies ideal \(C_F\). |

A known name does not need `@cstar` or `@cf`. An unknown name does. If the user names a loss and does not say whether it scales \(c^{*}\) or \(C_F\), ask. Do not guess the side.

Canonical names, always printed: `combustion`, `cstar`, `nozzle`, `divergence`.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Report ideal \(C_F\), ideal \(c^{*}\) in m/s, and \(g_0\).
3. Report every `eta_` value and its `eta_*_applies` side. State that a canonical efficiency the user did not give was printed as 1.
4. Report `eta_product_cstar`, `eta_product_CF`, actual \(c^{*}\) in m/s, actual \(C_F\), effective exhaust velocity \(c\) in m/s, and specific impulse \(I_s\) in s.
5. Report chamber pressure and throat area only when they are printed. Report `thrust_ideal_N` and `mdot_ideal_kg_s` as the theoretical thrust and mass flow with no losses, and `thrust_N` and `mdot_kg_s` as the delivered values. Omit all four when they are not printed.
6. If ideal \(C_F\), ideal \(c^{*}\), or the side of an unnamed efficiency is missing, say so. Do not fill in a performance number or an efficiency.
