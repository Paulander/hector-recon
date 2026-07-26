# V2 frozen-cohort canonical-contract reclosure — preregistration

Date: 2026-07-27

Starting commit: `a504ba919d92e7f1d1838a3ca318eac3d983811b`

## Purpose and hypothesis

This is a bounded outer engineering package. It repairs only the representation
boundary used to compare the frozen prefix contract with the contract rebuilt
from the exact persisted A/B/C snapshots. The stopped review-repair runner and
its `a504ba9` instrument abort remain unchanged and reproducible.

Hypothesis: all 32 frozen contracts are semantically exact after restoration,
and the seed-0 abort was caused only by JSON round-trip representation changes
(`tuple` to `list` and a string-valued enum to its string value). Verifying each
self-digest and comparing complete canonical JSON bytes will accept all 32
without accepting a changed contract.

Strongest null: at least one seed has a genuine canonical value, key, length,
order, candidate, hypothesis, topology, polarity, mode, initial-state, or
continuation difference; alternatively the result depends on evaluation order
or contract evaluation mutates a stored organism.

## Frozen input and disclosure

The package reuses one already-observed, outcome-blind candidate cohort and one
fixed synthetic ecology:

- all 32 fixed genome seeds remain included;
- planted targets are already known to exist in 32/32 seeds;
- frozen selected comparison targets are already known to exist in 30/32;
- 32 exact prefix organisms and 96 exact A/B/C snapshots are immutable inputs;
- discovery, selection, arm construction and snapshot persistence are not run;
- the evaluation suffix remains unopened.

Any future causal claim will therefore be conditional on this fixed,
outcome-blindly reused candidate cohort and ecology. This engineering package
itself makes no causal or KRK claim.

Bound commits:

- discovery: `ca9c45803b84794ce693884f434a7a24ea5208d9`;
- organisms: `58ed832b912629a25a1450acc1007c011e958840`;
- instrument abort: `a504ba919d92e7f1d1838a3ca318eac3d983811b`.

The binding manifest must include the exact prefix-manifest hash/digest, all 32
prefix transports, the raw and compressed snapshot-manifest hashes and sizes,
all 96 snapshot transports and semantic identities, every stored contract
digest, and the complete zero-outcome preflight receipt.

## Information and change boundary

Exactly one factor changes: complete contract comparison at the outer
persistence boundary uses canonical JSON bytes after independently verifying
the stored and reconstructed self-digests. No field is deleted. A digest alone
is not sufficient. Complete canonical equality remains required.

The laboratory may read only already-persisted prefix and snapshot artifacts.
It may reconstruct the raw manifest from its committed deterministic gzip,
restore the exact snapshots, compute their existing semantic contracts, and
compare them. It may not scan suffix rows, request exposure, instantiate the
truthful result stream, or open an outcome.

Byte-identical preservation is required for:

- the stopped review-repair runner;
- the protected V2.1 learner and registry;
- the graph implementation;
- the atomic snapshot harness;
- every prefix organism and A/B/C snapshot;
- all existing manifests, targets, seeds and reports.

## Comparison law

For each seed:

1. Load the frozen contract from the reconstructed manifest.
2. Recompute and require its self-digest.
3. Restore the exact A/B/C snapshots and recompute the existing full contract.
4. Recompute and require the restored contract's self-digest.
5. Compare the complete canonical JSON bytes.
6. Independently recheck candidate population, target hypotheses and member
   order.
7. Require complete before/after semantic organism identity.

On a canonical mismatch, stop with at most 32 deterministic field rows carrying
the exact seed, JSON pointer, kind, expected value and observed value. No seed
may be filtered, rebuilt, replaced or reordered out of the result.

## Arms and predictions

There are no learning or exposure arms. The engineering controls are three
fresh-process evaluation orders over the same immutable cohort:

1. ascending seed ordinal;
2. descending seed ordinal;
3. even ordinals followed by odd ordinals.

Prediction under the hypothesis: all three processes produce the same
order-independent cohort digest; all 32 contracts and 96 organisms pass; seed 0
reproduces raw-Python inequality while its canonical digest is exactly
`a5f275b7dc3d897f7870535d7e0f471969eb3ff8c9bec2452d77f8445c9d95aa`;
no organism or artifact changes; exposure and outcome counts remain zero.

Prediction under the null: a bounded genuine field difference, mutation, or
order-dependent cohort digest stops the package.

## Gates and stop rules

Pass requires all of:

- exact reconstruction of the 1,129,782,531-byte raw manifest with SHA-256
  `ccb91d226c61b3354cb1c89cc939123c01a24723a0868ac5da36bf9b14a0b2e4`;
- all fixed commit and artifact bindings exact;
- 32/32 stored self-digests valid and reproduced;
- 32/32 complete canonical contracts equal;
- 96/96 snapshot transport and semantic identities exact;
- identical cohort digest across three fresh processes and seed orders;
- zero candidate, graph, prefix or snapshot mutation;
- zero exposure rows and zero outcome reads;
- all stopped-package result paths remain absent.

Any genuine canonical mismatch, binding failure, mutation, order dependence,
exposure read or outcome read is a terminal engineering failure. Preserve it
and stop. Do not alter the comparison, cohort or learner in-package.

## Compute and delivery budget

Run the focused synthetic/seed-0 tests once, then the all-32 read-only verifier
in the three frozen orders. Do not run the full repository suite because all
protected files remain byte-identical. Do not run discovery, arm construction,
exposure, results, historical regression, retired-65, KRK R1 or any follow-up
learning mechanism.

Freeze source and artifact-binding manifests before the all-32 verification.
Commit and push the source freeze, manifest freeze and final engineering result
separately. Stop before exposure for independent review.
