# Phase 1.3 Primitives Memo

Basis: atomic terminals are bucketed/thresholded predicates over dieted `extract_learner_features`
percepts; composition is quorum `k-of-n` (`k=n` AND, `k=1` OR).

## Direct Opposition
Atoms: `king_delta_file_abs`, `king_delta_rank_abs`, `king_support_chebyshev_distance`, optional
`side_white_to_move` for ownership.
Quorums: `same_file_direct` = [`king_delta_file_abs=0`, `king_delta_rank_abs=2`], k=2;
`same_rank_direct` = [`king_delta_rank_abs=0`, `king_delta_file_abs=2`], k=2;
`direct_opposition_geometry` = [`same_file_direct`, `same_rank_direct`], k=1;
`direct_opposition_side` = [`direct_opposition_geometry`, side-to-move bucket], k=2 when needed.
Status: expressible; no gap.

## Distant Opposition
Atoms: `king_delta_file_abs`, `king_delta_rank_abs`, `king_support_chebyshev_distance`, optional
`side_white_to_move`.
Quorums: `same_axis` = [`king_delta_file_abs=0`, `king_delta_rank_abs=0`], k=1;
`even_distance` = [`king_support_chebyshev_distance=2`, `king_support_chebyshev_distance=4`,
`king_support_chebyshev_distance=6`], k=1; `distant_opposition_geometry` = [`same_axis`,
`even_distance`], k=2; add side-to-move bucket with k=2 when ownership matters.
Status: expressible. Distance-parity is the finite OR `dist=2 OR 4 OR 6`; no dedicated parity
primitive is needed because the OR quorum subsumes it.

## Rook Fence
Atoms: `rook_present`, `white_rook_file`, `white_rook_rank`, `white_king_file`,
`white_king_rank`, `black_king_file`, `black_king_rank`, plus `rook_distance_to_black_king_edge_line`
and `rook_fence_depth_relative_to_black_king_edge` as compact percept summaries.
Quorums: `rank_triplet(r,wk,wr,bk)` = [`rook_present=1`, `white_king_rank=r`,
`white_rook_rank=r`, `black_king_rank=r`, `white_king_file=wk`, `white_rook_file=wr`,
`black_king_file=bk`], k=7 for ordered triples where `wr` lies between `wk` and `bk`;
`file_triplet` is the analogous file-axis quorum; `rook_fence_between_kings` ORs all valid triplets,
k=1.
Status: expressible as a finite OR over coordinate buckets. Gap: compactness only; a generic BETWEEN
comparator would compress the circuit but is not required for expressivity.

## Killbox / Confinement
Atoms: `black_king_on_edge`, `black_king_nearest_edge_distance`, `black_king_corner_distance`,
`rook_present`, `rook_attacked_by_black`, `is_check`, `rook_fence_depth_relative_to_black_king_edge`,
and the eight `bk_neighbor_<dir>_available` atoms.
Quorums: `edge_pressure` = [`black_king_on_edge=1`, `black_king_nearest_edge_distance<=1`], k=1;
`corner_pressure` = [`black_king_corner_distance<=2`], k=1; `stable_rook` = [`rook_present=1`,
`rook_attacked_by_black=0`], k=2; `static_no_escape` = all eight neighbor-unavailable atoms, k=8;
`killbox_confinement` = [`edge_pressure`, `stable_rook`, `static_no_escape`], k=3.
Status: static confinement is expressible. Gap: behavioral mate safety still needs reply
confirmation, not more static boolean vocabulary.

## Mobility Restriction
Atoms: the eight retained `bk_neighbor_<dir>_available` atoms.
Quorums: `mobility_0` = all eight neighbor-unavailable atoms, k=8; `mobility_le_1` = same children,
k=7; `mobility_le_2` = same children, k=6; `mobility_restricted` ORs the selected task threshold,
k=1.
Status: expressible because neighbor availability atoms are retained; otherwise it becomes a
discovery target rather than a learner-visible legal-move-count feature.

## Confirmation Semantics
The one genuine formalism extension is mate-in-N confirmation: runtime must generate the opponent
reply set, spawn one subgraph instance per legal reply, and confirm only via an AND/quorum over all
reply-instance confirmations. This universal quantification over a runtime-generated set is distinct
from static boolean composition, which ReCoN already supports through thresholded terminals.
