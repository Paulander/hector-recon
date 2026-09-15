# Why the two corner orientations interfere

Completed read-only follow-up, 2026-09-09, to `M1_RETENTION.md` at
`6b464f0bf924befe08097ae288c41746211ce2b3`. The user asked whether detectors
replace one another, compete under a corner goal, or reflect a growth/feature prior.
No learner, feature or reward change. Evidence is in
[`M1_CORNER_MECHANISM_20260909.json`](../../reports/autogrowth/development/M1_CORNER_MECHANISM_20260909.json).

## The actual computation

There is no learned higher `corner mate` node arbitrating between strategies.
The persistent hierarchy is `action_choice` -> legal-action option -> Boolean
condition -> leaf equality readers. A condition has separate physical instances
per action binding, but one shared weight across bindings AND positions.
Conditions all contribute signed support when they confirm. The choice root
selects a primitive action from the summed option supports. Conditions do not
compete to become the one selected detector.

For action a, `q(a)=b+sum_j w_j*g_j(a)`. On selected action a with observed reward r,
all n active conditions receive the same `delta=.3*(r-q(a))/(1+n)`; so does the bias.
For a different position's win/loss comparison, the resulting margin change is
`delta * sum_active [g_j(win)-g_j(loss)]`. The shared bias cancels. This is the
direct route by which a successful action can harm another position's ranking.
Pure board-state cues shared by every legal action cannot change a within-board
ranking alone, though they affect prediction error. Conditional compositions
with action-dependent cues can distinguish policies by context.

## Both sets of contributions remain present

For a representative pair, Black king h8 and rook b2 stay fixed:

| Current board / preferred action | First orientation | Diagonally reflected orientation |
| --- | --- | --- |
| White king | g6 | f7 |
| King file/rank separation | (1,2) | (2,1) |
| Black king edge-file / edge-rank flags | true / true | true / true |
| Actual mating move | b2b8 | b2h2 |
| Other checking move, not mate | b2h2 | b2b8 |
| Chosen at saved step 4,096 | b2b8, mate | b2b8, not mate |
| Chosen at saved step 6,144 | b2h2, not mate | b2h2, mate |

Both the rank-alignment condition 23 and file-alignment condition 93 survive
throughout these endpoints. Condition 23's weight increases **.72784 -> .85436**;
condition 93's increases **.06513 -> .46536**. Rank-dependent condition 40 also
survives and strengthens **.55817 -> .79309**. The old contribution was not erased:
other shared contributions outweighed it. These are partial cues, not two complete
and separately trained corner detectors. Context-specific conditions coexist as well.

At the first known fixed-pair crossing, event **4,378**, training row 153 executes
**g3h3**, an actual mate with kings h8/f7, and receives +1. Its predicted reward is
**-.6282207144**. Six active conditions receive **+.06978088776** each. Four
of them (74, 93, 124, 208) are inactive for b2b8 and active for b2h2 on the other
position. Hence its margin changes by **-4*.06978088776 = -.2791235510**:
**+.1827223465 -> -.0964012046**. No condition is born or removed at this event.
The other two active conditions and the bias contribute zero to that margin.
This is a fixed pair crossing; it does not by itself assert the full choice result
immediately after the update. Saved full-choice results confirm the later loss.

## What the feature space preserves and discards

The 16 coordinates are turn, moving-piece identity, four paired file/rank
distances (king-king, rook-Black king, target-Black king, target-White king; eight
distance coordinates), two Black-king edge flags, two target/Black-king alignment
flags and two king-alignment flags. More exactly: two initial Boolean coordinates,
eight integer distances and six Boolean edge/alignment coordinates.

Distances are absolute. Global horizontal/vertical reflection therefore gives
the same measurements when actions are reflected too. A 90-degree rotation or
diagonal reflection swaps every corresponding file/rank coordinate. It does not
automatically share their condition definitions or weights. The current failure
concerns those two axis orientations, not a suppressed left/right sign.

At a corner both edge flags are true; neither axis has precedence. There is no
direct corner, knight-distance, king-coverage, opposition or mating-pattern
classification terminal. Those relationships must be composed from measurements.
Targets describe legal move parameters on the current board, not evaluated
successors. Input action bindings retain the actual target and direction.

All **56,312** action vectors across the eight transformations of the 384 examined
boards match the exact coordinate transformation law. Across the **2,836** distinct
raw vectors, none occurs with conflicting mate/nonmate labels on these rows.
This rules out the old precedence bug and raw-vector label collision on this
sample, not information completeness over every legal chess position. Tied score
selection need not be symmetry-equivariant; the measured crossing is not a tie.

## Supplied priors and contingent history

- The proposal law samples coordinates uniformly, chooses one to three distinct
  coordinate readers, samples values uniformly within each coordinate, then
  chooses AND/OR/exactly-one with probabilities .8/.1/.1 for multi-reader proposals.
  File and rank have equal marginal treatment. There is no closest-edge ordering,
  family-priority rule or slot dedicated to one corner alternative.
- Binary equalities are proposed four times as often per selected coordinate as
  a particular value in a distance's eight-value domain. Alignment Booleans also
  duplicate distance-zero facts. This is a prior toward cheaply available broad
  cues, equally for both axes, not an axis-specific preference.
- A finite random graph is usually asymmetric. At step 4,096 only **3 of 62** live
  definitions had their literal axis-swapped definition present; at 6,144 **5 of
  64** did. These counts include self-invariant definitions, not pairs of tied
  weights. Existing mirrored definitions still learn independently.
- Weak-weight pruning and its grace period select surviving conditions, but do
  not explicitly test unique causal value or redundancy. Syntactically different
  conditions can act identically in a context and receive repeated contributions
  of credit. Normalizing by active count does not remove that representation dependence.

Thus the mechanism of interference is structural and reproducible; which family
loses, when it loses, and which weights dominate depend on the sampled conditions
and history. Recovered seed 7 shows this is not an inevitable inability to hold
both skills. This observation does not establish a superior replacement learning law.

## Prediction is stricter than choosing the right move

At the final seed-9 graph, **two complete condition-activation patterns** occur
with both mate and nonmate labels across different boards. One includes only
training data on both sides: train row 107's mating h2a2 and train row 4's
nonmating e5a5 have identical gate vectors. Their raw feature vectors differ.
No fixed weights and shared bias can predict +1 and -1 for these identical gate
vectors simultaneously. This ambiguity is absent in the inspected 4,096, 4,352
and 4,480 graphs and appears by the final inspected graph. Its first appearance
and causal effect on the four target losses were not isolated.

This is compatible with the already verified perfect per-board ordering:
each board has a different set of alternatives and only relative rankings matter.
Exact reward prediction and correct action ranking are different requirements.
The observation does NOT prove that the least-squares optimum must misrank these
four positions, that this alias caused their first loss, or that all graphs share
this limitation. It makes the selected-action objective worth examining alongside
constant-step fluctuations. A lower rate cannot remove exact gate aliasing by
weight changes alone, although changed growth may later change that representation.

## Verification and next experiment

The offline script completed in **14.52 seconds**, under a 180-second internal /
210-second external time limit on one CPU. It performed **7,119 laboratory
transitions, zero training moves and zero learner updates**. Endpoint numerical
choices reproduce all historical train/development outcomes. Reconstructing the
actual 4,352–4,480 block matches saved weights within **2.23e-16**. Actors and
source payloads are unmodified.

Proceed with the separately authorized **.3 versus .1 learning-rate** control in
`M1_LEARNING_RATE.md`; it tests step size, not the removal of representation or
objective conflicts. Keep this diagnostic and all fitted/label information outside
training. Generic contextual credit, factoring and action-equivariant sharing are
further design questions. Installing a corner-specific detector is not the next step.
