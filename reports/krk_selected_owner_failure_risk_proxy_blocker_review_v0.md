# KRK Selected-Owner Failure-Risk Proxy Blocker Review v0

## Decision

- status: `failed_proxy_closed_next_evidence_v1_required`
- next step: `build_selected_owner_failure_risk_evidence_v1`
- runtime work allowed: `false`
- selector training allowed: `false`

## Metrics

- discovery precision / recall / safe-preservation: `1.0` / `1.0` / `1.0`
- independent precision / recall / safe-preservation: `0.0` / `0.0` / `0.42857142857142855`
- false positives / false negatives: `4` / `1`
- label count: `8`
- Stage 7 readiness rows: `0`

## Interpretation

- The v0 proxy fit the discovery dataset but failed independent protected validation.
- The independent run produced false positives on safe-preservation cases and missed the only selected-owner failure-risk case.
- A one-ply selected move-shape proxy is insufficient as a runtime-review basis.
- The next evidence must expose visible competing-provider proposals or selected-owner progress-window failure, not forced-capacity labels alone.

## Blocked Path

- The v0 one-ply move-shape proxy is rejected as overfit to the discovery dataset.
- No runtime-review packet is authorized from this evidence.
- Future evidence must separate forced-capacity labels from visible ownership-failure risk.

## Next Evidence Tracks

- `visible_competing_proposal_evidence`: `alternative_provider_live_proposal`, `alternative_provider_role_licensed`, `alternative_provider_score_visible`, `same_state_provider_conflict_visible`, `provider_family_pair`
- `progress_window_failure_evidence`: `selected_owner_trace_available`, `selected_owner_no_edge_progress`, `selected_owner_no_mate_progress`, `selected_owner_repeated_abstract_state`, `selected_owner_no_progress_plies`

## Non-Causal Boundary

- No runtime selector behavior.
- No runtime terminals.
- No selector training.
- No Stage 7 promotion.
- No Stage 8 training.
- No runtime DTM/tablebase.
- No gameplay-time topology mutation.
