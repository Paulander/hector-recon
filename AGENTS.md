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

On `codex/residual-shadow-nomination`, also read
`docs/autogrowth/RESIDUAL_SHADOW_NOMINATION.md` and
`docs/autogrowth/LIVE_TRIAL_MATERIALIZATION.md`. `ShadowDevelopment` remains
isolated; the explicitly authorized `TrialDevelopment` extension attaches one
nominee after a fixed prefix, preserving history. It uses ordinary actor credit,
stops shadow updates and keeps the new condition in TRIAL. No maturity claim.
For the current randomized-access extension, also read
`docs/autogrowth/TRIAL_USEFULNESS.md`. Its internal permission terminal gates one
trial before action selection. Disabled trials receive no action credit; all
assigned outcomes enter the comparison. The resulting signal does not yet choose
or retire structures. Original experimental classes remain unchanged controls.

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

This branch implements residual-ranked nomination and prospective shadow testing.
Its first three-seed result is in `docs/autogrowth/RESIDUAL_SHADOW_NOMINATION.md`:
actor behavior/state stayed identical to controls; ranking beat random in one
seed, chose the same candidate in another and slightly lost in the third.
Do not claim reliable ranking superiority or causal usefulness from this result.

One live TRIAL is now implemented and tested; read
`docs/autogrowth/LIVE_TRIAL_MATERIALIZATION.md`. All 4,224 planned actual moves
completed. Validation none/ranked/random: 126/126/128, 93/101/101 and 66/66/66.
The seed 2 AND condition changed 54 evaluation moves when masked, with a net
10-mate loss; ranked/random selected the same condition there. This confirms a
useful live composition in that policy, not reliable ranking superiority. No
retirement or maturity occurred; history continuity passed focused tests.

The internal randomized use/no-use mechanism is implemented and tested; read
`docs/autogrowth/TRIAL_USEFULNESS.md`. All 151 focused tests and 7,296 planned
actual moves completed; old controls reproduced exactly. Half-time probing
reduced or matched final chess performance, and short online estimates did not
establish reliable usefulness discrimination. Seed 2's probed policy scored 94,
but an offline masked clone scored 117. Do not turn that offline finding into a
coach-selected removal or claim it as an autonomous score.

Next bounded target: a matched recovery run with a fixed additional normal-access
training interval before adding a controller. The exact scope is in that document.
Keep always-enabled training as the reference. Do not promote 50% probing or treat
positive correlation, prediction accuracy or activation as causal maturity.
Experience and optimization also matter. Test learned child competence and parent
delegation separately in a tiny two-context/two-child environment before using M1
as an M2 child. Neither automatic rate regulation nor handover is implemented.

## Focused verification

Use Python 3.12 and run:

```bash
PYTHONPATH=src:libs/recon-lite/src python -m pytest -q \
  tests/autogrowth/test_trial_usefulness.py \
  tests/autogrowth/test_trial_usefulness_experiment.py \
  tests/autogrowth/test_live_trial.py \
  tests/autogrowth/test_live_trial_experiment.py \
  tests/autogrowth/test_residual_shadow.py \
  tests/autogrowth/test_residual_shadow_experiment.py \
  tests/autogrowth/test_mate_one_attribution.py \
  tests/autogrowth/test_terminal_development.py \
  tests/autogrowth/test_mate_one_coach.py \
  tests/autogrowth/test_native_local_interaction_v27.py \
  tests/test_intrinsic_credit.py \
  libs/recon-lite/tests/test_formal_choice.py \
  tests/test_fanin_terminals.py
```
