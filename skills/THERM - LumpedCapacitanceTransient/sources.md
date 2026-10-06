# Sources — THERM - LumpedCapacitanceTransient

Public-domain / U.S. government lumped-capacitance and Biot-limit identities used by this skill. Root catalog IDs refer to the repository [sources.md](../../sources.md).

| Local role | Document | Status | Scope used here |
| --- | --- | --- | --- |
| Primary | NASA Glenn T-MATS, *0-D Transient Conduction Library Block* (`HeatXfer_TMATS_0DTCondLS`). Root ID **V87**. [Repository](https://github.com/nasa/T-MATS). [Block help](https://github.com/nasa/T-MATS/blob/master/Trunk/TMATS_Library/TMATS_Support/HeatXfer_TMATS_0DTCondLS.html) | NASA Glenn open-source U.S. government work | Lumped capacitance: \(T(t)-T_{\infty}=(T_i-T_{\infty})\exp(-t/\tau)\) with \(\tau=\rho V c/(h A)=m c/(h A)\); \(L_c=V/A\); Biot check \(\mathrm{Bi}=h L_c/k\le 0.1\) for the spatially uniform-temperature assumption |
| Supporting Bi threshold | Clarke et al., *Power Cable Mass Estimation for Electric Aircraft Propulsion* (2021). Root ID **V89**. NTRS 20210015051. [Citation](https://ntrs.nasa.gov/citations/20210015051) | NTRS: Work of the US Gov. Public Use Permitted. NASA Glenn authors | First-order lumped-capacitance thermal model holds for Biot numbers less than 0.1 |
| Heisler / distributed limit | Miller, NASA TM X-1442, *Transient Heat Conduction in Finite Slabs with Position-Dependent Heat Generation* (1967). Root ID **V88**. NTRS 19670028932. [Citation](https://ntrs.nasa.gov/citations/19670028932). [PDF](https://ntrs.nasa.gov/api/citations/19670028932/downloads/19670028932.pdf) | NTRS: Work of the US Gov. Public Use Permitted. NASA Lewis author | Slab transient conduction with Biot \(\mathrm{Bi}=h L/k\) and Fourier \(\mathrm{Fo}=\alpha t/L^{2}\); Heisler-type convection/special-case discussion. Used only as the limit note when Bi is not ≪ 1. Chart data are not transcribed |

Commercial heat-transfer textbooks (Incropera, Cengel, and similar) are not used. Internal conduction gradients, radiation (unless linearized into an effective \(h\)), ablation, and TPS stacks are out of scope.
