# Sources — VIBR - CantileverNaturalFrequency

Public-domain / U.S. government structural-dynamics identities used by this skill. Root catalog IDs refer to the repository [sources.md](../../sources.md).

| Local role | Document | Status | Scope used here |
| --- | --- | --- | --- |
| Primary | Stanek, NASA TN D-2831, *Free and Forced Vibrations of Cantilever Beams with Viscous Damping* (June 1965). Root ID **V86**. NTRS 19650017041. [Citation](https://ntrs.nasa.gov/citations/19650017041). [PDF](https://ntrs.nasa.gov/api/citations/19650017041/downloads/19650017041.pdf) | NTRS: Work of the US Gov. Public Use Permitted. NASA Marshall author | Uniform cantilever free vibration: first five characteristic roots \(\lambda L\), with mode 1 equal to \(1.87510\). With zero viscous damping the vibration parameter reduces to \((\lambda L)^{2}\), so the undamped natural circular frequency scales as \((\lambda L)^{2}\) times the Euler–Bernoulli beam wave-speed factor \(\sqrt{E I/(\mu L^{4})}\). Forced-response and damping formulas in that note are not used |
| Supporting identity | Frequency equation \(\cosh(\lambda L)\cos(\lambda L)+1=0\) for a uniform fixed–free Euler–Bernoulli beam (mathematical relation; not a prose source) | Not copyrightable | Confirms the six-digit classic root \(\lambda_1 L \approx 1.875104\) used by the program; \((\lambda_1 L)^{2} \approx 3.516015\) |

Commercial handbooks (Blevins, Roark, and similar) are not used. Tip-mass / massless-beam tip-mass modes, higher bending modes, axial and torsional modes, shear / Timoshenko corrections, and non-cantilever end conditions are out of scope for v1.
