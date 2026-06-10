# CandidateMoveFrame DTM Alignment

Schema: `candidate_move_frame_dtm_alignment.v1`
Causal status: `non_causal`
FEN: `8/8/R7/8/2k5/8/8/3K4 w - - 2 2`

## Diagnosis

- Candidate: `cand.krk.box_shrink.family_2cc0b3e1033a.post_box_continuation_overlay_protocol.v1`
- Diagnosis: `multi_step_continuation_policy_gap_not_single_move_gap`
- Status: `narrow_plan_capsule_or_overlay_training_protocol_ready`

## DTM

- State DTM: 27
- Legal moves: 19
- Winning moves: 19
- All legal moves win: `True`
- Best child DTM: 26
- Best moves: `a6a5`, `a6d6`, `d1d2`, `a6a1`, `a6a2`

## Current Graph Legal-First

- Probe count: 19
- Outcomes: `{'h50:max_plies': 19}`

## Interpretation

All legal first moves are tablebase-winning, but current graph legal-first probes do not convert.
This supports a multi-step continuation/capsule diagnosis rather than another single legal-move role.
