# Recursive context specialization: bounded first prototype

Isolated branch `codex/recursive-context-specialization`, from local `637e59e3`.
Authorized 2026-09-09 after the corner-interference discussion. This tests local
recursive refinement and inheritance, not complete competing goal modules.
The interrupted learning-rate experiment remains closed and is not resumed.

## Mechanism and information path

One active contribution `w*f` may become `w0*(f AND NOT g) + w1*(f AND g)`.
Both new weights copy the parent's fast and slow values into independent objects.
Because the two paths partition f, all action scores initially remain unchanged.
The old direct scoring edge is removed to avoid counting it again. Its complete
condition/evidence record remains in history. New context-specific evidence begins
empty; parent evidence is ancestry, not invented evidence about either child.

Expressions are immutable recursive AND/OR/exactly-one definitions. NOT g is
exactly-one(TRUE,g). Definitions are reused, but SCRIPT instances retain a single
owning parent. Input terminals may be shared within one action binding. All
terminals remain leaves; there is no shared mutable SCRIPT request across callers.
Weights are shared across action bindings, independently plastic between sibling
contexts. Other contributors and bias remain plastic, so this does not guarantee
global retention. New definitions are versioned by construction, not silently
edited in all users. Working memory is current terminal/request state and pending
action credit; no temporal memory or global knowledge broadcast is introduced.

At the common prefix endpoint the organism randomly samples 12 context expressions
from its own live definitions and declared equality readers. Coordinate names,
task identity, action spelling and standalone atom competence do not select them.
Contexts are evaluated by formal SCRIPTs on the actually selected binding before
execution. After actual scalar feedback, active source contributions collect
residual sums/counts with each context true/false. Candidate split score is the
reduction in a two-group constant-residual fit: n0*n1/(n0+n1)*(mean1-mean0)^2.
It is a nomination statistic, not proof of causal usefulness or goal competence.
It conditions on selected-action participation, which can itself bias nomination.

At most once every 128 subsequent episodes, ranked chooses the largest eligible
score; random chooses uniformly among eligible source/context pairs; flat proposes
one ordinary shallow condition. A context needs four observations on each side.
No available split falls back to the same single shallow-proposal opportunity.
All roles use the unchanged selected-action reward-error update and aged weak
contribution retirement. Retired records remain; retained expressions/readers are
bounded by the physical/definition limits. The same nominal weighted-contribution
cap is not the same physical graph cost; both are reported.

There are no alternative-action rewards, injected fitted weights, context labels
or coach-side topology decisions. Laboratory planted graphs test primitives only.
The actual learning run starts empty. The growth rule is supplied generic code,
not a graph-learned growth policy. The current runtime cannot yet implement the
full proposed ecology of competing independently trained goals.

## Fixed first run, declared before outcomes

- Non-chess Boolean environment: four observed state bits and one action-binding
  bit; two opaque actuators. Environment reward +1 iff the chosen action matches
  x when z is false, y when z is true, else -1. Fourth state bit is irrelevant.
  z is an ordinary unnamed coordinate, never a supplied context/growth label.
- Three seeds, 1/2/3. Common 256-action prefix exposes the eight z=false rows
  equally. Six continuation blocks of 128 actions: first four give every z=false
  row two appearances and every z=true row fourteen; final two cover all rows
  equally. Orders are fixed independently of learning and scores.
- Clone each prefix into flat, random and ranked; 768 more rewarded actions each.
  Weight cap 16 in prefix and 24 in every continuation; at most six splits,
  expression depth four, 160 expression definitions, 4,096 physical nodes.
  Same eta=.3 and exploration=.25. After the prefix all roles separate growth
  and exploration RNGs; exploration draws match across the final paired arms.
- Evaluate all 16 rows after the prefix and every continuation block. These are
  development truth-table measurements, with learning/exploration disabled.
  Report both context groups and lost/gained rows, alongside total score.
- Exactly **7,680 training + 912 evaluation = 8,592 actual actions** if complete.
  Single process/core, 2 GiB address-space ceiling, interrupting 600-second total
  wall cap, no automatic retry/resume. Logs flush after actual feedback; checkpoints
  every block. An incomplete unit remains marked pending and is not inferred done.
- Flat controls still undergo their own ordinary births and pruning; they are
  unchanged in the isolated aspect that no recursive split occurs. Different
  proposal/retirement histories make this a mechanism-package pilot. Ranked versus
  random compares selection among each actor's currently eligible pairs, whose
  pools can diverge. Three seeds are insufficient for broad superiority claims.

The task is within the shallow grammar's representational scope: conditioning an
action-bit reader on z and x or y requires only three coordinate literals. We did
not choose a task known to be impossible for the flat control. It remains a
deliberately contextual toy, not chess evidence or a test of arbitrary hierarchy.

A separate discarded 32-action engineering calibration took 0.854 seconds with
85 physical nodes. It is outside the 8,592 experimental actions and supplies no
trained state to the experiment. Before launch, the wall cap was set to ten
minutes to allow larger nested graphs and checkpoint/evaluation overhead. The
experiment stays in the active execution session; cross-turn persistence is not
assumed. No parameter is changed in response to the experiment's scores.

## Verification

Focused tests cover unchanged prefix against the original learner, exact score
inheritance over all inputs, nested AND/OR/NOT execution, single-owner SCRIPT
instances, separate sibling credit, preserved ancestry, stale feedback rejection,
checkpoint continuation, renamed actuators, and resource/depth constraints.
Runtime/source hashes and checkpoints accompany the bounded run. Core production
learner, formal engine, chess feature space and rewards are unchanged.

## Completed pilot and limits

Executed the fixed protocol at `36429382` in **447.38 seconds**, one thread/core,
with peak RSS **34,148 KiB (33.35 MiB)**. The runner reports all **7,680 training
and 912 scheduled evaluation actions**. The 32-action discarded calibration is
separate. A subsequent 192-action frozen check reproduced every prefix and final
action/outcome directly from the twelve saved actors, with no training updates.

| Seed | Prefix | Flat | Random splits | Guided splits |
| --- | ---: | ---: | ---: | ---: |
| 1 | 12/16 | 13/16 | 13/16 | 15/16 |
| 2 | 6/16 | 8/16 | 8/16 | 12/16 |
| 3 | 11/16 | 12/16 | 15/16 | 16/16 |

Guided selection finishes higher in all three pairs against either control.
All three guided actors autonomously refine an already refined descendant
(generation two); maximum expression depth is three. Random splits also reach
generation two in seeds 1 and 2. These are actual during-learning births, separate
from planted mechanism tests. Each split arm performs six refinements as declared.

Retention remains incomplete. Relative to the common prefixes, guided actors
gain 18 and lose **four** solved rows (one in seed 1, three in seed 2). Random
actors also lose four, while gaining 11. Flat actors gain 11 and lose seven.
Thus the guided-versus-random aggregate gain is acquisition, not fewer lost
prefix successes. Against the final flat policies, guided actors gain 13 rows
and lose three; totals alone conceal those disagreements.

Final live weighted-contribution counts for flat/random/guided are 13/14/17,
13/9/13 and 15/18/15. Physical node counts are 91/143/159, 91/127/131 and
103/163/149. The experiment matches caps and growth opportunities, not realized
parameter counts or physical computation. This three-seed toy result supports
further study; it does not establish equal-compute superiority or general M1
retention. No chess actor was migrated or trained in this prototype.

All 30 distinct focused tests passed, including seven new mechanism tests. All
57 checkpoint payloads restore with valid formal pairs, leaf terminals, correct
weight aliases and distinct sibling weights. Source hashes match the run code.

**Evidence preservation is incomplete.** The saved action logs retain 7,576 of
the 7,680 reported training records. Seed 3 prefix events 251..255 and ranked
events 413..511 are missing: **104 records total**. Eleven stale pending markers
also remain, despite later verified checkpoints and completed evaluation reports.
The cause of these filesystem discrepancies is undetermined. The raw files and
markers are preserved; no missing records were fabricated and no training was
replayed. Frozen restoration independently verifies every prefix and final score,
but exact training-credit attribution through the missing intervals is unavailable.
Treat the result as completed with incomplete action logs, not fully verified
trajectory evidence. Before another run, replace the growing append log with
immutable block journals and verify their completeness before declaring completion.

The complete record is
`reports/autogrowth/development/RECURSIVE_CONTEXT_20260909.json`; private payloads,
logs, source hashes and the explicit gap record are preserved in the checkpoint ZIP.

Two architectural qualifications remain central. First, candidate contexts may
include action-binding coordinates: this is state-action specialization, not yet
a situation-only parent selector. Second, the sampled context vocabulary is held
fixed in this pilot; recursion refines the source contribution repeatedly. It
does not yet discover arbitrary new OR trees over goal modules, learn temporal
procedures, or decide whether an entire challenger policy should replace an
incumbent. Structural interning is supplied generic reuse, not learned compression.
The next mechanism question is retention/selection under this local split law,
with complete records, before migrating learned chess states or adding goal islands.
