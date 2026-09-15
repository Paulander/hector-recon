# Why seed 4 lost two successes after reaching 16/16

Completed 2026-09-14 while the user runs the independent Mac replication.
This is an offline follow-up to `RECURSIVE_SPLIT_BUDGET_RESULTS.md`, covering
seed 4 cap12's last 128 recorded updates, events 1664–1791. No new training,
evaluation actions, fitted weights or actor mutations were performed.

**Actual weight credit causes the entire regression.** The correct B branch
survives and improves, but two coexisting, functionally identical A contributions
receive shared credit that overwhelms that improvement. Pruning and the final
split change neither lost row's action margin.

## The competing paths

In this Boolean lab, x/y/z are three measured bits; a fourth bit is irrelevant.
Context A means z=False and rewards choosing x; context B means z=True and rewards
choosing y. Action a represents False, b represents True. These names and formulas
are our offline interpretation, not labels or a solution supplied to the learner.

The lost rows 6/7 both have x=False, y=True, z=True; they differ only in the fourth
bit. Their correct action is b. Three learned contributions determine their
relative score at the start of this interval:

| Contribution | Exact simplified condition | Starting weight | Final weight |
| --- | --- | ---: | ---: |
| 31 | x=False AND y=True AND action=a | +0.513524 | +0.692928 |
| 35 | x=False AND y=True AND action=a | -0.903835 | -0.724431 |
| 33 | x=False AND y=True AND z=True AND action=b | -0.306726 | -0.235619 |

The equivalences were verified on all 32 possible state/action cells. Contributions
31 and 35 have different nested syntax and separate histories, but identical
activation functions throughout this task. Both are generation-two descendants;
33 is generation three. A separate equivalence group, 28/30/34, exists elsewhere.
This is not raw sensor aliasing: the z coordinate distinguishes A and B.

For either failed row, before the final split:

\[
m_B = Q(b)-Q(a)=w_{33}-w_{31}-w_{35}.
\]

The b contribution does not have to be positive for b to win; the relative sum
matters. At the endpoint, the last split also adds `w39-w38`, which is exactly
zero because both children inherited the same parent weight. It does not explain
the loss. The original, specific B contribution remains live.

## Exact credit accounting

| Change in correct B margin | Each lost row |
| --- | ---: |
| At event 1664 | +0.083586 |
| Credit from successful A-context actions | -0.901505 |
| Credit from unsuccessful A-context actions | 0.000000 |
| Credit from successful B-context actions | +0.071107 |
| Credit from unsuccessful B-context actions | +0.542696 |
| Pruning | 0.000000 |
| Split installation | 0.000000 |
| At event 1792 | **-0.204117** |

The fixed final block contains 112 A-context and 16 B-context actions: A succeeds
101 times and fails 11; B succeeds 13 and fails 3. Most do not affect these two
rows' relative score. The relevant broad A terms each participate in **26 successful
A actions and two unsuccessful B actions**. The specific B term participates in
**two successful B actions**. Each broad term gains a net +0.179404; the specific
B term gains +0.071107. Therefore the net margin changes by
`0.071107 - 2 * 0.179404 = -0.287702`.

This is learning from actual successes and failures in both contexts, not an
absence of positive B experience. The broad A terms cannot independently retain
different weights in A and B because their conditions omit z.

The first strict loss occurs at **event 1668**. The actor correctly chooses a on
A row 5 and receives +1. It predicted 0.419852; four contributions were active.
The unchanged credit law applies:

\[
\Delta w=\frac{0.3(1-0.419852)}{1+4}=0.034809.
\]

Contributions 31 and 35 each receive that increase, reducing the B margin by
0.069618: **+0.036321 → -0.033297**. The specific B term is inactive on this
actual A action and receives no update. No structure changes at that event.

Both B rows recover at 1674, lose again at 1730, recover at 1738, lose at 1768,
recover at 1771, and finally lose at **1782**. All four losses follow successful
A actions, through the same two broad terms. There are no other strict row losses
in the interval. The pruning at 1696 removes a condition gated by z=False and has
zero effect on either B row's margin. The split at 1792 preserves all sixteen
score margins exactly in the reconstruction.

## Why didn't the guided growth rule separate those paths?

It already has a relevant signal. Reconstructing the eligible nominations
immediately before the last split gives:

| Rank | Source | Candidate context | Residual score | Samples on the two sides |
| --- | --- | --- | ---: | --- |
| 1 | 6: x=False | action=b | 22.8863 | 493 / 275 |
| 2 | 35: broad A term | x=False AND y=True AND z=True | 20.5452 | 50 / 5 |
| 3 | 31: broad A term | x=False AND y=True AND z=True | 14.6113 | 66 / 13 |

Both separating candidates satisfy the existing support/depth/duplicate checks.
They are not blocked by missing sensors or the minimum support threshold. The
ranked maximum is source 6 and reproduces the actual final nomination exactly.
The statistic weights conditional residual contrast by sample counts; it estimates
prediction-error distinctions rather than directly detecting or protecting lost
policies. Source-specific histories differ even when two current functions agree.

The twelve-split allowance is exhausted at that point. The last split is installed
at event 1792 and receives **no subsequent training in this protocol**. Do not
claim to have tested how its child weights would behave after further experience.
Similarly, the second/third nominations being relevant does not prove that choosing
them would autonomously learn or retain the desired policy. No alternative was
installed or tested here.

## What this changes for the next decision

The current mechanism performs partial contextual specialization. Growing one
specific winning-action path does not isolate its decision while broad competing
paths remain plastic. That is the concrete limitation to carry forward, rather
than treating hierarchy itself as ineffective or assuming a missing node type.

Functional duplication is also measurable here. Simply adding the two weights
and replacing their branches could preserve immediate scores, but would change
the present update normalization and participation multiplicity. It would also
require handling overlapping history without double-counting experiences.
Deduplication is therefore a separate learning intervention, not a proven free
retention fix.

Let the Mac's predeclared seeds 7/8/9 finish unchanged. Consolidate its row-level
trajectories, actual split counts and any failures with this selected-actor causal
accounting. If its actors regress, check whether the same incomplete context
separation/overlapping-credit pattern recurs before choosing a larger split budget,
a different nomination statistic, or a credit/retention mechanism. The local
replication and this explanation answer different questions; neither replaces
the other. No new learner change or further training is started by this report.

## Verification and reproducibility

All 128 logged pre-action predictions, active contribution sets, candidate truth
values and before/after weights reconstruct from the event1664 checkpoint. Maximum
prediction discrepancy is **1.78e-15**; reconstructed endpoint weights match
exactly. Computed initial/final margins agree with all sixteen recorded evaluation
outcomes. Source checkpoint/evaluation/journal hashes are retained. Historical
block payloads and the original verifier failure/resolution remain unchanged.

The analysis uses the independent process guard, one Linux CPU core, a 2 GiB
address-space cap and a 90-second worker limit (100-second supervisor). It calls
no actor `act`, `observe` or `refine` method. No new environment actions occurred.

[Reconstruction script](../../scripts/autogrowth/attribute_recursive_budget_loss.py),
[event ledger](../../reports/autogrowth/development/RECURSIVE_BUDGET_LOSS_20260914.json),
[branch and nomination checks](../../reports/autogrowth/development/RECURSIVE_BUDGET_LOSS_DETAILS_20260914.json).

Reproduce the event ledger using the script's `--run` and a fresh `--output`.
Add `--details-from` pointing to that ledger to reproduce exact branch equivalences
and the final nomination ordering without repeating the arithmetic reconstruction.
Code and results remain local to the work branch; nothing was published remotely.
