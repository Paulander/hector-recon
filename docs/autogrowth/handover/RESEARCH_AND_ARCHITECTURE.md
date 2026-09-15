# HECTOR: research and architecture handover

## Research objective and non-negotiable boundaries

Oskar's ReCoN (Request Confirmation Networks) project seeks learning and growing
decision structure within a graph, ultimately reusable hierarchical competence
across tasks such as KRK mating and KPK promotion. Earlier impressive chess demos
sometimes depended on external scaffolding. The current work deliberately studies
smaller mechanisms whose information boundaries can be audited. The Boolean
benchmark is an easier diagnostic of acquisition/interference, not a replacement
for the chess objective and not a chess win-rate claim.

The organism receives terminal observations and scalar outcome feedback bound
to its actually executed action. A supplied generic developmental law can operate
inside the learner, but must be described as such; it is not itself a controller
learned by the graph. The experiment's schedule and evaluation labels belong
outside the organism. Offline diagnostics may inspect saved graphs and solve
linear feasibility questions, but their labels/weights never enter training.
No new macro coach, task/phase router, authored winning condition, class-specific
freeze, privileged correct-action signal or modified-policy replay is allowed.

## Benchmark and the meaning of 16/16

There are 16 combinations of four Boolean state inputs `(x,y,z,noise)` and two
actions (`act-a`, `act-b`). Correct action-b is `y if z else x`; noise is irrelevant
to the task but is an ordinary declared input. Context A has z=false; B has z=true.
These facts are for experiment/diagnosis. The learner sees declared coordinates,
formal confirmations and scalar rewards (+1/-1), not the target formula or labels.

The fixed schedule is 640 A cases, 640 mostly B (7:1), then 640 mostly A (7:1),
with the seeded existing ordering. `run_owner_fresh_start.schedule` is authoritative.
Every 64 training actions, and at zero, evaluate all 16 cases on a disposable
checkpoint clone with exploration and updates disabled. Pending trials use the
continuing parent, so evaluation measures the committed policy. The clone cannot
teach the live actor. Frozen reproduction repeats each saved evaluation and is
counted separately from the originally scheduled evaluation.

A 16/16 score establishes the particular saved policy solves these 16 cases.
One such policy demonstrates representability, not reliable discovery,
uninterrupted retention, generalization or a guarantee of 100% future accuracy.
With 25% uniform random exploration over two actions, a perfect greedy policy's
expected training accuracy is .75 + .25*.5 = 87.5%. That arithmetic is not a
measurement of the actual runs.

## One decision and its credit

The actor reads state/action-bound terminal measurements through the formal
ReCoN graph. It builds scores for legal action bindings, selects via its policy
and independent exploration stream, executes exactly one action and accepts its
matching feedback. The selected binding's confirmed conditions receive the scalar
update. With owned bias included in active contributions:

`delta = 0.3 * (reward - prediction) / number_of_active_owned_contributions`.

The bias contributes equally to both action scores, so a bias prediction change
alone cannot make the greedy policy better. Existing fast/slow weight handling
remains. Only the actually active owner receives parameter and local evidence
updates. Invalid/unmatched feedback is rejected; checkpoints require completed
feedback. Old weights, observation evidence and proposal history are not guessed
from offline target labels.

## What an owner is, and why whole-scorer copies matter

An owner is a contextual decision region with its own full scoring parameters,
including its bias and competing action contributions. A split adds a Boolean
partition of that region. It copies the entire local scorer into both children,
so each initially produces the parent's scores in its own region. Children share
immutable expression definitions, not mutable weight objects or execution state.
Each execution SCRIPT retains one parent. Nested accepted partitions can grow.

This prevents feedback in one owner from altering another owner's weights. It
does not stop two cases *inside the same owner* from pushing shared weights in
opposite directions. That is the remaining problem which motivated finer useful
partitions and lifecycle work. Copying existing structure preserves initial
competence; ordinary births add new candidate scoring expressions with zero
initial weight. These are different operations with different exposure costs.

Children inherit parameter values and structural ancestry. Their own visits,
condition statistics and local nomination evidence start empty: parent observations
are retained as history, not relabeled as observations made by a newborn child.
The live continuing parent also keeps learning during provisional trials.

Four owners means at most four reserved contextual leaves, not four nodes or four
actions. A pending parent-vs-two-children comparison stores three scorers but
reserves two possible committed owners. Two committed regions, each with a pending
split, therefore store six scorers while reserving four owners. All live temporary
parameters/nodes count against storage limits. Archived history is not a live
scorer. Actual storage and runtime must be reported, not just committed leaves.

## Search and composition: supported versus discovered

The generic expression/compiler machinery supports nested Boolean composition.
Binary XOR is normal XOR; its n-ary implementation here means exactly one true,
not arbitrary parity. k-of-n exists in the underlying engine, but the present
fresh learner does not discover unrestricted k-of-n structures.

This experiment uses a fixed seed-specific pool of 24 shallow AND/OR/XOR scoring
predicates over declared coordinates, with residual-ranked nomination. Its split
candidate pool consists of eight individual state-bit tests (both polarities of
four inputs). A newly learned compound scoring predicate does not automatically
become a reusable split candidate. A runtime expression can compose subexpressions;
that does not mean the current search discovers arbitrary hierarchical abstractions.
Avoid claiming unrestricted XOR-between-learned-sublegs discovery.

A local compatibility check rejects a new predicate only if it is proven impossible
inside its owner's route given the declared schema. Unknown and rare/unobserved
predicates remain eligible. There is no empirical absence oracle or silent parent
cleanup. Complementary Boolean tests are one partition hypothesis, avoiding naive
same-owner retries under the opposite polarity. Semantic merging, common-trunk
factoring and general recombination are still absent.

## Existing and newly combined lifecycle mechanisms

The project already had lifecycle states, candidate-local statistics, an internal
permission terminal and real randomized use/no-use outcome records. Owner splitting
reuses these primitives. It does not erase older work or introduce a separate
external acceptance service. Do distinguish owner-split acceptance from condition
maturity: MATURE on a split does not promote every constituent feature or freeze
its weights. Final conditions in several earlier studies remained TRIAL.

The original owner-trial law retains the parent and gives the child alternative
half-time access through an internal RNG and formal permission gates. Assignment
is sampled before environment reads and shared across legal action bindings. Only
the region actually reached and its executed action record evidence. The nominal
on/off comparison is adaptive and finite; it is not a calibrated causal confidence
interval or a full-time-training counterfactual.

- Original trial: review after 256 region requests; at least 48 outcomes per
  alternative and 16 actual outcomes per child; gain at least .10 in mean reward;
  both halves of lifetime also have positive gain. Accept children and archive
  parent, or retire children as unproven while preserving histories.
- Revised TRIAL: retain the candidate while parent and each child acquire at least
  64 actual controlled actions after birth. Prior parent history does not count.
  The readiness-triggering outcome belongs to the learning phase.
- Revised PROBATION: collect 256 subsequent region requests; use the same .10,
  48 and 16 thresholds, without the early-half-positivity requirement.
- If unproven, preserve the exact candidate, weights, visits and failed-review
  history; one preallocated second review uses 512 cumulative prospective requests.
- At 1,536 region requests since birth, retire any still-unproven trial. Do not
  accept on a truncated prospective window. Endpoint-pending trials stay pending.

This combined timing/readiness/review change is not an ablation of each component.
It still excludes finally retired same-owner partitions. Retaining a live candidate
for reconsideration is not a dormant storage/revival subsystem. Longer lives may
occupy storage and delay further splits. No nested competing trial inside a pending
alternative is allowed, but accepted children can later develop/split normally.

Ordinary weight learning and condition birth/pruning continue in both alternatives.
The current baseline sometimes uses a split in place of a birth opportunity; the
original and revised trial classes instead birth first and then nominate a split.
Thus the first trial-vs-current intervention also changed opportunity scheduling.
The revised-vs-original trial comparison keeps that schedule the same.

## Results leading here

| Work package | Observed result | Interpretation |
| --- | --- | --- |
| Whole-decision ownership primitive | Score-preserving independent copies; inactive-owner credit isolation verified | Engineering capability, not a learned nomination policy by itself |
| Fivefold owner nomination | Seed10 current/split 12/11; seed11 13/14; both totals25/32 | Longer child exposure changed the earlier short-pilot interpretation; retention still imperfect |
| Context compatibility | Nine impossible births prevented; 96 fewer nodes across two arms; trajectories unchanged | Direct waste reduction; no observed compounded learning benefit or retention fix |
| Birth search, seeds10/11 | random/current,residual/current,random/extra,residual/extra:13/14/14/14 and16/16/13/16 | Residual ranking helped some cases; extra births were not consistently useful |
| Fresh starts, seeds12/13/14 | random/current15/12/14; residual/current14/14/16 | Ranked seed14 retained16 from768; incomplete reliability across seeds |
| Four/eight owners, seeds15/16/17 | four14/13/15; eight13/16/14 | More capacity won one pair and lost two; many early A-only splits, fewer visits per child |
| First combined trial, seeds18/19/20 | current16/14/14; trial12/12/12 | Combined rule lost all pairs;2 accepted,12 retired,2 pending trials |
| Learning-before-assessment, seeds21/22/23 | Interrupted after seed21 controls16/11; revised13 at1536 | Early-negative candidate later accepted, but final comparison unresolved |

For exact endpoints, histories, source identities, counts and costs use the
corresponding reports, not this condensed table. Earlier cohorts are closed;
only the newly user-authorized recovery of the interrupted 21/22/23 experiment
is active. Main is not a scientific-promotion shortcut.

Important prior failures: ranked seed12 reached15 but ended14; row11's own
feedback improved its correct-action margin by .073 while A examples sharing
its owner worsened it by .160. Ranked seed13 never exceeded14; row7 was lost
through interference mainly from another B case. Its row10 was never solved.
Both ranked endpoint graphs could rank all16 correctly with some weights, but
actual learning had not found those weights. Other endpoints lacked structural
ranking capacity. These are different failure modes, requiring separate diagnosis.

The first trial study exposed timing/support problems: seed19's candidate had
overall gain+.1605 but a negative early half and positive late half, so it was
rejected. Seed20's candidate had positive halves and overall+.1344 but one child
had14 outcomes versus16 required. Under7:1 exposure and half-time access,16 rare
child observations is approximately the expected count per256-request window.
The new timing rule was fixed before seeds21/22/23 were played; it was not tuned
after viewing their performance.

## What to examine after recovery

First finish the unchanged comparison and compare every seed, retention and cost.
For failures distinguish actual parameter interference from missing representational
capacity, no discovery, late readiness, unsupported review, pending allocation,
and retired useful structure. Do not infer the cause from node counts alone.
Compare committed evaluation, actual training accuracy, and per-child actual
exposure separately. Keep A640/B1280 retention distinct from acquisition.

Exact LP/rational certificates in `analyze_owner_split_trial.py` prove whether
one fixed saved committed graph admits correct rankings on all16 cases. They do
not prove that the learner can discover those weights, that future growth cannot
help, or that weights should be injected. All diagnostic weights stay offline.

Potential later work remains separate: reuse learned compound predicates as local
split candidates; richer hierarchical abstractions/k-of-n discovery; local
interference protection; reconsideration of finally retired hypotheses; common
trunk factoring/recombination; strong learned-prefix retention comparisons; broader
Boolean tasks and later clean chess integration. Oskar suggested coarse early
splitting followed by later refinement, and depth-scaled branching, but explicitly
preferred addressing the current problem before adding those knobs.

## Detailed repository reading map

- `CONTEXT_OWNERSHIP_PLAN.md`: recovered original architecture plan and checkpoints.
- `OWNER_DEVELOPMENT_EXPLAINED.md`: pedagogical local growth/ownership explanation.
- `OWNERS_COPIES_AND_LIFECYCLE.md`: copy versus birth versus provisional acceptance.
- `CURRENT_COMPOSITION_AND_LIFECYCLE.md`: engine support versus actual discovery.
- `OWNER_NOMINATION_FIVEFOLD_RESULTS.md`, `OWNER_COMPATIBILITY_RESULTS.md`.
- `OWNER_BIRTH_SEARCH_RESULTS.md`, `OWNER_FRESH_START_RESULTS.md`.
- `OWNER_FRESH_FAILURES.md`: exact row histories and within-owner credit attribution.
- `OWNER_HEADROOM_RESULTS.md`, `OWNER_SPLIT_TRIAL_RESULTS.md`.
- `OWNER_TRIAL_LEARNING.md`, `OWNER_TRIAL_LEARNING_STATUS.md`.
- Earlier chess motivation: `M1_RETENTION.md`, `M1_FAILURE_PATTERNS.md`,
  `M1_REPRESENTATION_DIAGNOSIS.md`, `M1_RANKING_CERTIFICATE.md`,
  `RETENTION_EXPERT_PROMPT.md`. Some old experiments also had interruptions;
  consult their status rather than restarting them.

All paths above are relative to `docs/autogrowth/`. Raw records are under
`snapshots/autogrowth/`; machine-readable summaries under
`reports/autogrowth/development/`. Read those details before making new claims.
