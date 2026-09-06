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
usefulness discrimination. Keep normal trial access as the reference. The next
bounded test is recovery through an additional fixed interval of ordinary play,
with all learning active, before adding a controller. Autonomous regulation and
strategic handover remain separate work.
