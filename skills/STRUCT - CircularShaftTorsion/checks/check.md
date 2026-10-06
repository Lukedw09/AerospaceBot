# Check summary

Identities in [identities.md](identities.md) for the script records in [../formulas.md](../formulas.md). Each listed formula passed its named numeric checks (or is the shared design definition reused from the motor-case records).

## Structures

- `polar_second_moment_solid` (shaft): unit_solid, twenty_mm_radius
- `polar_second_moment_hollow` (shaft): unit_hollow_annulus, matches_solid_when_ri_zero
- `circular_shaft_shear` (shaft): unit_shear, affdl_outer_fiber
- `circular_shaft_twist` (shaft): unit_twist, affdl_hollow_sample
- `margin_of_safety` (design): zero_margin, quarter_margin

Run the program self-check:

```text
python "skills/STRUCT - CircularShaftTorsion/circular_shaft_torsion.py" --check
```
