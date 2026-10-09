---
name: ROCKET - StageAscentDesignLab
description: >-
  Bake an interactive 2D stage-ascent page. Use only when the user explicitly
  asks for this lab, the interactive HTML designer, or a live view of stage
  masses, burnout altitude and speed, and peak dynamic pressure. Do not run
  it just because a stage or a trajectory is being sized.
---

# ROCKET - StageAscentDesignLab

Run this program only when the user explicitly asks for this lab. That means they name `ROCKET - StageAscentDesignLab`, or they clearly ask for the interactive HTML page or a live view that ties stage masses, burnout altitude and speed, and peak dynamic pressure together. Do not run it because a stage-split, mass-budget, LEO delta-v, ascent, or max-q conversation is underway. Do not run it from another rocket skill unless they explicitly said yes to that offer.

The program writes a PNG of the seed altitude and dynamic pressure and a self-contained HTML page. The page recomputes in the browser when inputs change. Quote the program stdout for the seed point only. Give `viewer:` as a markdown link. Pass `--open` only when they ask to open the page. Do not recompute the numbers by hand. The page has an Astraeus box with the settled MultiStageAscent inputs as `key: value` lines. If they paste that box, use those values for `ROCKET - MultiStageAscent`. This lab does not replace that CLI chain.

The loop sizes propellant from the LEO design delta-v, optionally replaces inert from a mass budget, flies the ascent, and writes the gravity and drag losses back until they settle. Steering loss stays 0. Rotation assist, circularization, and margin stay the values on the page. The delta-v budget uses \(R_0 = 6.3742\times 10^6\,\mathrm{m}\). The ascent uses \(R_\mathrm{Earth} = 6.356766\times 10^6\,\mathrm{m}\). Say both. A mass budget can make the flown vacuum delta-v differ from the design delta-v.

## When to run

1. Run only after an explicit request for this lab or its interactive page. If they did not ask for it, do not run it.
2. Convert supplied inputs to SI before describing them (m, m/s, kg, s, rad). State the converted units in the reply.
3. Say how many stages are active, whether size is payload or liftoff mass, and which split mode is active (`equal_dv`, `equal_mr`, or `max_payload`).
4. Say whether the loop settled, and quote design delta-v, gravity loss, drag loss, burnout altitude, burnout speed, and peak dynamic pressure.
5. Say steering loss is 0. Say the LEO radius and the ascent radius. If a stage replaces inert, say the flown vacuum delta-v can differ from the design delta-v.
6. State every default the user did not supply. Unless they set them, say the seed is two stages, equal delta-v, payload \(500\,\mathrm{kg}\), altitude \(200\,\mathrm{km}\), specific impulses \(280\,\mathrm{s}\) and \(320\,\mathrm{s}\), structural coefficients \(0.08\) and \(0.12\), burn times \(80\,\mathrm{s}\) and \(220\,\mathrm{s}\), kick \(0.05\,\mathrm{rad}\), \(C_D = 0.4\), and area \(2\,\mathrm{m}^2\). A third stage at \(300\,\mathrm{s}\), coefficient \(0.1\), and burn time \(250\,\mathrm{s}\) is unused until the count is 3. Mass budget and fairing drop are off until turned on. Burn times are shorter than a slow boost so this kick still climbs; say that when you state them.
7. Pass `--open` only when they ask to open the HTML file.
8. Do not offer to run this lab again in the same conversation after they have it open, unless they ask.

## Flags

Run:

```text
python "skills/ROCKET - StageAscentDesignLab/stage_ascent_lab.py" [--stages 1|2|3] [--mode equal_dv|equal_mr|max_payload] [--size payload|glow] [--path kick|gamma] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--stages` | Stage count, 1 to 3 | — | Optional |
| `--mode` | `equal_dv`, `equal_mr`, or `max_payload` | — | Optional |
| `--size` | `payload` or `glow` | — | Optional |
| `--path` | `kick` or `gamma` | — | Optional |
| `--out` | PNG path; HTML uses the same stem | — | Optional |
| `--open` | Open the HTML page | — | Optional |

`max_payload` needs `--size glow`.

## What to report

1. Quote the printed `key: value` stdout, including `graph:` and `viewer:`.
2. Say whether `settled` is yes, and quote `passes`.
3. Quote `dv_design_m_s`, `gravity_loss_m_s`, `drag_loss_m_s`, `Z_bo_m`, `V_bo_m_s`, and `q_max_Pa`.
4. Quote each `stage_N_mp_kg` and `stage_N_inert_kg`.
5. Name both Earth radii.
6. State every assumption the user did not supply.
7. Include the PNG. Give `viewer:` as a markdown link.
8. Tell them the page is where to change stage count, payload or liftoff mass, the split, altitude, the kick or held angle, drag, an optional fairing drop, and each stage, and that burnout and peak dynamic pressure update with the loop.
