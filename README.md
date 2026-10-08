# v6 SKY26d: 4x2 official acceptance experiment

Branch: `experiment/80mhz-official-4x2`.
Baseline: `679dbd88bb4a0062b3611c912f4d5e878e2e3574`, the passing 6x2 official-flow build.

This controlled trial changes only the design's tile allocation from 6x2 to 4x2.
Functional RTL, wrapper, tests, `src/config.json`, and `build_lock.json` remain
unchanged. The clock is 80 MHz, placement target density is 60%, synthesis uses
AREA 0, and both post-global-route repair switches remain enabled.

The GDS Action, precheck, and gate-level jobs retain the official acceptance
policy. All nine STA corner reports remain available. A passing workflow does
not imply all-corner 80 MHz timing or zero slew/fanout violations. The existing
MAX_CAPACITANCE_CONSTRAINT=null override is retained, as in the 6x2 baseline.

The 6x2 baseline occupies 122,427 um^2 of standard-cell area and reports 54.219%
core utilization after repair. Keeping that cell area in 4x2 would put utilization
near 83%; actual cell area and congestion depend on the new placement and repair.
Unused floorplan space is also needed for routing and physical repair.

An earlier 80 MHz 4x2 run (37651255886, commit d336c8c) failed detailed placement
during antenna repair, before final timing/electrical acceptance. This trial
includes the newer post-GRT repair configuration, so it is a new feasibility
test; its success is not assumed. No density or checking thresholds are relaxed.

`scripts/verify_inputs.py` checks the exact tile-only input change and immutable
RTL/test bytes. `scripts/assess_build.py` remains an optional diagnostics tool.

The 6x2 source and build remain preserved. This branch is not a shuttle
registration, payment, or fabrication submission.
