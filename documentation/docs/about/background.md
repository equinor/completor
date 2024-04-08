# Well Modeling with Inflow Control for Dynamic Simulations

Eclipse and OPM Flow have functionality to simulate advanced wells by multi-segment well (MSW) models.
With the MSW concept, it is possible to model multilateral wells and wells with and without inflow control technology,
annular flow and zonal isolation (packers).
The challenge is to establish schedule files (to be included in Eclipse or OPM Flow) representing the complex well completion designs.
Completor® provides a simple and efficient workflow for generating the necessary schedule files.

Completor® can model wells with:
- Standard perforation/open-hole.
- Wells with inflow control technology:
ICD, various AICDs (Taqa, Baker Hughes, Weatherford),
ResAdvance (SLB), EquiFlow (Halliburton), AICV (Inflow Control AS), and DAR (Innowell).
- Wells gravel pack in the annulus.
- Wells with annular flow.
- Wells with limited annular flow (packers).

There is a limitation on implementation of Inflow Control devices in OPM Flow,
it is still under development on modeling the annulus flow and DAR devices.