# Stage 7 Candidate-Move Layer Candidate Update

Schema: `stage7_candidate_move_layer_candidate_update.v1`

Status:

- Stage 7 remains `local_valid_composition_quarantined`.
- `cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1` is `local_family_repair_validated`.
- Promotion remains `sandboxed`; guardrails have not been run yet.

Result:

```text
25-sample default-off:
  12 mate / 13 max_plies
  local improved/optimal: 21/16
  shadow candidates: 23

25-sample enabled:
  16 mate / 9 max_plies
  local improved/optimal: 21/16
  shadow candidates: 15
  candidate role suggestions: 4
  e4d3:mate = 4
```

Interpretation:

```text
The ephemeral CandidateMoveFrame layer validates the 0926 visible move-shape
family repair without local one-ply regression on the paired 25-sample run.
It does not solve Stage 7 globally and must remain default-off.
```

Small guardrails:

```text
Stage 6 drive_to_edge 25 h40:
  25 mate / 0 max_plies
  candidate role suggestions: 0

Stage 5 fence_established 25 h40:
  20 mate / 5 max_plies
  local optimal: 25/25
  candidate role suggestions: 0

Stage 4 edge_trap_wrong_tempo 25 h40:
  22 mate / 3 max_plies
  local optimal: 25/25
  candidate role suggestions: 0
```

These guardrails show no candidate-role overfire outside the Stage 7 post-box scope. Larger guardrails are still required before any promotion decision.

Boundaries:

- Do not train Stage 8.
- Do not promote Stage 7.
- Do not create persistent topology nodes for legal moves.
- Do not add direct role-SCRIPT to provider SUB edges.
- Handoff packets, stats, shadow candidates, StructuralCandidates, GrowthGovernor records, and PlanCapsuleSpec records remain non-causal.
