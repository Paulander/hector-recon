# Why the first owner splits failed: saved-evidence audit

Read-only analysis on 2026-09-16 of the sealed Boolean seeds 33–35 pilot at
`snapshots/autogrowth/owner-action-balance-20260916-seeds33-35` and its complete
archive `reports/autogrowth/development/HECTOR_OWNER_ACTION_BALANCE_20260916.zip`
(SHA-256 `2c6fe1c376b76459df1a827cb2de37eaf57bed8d0c58518500a4fa43ab9c4214`).
No training, replay, parameter change, or chess evaluation was performed here.
The Boolean target is `x` when `z=false`, otherwise `y`; the fourth state bit is
irrelevant. These observations do not establish mate-in-2 competence.

## What failed, exactly

All first x-root trials had adequate parent, child, and randomized-access
exposure. They were rejected for **negative actual reward gain**, not for
unsupported certification. Both prospective windows were negative in every
owner-balanced seed. The matching action-contrast control also rejected x in
all three seeds.

| Seed | Balanced x review 1 | Balanced x review 2 | Full raw gain | Equal-row gain | Control raw gain |
| --- | ---: | ---: | ---: | ---: | ---: |
| 33 | -0.099 | -0.133 | -0.117 | -0.088 | -0.149 |
| 34 | -0.119 | -0.171 | -0.156 | -0.158 | -0.144 |
| 35 | -0.342 | -0.436 | -0.394 | -0.360 | -0.047 |

"Equal-row gain" is the unweighted mean of the 16 within-row differences in
observed reward between enabled and disabled trial access. All 16 rows had
observations under both arms. This removes the simple explanation that the
negative aggregate was only a lucky/unlucky mixture of easy rows. It does
not remove uncertainty from temporally coupled online learning or establish
an effect in other seeds.

The clearest loss is in the `x=false,z=false` region, where `act-a` is correct.
During the 512-action post-readiness window, parent versus child wins there
were: seed 33, **45/92 versus 24/75**; seed 34, **89/89 versus 72/90**; seed 35,
**71/79 versus 53/76**. The child often chose `act-b`: 51/75, 18/90, and 23/76
of those child-access actions respectively. In seed 34 the parent made zero
such mistakes. Those are actual submitted actions, not oracle predictions.

The x nomination was behaviorally relevant but not evidence that a copied
child scorer would add value. At birth, seed 33's parent and children had no
action-conditioned expression; the parent later acquired an x/z/action
expression with more exposure. Seed 34's `x=false` child inherited an
`x=true AND act-b` expression that can never activate inside its route, leaving
it action-blind until a later local birth. Seed 35's `x=true` child inherited a
similarly incompatible `x=false` expression. Thus copying every parent
condition creates dead or redundant child parameters, while each child gets
only about one quarter of the region's training actions during the trial.

The owner-balanced exploration law made this sharper in some runs: it boosts
the locally least-sampled action at the existing 0.25 exploration events.
Within an `x=false` child the usually useful `act-a` becomes common, so
coverage pressure can boost the usually wrong `act-b`. In seed 34, 17 of the
18 wrong `act-b` choices in the `x=false,z=false` child had a *negative*
unboosted chosen-action prediction; seed 35 had 19/23. This is consistent
with forced exploration, but the saved record does not flag individual
exploration events, so the exact causal fraction is not identifiable here.
The control also lost its x splits, so exploration balance is an amplifier,
not a complete explanation.

Scheduled greedy evaluations while a trial is pending disable child access
(`learn=False`); their scores describe the parent, not the provisional child.
The actual randomized training receipts above, rather than those evaluations,
are the evidence for the child-use comparison.

## What the positive y trial does and does not show

Owner-balanced seed 34 later accepted a y-root split with raw prospective
gain +0.208. During its review, child access won 64/80 context-B actions
versus parent access 37/77, but lost context-A performance (33/45 versus
51/54). Equal-row gain was only +0.088. The split can help under the current
training mixture, especially where y is relevant, while trading off already
learned competence. It is one positive online-use observation, not evidence
of a generally useful or retained subgoal; the final score was 14/16 at
high topology cost.

## Mechanistic conclusion and next experiment

`owner_trial.py` makes parent and children **exclusive alternatives** using
random access. `nominate_split` clones all parent conditions and gives each
child independent weights. `context_decision.py` applies the actual reward
update only to active conditions of the owner that acted. There is therefore
no parent–child contribution or reward-propagation contract in this path.
The test legitimately asks whether replacing the parent with children helps;
it does not test whether useful local specialists can cooperate with a parent.

The most economical next hypothesis is a **route-gated residual child**, not a
general intrinsic-reward system: keep the parent scorer active for every
action, initialize the child contribution at zero, and let the child add a
small action-conditioned correction when its route is active. The joint
prediction receives one environmental outcome; eligible parent and child
weights can both receive portions of its prediction error, with explicit
normalization to avoid double credit. Parent-only versus parent-plus-residual
access can still be prospectively compared. A child then serves its parent
by improving the jointly selected action, not by maximizing activation.
The route and contribution must remain formal graph conditions, not an opaque
Python action picker or externally supplied subgoal.
This is a proposed local credit contract, not a proven repair.

First test it data-free: zero-residual behavior must exactly match the parent;
an incompatible inherited condition must not consume a live parameter;
actual outcome credit must reach the parent on both access arms and the child
only when active; no unchosen action gets feedback; snapshot/replay must be
exact. Then use a tiny bounded Boolean comparison against the current cloned
trial, with separate reporting for context A/B, prospective gain, topology,
and retained parent competence. Reject it if the residual does not improve
prospective use or again trades away the already solved region. Do not launch
a chess or long run on this audit alone.
