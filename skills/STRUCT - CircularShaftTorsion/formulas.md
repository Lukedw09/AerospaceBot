# Circular shaft torsion formulas

Units are SI. Script records use the same style as the motor-case hoop records in the FormulaCatalouge: named `expr`, `family`, and `symbols`. The program implements these identities; `--check` exercises the numeric cases in [checks/identities.md](checks/identities.md).

Elastic torsion of a solid or concentrically hollow circular shaft follows the AFFDL Stress Analysis Manual (beam torsion, circular beams): shear \(f_s = T r / I_p\) and twist \(\theta = T L /(G I_p)\), with \(I_p = \pi/2\,(r_o^4 - r_i^4)\) (set \(r_i = 0\) for a solid shaft). Margin of safety uses the same fractional definition as the motor-case records, \(\mathrm{MS} = S_{\mathrm{allow}}/S_{\mathrm{design}} - 1\), with max shear as the design stress.

## Polar second moment (solid)

Polar second moment of area of a solid circular cross section of outer radius \(R_o\) (outer diameter \(D_o = 2 R_o\)).

\[
J = \frac{\pi}{2} R_o^{4} = \frac{\pi}{32} D_o^{4}
\]

```formula
## polar_second_moment_solid
family: shaft
expr: pi/2*Ro**4
symbols: Ro, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(J\) | Polar second moment of area | m⁴ |
| \(R_o\) | Outer radius | m |
| \(D_o\) | Outer diameter, \(2 R_o\) | m |

Assumptions: circular cross section. The diameter form is algebraically identical. \(R_o > 0\).

## Polar second moment (hollow)

Polar second moment of a concentrically hollow circular cross section.

\[
J = \frac{\pi}{2}\bigl(R_o^{4}-R_i^{4}\bigr) = \frac{\pi}{32}\bigl(D_o^{4}-D_i^{4}\bigr)
\]

```formula
## polar_second_moment_hollow
family: shaft
expr: pi/2*(Ro**4 - Ri**4)
symbols: Ro, Ri, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(J\) | Polar second moment of area | m⁴ |
| \(R_o\) | Outer radius | m |
| \(R_i\) | Inner radius | m |
| \(D_o, D_i\) | Outer and inner diameters | m |

Assumptions: concentric circular bore. \(R_o > R_i > 0\). A solid shaft is the \(R_i = 0\) limit of this expression (use the solid record when no bore is given).

## Circular shaft shear stress

Shear stress at radial station \(r\) under torque \(T\).

\[
\tau = \frac{T r}{J}
\]

Maximum shear is at the outer fiber, \(r = R_o\).

```formula
## circular_shaft_shear
family: shaft
expr: T*r/J
symbols: T, r, J
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\tau\) | Shear stress at radius \(r\) | Pa |
| \(T\) | Torque | N·m |
| \(r\) | Radial station from the center | m |
| \(J\) | Polar second moment | m⁴ |

Assumptions: elastic range; plane sections remain plane; radii remain straight; circular (solid or concentrically hollow) cross section. Non-circular Saint-Venant torsion and open thin-wall warping are omitted. \(T, J > 0\) and \(0 \le r \le R_o\).

## Angle of twist

Relative rotation of the ends of a prismatic circular shaft of length \(L\) and shear modulus \(G\).

\[
\theta = \frac{T L}{G J}
\]

```formula
## circular_shaft_twist
family: shaft
expr: T*L/(G*J)
symbols: T, L, G, J
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\theta\) | Angle of twist | rad |
| \(T\) | Torque | N·m |
| \(L\) | Shaft length | m |
| \(G\) | Shear modulus | Pa |
| \(J\) | Polar second moment | m⁴ |

Assumptions: uniform \(G\) and \(J\) along \(L\); ends free to warp in the Saint-Venant circular sense (no warping restraint correction). \(T, L, G, J > 0\).

## Margin of safety

Fractional amount by which the allowable stress exceeds the design stress. Same definition as the motor-case hoop records (NASA SP-8025 / FormulaCatalouge `margin_of_safety`).

\[
\mathrm{MS} = \frac{S_{\mathrm{allow}}}{S_{\mathrm{design}}} - 1
\]

```formula
## margin_of_safety
family: design
expr: allowable/design - 1
symbols: allowable, design
```

For this skill, \(S_{\mathrm{design}}\) is \(\tau_{\max}\). Equal allowable and design stresses give \(\mathrm{MS} = 0\).
