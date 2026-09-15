# Owners, copies, growth and lifecycle

Later experiment: [OWNER_SPLIT_TRIAL_RESULTS.md](OWNER_SPLIT_TRIAL_RESULTS.md)
records provisional owner trials and their negative first comparison. The diagram
below remains a faithful explanation of the earlier saved four/eight-owner runs.
Temporary alternatives add stored scorers beyond the committed partition, with
all parameters/nodes counted. They do not introduce a macro/network router.

Clarification requested2026-09-15 before another learner change or experiment.
The interactive fragment is `visuals/recon-owners-and-growth.html`. It is a
self-contained explanation, with no network requests and no training code.

## An owner is a local scorer

A live decision owner is one context region together with its independently
owned scorer: bias, scoring conditions and their trainable parameters. It scores
all available actions in that region. Four/eight owners means a ceiling on the
number of simultaneously live scorers, not a number of actions, networks or
physical nodes. Actors start with one owner. Replacing one by two children adds
one live owner; reaching four/eight takes three/seven successful binary splits.
The parent remains as ancestry, not another live competing scorer.

A given state belongs to exactly one owner, invariant across its action bindings.
Cases inside that region still share weights and can interfere. The displayed
tree is a logical partition: formal execution gates contributions by route
predicates, without a separate external router.

## Three structural operations

| Operation | Mutable weights | Effect |
| --- | --- | --- |
| Copy execution structure | The same owned parameters | Separate request/confirmation state for different action bindings or parent instances |
| Split a whole owner | Two independent copies of every weight, including bias | Two disjoint contexts can learn different scorers; inherited scores initially preserve behavior |
| Birth a scoring condition | One new zero-valued parameter inside an existing owner | Adds a possible contribution without increasing owner count or initially changing scores |

Splitting copies definitions and values, then gates the children by P and NOT P
within the old route. It does not deduplicate equivalent logic or prove overlap
harmful. Immutable definitions, mutable execution state and learned weights have
different sharing rules.

Birth is the counterpart of earlier unsplit growth. It now occurs inside an owner,
draws from the24-condition pool, excludes seen definitions and proven route
contradictions, and uses current residual/random nomination. Overlap is allowed
and can be useful. Compatibility does not solve semantic duplication or
interference. This remains bounded growth, not unrestricted compound discovery.

Ordinary credit runs every actual action. Every64 active-owner visits, development
checks retirement, then attempts a supported eligible split if resources allow,
otherwise a condition birth. A successful split consumes that birth opportunity.
The operation examples are therefore not the chronology of the fresh study:
the saved seed15 timeline splits before its first scoring births.

## Lifecycle is not replaced work

The current learner already imports and uses StemCellState and CandidateLocalStats
from the older stem-cell module. Requests, confirmations and correlations are
recorded through these classes. Old code and histories remain present. However,
no current owner-learning call promotes a Condition to MATURE. Ownership was a
scoped parameter-isolation test, not evidence of a better replacement lifecycle.

The older framework is more than a bare XP threshold: CandidateLocalStats separates
correlation from intervention counts and can require intervention evidence before
maturity. The provenance of those counts still matters. StemCellTerminal.update_xp
records its supplied affordance_delta as an intervention; naming a count cannot
itself establish the counterfactual benefit of a particular feature or split.

The old solidify_to_mature path creates a permanent pattern-sensor TERMINAL in a
registry. An owner split creates two local scorers with inherited parameters.
Their units, persistence and evidence semantics differ, so the old sensor
promotion path is not a drop-in owner lifecycle.

Earlier `learning/trial_usefulness.py` already implements internal randomized
use/no-use assignments and matching actual scalar outcomes. It is a reuse
candidate, not an established automatic split-acceptance mechanism. Its earlier
experiments did not establish reliable autonomous usefulness discrimination.

Recommended next design: reuse lifecycle vocabulary, separated evidence and
history/assignment machinery; adapt the evidence needed to retain local parameter
separation. Do not invent a parallel lifecycle or blindly restore the old manager.
A useful condition and a split worth its extra parameters are different hypotheses.
Preserve inherited knowledge and ancestry, while distinguishing child-local
evidence. Maturity need not freeze weights, prohibit splitting or prevent later
reconsideration. Composition must remain possible before individual maturity:
parts can be useful only jointly. No new promotion rule, threshold, experiment
or learner change is implemented by this clarification.

## Exploration arithmetic

For a perfect greedy policy, one correct action among two, and probability .25
of choosing uniformly among both, expected correctness is .75 + .25*.5 = .875.
Half the exploratory choices select the correct action; the other half cause the
12.5-point loss. Exploration does not mean deliberately choosing the other action.
For greedy accuracy q on the same input distribution, the expectation is
.75*q + .125. Finite logs fluctuate and the learner changes during training.
The87.5% figure is conditional expectation, not a measured result claimed here.

## Visualization evidence

The saved-growth view uses seed15, both owner ceilings, at actions0,64,192,448,
1024 and1920 from the closed headroom run. All192 displayed saved choices were
checked against recorded evaluations by offline arithmetic. Owner ancestry,
routes, weights, births and node counts come from those checkpoints. Operation
examples have explicitly illustrative weights, not trained fixtures.

Local checks exercise384 input/checkpoint/ceiling combinations at320/736px and
all operation views, with14 static SVG renders available for inspection. These
are DOM-state checks and SVG rendering, not a full browser integration test.
No new environment actions or checkpoint changes occurred.
