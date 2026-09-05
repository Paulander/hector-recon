# Feature terminals, scalar feedback, and internal growth

Status: implementation specification following the user's clarification.
The scalar-feedback correction is implemented. The feature/selector migration
and growth changes below are not yet implemented. The existing 67/128 result
uses a hybrid native learner and cannot establish the target architecture.

## What exists, and the actual gap

| Component | Current code | Required change |
| --- | --- | --- |
| External feedback | `coach/interface.py`, `coach/exercise.py` | Done: scalar reward plus binding to the organism's already selected action; diagnostic reasons stay in the coach log. |
| Observation | `BoardSensor.measure()` returns a piece-list snapshot; `NativeOrganism.act()` reconstructs a Python board | Publish a numeric feature basis; make graph requests reach it through leaf terminals. |
| Terminal representation | Native triplets create terminals for fixed feature keys | Spawn coordinate or sparse projection readers with their parameters persisted in graph-owned state. |
| Earlier representation machinery | `nodes/stem_cell.py` has feature masks, centroid/medoid prototypes and transition samples | Reuse the existing lifecycle and sample ownership where sound. Prototypes are not arbitrary learned linear projections. Audit the old stage-aware integration before reuse. |
| FeatureHub | `features/hub.py` centralizes a hand-written feature registry | Reuse measurement/caching mechanics, not its entire tactical/phase vocabulary as an allegedly neutral base. |
| Action selection | Native Python candidate scoring feeds a fresh anonymous formal choice graph | Persistent request/confirmation paths must compute candidate support and emit the action through actuator terminals. |
| Credit | `learning/intrinsic_credit.py` has eligibility, fast/slow values and grounded child providers | Connect those mechanisms to the actual active terminal/edge/parent paths and terminal parameters. |
| Growth | The coach adapter materializes selected before/action/after triplets | Integrate local residual-driven candidates with the existing stem-cell lifecycle; do not introduce a second lifecycle controller in the coach. |

## 1. Explicit base, actual terminals

Define a versioned feature schema and a frame-local numeric vector `x`.
The conservative first chess base is piece-type/color occupancy by square,
side to move, and the rule state needed by the chosen exercise. KRK M1 does not
need castling or en-passant fields; full chess does. Additional geometry, if
included, must be named and frozen as supplied prior knowledge. The base must
not quietly acquire mate-family, opposition-plan, endgame-stage, action-quality,
distance-to-mate, or winning-move coordinates.

Piece occupancy is one possible explicit base, not a claim that the user's
phrase "feature space" requires raw squares only. Any richer proposed basis
needs an equally explicit inventory. The architecture issue is who learns and
owns the readers and compositions, separately from how much prior structure the
base supplies.

A terminal first measures `z = w dot x + b`, then applies its response rule,
for example `a = sigmoid(z)`. A basis-vector `w` and zero bias measure coordinate
`x[k]`; an identity response returns that coordinate directly. A prototype/distance reader is a different permitted
representation, not the same operation with different terminology. Purely
linear layers composed without any nonlinearity remain linear; graph gates,
thresholds or other nonlinear interactions are needed for richer relations.
Measured value, continuous activation, learned expected return, and discrete
request/confirmation state have distinct meanings; do not collapse them into
one scalar because they happen to be carried by the same terminal.

The environment owns measured values. Each terminal owns its feature-schema ID,
coordinate/mask/projection parameters, response rule, local eligibility, and
fast/slow parameter state. The graph owns its connectivity. Birth and parameter
learning are internal. The coach supplies no detector weights or target feature
labels. Do not automatically attach every hand-written chess feature at birth.

REAL and VIRTUAL frames expose the same schema through separate frame contexts.
Shared measurements are immutable; request state, bindings and eligibility are
not shared across those contexts. Terminals remain leaves. A private rules
simulator may produce hypothetical feature vectors when requested through the
appropriate graph machinery; it supplies no action score or candidate ranking.
Knowing legal transitions is supplied embodiment, not proof of learned dynamics.

Proposed code boundary: a task-independent feature-frame/projection terminal
type in the Hector/core substrate, a chess-only basis encoder, the existing
stem-cell manager as owner of birth/maturation, and a graph policy entry point
whose access to observations and actions is restricted to terminals. Do not
reconstruct the current Python scoring loop behind that entry point.

## 2. Reward and credit have different jobs

External reward defines the objective. Internal prediction error allocates
credit; it is not a second coach reward. Start M1 with the existing +1/-1
exercise contract. Do not change reward scale while changing representation.

For later multistep exercises, a possible objective is +5 for mate, -5 for
exercise failure/draw, with a small cost per **real move**. No ideal-move count
is needed. An ideal-moves adjustment would import a coach target or solver
unless it were the network's own estimate. The latter belongs in internal
prediction, not external grading.

Bound the total speed cost or choose it against the finite move horizon. For
example, total speed cost at most 1 preserves returns of at least +4 for every
win and at most -5 for every failed exercise. An uncapped 0.5 per move can make
a sufficiently slow win worse than an immediate draw. Costs should apply
consistently to trajectories, including failed ones; failure must not erase
already incurred cost. For unrestricted games, revisit the draw-versus-loss
objective: these known-winning exercises are a narrower task.

Current native Q and credit ranges are [-1,1], and the adapter accepts only
rewards of +/-1. A +5/-5-plus-cost experiment requires one explicit, consistent
reward/return normalization or a coherent range change across predictions,
TD updates, uncertainty and slow values. Do not just replace the coach constants:
existing clipping would change the learning semantics. Charge move cost once;
do not charge it in both the coach and `IntrinsicCreditEngine`.

Local eligibility records which parameters and connections participated in the
executed request/action. A scalar TD error modulates those local traces. A
schematic value update is `delta = r + gamma * V(next) - V(current)` followed by
`parameter += learning_rate * delta * local_eligibility`; the actual terminal
and action-selection rule must define the local sensitivity/eligibility it uses.
This is not permission to increment every active node by the same reward.
Inactive alternatives, blocked paths, read-only evaluation and hypothetical
outcomes must not gain real success evidence.

Young nodes need fast updates before maturity, or nothing can mature. Maturity
controls trust in a reusable value prediction and slower consolidation, not
permission to learn. A mature child predicts eventual environmental return;
its firing does not create extra reward. Avoid counting the child's prediction
and the same terminal win twice. Across an option lasting `k` real steps, use
the actual accumulated reward and `gamma**k`, not a single-step discount merely
because the parent issued one request. This follows the distinction between
primitive-step credit and temporally extended actions in the
[options framework](https://www.sciencedirect.com/science/article/pii/S0004370299000521).
Eligibility-trace foundations are described in chapter 12 of
[Sutton and Barto](https://incompleteideas.net/book/the-book-2nd.html).

## 3. Growth within one persistent learner

Use one organism with fast weight adaptation, slower candidate creation and
still slower consolidation. Short internal periods of topology stability can
let new weights settle. They need not be separate training runs or require the
coach to inspect topology. Mature parameters retain controlled plasticity;
stability must not make later correction impossible.

Recommended local growth policy, to implement and test separately:

1. A parent requests available children and maintains a small opportunity for
   exploratory birth. A childless/unsupported parent can grow immediately.
2. Participating paths adapt quickly from real prediction error.
3. Persistent context-specific residual error, novelty or missing supported
   actions increases candidate pressure after sufficient actual experience.
4. Existing stem cells instantiate sparse readers/compositions under that
   parent. Shared scalar feedback and local participation determine learning.
5. Repeated grounded usefulness consolidates a candidate; redundancy, resource
   cost or persistent unhelpfulness leads to pruning using the existing lifecycle.

Growth must have a budget and a nonzero route out of an empty graph. Surprise
alone is insufficient: unpredictable opponent behavior can stay surprising
forever. Growth should target reducible, repeated error rather than indiscriminate
novelty. A single failed move does not establish that topology is inadequate.
The coach's knowledge that this curriculum requires growth must not become a
stage flag or externally issued node-birth command.

Affordance and desirability also differ. A leg can reliably confirm that it can
perform an action or achieve a subgoal while that action is currently poor.
Parent choice must combine contextual support with learned expected return,
uncertainty and relevant duration/cost. Summing terminal activations without
calibration would favor larger or more excitable modules. The exact combination
is a learned/mechanistic hypothesis to test, not an already verified selector.

## 4. Implementation order and acceptance tests

| Work package | Required executable acceptance tests |
| --- | --- |
| Scalar feedback boundary (implemented) | Only reward and event/action binding reach `observe`; failure reasons remain in the external log; wrong/duplicate feedback is rejected; existing play and resume behavior still passes. |
| Later reward scaling/speed cost | A slower win scores below a faster win and above a failed exercise throughout the declared horizon; total time cost is bounded; changing internal microticks or imagined moves does not change the real-move reward; the same fixed normalization applies to rewards, values and consolidation. |
| Base and projection terminals | Schema/dimension mismatch fails; coordinate and mixed projections match analytic examples; saved/restored parameters match; terminals are leaves; same-schema REAL/VIRTUAL frames never share mutable request or eligibility state. |
| Internal representation learning | With an externally opaque learner, reward changes the participating projection parameters on a small non-chess task requiring a mixed feature detector; inactive controls stay unchanged; representations survive save/resume. A constructor-only projection test is insufficient. |
| Persistent graph action selection | Disable the legacy candidate-score builder; actions still follow terminal request/confirmation paths; graph intervention changes the selected actuator; unused Python ranking/cache values cannot affect it. No rewarding hypothetical alternatives. |
| Delayed and hierarchical credit | A delayed observed reward updates the earlier participating path; maturity is not required for fast learning; no update reaches an inactive sibling; terminal reward is counted once; variable-duration child completion uses the correct elapsed-time return; cyclic self-confirmation cannot manufacture value. |
| Internal growth controller | An empty unsupported graph can create its first candidate; a stable solved context does not grow indefinitely; reproducible prediction error can trigger a useful candidate; an irreducibly noisy control does not exhaust unlimited topology; the coach has no growth/curriculum flag. |
| Behavioral chess validation | Replay the same opaque M1 coach on a fresh learner with a frozen explicit base; evaluate held-out actual moves; compare with the hybrid reference without transferring its autonomy claims or its weights. |

Implement one scientific change per comparison. The first representation
experiment must freeze its explicit basis, terminal family, parameter update,
birth rule and budget before seeing chess results. Its hypothesis is that
reward-conditioned terminal representations improve behavior beyond unchanged
random readers with matched resources; the strongest null is that fixed
features/action values alone explain the gain. A proposed first control is to
freeze reader parameters at their identical initialization while retaining the
same graph/action-value learning. Randomized generic tasks are engineering
mechanism tests unless separately designed for scientific transfer claims.

Do not select among terminal families or alter birth rules after inspecting a
failed test and present that as the same experiment. Record the failure and the
next distinct hypothesis. The detailed learning law and compute budget must be
made concrete in that work package; this specification is not a claim that an
unspecified projection learner is ready for a long training run.
