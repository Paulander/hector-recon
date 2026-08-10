# Prospective contradiction-triggered specialization of shadow-origin hypotheses

Status: **DESIGN_ONLY — NOT_IMPLEMENTED — NOT_EXECUTED**

This composition asks whether a prospectively contradicted shadow-origin
hypothesis can nominate a narrower, independently certified child using the
existing graph-local specialization machinery. It adds no scorer,
chess-specific rule, data source, or outcome-time child creation.

## Required event and epoch sequence

1. An actual genome nomination finalized as `mixed_outcomes` remains a dormant
   shadow with zero decision influence.
2. Distinct, later REAL outcomes may satisfy the unchanged V2 prospective rule
   and certify the parent. Discovery evidence and VIRTUAL frames do not count.
3. A later REAL contradiction is evaluated prequentially, then immediately
   revokes the parent's decision influence through the existing graph-local
   removal path.
4. In the specialization arms, that same confirmed contradiction may emit the
   existing graph-local specialization request. The open outcome event ends
   after revocation and request emission: it may not create, evaluate, match,
   certify, or grant capacity to a child.
5. A subsequent structural epoch may consume the frozen request. The existing
   genome may materialize at most one width-two, one-level child through the
   current specialization grammar: `context:<parent>` plus one eligible base
   identity.
6. The child receives a new immutable nomination escrow, the parent's fixed
   polarity, a lineage link, and a certification frontier at or after every
   receipt read during nomination. Parent discovery support, parent prospective
   support, eligibility reads, and the triggering contradiction are categorized
   discovery/proposal evidence and are all certification-excluded.
7. The child begins dormant with zero decision influence. Only still-later,
   distinct REAL outcomes beyond its frontier may certify it under the unchanged
   V2 rule. VIRTUAL frames remain measurement-only. A later contradiction uses
   the same graph-local revocation path.

The persisted request must bind the parent identity, request ordinal,
contradiction receipt, graph-confirmed eligible terminal identities,
specialization mode, and source continuation digest. Serialization/restoration
must preserve it exactly. It is an unevaluated structural request, not a child
or a provisional decision cell.

## Paired comparison

| arm | contradiction behavior | later structural epoch |
| --- | --- | --- |
| local-contrast specialization | revoke parent and emit the existing `LOCAL_CONTRAST` request | existing genome may choose one graph-eligible identity supported with the parent and absent from the contradiction |
| demotion/revocation only | existing revocation with `DISCONNECTED` specialization | no request and no child |
| counterexample-blind specialization | revoke parent and emit the existing `COUNTEREXAMPLE_BLIND` request | same genome, proposal slot, width, and child lifecycle, without the local absence-from-contradiction condition |

Local-contrast and counterexample-blind arms must be exactly matched per parent
for request opportunities, request ordinals, proposal attempts, genome seed,
proposal width, capacity checks, and without-replacement behavior. Differences
in graph-confirmed eligibility are the intended factor. The revocation-only arm
must be identical through the parent's contradiction and removal.

## Prequential measurements

- Transition ledger per lineage:
  `DORMANT_PARENT -> PROSPECTIVELY_CERTIFIED_PARENT -> GRAPH_LOCAL_REVOCATION -> REQUEST_EMITTED -> EVENT_CLOSED -> CHILD_NOMINATED_IN_LATER_EPOCH -> DORMANT_CHILD -> {PROSPECTIVELY_CERTIFIED_CHILD, DORMANT_CHILD}`,
  followed by child revocation when contradicted.
- False decision influence: any parent influence before certification or after
  its contradiction, any child influence before its own certification, and any
  influence caused by a VIRTUAL frame. Every such count must be zero.
- Evidence separation: exact receipt IDs and ordinals used for parent discovery,
  parent certification, contradiction, request eligibility, child escrow, and
  child certification. Their prohibited intersections must be empty.
- Specialization accounting: emitted, restored, consumed, rejected, and
  materialized requests; eligible identities; proposal attempts; child births;
  child certifications; parent and child revocations.
- Final safe coverage: unique positive evaluation rows influenced by currently
  certified, non-revoked cells, reported only for populations with zero false
  positive decision rows. Report raw coverage; impose no 29/32 or Mate-in-2
  claim.
- Exact R0 retention at source, parent certification, parent contradiction,
  event closure, request restoration, child birth, child certification, and
  final evaluation: topology, weights, credit, lifecycle, action, ordered signal
  identities, typed terminal signals, and terminal source identities.

## Validity stops

Stop before interpretation if a child is created or evaluated inside the
triggering outcome event; if any pre-frontier, duplicate, or VIRTUAL receipt
certifies a child; if a child lacks a fresh escrow or immutable polarity; if
more than one child is materialized per request; if a non-graph-nominated member
is injected; if specialization arms lose matched budgets; if serialization
changes a request or lifecycle state; or if any R0 audit or semantic trace
changes.

No cohort, seed, threshold, row, or execution is selected by this note. No
fresh data, 32-seed replay, R1 transition, or implementation is authorized.
