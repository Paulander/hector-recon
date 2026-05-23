# KRK Candidate-Generation Capacity Evidence Manifest v2

This manifest proposes a capped protected-only offline capacity-label slice for candidate generation. It does not run labels or authorize selector behavior.

## Decision

- status: `candidate_generation_capacity_evidence_manifest_ready`
- labels_run_by_this_artifact: `False`
- selector_allowed: `False`
- recommended_next_step: `review_or_run_bounded_offline_capacity_labels`

## Summary

- candidate_pool_count: 23
- job_count: 12
- job_cap: 12
- job_count_by_stage: `{'stage4': 3, 'stage5': 5, 'stage6': 4}`
- job_count_by_provider_family: `{'edge_trap': 6, 'stage0_basin': 6}`
- stage7_job_count: 0

## Jobs

- `job.krk.cg_capacity_v2.75ae33a275f1` stage=`stage4` provider=`krk.stage0_basin` family=`stage0_basin` move=`f6f7`
- `job.krk.cg_capacity_v2.205639284e23` stage=`stage5` provider=`krk.edge_trap_close` family=`edge_trap` move=`h7c7`
- `job.krk.cg_capacity_v2.36f95a84102d` stage=`stage6` provider=`krk.edge_trap_close` family=`edge_trap` move=`h7c7`
- `job.krk.cg_capacity_v2.a1d20c18ea0f` stage=`stage4` provider=`krk.stage0_basin` family=`stage0_basin` move=`b7b1`
- `job.krk.cg_capacity_v2.4c4a0a90354b` stage=`stage5` provider=`krk.edge_trap_enemy_between` family=`edge_trap` move=`h7c7`
- `job.krk.cg_capacity_v2.89cb2ec1f824` stage=`stage6` provider=`krk.edge_trap_enemy_between` family=`edge_trap` move=`h7c7`
- `job.krk.cg_capacity_v2.141862dde05b` stage=`stage4` provider=`krk.stage0_basin` family=`stage0_basin` move=`d6c7`
- `job.krk.cg_capacity_v2.2285c6bdb5ce` stage=`stage5` provider=`krk.edge_trap_wrong_tempo` family=`edge_trap` move=`h7c7`
- `job.krk.cg_capacity_v2.2557dcb9229f` stage=`stage6` provider=`krk.edge_trap_wrong_tempo` family=`edge_trap` move=`h7c7`
- `job.krk.cg_capacity_v2.a4bbf1706a56` stage=`stage5` provider=`krk.stage0_basin` family=`stage0_basin` move=`a7a8`
- `job.krk.cg_capacity_v2.8df03270eb29` stage=`stage6` provider=`krk.stage0_basin` family=`stage0_basin` move=`a8f8`
- `job.krk.cg_capacity_v2.a29804da547d` stage=`stage5` provider=`krk.stage0_basin` family=`stage0_basin` move=`c6b6`

## Boundary

Jobs are forced-provider capacity labels only. They are not ownership labels, runtime inputs, score updates, guardrails, or promotion evidence.
