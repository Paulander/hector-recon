# Mate-in-one: play first, learn internally

Branch: `codex/mate-in-one-coach`, based on `b5fbd7b` (V27).
This is a fresh KRK engineering baseline using the existing native learner.
It imports no trained finisher, teacher policy, solved move table, or frozen
baseline. The initial learned graph contains one root and zero learned edges.

The clarified target is a numeric feature basis with spawned, learned projection
terminals. The current `BoardSensor` adapter does **not** implement that target.
The commands below remain runnable hybrid-reference experiments. The next
implementation is specified in
[Feature terminals, credit, and growth](FEATURE_TERMINAL_IMPLEMENTATION.md).

Initial smoke: 196 actual training moves produced 13 checkmates; the resulting
greedy policy solved 67/128 validation exercises with learning disabled, no
illegal moves, and no abstentions. These validation rows span 25 symmetry
orbits. The fresh greedy baseline abstained on all rows; it is not a random
baseline. This was less than one training epoch, not a mastery or replication
result. The reserved test remains unopened. See the
[measured smoke summary](../../reports/autogrowth/development/MATE_ONE_COACH_SMOKE_20260905.json).

## Information boundary

The coach presents a board through `BoardSensor.measure()`. The organism
receives piece locations and board clocks/turn, reconstructs its private rules
model, chooses one action, and receives feedback for that action. The coach
executes exactly that submitted move on the real board. Reward is +1 for
observed checkmate and -1 otherwise. A legal nonmate is `exercise_timeout`,
not a chess loss. This is explicitly coached mate-in-one feedback, which is
more informative than full-game win/loss feedback.

Only scalar reward crosses the feedback boundary, accompanied by the event ID
and already-submitted action for exact credit binding. `reason` remains in the
coach's move log. It is not a learner input. The earlier adapter passed that
unused diagnostic field; this interface correction removes it.

The published 67/128 result belongs to commit `c10164f8`, before that correction.
Source fingerprints deliberately prevent its checkpoint from resuming under
changed code. Use its original checkout to continue that reference run; start
a new run directory for this version. Do not remove the source check.

Only offline `prepare` checks whether candidate exercises have a mating move.
It writes FENs, split hashes, and counts; no answers. Training reads only the
training FEN file. Scheduling is shuffled repetition, independent of success,
graph contents, or imagined futures. Reflection/rotation equivalent positions
are assigned to the same split. Validation is a separate, nonlearning command.

The organism uses existing generated before/action/after triplets, finite
local UCB exploration, and M3 updates. Only its emitted action gets real
outcome credit. Its local credit engine consolidates slow values every 256
observed actions, using its own grounded outcome evidence. The coach neither
approves that step nor freezes the policy. These slow values are preparation
for child-value use; they do not yet control this one-level policy. This is
not causal structural-candidate promotion or a complete M5 lifecycle.

Sensors are shared read-only measurements. Saved native graph inputs are
leaf `TERMINAL` nodes queried by scripts. Sharing a measurement does not
authorize sharing mutable request/frame/binding state across independent
terminal contexts. Tests assert leaf terminal structure.

**Remaining learner limitations are explicit:** the inherited implementation
still enumerates legal actions and simulates their successors in Python,
constructs scores, then uses an anonymous formal choice graph to emit an
action. It retains the native raw/geometric feature vocabulary, including
king/rook relationships; it is not a raw-square-only learner. Hand-authored
shared projection conjunctions, grouped cache terminals, action-only scoring,
and hierarchy-edge scoring are disabled in this profile. Merely wrapping it
does not move all control into persistent ReCoN vertices. Known chess rules
are supplied; no claim is made that the transition rules were learned.
Internal hypothetical board evaluation is permitted; the coach never sees it.

## Fixed first experiment

- Hypothesis: this fresh learner can improve unseen mate-in-one behavior from
  repeated selected-action feedback without coach access to its graph.
- Strongest null: it memorizes local choices while held-out behavior stays
  poor, or exploration/representation prevents useful improvement.
- Profile: the constructor in `coach/native.py`, unchanged throughout a run.
  This restart establishes a baseline; it is not a one-factor causal comparison
  with V27, whose initialization, training contract, and profile differ.
- Replicates: same 256/128/128 pool and code; training-order seeds 1 and 2.
  Both arms should improve if the claim is robust. Seed order, not a different
  feature package, distinguishes the two computers.
- Budget per replicate: 20,000 total attempts, up to eight hours per invocation.
  The wall limit checkpoints a partial run; resume to the same total target.
  No automatic new mechanism, parameter sweep, or curriculum expansion follows.
- Check behavior at 2,000, 10,000, and 20,000 attempts with separate validation
  commands. These viewed positions are development data, not sealed confirmation.
  Training always ignores the results. Compare greedy evaluation with its
  zero-attempt baseline; training statistics include exploration.
- Stop this profile after the fixed budget if held-out behavior remains poor.
  Report a negative/inconclusive result and investigate the learning trace
  offline; do not add answer labels or inspect virtual states to shape rewards.
- Do not advance to mate-in-two on training memorization. Require 100% on the
  frozen validation exercises in both replicates, then a fresh confirmation
  exercise pool after freezing code. A finite test is not proof over all KRK.
  The reserved test below is a final internal check, not independently adjudicated
  generic-core transfer evidence. Opening it freezes that run for training.

Mate-in-two is deliberately a later exercise implementation: exact M2 gives
two own moves with an actual opponent reply. Three own moves would be a named
relaxed exercise. No imagined mate label or arbitrary ten-move cap substitutes
for observed success. Broad KRK, learned module selection, longer commitments,
and counterfactual sequences of consecutive own moves are not implemented here.

## Install and launch

Use Python 3.12 and this checkout. These commands avoid installing Torch.

```bash
git fetch origin
git switch --track origin/codex/mate-in-one-coach
python3.12 -m venv .venv-coach
source .venv-coach/bin/activate
python -m pip install -r requirements-mate-one-coach.txt
python scripts/autogrowth/run_mate_one_coach.py prepare --pool reports/autogrowth/runs/m1-pool
```

On Windows, use `py -3.12 -m venv .venv-coach` and
`.venv-coach\Scripts\Activate.ps1` instead of the two Unix environment commands.
If the local branch already exists, use `git switch codex/mate-in-one-coach`.
The launcher sets a deterministic Python hash seed before importing the learner
and defaults native numerical libraries to one thread. A GPU is not used.

Computer A:

```bash
python scripts/autogrowth/run_mate_one_coach.py train --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/m1-seed1 --seed 1 --episodes 20000 --wall-seconds 28800
```

Computer B: run the same preparation command with its unchanged defaults, then:

```bash
python scripts/autogrowth/run_mate_one_coach.py train --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/m1-seed2 --seed 2 --episodes 20000 --wall-seconds 28800
```

Both machines use the identical pool; their manifests should match. Each has
its own organism and run directory. Do not merge their weights. Compare their
held-out chess outcomes. Alternatively, both processes can run on one machine
using separate run directories; each uses one CPU process.

To capture the zero-attempt baseline, first run the training command with
`--episodes 0`. It checkpoints the fresh organism without moving. Run
validation, then train with `--episodes 20000 --resume`. A fresh graph can
abstain during greedy evaluation; report that separately rather than calling
it random play.

For scheduled checks, first target `--episodes 2000`, evaluate, then resume
with `--episodes 10000`, and finally `20000`. Or run uninterrupted for the
full budget. `--episodes` is always a **total** target, not additional attempts.

```bash
python scripts/autogrowth/run_mate_one_coach.py evaluate --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/m1-seed1 --split validation
python scripts/autogrowth/run_mate_one_coach.py train --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/m1-seed1 --seed 1 --episodes 20000 --wall-seconds 28800 --resume
```

Ctrl-C or a file named `STOP` in the run directory requests a stop after the
current action and feedback finish. Remove `STOP` before resuming. Checkpoints
retain the organism and exact shuffled schedule together, with the two most
recent complete files retained. A crash can lose work after the last checkpoint
(default 256 attempts); resume discards uncommitted trace entries. After a hard
crash remove `run.lock` only once the old process has stopped. Resume requires
the original source, Python minor version, package versions, pool, and seed.
Use only checkpoints you produced or trust: they contain Python pickle data.

Outputs are `moves.jsonl` (real positions/actions/outcomes), `progress.json`,
`latest.json`, opaque compressed checkpoints, and separate evaluation JSON.
Checkpoint hashes verify transport integrity; the continuation tests compare
canonical graph semantics, credit state, and subsequent actual moves. Hashing
a pickle is not evidence of semantic equality or mastery.

When the configuration is frozen, `evaluate --split test` opens the reserved
test once and writes `final_test_opened.json`. That run cannot train afterward.
Repeated validation at different checkpoints is allowed; the same checkpoint
and split cannot overwrite an existing evaluation.

## Tests

From an activated environment on Unix:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPATH=src:libs/recon-lite/src python -m pytest -q tests/autogrowth/test_mate_one_coach.py tests/autogrowth/test_native_local_interaction_v27.py tests/test_intrinsic_credit.py libs/recon-lite/tests/test_formal_choice.py tests/test_fanin_terminals.py
```

The coach tests cover actual-move-only grading, no graph access by the coach,
no runtime teacher helpers, empty initialization, terminal leaves, exact
feedback binding, no double credit, consistent value updates and slow memory,
semantic continuation after restore, deterministic resume order, disjoint
curated splits, read-only evaluation, and corrupt-checkpoint rejection. Unit
tests may inspect internals; production feedback and scheduling may not.
