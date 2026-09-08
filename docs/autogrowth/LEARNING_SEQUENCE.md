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

Learned reuse and simplification are an explicit further structural milestone.
Aim for compact, behaviorally reliable shared definitions; an exact minimum node
count is not a gate for learning or delegation. The current birth law proposes
shallow one-to-three-reader conditions. It does not discover arbitrary nested
factoring or symmetry sharing. Future generic reuse must preserve terminal and
action-binding semantics, receive evidence from subsequent real outcomes, and
protect young jointly useful combinations. Keep this separate from the present
exploration comparison; the coach never rewards graph shape or supplies chess
rules. Count shared definitions and measurement complexity as well as physical
vertices. Smaller graphs are not automatically more general or more stable.

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
structural selection. The subsequent `TrialDevelopment` experiment permits one
young nominee to act and learn, with its complete shadow record retained, under
ranked/random/no-addition controls. A trial need not first prove scientific
maturity. Read the branch status in `OFFICIAL_CONTINUATION_20260906.md` for exact
results and continuation. The later internal randomized-use probe passes its
mechanism checks but half-time probing reduced or matched final chess performance.
Its short aggregate estimates do not justify automatic retention or maturity.
That recovery comparison is complete: recovery was partial, ordinary pruning and
replacement occurred, and harmful trial instances survived. The fixed-topology
comparison has also completed: holding definitions while weights learned improved
zero of fifteen pairs, tied twelve and worsened three. See the latest branch
result in `OFFICIAL_CONTINUATION_20260906.md`. Keep normal lifecycle as the
reference. The longer ordinary-M1 follow-up is complete: at 1,024 decisions,
none/ranked/random scores are 124/128/128, 124/124/124 and 66/66/66. Seed 2's added
policies improved from 98 to 124 and rely strongly on their AND, but the actor
without an addition also reaches 124. Seed 3's plateau persisted. The subsequent
offline investigation found no formal-computation bug, but proved
incompatible weight requirements in those particular saved graphs. That result
concerns fixed representations. A paired condition-budget probe then supplied
256 more ordinary decisions at 32 versus 64 conditions. Seed 2 finished 124 versus
128; seed 3 escaped 66 to 111 in both arms. See the latest result in
`OFFICIAL_CONTINUATION_20260906.md`.

The existing growth/learning process can therefore progress without a new
mechanism or larger budget. The fresh-seed replication then completed all 12,288
moves: all six 32-budget actors improved from 384 to 1,280, and late expansion
won four pairs and tied two, with 25 paired gains and no losses. However, seed 5
regressed from 128 at 1,024 to 124 at 1,280. See the latest result in
`OFFICIAL_CONTINUATION_20260906.md` for all scores and verified checkpoints.

Early plateaus are not final limits, and more play is not monotonically helpful.
The learning rate remained 0.3; “too slow” was not tested as an explanation.
The longer study is now complete: at 4,096 the six saved larger-budget actors
scored 128, 128, 128, 126, 128 and 111. Two improved and four tied starting totals,
with 28 gained and two lost rows. Seed 4 temporarily regressed then recovered;
seed 9 stayed at 111 despite turnover. See the latest branch record in
`OFFICIAL_CONTINUATION_20260906.md`. All 199 tests and 19,968 moves completed.
No setting or mechanism changed. The read-only follow-up is now complete at
`ff71baaaf85d46dc2f394e9aeab2df6f77c34d57`: 209 branch tests passed and 8,575
diagnostic executions included zero training. The remaining corner/knight-offset
family matches the project's July 3 history, where a manually added alternative
conjunction repaired recognition. That history requires preserving jointly useful
signals and diverse compositions; it does not justify supplying the chess rule.
Seed 7 gained per-split representational capacity during ordinary growth. Seed 9
already had it initially, so its plateau cannot simply be called missing nodes.
Each feasibility result concerns one split, not a shared fit or learnability.

The exploration comparison is complete at `37e064ecbd6203163c8376c5a0882ed8070dbcae`:
215 tests and 14,592 actual moves. Both rates end at 128, 128 and 124 / 128 for
seeds 4/7/9, with identical final outcome partitions. Higher exploration temporarily
worsened two histories and gave no final advantage. Seed 7 recovered. Seed 9
learned all 17 old failures but lost four other corner rows, one symmetry orbit.
Both families received actual successes; 0.50 yielded fewer than 0.25. All trained
endpoints and action histories are retained. See the latest official record.

Keep 0.25. That retention attribution is complete at
`6b464f0bf924befe08097ae288c41746211ce2b3`; read the latest official record and
linked report/expert prompt. All 221 tests and 8,959 diagnostic executions passed,
with zero training. All five inspected graphs admit a perfect SHARED ordering
on the train/development union. Actual credit reconstructs every saved boundary;
shared-weight updates, especially rewards for the other corner alternative,
explain most of the representative loss. Removal contributes relatively little.
The four development rows briefly recover at step 5,888 in .25, then fail again.
Two actually practised training rows also finish lost in both exploration arms.
Functional overlap among differently defined conditions is confirmed within the
corner contexts, without proving global redundancy or a benefit from deletion.

Next propose ordinary play from step 4,096 with eta=0.3 versus 0.1, fixed .25
exploration, cap 64 and normal birth/pruning. Declare bounds before running and
measure both acquisition and retention across seeds 4/7/9. This is a minimal
step-size hypothesis, not proven consolidation or a fix. If it merely delays
acquisition or leaves interference, examine generic credit allocation/contextual
factoring next. No new controller is justified yet. The independent expert prompt
explicitly invites disagreement with this ordering. Do not install an offline
solution, replay logs under a changed policy or add a corner/retention rule.
These selected-history results establish neither general rate superiority,
consolidation nor general mastery. Future fresh pools
must preserve orbit partition assignment: the current generator's seed changes
both sampling and split assignment. Keep the final test unopened.
Main's learner and original 96-condition default remain unchanged. Diagnostic
answers stay outside training. Automatic regulation and the independently trained
child-competence/delegation experiment remain separate capabilities; delegation
need not wait for perfect structural discovery.
