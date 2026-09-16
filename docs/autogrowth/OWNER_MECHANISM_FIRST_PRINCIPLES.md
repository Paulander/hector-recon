# Owner growth: first-principles mechanism audit

2026-09-16; no learner edits, tests, replay or new training in this audit.
Relevant execution tree: private branch `codex/context-owned-decisions`, code
tree `341267534fd318a3ec4f67f7c4dcf36e6d0313d3`. The sealed seeds 33–35
pilot is used only to identify concrete examples, not to fit a remedy. This
Boolean action-choice prototype is not the native chess mate-in-2 learner.

## Correcting the “impossible child” claim

There are three different objects:

1. A **child route** `P AND g` or `P AND NOT g`.
2. A **newly proposed condition** `F` within an existing owner's route.
3. A **copy of an old parent condition** into a new child.

`ActionContrastEvidence.score` requires observations in all four route-side ×
executed-action cells before automatic nomination. The first x-route child
paths therefore had witnessed states; they were not impossible children.
`CompatibleOwnerDevelopment._compatibility` and
`BirthSearchOwnerDevelopment._birth_local` reject a *new* condition only if
`P AND F` is proven unsatisfiable. `TrialOwnerDevelopment.nominate_split`
does not call that check on **inherited copies**. Thus an `x=false` child may
contain a copy of `x=true AND act-b`. It is a permanently silent condition
and a resource cost, but it does not make the child path impossible.
Nor is route satisfiability an unconditional API invariant: a directly
planted `nominate_split`/`split_decision` route is checked for reader scope
and depth, not for nonempty `P AND g` and `P AND NOT g`. Automatic
action-contrast nomination supplied the needed witnesses in this run. A
future mutation source should not assume the direct API alone excludes
impossible child routes.

More importantly, the silent copy **cannot explain immediate forgetting**.
For state `s` in a new child's route `P`, the compiler changes each inherited
condition `F_i(s,a)` to `P(s) AND F_i(s,a)`, and copies its weight exactly.
Since `P(s)=true`, every inherited term has the same value as in the parent:

    Q_child(s,a) = Σ_i w_i [P(s) AND F_i(s,a)] = Q_parent(s,a).

The existing planted-split fixture checks this score-preservation property
over its entire small Boolean domain. A condition impossible under `P` was
also false in the parent on those same states. My previous audit overstated
the behavioral importance of the dead copies; cleaning them would save
structure, not repair the observed learning failure by itself.

## The actual mismatch: evidence names an interaction, mutation forks a scorer

The formal engine sums the SUR weights of confirmed conditions into each
action option. For two legal actions, the decision margin is

    D(s) = Q(s,act-b) - Q(s,act-a)
         = Σ_i w_i [F_i(s,act-b) - F_i(s,act-a)].

A state-only feature, including the owned TRUE “bias,” has zero bracketed
difference. If every condition live in a region is action-invariant, changing
their weights by *any* amount leaves `D(s)=0`. Local reward updates can change
value prediction there, but cannot change action ranking until an
action-sensitive expression or edge is born. The fixed tie order then chooses
`act-b` unless exploration overrides it. This is a structural zero-gradient
statement about ranking, not a conjecture about insufficient training time.

The action-contrast nominee measures a difference-in-differences of actual
selected-action residuals across `g=false/true` and the two actions. That is
evidence for a missing **route × action** interaction in the scorer. But the
mutation it requests is a copy of the *entire* scorer into two independent
owners. Copying does not add an action-sensitive direction. In seed 33 both
x children were action-blind at birth. In seed 34 the `x=false` child had
only TRUE and an impossible-on-that-route `x=true AND act-b` term; its action
margin was zero. In seed 35 the `x=true` child inherited an incompatible
`x=false` action term. The valid routes did not yet possess the local scoring
direction that the nomination evidence called for.

The generic birth system does not close this gap reliably. It draws from a
finite random pool of 24 definitions and independently ranks them by a
different, single-feature residual score. At each 64-visit opportunity,
`TrialOwnerDevelopment._run_development` attempts an ordinary condition birth
*then* nominates a whole-owner split. In seeds 33–35 the first x split and a new
zero-weight parent condition were created at the same episode 64, before that
condition could learn. The parent continues learning on about half the trial
assignments; each child gets roughly a quarter and may wait for its own
action-sensitive birth. Exclusive access credits only the active owner.
Hence the split tests independent retraining under less data, not a useful
child's contribution to its parent.
The first prospective review in each seed ended before the 640-action
curriculum boundary and was already negative. The failure is not merely a
later shift from x-relevant to y-relevant examples.

Whole-owner fission is not required by the Boolean target's representational
class. Let `b` mean choosing `act-b`. A single owner's allowed conjunctions
can realize the exact margin for all 16 rows:

    D = -1·[b] + 2·[b AND NOT z AND x] + 2·[b AND z AND y].

It is +1 precisely when `act-b` is correct and -1 otherwise. The finite
sampled candidate pool may lack these exact terms, so this is a capacity
proof, **not** a claim that the present learner can discover them. It shows
that the x residual signal alone does not justify paying for a full fork.

The owner-balanced exploration pilot adds a separate confound. Its fixed
0.25 exploration event boosts the least-used binding of the active owner
strongly enough to win the graph choice. A child whose route mostly requires
`act-a` tends to keep `act-b` least-used and can be forced toward it even
after learning. Parent and child then have different exploration policies
merely because ownership changed. This can amplify a child-use loss; it is
not the whole explanation, since uniform-exploration controls also rejected
the x splits. Do not promote owner-balanced exploration as a general law.

## Minimal mechanism repair to implement before more play

Treat persistent route-dependent action residual as a request to **bud an
action-sensitive local contribution**, not immediately fork all decision
weights. Compose the observed state-route micropattern `g` with an already
formal action-varying terminal or affordance pattern `h(s,a)`. Attach the new
SCRIPT condition as a zero-weight contribution to the still-active parent
option. Its initial zero weight preserves every action score; subsequent
actual selected-action reward updates it through the existing normalized
local error and SUR weight. Negative as well as positive weights must be
allowed. A state-only subpattern may be a useful component, but by itself
must not be mistaken for a new action preference.

This is not an externally chosen correct move: `g` comes from local residual
evidence; `h` is a graph-measured pattern that differs across available
bindings; and only the action actually executed receives outcome credit.
For chess, `h` should be a relational move-effect/affordance feature rather
than an absolute UCI move identity. Compatible-growth checks still exclude
proven contradictions; unknown combinations remain eligible. Existing
weight/age/resource competition can retire buds that do not become useful.
Do not add a separate intrinsic reward for mere activation.
The simple `coach/terminal.py` chess port already distinguishes board-only
readings from candidate-move measurements such as target-to-king distances
and target alignment. Those are plausible `h` inputs without encoding a
correct move. This does not assert that the separate native R0 chess graph
uses this exact port or that these measurements suffice for mate-in-2.

Reserve whole-owner fission for a later, distinct question: does a shared
parent continue to suffer demonstrable cross-context interference *after*
cheap action-sensitive compositions have had a chance to learn? Its current
action-contrast statistic does not answer that. A route split may still be
valuable for protection or capacity, but it must not be the default response
to the gradient signal for one missing interaction.

The narrow code boundary is `owner_action_contrast.py` (the interaction
evidence), `owner_birth_search.py` (local proposal and finite-pool limitation),
and `owner_trial.py` (the premature birth-then-fission lifecycle). The core
formal action scorer and selected-action credit in `context_decision.py` can
initially remain unchanged. This is a design decision, not an implemented
repair. No training or tests should be inferred from this document.
