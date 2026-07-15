# Generic-Core Support-Conditioned Lifecycle Grace Work Package

Date: 2026-07-15. Track: generic-core science. Status: frozen before
implementation or fresh execution. Authorized by external adjudication after
closed exact-evidence result `261bc34` and FrameContext correction `0fa0310`.

## Prior result, hypothesis, and strongest null

The graph-internal exact-evidence package is immutable negative evidence. All
80 target structures were discovered, exact measurement was sound, and exact
requests modestly improved the weakest support, but all four targets reached
support 32 and matured in only 2/20 tasks. Eighteen of 80 targets died
unsupported under the frozen two-review lifecycle with final reviewed support
5--22. Priority was not identified and is not a binding factor here.

Hypothesis: a trial that senses its exact anonymous evidence deficit, recent
retained-support progress, active evidence request, and bounded remaining life
through graph-local internal terminals can defer unsupported pruning long enough
to reach ordinary rent adjudication while consuming less candidate capacity than
a content-blind fixed six-review lifetime.

Strongest null: any gain over two reviews is explained entirely by more life. A
fixed six-review control matches or exceeds evidence, maturation, and behavior,
while conditioned grace fails to reduce live occupancy, challenger blocking, or
displaced proposals. Any result involving host-side reconstruction, target
identity, changed exploration, changed reward/rent, or integrity failure is
invalid.

## Changed factor and immutable boundaries

The sole scientific factor is the unsupported-trial lifecycle rule after exact
evidence requests are already present:

1. the predecessor's ordinary two-review lifecycle;
2. a content-blind fixed six-review maximum; or
3. a graph-emitted support-conditioned maximum of six reviews.

The following remain byte/protocol frozen to the predecessor: exploration rate
0.15 and schedule, support threshold 32, proposal interval 128, review interval
512, temporary challenger allowance 4, global capacity 32, reservoir capacity
2,048, learning and topology budgets, residual-ranked proposal order, outcome
learning, reward, resource cost, rent/margins, main/topology/reservoir/support RNG
streams, phase-0 admission, row generation, and evaluation. Once a trial reaches
support 32, ordinary rent promotion, rejection, replacement, retirement, and
neutral-review handling are unchanged. Grace cannot alter exploitative scores,
reward, rent, maturity, evidence support, or exploration allocation.

Priority exposure and allocation statistics remain descriptive and may be
reported `not_identified`; priority is not a grace gate. Virtual frames, child
responses, prediction residuals, consolidation, and native KRK are excluded.

## Exact graph-local grace contract

Fixed-six and conditioned-six use identical candidate-local node/edge identity.
Every live trial in those arms materializes four disconnected internal
TERMINALs and one AND request SCRIPT:

- `EVIDENCE_DEFICIT`: positive iff exact retained support is below 32;
- `EVIDENCE_PROGRESS`: positive iff the retained-support interval high-water
  increased over the trailing two-review window; the first review is an explicit
  initialization window, which supplies the single tolerated initial stall;
- `REQUEST_ACTIVE`: positive iff the candidate's ordinary exact evidence-request
  SCRIPT emitted at least once since its previous review/birth; and
- `GRACE_BUDGET_REMAINING`: positive iff fewer than six total trial reviews have
  occurred, normalized by the six-review cap.

The candidate-local `DEFER_PRUNING_REQUEST` SCRIPT is an AND over exactly these
four terminals. It has no edge to the exploitative `action_score` root. The host
lifecycle bus may consume only the emitted request plus its anonymous graph IDs.
It may not reread support/candidate fields, infer targets, reconstruct the AND,
or independently grant an extension. No emission means the normal unsupported
transition occurs.

For the fixed-six arm, topology is identical but `EVIDENCE_PROGRESS` and
`REQUEST_ACTIVE` use frozen always-active measurement backends. Deficit and
budget remain measured normally. It therefore defers every unsupported review
1--5 and prunes at review 6. For conditioned grace, all four measurements are
real candidate-local state. Thus conditioned versus fixed-six isolates local
self-regulation rather than life dose.

Trailing two-review progress is computed from support high-water marks, not only
the potentially evicted current count. At review 1 it is true by initialization.
At review r >= 2 it is true iff the current interval high-water exceeds the
high-water recorded two reviews earlier. One stalled interval following progress
therefore remains eligible; two consecutive intervals without a new high-water
make it false. Eviction cannot reset birth time, high-water history, review age,
or grace budget. Review 6 has zero remaining budget and cannot emit.

Only trials can own or emit grace topology. Mature/pruned candidates remove it.
A pruned candidate can never revive. Clone/checkpoint/restore must preserve all
node IDs, edges, activations, counters, high-water history, request baselines,
RNG state, and audit state.

## Required lifecycle audit

For every candidate record:

- anonymous action/candidate graph identity and immutable member IDs;
- birth observation, birth terminal count, birth global review, and birth
  retained support;
- every review number and terminal count;
- current support, lifetime support high-water, interval high-water, and trailing
  two-review comparison high-water;
- evidence-request count at interval start/end and `REQUEST_ACTIVE`;
- each of the four terminal measurements/activations;
- defer SCRIPT activation/emission, extension count, and remaining review budget;
- lifecycle transition and precise pruning reason;
- live trial/mature/global occupancy at every review and proposal opportunity;
- challenger blocking and eligible proposals displaced by a full challenger
  allowance; and
- end-of-phase right-censoring.

A live trial reaching phase end before its applicable review cap is recorded as
`right_censored`, not as unsupported/no-progress death. It remains a failure to
mature for target evidence, maturation, and behavior gates. Finalization must
not silently prune it or let it influence exploitative behavior.

## Mandatory pre-fresh validation

Focused tests must establish:

1. fixed and conditioned arms have identical grace node/edge identities;
2. all grace structures are disconnected from exploitative roots;
3. two-review mode preserves predecessor lifecycle/event behavior;
4. fixed-six emits at unsupported reviews 1--5 and not 6;
5. conditioned progress across gain/stall, stall/gain, and two-stall sequences;
6. no request activity prevents conditioned extension;
7. support 32 routes to unchanged ordinary rent, never grace;
8. eviction cannot reset age/budget/high-water history;
9. mature/pruned candidates cannot emit and leave no stale grace references;
10. clone/checkpoint/restore parity for graph/counters/RNG/audit;
11. host bus consumes graph emission without field inspection/reconstruction;
12. proposal displacement, blocking, occupancy, and birth/review audit accuracy;
13. right-censored trials are distinct from deaths but fail maturation; and
14. zero changes to exploration event/RNG/row budgets across lifecycle arms.

Run retired/truncated smoke only, then full repository validation, before fresh
seeds. Any counter, topology, root-firewall, clone, RNG, event-budget, or audit
mismatch blocks fresh execution.

## Fresh candidate pool and admission freeze

Candidate seeds are exactly 20262401--20262440. Before this freeze, exact
numeric-boundary searches found no use in repository text, compressed artifacts,
or Git history. Generate candidates ascending and freeze the first twenty
admitted checkpoints under the unchanged predecessor admission rule: 4,096
phase-0 episodes, 512-row old-task development evaluation, quiesce unfinished
trials, then require joint success >=0.85, zero remaining trials, and byte-identical
deployed behavior across quiescence. Fewer than twenty admissions within the
capped range closes as an admission abort. No phase-1 row is touched first.

The canonical live process writes and pauses on the attempted/admitted/rejected
manifest. Commit and push the exact bytes, verify HEAD and SHA-256, then resume
the same process. Every touched seed/row is permanently development data. No
selective cell rerun is allowed.

## Five frozen phase-1 arms

For demand m=2, clone every admitted phase-0 checkpoint into:

1. `fixed_8_ranked`: unchanged fixed-capacity stability reference.
2. `rent_batch_4_ranked`: unchanged ordinary-exploration causal-rent control.
3. `rent_batch_4_graph_exact_two_review`: exact-directed requests with the
   predecessor two-review unsupported lifecycle.
4. `rent_batch_4_graph_exact_fixed_six`: identical exact-directed requests and
   grace topology, with unconditional fixed-six measurement backends.
5. `rent_batch_4_graph_exact_conditioned_six`: identical exact-directed requests
   and grace topology, with measured deficit/progress/request/budget terminals.

Each arm consumes the same 4,096 matched phase-1 rows and the same 512 old plus
512 new evaluations. Persist after every arm and admitted seed.

## Frozen independent gates

1. **Measurement/integrity:** zero support/full-scan, grace graph identity,
   terminal/backend, root-firewall, stale-reference, clone/restore, RNG/event/row
   budget, final-return, audit, or right-censor classification failures.
2. **More-life effect:** relative to exact two-review, conditioned-six has larger
   paired per-task minimum target support in at least 14/20 with median advantage
   >=12. Passing this alone supports only `more life helps`.
3. **Conditioned evidence:** all four targets reach support 32 in at least 16/20
   conditioned tasks and conditioned unsupported lifecycle deaths are <=4/80.
   Right-censored unmatured targets do not count as deaths but still fail the
   all-four task count.
4. **Conditioned maturation:** all four targets obtain positive rent and mature
   in at least 16/20 conditioned tasks.
5. **Self-regulation versus fixed-six:** conditioned support-32 and all-four
   maturation task counts are each no more than two below fixed-six; median paired
   minimum-support difference is >=-2; median paired minimum old/new behavior
   difference is >=-0.05; median episode-weighted live-trial occupancy is at least
   10% lower; and both challenger blocks and displaced proposals are strictly
   lower in at least 14/20 paired tasks. All clauses are required.
6. **Behavior:** conditioned median old and new joint success are each >=0.85, at
   least 16/20 master both, and median paired minimum old/new difference versus
   fixed reference is >=-0.05.
7. **Stability:** fixed reference median old and new are each >=0.85 and at least
   16/20 master both. Conditioned retention is already required by behavior.
8. **Priority:** descriptive only; report zero/one/multi/unequal opportunities
   and allocator-could-differ counts as `identified` or `not_identified`, with no
   bearing on grace support.

`support_conditioned_self_regulation` requires gates 1--5. `behavioral_readiness`
additionally requires 6--7. This package can never itself authorize native KRK
or virtual-frame transfer.

## Predeclared interpretations and stop rules

- Conditioned beats two-review but not fixed-six: only more life helps; local
  self-regulation is not supported.
- Fixed-six and conditioned both remain below support 32: close lifecycle grace
  at this cap; do not add throughput automatically.
- Conditioned matches evidence/maturation but uses fewer resources than
  fixed-six: support-conditioned self-regulation is supported.
- Support reaches 32 but positive rent/maturation does not: investigate
  individual rent versus cooperative contribution in a separately frozen package.
- Maturation passes but behavior fails: investigate competition/plasticity.
- Behavior passes but retention fails: isolate consolidation.
- Any integrity failure stops immediately. Once fresh phase 1 starts, code,
  thresholds, seeds, rows, mechanisms, and gates are immutable.

Compute budget: one implementation, focused/property/integration tests, one
retired truncated smoke, one full suite, one capped 40-seed admission, and at
most 20 admitted checkpoints x 5 arms x 4,096 phase-1 episodes. If the package
closes early, remaining work may prepare—but not execute—a native design in
which each hypothetical successor actually requests the frozen mature R0 graph.
No scientific handover package may inject child expected values from its harness.
