# V2 scientific harness atomic-snapshot reclosure — engineering result

Date: 2026-07-25

## Verdict

The bounded engineering reclosure **passes**. It repairs the instrument boundary
that caused the closed V2 scientific suffix to open arm A before discovering a
later arm-B identity mismatch. This is not a scientific result and the consumed
suffix was not resumed.

From pushed source commit `96e0568`, the canary constructed each of the 32
preserved prefix organisms once, persisted its A/B/C arms together, restored and
semantically verified all 96 saved arms, and only then issued the global
preflight receipt. The preserved-cohort outcome counter remained exactly zero.

The protected V2.1 authority and registry remained byte-identical:

- authority: `25945864fd998caf22ae12cbcb9bcb4779447337c0079f705640c63d2356f029`;
- registry: `f3aee5cccf761af1cb6a5de94b886d5e758c0a07cb0f6d77b8898f662ca73b58`.

## Diagnosis closed

Outcome-free seed-0 reconstruction reproduced the established cause:

- preoutcome exposure had constructed A/B/C through separate fresh cloning
  calls, while canonical execution reconstructed all three together;
- all reconstructed raw pickle hashes differed from the old frozen transport
  hashes;
- every canonical continuation digest remained exact;
- A/B wrappers, bases, envelopes, R0 organisms and state containers were
  nonaliased.

Therefore raw pickle SHA-256 is transport identity for one saved blob, not
semantic organism equality. The complete canonical continuation manifest plus
explicit experiment/source/candidate/polarity/topology/authority identities is
the semantic contract.

## Canonical outcome-free canary

| Gate | Result |
|---|---|
| Persist-once cohort | 32 seeds, 96 A/B/C snapshots |
| Snapshot count/bytes | 96 / 23,857,221 compressed bytes |
| Snapshot inventory digest | `d394cc6a05c36cb7778016144d553c3a2657aabbb036fd8f1a3fe084cac6d892` |
| Global transport/restoration/semantic coverage | 96/96 |
| Manifest internal digest | `a39dddc5ec1aa0231a47518c7c971b43235e64cd99b40d0b21bfd65e638c325d` |
| Preflight receipt digest | `8a3d7a8a8a551435dec8a5769012b2d8c32cd57e54c90bf826a0a9d1c05f0b56` |
| Preserved-cohort outcome access | 0 |
| Old suffix used | no |

The fully expanded manifest was 526,862,477 bytes because it contains every
complete canonical identity and a forensic compressed transport reference for
each arm. After the successful preflight, it was losslessly packaged with
deterministic gzip for Git transport. The uncompressed SHA-256 is
`c1471f2f2ff29fc46807199dbc5db2642a385861b61a925b9a46606d669076d8`;
the 41,734,169-byte compressed SHA-256 is
`f0ee54a32210d38a78f98588f42baffeb67324335273148e856f053fb6a9d557`.
`arm_snapshot_manifest_transport.json` binds both representations.

## Atomic transaction canary

The separately synthetic canary ran two rows through row-major A/B/C barriers.
It opened six synthetic events only, ended all three values at zero, and wrote
the exact durable sequence:

`PREPARED -> TRI_ARM_ROW_COMMITTED -> TRI_ARM_ROW_COMMITTED -> COMMITTED`.

The result digest is
`60284f700e1dd34ddb55a22ad38364c76d4e1f10dc24e3f0a73690ff2a9bcd8f`;
the journal-chain digest is
`c14b1079d7d15e8a6c02943943feb235262d33705a2b988177fd9aa14b85aa57`.
Adversarial tests inject failures at every A/B/C open, mint, consume and
invariant stage plus each durable-write stage. Live state remains all-or-none;
a dangling PREPARED seed is permanently nonresumable, while COMMITTED resumes
only at the next seed.

## Transparent preliminary stop

The first implementation canary at `b3a8749` stopped before global preflight and
with zero outcomes because the outer validator called the protected B mode
`legacy`, whereas `V2Mode.LEGACY.value` is `legacy_same_ledger`. The failed
attempt is preserved under
`v2_atomic_snapshot_reclosure_failed_b3a8749/`. The outer-only correction was
committed and pushed before the canonical rerun; no V2.1 byte changed.

## Validation

- focused/adversarial harness: final 42 passed in 15.93 seconds;
- critical V2.1 transaction/replay/VIRTUAL/registry subset: 5 passed in
  7,018.64 seconds;
- exact adjacent suite: 54 passed in 618.23 seconds;
- existing 1,013-test certificate inherited because both protected hashes are
  exact.

The canonical reconstruction/preflight/synthetic canary took approximately
30.5 minutes. No full-suite rerun was performed, as frozen.

## Scientific boundary and next work

This package proves instrument readiness only. It does not adjudicate
prospective authority, safety, coverage, engagement, any paired contrast, or
KRK behavior. No replacement outcome stream, fresh KRK, R1, retired-65,
historical regression or unopened validation data was accessed.

Any later scientific package must be separately preregistered and use a new
experiment/seed namespace with a physically disjoint full ecology and full
prefix/candidate/suffix tape. It must restore these persist-once semantics,
global all-arm preflight and atomic row-major A/B/C execution; it may not reuse
the consumed suffix.
