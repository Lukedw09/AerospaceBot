# AerospaceBot

Cursor agent skills for aerospace engineering: checked formulas and small physics programs the bot can run and report, instead of reinventing equations or redrawing plots by hand.

## Skills

| Skill | Purpose |
| --- | --- |
| [`aero-formulas`](skills/aero-formulas) | Select and use verified aerospace formulas (compressible flow, rocket propulsion, aerodynamics). Only formulas listed in `checks/check.md` are allowed. |
| [`ROCKET - Area-Mach Graph`](skills/ROCKET%20-%20Area-Mach%20Graph) | Run `area_mach.py` for an isentropic nozzle area-Mach curve, exit Mach from area ratio, exit pressure, ideal thrust, and expansion state. |

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
```

## Requirements

- **aero-formulas** — no extra runtime; the agent reads the markdown references.
- **ROCKET - Area-Mach Graph** — Python 3 with `numpy` and `matplotlib`.

Example:

```bash
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --gamma 1.25
python "skills/ROCKET - Area-Mach Graph/area_mach.py" --check
```

## Units

SI is the working system (Pa, m², N). Skills convert other units before calling programs and state the units used in the reply.

## License

No license file is included yet. Treat the repository as private unless a license is added.
