# Stage 7 2cc Frozen Model Sandbox Summary

Schema: `stage7_2cc_frozen_model_sandbox_summary.v1`
Causal status: `non_causal`
Runtime behavior changed: `False`

## Default Off

Playouts: `{'mate': 2, 'max_plies': 3}`
Supported suggestions: `0`

## Enabled

Playouts: `{'mate': 2, 'max_plies': 2, 'draw': 1}`
Supported suggestions: `4`
Selected supported: `1`
Supported moves by outcome: `{'e2f2:max_plies': 1, 'e4d3:max_plies': 1, 'd1e2:draw': 1, 'f2g2:mate': 1}`
Selected by outcome: `{'d1e2:draw': 1}`

## Candidate Update

Candidate: `cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1`
Diagnosis: `selected_candidate_move_still_insufficient_for_multistep_conversion`
Next action: `run bounded candidate-local continuation warmup only if guardrails remain scoped`
