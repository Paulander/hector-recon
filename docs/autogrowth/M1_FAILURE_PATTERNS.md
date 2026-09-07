# M1 failure patterns and saved-graph constraints

Post-hoc diagnostic scope declared before execution, following the completed
long-play result at `a21473e7b818271fbd5424204ea83d49c2d550f8`. This combines the
planned initial/final comparison of seeds 7 and 9 with the user's question about
common chess patterns, including seed 7's two lost development positions.
Selection is explanatory, not a fresh-seed confirmation study. No learner changes.

## Fixed scope and information boundary

Inspect **seeds 7 and 9 at events 1,280 and 4,096**, four actors. Use all **256
training-pool and 128 development-pool rows**, in existing order. Restore the
exact indexed private payloads against the published state/configuration and
current runtime hashes. Preserve source files. The final test stays unopened.

The laboratory grades every legal alternative on an isolated board copy once.
Record mate/check/quiet/stalemate, moving piece, legal Black replies, whether the
rook can be captured and target-to-Black-king distance. Describe the original
position by corner/file-edge/rank-edge and both king-separation coordinates,
including their rotation-invariant unordered pair. Count rows and symmetry
orbits; show all category denominators, not only failure examples. These are
post-learning descriptions, not new terminal features or rewards.

Replay each frozen actor through its ordinary input terminals, formal graph
choice and output terminal on both splits. Check every computed support and
selected action against the existing Boolean/weight calculation. Reproduce the
published development action digest/outcomes exactly and preserve learned state.
The optional observer in the existing offline diagnostic runs only after the
actor's action; the organism and coach never import or call it.

Reuse the existing signature-alias and exact tie-aware ranking checks. For each
failed row, additionally ask whether a fixed weight vector could solve that row
while retaining **every currently solved row in that split**. Every exercise must
have exactly one winning action. A feasible mathematical comparison is not a
trained policy or achieved score; coefficients are discarded. Separate feasible
repairs need not combine into a jointly feasible repair. Unresolved numerical
checks remain explicitly inconclusive rather than becoming positive claims.

Measure live grammar/reader coverage, action-invariant versus action-discriminating
conditions on the examined pools, inactive conditions, training participation,
old/new survivors and absolute weight mass. A context-only condition can receive
credit while contributing equally to every action. That does not by itself prove
it is dispensable from the learning dynamics. Distinguish condition definitions
from physical action-binding replicas and do not infer causal usefulness from
participation counts.

For persistent/new failures, account for changes in the winning-versus-finally-
chosen-action margin: changed weights of retained definitions, removed old
contributions and new contributions. Their sum must reproduce the measured margin
change. This is arithmetic decomposition, not a causal intervention into learning.
No ablated or fitted actor is deployed, trained or reported as an autonomous gain.

## Execution and evidence

**7,039 laboratory alternative transitions + 1,536 frozen actor moves = 8,575
explicit executions; zero training moves.** One process, **1,800 seconds**, one
attempt, no retry or automatic extension. Save per-split completed reports and an
explicit failure/count record if interrupted. No new private trained payloads are
created. Publish diagnostic aggregates and failure-row descriptions; do not save
an alternative-action training dataset, action list or fitted weight vector.

Python 3.12, chess 1.11.2, numpy 2.3.5 and the existing diagnostic SciPy installation.
The launcher fixes hash seed 0 and numerical library threads to one. Run the full
required branch suite, including the new focused diagnostic tests, before the
declared study:

```bash
python scripts/autogrowth/diagnose_m1_failure_patterns.py \
  --pool reports/autogrowth/runs/m1-coach-smoke-pool \
  --reference reports/autogrowth/development/M1_LONG_PLAY_20260907.json \
  --private snapshots/autogrowth/m1-long-play-seeds4-9 \
  --output reports/autogrowth/runs/m1-failure-patterns-seeds79 \
  --wall-seconds 1800
```

## Decision after evidence

Separate a common geometric failure from its mechanism. A graph may distinguish
moves within each board yet impose conflicting shared weight requirements across
boards. Conversely, a failed row might admit a weight-only repair while preserving
current successes. Neither result alone identifies a correct learning rate or a
successful adaptive birth law.

Use the result to justify one subsequent ordinary-play comparison of an existing
budget or learning setting, if supported. Do not supply the missing chess pattern,
add a controller by assumption or endlessly optimize these viewed positions.
Broader coverage and the small independently trained child-competence/delegation
task remain separate next capabilities; perfection on this pool is not their gate.
