# v6 SKY26d experiment

Unchanged v6 sign-overlap and approximate peak detector, built for TTSKY26d.

| Branch | Clock | Period | Highest input frequency | Output handoff |
| --- | ---: | ---: | ---: | ---: |
| main | 40 MHz | 25 ns | 19.53125 kHz | 2 ms |
| experiment/80mhz | 80 MHz | 12.5 ns | 39.0625 kHz | 1 ms |

Both builds start at 4x2 tiles. If placement capacity requires expansion, both use the same 6x2 or 8x2 size.

Levels 0-23 are retained. Input frequency is clock_hz / (2048 * 2^level).
40 MHz levels 0-22 match the original 80 MHz levels 1-23; level 23 extends lower.
80 MHz exceeds the official SKY130 input-pad rating and is an experimental target.

RTL remains byte-identical to v6 commit dae8933. A transparent wrapper supplies a unique top-module name.
All nine setup/hold corners and electrical rules must pass for strict acceptance.
Completed layouts are preserved for physical and functional checks even when strict acceptance fails.

Run RTL checks with `cd test && make`. GitHub Actions builds GDS, performs precheck and gate-level checks.
No FPGA, ADC, board or silicon validation is implied. This repository has not been registered or paid for a shuttle.
