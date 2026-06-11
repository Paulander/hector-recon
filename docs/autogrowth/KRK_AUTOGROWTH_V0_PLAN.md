# KRK Autogrowth v0 Plan

## Verdict Driving This Reset

The ReCoN direction is still worth testing. The previous branch workflow is not. It accumulated a control-plane-first posture: many mechanisms were represented, reviewed, and blocked from acting, while direct evidence of learned structural KRK improvement stayed weak.

This branch resets the work queue around a minimal causal learner.

## Research Question

Can ReCoN autonomously grow one useful topology addition from traces that improves held-out KRK conversion, without learner-visible stage labels or hardcoded phase switches?

## Mechanism Under Test

The minimum real loop:

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

## Arms

Run three arms:

- Arm A: protected baseline, all quarantined mechanisms disabled.
- Arm B: sham growth, same pipeline but compiled no-op candidate.
- Arm C: autogrowth, one trace-derived candidate may change behavior in sandbox and after promotion.

Only Arm C may change behavior.

## Data

Training:

- 200 generated legal KRK positions.
- White to move.
- Kings non-adjacent.
- Rook present and legal.
- Not already mate/stalemate.
- Exclude immediate mate-in-1.
- Exclude positions appearing in archived reports/snapshots/traces where practical.
- Bias toward nontrivial conversion rather than easy edge mates.

Held-out:

- 200 generated legal KRK positions.
- 100 weakness-zone positions.
- 100 broader random legal positions.
- Lock seed before running learner.

Offline tablebase/DTM labels may be used as training/evaluation labels if needed, but never as runtime move providers.

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

## Implementation Milestones

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
