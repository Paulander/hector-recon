# KRK Stage 4 First-Move Contrast Runtime Review Packet v0

## Decision

- status: `stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval`
- runtime_review_ready: `True`
- implementation_authorized_by_this_packet: `false`
- requires_explicit_approval_before_implementation: `true`

## Evidence

- sequence_candidate_status: `stage4_first_move_ranking_gap`
- feature_review_status: `stage4_first_move_feature_contrast_found_single_state`
- stratified_validation_status: `stage4_stratified_contrast_validation_supports_first_move_ranking_gap`
- stratified_gap_variant_count: `4`
- positive_terms: `['king_destination_c_file', 'rook_mid_rank8_cut_candidate']`
- failure_terms: `['king_destination_a7', 'rook_far_rank8_drift_candidate']`

## Approved Scope If Later Explicitly Authorized

- default-off Stage 4 first-move contrast sandbox only
- CandidateMoveFrame legal first-move hypotheses only
- no exact-state or exact-move runtime exception
- no selector, provider suppression, broad stage0 penalty, Stage 7 promotion, or Stage 8 training

## Risks

- Evidence is synthetic/symmetry-stratified, not broad random KRK coverage.
- The scope is Stage 4-specific and must not become a general selector.
- Forced-first-move conversion labels are contrast evidence, not ownership labels.
- A broad penalty on stage0_basin would risk protected safe-preservation behavior.

## Boundaries

- This packet does not implement or authorize runtime behavior.
- A later explicit approval is required before any sandbox code is added.
