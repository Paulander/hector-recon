# Adaptive boundary ecology: architecture handoff

## Status and scope

This note describes the mechanism implemented on branch
`codex/adaptive-boundary-ecology` at exact commit
`ad3b0777ad22c26694e7496ef620eb7712ea05ad` in
[`Paulander/hector-recon`](https://github.com/Paulander/hector-recon). The branch
is pushed. Its implementation base is `2f1b68c992eb6868b468148004d8e5a4746c88ab`.

The mechanism has passed exact software/replay tests and a small viewed
development experiment. It has **not** demonstrated mate-in-2 competence or a
general learning result. The V15 validation and regression results were each
`0/4` exhaustive mate-in-2 in both seeds and both factorial arms. Treat this as
an architecture and mechanism handoff, not as a scientific claim.

## The idea in plain language

The desired organism starts with a learned mate-in-1 competence skeleton. It
then tries first moves from harder positions. After each possible opponent
reply, it asks: “Does some already grounded local structure know how to finish
from here?”

When an unexpected environmental success occurs just outside the known
boundary, a few cheap local pattern sketches are born from the graph features
that were active. A sketch is only a proposal. It must recur on later, distinct
REAL interactions before it receives authority. Failures do not merely kill a
coarse sketch: they identify a residual region in which it must abstain, and
narrower children may be tried. Useful local structures can become new anchors
for further outward growth.

For a candidate first move to receive positive successor value, **every legal
opponent reply** must be handled by grounded authority. A single refuted reply
vetoes the move; an unknown reply keeps it unknown. The value is the minimum
over replies. This is the adversarial, worst-reply part of the mechanism.

No correct move, mate-distance label, tablebase, Stockfish answer, held-out
answer, or absolute-position identity is supplied to the learner. Legal move
generation, actual environmental outcomes, and exhaustive report-only
evaluation are environment/harness functions, not teacher labels.

## Vocabulary

| Term | Meaning here |
| --- | --- |
| **R0 / core** | The previously learned native mate-in-1 competence. “R0” is a curriculum index, not a different kind of network. |
| **R1 / boundary task** | Learning a first move whose resulting positions can be finished by the core or certified descendants after every opponent reply. In this development curriculum it corresponds to mate-in-2. |
| **REAL receipt** | An immutable record of one action/outcome interaction actually opened to the learner. |
| **VIRTUAL query** | A read-only prospective query. It may test whether authority responds but cannot certify or train it. |
| **Bud / sketch** | A cheap, tentative conjunction of locally active graph-visible signals. It has no authority. |
| **Promotion** | Atomic materialization of an eligible sketch as a dormant authority child. Promotion still gives it zero authority. |
| **Certification** | Later, post-birth REAL evidence makes a promoted child prospectively authoritative. Discovery evidence is excluded. |
| **Handoff** | A complete all-reply envelope exposes grounded successor value to credit the exploratory first move. |
| **Safe point** | A content-blind quiescent boundary at which pending graph mutations are committed atomically. It decides *when* mutation is safe, not *what* should grow. |

## End-to-end loop

```text
harder predecessor position
        |
        v
choose and execute one candidate first move
        |
        v
enumerate every legal opponent reply
        |
        +--> query frozen core and certified descendants for reply 1
        +--> query frozen core and certified descendants for reply 2
        +--> ...
        |
        v
fail-closed all-reply envelope
  REFUTED if any reply is refuted
  AVAILABLE only if every reply is grounded and available
  UNKNOWN otherwise
  value = minimum grounded reply value
        |
        v
choose the weakest/counterexample reply for one REAL challenge
        |
        v
environmental outcome only
        |
        +--> TD/eligibility credit to the observed first-move pattern
        |
        +--> local ecology: support, contrast, birth, refinement, pruning
        |
        v
quiescent safe point: atomically promote/retire/materialize pending structures
```

The implementation currently has one serious disconnect from this ideal:
R1 training chooses first moves from a deterministic hash-permuted schedule,
not from the learned ranking. TD changes graph scores, but those scores do not
normally choose subsequent training actions. That is a current harness/policy
limitation, not part of the intended architecture.

## The native components

### 1. Shared native graph and local patterns

The graph represents before-state, action/delta, and after-state micropatterns,
their shared atoms, composite cells, and action triplets. Outcome-grounded M3/TD
updates change local weights. The same micropattern can recur at translated or
symmetry-related board locations; this is deliberate generalization rather
than absolute-position memorization.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py)
  - `apply_intrinsic_td` applies one scalar TD error only to an actually
    observed action branch;
  - `rank_shared_composite_candidates` finds reusable coactivations;
  - graph choice/ranking provides the eventual policy substrate.

One known tradeoff is action aliasing: different legal moves can instantiate
the same abstract triplet. Credit then strengthens a local action pattern, not
necessarily one exact UCI move. That is desirable when the abstraction is
correct and harmful when it collapses strategically different actions.

### 2. Frozen mate-in-1 core and jurisdiction gate

After R0 training, the core graph and its triplet set are frozen. A learned
outcome-calibrated local gate is intended to decide whether the core has
jurisdiction on a successor. If it emits a grounded legal response, it has
precedence over descendants and the plastic graph.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  - `_protected_core_r0_available` performs the local frozen-core query;
  - `_choose_with_child_priority` routes core, then V2 descendants, then the
    plastic graph;
  - `_r1_reply_authority_from_core_response` projects only grounded core value
    into a reply envelope.

The current implementation distinguishes “core routing configured” from
“core routing actually grounded” imperfectly. In both V15 seeds the gate was
globally `mature=false`, so the configured core abstained everywhere. The
forensic note documents one concrete retention error caused by falling through
to the plastic graph. In addition, the current top-level sequence fits this
gate before `mature_existing_graph()` changes the graph that is subsequently
frozen and routed. That sequencing did not cause the exact V15 abstention—the
gate had already failed maturity—but a future operational gate must be fit or
revalidated against the final frozen response distribution. Both issues must be
repaired before a longer run.

### 3. All-reply adversarial envelope

Each candidate first move gets one row for every legal opponent reply. Per
reply, the row may be `AVAILABLE`, `UNKNOWN`, or `REFUTED` based only on
grounded core/descendant authority.

The aggregate is deliberately fail-closed:

- any `REFUTED` reply makes the first move `REFUTED`;
- all replies must be grounded `AVAILABLE` to make it `AVAILABLE`;
- otherwise it remains `UNKNOWN`;
- the positive value is the minimum reply value;
- the weakest reply is selected as the next counterexample challenge.

This already supports composition across siblings: different certified cells
may cover different reply contexts, and their union can satisfy the envelope.
What V15 lacked was learned coverage of every reply, not an aggregation
operator.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_all_reply_envelope.py`](../../src/recon_lite_chess/autogrowth/native_all_reply_envelope.py)
  - `evaluate_all_reply_envelope` implements veto, unanimity, minimum value,
    and exact replay;
  - `rank_counterexample_challenges` chooses the weakest reply without looking
    at a correct move label.

### 4. Event-driven positive-shell ecology

The ecology sees only:

- opaque, generic graph-visible signal identities and their roles;
- the unique REAL receipt/physical-interaction identity and ordinal;
- one grounded Boolean environmental outcome.

It does not read board answers, held-out labels, mate distance, or an external
chess oracle.

On every REAL observation it updates matching sketches. A new family is born
only on **surprise success**: the environmental outcome is positive while the
pre-outcome authority was not already `AVAILABLE`. Up to one best conjunction
at each width 1, 2, and 3 is proposed. Candidate generation combines a bounded
evidence-ranked beam with a fixed share of content-blind hash exploration.

Default resource bounds are architectural safety limits:

| Bound | Current value |
| --- | ---: |
| Active sketches | 32 |
| Conjunction width | 1–3 |
| Candidate beam | 16 |
| Candidate search budget per demand | 4096 |
| Local observation proposal window | 256 |
| Residual children per contradiction event | 3 |
| Refinement events per sketch | 4 |

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_prospective_boundary_candidate_ecology.py`](../../src/recon_lite_chess/autogrowth/native_prospective_boundary_candidate_ecology.py)
  - `BoundaryObservation` and `BoundaryExpandDemand` define permitted inputs;
  - `ProspectiveBoundaryCandidateEcology.observe` updates matching sketches;
  - `rank_candidates` runs bounded local competition;
  - `retire_redundant` and the refinement lifecycle bound active metabolism.
- [`src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_intrinsic_curriculum.py)
  - `_boundary_ecology_step` connects one accepted REAL receipt to the ecology;
  - `_boundary_promotion_request_from_candidate` recloses an eligible sketch at
    a safe point.

### 5. Support, contradiction, refinement, dormancy, and death

A live sketch collects matches. A matching positive receipt is support; a
matching negative receipt is contradiction.

Promotion eligibility is fixed at:

- at least four supports;
- zero contradictions;
- Wilson lower bound at least `0.55`, with `z=1.6448536269514722`.

The Wilson quantity should be understood as a conservative ranking/gating
score. The development receipts are not guaranteed IID, so it is not a valid
frequentist confidence claim about the full chess distribution.

A first contradiction does not immediately kill a candidate. The coarse
candidate enters `REFINING` and abstains in the contradicted region. Residual
children add locally active contrast features that were absent from the
parent. Refinement has a finite event and child budget. Once exhausted, the
parent becomes dormant if a strict live residual exists, otherwise dead.
Capacity pressure and exact-pattern redundancy can also retire sketches.

The ecology keeps exact lifetime evidence/tombstones for replay, but recurring
hot-path indexes are bounded by the active resource caps.

### 6. Promotion is not authority

An eligible ecology sketch is converted into a `BoundaryPromotionRequest`.
At a content-blind safe point, the authority atomically:

1. validates compact commitments against accepted REAL chronology;
2. reserves/reclaims bounded successor capacity;
3. materializes a new dormant child with zero authority;
4. records an exact structural mutation/journal commitment;
5. opens the next prospective generation.

The discovery/eligibility receipts are committed to an exclusion set. They can
never certify the new child. Only later matching REAL receipts with ordinal
strictly beyond its birth frontier count. Current certification again requires
four clean supports and the fixed lower-bound gate. A contradiction prevents
`AVAILABLE` authority and can motivate narrower local refinement.

The authority successor capacity is 192 live/dormant specialization children.
Automatic retirement prefers weak replaceable leaves, protects immutable core
cells and live lineage parents, preserves unique tombstones, and rolls back the
entire structural transaction on any late failure.

Main implementation:

- [`src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py`](../../src/recon_lite_chess/autogrowth/native_prospective_evidence_authority_v2.py)
  - `BoundaryPromotionRequest` binds the promotion evidence;
  - `NativeProspectiveAuthorityV2.settle_pending_structural_requests` performs
    event-driven atomic settlement;
  - `retire_adaptive_leaves` provides bounded slot reuse;
  - `evaluate_sealed_real` and the REAL transaction methods separate read-only
    evaluation from learning.

### 7. Handoff and intrinsic credit

When an all-reply envelope is grounded `AVAILABLE`, its minimum successor value
is handed back to the first-move branch. The intrinsic-credit engine combines
that value with immediate environmental reward and eligibility/responsibility
to produce a TD error. Only the observed first move receives this update; no
unplayed action receives a synthetic positive label.

Main implementation:

- [`src/recon_lite_hector/learning/intrinsic_credit.py`](../../src/recon_lite_hector/learning/intrinsic_credit.py)
  - `IntrinsicCreditEngine` owns competence values, responsibility, eligibility
    traces, and grounded successor credit.
- [`src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py`](../../src/recon_lite_chess/autogrowth/native_single_graph_curriculum.py)
  - `apply_intrinsic_td` writes the scalar update into the observed graph
    pattern.

V15 proved that this write path can change later rankings relative to the
no-bootstrap control. It did not prove improved action choice or mate-in-2,
because the scheduled R1 training policy did not close the loop around those
rankings.

## Learner architecture versus scientific harness

This distinction matters when discussing whether the design is genuinely
local/self-organizing.

### Learner/organism semantics

- graph-visible micropattern activation and shared composites;
- local support/contrast receipts;
- surprise-success budding;
- local candidate competition and residual refinement;
- post-birth prospective certification;
- core/descendant authority routing;
- all-reply minimum/veto;
- responsibility, eligibility, and TD updates;
- bounded retirement and slot reuse.

### Harness or execution scaffolding

- generation of development positions and deterministic seeds;
- legal move/reply enumeration supplied by the chess environment;
- deterministic hash action schedule used by the current development runner;
- content-blind epoch/quiescent safe points for atomic mutation;
- independent full/no-bootstrap arms;
- snapshots, exact replay/resume checks, resource ceilings, and stop/go gates;
- held-out exhaustive mate evaluation used only after learning/reporting.

A safe point is acceptable scaffolding because it does not inspect pattern
content or decide what grows. The current stable-hash first-move schedule is
more consequential: it decides experience while ignoring learned value, so it
must not be mistaken for the desired autonomous policy. It uses an opaque
position identity for reproducible action permutation; that identity is not a
learner feature or certification signal, but it is still harness control over
experience.

## Defensible invariants

The current code and tests support these limited claims:

- discovery receipts are disjoint from certification receipts;
- only unique REAL physical interactions can add evidence;
- VIRTUAL queries cannot certify or train;
- promoted children begin with zero prospective authority;
- an all-reply `AVAILABLE` result requires every legal reply to be grounded;
- any refuted reply vetoes and successor value is the minimum reply value;
- structural mutations are atomic and replay-exact or roll back;
- active ecology work and live authority occupancy have explicit finite caps;
- immutable core source state and unique retirement tombstones are preserved;
- snapshot/resume and direct/replay paths are covered by exact tests.

The mechanism does **not** establish:

- convergence to mate-in-2 or any optimal policy;
- IID support receipts or calibrated statistical confidence;
- bounded lifetime artifact size (historical receipts/tombstones can grow);
- correctness of every learned abstraction or action alias;
- guaranteed core retention under the current immature-gate routing;
- eventual exploration of every useful region under the current finite run;
- a non-singleton, worst-reply-complete mate-in-2 handoff.

## Exact code lineage

| Commit | Role |
| --- | --- |
| `2f1b68c9` | Audited V2 intrinsic R0→R1 base and failed one-shot authority. |
| `55e940a9` | Implemented positive-shell event-driven ecology, refinement, retirement, and atomic integration. |
| `4cf1711b` | Corrected compact promotion commitment auditing. |
| `4a87eaa0` | Added bounded eight-epoch follow-through profile. |
| `58fbd0d8` | Predeclared the V15 mechanism gate. |
| `ad3b0777` | Added follow-through tests, exact audit assertions, and final branch logbook. |

Use [`BRANCH_LOGBOOK.md`](../../BRANCH_LOGBOOK.md) for the complete experiment
ledger. The exact V15 forensic analysis is in
[`ADAPTIVE_BOUNDARY_V15_FORENSICS_20260901.md`](ADAPTIVE_BOUNDARY_V15_FORENSICS_20260901.md).

## Focused tests

The most relevant suites are:

- [`tests/autogrowth/test_native_prospective_boundary_candidate_ecology.py`](../../tests/autogrowth/test_native_prospective_boundary_candidate_ecology.py)
- [`tests/autogrowth/test_native_intrinsic_all_reply_policy.py`](../../tests/autogrowth/test_native_intrinsic_all_reply_policy.py)
- [`tests/autogrowth/test_native_intrinsic_curriculum.py`](../../tests/autogrowth/test_native_intrinsic_curriculum.py)
- [`tests/autogrowth/test_native_prospective_evidence_authority_v2.py`](../../tests/autogrowth/test_native_prospective_evidence_authority_v2.py)

They cover surprise-success-only birth, failure-driven residual refinement,
promotion/certification separation, discovery exclusion, worst-reply gating,
core precedence, retirement/slot reuse, atomic rollback, exact replay/resume,
and TD integration.

## The architectural questions that remain worth discussing

1. What is the smallest genuinely local action-selection rule that lets learned
   value affect future experience while preserving broad exploration and exact
   replay?
2. Should core jurisdiction remain a separate prototype gate, or become a
   prospectively certified native competence shell using the same local
   evidence ecology?
3. When do abstract action triplets generalize correctly, and what local,
   action-relative residual feature should split an alias without injecting an
   absolute move or board identity?
4. Should certification require diversity across local context signatures in
   addition to unique physical receipts, to avoid several correlated patterns
   certifying from the same small event set?
5. How should local lineage families compete for reply coverage without adding
   a global planner or a new infrastructure layer?

The next implementation should answer the first two correctness/control
questions before expanding candidate machinery. The V15 evidence does not
justify a broader redesign yet.
