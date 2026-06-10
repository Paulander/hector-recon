# Plasticity Balance Protocol

This note defines how ReCoN balances weight/plasticity learning, structural growth, preservation, and performance.

## Policy

Structural growth is slower than weight learning.

```text
First try existing structure.
Then try bounded weight/plasticity calibration.
Only then propose or sandbox new topology.
```

Decision logic:

```text
If forced/controlled use of existing topology works:
  treat as routing/weight/calibration problem first.

If forced/controlled use fails:
  treat as possible structural/capacity gap.

If performance is still improving under current structure:
  block new growth and continue settling.

If performance has plateaued and the same failure family repeats:
  allow structural candidate proposal.

If a candidate improves target but regresses protected guardrails:
  quarantine or require overlay composition.
```

## Growth Governor V0

Growth Governor v0 is metadata/reporting only. It must not alter runtime routing, training, or topology.

Tracked fields:

```text
episodes_since_last_structural_change
recent_conversion_rate_history
recent_shadow_candidate_rate
repeated_failure_family_count
route_conflict_rate
handoff_gap_rate
reward_contract_mismatch_rate
guardrail_pass_rate
weight_delta_magnitude
weight_saturation_rate
plasticity_improvement_slope
active_candidate_count
provider_maturity
promotion_status
```

Candidate/governor statuses:

```text
settling
needs_more_weight_training
structure_insufficient
growth_allowed
growth_blocked_by_cooldown
growth_blocked_by_guardrail
growth_blocked_by_active_candidate_limit
growth_blocked_by_improving_performance
```

Default rules:

```text
max_active_candidates_per_stage = 3
max_promoted_overlays_per_stage_before_settling = 1
require_candidate_resolution_before_next_overlay = true
block_growth_if_guardrails_regress = true
prefer_settling_if_conversion_rate_improving = true
require_repeated_failure_family_before_growth = true
```

## Topology Vs Weight Diagnosis

Candidate evaluation should not treat frozen-weight failure as topology failure.

Each structural candidate records:

```text
frozen_weight_probe_result
forced_oracle_probe_result
bounded_m3_warmup_result
bounded_m4_consolidation_result
guardrail_delta
weight_saturation
candidate_locality
candidate_complexity
```

Diagnostic labels:

```text
topology_absent
topology_present_untrained
topology_miswired
topology_overbroad
topology_underbroad
parameter_miscalibrated
provider_capacity_missing
consolidation_failure
expressive_but_untrained
trainable_candidate
quarantined_after_calibration_budget
```

Evaluation phases:

```text
Phase 0: static sanity
Phase 1: frozen-weight probe
Phase 2: forced/oracle probe
Phase 3: bounded plasticity warmup
Phase 4: bounded M4 consolidation probe
Phase 5: guardrail validation
Phase 6: promote/quarantine/reject
```

Do not reject a topology only because frozen weights fail. Do not promote a topology merely because unlimited tuning could make it work.

## Provider Preservation

Provider metadata includes:

```text
provider_version
source_stage
source_checkpoint
validated_profile
frozen_provider
overlay_provider
provider_maturity
plasticity_scope
can_m3_update
can_m4_consolidate
guardrail_status
```

Maturity states:

```text
candidate_high_plasticity
sandbox_medium_plasticity
settling_medium_plasticity
validated_low_plasticity
foundation_frozen
quarantined_no_plasticity
```

Default policy:

```text
validated/frozen providers:
  no mutation during later-stage training except explicit low-rate consolidation tests

new overlay candidates:
  plasticity allowed only inside sandbox/warmup

quarantined candidates:
  no causal influence, no consolidation

promoted overlays:
  enter settling phase before further structural growth
```

## Performance Guardrails

Growth audits must remain practical.

```text
diagnostic caches enabled for large validation
parallel workers for independent samples
thin validation for successes
full traces only for failures or targeted states
avoid exhaustive legal-first sweeps unless candidate specifically requests it
augment existing audit artifacts replay-free when possible
```

Audit artifacts should include performance metadata where available:

```text
wall_time
samples
workers
cache_hits_misses
engine_decisions
engine_ticks
teacher_features_calls
goal_distance_calls
worst_reply_reward_calls
trace_mode
```

If a new audit projects to hours, stop and add filtering/cache/parallelization first.

## Boundary

External tooling may:

```text
load artifacts
compile sandbox topologies
run validations
run guardrails
serialize candidates
promote/quarantine/reject
```

External tooling must not:

```text
become a hidden runtime router
alter move selection from metadata alone
mutate topology during gameplay
make HandoffPacket/stats/shadow candidates causal
```

The cognitive part starts when:

```text
ReCoN-visible monitor SCRIPTs emit candidate hypotheses with source terms.
```

Every `StructuralCandidate` must cite:

```text
source_monitor_script
source_terms
trigger_failure_classes
evidence_artifacts
causal_status = non_causal
```
