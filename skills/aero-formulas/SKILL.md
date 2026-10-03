---
name: aero-formulas
description: >-
  Select an aerospace formula from the skill reference using the user's
  context, then either calculate with it or present it with every variable and
  unit defined. Use when the user asks for an aerospace equation, a flight or
  orbital calculation, or what a formula's symbols and units mean.
---

# Aero Formulas

Read [formulas.md](formulas.md) before answering. Use only formulas listed there.

## Select the formula

1. Search every formula in formulas.md.
2. Use the user's wording, known quantities, and requested result to choose the formula that fits.
3. If more than one formula fits, choose the one that uses the quantities the user already has. If the choice is still ambiguous, ask which result they want before calculating.
4. If none fit, say so. Do not invent a formula.

## Respond in one of two ways

**Calculate** when the user gives enough known values to solve.

- State the formula.
- Define every variable and its unit.
- Substitute the user's values in consistent units.
- Give the numeric result with its unit.

**Present** when the user asks for the equation itself, or when known values are missing.

- State the formula.
- Define every variable by name.
- Give the unit of every variable.
- Do not invent values or compute a result.
