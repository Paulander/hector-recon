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

Next candidate: one adaptive residual-ranked nomination mechanism in shadow mode,
compared with matched random proposals. Do not assume added topology is the cause
or cure of weak performance; experience/exploration order and optimization also
matter. Test learned child competence and parent delegation in a tiny
two-context/two-child environment before using M1 as an M2 child.

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
