# v6 SKY26d: 4x2 at 70% placement target density

Branch: `experiment/80mhz-official-4x2-density70`.
Baseline: `4fc28307d41d38ff5437dbef0d0d5de16b1b4fd6` (4x2 at 60%).
Preserved passing 6x2 baseline: `679dbd88bb4a0062b3611c912f4d5e878e2e3574`.

This single-variable trial changes `PL_TARGET_DENSITY_PCT` from 60 to 70.
RTL, wrapper, functional tests, info.yaml and build_lock.json are unchanged.
The design remains 4x2 tiles at 80 MHz (12.5 ns). I/O delays, hold margins,
AREA 0 synthesis, and both post-global-route repair switches are preserved.
All other src/config.json values remain identical to the 60% baseline.

The previous 4x2 run (37853828968) completed global placement but failed in
antenna repair with DPL-0036 (detailed placement failed). Its last completed
stage reported 81.0059% core utilization. This was a physical placement failure
before final timing/electrical acceptance. A different target density may alter
placement, routing, and buffer insertion; success is not assumed. Target density
is not a hard cap on utilization after physical repair.

GDS, official precheck and gate-level tests retain the same acceptance policy.
All nine STA corner reports remain available when the flow reaches signoff.
The existing MAX_CAPACITANCE_CONSTRAINT=null setting is unchanged. A green
workflow does not establish all-corner 80 MHz timing or zero slew/fanout issues.

The provenance script checks that density is the only implementation input
change. This branch does not register, pay for, or submit fabrication. The
restored 6x2 checkout and the 60% experiment remain preserved.
