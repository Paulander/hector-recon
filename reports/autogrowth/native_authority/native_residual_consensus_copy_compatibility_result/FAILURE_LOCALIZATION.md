# Residual-consensus failure localization

This is one bounded, offline localization from source commit `1e277c9bbca856ef7fcf3ba31e2e3df52ff3662d`. It used only the completed result, 32 frozen source organisms, and already-viewed frozen rows. It did not rerun growth, restore a cell, mutate an organism, open new data, certify anything, or influence a decision. The complete per-cell and per-seed measurements are in `residual_consensus_failure_localization.json.gz` (SHA-256 `f10cb869d96816ee39c1cbcea9a72df8f04231325f7dd9f83a4fa385b9b0aa42`).

## Trace reconstruction

All 64 evaluation queries were reconstructed under the established frame-neutral semantic comparison. This produced 2,048 REAL/VIRTUAL checks (64 rows x 32 organisms), 1,024 full frozen-reference checks (32 certification traces x 32 organisms), and confirmed the completed package's 6,144 action/trace checks (64 rows x 32 seeds x 3 arms). The frozen package contains 32 certification-bearing prospective traces; its 64 viewed rows comprise 16 validation positives, 16 validation decoys, and those same 32 reference rows. Raw prospective activation therefore uses the exact 32 certification traces used by the completed gate.

## Primary localization

The answer is **B: recurring candidates were tombstoned before the opportunity counter could see them**. V2 state construction excluded discovery-time-pruned cells, so their exact member patterns could recur without entering the recorded opportunity counter.

| arm | nominated | mixed-pruned | mixed-pruned raw >=1 | mixed-pruned raw >=4 | recorded >=4 | shadow-only V2-rule count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| true residual consensus | 5,073 | 5,040 | 5,040 | 4,994 | 0 | 9 |
| responsibility deranged | 5,073 | 5,040 | 5,040 | 4,995 | 0 | 0 |
| hash priority | 4,787 | 4,565 | 4,561 | 4,388 | 47 | 66 |

Every one of the 14,933 nominated cells, including PRUNED cells and tombstones, has a JSON row recording members, width, fixed polarity, discovery supports and oppositions, structural state and prune reason, lifecycle-agnostic prospective activations, the four-activation threshold, and descriptive supporting/contradictory outcomes.

The retained-population calculation is explicitly post-hoc and non-scientific. True-arm shadow qualifiers yielded 288 positive and 28 false-positive classifications in aggregate, with maximum positive coverage at zero false positives of 0. Deranged yielded 0/0 and hash yielded 695/60, with maximum positive coverage at zero false positives of 23. No arm had a seed with zero false positives and at least 29/32 positive coverage. Thus the localization explains counter invisibility but does not rescue the scientific result.

## R0 persistent-state mismatch

Across all 32 seeds, the only transition with any difference was raw source -> normalized deepcopy baseline. The changed audit fields were `exact_state_sha256` and `serialized_state_sha256`; the changed exact components were `frozen_triplet_ids` and `graph_dict`; within the graph, only `triplet_nodes` changed. Exact per-seed before/after digests are retained in the JSON. Normalized baseline -> empty organism, empty -> after growth, after growth -> V2 wrapping, and wrapping -> serialization/restoration were all identical. The after-growth stage is a source-proven identity measurement—growth was not rerun and the preserved growth path does not read or write `organism.r0`.

Topology, weights, credit, and lifecycle digests were invariant at every stage, and completed R0 behavior remained 3,072/3,072. The mismatch is construction/serialization identity, not a semantic R0 change.

## Budget localization

True and deranged arms have exact per-seed equality in all 32 seeds for proposal slots, proposal slots by tuple width, unique tuples examined, and candidate-score evaluations.

Hash differs in exactly seed ordinals `5, 7, 11, 12, 13, 14, 16, 19, 23, 26, 27, 30`. Their respective round-2 requests rerouted from direct width-3 to context-plus-base width-2 are `35, 31, 35, 9, 35, 20, 31, 15, 35, 9, 22, 9`. In each case a hash-selected width-2 candidate matured after structural round 1. The active mature context changed the frozen round-2 grammar branch; total proposal slots stayed 3,072, while width opportunities, unique tuples, and score evaluations changed. Exact contexts and deltas are preserved per seed in the JSON. This records the completed gate mismatch without reinterpreting or repairing it.

## Architectural diagnosis

Discovery-time outcome-purity pruning does conflate structural relevance with prospective decision reliability here: mixed discovery outcomes caused structural tombstoning before prospective state construction, although direct member matching shows that thousands of those patterns recurred later. This is a post-hoc architectural diagnosis only, not a certification, rescue, replacement mechanism, or new experiment.
