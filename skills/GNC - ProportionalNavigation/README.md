# GNC - ProportionalNavigation

Planar true proportional navigation: instantaneous commanded acceleration \(a_c=N' V_c\dot{\lambda}\), and optional constant-speed planar engagement with PN steering (intercept time or miss distance).

Guidance kinematics live in the GNC family beside `GNC - SecondOrderResponse`.

## Run

```text
python "skills/GNC - ProportionalNavigation/proportional_navigation.py" --n-prime 3 --vc 1000 --los-rate 0.01
python "skills/GNC - ProportionalNavigation/proportional_navigation.py" --n-prime 4 --range 10000 --los-angle 0.35 --vm 450 --hm 0.2 --vt 250 --ht 3.0 --out pn.png
python "skills/GNC - ProportionalNavigation/proportional_navigation.py" --check
```

SI only at the program boundary. Mode 1 is instantaneous \(a_c\). Mode 2 integrates a planar engagement; pass either speed/heading (`--vm --hm --vt --ht`) or velocity components (`--vmx --vmy --vtx --vty`), not both.

## Docs

| File | Role |
| --- | --- |
| [SKILL.md](SKILL.md) | Agent instructions |
| [formulas.md](formulas.md) | Script-record identities |
| [checks/identities.md](checks/identities.md) | Named numeric checks |
| [checks/check.md](checks/check.md) | Pass list |
| [sources.md](sources.md) | U.S. gov / public-domain sources |

## Out of scope

3D PN, seeker noise, filters, gravity, atmosphere, autopilot lag, pursuit, APN. Second-order step-response metrics belong in `GNC - SecondOrderResponse`.
