# ReCoN/Hector agent instructions

`main` is the official restart line from 2026-09-06. The active claim is narrow:
the M1 learner respects the terminal observation/action boundary and receives only
action-bound scalar outcomes. It has not demonstrated adaptive topology growth,
strategic competence, handover, full KRK or a learned world model.

Read these current documents before changing the learner:

1. `docs/autogrowth/ARCHITECTURE_CONSTITUTION.md` — enduring architecture and
   information boundary.
2. `docs/autogrowth/OFFICIAL_CONTINUATION_20260906.md` — restart decision,
   accepted review findings and next tests.
3. `docs/autogrowth/MATE_ONE_COACH.md` — runnable terminal M1 substrate and
   bounded engineering evidence.
4. `docs/autogrowth/LEARNING_SEQUENCE.md` — implementation order, concurrent
   learning and future operating profiles; identifies the isolated work branch.

`CODEX_HANDOFF_BRIEF.md`, `docs/BRIEF.md`, TG/V plans, phase reports and archived
runners are historical evidence, not live instructions. Consult them only for a
specific reuse or failure-mode question. Git history preserves the longer agent
rules replaced here.

## Non-negotiable boundary

- The environment owns the chess board, legal transitions and outcome grading.
- Input terminals alone measure declared feature coordinates. Output terminals
  alone translate a selected binding into a real primitive action.
- The graph chooses the action. Do not hide a scorer, solver, mate predicate,
  correct-action lookup, after-state evaluator or authored chess strategy behind
  a terminal or opaque wrapper.
- Training feedback is the result of the submitted behavior, bound to its event
  and action. Current M1 uses +1 for actual checkmate and -1 otherwise.
- The coach may choose exercises and log outcomes. During training it must not
  inspect graph topology, activations, virtual states or hypotheses to decide
  reward, growth, consolidation, pruning or action.
- Offline tests and scientific interventions may inspect internals. Keep those
  out of the learner's inputs and label their results as analysis.
- Terminals are leaves. Shared sensor code is permitted only when separate
  request, binding and frame semantics remain equivalent to separate terminals.

The fixed feature schema may contain heterogeneous Boolean, bounded-integer and
other declared scalar coordinates. Geometry is explicitly allowed. A terminal
may read a sparse subset. Report strong task-specific measurements honestly;
“per-terminal sparse” does not imply sparse population coverage or a general
representation.

## Correct terminology

- `action_choice` confirms that one action was selected. It is not goal success,
  competence, availability or transferable child value.
- Current conditions are randomly proposed and behaviorally weighted. Do not
  call this adaptive structural discovery.
- Participation and outcome correlation do not establish PROBATION, maturity or
  causal usefulness. Use prospective comparisons for those claims.
- Fast-to-slow transfer that preserves the effective sum is bookkeeping until a
  retention/interference experiment shows a behavioral effect.
- Physical graph vertices replicated across action bindings are not independent
  learned concepts. Report physical vertices and shared definitions separately.
- Python may implement generic local learning and birth laws. That is not
  cheating, but it is also not a graph-learned credit or growth policy.

## Development rules

- Young structures may act and learn. Scientific confirmation thresholds do not
  gate ordinary learning unless a specific experiment requires that freeze.
- Components may be useless marginally and useful jointly. Do not require an
  atom to prove individual value before composition.
- Preserve evidence when a hypothesis is pruned, materialized or reconsidered.
  A new storage identity must not erase applicable successes or failures.
- Do not activate a historical subsystem wholesale. Port the smallest compatible
  mechanism and recheck its complete information path.
- Keep ordinary work small: one mechanism or attribution question, focused tests,
  actual play when relevant, and an honest result. Do not build another audit
  bureaucracy around an untested learner.
- Viewed validation is development data. A final test stays unopened until a
  configuration is intentionally frozen, but this is an evidence rule rather
  than permission for the organism to learn.
- Checkpoint identity covers the actual runtime dependency set. Do not bind clean
  checkpoints to unrelated historical experiment trees.

## Immediate sequence

The saved M1 checkpoint already passed three read-only development ablations:
124/128 no-op, 75/128 without multi-reader contributions, and 4/128 without all
condition contributions. This shows behavioral dependence on learned condition
weights and added value from compositions. It does not show adaptive growth,
because condition birth was random and the atomic vocabulary was nearly covered.

The first matched comparison is complete; see
`docs/autogrowth/M1_GROWTH_ATTRIBUTION.md`. Online versus identical fixed random
conditions differed by 0, 0 and +2 mates out of 128 across three seeds. Mixed
versus atomic-only differed by -22, 0 and +51; there is no consistent superiority
claim. These are experimental controls outside the unchanged production learner.

Residual nomination, one live TRIAL, and an internal randomized-use probe are
implemented on the separate branch
`codex/residual-shadow-nomination`; see the exact commits, results and next step in
`docs/autogrowth/OFFICIAL_CONTINUATION_20260906.md` before starting new work.
Main intentionally retains the stable learner. Do not reimplement the experiment
or merge its controls into production by default.

Develop bounded experiments freely on the work branch. Preserve each protocol,
exact source identity and favorable/adverse results in commits. Update main's
status summary after a completed experiment. Tags are for deliberate stable
releases or major evidence milestones, not every trial; never move an old tag.
Test success, chess performance and architectural capability are separate claims.

The branch tests live materialization with preserved history and
ranked/random/no-addition behavioral controls. A TRIAL may act and learn before
scientific maturity is established. Predictive history stays separate from live
participation; after attachment it must not receive a second shadow update.
The use/no-use probe and fixed-topology controls passed their mechanism tests,
but neither became a default training improvement. Their complete favorable and
adverse evidence remains on the work branch and in the continuation document.
The longer ordinary-M1 run is now complete at
`ea74d8fff85409336a8e9c302a28941006ca7cb7`; read the latest branch result in
`OFFICIAL_CONTINUATION_20260906.md`. All 181 distinct focused tests and 13,056
moves completed in one attempt. Each of nine actors reproduced its historical
384-decision state, reloaded a private checkpoint and continued to 1,024 decisions.
Final none/ranked/random scores are 124/128/128, 124/124/124 and 66/66/66.
Seed 2's added policies improved from 98 to 124, and fall to 88 when masked
offline; its no-addition actor also reaches 124. Equal nominees and trajectories
are not independent evidence for ranking. Seed 3 stayed at 66 despite 24–28
further replacements. All added conditions remain live TRIALs, not mature skills.
The final test stays unopened; these are reused development results.

The investigation and capacity follow-up are now complete at
`1a67e292305183756a3d3fd15cf9dd556d28af99`; read the latest result in
`OFFICIAL_CONTINUATION_20260906.md`. All 194 branch tests passed. No formal support
or choice bug was found. Exact contradictory weight requirements prove limits
of the particular saved graphs, not of the growing learning process.
A subsequent 1,536-move probe changed ONLY the work-branch condition budget, 32
versus 64, with 256 more ordinary training decisions per actor. Seed 2 finished
124 versus 128; seed 3 escaped 66 to 111 in BOTH arms. Thus more ordinary play
can improve the existing process without a new mechanism or a larger budget.
More random capacity helped one selected case; adaptive structural selection is
still unproved. Main's learner/defaults are unchanged (its original default was
96 conditions, distinct from the small experimental budget).

Next replicate the matched capacity comparison on fresh seeds under a declared
complete training schedule before changing a learning law or adopting a profile.
Keep normal growth/pruning, exploration and scalar-outcome learning active.
A fixed-graph impossibility certificate does not require replacing the learner;
ordinary training changes graph and weights. Do not supply a hand-authored
composition, correct-action label or new controller because of a short plateau.
Offline diagnostic answers and fitted weights never enter training. Report real
training experience separately from evaluation and laboratory transitions.
Private checkpoints and favorable/adverse evidence are retained. Learned child
competence and parent delegation remain a separate tiny two-context/two-child
test before M2; no handover, learned world model or M1 mastery is established.

## Focused verification

Use Python 3.12 and run:

```bash
PYTHONPATH=src:libs/recon-lite/src python -m pytest -q \
  tests/autogrowth/test_mate_one_attribution.py \
  tests/autogrowth/test_terminal_development.py \
  tests/autogrowth/test_mate_one_coach.py \
  tests/autogrowth/test_native_local_interaction_v27.py \
  tests/test_intrinsic_credit.py \
  libs/recon-lite/tests/test_formal_choice.py \
  tests/test_fanin_terminals.py
```
