---
name: CTRL - ProportionalNavigation
description: >-
  Run the planar true proportional navigation program and report its printed
  results and optional PNG. Use when the user wants the instantaneous true-PN
  commanded acceleration a_c = N' V_c λ̇ from navigation constant, closing
  speed, and LOS rate, or a simple planar constant-speed intercept engagement
  with PN steering. Guidance kinematics live under CTRL with SecondOrderResponse;
  do not invent a GNC family. Do not redraw the plot or recompute the numbers
  by hand.
---

# CTRL - ProportionalNavigation

Use this skill for planar true proportional navigation: an instantaneous commanded acceleration and/or a simple constant-speed planar intercept. Run the program once; quote its stdout and include the PNG when `graph:` is printed. Do not redraw the plot or recompute the numbers by hand. Second-order plant metrics stay in `CTRL - SecondOrderResponse`; this skill does not replace that.

True PN commanded acceleration is `true_pn_commanded_acceleration`:

\[
a_c = N'\, V_c\, \dot{\lambda}
\]

Closing speed is `closing_speed`, \(V_c = -\dot{R}\) (positive when range decreases). The line-of-sight (LOS) angle \(\lambda\) is measured from the interceptor to the target in the engagement plane, \(\mathbf{R}=\mathbf{r}_t-\mathbf{r}_m\), \(\lambda=\mathrm{atan2}(R_y,R_x)\). LOS rate is `los_rate`:

\[
\dot{\lambda} = \frac{R_x V_y - R_y V_x}{R^{2}}
\]

with relative velocity \(\mathbf{V}=\mathbf{v}_t-\mathbf{v}_m\). The true-PN acceleration of the interceptor is normal to the LOS in the direction of increasing \(\lambda\).

**Mode 1 (instantaneous):** \(N'\), \(V_c\), and \(\dot{\lambda}\) → \(a_c\) only.

**Mode 2 (engagement):** \(N'\), initial range and LOS angle, and interceptor/target planar velocity state (speed+heading or velocity components); integrate constant-speed planar kinematics with PN steering; optional constant target lateral acceleration (default 0); report time to intercept or miss distance. Speeds are held fixed by dropping the along-track part of each commanded acceleration (no gravity, atmosphere, seeker noise, filters, or autopilot lag).

## When to run

1. Use this skill when the user wants true-PN commanded acceleration, closing-speed/LOS-rate definitions, or a planar PN intercept / miss estimate.
2. Convert inputs to SI before the call (m/s, rad/s, m, rad). State the converted units in the reply. Do not invent \(N'\), rates, or geometry.
3. Pass exactly one mode: Mode 1 (`--vc` with `--los-rate`) or Mode 2 (`--range` with `--los-angle` and a velocity path). Do not mix the modes.
4. For Mode 2, pass exactly one velocity API: `--vm --hm --vt --ht`, or `--vmx --vmy --vtx --vty`. Do not mix them.
5. Pass `--at-lat`, `--dt`, `--t-max`, or `--hit-radius` only when the user gave them or when documenting the program defaults. Safe defaults are target lateral accel 0, `dt=0.01` s, `t_max=300` s, hit radius 1 m.
6. Pass `--out` only for Mode 2 when the user wants the engagement-plane PNG. Do not invent a plot path when they did not ask for a figure.
7. Do not use this skill for 3D PN, seeker noise, filters, gravity, atmosphere, autopilot lag, pursuit, or APN. Do not use it for second-order step-response metrics (`CTRL - SecondOrderResponse`).

## Flags

Run:

```text
python "skills/CTRL - ProportionalNavigation/proportional_navigation.py" --n-prime <N'> (--vc <m/s> --los-rate <rad/s> | --range <m> --los-angle <rad> (--vm <m/s> --hm <rad> --vt <m/s> --ht <rad> | --vmx <m/s> --vmy <m/s> --vtx <m/s> --vty <m/s>) [--at-lat <m/s^2>] [--dt <s>] [--t-max <s>] [--hit-radius <m>] [--out <png>])
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--n-prime` | Effective navigation ratio \(N'\) | dimensionless, \(> 0\) | Required |
| `--vc` | Closing speed \(V_c\) | m/s | Mode 1 with `--los-rate` |
| `--los-rate` | LOS rate \(\dot{\lambda}\) | rad/s | Mode 1 with `--vc` |
| `--range` | Initial range \(R_0\) | m, \(> 0\) | Mode 2 with `--los-angle` |
| `--los-angle` | Initial LOS angle \(\lambda_0\) | rad | Mode 2 with `--range` |
| `--vm` | Interceptor speed | m/s, \(> 0\) | Mode 2 speed/heading API |
| `--hm` | Interceptor heading from \(+x\) | rad | Mode 2 speed/heading API |
| `--vt` | Target speed | m/s, \(> 0\) | Mode 2 speed/heading API |
| `--ht` | Target heading from \(+x\) | rad | Mode 2 speed/heading API |
| `--vmx`, `--vmy` | Interceptor velocity components | m/s | Mode 2 component API |
| `--vtx`, `--vty` | Target velocity components | m/s | Mode 2 component API |
| `--at-lat` | Constant target lateral acceleration | m/s² | Optional; default 0 |
| `--dt` | Integrator step | s, \(> 0\) | Optional; default 0.01 |
| `--t-max` | Maximum engagement time | s, \(> 0\) | Optional; default 300 |
| `--hit-radius` | Intercept range threshold | m, \(> 0\) | Optional; default 1 |
| `--out` | PNG path | — | Optional; Mode 2 only |

Angles in degrees use \(\mathrm{rad}=\mathrm{deg}\cdot\pi/180\). Speeds in km/s use `1 km/s = 1000 m/s`. Range in km uses `1 km = 1000 m`.

When `--out` is passed in Mode 2, the program writes one PNG. The plot title is `Proportional navigation`. The curves are engagement-plane paths of interceptor and target. `graph:` is the PNG.

## What to report

1. Quote the printed `key: value` stdout. Do not recompute the numbers.
2. Include the PNG at `graph:` only when that key is printed.
3. Report `mode`, `N_prime`, `a_c_m_s2`, and `a_c_units`.
4. For Mode 1, report `Vc_m_s` and `lambda_dot_rad_s`.
5. For Mode 2, report `t_intercept_s` or `miss_distance_m`, `range_final_m`, `outcome`, and the printed `assumptions` line.
6. If \(N'\) or the chosen mode’s required inputs are missing, say so. Do not fill them in.
