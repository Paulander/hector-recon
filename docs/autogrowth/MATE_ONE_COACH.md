# Mate-in-one: play through learned feature terminals

Official restart line: `main`. The default learner is
`coach/terminal.py:TerminalOrganism`, backed by the generic
`learning/terminal_development.py` runtime. Start a new run directory: old hybrid
checkpoints and the pre-correction terminal checkpoint intentionally cannot resume
against changed source code.

The [official continuation](OFFICIAL_CONTINUATION_20260906.md) records the review,
accepted corrections and next attribution tests.

## Measured initial run

At commit `e3900df`, after 182 actual training moves (99 mates, 180.675 seconds including final
checkpoint), nonlearning validation improved from 4/128 to **124/128 (96.875%)**.
There were no illegal moves or abstentions. These development rows cover 25
symmetry orbits; this is one short seed, not sealed confirmation. The final test
is unopened. Pruning's 256-exercise grace period was not reached in chess;
pruning and dependency retention passed separate mechanism tests.

The saved graph has 96 condition definitions, 70 distinct reader definitions,
20 action-binding slots, and 3,385 instantiated vertices. Twenty-five conditions
already carry nonzero slow weights. No causal MATURE certificate was issued.
See the [measured report](../../reports/autogrowth/development/TERMINAL_DEVELOPMENT_SMOKE_20260905.json).
The focused suite passed 79 tests; two boundary tests were rechecked after the
final protocol typing/doc clarification.
The corrected official baseline passes 81 focused tests, including action-root
semantics, TRIAL lifecycle behavior and evidence-preserving pruning.

A subsequent read-only weight ablation reproduced 124/128, fell to 75/128 when
all multi-reader condition contributions were zeroed, and fell to 4/128 when all
condition contributions were zeroed. This establishes behavioral dependence on
the learned weights and material contribution from compositions at that checkpoint.
It does not establish adaptive topology growth because birth was random. See the
[ablation report](../../reports/autogrowth/development/TERMINAL_M1_WEIGHT_ABLATION_20260906.json).

The separately supplied `TERMINAL_DEVELOPMENT_SMOKE_20260905.zip` archive
contains the exact trained organism, pool, schedule, real-move log and evaluation
results. It is not published in the repository. Extraction and checkpoint
restoration were verified against `e3900df`. Download it into a checkout of that
commit and extract it before creating directories with these same names:

```bash
python -m zipfile -e TERMINAL_DEVELOPMENT_SMOKE_20260905.zip .
```

This restores `reports/autogrowth/runs/terminal-m1-seed1` and
`reports/autogrowth/runs/m1-coach-smoke-pool`. The initial 180-second experiment
is complete. Current `main` deliberately rejects its continuation because the
action-root, lifecycle, hypothesis-history and source-identity semantics changed.
Use a new run directory for new experiments.

## Implemented loop

The environment owns the board. A catalog terminal reads legal actuator bindings;
spawned input terminals read individual coordinates of a fixed, typed feature
schema. SCRIPT nodes combine their confirmations. Plastic SUR edges carry signed
expected-return contributions into a `weighted_evidence` SCRIPT; the existing
formal choice primitive selects one bound action. A requested output terminal
then executes that action. The coach observes its actual result and sends only
scalar reward plus the action/event binding: +1 for actual mate, -1 for failing
this one-own-move exercise. Nonmate is exercise failure, not a chess loss.

The 16-coordinate schema is declared in `coach/terminal.py`. It contains current
turn, whether the bound actuator moves the rook, king/piece distances, edge and
alignment measurements, and distances/alignment between the actuator's target
square and current kings. These last coordinates describe action parameters;
no successor board is constructed. They are supplied geometric embodiment, not
learned rules or tactical classifications. No checkmate, opposition, ideal-move,
mate-distance or selected-answer coordinate exists.

One learned condition definition contains one to three equality readers and an
AND, OR or exactly-one XOR operator. Equality to False supplies Boolean negation.
Readers may join a composition immediately; independent usefulness or maturity
is not a prerequisite. Random proposals provide the initial finite search
family; selected-action reward error adjusts their effective graph-edge weights.
The proposal distribution itself is not learned in this first implementation.

Conditions share their parameters across action bindings and positions. Each
binding has separate physical terminal/SCRIPT instances, including separate
request states. A 96-definition budget therefore does **not** mean 96 total
vertices. The persisted graph includes all instantiated vertices and edges.
Terminal readers are shared among conditions within a binding only; they remain
leaves and are retained while any surviving condition needs them.

Final outcome credit reaches the actual participating conditions of executed
actions. Earlier actions can retain decaying eligibility until final feedback.
Inactive conditions do not receive that outcome update. Randomly proposed
conditions remain TRIAL: participation and outcome correlation do not nominate
them for PROBATION. The `PlasticWeight` type retains fast/slow fields, but simple
sum-preserving transfer does not change effective learning dynamics or demonstrate
resistance to forgetting.
Pruning retires weak whole conditions after a grace period and then removes
orphan readers. A tombstone retains the condition identity and evidence and blocks
evidence-free identical rebirth. This is a bounded engineering survival rule, not evidence of
causal structural importance. Reward correlations never become fabricated
intervention evidence or causal MATURE certification.

The coach does not inspect topology or virtual states to schedule, reward,
consolidate or prune. It saves the opaque organism and shuffled exercise order.
Offline preparation may verify that starts contain a mate; exported pools
contain no answer moves. Reflection/rotation equivalent positions stay in the
same split. Validation is a separate nonlearning process and never saves changes
to the organism. The final test remains sealed until explicitly evaluated.

## Scope and reuse

This uses the existing Graph, formal request/confirmation engine, choice and
Boolean operators, plus `StemCellState` and `CandidateLocalStats`. The existing
stem-cell integration receives board/FEN or whole-feature samples; M5's broader
structure manager scans rich episode traces and includes KRK-specific discovery.
`OnlinePairCompositionLearner` requires supplied atom IDs and keeps trials out
of prediction until validated. Those entry points do not provide this empty-root,
terminal-only, immediately composable action path. The small lifecycle adapter
therefore lives inside Hector's learning package, never in the coach; it reuses
candidate statistics while keeping correlation distinct from intervention.

The older intrinsic-credit engine remains for grounded hierarchical child-value
handoff. Its competence-provider gating is not used to authorize local feature
weight updates: that would prevent immature features from learning. This first
path implements a normalized episodic reward-error update, not a claim that
hierarchical value handoff or variable-duration option learning is completed.

The root is named `action_choice` and confirms action selection, not achievement of checkmate.
Its raw activation, including any exploration bonus, is not calibrated child
competence or a transferable goal-value signal. A future hierarchical interface
must distinguish these before using a child response to support delegation.

Still deferred: reader-parameter mutation beyond birth/selection, residual-driven
proposal selection, recursive SCRIPT/sequence discovery, virtual frames, learned
world dynamics, module arbitration and multi-move chess exercises. A finite
random condition grammar can miss useful structures. Passing a small Boolean
task or improving M1 is not proof of full KRK or general self-organization.

The earlier 67/128 validation result belongs to the historical hybrid, which
reconstructed boards and scored candidate successors. Its code is retained for
regression/reference, and its original protocol is in
[MATE_ONE_COACH_HYBRID_REFERENCE.md](MATE_ONE_COACH_HYBRID_REFERENCE.md).
It is not evidence for this new implementation.

## Install and run

Use Python 3.12. No GPU or Torch installation is needed.

```bash
git fetch origin
git switch main
git pull --ff-only
python3.12 -m venv .venv-coach
source .venv-coach/bin/activate
python -m pip install -r requirements-mate-one-coach.txt
python scripts/autogrowth/run_mate_one_coach.py prepare --pool reports/autogrowth/runs/m1-pool
```

For a first checkout, clone the repository and use `main`. Windows activation is
`.venv-coach\Scripts\Activate.ps1`.
The launcher fixes Python's hash seed and limits numerical-library thread counts.

The initial engineering budget and failure criteria are frozen in
[TERMINAL_DEVELOPMENT_RUN.md](TERMINAL_DEVELOPMENT_RUN.md). Capture the untrained
baseline, then run up to 2,048 exercises or 180 seconds:

```bash
python scripts/autogrowth/run_mate_one_coach.py train --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/terminal-m1-new-seed1 --seed 1 --episodes 0
python scripts/autogrowth/run_mate_one_coach.py evaluate --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/terminal-m1-new-seed1 --split validation
python scripts/autogrowth/run_mate_one_coach.py train --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/terminal-m1-new-seed1 --seed 1 --episodes 2048 --wall-seconds 180 --resume
python scripts/autogrowth/run_mate_one_coach.py evaluate --pool reports/autogrowth/runs/m1-pool --run reports/autogrowth/runs/terminal-m1-new-seed1 --split validation
```

The initial graph can make a legal move without learned readers. Its greedy
baseline uses the formal primitive's deterministic tie rule, not random play.
After this diagnostic run, a longer run or second seed should be identified as
an additional experiment. On a second computer use the identical code/pool and
a separate run directory and seed; do not merge weights or checkpoint files.

`--episodes` is a total target, including resumed episodes. A wall limit ends
only after the current action/feedback transaction. Ctrl-C or a `STOP` file in
the run directory likewise requests a clean checkpoint. Remove `STOP` to resume.
The two newest checkpoints are retained. Resume restores the organism, RNG and
shuffled schedule, and rejects changed source/runtime, pool or seed. After a
crash, remove `run.lock` only once the old process has stopped. Python pickle
checkpoints must come from a trusted source.

Outputs: real-move JSONL, progress JSON, a checkpoint pointer, compressed opaque
checkpoints and separate evaluation JSON. Transport hashes protect file bytes;
continuation tests compare learned state, graph edges, shared parameter identity
and subsequent actions. Neither is evidence of chess mastery.

`evaluate --split test` opens the reserved test once and freezes that run against
further training. M2 remains blocked until reliable disjoint M1 performance;
this implementation does not automatically change the curriculum.

## Tests

```bash
PYTHONPATH=src:libs/recon-lite/src python -m pytest -q tests/autogrowth/test_terminal_development.py tests/autogrowth/test_mate_one_coach.py tests/autogrowth/test_native_local_interaction_v27.py tests/test_intrinsic_credit.py libs/recon-lite/tests/test_formal_choice.py tests/test_fanin_terminals.py
```

These exercise terminal-only observation/action, typed sparse masks, actual
AND/OR/XOR semantics, learning XOR without marginal feature correlation, selected
and delayed credit, protected composition members, bounded noisy growth,
consolidation, persistence, real chess moves, coach opacity and old-path
regressions. Test-side planted structures isolate primitives; the XOR learning
test starts empty and receives only scalar outcomes of its own choices.
