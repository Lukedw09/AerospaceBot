# Check summary

Identities in [identities.md](identities.md) for the script records in [../formulas.md](../formulas.md). Each listed formula passed its named numeric checks. The program `--check` path also runs a Mode 2 head-on engagement regression (collision course, \(\dot{\lambda}=0\), intercept at \(R_0/V_c\)).

## Dynamics and control

- `true_pn_commanded_acceleration` (control): three_times_thousand_times_hundredth, signed_four_times_half_thousand
- `closing_speed` (control): approaching_two_fifty
- `los_rate` (control): three_four_closing_x

## Engagement regression

- Head-on collision course: \(R_0=10000\,\mathrm{m}\), \(\lambda_0=0\), \(V_m=300\,\mathrm{m/s}\) east, \(V_t=200\,\mathrm{m/s}\) west, \(N'=3\), \(a_{t,\mathrm{lat}}=0\) → \(V_c=500\,\mathrm{m/s}\), \(\dot{\lambda}=0\), \(a_c=0\), intercept at \(t=20\,\mathrm{s}\) within hit radius 1 m.

Run the program self-check:

```text
python "skills/GNC - ProportionalNavigation/proportional_navigation.py" --check
```
