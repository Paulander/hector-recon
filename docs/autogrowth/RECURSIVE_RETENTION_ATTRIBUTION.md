# Recursive retention: what caused the remaining losses?

Completed 2026-09-12. This is an offline follow-up to
[the retention comparison](RECURSIVE_RETENTION_RESULTS.md), using guided seeds
4/5/6. No actor was trained, modified or resumed. Diagnostic rewards, candidate
comparisons and fitted weights never enter the learner.

## What grows, and what does not

The current runtime starts with parallel weighted contributions to action scores.
It can replace one contribution with two complementary, independently plastic
descendants, then refine either descendant again:

\[
wF \longrightarrow w_0 F\neg G + w_1 FG
\longrightarrow w_0 F\neg G + w_{10}FG\neg H + w_{11}FGH.
\]

This produces three conditional alternatives through repeated binary refinement.
At each split both child weights inherit their parent's value, preserving its
initial score; the old direct scoring contribution is removed. Other parallel
contributions remain. Descendants of one source partition that source, while
different source families may overlap and affect the same action.

Contexts are sampled from existing expressions and equality readers. The guided
arm selects eligible source/context pairs by observed reward-prediction residuals;
it does not pick the split uniformly at random. The random arm does. There is a
shallow random-proposal fallback when a split cannot be made. In this prototype
the sampled context vocabulary remains fixed after the prefix. Repeated source
refinement supplies recursion, subject to six splits and depth four in this run.

A and B were labels for two environment contexts, not installed modules. The
runtime does not automatically spawn A/B/C goal networks, learn their delegation,
or isolate every weight belonging to a skill. Shared definitions have separate
single-parent SCRIPT execution instances. Eight of the eighteen guided splits
used contexts containing the action coordinate; specialization need not coincide
with a state-only context selector.

## Seed 6: shared credit displaced a representable behavior

The final graph admits one set of weights that ranks all sixteen rows correctly.
The first measured checkpoint with that capacity is episode 640. It remains
feasible at the subsequent measured checkpoints. The two final failures, rows 6/7,
differ only in the irrelevant fourth bit; both require action b.

For either row, from episode 640 to 1024:

| Change in correct-action margin | Value |
| --- | ---: |
| Initial margin | +1.577020 |
| Actual weight credit | -1.671561 |
| Pruning | +0.008414 |
| Final margin | -0.086127 |

All split installations preserve margins within numerical tolerance. Pruning
slightly helps these rows; the net loss comes from actual credit updates.

The first strict positive-to-negative crossing after the return to mostly A is
event 747: the actor chooses b incorrectly on A row 1 and receives -1. Credit
reduces two original contributions, `[action=b]` and `[x=False AND action=b]`.
They are also active for the correct b action in B rows 6/7. Each reduces those
rows' margin by 0.041331, taking it from +0.031076 to -0.051586. Both cues survive;
neither is replaced at that event. Later updates recover and lose these rows
again. The last strict crossing is event 994, through the same two contributions.

This is a concrete failure of contextual isolation. It does not prove that those
features are globally harmful or that an available perfect ranking would be
learned simply by reducing the learning rate. The reconstructed changes explain
the actual loss, not the counterfactual outcome of a different learning law.

## Seed 4: the final representation cannot rank a conflicting pair correctly

The raw input distinguishes the contexts, but the final grown action preferences
do not. Consider:

| Row | x | y | z | Irrelevant bit | Required action |
| --- | --- | --- | --- | --- | --- |
| 5 | False | True | False (A) | True | a |
| 7 | False | True | True (B) | True | b |

For both rows the final graph has the same relative action score:

\[
Q(b)-Q(a)=w_{27}-w_{16}-w_{18}.
\]

Row 5 requires this quantity to be negative; row 7 requires it to be nonnegative
(option 1/b wins exact ties). No shared weights can meet both requirements.
An exact rational certificate combines the opposing inequalities into the
contradiction `0 >= 1/2`, after scaling the strict requirement to unit margin.
This is a constraint on the saved graph, not on the full recursive grammar.
All seven measured seed 4 graphs fail joint sixteen-row ranking feasibility;
we did not test every intervening topology.

Weight updates still cause the observed policy changes. Row 5 first loses its
positive margin at event 256, a rewarded action on another A row, before any
recursive split. Across the continuation, its margin changes from +0.011954 to
-0.892454: credit contributes -0.912909 and pruning +0.008502. Thus even this loss
cannot be described simply as B replacing an A detector.

## Can the existing mechanism supply the missing distinction?

Immediately before seed 4's final split, none of the 66 eligible single-split
alternatives would by itself make all sixteen rows jointly rankable. The actual
selected candidate reproduces the maximum residual score exactly.

After that final split, **three of 56 otherwise eligible further splits** would
provide sufficient representational capacity, if the exhausted six-split cap
were lifted. They rank 13th, 23rd and 27th under the existing statistic. For example,
splitting contribution 16 using the already sampled conjunction
`x=False AND y=True AND z=True` permits a perfect ranking; that nomination has
67/14 observations on its two sides. No new sensor or Boolean operator is needed
for this hypothetical repair. None of these splits or fitted weights was installed.

The top-ranked further candidate does not provide that complete capacity. More
opportunities could therefore help, but neither the current cap nor the residual
ranking guarantees that the useful refinement will be reached. Offline capacity
is not evidence that a split would autonomously learn good weights or retain them.

Seed 5 is the successful reference: its measured graphs become jointly rankable
at 768, and it eventually learns all sixteen choices. Structure and learned
weights must both be assessed; depth alone does not settle either question.

## Verification and next decision

Arithmetic reconstruction checks all 2304 logged guided continuation updates,
including selected-action predictions, active conditions and sampled context
truth values. Maximum prediction discrepancy is 2.0e-15. All eighteen subsequent
checkpoint weight sets match, and all eighteen frozen evaluations reproduce
(288 evaluation actions, zero training actions). Strict margin crossings omit
near-zero ties; they are not a count of every policy change. Feasibility witnesses
are checked against all constraints; seed 4's contradiction is verified exactly
with rational arithmetic. Diagnostic processes use one core and finite time limits.

The next bounded training comparison should keep ordinary learning active in
both arms and compare the existing split cap with additional recursive split
opportunities. That would test whether the existing generic growth process can
reach useful refinements and whether seed 6's shared-weight interference improves
or persists. Do not select the above oracle-identified candidates for the actor.
There is no basis yet for installing a new goal hierarchy or retention rule as
the assumed solution. No additional training was started by this investigation.

Reproducible analysis:
[script](../../scripts/autogrowth/attribute_recursive_retention.py),
[trajectory attribution](../../reports/autogrowth/development/RECURSIVE_RETENTION_ATTRIBUTION_20260912.json),
[capacity, candidate and accounting details](../../reports/autogrowth/development/RECURSIVE_RETENTION_ATTRIBUTION_DETAILS_20260912.json).

Run the script with `--run`, a fresh `--output`, and optionally `--details-from`
an existing attribution to regenerate the LP/accounting details without repeating
the frozen evaluations. Results and code remain local to the work branch.
