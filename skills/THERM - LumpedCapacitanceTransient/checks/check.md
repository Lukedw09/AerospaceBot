# Check summary

Identities in [identities.md](identities.md) for the script records in [../formulas.md](../formulas.md). Each listed formula passed its named numeric checks.

## Aerothermodynamics

- `lumped_thermal_time_constant` (aerotherm): unit_mass, twenty_seconds
- `lumped_capacitance_temperature` (aerotherm): at_one_time_constant, initial_instant
- `lumped_capacitance_time_to_temperature` (aerotherm): one_time_constant, halfway_excess
- `lumped_capacitance_heat_transferred` (aerotherm): cool_by_one_kelvin, at_one_time_constant
- `biot_number` (aerotherm): small_biot, warn_threshold

Run the program self-check:

```text
python "skills/THERM - LumpedCapacitanceTransient/lumped_capacitance_transient.py" --check
```
