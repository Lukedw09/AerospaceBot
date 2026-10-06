# Check summary

Identities in [identities.md](identities.md) for the script records in [../formulas.md](../formulas.md). Each listed formula passed its named numeric checks.

## Vibration

- `cantilever_lambda1_L` (vibration): stanek_mode1, six_digit_classic
- `cantilever_omega_bending_1` (vibration): unit_beam, aluminum_sample
- `cantilever_freq_hz` (vibration): unit_hz, sample_hz
- `cantilever_mu_from_mass` (vibration): unit_mu, half_metre_beam

Run the program self-check:

```text
python "skills/VIBR - CantileverNaturalFrequency/cantilever_natural_frequency.py" --check
```
