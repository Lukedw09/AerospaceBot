# Proportional navigation formulas

Units are SI. Script records use the same style as the motor-case hoop records in the FormulaCatalouge: named `expr`, `family`, and `symbols`. The program implements these identities; `--check` exercises the numeric cases in [checks/identities.md](checks/identities.md).

Planar true proportional navigation follows the NASA Goddard intercept guidance statement of classical PN: commanded acceleration proportional to closing velocity and line-of-sight (LOS) rate, applied perpendicular to the instantaneous LOS (Zebenay, Lyzhoft, and Barbee; NTRS 20170001430). Closing speed is the negative range rate along the interceptor-to-target LOS.

## Sign conventions

Engagement plane \((x,y)\). Relative position from interceptor to target \(\mathbf{R}=\mathbf{r}_t-\mathbf{r}_m\). Relative velocity \(\mathbf{V}=\mathbf{v}_t-\mathbf{v}_m\). LOS angle \(\lambda=\mathrm{atan2}(R_y,R_x)\) from \(+x\) toward \(+y\). Range \(R=|\mathbf{R}|\). Range rate \(\dot{R}=(\mathbf{R}\cdot\mathbf{V})/R\). Closing speed \(V_c=-\dot{R}\) (positive when closing). LOS rate \(\dot{\lambda}=(R_x V_y-R_y V_x)/R^{2}\). True-PN interceptor acceleration is \(a_c(-\sin\lambda,\cos\lambda)\), normal to the LOS in the direction of increasing \(\lambda\).

## True PN commanded acceleration

Scalar true-PN acceleration command from effective navigation ratio, closing speed, and LOS rate.

\[
a_c = N'\, V_c\, \dot{\lambda}
\]

```formula
## true_pn_commanded_acceleration
family: control
expr: N_prime*Vc*lambda_dot
symbols: N_prime, Vc, lambda_dot
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(a_c\) | Commanded acceleration (true PN) | m/s² |
| \(N'\) | Effective navigation ratio (script `N_prime`) | dimensionless |
| \(V_c\) | Closing speed (script `Vc`) | m/s |
| \(\dot{\lambda}\) | LOS rate (script `lambda_dot`) | rad/s |

Assumptions: planar true PN; acceleration direction is normal to the LOS. \(N'>0\). \(V_c\) and \(\dot{\lambda}\) keep their algebraic signs. Mode 1 of the program evaluates this identity alone.

## Closing speed

Closing speed is the negative of the range rate along the interceptor-to-target LOS.

\[
V_c = -\dot{R}
\]

```formula
## closing_speed
family: control
expr: -R_dot
symbols: R_dot
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(V_c\) | Closing speed | m/s |
| \(\dot{R}\) | Range rate (script `R_dot`) | m/s |

Assumptions: \(V_c>0\) when the vehicles are approaching. Matches the NASA closing-velocity definition as the negative of relative velocity dotted into the LOS unit vector (with LOS from interceptor to target).

## LOS rate

Planar LOS angular rate from relative position and relative velocity.

\[
\dot{\lambda} = \frac{R_x V_y - R_y V_x}{R^{2}}
\]

```formula
## los_rate
family: control
expr: (Rx*Vy - Ry*Vx)/R**2
symbols: Rx, Ry, Vx, Vy, R
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\dot{\lambda}\) | LOS rate | rad/s |
| \(R_x,R_y\) | Relative position components (target minus interceptor) | m |
| \(V_x,V_y\) | Relative velocity components | m/s |
| \(R\) | Range \(\sqrt{R_x^{2}+R_y^{2}}\) | m |

Assumptions: planar engagement; \(R>0\). Equivalent to the \(z\)-component of \(\mathbf{R}\times\mathbf{V}/R^{2}\).
