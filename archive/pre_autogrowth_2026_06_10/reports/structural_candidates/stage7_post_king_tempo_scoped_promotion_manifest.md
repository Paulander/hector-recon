# Stage 7 Scoped Overlay Promotion Manifest

Candidate:

```text
cand.krk.box_shrink.post_king_tempo_continuation.v1
```

Status:

```text
validated_scoped_overlay
promotion_status: promoted_scoped
global_default: false
```

## Scope

This overlay is valid only under:

```text
domain: KRK
active_landmark_label: box_shrink
stage7_provider_scope_label: box_shrink
```

It must not be treated as a global KRK policy. The unscoped version solved
Stage 7 but measurably regressed the Stage 4 wrong-tempo guardrail.

## Added Visible Providers

```text
terminal.krk.stage7_king_tempo
terminal.krk.stage7_post_king_tempo
```

Temporal scope:

```text
stage7_king_tempo fires at most once per playout
stage7_post_king_tempo fires only after stage7_king_tempo and at most once per playout
```

Both remain opt-in and graph-visible. They do not make packets, stats, or
shadow candidates causal.

## Validation

Target:

```text
artifact: reports/structural_candidates/stage7_post_king_tempo_scoped_on_100_h40.json
Stage 7 box_shrink, 100 samples, horizon 40
mate: 100/100
shadow candidates: 0
improved: 100/100
local optimal: 49/100
```

Guardrail deltas versus controls:

```text
Stage 6 drive_to_edge: no regression
Stage 5 fence_established: no regression
Stage 4 edge_trap_wrong_tempo: no regression
```

Promotion evaluation:

```text
reports/structural_candidates/stage7_post_king_tempo_scoped_100_promotion_eval.json
promotion_status: promoted
```

## Interpretation

This is a successful Growth Monitor path:

```text
Stage 7 failure evidence
  -> StructuralCandidate
  -> legal-first follow-up diagnosis
  -> scoped visible sandbox provider
  -> target validation
  -> guardrail validation
  -> scoped promotion
```

The remaining local one-ply non-optimality is a calibration/plasticity issue,
not a composition blocker for this scoped profile.
