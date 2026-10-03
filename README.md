# AerospaceBot

Cursor agent skills for aerospace engineering: checked formulas and small physics programs the bot can run and report, instead of reinventing equations or redrawing plots by hand.

## Skills

| Skill | Purpose |
| --- | --- |
| [`aero-formulas`](skills/aero-formulas) | Select and use verified aerospace formulas (compressible flow, atmosphere, rocket propulsion, aerodynamics, structures). Only formulas listed in `checks/check.md` are allowed. |
| [`ROCKET - Area-Mach Graph`](skills/ROCKET%20-%20Area-Mach%20Graph) | Run `area_mach.py` for an isentropic nozzle area-Mach curve, exit Mach from area ratio, exit pressure, ideal thrust, and expansion state. |
| [`ROCKET - PerformanceParameters`](skills/ROCKET%20-%20PerformanceParameters) | Run `performance.py` for frozen-CEA c*, temperature, gamma, ideal Cf, specific impulse, and density impulse. Do not call CEA at reply time. |
| [`ROCKET - ThroatSizingandMassFlow`](skills/ROCKET%20-%20ThroatSizingandMassFlow) | Run `throat_sizing.py` for circular-throat area and diameter from thrust, thrust coefficient, and chamber pressure, and mass flow from characteristic velocity. |
| [`ROCKET - PropellantLoad`](skills/ROCKET%20-%20PropellantLoad) | Run `propellant_load.py` for usable propellant mass and tank volume (total, oxidizer, fuel) from mass flow, burn time, mixture ratio, and liquid densities. |
| [`ROCKET - ExpansionMatchEarth`](skills/ROCKET%20-%20ExpansionMatchEarth) | Run `expansion_match.py` for the altitude-matched nozzle expansion ratio on the 1976 U.S. Standard Atmosphere. Area ratio and ideal \(C_F\) come from Area-Mach. |
| [`ROCKET - PayloadtoDeltaV`](skills/ROCKET%20-%20PayloadtoDeltaV) | Run `payload_to_deltav.py` for useful payload from ideal delta-v, or ideal delta-v from useful payload, for one or more stages. A missing delta-v and payload writes a payload-versus-delta-v PNG. |
| [`ROCKET - LossStack`](skills/ROCKET%20-%20LossStack) | Run `loss_stack.py` for actual thrust, specific impulse, thrust coefficient, c*, and mass flow from ideal \(C_F\), ideal \(c^{*}\), and named efficiencies. With throat area and chamber pressure it also prints the lossless thrust and mass flow. Omitted efficiencies stay 1. |

Each skill has a `SKILL.md` that tells the agent when to use it and how to respond.

## Repository layout

```text
skills/
  aero-formulas/
    SKILL.md
    formulas.md          # formula reference
    checks/              # identity checks and allow-list
  ROCKET - Area-Mach Graph/
    SKILL.md
    area_mach.py         # nozzle area-Mach program (PNG + key: value stdout)
  ROCKET - PerformanceParameters/
    SKILL.md
    scripts/pairs.json   # propellant pairs, OF grids, density constants
    scripts/build_table.py  # offline CEA table builder
    src/load_table.py
    src/performance.py   # performance program (key: value stdout, optional PNG)
  ROCKET - ThroatSizingandMassFlow/
    SKILL.md
    throat_sizing.py     # throat area, diameter, and mass flow (key: value stdout)
  ROCKET - PropellantLoad/
    SKILL.md
    propellant_load.py   # propellant mass and volume (key: value stdout)
  ROCKET - ExpansionMatchEarth/
    SKILL.md
    expansion_match.py   # optimal expansion ratio versus altitude (key: value stdout, optional PNG)
  ROCKET - PayloadtoDeltaV/
    SKILL.md
    payload_to_deltav.py # payload versus ideal delta-v (key: value stdout, sweep PNG)
  ROCKET - LossStack/
    SKILL.md
    loss_stack.py        # delivered CF, c*, Isp, thrust, and mass flow (key: value stdout)
```

## Requirements

- **aero-formulas** — no extra runtime; the agent reads the markdown references.
- **ROCKET - Area-Mach Graph** — Python 3 with `numpy` and `matplotlib`.
- **ROCKET - PerformanceParameters** — Python 3 with `numpy` and `matplotlib`. Frozen tables are produced offline by `scripts/build_table.py` (`rocketcea`). A reply does not call CEA.
- **ROCKET - ThroatSizingandMassFlow** — Python 3 standard library only.
- **ROCKET - PropellantLoad** — Python 3 standard library only. Pair densities are read from `ROCKET - PerformanceParameters` `scripts/pairs.json`.
- **ROCKET - ExpansionMatchEarth** — Python 3 with `numpy` and `matplotlib`, because it calls `ROCKET - Area-Mach Graph`. It does not call CEA.
- **ROCKET - PayloadtoDeltaV** — Python 3 standard library for a point result. A delta-v sweep also needs `matplotlib`.
- **ROCKET - LossStack** — Python 3 standard library only.

Example:

```bash
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --gamma 1.25
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --check
python "skills/ROCKET - ThroatSizingandMassFlow/throat_sizing.py" --thrust 1500 --cf 1.5 --pc 2e6 --cstar 1600
python "skills/ROCKET - ThroatSizingandMassFlow/throat_sizing.py" --check
python "skills/ROCKET - PropellantLoad/propellant_load.py" --mdot 4 --tb 10 --r 2.3 --pair LOX/RP1
python "skills/ROCKET - PropellantLoad/propellant_load.py" --check
python "skills/ROCKET - PayloadtoDeltaV/payload_to_deltav.py" --stages 1 --stage mp=100,inert=10,isp-vac=300 --payload 5
python "skills/ROCKET - PayloadtoDeltaV/payload_to_deltav.py" --check
python "skills/ROCKET - LossStack/loss_stack.py" --cf 1.5 --cstar 1600 --throat 5e-4 --pc 2e6 --eta combustion=0.98 --eta nozzle=0.97
python "skills/ROCKET - LossStack/loss_stack.py" --check
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --pc 2e6 --gamma 1.25 --alt 0
python "skills/ROCKET - ExpansionMatchEarth/expansion_match.py" --check
```

## Units

SI is the working system (Pa, m², N). Skills convert other units before calling programs and state the units used in the reply.

## License

No license file is included yet. Treat the repository as private unless a license is added.
