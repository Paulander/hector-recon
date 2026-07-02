# CODEX HANDOFF BRIEF — Hector/ReCoN reset (2026-07)

You are joining mid-project after an external review. Read this file fully. Do NOT read
`docs/autogrowth/ACTIVE_BRIEF.md` except when a task below explicitly points you at a line in it —
it is a 290-line historical log whose format has been driving checkpoint-accretion behavior.
An external review document may be provided alongside this brief; treat it as reference, not as a task list.

## Project state, in three sentences

The repo contains three partial solutions that never met: (1) the Jan–Feb 2026 baseline learner on
`main` (delta-pattern actuators, GoalMemory basin backchaining, a baseline→ReCoN compiler),
(2) the native ReCoN runtime line TG26o–TG27b (FormalReConEngine, SUB/SUR/POR/RET, materialized
quorum SCRIPTs, causal ablations), and (3) the TG46+ clean-slate line (validated all-reply
evaluation, decoy discipline, frozen-artifact provenance) — which however runs on a flat argmax
scorer, not a ReCoN, and has known reward bugs. The mission is to MERGE these three assets, not to
extend any one of them. Roughly 80k lines of harness accumulated around a learner whose
representation got weaker; your job is to reverse that ratio.

## Non-negotiable working rules (anti-scaffold contract)

1. **Definition of done for any training task**: frozen-after-training learner beats the stated
   baseline on heldout behavior, with an ablation showing the learned structure is causal.
   "Artifact written", "tests pass", "run completes", "infrastructure pass" do NOT count as done.
2. **No new TG checkpoints.** Do not create new `TGxx` names, new `run_krk_tgXX_*.py` scripts, or
   new report-note documents. Work happens as ordinary commits on ordinary modules.
3. **Net-negative line budget for harness code.** Any PR adding harness/audit/pool/cache code must
   delete at least as many lines of existing harness code. Learner/representation code is exempt.
4. **One primary metric per task**, stated before you start, unchanged during the task.
5. **Modify existing modules instead of creating parallel ones.** New files require a one-line
   justification in the commit message explaining why no existing module could host the code.
6. **Multi-seed or it didn't happen**: any comparison you report runs ≥3 seeds. Differences inside
   seed noise are reported as "no effect".
7. **Do not read or load anything under `reports/autogrowth/pools/` or `archive/`** unless a task
   names a specific file. Several are tens of MB and will destroy your context.
8. Purity rules remain in force: no runtime tablebase/Stockfish/DTM move source, no Python
   selection logic beyond graph-requested actuator resolution, no learner-visible curriculum/stage/
   basin/tempo/opposition labels. Trainer-side validation and curriculum scheduling stay allowed.

## Where the three assets live

- **Feb baseline learner**: commit `2b8642c0` on `main`. Key files at that commit:
  `src/recon_lite/learning/baseline.py` (sensors as sparse readouts; actuators as sparse quantized
  Δ-sensor patterns; `GoalMemory`), `scripts/train_baseline_krk_chain.py` (stage-0 mate-in-1 →
  stage-1 backchaining via distance-to-goal-memory labeling), `scripts/baseline_to_recon.py`
  (compiler: Root→Hub→Legs, precond→actuator→postcond micro-scripts).
- **Native ReCoN runtime**: current branch, `src/recon_lite_hector/` (engine, nodes, graph) and the
  TG26o–TG27b modules `native_quorum_materialization.py`, `native_quorum_mate2_chaining.py`,
  `forced_chain_decomposition.py`, `native_foundation_scale_replay.py` in
  `src/recon_lite_chess/autogrowth/`.
- **Evaluation rigor**: `validated_reachability_expansion.py` (exact all-reply validation),
  the decoy/hard-decoy generators in `edge_killbox_curriculum.py` and
  `tg48a2_same_side_microstage.py`, and the frozen-parent hash/zero-delta checks.

## PHASE 0 — Hygiene and known-bug fixes (target: ≤2 sessions)

0.1 Create `docs/BRIEF.md` (≤40 lines): current mission, current task, current metric. This file
    replaces ACTIVE_BRIEF as the living doc. Never append history to it; overwrite it.
0.2 Fix the TG48a2 episode reward classifier in
    `src/recon_lite_chess/autogrowth/tg48a2_same_side_episode_training.py`:
    (a) `_foundation_response_for_board` (~line 604) must evaluate flags for the state actually
        reached / the move actually played — not OR over all legal moves. Keep the OR version as an
        explicitly renamed availability diagnostic if needed.
    (b) `_classify_endpoint` (~line 540): validated-entry endpoints take priority over
        `graph_positive_false_basin`; false-basin applies only when the selected trajectory's
        graph-positive assertion fails validation.
    (c) Separate "achieved entry" from "handoff available" as distinct reward channels.
    (d) `partial_only_near_basin` becomes a non-terminal, small-positive-or-zero shaping signal —
        not a −3 stop endpoint.
    (e) Replace whole-trajectory reward broadcast in `_credit_assignments`/`_apply_episode_credit`
        with contrastive episode credit: paired trajectories from the same start (learner-chosen vs
        alternative), credit assigned to the terminal-activation difference. This is the
        trajectory-level version of the TG46c pairwise fix.
    Acceptance: reward-channel audit shows a non-degenerate reward distribution; at least one
    positive (non-veto) affordance promotes; heldout episode success is no longer structurally 0.
0.3 In `m4_foundation_consolidation.py` `_select_promoted_keys` (~lines 395–409): the four fields
    `train/heldout/regression/all_reply_precision` are copies of one train-side number. Either
    compute them on their named splits or rename to `train_credit_precision` everywhere.
    Acceptance: no field name claims a split it isn't computed on.

## PHASE 1 — Feature diet + expressivity check (can run parallel to Phase 0)

1.1 Produce `docs/FEATURE_AUDIT.md` (≤60 lines): classify every learner-visible feature in
    `src/recon_lite_chess/autogrowth/features.py` and `SAFE_FEATURE_HUB_NAMES` in
    `terminal_substrate.py` as PERCEPT (direct board geometry) or COMPUTED-LOOKAHEAD (enumerates or
    pushes moves) or CONCEPT (hand-authored chess concept). Then remove CONCEPT features
    (`feature_hub_*` tempo/opposition/mating_net/stalemate_danger) and COMPUTED-LOOKAHEAD features
    (`rook_lateral_escape_available`, `white_king_controls_escape_band`) from the learner-visible
    space. They may survive as trainer-side diagnostics.
1.2 Retrain the TG46-style Mate-in-1/Mate-in-2 foundation on the dieted feature space, 3 seeds.
    Acceptance: Mate-in-2 heldout all-reply conversion ≥0.90 without concept/lookahead features.
    If it fails, report which removals caused the drop — that is a result, not a failure.
1.3 Expressivity memo (`docs/PRIMITIVES.md`, ≤50 lines, paper-and-pencil, no code): for opposition
    (incl. distance PARITY), rook-fence betweenness, killbox, and tempo/side-to-move interaction,
    write the minimal circuit over the planned primitive basis (AND/OR/XOR, threshold comparators,
    LAG). Where inexpressible (parity over scalar distance is the expected gap), propose a GENERIC
    primitive (e.g., parity terminal, betweenness comparator) — mathematically generic names only.

## PHASE 2 — The merge (the actual work)

Rebuild the first two curriculum rungs (Mate-in-1, Mate-in-2) as native ReCoN structure:

2.1 Resurrect Δ-sensor-pattern actuators from `2b8642c0` as actuator TERMINALs in the
    `recon_lite_hector` graph: an actuator encodes a desired sparse feature delta; when requested,
    it confirms iff some legal move realizes the delta (local resolution of delta→move is allowed
    mechanics; WHICH actuator is requested must be graph dynamics).
2.2 Resurrect GoalMemory as learned prototype/quorum basin terminals (TG26s→u pattern), materialized
    as quorum SCRIPTs in FormalReConEngine. No stored-FEN patterns; prototypes over the dieted
    feature space.
2.3 Implement AND-over-replies confirmation ONCE, as graph structure/formal semantics, not per-run
    harness logic: a mate-in-2 script confirms only if for every legal black reply the mate-in-1
    subgraph confirms. Trainer-side exact validation supplies training signal for a chain-confidence
    terminal (TG26v/TG26z pattern); document this as a formal extension in `docs/PRIMITIVES.md`.
2.4 Evaluate with the TG46-era harness: exact validated all-reply conversion, decoy + hard-decoy
    pools, frozen-artifact hashes, 3 seeds, plus one conventional baseline (logistic regression or
    small MLP over the same dieted learner-visible features) so the graph's contribution is
    measurable against an ordinary learner on identical inputs.
    Acceptance for Phase 2: native-engine graph reaches parity (±seed noise) with the flat scorer on
    Mate-in-2 heldout, with request/confirmation traces recorded and ablations causal.

## Explicit no-go list

New TG letters; new pool/cache formats; new audit documents; imagination/virtual frames; LAG
terminals; ecological spawning; TG48b/fence work; KQK/KPK — all parked until Phase 2 acceptance.
If you believe a no-go item is blocking, stop and say so instead of building around it.

## Reporting format

Per session: ≤15 lines in the PR/commit description — task, metric, result vs baseline, seeds,
ablation outcome, next step. No standalone markdown reports.
