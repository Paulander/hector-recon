# TG26g Fence Boundary Local Signal

Artifact: `reports/autogrowth/krk_autogrowth_tg26g_fence_boundary_signal.json`

TG26g tests one local generic ACTION signal for fence boundary transfer. The
fence ranker receives additional post-move delta feature nodes:

- `post_move_confinement_delta_sign`
- `post_move_black_edge_distance_delta_sign`
- `post_move_black_mobility_delta_sign`
- `post_move_white_king_distance_delta_sign`
- `post_move_rook_safe`

These are local ACTION features only. They do not choose moves directly, do not
use learner-visible stage labels, and do not introduce runtime tablebase/DTM or
a provider override.

Main run:

- seed: `20260615`
- edge/fence filtered train pool: 64 positions each
- fence unfiltered signal rehearsal: 32 positions
- fence boundary signal rehearsal: 32 positions
- heldout: 32 positions per slice
- train samples per chunk: 128
- chunks: 2

Edge guard:

- filtered: 21/32 conversion and handoff;
- unfiltered: 12/32;
- boundary: 4/32;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 110,814; M4: 0.

Fence result:

- filtered: 18/32 conversion and handoff;
- unfiltered: 3/32;
- boundary: 0/32;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 150,600; M4: 0.

Interpretation: the local delta signal nudges fence unfiltered from TG26f's
2/32 to 3/32, but boundary remains 0/32. The signal is not sufficient. Fence is
not competent. No M4 consolidation. No broad KRK.

Suggested pause: external audit before adding more mechanisms. The audit should
focus on why fence boundary states remain safe/no-progress despite filtered and
small unfiltered signals.
