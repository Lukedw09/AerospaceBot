# Sources — STRUCT - CircularShaftTorsion

Public-domain / U.S. government strength-of-materials identities used by this skill. Root catalog IDs refer to the repository [sources.md](../../sources.md).

| Local role | Document | Status | Scope used here |
| --- | --- | --- | --- |
| Primary | Air Force Flight Dynamics Laboratory, AFFDL-TR-69-42 / October 1986 *Stress Analysis Manual*, beam torsion (circular beams). Root ID **V81**. HTML excerpt: [Beam Torsion](https://engineeringlibrary.org/reference/beam-torsion-air-force-stress-manual) | U.S. Air Force technical report; U.S. government work | Elastic circular torsion: \(f_s = T r / I_p\), \(\theta = T L /(G I_p)\), with \(I_p = \pi/2\,(r_o^4 - r_i^4)\) (solid when \(r_i = 0\)). Plastic / modulus-of-rupture torque formulas in that chapter are not used |
| Supporting | NASA Marshall Space Flight Center, NASA TM X-73305 / TM X-73306, *Astronautic Structures Manual* (August 1975). Root ID **V80** (Vol. I); Vol. II section B8 covers torsion of solid sections | NTRS: Work of the US Gov. Public Use Permitted | Confirms circular Saint-Venant torsion as the closed-form circular-shaft case; thin-wall open/closed warping charts in B8 are out of scope for this skill |
| Margin definition | NASA SP-8025, *Solid Rocket Motor Metal Cases* (April 1970), as recorded with FormulaCatalouge `margin_of_safety` | NTRS: Work of the US Gov. Public Use Permitted | \(\mathrm{MS} = S_{\mathrm{allow}}/S_{\mathrm{design}} - 1\) with design stress taken as \(\tau_{\max}\) |

Commercial handbooks (Roark, Bruhn, and similar) are not used. Non-circular Saint-Venant torsion, open thin-wall warping, plastic torsion, and combined bending-plus-torsion are out of scope.
