# ReCoN Architecture Constitution

Status: active boundary for native KRK autonomy claims.

## Founding objective and clarified measurement boundary

The user's September 5, 2026 clarification is the controlling interpretation:
start with a top-level goal and generic embodiment, then learn useful terminal
readers, script/gate structure, temporal relationships, weights, and reuse by
playing chess and receiving scalar outcome feedback. Chess is the controlled
task for developing this architecture. A good chess score by itself does not
establish that the graph discovered a strategy.

The environment adapter owns the board and executes chess rules. The generic
ReCoN runtime executes requests, confirmations and learning rules; sharing a
process with the board does not give graph policy or structural-growth decisions
permission to inspect it directly. All observational influence on those
decisions must pass through declared terminal measurements. Action terminals
translate graph requests into primitive chess actions. A host helper may perform
that translation; it must not return an unrequested tactical choice or score.

The supplied feature schema may include geometry: the user explicitly allows
opponent-king-at-edge and distances between pieces. These are declared prior
measurements, not forbidden scaffolding. The target does not require starting
from raw square occupancy alone or learning the rules of chess. It does require
learning which measurements, parameter ranges and compositions support action.
Providing an opposition strategy, mate-family classifier, correct action, or
whole solution policy as a supposedly atomic measurement changes the claim.

For a fixed schema, the environment has a numeric feature vector `x` of length
`n`. Coordinates may have different units, ranges and value types encoded
numerically. Terminal `i` selects a subset `S_i` and measures `x[S_i]`, whose
length `k_i` may be one, two or more. Different terminals may therefore use
different dimensional subspaces of the same fixed-dimensional ambient space.
Normalize or otherwise define coordinate scales explicitly; version the schema
when its coordinate identities or meanings change.

A sparse coordinate, interval, threshold, projection or prototype reader can
be a valid terminal. Arbitrary trainable dense projections are not a prerequisite
for structural learning. What matters is that terminal birth, selection,
parameters, connectivity and survival are learned internally within the stated
representation family. A terminal need not inspect every feature or reconstruct
a complete chess board. Growth may probe a previously unused coordinate through
a trial terminal. It must not bypass the terminal boundary to mine the raw board
or obtain teacher-labelled candidate structures.

SCRIPT nodes compose and coordinate terminal/subgraph responses. SUB/SUR and
POR/RET supply generic request/confirmation and sequencing grammar; their useful
learned organization is part of the result. Generic before/action/after birth
templates may provide a way to act and observe consequences. Generating one
large stored triplet per encountered situation is not, by itself, evidence of
compact reusable strategic structure. Terminals remain leaves; sensor sharing
must preserve the behavior of independent request/frame/binding contexts.

The curriculum coach supplies positions, executes the submitted move and grades
its observed outcome. It does not choose structures to mature, inspect virtual
states to assign reward, select actions, or inject subgoal labels. The current
M1 contract explicitly rewards observed mate and punishes failure within one
own move. Internal eligibility, prediction error, affordance and consolidated
child value are computed by the organism, not supplied as additional teacher
judgments. Offline scientific inspection remains permitted and must not become
an online teaching channel.

Internal terminals obey the same measurement discipline for network state.
Virtual frames later change the context in which terminals measure; they do not
authorize a hidden solver or turn imagined success into observed success.
Separately trained modules should eventually be reused and prioritized through
learned contextual support and goal-relevant value, without hand-coded material
switches. This is a target to demonstrate, not an assertion of current coverage.

A small strategic motif may end with roughly a dozen nodes; no such bound has
been established for a full KRK policy. Node counts must account for complexity
in feature extractors, action primitives and binding rules. Discovery may require
more temporary candidates than the final consolidated motif. Do not impose the
user's compactness intuition as a hard initial growth cap.

### Source trail and interpretation

- [Published AAAI paper](https://ojs.aaai.org/index.php/AAAI-SS/article/view/42560):
  pages 317-318 describe the progression from fixed topology and learned
  coordination to exploratory structural growth. The stronger discovery wording
  on page 319 must be assessed against the actual implementation and evidence;
  it does not establish that every later from-scratch requirement already passed.
- [Recorded talk: Hector Cognitive Architecture for Structural Deliberation](https://www.youtube.com/watch?v=sIJL_UvSGBk).
  Located by title and author; the recording's transcript was not available in
  this review. Its content is not used as independent evidence here.
- [Earlier internal-terminal decision](INTERNAL_PROPRIOCEPTION_ARCHITECTURE_DECISION_20260713.md)
  already requires internal decisions to consume measurements through topology.
- [Earlier from-scratch plan](NATIVE_FROM_SCRATCH_KRK_PLAN.md) sets the empty
  learned-graph and real-consequence goal. Its older continuation/consolidation
  instructions yield to the user's explicit M1 coaching contract above.
- [Current implementation specification](FEATURE_TERMINAL_IMPLEMENTATION.md)
  separates implemented code from remaining terminal, credit and growth work.

## Four systems

### Environment

May execute legal chess transitions and expose generic world facts: legal move,
checkmate, stalemate, piece loss, and elapsed real steps. It may execute a child
policy to obtain a real rollout. It must not choose the learner's move using
mate distance, tablebase policy, a curriculum label, or a validator verdict.

The user-authorized V27 opponent boundary is different: Black may use exact
chess knowledge to choose its own legal defence after White has committed its
move. Only the played move/board is exposed to the learner, never solution
labels, search values, or hypothetical successful continuations. The current
rules-only opponent is exact for denying mate on White's next move, not for
unrestricted full-game WDL/DTM. This supersedes the older blanket prohibition
on engine-selected moves for the opponent only. Actual environmental outcomes
still determine reward; opponent search is not a reward-shaping oracle.

### Generic embodiment/genome

Provides sensors, legal-action interfaces, request/confirmation semantics,
plasticity, spawning, lifecycle, and generic aggregation. The current genome is
KRK-informed and must be reported as such. An empty learned graph is not a
sensor-free blank slate.

### Learner/ecology

Owns learned topology, action scores, competence values, eligibility, and
promotion/pruning state. It may receive only environment facts, graph state,
generic sensors, and value emitted by a mature outcome-grounded child. It must
not receive rung names, row IDs, correct moves, mate distance, exact-solution
predicates, or laboratory selection outcomes.

### Laboratory

May generate and stratify pools, calculate diagnostic solution labels, inspect
all state, run paired interventions, and select checkpoints under a frozen
protocol. Laboratory information must never change runtime routing, reward,
structural eligibility, plasticity, or action selection except in an explicitly
named oracle/control arm.

## Internal proprioception and virtual frames

Internal terminals are first-class generic embodiment. Their measurement
backends may be implemented by the host, as board sensors are, but learner
decisions must consume their values through ordinary graph topology rather than
hidden host reads. Persistent/internal-real terminals such as
`EVIDENCE_DEFICIT` are distinct from frame-local terminals such as future
`CHILD_RESPONSE` and `PREDICTION_SURPRISE`.

Virtual frames and internal terminals are orthogonal: a frame selects the real
or hypothetical state in which external and internal terminals are evaluated.
Dream execution must be side-effect-free with respect to persistent weights,
lifecycle, reservoir, maturity, reward, and real actuators. Internal
measurements may route requests but cannot create correctness, reward, rent,
maturity, consolidation, or grounding. A dream can never confirm or credit
itself; only observed outcomes or consolidated value from an outcome-grounded
mature child may supply learning credit.

## Named non-autonomous controls

- `virtual_frame_verified` directly executes the selected hypothetical child
  move and observes exact mate. It is an oracle-verified upper bound, not
  evidence that the child recognizes its competence basin.
- `prototype_gate` is outcome-calibrated and learned, but currently lives in
  the host rather than the ReCoN graph. It is a mechanistic intermediate, not
  the final graph-native availability mechanism.
- Constant, zero-value, shuffled-availability, disabled-hierarchy, and routing
  masks are laboratory controls. Their results diagnose causality but are not
  autonomous agents.
- Offline forced-mate predicates may score parent first-move correctness only
  in evaluation artifacts. They never enter training credit.

## Curriculum invariant

One persistent ecology advances Mate-in-1 -> Mate-in-2 -> outward KRK only after
100% disjoint validation and prior-rung regression. Mate-in-2 must ultimately be
credited when the mature Mate-in-1 child recognizes the real successor and
emits its consolidated value. Experience scheduling may use curriculum geometry;
the learner may not see the schedule label or solution.

## Experimental invariants

- All causal arms clone one frozen source checkpoint.
- Availability, emitted value, child routing, hierarchy scoring, topology
  growth, and successor aggregation are separate named factors.
- Parent first-move correctness and child completion are reported separately.
- Repeated selection data are development data. Regression is one-touch only
  after configuration freeze; final test remains untouched.
- An exposed failure is retired from confirmation but retained as learner
  counterexample/replay experience. Excluding it and its symmetries from the
  entire ecology may define a different engineering pool, but cannot demonstrate
  that the learner adapted to the failure.
- Checkpoints are immutable and fingerprint source code, commit, dependencies,
  behavior configuration, pools, and frozen source state.
- One seed or row-level significance cannot establish a training-level causal
  claim. Confirmation requires preregistered independent seeds and paired-row
  analysis.
- Composition must compare grounded-child x no-growth/mined-growth/matched-
  random-growth. A bootstrap-plus-growth arm versus no bootstrap is not a
  composition test.
- No R2 until a fresh, replicated R1 mechanism reaches joint 100% validation,
  regression, and protected R0 retention.
