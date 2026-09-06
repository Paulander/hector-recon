# Residual nomination with prospective shadow predictions

Work branch: `codex/residual-shadow-nomination`, from main `47181307`.
Scope: one generic, internal nomination law and its prediction control. No live
promotion, pruning change, strategic handover or automatic learning-rate regulator.

## Mechanism and information path

The ordinary actor keeps its graph choice, random birth and scalar edge updates.
A generic no-op hook in `TerminalDevelopment` runs after choice and before the
actuator closes the observation frame. The branch subclass uses this hook to
request a disconnected shadow SCRIPT tree. Its leaves are ordinary typed input
terminals, reading only the selected binding. These are real observations, not
imagined moves. No shadow weight contributes to an actor edge or exploration.

At its first training action, the organism samples 64 distinct definitions with
the existing 1-to-3-coordinate AND/OR/exactly-one grammar and a separate RNG. No
atom needs individual usefulness before it can enter a composition. This pool is
random; selection from it is the experience-directed part of this experiment.
Definitions and statistics retain their identities throughout the run.

For each candidate, retain activation count, residual sum and a shadow coefficient.
The residual is the submitted action's scalar reward minus the actor's prediction
at selection time, with the exploration bonus removed. All candidates have the
same 64 discovery opportunities, but different actual activation counts.

After 64 completed actions, rank eligible candidates by
`abs(mean active residual - mean residual) * sqrt(active count)`, the small score
used in the historical generic `online_composition` module. Port only that idea:
the old active-atom input API and automatic maturity machinery are not imported.
Exclude definitions already in the live actor and require at least four active
and four inactive observations. This is support for estimating a hypothesis,
not a requirement that each constituent terminal be useful.

The highest score with a matching peer becomes the nominee. A random control is
drawn uniformly from its group: same arity, operator and activation-frequency
quartile during discovery. The winner remains eligible for random selection.
Report actual counts and whether both roles chose the same definition. This is
coarse support matching, not exact activation or physical-cost matching. If no
group has two eligible candidates, record `no_matched_pair`; never relax the rule
from observed results.

## Prospective comparison

Before each actual actuator execution, commit the actor prediction and each
candidate's augmented prediction (`actor + shadow weight` if active, actor
otherwise). After the corresponding scalar outcome, first score those committed
forecasts, then update each active shadow coefficient by
`0.3 * (reward - augmented prediction)`. The actor also keeps learning normally.

Nomination uses only the discovery prefix. The next 64 actions measure paired
squared-error improvement versus the same actor forecast, and ranked versus
matched random. Nomination cannot be changed by these outcomes. Coefficients keep
adapting equally; this measures subsequent online predictive performance, not a
frozen-model holdout and not a counterfactual reward for an unplayed action.
No score is clipped and no intermediate or alternative-action reward is created.

The shadows never alter behavior. A prediction improvement is not causal action
value, maturity, a useful live policy addition or generalization to new tasks.
It only earns a reason to test materialization in a later controlled experiment.

The first implementation explicitly supports one-action episodes. It rejects a
second learning action before feedback instead of inventing multi-step credit.
M2 will need a separate episode/eligibility extension. Evaluation never initializes
or updates shadow statistics; checkpoint continuation retains pending-action guards,
candidate history and independent RNG state.

## Fixed first-run budget, specified before chess outcomes

- Seeds 1, 2, 3. Existing development training pool: 256 M1 positions, seed
  20260905. Reuse its deterministic shuffled order, first 128 rows per seed.
- Actor: ordinary `TerminalDevelopment`, maximum 32 random live conditions,
  default edge learning/exploration, no frozen baseline. Default grace is 256,
  so the 128-action experiment ends before structural pruning can occur.
- Shadow: 64 random candidates, 64 discovery actions and 64 prospective actions,
  minimum active/inactive support 4, four support bins, learning rate 0.3.
- Matched no-shadow actor per seed, identical seed, exercise order and config.
  Require identical action/outcome digests AND final learned actor state.
- Six actor runs total, 768 actual White moves. Three worker processes; each
  complete seed pair has a 600-second bound. No automatic extension or tuning.
- Primary: each seed's prospective ranked-minus-random reduction in squared
  prediction error. Also report both against base, active support, nomination
  availability, random-equals-ranked cases, actual mates, graph cost and runtime.
- Do not open validation or final-test files. The prospective suffix is later
  actual training experience, not an independent mastery evaluation; symmetry
  orbits may span the two phases. No claim of independent row observations.
- Save protocol, source hashes, random definitions and schedule before play.
  Incomplete seed pairs do not enter a success summary. Preserve negative or
  unavailable nomination results; no automatic promotion from this report.

## Continuation

Run using the same Python 3.12 dependencies as `MATE_ONE_COACH.md`:

```bash
python scripts/autogrowth/run_residual_shadow.py --pool reports/autogrowth/runs/m1-coach-smoke-pool --output reports/autogrowth/runs/residual-shadow-seeds123 --seeds 1 2 3 --conditions 32 --candidates 64 --discovery 64 --prospective 64 --workers 3 --wall-seconds 600
```

Use a different output directory for a separately declared replication. The
entry point pins hash seed 0 and defaults numerical-library threads to one.
`--workers 1` gives the same behavior serially. Pool generation is documented in
`MATE_ONE_COACH.md`; do not silently generate different positions for comparison.

Tests are `tests/autogrowth/test_residual_shadow.py` and
`tests/autogrowth/test_residual_shadow_experiment.py`, plus the focused baseline
suite in `AGENTS.md`. They cover formal terminal compositions, zero marginal
signal with useful joint signal, reward-dependent nomination, discovery/prospective
separation, action-bound credit, inert shadows, serialization, opaque coaching,
actual-only board moves, untouched evaluation pools and serial/parallel parity.

Run focused tests before the fixed experiment. If the candidate selector earns
prospective evidence, the next implementation question is live materialization
with preserved history and a behavioral control. If it does not, diagnose the
nomination/update/support result before adding a larger regulator. Neither sign
alone establishes whether M1 needs more topology or more stable weight learning.

See [LEARNING_SEQUENCE.md](LEARNING_SEQUENCE.md) for concurrent learning and future
development/operation profiles. This experiment's phase split is a measurement
control, not the lifelong training schedule.
