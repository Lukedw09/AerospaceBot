# THERM - LumpedCapacitanceTransient

Lumped thermal capacitance under convection to a fixed ambient (\(\mathrm{Bi}\ll 1\)): \(\tau=m c/(h A)\), \(T(t)-T_{\infty}=(T_i-T_{\infty})\exp(-t/\tau)\), optional time to a target temperature, heat transferred \(Q=m c(T_i-T)\), and optional Biot \(\mathrm{Bi}=h L_c/k\).

## Run

```text
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --mass <kg> --c <J/(kg*K)> --area <m^2> --h <W/(m^2*K)> --ti <K> --t-inf <K> --time <s>
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --mass <kg> --c <J/(kg*K)> --area <m^2> --h <W/(m^2*K)> --ti <K> --t-inf <K> --target-temp <K> --k <W/(m*K)> --char-length <m> --out lumped_capacitance_transient.png
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --check
```

SI only at the program boundary. Pass exactly one of `--time` or `--target-temp`. Pass `--k` and `--char-length` together for Biot, or neither. Do not invent \(m\), \(c\), \(A\), \(h\), temperatures, \(k\), or \(L_c\).

## Docs

| File | Role |
| --- | --- |
| [SKILL.md](SKILL.md) | Agent instructions |
| [formulas.md](formulas.md) | Script-record identities |
| [checks/identities.md](checks/identities.md) | Named numeric checks |
| [checks/check.md](checks/check.md) | Pass list |
| [sources.md](sources.md) | U.S. gov / public-domain sources |

## Out of scope

Internal conduction gradients / Heisler charts as the primary model, radiation unless folded into an effective \(h\), ablation, TPS stacks, and heat-flux skills except as a user-reduced effective \(h\).
