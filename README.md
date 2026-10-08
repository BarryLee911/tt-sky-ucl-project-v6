# v6 SKY26d: official acceptance experiment

Branch: `experiment/80mhz-official-checks`.
Baseline: `da3743552a625af0f71b2d3b912b2f3708bcc8b5` (AREA 0 with post-GRT repair).

This experiment restores the default TTSKY26d build acceptance policy. The GDS,
precheck and gate-level jobs follow the official template dependency chain;
the exact Action and support-tool commits and LibreLane version remain pinned.
Precheck and gate-level tests run after a successful GDS job. There is no
continue-on-error, recovered submission packaging, or custom strict signoff gate.
The optional Pages viewer is not deployed from this experiment branch.

The four project overrides for TIMING/HOLD/MAX_SLEW/MAX_CAP_VIOLATION_CORNERS
are removed. With the locked SKY130/LibreLane versions, Setup violations are
fatal in typical-process corners, Hold violations are fatal in all corners,
and slew/capacitance violations are reported as warnings. All nine STA corners
are still analyzed. The custom requirement for zero fanout violations is not a
workflow acceptance gate.

The RTL, wrapper and functional tests are unchanged. Implementation settings
remain 80 MHz (12.5 ns), 6x2 tiles, 60% placement density, AREA 0, and both
post-global-route repair switches enabled. I/O delay remains 2.5 ns, maximum
transition 0.75 ns and maximum fanout 10. The existing
MAX_CAPACITANCE_CONSTRAINT=null override remains for a controlled comparison;
it uses Liberty limits rather than adding the PDK's global 0.2 pF constraint.
This changes acceptance rules, not every design parameter to template defaults.

The official GDS_logs artifact retains the final nine-corner STA results and
resolved configuration. `scripts/assess_build.py` is an optional read-only
diagnostic report generator; it does not set workflow outputs or modify build
provenance. `scripts/verify_inputs.py` checks source/configuration consistency
in the independent RTL regression, without adding timing or electrical gates.

80 MHz remains above the published SKY130 input-pad rating. A passing workflow
does not demonstrate reliable 80 MHz operation across all corners or on hardware.
The original v6 source and earlier experimental branches are retained. No shuttle
registration, payment, or fabrication submission is performed by this workflow.

Official sources:
- [TTSKY26d template workflow](https://github.com/TinyTapeout/ttsky-verilog-template/blob/68c3fd3f3ec640e5edcb6a5f74f360ebc016bb2a/.github/workflows/gds.yaml)
- [LibreLane 3.0.14 checker policy](https://github.com/librelane/librelane/blob/f24e0ea5db2260719e9a0c7d51d07db74a87fa23/librelane/steps/checker.py)
- [SKY130 corner defaults](https://github.com/librelane/librelane/blob/f24e0ea5db2260719e9a0c7d51d07db74a87fa23/librelane/config/pdk_compat.py)
