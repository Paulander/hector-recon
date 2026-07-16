# NATIVE_FRAME_PURITY_AND_COMPETENCE_AUTHORITY_CLOSURE

Date: 2026-07-16. Status: engineering-only package. Commit `1501a18` and
its canonical admission abort are immutable. This package does not rerun
competence learning or access validation, regression, retired-successor, final,
or fresh pools.

## Objective

Close two implementation boundaries before any corrected competence admission:

1. R0 inference must use frame-local runtime state while persistent topology,
   weights, credit, lifecycle, telemetry, and exact serialized state remain
   unchanged.
2. The connected competence path must pass a serialized
   `NativeR0CompetenceOrganism` directly into
   `NativeHandoverGenome.query_child_slots`; experiment-side response injection
   is restricted to explicitly named laboratory controls.

## Contracts

- one real R0 query preserves full persistent-component hashes;
- repeated and permuted frame orders produce identical per-frame actions and
  responses;
- one virtual successor cannot contaminate another;
- scheduler telemetry cannot affect inference;
- R0 pickle serialization and load normalize node state, tick, activation,
  scheduler telemetry, and runtime choice counts;
- a serialized competence wrapper is accepted directly by native child-slot
  generation;
- the connected wrapper path remains functional when experiment-level
  `response_with_availability` is fail-hard;
- a synthetic mature envelope changes native handover while disconnected and
  shuffled controls fail.

The exact-state audit retains runtime fields and scheduler telemetry. Purity is
proved through non-mutation, not by excluding fields from the digest.

## Admission-only canary

The canary may access only the 48 R0-train plus 16 train-decoy contexts already
used by the aborted package. It performs no competence update or growth.

It persists exact overall and subgroup counts before applying these gates:

- 64 unique evidence keys;
- both outcome classes;
- at least 12 successes and 12 failures;
- zero fabricated reward;
- exact persistent-state identity;
- natural/repeated/permuted virtual-frame parity;
- direct serialized-wrapper authority;
- causal synthetic-envelope controls;
- zero competence growth.

Whatever the result, stop for review. Do not open validation, regression,
retired successors, fresh data, or R1 learning.
