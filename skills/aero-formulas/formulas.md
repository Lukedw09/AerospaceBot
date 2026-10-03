# Aerospace formulas

Units below are SI. Any single consistent unit system is valid. Do not mix systems in one calculation.

## Area-Mach relation

Local duct area compared with the sonic throat area for isentropic flow of a calorically perfect gas.

\[
\frac{A}{A^{*}} = \frac{1}{M}\left[\frac{2}{\gamma+1}\left(1+\frac{\gamma-1}{2}M^{2}\right)\right]^{\frac{\gamma+1}{2(\gamma-1)}}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(A\) | Local cross-sectional flow area | m² |
| \(A^{*}\) | Sonic throat area, the area where \(M = 1\) | m² |
| \(M\) | Local Mach number | dimensionless |
| \(\gamma\) | Ratio of specific heats, \(c_p / c_v\) | dimensionless |

Assumptions: steady, one-dimensional, isentropic flow of a calorically perfect gas. For air, use \(\gamma = 1.4\) unless the user gives another value.

## Bernoulli's relation

Mechanical energy is constant along a streamline in steady, incompressible, inviscid flow.

\[
p + \frac{1}{2}\rho V^{2} + \rho g z = \text{constant}
\]

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(p\) | Static pressure | Pa |
| \(\rho\) | Density | kg/m³ |
| \(V\) | Flow speed | m/s |
| \(g\) | Gravitational acceleration | m/s² |
| \(z\) | Elevation | m |

Assumptions: steady, incompressible, inviscid flow along a streamline. Density is constant. Use \(g = 9.80665\,\text{m/s}^2\) unless the user gives another value. When elevation change is negligible, the \(\rho g z\) term may be dropped, leaving \(p + \frac{1}{2}\rho V^{2} = \text{constant}\).
