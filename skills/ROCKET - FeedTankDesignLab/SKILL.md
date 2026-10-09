---
name: ROCKET - FeedTankDesignLab
description: >-
  Bake an interactive 2D liquid-engine feed and tank page. Use only when
  the user explicitly asks for this lab, the interactive HTML designer,
  or a live view of oxidizer and fuel tanks with a pressure-fed or
  electric-pump switch. Do not run it just because an engine is being sized.
---

# ROCKET - FeedTankDesignLab

Run this program only when the user explicitly asks for this lab. That means they name `ROCKET - FeedTankDesignLab`, or they clearly ask for the interactive HTML page, the live feed-and-tank designer, or a design view of both propellant branches. Do not run it because an engine-sizing conversation is underway. Do not run it from another rocket skill unless they explicitly said yes to that offer.

The program writes a PNG of the opening tanks and a self-contained HTML page. The page recomputes both branches in the browser when inputs change. Quote the program stdout for the seed point only. Give `viewer:` as a markdown link. Pass `--open` only when they ask to open the page. Do not recompute the numbers by hand. The page has an Astraeus box with the chosen inputs as `key: value` lines. If they paste that box, use those values. This lab does not replace that CLI chain.

Oxidizer and fuel are always side by side. The architecture is pressure-fed or electric-pump-fed. An electric pump is not a turbine, gas-generator, expander, or staged-combustion cycle. Shared inputs are chamber pressure, one named line drop, height, burn time, residuals, allowable stress, and material density. Each branch has its own injector drop, discharge coefficient, orifice count, density, and tank.

## When to run

1. Run only after an explicit request for this lab or its interactive page. If they did not ask for it, do not run it.
2. Convert supplied inputs to SI before describing them (Pa, kg/s, kg/m³, m, s). State the converted units in the reply.
3. Say which architecture is active and which flow mode is active. Flow is either a total mass flow plus mixture ratio \(r=\dot{m}_o/\dot{m}_f\), or separate oxidizer and fuel flows.
4. Say that an electric pump is not a turbine cycle. In electric-pump mode, blowdown is hidden, pump rise is supply pressure minus the user inlet pressure, and tank MEOP is a separate user pressure.
5. In pressure-fed mode, say the shell and the membrane stress use each tank's initial pressure \(p_0\), and say whether each tank is flagged. A tank is flagged when burnout ullage pressure \(p_2\) is below that branch's supply pressure.
6. Say the membrane stress is the thin-wall check at the tank design pressure, and that chamber pressure is only the injector-end pressure. Design pressure is the design factor (default 1) times \(p_0\) when pressure-fed, or times the user tank MEOP when electric-pump-fed.
7. State every default the user did not supply. Allowable stress and material density are assumptions, not a named alloy. Unless they set them, say allowable stress is \(900\,\mathrm{MPa}\) and material density is \(4430\,\mathrm{kg/m^3}\). Also state unused defaults: chamber pressure \(2\,\mathrm{MPa}\), line drop \(100\,\mathrm{kPa}\), height \(1\,\mathrm{m}\), burn time \(20\,\mathrm{s}\), residuals \(0.02\), mixture ratio \(2.3\), total flow \(2\,\mathrm{kg/s}\), oxidizer injector drop \(200\,\mathrm{kPa}\), fuel injector drop \(150\,\mathrm{kPa}\), \(C_d=0.75\), 20 orifices, densities \(1141\) and \(810\,\mathrm{kg/m^3}\), \(p_0=4\,\mathrm{MPa}\), ullage \(0.1\,\mathrm{m^3}\), blowdown exponent \(1\), weld efficiency \(1\), design factor \(1\), and a sphere. If they switch to an electric pump without setting the pump inputs, say inlet pressure \(300\,\mathrm{kPa}\), pump efficiency \(0.65\), motor efficiency \(0.9\), and tank MEOP \(500\,\mathrm{kPa}\) are assumptions.
8. Pass `--open` only when they ask to open the HTML file.
9. Do not offer to run this lab again in the same conversation after they have it open, unless they ask.

## Flags

Run:

```text
python "skills/ROCKET - FeedTankDesignLab/feed_tank_lab.py" [--architecture pressure|electric] [--flow ratio|branches] [--shape sphere|cylinder] [--out <png>] [--open]
```

| Flag | Meaning | Unit | Required? |
| --- | --- | --- | --- |
| `--architecture` | `pressure` or `electric` | — | Optional |
| `--flow` | `ratio` (total flow and mixture ratio) or `branches` | — | Optional |
| `--shape` | `sphere` or `cylinder` | — | Optional |
| `--out` | PNG path; HTML uses the same stem | — | Optional |
| `--open` | Open the HTML page | — | Optional |

## What to report

1. Quote the printed `key: value` stdout, including `graph:` and `viewer:`.
2. Name the active architecture and the active flow mode.
3. Say an electric pump is not a turbine cycle.
4. In pressure-fed mode, say the shell and the stress use \(p_0\), and quote `flagged_ox` and `flagged_fuel`.
5. Say the membrane stress is the thin-wall check at the tank design pressure. Chamber pressure is only the injector-end pressure.
6. State every assumption the user did not supply, including allowable stress and material density as assumptions rather than a named alloy.
7. Include the PNG. Give `viewer:` as a markdown link.
8. Tell them the page is where to change architecture, flow mode, chamber pressure, line drop, injector drop, discharge coefficient, ullage, tank pressure, allowable stress, and the other inputs, and that both branches update immediately.
