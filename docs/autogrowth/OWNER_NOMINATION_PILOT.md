# Experience-driven owner development: first pilot

Declared 2026-09-14, before running the pilot, on `codex/context-owned-decisions`
after mechanical checkpoint `129c1f78`. User authorized proceeding and requested
a pedagogical account of implemented behavior and remaining gaps.

## Mechanism

An owner is the runtime record for one contextual local decision and all its
competing scoring weights. Its expressions execute through ordinary formal
SCRIPTs; its observations come from terminals, and its errors from actual
selected-action scalar feedback. Owner metadata is a supplied developmental
primitive, not a graph-learned developmental controller or a new task label.

At conversion, sample at most 12 candidate routes from declared state-coordinate
equality readers and the actor's existing state-only expression definitions of
depth at most two. Sampling ignores names, phase labels and correct actions.
The candidate vocabulary remains fixed during this first pilot. Both arms
materialize/probe the same candidates using formal SCRIPTs, only on the actual
selected binding, before execution. A later chosen route is also checked for
agreement across all current bindings before the output terminal can act.

After actual feedback, the visited owner records the original prediction error
e = reward - predicted_reward for each observed candidate truth value. At every
64th local visit, a split nominee needs at least four observations on each side
and positive n0*n1/(n0+n1)*(mean(e1)-mean(e0))^2. Try nominees in descending score
order until one fits the whole-graph bounds. This is correlation-based nomination,
not proof of causal usefulness, a maturity certificate, or oracle model selection.
Only the visited owner can nominate, retire or grow. Other owners' weights and
applicable evidence do not change. Newly split owners start their own observation
counts; all parent observations/conditions remain accessible as ancestry.

Local lifecycle: at a development opportunity, retire non-bias contributions
whose local age is at least the unchanged grace (256 visits) and effective
weight magnitude below .02. Preserve their full record and block identical
rebirth in the same owner. A specialized child's scope is a new hypothesis;
the ancestor's retirement remains recorded rather than fabricated as child data.
If no split occurs, make one ordinary random 1..3-reader AND/OR/exactly-one
proposal within the visited owner, using the existing 8:1:1 operator prior.
All growth commits atomically within budgets. Weight learning remains active when
development is impossible. Bias cannot be pruned. No owner is frozen or merged.

## Fixed schedule and comparison

- Fresh seeds 10, 11; the existing four-state-bit/two-action Boolean environment.
  In the environment only, rewarded action is x when z=false, y when z=true;
  the fourth bit is irrelevant. All four state coordinates are available to
  routing; the action-parameter coordinate is excluded by scope, not by its name.
- Each seed starts empty, learns a common 128-action A-only prefix with the
  original recursive actor in flat mode and an eight-condition limit. Save two
  64-action prefix blocks. Evaluate the 16 rows only at the prefix endpoint.
- Fork into **owner splitting enabled/disabled**. Both receive candidate probes,
  the same local retirement/birth law, eta=.3 and exploration=.25. Both have at
  most four owners, 64 effective parameters including biases, 256 retained
  expression definitions, depth four, and 2048 physical vertices. The disabled
  arm cannot fork owners. These equal ceilings do not ensure equal realized cost.
- Each arm receives four 64-action blocks: first two contain each A row once
  and each B row seven times; last two reverse those frequencies. A separate
  seeded scheduler shuffles them. Every arm follows its full schedule regardless
  of scores; every block ends with frozen evaluation of all 16 rows.
- Exactly **1280 rewarded training actions + 288 scheduled evaluation actions**,
  20 completed training blocks and 26 checkpoint files (two empty starts,
  four prefix block endpoints, four fork starts, 16 continuation endpoints).
  Final verification repeats the 288 evaluations on disposable clones, separately
  counted; no training is replayed. Last-moment splits get no assumed benefit.
- One worker/CPU, numeric libraries one thread, 2 GiB address-space limit,
  64 MiB individual file ceiling, 540-second worker wall/CPU limit and independent
  570-second guard. Preserve partial evidence; no automatic retry or extension.
  A discarded engineering calibration, if used, cannot supply actors to this run.

This tests whether experience-driven owner specialization functions and how its
early learning/retention compares with the same new runtime without owner splits.
It is not yet the planned three-arm comparison against the original contributor
split learner and a local freezing controller. Those need a separate protocol;
the original learner stays unchanged and remains that comparison's baseline.

## Evidence and interpretation

Persist exclusive per-block action journals, original predictions and actual
active weights, candidate observations and selected owner IDs after the normal
interaction; instrumentation supplies nothing to the learner. Save immutable
source snapshots, checkpoint hashes and block ancestry. Verify the actual credit
arithmetic, source identity, checkpoint ownership/aliases and frozen evaluations.
Report all rows' gains/losses at each milestone and realized parameters/nodes,
not just the endpoint. Definition sharing is not common-trunk factoring, and
neither a nested split nor a high final score proves reliable retention.

First pass mechanism tests cover terminal-only candidate observation, no extra
reward, invalid feedback, disabled-arm equivalence before a split, evidence
ancestry, local retirement/birth isolation and restored continuation. No chess
rule, supplied context predicate, fitted weight or evaluation label enters play.

## Preflight adjustment before pilot training

The initial draft used three seeds and six continuation blocks per arm (2688
training plus624 scheduled evaluation actions). A discarded calibration measured
0.258 seconds per frozen action in a planted four-owner graph with379 vertices,
while the one CPU was also running legacy tests. Applying that conservative rate
to the entire original workload exceeded the planned wall budget. Before any
pilot actor was trained, reduce to seeds10/11 and four blocks per arm as specified
above:1280 training,288 scheduled evaluations and288 frozen reproductions,1856
actions in total. Keep every-block measurement and the symmetric two-block B/two-
block A continuation; no outcome, learning parameter or candidate rule determined
this size adjustment. Seed12 was not run or selected against on performance.
The calibration executed32 training and32 evaluation actions on separate seed0
actors with manually installed routing. None supplies state to the pilot. The
hard resource limits remain unchanged; no retry/extension if the pilot stops.
