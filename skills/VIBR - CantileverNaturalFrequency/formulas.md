# Cantilever natural-frequency formulas

Units are SI. Script records use the same style as the FormulaCatalouge: named `expr`, `family`, and `symbols`. The program implements these identities; `--check` exercises the numeric cases in [checks/identities.md](checks/identities.md).

Undamped free transverse vibration of a uniform Euler–Bernoulli cantilever follows NASA TN D-2831 (Stanek): the first five characteristic roots \(\lambda L\) for the fixed–free beam include \(1.87510\) for the fundamental mode; with zero viscous damping the vibration parameter reduces to \((\lambda L)^{2}\). The program uses the six-digit classic value \(\lambda_1 L = 1.875104\). Circular frequency is \(\omega_n = (\lambda_1 L)^{2}\sqrt{E I/(\mu L^{4})}\); cyclic frequency is \(f_{\mathrm{Hz}}=\omega_n/(2\pi)\). Mass per length \(\mu\) is the primary mass path; total beam mass uses \(\mu = m_{\mathrm{beam}}/L\).

## First fixed–free characteristic root

Dimensionless first root of the uniform cantilever frequency equation \(\cosh(\lambda L)\cos(\lambda L)+1=0\).

\[
\lambda_1 L \approx 1.875104
\]

```formula
## cantilever_lambda1_L
family: vibration
expr: 1.875104
symbols:
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\lambda_1 L\) | First fixed–free characteristic root | dimensionless |

Assumptions: uniform prismatic Euler–Bernoulli beam; fixed–free ends; undamped free vibration. Higher roots and other end conditions are omitted. NASA TN D-2831 lists \(1.87510\) for mode 1.

## Fundamental bending circular frequency

Undamped natural circular frequency of the first bending mode.

\[
\omega_n = (\lambda_1 L)^{2}\sqrt{\frac{E I}{\mu L^{4}}}
\]

```formula
## cantilever_omega_bending_1
family: vibration
expr: (lambda1_L)**2 * sqrt(E*I/(mu*L**4))
symbols: lambda1_L, E, I, mu, L
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\omega_n\) | Undamped natural circular frequency | rad/s |
| \(\lambda_1 L\) | First fixed–free root (`cantilever_lambda1_L`) | dimensionless |
| \(E\) | Young’s modulus | Pa |
| \(I\) | Second moment of area about the bending axis | m⁴ |
| \(\mu\) | Mass per unit length | kg/m |
| \(L\) | Beam length | m |

Assumptions: uniform \(E\), \(I\), and \(\mu\) along \(L\); Euler–Bernoulli kinematics (no shear deformation or rotary inertia); undamped; first bending mode only; no tip mass. \(E, I, \mu, L > 0\).

## Cyclic frequency

\[
f_{\mathrm{Hz}} = \frac{\omega_n}{2\pi}
\]

```formula
## cantilever_freq_hz
family: vibration
expr: omega_n/(2*pi)
symbols: omega_n, pi
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(f_{\mathrm{Hz}}\) | Natural frequency in hertz | Hz |
| \(\omega_n\) | Circular frequency from `cantilever_omega_bending_1` | rad/s |

## Mass per length from total beam mass

Alternate mass path when only the total beam mass is known. Primary path is to supply \(\mu\) directly.

\[
\mu = \frac{m_{\mathrm{beam}}}{L}
\]

```formula
## cantilever_mu_from_mass
family: vibration
expr: m_beam/L
symbols: m_beam, L
```

| Symbol | Meaning | Unit |
| --- | --- | --- |
| \(\mu\) | Mass per unit length | kg/m |
| \(m_{\mathrm{beam}}\) | Total uniform beam mass | kg |
| \(L\) | Beam length | m |

Assumptions: uniform mass distribution along \(L\). Tip mass is not included. \(m_{\mathrm{beam}}, L > 0\).
