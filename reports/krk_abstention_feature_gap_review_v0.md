# KRK Abstention Feature Gap Review v0

This review explains why the abstention-first selector is still not runtime-ready after the v1 label-count threshold was met.

## Accepted Result

- `row_count`: `51`
- `unsafe_owner_count`: `17`
- `best_objective`: `provider_family`
- `best_negative_suppression`: `0.17647058823529413`
- `best_safe_preservation`: `0.6176470588235294`
- `runtime_ready`: `False`

## Diagnosis

- Raw provider family/provenance is not enough to distinguish unsafe owners once selected-playout labels are included.
- The abstention gate now has enough examples by count, but it lacks state-local context features that explain why a normally useful provider is unsafe in a specific position.
- The next evidence object should join abstention labels to ControlPlaneEvidenceFrame terminal-space context, not collect more Stage7 repair traces.

## Required Feature Groups

- terminal_space_context: edge distance, box relevance, fence/cut state, rook safety, king support, mobility
- proposal_context: provider rank, normalized score, raw score gap, selected-vs-forced semantics
- monitor_context: local_provider_competition_failed, repair_needed_monitor, post_plan_stagnation where available
- label_semantics: selected_playout_success versus forced_provider_conversion separated at evaluation time

## Recommended Next Step

- Status: `join_abstention_labels_with_control_plane_context`
- Implementation allowed: `non_causal_replay_free_only`
- Artifacts: `['reports/krk_abstention_context_feature_dataset_v0.json', 'reports/krk_abstention_context_feature_dataset_v0.md', 'reports/krk_abstention_context_feature_probe_v0.json', 'reports/krk_abstention_context_feature_probe_v0.md']`
