# KRK Two-Stage Abstention Enabled Tiny Smoke v0

Status: `enabled_tiny_smoke_no_behavior_delta`

Opt-in selector was enabled with penalty `1.0` on three protected labels. Paired h40 metrics matched the baseline for every label; the selector penalized suggestions but no penalized suggestion became selected.

| Label | Baseline playouts | Enabled playouts | Penalized | Selected penalized | Shadow baseline -> enabled | Core metric diff |
| --- | --- | --- | ---: | ---: | --- | --- |
| `edge_trap_wrong_tempo` | `{"max_plies": 1, "mate": 2}` | `{"max_plies": 1, "mate": 2}` | 0 | 0 | 2 -> 2 | `false` |
| `fence_established` | `{"mate": 3}` | `{"mate": 3}` | 24 | 0 | 0 -> 0 | `false` |
| `drive_to_edge` | `{"mate": 3}` | `{"mate": 3}` | 0 | 0 | 0 -> 0 | `false` |

Aggregate:

- Total penalized count: `24`
- Total selected penalized count: `0`
- Labels with core metric diffs: `[]`
- Labels with conversion regression: `[]`
- Labels with shadow regression: `[]`

Interpretation: the selector fired on protected controls but no penalized suggestion was selected, and paired h40 outcomes matched the baseline for all three labels. This supports default-off safety and traceability, but does not yet show target improvement.

Next step: `bounded_target_challenge_smoke_or_review_before_stage7_allow_flag`
