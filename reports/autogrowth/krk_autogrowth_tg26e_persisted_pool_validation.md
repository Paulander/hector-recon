# TG26e Persisted Pool Validation

Artifact: `reports/autogrowth/krk_autogrowth_tg26e_persisted_pool_validation.json`

TG26e persists six indexed pools with entry-level candidate metadata:

- `edge_filtered`
- `edge_unfiltered`
- `edge_boundary_near_miss`
- `fence_filtered`
- `fence_unfiltered`
- `fence_boundary_near_miss`

Each entry includes FEN, generator/slice type, acceptance reason, cheap and
deep candidate scores, best candidate action, handoff type, safety flags,
black reply for the best candidate when available, and cached feature/action
keys. The pool is schedule/evaluation data only; learner-visible features remain
generic and no provider override or runtime tablebase/DTM source is enabled.

Main run: 64 filtered train-pool positions per stage, 32 heldout positions per
slice, 96 train samples per chunk, 2 chunks.

Edge-trap:

- filtered: 21/32 conversion and handoff;
- unfiltered: 12/32 conversion and handoff;
- boundary: 4/32 conversion and handoff;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 82,869; M4: 0.

Fence-hold:

- filtered: 19/32 conversion and handoff;
- unfiltered: 1/32 conversion and handoff;
- boundary: 0/32;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 84,962; M4: 0.

Pool generation:

- edge filtered: 96/441 accepted, 245 no-handoff rejections;
- edge unfiltered: 32/45 accepted;
- edge boundary: 32/58 accepted;
- fence filtered: 96/1703 accepted, 543 no-handoff rejections;
- fence unfiltered: 32/80 accepted;
- fence boundary: 32/140 accepted.

Interpretation: edge generalization survived larger bounded validation. Fence is
improved relative to TG26d because unfiltered is now nonzero, but 1/32 is tiny
and boundary remains 0/32. Fence is not competent. No broad KRK. No ecological
spawning. No M4 consolidation.
