# What the fresh-start scores measure and why cases fail

Read-only follow-up,2026-09-15. **The16 cases are the exhaustive states of a
four-bit Boolean task. They are not mate-in-one chess positions.** The preceding
results summary should have stated that explicitly. No new chess performance
was measured by these six runs.

Inputs are x,y,c,n. The correct output bit is x when c=0 and y when c=1; n is an
irrelevant distractor. Two actions emit output0 or1. The environment returns
+1 for the correct actual action and−1 otherwise. The learner receives no target
bit, task formula or counterfactual outcome. The supplied typed terminal schema
also exposes the candidate action's bit as a fifth coordinate.

There are2^4=16 input states, eight with c=0 (A) and eight with c=1 (B). A score
of14/16 means the saved greedy policy answers14 correctly on a frozen clone.
It is not a count of independent learned skills. Checks occur every64 training
actions. The task rule remains fixed while sampling shifts:640 A-only actions,
640 with7/8 B, then640 with7/8 A. Some initial ties happen to be correct; early
correctness alone does not establish a learned or stable solution.

## Weight learning and structural growth

Each condition has an owned scoring parameter on its SUR contribution into an
action option. Binding instances within an owner use that same parameter;
different owners have independent parameters. Structural routing and logical
links are not all independently trained numeric weights.

After every actual training action, let r be its scalar reward, q its predicted
score excluding exploration, and m the number of active scoring contributions,
including the owned bias. Every participating weight receives

    delta_w = 0.3 * (r - q) / m

Only contributions active for the selected action and owner receive this update.
Other owners are untouched. Weight learning continues during development and
after a high evaluation score; evaluation is never a freeze signal. The current
law trains reward predictions, without directly imposing preservation of every
previously correct action ordering.

Every64 visits to the active owner, the local developmental rule assesses
pruning and growth using accumulated local observations and actual residuals.
It can split on supported state-only residual differences, up to four owners.
A split copies the parent's whole scorer into two independently plastic children
and starts their local observation counts at zero. It preserves the initial
decision scores; it does not retrain children from zero.

If no split succeeds, one compatible, previously unseen condition can be born
from the fixed24-candidate pool. Random mode chooses uniformly; ranked mode uses
local residual evidence with a25% random path and a random fallback when no
supported score exists. A new condition starts with weight zero and learns from
later actual activations. A successful split replaces that birth opportunity in
the current schedule. Ordinary low-weight retirement remains enabled; there is
no freezing or mature-skill protection rule in this experiment.

## Ranked seeds12 and13 have different histories

| Ranked seed | Best measured total | Final total | Final wrong rows | Same final correct set continuously at measured checkpoints since |
| --- | ---: | ---: | --- | ---: |
| 12 | 15/16 | 14/16 | 10,11 | 1792 |
| 13 | 14/16 | 14/16 | 7,10 | 1280 |

Seed12 reaches15 at1344,1600,1664 and1728. Row10 is correct at960, then wrong
from1024 through1920. Row11 is correct at1024–1344, wrong at1408–1536, correct
again at1600–1728, then wrong from1792 onward. Both endpoint failures had been
answered correctly earlier; this is mixed retention, not two never-found cases.
It never solves all16 simultaneously at a scheduled checkpoint.

Seed13 keeps exactly the same14 correct from1280 through1920. It never exceeds14.
However, its two final failures have different histories: row10 is never correct
at any scheduled checkpoint, while row7 is correct through896 and becomes wrong
at960. At896 its correct-action margin is+0.2263, so that last correct result is
not merely the untrained tie-break. Thus the final plateau is stable, but the
entire earlier history is not loss-free.

All time ranges above refer to the64-action measurements, not uninterrupted
behavior between them. Row identities are zero-based x,y,c,n binary order.

## Common failure pattern and representational capacity

| Ranked seed / row | x | y | c | n | Required output | Actual final output |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 /10 | 1 | 0 | 1 | 0 | 0 | 1 |
| 12 /11 | 1 | 0 | 1 | 1 | 0 | 1 |
| 13 /7 | 0 | 1 | 1 | 1 | 1 | 0 |
| 13 /10 | 1 | 0 | 1 | 0 | 0 | 1 |

All are B cases with x!=y, where applying the earlier A rule gives the wrong
answer. All final A cases are correct in every arm. Seed13 additionally behaves
differently on otherwise identical cases when the irrelevant n bit changes.
The early owner partitions include distractor-based divisions; their capacity
was exhausted before c varied in training. A and B examples can therefore still
share a decision owner and its broad scoring features.

An offline linear feasibility check finds that **all three ranked final
structures can represent correct choices on all16 states**. Rationalized witness
weights satisfy the exact integer feature constraints, including the actual
tie-break rule. These weights are used only to check feasibility and are never
installed or executed as a policy. Thus ranked12/13's endpoint failures are not
forced by a lack of final representational capacity. Their learned coefficients
have not reached or retained a jointly correct configuration. This does not
prove that more training under the same law will find one.

The random controls differ: seed12 cannot distinguish rows10 and14 in its action
score difference, although they need opposite outputs. Random seed13 also has
incompatible exact aliases and a forced tie failure. Their final structures
cannot solve all16 by changing weights alone. Random seed14 has enough capacity
but wrong learned weights. Its failures are B rows14/15, where x=y, so the
x!=y pattern applies to the ranked failures, not every control failure.

## Actual credit explains the observed losses

For selected loss intervals, sum each recorded weight update multiplied by its
contribution to the failing row's correct-minus-wrong action score. The totals
match the change between saved checkpoints. There is no splitting or retirement
in these intervals; new scoring conditions enter at zero weight.

| Ranked seed / row | Interval | Correct-action margin before → after | Contribution from A training | Contribution from B training |
| --- | --- | --- | ---: | ---: |
| 12 /10 | 960→1024 | +0.0268→−0.3884 | −0.2707 | −0.1446 |
| 12 /11 | 1728→1792 | +0.0069→−0.0801 | −0.1602 | +0.0731 |
| 13 /7 | 896→960 | +0.2263→−0.0804 | −0.0094 | −0.2972 |

For seed12 row11, its own B feedback improves the margin by0.0731, but updates
from A rows9/13 worsen it by0.1602, flipping the decision. For seed13 row7,
the largest negative term is−0.4924 from another B case, row3, outweighing
row7's own+0.1952 correction. That loss occurs during mostly-B training, so
it cannot be blamed solely on the later return to mostly A.

This identifies interference through shared scoring weights inside an owner.
Ownership isolation between different owners still holds. The arithmetic
attributes the realized update sequence; it is not a counterfactual claim about
what another growth schedule or training rule would have done.

The analysis script and machine-readable findings are
`scripts/autogrowth/analyze_owner_fresh_failures.py` and
`reports/autogrowth/development/OWNER_FRESH_FAILURES_20260915.json`.
All saved checkpoint choices are checked by offline score arithmetic. No new
environment actions, training, fitted-weight installation or checkpoint edits
are performed. The original cohort remains closed.
