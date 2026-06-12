# KRK Autogrowth v0 Plan

## Verdict Driving This Reset

The ReCoN direction is still worth testing. The previous branch workflow is not. It accumulated a control-plane-first posture: many mechanisms were represented, reviewed, and blocked from acting, while direct evidence of learned structural KRK improvement stayed weak.

This branch resets the work queue around a minimal causal learner.

## Research Question

Can ReCoN autonomously grow one useful topology addition from traces that improves held-out KRK conversion, without learner-visible stage labels or hardcoded phase switches?

## Mechanism Under Test

The minimum real loop currently uses triplets because they are measurable and easy to audit:

1. Run protected baseline ReCoN on generated KRK positions.
2. Record traces:
   - generic board features
   - active terminals
   - legal action chosen
   - resulting generic board features
   - rollout outcome
3. Mine candidate triplets:

```text
before_feature_cluster -> action_or_action_schema -> after_feature_cluster
```

4. Spawn exactly one candidate ReCoN node/subgraph from the highest-credit triplet.
5. Activate the candidate in sandbox rollouts.
6. Use M3 fast plasticity to update local edge/action weights during sandbox evaluation.
7. Use M4 consolidation to persist the candidate only if it improves held-out performance.
8. Delete/quarantine the candidate if it fails.

Triplets are not the whole topological-growth space. Future stem-cell/TRIAL candidates may also be:

- stand-alone input TERMINAL sensors;
- shared sensor implementations used as a performance shortcut, if saved/real ReCoN topology preserves equivalence to each consuming SCRIPT owning its own terminal instance;
- local sensor-composition terminals such as AND, OR, and XOR;
- LAG/temporal terminals that compare a sensor value with prior tick values, enabling change detection, low-pass filtering, persistence tests, and derivative-like signals;
- small subgraphs/circuits built from these primitives and then attached locally under SCRIPT/ACTION parents.

These primitives are central to the long-term learning direction: the network should be able to discover useful intermediate sensors and temporal circuits, not only before/action/after triplet chains. They also complicate credit assignment, so they should be introduced as bounded TG subcheckpoints rather than mixed into the current fragment-chain curriculum run.

## Arms

Run three arms:

- Arm A: protected baseline, all quarantined mechanisms disabled.
- Arm B: sham growth, same pipeline but compiled no-op candidate.
- Arm C: autogrowth, one trace-derived candidate may change behavior in sandbox and after promotion.

Only Arm C may change behavior.

## Data

Training:

- TG25 foundation curriculum first: generated legal Mate_In_1 positions, then mechanically verified forced Mate_In_2 positions.
- Curriculum scheduling is the actual experience distribution. This is allowed training scaffolding, equivalent to progressive KRK exercises.
- White to move.
- Kings non-adjacent.
- Rook present and legal.
- Not already mate/stalemate.
- Stage/curriculum labels can select the exercise distribution and slice diagnostics, but must not enter learner-visible candidate features.
- After Mate_In_1 and Mate_In_2 are strong, continue into edge-trap/fence/cut/box positions before broader random KRK conversion.
- Exclude positions appearing in archived reports/snapshots/traces where practical.

Held-out:

- For foundation: separately generated Mate_In_1, mirrored/transformed Mate_In_1, and verified forced Mate_In_2 heldout sets.
- For broader KRK: 200 generated legal KRK positions, 100 weakness-zone positions, and 100 broader random legal positions.
- Lock seed before running learner.

Offline tablebase/DTM labels may be used as training/evaluation labels if needed, but never as runtime move providers.

## Foundation Curriculum Advancement

Curriculum is the training distribution, not a cheat. The trainer may select
progressively harder KRK exercises, while learner-visible records stay generic:
board/action/graph/outcome features only. Stage names, tactical names, and
curriculum IDs are schedule and diagnostic metadata, never causal inputs.

Mate_In_1 and Mate_In_2 are classification-like:

- Mate_In_1 correct move: immediate checkmate.
- Mate_In_2 correct first move: preserves forced mate over black replies; the
  second white move mates after the reply.
- Harsh wrong-move credit is acceptable because the correct action is sharply
  defined.

Edge/fence/cut/box stages must use graded reward, not flat non-mate failure:

- checkmate remains dominant;
- faster mate is better, but do not over-reward beating the declared ideal;
- reaching a previously solved earlier-stage region is positive;
- preserved/improved confinement is useful but lower priority;
- king approach is useful only when confinement/fence is preserved;
- repetition/no progress is bad;
- confinement regression or king escape is worse;
- stalemate, rook loss, and illegal/no-move are catastrophic.

Use ideal count `M` from curated curriculum, tablebase label, or evaluator only
as training/evaluation scaffolding. If actual count is `m`:

```text
reward = max(mate_reward_floor, R_mate - delta_moves * max(0, m - M))
```

Default starting values: `R_mate=1.0`, `delta_moves=0.02`,
`mate_reward_floor=0.3`. Clamp faster-than-ideal bonus to zero or tiny; if
`m < M`, assume the ideal label may be wrong.

Do not train each stage from scratch. A harder stage should learn:

```text
current harder position -> move into known earlier solved region ->
earlier learned Mate_In_1/Mate_In_2 structure finishes
```

Advancement should be chunked:

- train chunk: normally 500-2000 games when throughput permits;
- eval window: at least 100 heldout positions for production advancement;
- require two consecutive passing eval windows before advancing;
- allow early stop at 100% success for two consecutive windows;
- for harder/noisier stages, 90-95% success may be acceptable if justified.

Do not advance unless current stage passes, Mate_In_1 regression remains at
least 99%, Mate_In_2 regression remains at least 90-95%, rook loss/stalemate/
illegal regressions are zero, M3 updates are nonzero, and M4 consolidation
happens only after heldout confirmation.

Throughput rule for harder stages: split cheap and expensive credit. Score all
legal actions first with generic local safety/progress checks; reject or heavily
penalize rook-loss, one-reply rook-loss risk, stalemate, confinement regression,
and no-progress actions before deeper rollout. Run expensive all-reply
foundation-handoff checks only for a configurable top-K of plausible actions and
cache by FEN/action/ideal-count. Report cheap-scored, deep-scored, pruned,
safety-rejected, and cache-hit counts in the artifact.

## Metrics

Primary:

- h40 mate/conversion rate.
- h80 mate/conversion rate.
- max-plies failure count.
- illegal move count.
- stalemate/blunder count.
- protected baseline regression count.
- paired delta:
  - candidate succeeds where baseline fails
  - candidate fails where baseline succeeds
- graded non-terminal progress:
  - old curriculum reward component when exact stage/template is known
  - excess moves versus curriculum `optimal_moves` when applicable
  - box/confinement trajectory and box escape count
  - enemy king edge-distance trajectory
  - black mobility trajectory
  - king/rook coordination distance trajectories
  - repetition/fivefold and repeated-action metrics

Learning-specific:

- candidate nodes spawned
- candidate nodes promoted
- candidate activation rate
- positive-credit count
- negative-credit count
- M3 update count
- M4 consolidation event count
- deleted candidate count

If M3/M4 do not fire, the run fails as a learning experiment even if behavior improves.

## Credit Protocol

Selection/training and confirmation are separate.

1. During training/selection chunks, M3 may update fast weights and nominate candidates.
2. During confirmation chunks, M3 is frozen and candidate-on/off rollouts are paired by FEN and opponent policy/seed.
3. M4 may consolidate only from fresh confirmation evidence, not from a moving M3 target.
4. Passive activation is not causal credit. Credit requires a requested/started candidate, behavior-changing ACTION/inhibition/retry, after-terminal confirmation/failure, or measurable continuation effect.
5. Candidate generation should be compared against yoked random controls with matched candidate count, shape, and evaluation budget.

## Purity Boundary

The strict purity claim is runtime execution plus learner-visible feature discipline: learned topology must execute through ReCoN request/confirmation structure at runtime, without direct move override or hidden phase control.

Learning/evolution machinery may be global: trace miners, budget allocators, promotion evaluators, and random/yoked controls are allowed as instrumentation and candidate-management machinery. Do not pretend the whole learning process is purely local.

Curriculum labels, stage names/IDs, hand-authored tactical labels, provider labels, and report row IDs are diagnostic/evaluation-only. They must not enter candidate input features or learner-visible causal records.

Offline tablebase/DTM labels may be recorded as evaluation/training labels if clearly marked. Runtime tablebase/DTM move provision remains forbidden, and DTM-distilled runtime progress sensors require future explicit review.

## Expressivity Ceiling Control

Before interpreting repeated null results as a learning failure, establish whether the exact ReCoN runtime semantics can express a complete KRK-winning policy. A hand-authored KRK ReCoN topology is allowed only as an expressivity control. It must be quarantined from learner training data and cannot count as autogrowth evidence.

## Pass Threshold

Pass only if all are true:

- h40 conversion improves by at least +10 percentage points on held-out positions.
- h80 conversion improves by at least +5 percentage points.
- max-plies failures drop by at least 20%.
- protected safe-control regressions are zero.
- illegal moves are zero.
- stalemate/blunder regressions are zero.
- promoted candidate activates on at least 10% of held-out positions.
- at least one M3 update contributes to candidate scoring.
- M4 consolidation persists the candidate.
- sham-growth arm does not show the same improvement.

## Fail Threshold

Fail if any are true:

- Candidate does not improve held-out KRK.
- Improvement appears only on training/dev positions.
- Candidate uses hidden stage labels.
- Candidate only works through direct provider override.
- Selector sandbox changes behavior.
- Stage7 opt-in terminals are involved.
- M3/M4 never affect credit or promotion.
- Candidate causes any protected regression.
- Growth produces reports but no topology change.

## Disabled Artifacts

Disabled in this experiment:

- selector behavior sandbox
- selector-driven provider/move/score/routing changes
- Stage7 opt-in terminals/providers
- Stage8 training/overlay
- Plan Capsule causal routing
- runtime tablebase/DTM
- direct provider override
- gameplay-time topology mutation outside the sandbox/promotion process
- stage-label learner features
- old report-row IDs as training examples

## Topological-Growth Subcheckpoints

The `M` labels below are historical subcheckpoint names inside one larger milestone: **TG: learned topological growth works**. They are not separate research milestones. Future work should prefer TG checkpoint names when the work is about the same topological-growth objective.

### M0: Clean Reset Baseline

Done when:

- Old reports/audit pack/report-gate tests are archived.
- `AGENTS.md` points future agents at autogrowth.
- Core tests run without the old report-gate suite.

### M1: Feature Firewall

Implement a small feature module for learner-visible KRK state.

Allowed examples:

- king/rook coordinates encoded generically
- relative distances
- legal move metadata
- check/stalemate/mate outcome flags after rollout

Forbidden examples:

- `Stage7`
- `Stage8`
- `box_shrink`
- `opposition_tempo`
- provider source stage
- report row ID

Checkpoint:

- Unit test asserts forbidden names are absent from learner feature vectors and trace records.

### M2: Position Generator

Implement train/dev/held-out KRK generation with locked seeds.

Checkpoint:

- 200 train, 200 held-out positions generated reproducibly.
- No illegal, mate-in-1, stalemate, or adjacent-king positions.

### M3: Baseline and Sham Arms

Implement evaluation runner for Arm A and Arm B.

Checkpoint:

- Baseline and sham produce identical behavior except run metadata.
- Metrics JSON includes h40/h80 conversion and failure reasons.

### M4: Trace Mining

Implement trace collection and candidate triplet mining.

Status: implemented as non-behavior-changing evidence preparation.

Checkpoint:

- Candidate records are generated mechanically from traces.
- Candidate records include before/action/after summaries and credit evidence.
- No stage labels or archived report IDs appear in candidate records.

Artifacts:

- `reports/autogrowth/krk_autogrowth_m4_traces.json`
- `reports/autogrowth/krk_autogrowth_m4_candidates.json`
- Smoke variants with `_smoke` suffix.

Important boundary: M4 candidates are mined records only. They are not spawned, active, promoted, or allowed to change behavior until M5 sandbox wiring.

### M5: Candidate Sandbox

Compile exactly one candidate node/subgraph and evaluate it in sandbox.

Status: implemented for the selected M4 candidate.

Checkpoint:

- Candidate activation is logged.
- Candidate may affect sandbox behavior.
- Illegal/stalemate/blunder regressions are counted.

Current result:

- `reports/autogrowth/krk_autogrowth_m5_sandbox.json`
- Selected candidate activates on 150/200 held-out positions and changes behavior on 19/200.
- Result is a failure: 0/200 mates, 18 rook-loss regressions, no held-out conversion gain.

### M6: M3/M4 Wiring

Wire M3 fast updates and M4 consolidation into candidate scoring and promotion.

Status: implemented as sandbox scoring and promotion/deletion decision.

Checkpoint:

- M3 update count is nonzero when candidate receives credit.
- M4 consolidation event is recorded only on promotion.
- Candidate deletion/quarantine happens automatically on failure.

Current result:

- M3 updates fire when the candidate changes behavior: 19 updates at h40 and h80.
- M4 consolidation events are zero because the candidate fails promotion.
- Candidate is quarantined automatically for no conversion gain and safety regression.

### M7: Full Three-Arm Run

Run Arm A/B/C on locked held-out data.

Status: implemented for the current selected M4 candidate.

Checkpoint:

- One result JSON under `reports/autogrowth/`.
- Optional short summary markdown.
- Decision: promote, quarantine, or reset the growth mechanism.

Current result:

- `reports/autogrowth/krk_autogrowth_v0_experiment.json`
- Arm A baseline: 0/200 h40 mates, 0/200 h80 mates.
- Arm B sham-growth: identical to baseline.
- Arm C autogrowth sandbox: candidate activates but remains 0/200 h40/h80 mates and causes 18 rook-loss regressions.
- Decision: fail and quarantine the current candidate. This proves the v0 loop can act and reject a bad topology, but does not prove useful KRK improvement yet.

### M8: Multi-Candidate Growth Training

Run multiple mined candidates through lifecycle training with early structural exploration and M3 fast-credit feedback.

Status: implemented for the current M4 candidate pool.

Checkpoint:

- Multiple candidates are spawned from trace-mined topology records.
- Candidate experience, fast weight, credit counts, and lifecycle state are tracked.
- Negative credit suppresses future candidate choice through fast weights.
- Unsafe candidates are quarantined; safe candidates may mature.
- Held-out evaluation uses the best surviving candidate, if any.

Current result:

- `reports/autogrowth/krk_autogrowth_m8_training.json`
- Default run: 8 candidates spawned, 271 M3 updates, 8 candidates quarantined, no heldout candidate survives.
- Broader run: `reports/autogrowth/krk_autogrowth_m8_training_12c8.json`, 12 candidates spawned, 370 M3 updates, 12 candidates quarantined.
- Decision: the lifecycle loop is alive, but the current mined action schemas are unsafe/low-quality. More cycles alone are not the next lever; candidate mining/action construction needs better learner-visible risk evidence.

### M9: Normalize Existing Candidate Nodes

Do not create another candidate lifecycle beside the existing stem-cell/TRIAL machinery. The current repo already has candidate-node substrate in:

- `src/recon_lite_hector/nodes/stem_cell.py`
- `src/recon_lite_hector/learning/m5_structure.py`
- `src/recon_lite_hector/nodes/pack_template.py`

M9 is a constraint/instrumentation pass on that machinery.

Required split:

- Relevance stats: request exposure, activation count, confirmation count, parent locality, sibling contrast, context precision, context coverage.
- Credit stats: positive/negative/neutral correlation and positive/negative/neutral causal intervention.
- Survival stats: maturity, prune pressure, quarantine reason, last confirmation cycle.

Rules:

- Correlation may nominate a candidate.
- Relevance can keep a candidate alive locally.
- Maturity/promotion requires at least one causal intervention.
- Negative causal credit on a relevant node should inhibit or convert it into a local suppressor, not automatically erase the evidence.
- XP alone must not be the only survival score.

### M10: Local Survival Rules

Implement survival/maturity decisions under the candidate's current parent, not through global promotion bypasses.

For the KRK proof experiment, disable or mark non-causal:

- KRK box-method discovery as a promotion path.
- forced hoisting.
- perfect-success, survivor, extreme-failure, and sample bypasses.
- stage/provider labels as learner causes.
- random fallback outcomes credited to candidate nodes.

Survival matrix:

- high relevance + positive causal credit: mature locally and strengthen local edges.
- high relevance + negative causal credit: inhibit, suppress, or quarantine under the same parent.
- low relevance + positive credit elsewhere: keep dormant/local nursery only; do not globally promote.
- low relevance + neutral/negative credit: prune.

### M11: One Local Suppressor Experiment

Status: implemented for one learned local suppressor candidate using `StemCellTerminal` TRIAL state.

Do not broaden candidate types yet. Test exactly one candidate type:

```text
parent script/action leg
  existing sibling action
  learned suppressor terminal
```

The suppressor confirms when generic local context predicts bad continuation and inhibits only the sibling action under the same parent. It must not choose moves directly.

Bad continuation labels for trainer/evaluator only:

- rook captured within N plies.
- stalemate caused.
- no move/stall.
- no mate/progress within h40.

Learner-visible records must not use `rook_loss_risk`, `box_shrink`, `opposition_tempo`, stage labels, provider labels, or KRK tactical phase strings.

Pass the single suppressor experiment only if:

- KRK conversion improves on locked heldout KRK for a competence pass.
- rook-loss count drops by at least 50%.
- protected regressions, illegal moves, and stalemate/blunder regressions are zero.
- candidate trigger rate is at least 10%.
- removing the candidate returns behavior to baseline.

Current result:

- `reports/autogrowth/krk_autogrowth_m11_local_suppressor.json`
- The suppressor is represented as a TRIAL `StemCellTerminal` with local relevance/credit/survival stats.
- It suppresses only the mined sibling action and never returns a move.
- Heldout safety improves for the bad sibling: rook losses drop from 18 to 3, with 77 suppressions, zero illegal moves, zero stalemates, and no new direct move source.
- KRK competence is still not proven: mate conversion remains 0/200. Treat M11 as a local safety/topology checkpoint, not a solved-growth checkpoint.

### M12: Local ACTION Arbitration

Status: implemented as a safe-fail checkpoint.

This checkpoint allows learned move choice, but only through local ReCoN-style structure:

- candidate ACTION siblings under one local SCRIPT parent
- stem-cell/TRIAL relevance, credit, and survival stats on each ACTION candidate
- local weights updated from training rollout credit
- suppressor/risk terminals inhibiting unsafe siblings
- fallback to baseline when no local ACTION sibling survives

The harness may train local weights and evaluate outcomes. Runtime heldout behavior must not use an external move selector, direct move override, or tablebase/DTM move source.

Current result:

- `reports/autogrowth/krk_autogrowth_m12_local_arbitration.json`
- 12 M4 ACTION siblings were evaluated under local arbitration.
- Every trained ACTION sibling received negative causal intervention evidence, so the local survival gate made them non-selectable.
- Heldout arbitration selected 0 local ACTION moves, caused 0 rook losses, 0 illegal moves, and 0 stalemates, but also produced 0/200 mates.
- Decision: safe local-arbitration failure. The substrate can refuse unsafe learned actions, but the current M4 candidate generator is not producing competence-improving actions.

### M13: Candidate Generation Gate

Status: implemented as a safe-fail checkpoint.

This checkpoint tests whether candidate generation, rather than arbitration, is the bottleneck. It enumerates legal white training actions offline, rejects projected negative continuations, scores only generic progress/risk features, emits ReCoN-compatible ACTION candidates, and then evaluates them through M12 local arbitration.

Current result:

- `reports/autogrowth/krk_autogrowth_m13_risk_aware_candidates.json`
- 3,841 legal white actions considered.
- 316 actions rejected by projected negative continuation.
- 12 risk-aware ACTION candidates emitted.
- Local arbitration selected 0 heldout ACTION moves after training because the generated candidates still received negative causal intervention evidence.
- Heldout result: 0 rook losses, 0 illegal moves, 0 stalemates, but 0/200 mates.

Decision: safe candidate-generation failure. The current action-schema representation is too coarse: even candidates generated from safe-looking legal actions do not survive local rollout credit. Long training remains blocked until candidate representation becomes more discriminative or structural candidates include richer local context without direct move choice.

### M14: Context-Specialized ACTION Candidates

Status: implemented as a safe-fail checkpoint.

This checkpoint tests whether M13 failed because the candidate terminal context was too broad. It uses the same offline legal-action generation boundary, but each candidate terminal includes 18 generic before-context features and heldout arbitration uses exact-match activation.

Current result:

- `reports/autogrowth/krk_autogrowth_m14_context_specialized_candidates.json`
- 3,841 legal white actions considered.
- 316 actions rejected by projected negative continuation.
- 12 context-specialized ACTION candidates emitted.
- Local arbitration selected 0 heldout ACTION moves after training.
- Heldout result: 0 rook losses, 0 illegal moves, 0 stalemates, but 0/200 mates.

Decision: safe representation failure. Making one-step ACTION candidates more context-specific still does not produce competence-improving structure. The next checkpoint should test local multi-step SCRIPT/subgraph candidates rather than more one-step ACTION bucket variants.

### M15: Local Multi-Step SCRIPT Candidates

Status: implemented as a safe activation-fail checkpoint.

This checkpoint tests whether one-step ACTION candidates are the wrong structural unit. It generates local SCRIPT candidates with two sequential ACTION children, a generic before-context terminal, POR-like step ordering, and local stem-cell/TRIAL survival stats.

Current result:

- `reports/autogrowth/krk_autogrowth_m15_local_scripts.json`
- 3,841 first-step legal white actions considered.
- 12 local SCRIPT candidates emitted.
- Heldout SCRIPT starts: 0.
- Heldout SCRIPT steps: 0.
- Heldout SCRIPT completions: 0.
- Heldout result: 0 rook losses, 0 illegal moves, 0 stalemates, but 0/200 mates.

Decision: safe activation failure. Multi-step SCRIPT structure is now represented, but exact full-context script starts do not generalize to heldout. The next checkpoint should improve activation/generalization through reusable subconditions or script fragments without weakening local causal survival rules.

### M16: Reusable SCRIPT Fragment Readiness

Status: implemented as a partial-curriculum readiness checkpoint.

This checkpoint tests whether M15 failed because the entire before-context was too brittle. It converts exact M15 SCRIPT starts into local SCRIPT candidates confirmed by a reusable TERMINAL fragment over generic features:

- black king edge distance
- white king to black king distance
- white rook to black king distance
- white king to rook distance
- rook attacked flag
- check flag

The fragment confirms the SCRIPT locally through ReCoN-style structure. It does not choose moves directly.

Current result:

- `reports/autogrowth/krk_autogrowth_m16_script_fragments.json`
- 12 fragment-confirmed SCRIPT candidates emitted.
- Train replay starts: 11.
- Heldout starts: 10.
- Heldout steps: 12.
- Heldout completions: 2.
- Heldout result: 0 rook losses, 0 illegal moves, 0 stalemates, but 0/200 mates.
- Decision flags: `partial_curriculum_ready=true`, `broad_curriculum_ready=false`.

Decision: narrow partial-curriculum runway. Fragment generalization solves the zero-activation problem without heldout safety regression on the locked full set, but it does not move KRK conversion. Do not launch broad long training yet. The next checkpoint should run a bounded partial curriculum over these fragment-gated SCRIPT candidates and require rollback if rook loss, illegal moves, or stalemates reappear.

### TG17: Triplet-Chain Runway

Status: implemented as a bounded partial-curriculum gate.

This checkpoint makes the old triplet idea explicit again:

```text
before TERMINAL -> ACTION delta vector -> after TERMINAL
after TERMINAL -> local request/confirmation for another before TERMINAL
```

It also inventories old predefined-topology KRK runs as controls only. Those runs prove the supplied-topology path can learn useful KRK behavior, but they are not evidence that current autogrowth has solved topology discovery.

Current result:

- `reports/autogrowth/krk_autogrowth_tg17_triplet_chain_runway.json`
- 4 ready/formally validated legacy predefined-topology control runs found.
- 12 current fragment SCRIPT candidates represented as terminal-space triplets.
- 42 after-to-before chain edges found at chain distance <= 1.5.
- Current fragment result remains safe but incomplete: 10 heldout starts, 0 rook losses, 0 illegal moves, 0 stalemates, and 0/200 mates.
- Decision flags: `bounded_partial_curriculum_allowed=true`, `broad_curriculum_allowed=false`.

Decision: proceed to a bounded fragment-chain curriculum over activating local triplets only. This is not a broad KRK curriculum, and it is not a KPK/KQK transfer claim. The curriculum must preserve the current boundary: behavior-changing learning has to flow through local TERMINAL/SCRIPT/ACTION/stem-cell structure, with rollback on rook loss, illegal move, or stalemate.

### TG18: Bounded Fragment-Chain Curriculum

Status: implemented as a clean failure with rollback/quarantine.

This checkpoint runs the TG17/M16 runway as an actual bounded curriculum with three arms:

- protected baseline
- sham fragment-chain
- real fragment-chain autogrowth

Only the real fragment-chain arm can change behavior. It uses the existing fixed fragment SCRIPT/triplet candidates and chain edges; it does not add LAG, boolean composition, standalone sensor growth, selector behavior, runtime tablebase/DTM, or direct move/provider override.

Current result:

- `reports/autogrowth/krk_autogrowth_tg18_fragment_chain_curriculum.json`
- short summary: `reports/autogrowth/krk_autogrowth_tg18_fragment_chain_curriculum.md`
- 12 candidates and 42 chain edges.
- Training M3 updates: 16.
- Heldout h40 real chain: 8 starts, 10 steps, 1 completion, 10 M3 updates.
- Baseline h40: 0/200 mates, 2,600 repetition events, 0 rook losses.
- Sham h40: identical to baseline on mate/repetition/safety.
- Real chain h40: 0/200 mates, 2,574 repetition events, 2 rook losses.
- M4 consolidation events: 0.

Decision: fail and quarantine. TG18 produced a weak continuation signal by reducing repetition events, but it violated the safety gate with rook-loss regressions and did not produce heldout conversion. Do not run longer over the same fragment-chain representation. The next checkpoint should isolate LAG/temporal terminals to see whether local change detection improves activation precision and dead-loop avoidance without direct move choice.

### TG19: Isolated LAG Terminal Checkpoint

Status: implemented as a partial-continue safety signal.

This checkpoint adds one bounded temporal primitive to the TG18 fragment-chain runway. The LAG terminal compares before/after generic features for a candidate transition and may inhibit that local transition through RET-style structure. It does not rank actions, choose replacement moves, use tablebase/DTM, or add stage/box/opposition labels.

Current result:

- `reports/autogrowth/krk_autogrowth_tg19_lag_terminals.json`
- 12 candidates and 42 chain edges, matching the TG18 runway.
- Training LAG triggers/suppressions: 2; training M3 updates: 16.
- Heldout h40 no-LAG arm: 0/200 mates, 2 rook losses, 1 chain completion, 2,574 repetition events.
- Heldout h40 LAG arm: 0/200 mates, 0 rook losses, 0 chain completions, 2 LAG suppressions, 2,599 repetition events.
- Heldout h80 LAG arm: 0/200 mates, 0 rook losses, 0 chain completions, 2 LAG suppressions, 2,600 repetition events.
- M4 consolidation events: 0.

Decision: partial-continue only. LAG proves that a local temporal terminal can remove the known rook-loss regression without direct move choice, but it also suppresses the only observed completion and still does not move KRK conversion. The next checkpoint should improve local continuation construction or activation precision before any broad long training run.

### TG20: Local Continuation Retry

Status: implemented as a partial-continue conversion signal.

This checkpoint uses the TG19 safety evidence locally. When an active SCRIPT's completion action is inhibited by the LAG terminal, TG20 may retry another SCRIPT sibling under the same local parent on the same tick. The retry still uses local before-terminal confirmation, local SCRIPT/ACTION weights, and the same LAG terminal inhibition. It does not choose a move through an external provider, tablebase/DTM, or direct override.

Current result:

- `reports/autogrowth/krk_autogrowth_tg20_continuation_retry.json`
- 12 candidates and 42 chain edges, matching TG18/TG19.
- Training retries: 6; training M3 updates: 22.
- Heldout h40 LAG-only: 0/200 mates, 0 rook losses, 0 chain completions, 2,599 repetition events.
- Heldout h40 retry: 1/200 mates, 0 rook losses, 0 illegal moves, 0 stalemates, 1 chain completion, 2 retry successes, 2,584 repetition events.
- Heldout h80 retry: 1/200 mates, 0 rook losses, 0 illegal moves, 0 stalemates, 1 chain completion.
- M4 consolidation events: 0.

Decision: partial-continue. This is not KRK competence, but it is the first heldout conversion movement on the current autogrowth runway while preserving the TG19 safety gain. The next checkpoint should mine/reinforce safer continuation candidates from retry traces and test whether the signal scales beyond 1/200 without broad hand-authored curriculum or direct move choice.

### TG21: Local Retry-Edge Reinforcement

Status: implemented as a clean no-scale failure.

This checkpoint mines local retry edges from TG20-style training traces:

```text
LAG-suppressed active SCRIPT completion -> same-parent SCRIPT sibling retry
```

The mined edge is a local request/weighting signal only inside the retry context. It does not choose moves directly, does not access heldout during training, and does not use tablebase/DTM or provider override.

Current result:

- `reports/autogrowth/krk_autogrowth_tg21_retry_edges.json`
- 12 candidates and 42 chain edges, matching TG18-TG20.
- Train-mined retry edges: 4.
- Training retries: 6; training M3 updates: 22.
- Heldout h40 retry-edge arm: 1/200 mates, 0 rook losses, 0 illegal moves, 0 stalemates, 1 chain completion, 2 edge-bonus hits, 2,584 repetition events.
- Heldout h80 retry-edge arm: 1/200 mates, 0 rook losses, 0 illegal moves, 0 stalemates, 1 chain completion, 2 edge-bonus hits.
- Compared with TG20 retry: no mate gain, no completion gain, no repetition gain.
- M4 consolidation events: 0.

Decision: fail cleanly. TG21 proves train-mined local retry edges can be represented and activated without breaking safety, but they are behaviorally redundant on the locked heldout split. Do not run longer over the same edge-bonus mechanism. Inspect retry-edge transfer failure or change the local candidate representation before broad training.

### TG22: Retry-Event Diagnostics

Status: implemented as diagnostic-only evidence.

This checkpoint does not change behavior. It traces TG20/TG21 retry contexts and compares no-edge vs edge-weighted retry choices to explain why TG21 did not scale the TG20 signal.

Current result:

- `reports/autogrowth/krk_autogrowth_tg22_retry_diagnostics.json`
- 43 retry event records captured.
- 18 heldout no-edge/edge comparisons captured.
- 4 edge-bonus hits in heldout comparisons.
- 0 edge-bonus choice changes.
- 34 retry events had no local sibling available.
- 4 retry events were linked to completion/mate.
- Diagnosis: `retry_edges_redundant`.

Decision: do not tune retry-edge bonus and do not run longer over the same exact mechanism. The failure is not that the edge is absent; the edge fires but usually reinforces the same sibling already chosen, while the dominant failure mode is no local retry sibling. The next checkpoint should improve local continuation candidate construction or mine richer retry context terminals. A single isolated sensor-composition primitive is reasonable only if it directly addresses this retry-context gap.

### TG23: Retry-Context Candidate Expansion

Status: implemented as a clean precision failure.

This checkpoint responds directly to TG22's no-local-sibling finding. It mines additional train-only SCRIPT sibling candidates from retry contexts where the active SCRIPT was suppressed and no local sibling was available. These candidates are ordinary local ReCoN SCRIPT/TERMINAL/ACTION structures and compete only through the existing local retry path.

Current result:

- `reports/autogrowth/krk_autogrowth_tg23_retry_candidate_expansion.json`
- 8 expansion candidates mined from 6 train retry contexts.
- Combined candidate count: 20.
- Chain edges: 56.
- Heldout h40 base retry: 1/200 mates, 1 completion, 2 retry successes, 0 rook losses, 2,584 repetition events.
- Heldout h40 expanded retry: 0/200 mates, 0 completions, 1 retry success, 0 rook losses, 2,600 repetition events.
- Heldout h80 shows the same regression: base retry 1/200 mates, expanded retry 0/200.
- Training M3 updates: 39; heldout M3 updates: 16; M4 consolidation events: 0.

Decision: fail cleanly. TG23 proves the no-sibling gap can be filled mechanically, but ungated retry-context expansion worsens the only current conversion signal. The problem is not merely missing candidate count; it is missing precision in when new candidates should compete. Do not add more ungated retry candidates. The next checkpoint should either add a local context terminal/composition primitive for retry precision, or require stronger train support before expansion candidates can enter local competition.

### Future TG: Sensor/Circuit Growth Primitives

Status: direction recorded; LAG has one isolated TG19 checkpoint, TG20 local-continuation use, TG21 retry-edge transfer test, and TG23 shows ungated candidate expansion is too imprecise. AND/OR/XOR and broader sensor circuits are still not implemented in this runway.

Topological growth should not stay limited to triplet candidates. A mature ReCoN learner likely needs to spawn and test stand-alone sensors and minimal local sensor circuits:

- input TERMINAL candidates that read generic feature-space coordinates;
- AND/OR/XOR composition terminals over existing sensor outputs;
- LAG terminals over one or more prior ticks;
- small combinations of the above that can become SCRIPT-requestable context terminals.

Training may use a shared sensor implementation for performance. That is acceptable only if it is equivalent to per-SCRIPT terminal instantiation in the saved ReCoN graph or clearly marked as a performance compression of that topology.

Decision boundary: do not mix multiple primitive families into one broad curriculum run. Test one primitive family at a time with isolated metrics, and require behavior-changing use to stay mediated through local ReCoN TERMINAL/SCRIPT/ACTION/stem-cell structure.

## Long-Run Protocol

Agents should be willing to run multi-hour local experiments when useful. A valid long run must:

- write periodic artifacts under `reports/autogrowth/runs/` or `snapshots/autogrowth/`
- print enough progress to diagnose stalls
- include seed/config in the output
- produce a final metrics JSON
- be resumable or cheap enough to restart

Do not stop a run merely because it is long if it is producing useful metrics.

## Commit Rhythm

Commit at real checkpoints:

- reset baseline
- feature firewall
- generator
- baseline/sham runner
- trace miner
- candidate sandbox
- M3/M4 wiring
- full v0 experiment result

Do not commit every report. Commit code and metric summaries that define a new reproducible baseline.
