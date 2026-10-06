# VIBR - CantileverNaturalFrequency

Fundamental bending natural frequency of a uniform Euler–Bernoulli cantilever (fixed–free): \(\omega_n = (\lambda_1 L)^{2}\sqrt{E I/(\mu L^{4})}\) with \(\lambda_1 L \approx 1.875104\), and \(f_{\mathrm{Hz}}=\omega_n/(2\pi)\).

## Run

```text
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --E <Pa> --inertia <m^4> --length <m> --mu <kg/m>
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --E <Pa> --inertia <m^4> --length <m> --mass <kg> --out cantilever_natural_frequency.png
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --check
```

SI only at the program boundary. Pass `--mu` (primary) or `--mass` (\(\mu = m_{\mathrm{beam}}/L\)), not both.

## Docs

| File | Role |
| --- | --- |
| [SKILL.md](SKILL.md) | Agent instructions |
| [formulas.md](formulas.md) | Script-record identities |
| [checks/identities.md](checks/identities.md) | Named numeric checks |
| [checks/check.md](checks/check.md) | Pass list |
| [sources.md](sources.md) | U.S. gov / public-domain sources |

## Out of scope

Higher bending modes, tip mass / massless-beam tip-mass formulas, damping, forced response (use `CTRL - SecondOrderResponse`), axial or torsional modes, non-cantilever end conditions.
