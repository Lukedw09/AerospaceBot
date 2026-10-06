# Sources — CTRL - ProportionalNavigation

Public-domain / U.S. government proportional-navigation identities used by this skill. Root catalog IDs refer to the repository [sources.md](../../sources.md).

| Local role | Document | Status | Scope used here |
| --- | --- | --- | --- |
| Primary | Zebenay, Lyzhoft, and Barbee, *Hybrid Guidance Control for a Hypervelocity Small Size Asteroid Interceptor Vehicle*, AAS 17-270 (NTRS 20170001430). Root ID **V90**. [Citation](https://ntrs.nasa.gov/citations/20170001430). [PDF](https://ntrs.nasa.gov/api/citations/20170001430/downloads/20170001430.pdf) | NTRS-hosted NASA Goddard / NASA-affiliated authors; U.S. government work | Classical PN: commanded acceleration perpendicular to the instantaneous LOS, \(u=n\,v_c\,\dot{\lambda}\); closing velocity \(v_c=-\dot{\mathbf{x}}_R\cdot\hat{\lambda}\); effective navigation gain \(n\) typically 3–5. Three-plane / kinematic-impulse hybrids in that paper are out of scope |
| Supporting | Cicolani, NASA TN D-772, *Trajectory Control in Rendezvous Problems Using Proportional Navigation* (April 1961). Root ID **V91**. NTRS 20040005909. [Citation](https://ntrs.nasa.gov/citations/20040005909). [PDF](https://ntrs.nasa.gov/api/citations/20040005909/downloads/20040005909.pdf) | NTRS: Work of the US Gov. Public Use Permitted. NASA Ames author | Planar proportional-navigation engagement geometry: LOS, lead angle, and the PN constraint that the relative-velocity rotation stays proportional to LOS rate. Rendezvous end-condition extensions (\(K\) constraint) are not used |

Commercial PN textbooks (for example Zarchan) and IEEE survey papers are not used. Pure pursuit, augmented PN (APN), seeker noise, filters, gravity, atmosphere, and autopilot lag are out of scope. Second-order plant step-response metrics remain under `CTRL - SecondOrderResponse` (V73–V76).
