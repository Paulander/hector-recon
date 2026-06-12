# TG26d Handoff Filter Validation

Artifact: `reports/autogrowth/krk_autogrowth_tg26d_handoff_filter_validation.json`

TG26c artifact integrity is verified. The canonical main artifact is parseable
full JSON: 3,343,251 bytes, schema
`krk_autogrowth_tg26c_edge_fence_handoff_curriculum.v0`, sha256
`50e6cb6eecb52f9ddddff6a61b8ac665f162dedd1333ce640b2a342720844d6a`.

The handoff filter is curriculum scheduling, not stage competence. TG26d
therefore evaluates three slices separately:

- filtered train-like heldout: same filter as training;
- unfiltered curriculum heldout: same generators without handoff requirement;
- boundary/near-miss heldout: cheap-safe/plausible positions with no immediate
  handoff candidate found.

Main bounded run: 40 filtered train-pool positions, 80 train samples per chunk,
12 heldout positions per slice, 2 chunks.

Edge-trap:

- filtered: 4/12 conversion and handoff;
- unfiltered: 6/12 conversion and handoff;
- boundary: 1/12 conversion and handoff;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 68,356; M4: 0.

Fence-hold:

- filtered: 7/12 conversion and handoff;
- unfiltered: 0/12;
- boundary: 0/12;
- safety: 0 rook loss, 0 stalemate, 0 illegal, 0 confinement regression;
- M3 updates: 69,184; M4: 0.

Interpretation: partial edge generalization signal, fence runway-only signal.
No edge/fence competence claim. No M4 consolidation.

Throughput: on-demand 80/24 and 160/48 TG26d validation runs were stopped after
several minutes. Fence filtered train-pool acceptance was 40/630 attempts
(6.35%), with 191 no-handoff rejections. The next checkpoint should persist or
index handoff-eligible and boundary/near-miss pools before scaling.
