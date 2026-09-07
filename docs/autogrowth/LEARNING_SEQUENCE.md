# Learning sequence and operating modes

This is a design direction, not a claim that automatic regulation or handover
already works. The stable baseline is `main`. The next isolated work track is
`codex/residual-shadow-nomination`; read its experiment document before resuming
that branch. Do not import its experimental controls into production by default.

## Order of implementation

1. **Edge learning:** verify that terminal-mediated actions and their scalar
   outcomes change actual choices. Keep this plastic while adding mechanisms.
2. **Structural adaptation:** compare experience-guided nominations with matched
   random proposals on subsequent outcomes. Then test materialization, survival,
   pruning and reuse through actual behavior. Random birth alone is insufficient.
3. **Learned coordination:** independently train small child skills, then learn
   contextual child competence and parent delegation in a small separate task.
   This can begin before full KRK or perfect structural growth. Only then use
   the interface for longer chess plans and M2-to-M1 handover.
4. **Retention and regulation:** test interference, recovery and changing tasks
   before claiming consolidation or automatic control of learning rates.

These are implementation dependencies, not a curriculum that freezes each
completed mechanism. A separate coordination experiment need not wait until
every possible growth mechanism is implemented.

## When the mechanisms coexist

Choosing an already learned strategy happens on each relevant request. It does
not require growing a node or changing a weight. Fast edge learning subsequently
adjusts contextual preferences and predictions from eligible actual outcomes.
Structural proposals operate at a slower, bounded rate while those weights keep
learning. Consolidation and retirement need longer evidence windows.

Do not require the existing topology to fail completely before trying any new
structure. That can prevent discovery of useful alternatives and combinations.
Also do not interpret every prediction error as missing topology: inadequate
experience, unstable weights, changed context or irreducible uncertainty can
produce error. A useful proposal must earn predictive and then behavioral value.

A future local regulation law may use sustained residuals, uncertainty, novelty,
recent progress and resource cost to adjust exploration and proposal frequency.
Keep explicit minimum/maximum rates, finite trial budgets and retained history.
Large surprise alone must not trigger uncontrolled growth. Individually weak
readers may still participate in joint trials; no marginal-maturity prerequisite.
Do not add this regulator until the controlled mechanisms have measurable effects.

Parent selection should use learned, contextual and goal-relative child value,
availability and uncertainty through internal terminals. Raw activation strength
is not a calibrated value scale. Independent child training needs subsequent
coordination experience; it does not require erasing child skills or relearning
all child weights. Parent and child credit must bind to their actual participation
and eventual outcome, including delayed outcomes for multi-step plans.

## Training, ordinary operation and evaluation

Use the same architecture and update laws with explicit parameter profiles:

| Mode | Edge adaptation | Exploration and structural trials | Retention |
| --- | --- | --- | --- |
| Development | Active | Larger declared budgets | Measure rather than assume |
| Competent operation, future | Continues at a lower baseline, locally correctable | Smaller nonzero budgets and slower topology changes | Protect useful skills without permanent freezing |
| Scientific evaluation | Disabled | No stochastic training exploration or nominations | No learned-state changes |

The first two profiles are operating choices, not proven optimal hyperparameters.
Competence varies with context; a global “pretrained” flag is not a competence
estimate. Later, local modulation can sit inside these profiles. Start with fixed
limits so experiments can identify what helps. Do not change profiles from a
coach-side graph inspection or silently tune them on evaluation outcomes.

## Current branch scope

The residual-shadow track adds generic candidate terminals and compositions,
internal outcome-residual statistics, a discovery-only nomination decision, and
prospective prediction comparison against a support/grammar-matched random
candidate. The actor's weights continue learning. Shadow candidates cannot change
the selected action, exploration, live weights, birth or pruning.

Its discovery/prospective split is an experimental attribution control. It is not
a proposed permanent two-phase training schedule or a maturity gate on ordinary
learning. The first prediction results were mixed; they do not establish useful
structural selection. The next extension, `TrialDevelopment`, nevertheless permits
one young nominee to act and learn, with its complete shadow record retained.
Ranked/random/no-addition actual-play controls test that connection; a trial need
not first prove scientific maturity. See `LIVE_TRIAL_MATERIALIZATION.md` for the
fixed protocol. The subsequent randomized trial-use probe is in
`TRIAL_USEFULNESS.md`: it preserves the boundary and passes mechanism tests, but
50% probing reduced or matched final chess scores and did not establish reliable
usefulness discrimination. Keep normal trial access as the reference. The
bounded recovery test is complete; see `TRIAL_RECOVERY.md`. Recovery was partial;
ordinary pruning/replacement occurred, and harmful trials could survive. The
paired fixed-topology control is also complete; see `FIXED_TOPOLOGY_RECOVERY.md`.
Holding definitions while weights learned improved no final score, tied twelve
comparisons and worsened three. It did not repair seed 2's probed-policy harm or
seed 3's plateau. Ordinary lifecycle remains the reference; no retention controller
is justified. The longer ordinary-M1 study is also complete; see
`ORDINARY_M1_CONTINUATION.md`. At 1,024 decisions, none/ranked/random scores are
124/128/128, 124/124/124 and 66/66/66. More play improved seed 2, including policies
with a useful live AND, but did not resolve seed 3 or establish ranking superiority.
Nine historical anchors and actual checkpoint reloads matched. The saved-actor diagnostic subsequently proved incompatible weight requirements
for those particular fixed graphs, while finding no formal-computation mismatch.
The following capacity-budget probe then changed only max_conditions (32 versus
64), with 256 more ordinary decisions in both arms. Seed 2 finished at 124 versus
128; seed 3 escaped 66 to 111 in both arms. See `M1_CAPACITY_PROBE.md`.

Keep this distinction explicit: fixed-graph capacity is a property of a saved
representation; ordinary training changes both the graph and its weights. The
current process can make further progress without adding a new mechanism. More
random capacity helped one development case, but does not establish adaptive
structural selection or explain which births caused the improvement.

The fresh-seed replication is complete; see `M1_CAPACITY_REPLICATION.md`. All six
32-budget actors improved from 384 to 1,280 decisions. Late expansion to 64 won
four pairs and tied two, with 25 gained and zero lost paired development mates.
However, seed 5's ordinary control fell from 128 at 1,024 to 124 at 1,280. Early
plateaus are not final limits, and further learning is not monotonically helpful.
No learning rate was varied, so neither “too slow” nor a corrective rate is
established. The longer fixed continuation is now complete; see `M1_LONG_PLAY.md`.
At 4,096 the six larger-budget actors scored 128, 128, 128, 126, 128 and 111.
Longer play helped two and matched four starting totals, with 28 row gains and
two losses. Seed 4 temporarily regressed then recovered; seed 9 did not improve.
This is evidence of continued learning and incomplete stability on viewed M1
positions, not behavioral consolidation or a causal learning-rate comparison.
The subsequent `M1_FAILURE_PATTERNS.md` diagnosis is complete. The corner/knight-
distance family matches the July history, but the old corner branch was authored.
Seed 7 acquired a more expressive condition set during ordinary turnover; seed 9
already admitted perfect ranking on each examined split at both endpoints.
Its remaining problem cannot simply be declared missing capacity. Failure score
margins improved without crossing the selection boundary. Next compare the
existing exploration setting 0.25/0.50 from final seeds 9, 7 and strong reference
4, with normal growth and all other settings unchanged. Declare budgets first
and log actual behavior; never route diagnosed families or fitted weights back
into play. This tests an explanation, not an established corrective rate.
Remember joint signal and candidate diversity from the linked historical review.
For future broader coverage, preserve the existing orbit partition: the current
generator's seed changes both sampling and split assignment. Keep the final test
unopened. Per-split mathematical capacity is not a jointly learned policy,
general mastery or adaptive proposal selection.
Keep diagnostic answers outside training. Main's learner/defaults stay unchanged.
Automatic regulation and the independently trained child-competence/delegation
experiment remain separate capabilities.
