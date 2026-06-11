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
