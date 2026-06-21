# TG28i Short Staged Edge/Bridge/Foundation Rollout

Artifact: `reports/autogrowth/krk_autogrowth_tg28i_staged_edge_bridge_foundation_rollout.json`

TG28i is a bounded pass, not a broad KRK claim.

Result:
- `checkpoint_pass`: true
- `selected_training_schedule`: `tg28h_mixed_balanced_baseline`
- Foundation remained frozen: Mate_In_1 1.0, Mate_In_2 1.0, M3/M4 deltas 0/0.
- Frontier slice: 1/1 selected, 1 foundation handoff, 1 same-graph continuation.
- Generic edge/fence slice: 2/2 selected, success 1.0, rook blunders 0, stalemate failures 0.
- Staged generation: 2 accepted from 8 attempts, acceptance rate 0.25.
- Staged heldout: 1/1 selected first move, 2/2 S1 bridge selections, 2 foundation-reachable bridge responses, 2 same-graph foundation continuations, all-reply success 1/1.
- Near-miss slice was disabled in this bounded artifact (`near_miss_heldout_count=0`) to keep runtime tractable.
- Ablations were skipped in this bounded artifact (`max_ablation_positions=0`); TG28h remains the current ablation evidence for the component layers.

Interpretation:

The components can compose in a short controlled rollout:

generic edge/fence move -> black reply -> bridge/frontier move -> black reply -> frozen TG27b foundation response.

The added staged-training arms did not beat the TG28h mixed-balanced baseline in this tiny run. That is important: the pass shows sequential compatibility, not that staged examples have improved learning yet.

Next:

Build a persisted staged-predecessor pool before scaling. The forward filter can find staged examples, but generation is expensive and should not dominate future TG28i/TG28j runs.
