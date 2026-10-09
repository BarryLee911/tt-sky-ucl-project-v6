# v6 SKY26d: 4x2 at 80% placement target density

Branch: `experiment/80mhz-official-4x2-density80`.
Baseline: `e69a4847c0a5b4b7d2f06c63eae7e1f66977c02e` (4x2 at 70%).
Preserved passing 6x2 baseline: `679dbd88bb4a0062b3611c912f4d5e878e2e3574`.

This single-variable trial changes `PL_TARGET_DENSITY_PCT` from 70 to 80.
RTL, wrapper, functional tests, info.yaml and build_lock.json are unchanged.
The design remains 4x2 tiles at 80 MHz (12.5 ns). I/O delays, hold margins,
AREA 0 synthesis, and both post-global-route repair switches are preserved.
All other src/config.json values remain identical to the 70% baseline.

The 70% trial (37862348367) failed in OpenROAD.ResizerTimingPostCTS after
inserting 3221 hold buffers. Detailed placement reported 23 failed instance
entries and DPL-0036. This occurred before global routing and final signoff.
The earlier 60% trial (37853828968) reached antenna repair before failing
with DPL-0036. Raising target density has not yet demonstrated an improvement.
This 80% trial may change placement, routing and buffer insertion; success is
not assumed. Target density is not a hard cap on utilization after repair.

GDS, official precheck and gate-level tests retain the same acceptance policy.
All nine STA corner reports remain available when the flow reaches signoff.
The existing MAX_CAPACITANCE_CONSTRAINT=null setting is unchanged. A green
workflow does not establish all-corner 80 MHz timing or zero slew/fanout issues.

The provenance script checks that density is the only implementation input
change. This branch does not register, pay for, or submit fabrication. The
restored 6x2 checkout and the 60% and 70% experiments remain preserved.
