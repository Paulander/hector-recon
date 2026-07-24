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

## Epistemic Governance

Truth and identifiability outrank visible progress.

Before changing a scientific mechanism, state and freeze:

- one hypothesis and its strongest null;
- the learner-versus-laboratory information boundary;
- exactly one changed scientific factor;
- predicted outcomes by arm;
- a kill criterion;
- a compute/change budget;
- a frozen transfer test.

A negative result completes the work package. It does not authorize an automatic
repair, new feature, pool exclusion, curriculum change, or next mechanism. The
builder may not approve its own result. Viewed evaluation rows become
development data permanently. Retiring them from confirmation does not remove
them from the learning ecology; learner adaptation must replay the failure and
confirmation must move to fresh sealed rows.

Keep three tracks explicit and never transfer claims between them:

1. **KRK engineering:** tune freely to solve KRK; make no autonomy claim.
2. **Generic-core science:** freeze the learner and test developmental laws in
   randomized non-chess environments.
3. **Sealed confirmation/transfer:** fresh data, frozen code, independent
   execution and adjudication.

### Serialized organism identity

Raw pickle or compressed-pickle hashes establish transport integrity only for
the exact persisted blob. They are never semantic organism equality: equivalent
objects can serialize to different bytes because of construction and pickle
memo history. Semantic organism identity is the complete canonical continuation
manifest and its digest, together with explicit experiment/source/candidate/
polarity/topology/authority identities. A restored object is not required to
re-pickle byte-identically. Scientific harnesses must persist arms once, restore
those exact snapshots, and globally verify every arm's transport and semantic
identity before the first outcome is opened.

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

## CENTRAL, NON-NEGOTIABLE KRK Curriculum Doctrine

This is the core experimental strategy, not a convenience. It has been
rediscovered after repeatedly broadening the curriculum too early. Treat a
violation as an experimental-design defect; do not tune around it.

- Start one persistent **empty learned graph**: no KRK rules, learned weights,
  composites, action triplets, TG artifacts, or competence values. A literal
  node-free graph is not the target; ReCoN keeps only its task-generic embodiment
  (board sensors/features, legal-action interface, terminal world facts, clock,
  and generic spawning/plasticity machinery).
- Learn the ladder at high resolution, in order: Mate-in-1, Mate-in-2, edge
  killbox, same-side tempo, farther approach, edge drive, safe fence
  establishment, then broad KRK. Do not skip from the foundation to a broad
  position distribution.
- Do not advance because training rows were memorized. Advance only at 100% on
  hash-frozen, disjoint validation plus prior-rung regression, with protected
  safety and move-efficiency gates. Keep a final test untouched until the
  configuration is frozen.
- Mate-in-1 is grounded by an observed checkmate after ReCoN's own legal action.
  Mate-in-2 is rewarded when its successor is recognized by the mature,
  outcome-grounded Mate-in-1 child and that child emits consolidated value.
  Continue recursively outward. The trainer must never replace this handoff
  with forced-move labels, mate-distance labels, geometry reward, or a validator
  verdict.
- Curriculum geometry may schedule experience and evaluation slices only. Stage
  names and solution labels never enter learner records. Executing chess rules
  and exposing checkmate/stalemate/rook-loss facts is environment interaction,
  not a move oracle.
- Preserve the same graph snapshot between rungs. Alternate bounded structural
  growth, topology-frozen fast-weight equilibration, heldout consolidation, and
  causal promote/prune decisions. Replay mastered rungs before every outward
  advance.
- A result is not "from scratch, ReCoN-native" unless the artifact proves the
  zero-learned-state start, persistent graph identity, graph-selected actions,
  graph-owned child value/credit, actual topology growth, and absence of
  teacher/provider leakage.

The execution plan and exact evidence boundary are in
`docs/autogrowth/NATIVE_FROM_SCRATCH_KRK_PLAN.md`. Existing TG46b and TG26p are
precursors, not this proof: TG46b starts fresh but uses oracle-derived positive
moves; TG26p uses a native graph but supplies trainer-side reward labels and
evaluates on its curriculum positions.

## Candidate Node Direction

Do not create a parallel candidate-node lifecycle system unless there is a concrete reason the existing one cannot be tightened. The repo already has first-class structural-growth machinery under:

- `src/recon_lite_hector/nodes/stem_cell.py`
- `src/recon_lite_hector/learning/m5_structure.py`
- `src/recon_lite_hector/nodes/pack_template.py`

For the next KRK autogrowth work, treat `StemCellTerminal` / TRIAL / MATURE / PRUNED lifecycle as the candidate-node substrate to normalize and instrument. Keep relevance and outcome credit separate:

- Relevance/context fit: request exposure, activation, confirmation, parent locality, sibling contrast, context precision/coverage.
- Outcome valence/credit: positive/negative/neutral causal interventions and correlation evidence.

Correlation may nominate a candidate, but promotion/maturity requires causal intervention evidence. Negative causal credit should not automatically erase a relevant node; it may become a local suppressor/inhibitor under the same parent. Avoid global bypasses or hand-authored KRK tactical managers as promotion paths for autonomy claims.

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

## Credit and Confirmation Rules

- Runtime purity claim means learned behavior executes through ReCoN request/confirmation structure and respects the learner-visible feature boundary. The training/evolution machinery may be global, but should stay task-agnostic/content-blind where possible.
- While held-out KRK conversion is near 0/200, expose graded progress before adding broad new candidate families. Mate/no-mate alone is too sparse to guide growth.
- Prefer paired candidate-on/off rollouts for causal credit: same FEN, same opponent policy/seed, candidate enabled versus gated off.
- Separate selection from confirmation: M3 may update during training/selection chunks, but confirmation/promotion chunks must freeze M3. M4 may consolidate only from fresh confirmation evidence.
- Compare generated candidates against yoked random candidates with matched budget and shape when evaluating whether the miner adds signal.
- Offline tablebase/DTM labels may be used only for training/evaluation labels when clearly marked. Runtime tablebase/DTM move provision remains forbidden.
- Before treating repeated failures as proof that learning failed, check the expressivity ceiling: exact ReCoN runtime semantics must be able to express the target policy. Hand-authored topology is an expressivity control only, not autogrowth evidence.

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

- Central curriculum plan: `docs/autogrowth/NATIVE_FROM_SCRATCH_KRK_PLAN.md`
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
