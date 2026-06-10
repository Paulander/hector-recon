# ReCoN/Hector Agent Instructions

## Active Goal

The active branch direction is `KRK Autogrowth v0`.

The goal is to prove or falsify that ReCoN can autonomously grow one useful topology addition from trace evidence that improves held-out KRK conversion, without learner-visible stage labels or hardcoded phase switches.

Historical report/control-plane work is archived under `archive/pre_autogrowth_2026_06_10/`. Treat it as background evidence only, not as active instructions.

## Operating Mode

- Optimize for learning progress, not for producing more review packets.
- Prefer executable code, training runs, metrics, and failing/passing experiments over documentation.
- If a plan is made, it should usually end in runnable commands, measurable checkpoints, and a commit-ready result.
- Agents may run local training/evaluation jobs for long periods when they are relevant, deterministic enough to inspect, and write outputs under the approved run-output paths.
- Do not stop at "needs review" unless the next action is genuinely unsafe, destructive, or blocked by missing information.
- Do not recreate the old report-gate loop. New reports should be minimal summaries of actual runs.

## Active Research Loop

The loop under test is:

```text
rollout ->
trace ->
mine before/action/after triplets ->
spawn candidate node/subgraph ->
sandbox candidate rollouts ->
assign credit ->
M3 fast update ->
promote or delete ->
M4 consolidate if promoted ->
evaluate held-out KRK ->
repeat
```

If a change does not move this loop forward, it is probably not branch-critical.

## Learner Vocabulary Boundary

Runtime/evaluation may use:

- Board state.
- Legal moves.
- Generic board features.
- ReCoN graph state.
- Learned node activations.
- Candidate node activations.
- Reward/conversion outcome.

The learner must not use:

- `Stage7` or `Stage8`.
- `box_shrink` or `opposition_tempo` as causal features.
- Provider source stage.
- Report row IDs.
- Selector-owner labels.
- Hand-authored curriculum labels.
- Runtime tablebase/DTM as a move provider.

Stage labels may still be used after the fact for diagnostics and evaluation slices, but not as learner-visible causes.

## Minimal Safety Rule

Safety belongs at the promotion boundary:

- Candidate growth may act in sandbox rollouts.
- A candidate may be promoted only if it improves held-out performance and causes zero protected regressions.
- Illegal moves, stalemates caused by the candidate, and baseline-safe regressions block promotion.
- Runtime tablebase/DTM and old selector behavior remain off unless a future experiment explicitly changes that rule.

Do not use safety language to prevent the learner from acting in its own sandbox.

## Default Work Cycle

1. Implement or adjust one piece of the autogrowth loop.
2. Run focused tests.
3. Run the smallest relevant training/evaluation job.
4. Inspect metrics and artifacts.
5. Update parameters or code.
6. Repeat until the checkpoint is clear.
7. Commit a coherent baseline when a checkpoint is reached.

Preferred checkpoints are metric checkpoints, not document checkpoints.

## Active Paths

- Current plan: `docs/autogrowth/KRK_AUTOGROWTH_V0_PLAN.md`
- Current brief: `docs/autogrowth/ACTIVE_BRIEF.md`
- Active run summaries: `reports/autogrowth/`
- Large run artifacts: `reports/autogrowth/runs/` or `snapshots/autogrowth/`
- Historical reports/tests/audit pack: `archive/pre_autogrowth_2026_06_10/`

## JavaScript Tooling

Prefer the repo's pinned Node runtime when running JavaScript tooling:

```text
/home/banquo/.nvm/versions/node/v20.20.0/bin
```
