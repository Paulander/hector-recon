# TG26f Fence Boundary Rehearsal

Artifact: `reports/autogrowth/krk_autogrowth_tg26f_fence_boundary_rehearsal.json`

TG26f tests a narrow intervention: keep edge as a regression guard, but train
fence with separate unfiltered and boundary/near-miss rehearsal pools in
addition to filtered handoff positions.

This remains local ACTION-weight training over persisted curriculum pools. It
does not add a direct move provider, runtime tablebase/DTM source, learner-visible
stage labels, broad KRK, or ecological spawning.

Main run:

- seed: `20260615`
- edge/fence filtered train pool: 64 positions each
- fence unfiltered rehearsal: 32 positions
- fence boundary rehearsal: 32 positions
- heldout: 32 positions per slice
- train samples per chunk: 128
- chunks: 2

Edge regression guard:

- filtered: 21/32 conversion and handoff;
- unfiltered: 12/32;
- boundary: 4/32;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 110,814; M4: 0.

Fence result:

- filtered: 21/32 conversion and handoff;
- unfiltered: 2/32;
- boundary: 0/32;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 115,253; M4: 0.

Interpretation: edge stability is preserved. Fence unfiltered improves only
slightly over TG26e's 1/32, but boundary remains 0/32. Boundary rehearsal alone
does not solve the fence transfer problem. Fence is not competent. No broad KRK.
No M4 consolidation.

Next: inspect fence boundary failures and add a more informative local
feature/credit signal before another larger run.
