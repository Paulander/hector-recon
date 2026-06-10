# KRK State-Local Paired Runtime Proxy Design v0

Non-causal design for visible proxy candidates. This does not add runtime terminals or selector behavior.

## Proxy Specs

### terminal.krk.selected_owner_failure_risk_proxy

- `type`: `visible_runtime_proxy_candidate`
- `status`: `proposed_proxy_not_runtime_authorized`
- `meaning`: The currently selected owner may be unsafe in this state-local context; a competing owner may need review.
- `candidate_visible_terms`: `current_selected_owner_provider_family, active_landmark_label, source_stage/profile scope, terminal_space_context buckets, selected_move_shape/post_move proxy terms, same-state competing provider proposal evidence if a future candidate set exposes it`
- `forbidden_terms`: `owner_a_positive, selected_playout_result, future h40 conversion result, DTM/tablebase label, forced-provider h40 result as direct runtime input`

### terminal.krk.safe_preservation_confidence_proxy

- `type`: `visible_runtime_proxy_candidate`
- `status`: `proposed_proxy_not_runtime_authorized`
- `meaning`: The selected owner is a protected/current-profile owner and should be preserved unless visible failure-risk evidence is strong.
- `candidate_visible_terms`: `selected owner is normal-routing owner, selected owner provider family/provenance/maturity, protected stage/profile scope, selected move safety/progress context, alternative is only capacity/proposal evidence unless normal selected failure is visible`
- `forbidden_terms`: `owner_a_positive, owner_b_positive, selected_owner_converted label, forced_capacity_positive label as direct runtime preference, DTM/tablebase label`

## Decision

- `status`: `proxy_design_ready_for_replay_free_validation`
- `runtime_work_allowed`: `False`
- `selector_training_allowed`: `False`
- `recommended_next_step`: `build_runtime_proxy_dataset_and_probe_visible_candidate_features`
