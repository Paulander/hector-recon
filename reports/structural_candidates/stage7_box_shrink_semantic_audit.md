# Stage 7 Structural Candidate Audit

Schema: `structural_candidate_audit.v1`
Causal status: `non_causal`
Candidates: `3`

## Status Counts

- `handoff_role_audit_required`: 1
- `needs_more_terms`: 1
- `quarantine_confirmed`: 1

## Candidate Audits

### cand.krk.box_shrink.reward_contract_refinement.v1

- Type: `contract_refinement`
- Monitor: `growth.monitor.reward_contract_mismatch`
- Audit status: `needs_more_terms`
- Candidate update: `proposed` -> `needs_more_terms`
- Finding: box_shrink reward confirms in states where the current visible contract does not confirm
- Finding: box_area_decreased_after_own_move is not consistently true under reward confirmation
- Finding: box_area_not_increased_after_reply is weaker than true box shrink and may only show non-expansion
- Finding: some reward-confirmed samples lack visible fence/cut preservation
- Reward mismatches: `24`

### cand.krk.box_shrink.handoff_role_refinement.v1

- Type: `successor_contract_refinement`
- Monitor: `growth.monitor.successor_miscalibration`
- Audit status: `handoff_role_audit_required`
- Candidate update: `proposed` -> `sandbox_ready`
- Finding: stage0_basin remains the dominant failed continuation after box_shrink
- Finding: some selected successors are not licensed by visible role evidence
- Finding: high-score successor selections still fail conversion and need role/contract audit
- Stage0 max-plies ratio: `31/31`

### cand.krk.box_shrink.overlay_quarantine_confirmed.v1

- Type: `quarantine_overlay`
- Monitor: `growth.monitor.stage_overlay_quarantine`
- Audit status: `quarantine_confirmed`
- Candidate update: `quarantined` -> `quarantined`
- Finding: overlay remains quarantined by target conversion/shadow evidence
