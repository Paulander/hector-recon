# V2 frozen-cohort execution adapter freeze — preregistration

Date: 2026-07-27

Starting commit: `2916fb04f4020bc682c29474ec3b1e9cb8dbf405`

Independent decision: `GO_TO_EXECUTION_FREEZE`

## Purpose and stop boundary

This is a bounded outer engineering package connecting the accepted canonical
candidate-contract comparison and stable import-path launcher to the existing
frozen exposure and outcome machinery. It executes readiness only. The real
exposure scan and outcome suffix remain unopened.

The package introduces one separately named adapter namespace and new output
paths. It does not modify the original V2 driver, learner, graph, registry,
snapshot implementation, stopped canonical comparison, stable launcher, 32
prefix organisms, 96 A/B/C snapshots, candidates, seeds, ecology, target
selection, arms, thresholds, endpoints, statistics or stopping rules.

Discovery, organism construction, cloning, filtering, seed replacement,
exposure and outcomes are forbidden in this package.

## Frozen inputs

At minimum the adapter binds:

- starting HEAD `2916fb04f4020bc682c29474ec3b1e9cb8dbf405`;
- passing launcher result SHA-256
  `92cf2e099a1f860deef4c90515f6b0617d7b95af521ab1c8604baecccd7202df`;
- accepted cohort digest
  `a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8`;
- prefix manifest SHA-256
  `b927528e1566f7c057cd5bedbf48d69b449633330c9a010c2667e29d22c0c542`;
- prefix digest
  `9397f9734d42dbcfd0d614d5c30accd5253a73020b6c260f1a095db585bc642e`;
- raw snapshot size 1,129,782,531 bytes and SHA-256
  `ccb91d226c61b3354cb1c89cc939123c01a24723a0868ac5da36bf9b14a0b2e4`;
- compressed snapshot SHA-256
  `92b8e7aa1b437281e346ddc57b1f4cb5c139ef68190c57f1699e6acd86f8d43f`;
- complete stored-cohort receipt SHA-256
  `a20aec5ac0263deb6780c7426a5d2c3c02e92e0279f121735b2c1c3ca33afb92`;
- receipt digest
  `bfd01aa67abbbb18849f5e15f2a8b05901fdd5ad158095612f1fda8b8033ec2e`;
- the complete original frozen laboratory package hash map.

The cohort is already known to contain the planted candidate in 32/32 seeds
and the selected comparison candidate in 30/32. Absent targets remain absent.

## Canonical runtime-view law

For each seed, readiness restores the exact A/B/C organisms, recomputes the
full candidate contract, verifies the stored and observed self-digests, and
requires complete canonical-byte equality. A genuine mismatch produces a
bounded field-level failure and stops.

Only after equality is proven may the adapter create a shallow ephemeral
manifest view whose per-seed contract object is the already-proven native
representation. The view may differ only by JSON representation: lists versus
tuples and strings versus string-valued enums. Its complete canonical byte
stream, size and digest must equal the source manifest. The source manifest
object and file must remain unchanged before and after construction.

The adapter then calls the exact frozen raw prefix-to-snapshot verifier with
that in-memory view. It never writes the view to disk, replaces a module global,
or changes candidate or graph state. The old seed-0 representation-sensitive
abort must remain reproducible before substitution.

## Public commands

The adapter freezes three future-facing public operations under literal fully
qualified module paths:

1. `verify-readiness` restores and checks the complete cohort, validates the
   ephemeral view and frozen raw verifier, and writes only readiness.
2. `run-exposure` repeats readiness, calls the unchanged frozen registry scan
   and parity/qualification reconstruction, applies the unchanged 24/32 gate,
   writes only the new exposure and execution paths, and cannot read outcomes.
3. `run-science` requires a committed admitted exposure and execution freeze,
   reconstructs all admission identities using the same restored objects, and
   only then permits the unchanged environment, atomic row execution, journal,
   committed-result reconstruction and adjudication to run in new paths.

No path is derived from `__name__`, callable metadata, `runpy`, source loading,
stack inspection or a parent command. There is no runtime replacement of old
module paths or globals.

## Preserved scientific design

The adapter preserves exactly:

- all 32 fixed seeds and all 96 A/B/C organisms;
- prospective A, same-ledger B and truthfully permuted C;
- the fixed 16-row suffix;
- four distinct target opportunities and the 24/32 admission rule;
- the complete engagement conjunction and every required graph clearing;
- `D_safe` and `D_signal`;
- all-32 paired sign tests;
- Holm correction over exactly two tests;
- the 17/32 favorable-seed rule;
- all frozen endpoints, thresholds, statistics and stop labels.

No tuning, candidate repair, seed filtering or scientific change is permitted.

## Focused engineering checks

Before the real cohort readiness command, focused tests cover:

- canonical byte/digest equality and source immutability of the runtime view;
- rejection of a true semantic change before view construction;
- reproduction of the stopped raw mismatch and pass only after equality;
- no candidate, graph or module-global mutation;
- literal public module paths and real fresh-process help commands;
- unchanged earlier output identities;
- rejection of any exposure outcome access;
- science admission failure before an admitted exposure;
- two-seed journal continuation at the next unfinished seed;
- all-complete summary reconstruction without replay;
- pre-outcome rejection of changed exposure, snapshot, prefix or execution
  identity.

Outcome-stage failure cases use synthetic fixtures only. The real exposure and
suffix remain closed.

## Real-cohort readiness gate

After source and artifact manifests are committed and pushed, execute exactly
one `verify-readiness` command in a fresh process. Pass requires:

- 32/32 canonical contracts;
- 96/96 restored organisms;
- cohort digest
  `a144fe94f4479c819756dfc44b22a2594e2b9df09367d571d39ab54007560bb8`;
- identical source/runtime/source canonical manifest byte identities;
- unchanged stored manifest hash and self-digest;
- zero candidate or graph mutation;
- zero module-global replacement;
- zero exposure rows and zero outcome reads;
- byte-identical earlier package files and outputs.

A failure is preserved in the new namespace and stops. No in-package repair or
rerun follows a real readiness failure.

## Delivery

Commit and push separately:

1. adapter source, focused tests and this preregistration;
2. source and artifact manifests;
3. the passing readiness artifact, result note and authoritative ledger update.

Run no three-order closure repeat and no full repository suite. Inherit those
results by exact hash. Stop before `run-exposure` for independent review.
