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

## Historical requirement recovered during this analysis

The user identified this as the earlier corner/knight-distance failure. Repository
history confirms that connection. This section is a source review, not new chess
play or a rerun of old experimental claims.

- [53623a6c, July 3: edge-relative opposition](https://github.com/Paulander/hector-recon/commit/53623a6cfeb7205b1f9ac0c2e578fdaa5c2054ac)
  replaced a coarse king-distance condition with separate file-edge and rank-edge
  conjunctions. Its recorded fresh recognizer recall was 0.766.
- [31e85b42, July 3: corner mate branch](https://github.com/Paulander/hector-recon/commit/31e85b428368b50f34292f91f5a0d9908af4fec5)
  records that all 15 preceding fresh false negatives had a cornered Black king
  and king offsets (1,2)/(2,1). The code explicitly added a corner AND
  knight-support branch under an OR with edge-relative opposition. Reported
  recognizer recall became 1.00 on the listed pools. That is an authored
  expressivity demonstration, not proof of autonomous structural discovery:
  `mate_in_one_basin_atoms()` supplies named chess predicates and
  `build_mate_in_one_basin_graph()` wires the specific solution.
- This predates [d3b73cad, July 5: “no fable”](https://github.com/Paulander/hector-recon/commit/d3b73cadfcdef298adff2719c62cacada742d142)
  and is in the ancestry of both `recon-merge-v1` and
  `v1-merge-continuation-without-fable`. The
  [July 9 corrected ledger](https://github.com/Paulander/hector-recon/blob/66320e2b1f6068bbfdbe1fc11f8e98523fc8ebf8/docs/BRIEF.md)
  explicitly withdrew broad autonomy/causality claims: hand-shaped ecological
  credit, Python-mediated arbitration and invalid restored-target measurements
  remained. A formal graph containing a rule was not evidence it learned the rule.

Two further lessons should survive that correction. The
[July 3 brief](https://github.com/Paulander/hector-recon/blob/31e85b428368b50f34292f91f5a0d9908af4fec5/docs/BRIEF.md)
reported lost distributed signal after per-key precision promotion (0.94 to
0.86); this motivates evaluating combinations rather than demanding that each
atom first prove marginal usefulness. The
[July 11 composition audit](https://github.com/Paulander/hector-recon/blob/a1dc7654f154d73e87d90ebc7938ea67784d4285/docs/autogrowth/NATIVE_INTRINSIC_KRK_RESUME_COMPOSITION_AUDIT_20260711.md)
reported four differently named candidates with the same activation signature
and no measured behavioral effect. It added signature diversity and both positive
and negative proposals. Those historical results are not revalidated here and
do not establish that the old selection law will help the current actor.

The reusable requirement is **context-dependent conjunctions and alternative
support structures, with useful joint signal preserved and distinct candidates
actually receiving learning opportunity**. Do not turn the historical diagnosis
into a supplied corner/knight-mate terminal, authored branch, shaped reward or
stage selector. The current restart already has exact file/rank measurements and
generic AND/OR/exactly-one conditions. Whether a particular saved graph lacks
expressivity, or has sufficient structure but poor learned ordering, must be
tested separately. More hierarchy is not automatically necessary just because
the old demonstration used a deeper authored graph.

Historical coverage warnings also remain relevant. The
[July 11 R0 correction](https://github.com/Paulander/hector-recon/commit/9aba7c9f36c4e6914ba0e924c371307dc044d2f2)
balanced edge/corner locations. Our current training pool already contains both
knight-offset orientations: 29 rows with (1,2), 20 with (2,1). Every training row
appears 16 times in each actor's event-4,096 schedule. Thus outright absence of
this family is not the explanation here; these counts do not tell us how many
of those encounters produced an actual winning action or useful candidate credit.
Old mandatory freezes, MATURE-only operation and bans on separately trained
children are not current restart instructions.

## Completed result — 2026-09-07

Implementation/protocol was published before execution at
`b780db52e73563fb71e8a2e56765ec514ff27727`. All **209 required branch tests passed**
in 363.55 seconds. The diagnostic completed its one attempt in **1,093.001
seconds**, within 1,800: **7,039 laboratory transitions, 1,536 frozen actor moves,
zero training moves**. No retry, extension, final-test access or learner change.
All four actors reproduced their development actions/outcomes, and all eight
split replays matched formal support and choice while preserving learned state.
All 162 original private payload hashes remain unchanged. No new trained states
were created. Full results are in the
[public aggregate](../../reports/autogrowth/development/M1_FAILURE_PATTERNS_20260907.json).

### The failures are a specific geometric family

Development mates by initial king geometry, with absolute file/rank separations:

| Family | Rows | Seed 7 at 1,280 | Seed 7 at 4,096 | Seed 9 at 1,280 | Seed 9 at 4,096 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Aligned kings, separation two, corner or other edge | 86 | 86 | 86 | 86 | 86 |
| Corner, one file and two ranks apart | 25 | 0 | 25 | 25 | 25 |
| Corner, two files and one rank apart | 17 | 17 | 15 | 0 | 0 |

All 17 persistent seed 9 misses are the last family, across seven symmetry
orbits. Every one is a rook check leaving exactly one legal Black reply rather
than mate; none is stalemate or an immediately capturable rook. Seed 7's two
lost rows are in that same family and are two rotations of **one** orbit:
White king c2 / rook f3 / Black king a1, and White king f7 / rook c6 / Black king
h8 (development rows 59 and 119). They also select a rook check with one escape.
Thus two lost rows are not two independent geometric problems. Their final
winning-versus-chosen support margin is only **−0.035315**.

Training-pool evaluation tells the same larger story. Seed 7 went from 227/256
to 254/256, gaining 27 of the 29 opposite-orientation corner cases and losing
none of its prior training successes. Its two remaining training misses form
one other orbit and have margin **−0.028293**. Seed 9 stayed 236/256, failing all
20 training examples of its problematic orientation at both endpoints. These
are frozen replays of training positions, not another set of rewarded episodes.

### Structure and learned ordering are different bottlenecks

| Actor | Training/development behavior | Perfect ranking possible with the saved conditions? |
| --- | --- | --- |
| Seed 7, event 1,280 | 227/256; 103/128 | No on either split: an elementary opposing-constraint witness exists |
| Seed 7, event 4,096 | 254/256; 126/128 | Yes on each split, with verified strict margins |
| Seed 9, event 1,280 | 236/256; 111/128 | Yes on each split, with verified strict margins |
| Seed 9, event 4,096 | 236/256; 111/128 | Yes on each split, with verified strict margins |

No raw-coordinate, grown-reader or grown-gate within-position winning/losing
alias was found in any of the eight replays. Seed 7's initial obstacle was across
positions: a common set of weights faced incompatible requirements. Its final
condition set removed that particular expressivity limit. This is a real
representation-capacity gain during ordinary random birth/turnover, alongside
behavioral improvement. It does not prove adaptive proposal selection or tell
us which individual birth caused that gain.

For final seed 7, both remaining development failures can be solved jointly by
some weights on its existing graph; the same is separately true for its training
split. Final seed 9 also admits perfect ordering on each examined split. Every
final failed row additionally passed the check that it could be repaired while
retaining all current successes in its split. No fitted coefficients were
installed or returned. **These are separate split existence checks, not a proof
that one vector solves their union, generalizes, or is reachable by the current
update law.** Feasibility is not learned performance.

Two full tie-aware numerical solutions (final seed 9) did not reproduce their
intended exact ties and remain marked inconclusive in the raw report. Independent
strict-margin solutions were directly checked and already suffice to establish
the per-split capacity above. Three individual initial-seed-7 training repairs
remain numerically inconclusive; 22 were feasible and four impossible. Initial
development repairs were 21 feasible and four impossible. None of these numerical
issues was a formal-engine choice discrepancy.

### Turnover happened; unchanged win totals hid movement

| Actor | Live conditions | Action-discriminating conditions on the examined pools | Newly born live conditions at the end |
| --- | ---: | ---: | ---: |
| Seed 7 | 64 → 62 | 40 → 46 | 34, of which 26 discriminate actions |
| Seed 9 | 64 → 62 | 41 → 44 | 34, of which 23 discriminate actions |

Both retained 28 initial definitions. Final populations also contain 16 and 18
conditions that contribute equally to all alternatives within every examined
board, including three and eight never-active conditions. These figures do not
identify a stall simply from population size or birth count. Equal-action
contributions can still affect reward prediction and subsequent updates; they
are not automatically safe to remove.

Seed 9's average development failure margin moved **−1.017576 → −0.596372**;
its training failure margin moved **−0.961909 → −0.424004**. All remained below
the competing chosen action, so the binary score hid this movement. On the fixed
development win/loss pairs, retained-weight changes contributed +0.108953,
removed contributions −0.351993, and new contributions +0.664244 on average.
These sum to the observed change. They do not guarantee that more play will
continue improving the margin or isolate the cause of improvement.

Seed 7's lost development pair instead moved **+0.930689 → −0.035315**. The
accounting is −0.040927 from changed retained weights, −0.109580 from removals
and −0.815496 from new contributions. Most of the margin reversal therefore
comes from contributions of definitions born during the continuation, rather
than a disappearance of all old learned weights. This is interference in the
resulting score; a matched intervention would still be needed to attribute the
training trajectory causally to particular births or pruning decisions.

### Updated next decision

The old corner lesson should have been linked from the active guidance earlier.
It is now preserved above. But its recurrence does **not** establish that the
current stalled actor lacks a corner mechanism: seed 9 already had sufficient
per-split ranking capacity before this continuation. More capacity, another node
type, or copying the historical recognizer is therefore not the leading next
intervention. Nor has a particular learning rate been identified as the cause.

**Follow-up completed in [M1_EXPLORATION.md](M1_EXPLORATION.md):** declare a matched ordinary-play comparison of the **existing exploration
parameter**, 0.25 versus 0.50, with otherwise unchanged settings and normal growth
active. Use final seed 9 as the stalled case, seed 7 as the improving/near-boundary
case and seed 4 as the retained strong reference. These are selected-history
diagnostics, not a fresh-seed efficacy claim. Fix the complete schedule, endpoints
and resource cap before play; measure gains, losses and the actually executed
action/outcome record. Both arms must receive the same exercise opportunities.

Logging the submitted behavior allows a subsequent offline count of actual wins
in each geometric family. Sixteen exercise encounters per training row do not
mean sixteen positive examples: the actor sees only its chosen move's reward.
The preceding aggregate-only logs do not establish how many corner wins it
experienced. Do not use this uncertainty to assume an exploration problem; test
it. No family detector, oversampling of a diagnosed answer family, fitted score,
branch intervention or changing schedule from graph inspection enters training.
If extra exploration does not help, investigate the local selected-action credit
objective before inventing another hierarchy. Keep broader coverage and learned
child competence/delegation separate; this closed analysis creates no new M2 or
handover capability.
