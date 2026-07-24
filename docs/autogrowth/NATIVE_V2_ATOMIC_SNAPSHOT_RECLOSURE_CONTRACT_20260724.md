# V2 scientific harness atomic-snapshot reclosure — frozen contract

Date: 2026-07-24

## Status and scope

This contract is frozen before implementation. It opens one engineering-only
package from `b54bacea2110f74000227671ccf7c6c731173562`. The closed V2 scientific
integrity abort and every existing artifact remain immutable. The old suffix is
never resumed or rerun.

No replacement outcome, scientific contrast, p-value, KRK fresh/historical/
validation stream, R1 row, or retired-65 successor may be opened. The protected
V2.1 files remain byte-identical:

- authority: `25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029`;
- registry: `f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58`.

The strongest null is that the harness cannot create one persistent semantic
arm identity that survives transport, complete-cohort preflight, atomic
tri-arm execution, and restart without altering V2.1.

## Established diagnosis

The preserved source proves that pre-outcome exposure called
`candidate_identical_arms` separately for each A/B/C cohort, whereas canonical
execution called it once and retained the three returned arms together. Pickle
memo/construction history therefore entered raw bytes.

An outcome-free fresh-process reconstruction from the preserved seed-0 prefix
and pre-outcome artifacts found:

| arm | frozen raw SHA-256 | reconstructed raw SHA-256 | canonical digest |
|---|---|---|---|
| A | `aadc95831b68d86216bcb64c9fd6f4b6d339988d53ddd1ac35cd2d896376f31d` | `d22f6e8e9bfe1c8f8bf9bd906d79577bf72d21ed7ec093c25a818b949f3f1187` | exact |
| B | `79eedded469073315b5c3beb4562e96fb5b92e81f5b8b127b9b468d069dec32b` | `1861105beb5d8a37866c8a21c7b7676db6a0fc9766653de2d06c1e28f98920d0` | exact |
| C | `88f561bf928cf5eedb4c3a2fb978427c411abfe852001a9b24e937cb6eb800b4` | `4eb183581d2f9e4a62369bd7fdaa29e2b9cee8c6d09f395e08f920b85587f74f` | exact |

All three reconstructed continuation manifests hash to their exact frozen
continuation digests. A and B have distinct wrapper, base, envelope, R0, and
state-container identities. No semantic B drift or mutable A/B alias is
present.

Binding rule: raw pickle SHA-256 is transport integrity for the exact persisted
blob only. It is never semantic organism equality. Canonical continuation
manifest plus its digest is the semantic identity contract. A restored object
need not re-pickle byte-identically.

## One changed engineering factor

Replace independent arm reconstruction and arm-local just-in-time checking with
one persisted arm cohort, one global semantic preflight, and one atomic tri-arm
execution/journal boundary. Learner, polarity, topology, lifecycle, authority,
receipt, registry, and scientific factors do not change.

## Predeclared implementation and artifact paths

Implementation may add only outer harness code:

- `src/recon_lite_chess/autogrowth/native_v2_atomic_snapshot_graph.py`;
- `src/recon_lite_chess/autogrowth/native_v2_atomic_snapshot_harness.py`;
- `tests/autogrowth/test_native_v2_atomic_snapshot_harness.py`.

Engineering artifacts live under:

`reports/autogrowth/native_authority/v2_atomic_snapshot_reclosure/`

with these paths:

- `arm_snapshots/seed-XX/{A,B,C}.pkl.gz`;
- `arm_snapshot_manifest.json`;
- `global_preflight_receipt.json` or `global_preflight_failure.json`;
- `legacy_diagnosis.json`;
- `synthetic_atomic_canary.json`;
- `synthetic_journal/`.

No scientific result path is declared.

## Persist-once arm law

After candidate freeze, each seed's A/B/C arms are constructed together exactly
once. The 96 raw payloads are compressed deterministically and atomically
persisted. The cohort manifest records for every seed/arm:

- path, raw/compressed SHA-256 and byte sizes;
- complete canonical continuation manifest and digest;
- experiment, source-organism, source-state, candidate-population, polarity,
  topology, executed-topology, authority, mode, and lawful initial-authority
  identities.

Exposure and execution may only restore these exact paths. They never reclone.
Transport hash verifies saved bytes; semantic identity verifies the restored
continuation manifest. `dumps(loads(payload))` equality is forbidden as a gate.

## Stable loading law

Future laboratory graphs are defined in
`native_v2_atomic_snapshot_graph.py`, never `__main__`. A compatibility loader
may map the old preserved `__main__.OpaqueChessEcologyGraph` only for the
outcome-free legacy canary. Every newly written snapshot must restore in a fresh
canonical subprocess through its real import path.

## Global all-arm preflight

Before any outcome call, load and verify all 32 x 3 registered artifacts.
Require exact coverage and association; transport hash/size; restoration;
canonical semantic identity; candidate, polarity, topology, authority, source,
and lawful arm-mode identity. The harness owns an outcome-access counter and
requires it to be zero.

Only after all 96 pass may the harness atomically write a digested global
preflight receipt binding the manifest and all entries. Execution requires that
exact receipt. Missing, duplicate, swapped, foreign, first/last corruption, or
semantic drift fails before outcomes.

Failure records must contain seed, arm, path, expected/observed raw hashes and
sizes, first differing byte offset, expected/observed continuation digests, and
stable JSON-pointer semantic differences. Classification is exactly transport
corruption, restore failure, or semantic drift.

## Atomic tri-arm and durable-journal law

Execution is seed-major and row-major. Before a row's environment outcome is
opened, all A/B/C pre-outcome states and graph commitments are verified. Mint,
consume, and invariant validation run on isolated staged copies. Live A/B/C
state changes only after every staged arm succeeds and durable row state is
written. Any A/B/C open, mint, consume, invariant, or durable-commit failure
commits none of the three live states.

Before opening a seed, write a hash-chained PREPARED record. Persist every
completed tri-arm row and an atomic COMMITTED seed checkpoint. A fully COMMITTED
seed resumes only at the next untouched seed. A dangling PREPARED record makes
outcome access uncertain and the stream permanently nonresumable. An uncertain
row or seed is never retried.

## Canary and adversarial gates

The preserved old cohort is used only to reconstruct/persist 96 snapshots and
run outcome-free global preflight. Transaction execution uses a small synthetic
engineering canary unrelated to the consumed suffix.

Tests must prove:

1. semantically identical, byte-different pickle layouts pass semantic identity;
2. semantic drift reports exact JSON-pointer differences;
3. first or last corruption among 96 fails with zero outcomes;
4. candidate, topology, polarity, mode, or source swaps fail;
5. failures at A/B/C open, mint, consume, invariant, and durable commit leave
   all live arms unchanged;
6. B/C failure cannot advance A;
7. dangling PREPARED is nonresumable and COMMITTED resumes at the next seed;
8. replay/remint, VIRTUAL isolation, candidate identity, and fixed polarity are
   unchanged;
9. future graph snapshots restore in a fresh process without `__main__` help.

Kill criteria are any protected-hash change, any outcome call before a complete
preflight receipt, any partial live tri-arm mutation, any imprecise mismatch
record, or any old-suffix access.

## Validation and closure

Run once: focused/adversarial harness tests; the critical V2.1 transaction/
replay/VIRTUAL/registry subset; and the adjacent 54-test suite. Inherit the
1,013-test certificate while protected hashes remain exact; do not rerun the
full suite.

Commit and push the engineering result with exact hashes and a clean worktree,
then stop. The next scientific package, if separately authorized, must use a
new experiment/seed namespace and physically disjoint full ecology/tape while
preserving the old hypothesis, arms, exposure gate, endpoints, and all-32 paired
analysis.
