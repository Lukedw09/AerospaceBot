# STRUCT - CircularShaftTorsion

Elastic torsion of a solid or hollow circular shaft: polar second moment \(J\), max shear \(\tau_{\max} = T R_o / J\), optional twist \(\theta = T L /(G J)\), and optional margin of safety.

## Run

```text
python "skills/STRUCT - CircularShaftTorsion/circular_shaft_torsion.py" --torque <N*m> --radius <m>
python "skills/STRUCT - CircularShaftTorsion/circular_shaft_torsion.py" --torque <N*m> --diameter <m> --inner-diameter <m> --length <m> --G <Pa> --allowable <Pa> --out torsion.png
python "skills/STRUCT - CircularShaftTorsion/circular_shaft_torsion.py" --check
```

SI only at the program boundary. Use either the radius API (`--radius` / `--inner-radius`) or the diameter API (`--diameter` / `--inner-diameter`), not both.

## Docs

| File | Role |
| --- | --- |
| [SKILL.md](SKILL.md) | Agent instructions |
| [formulas.md](formulas.md) | Script-record identities |
| [checks/identities.md](checks/identities.md) | Named numeric checks |
| [checks/check.md](checks/check.md) | Pass list |
| [sources.md](sources.md) | U.S. gov / public-domain sources |

## Out of scope

Non-circular sections, open thin-wall warping, plastic torsion, combined bending-plus-torsion Mohr.
