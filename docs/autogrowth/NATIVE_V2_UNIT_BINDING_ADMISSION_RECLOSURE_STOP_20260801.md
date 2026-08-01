# Native V2 unit-binding admission reclosure — preserved stop

## Classification

This bounded, outcome-free package is an **instrument stop during the second
restore**, not a mechanism result, valid negative, engagement result, or KRK
result.  It did not launch science and did not read an outcome.

Starting commit: `4c41e8b15597aab959ac2d271bffa2f5293d7bb5`  
Replacement attempt: `20260731T202101435174689Z`  
Elapsed time to preserved stop: approximately 3 h 35 min 08 s

## Exact localization

The original second-restore rejection was reproduced without constructing the
outcome environment.  Only arm A changed.  Its root difference was the raw
serialized payload of `A/seed-00`:

- historical exposure payload SHA-256:
  `8d029f3dd290b1e76aa5b566fda6c913761b8e79494ebe1b33d41fb7c39df18d`;
- second-restore payload SHA-256:
  `b7c977af92995c6163b555fd50817101e4f887532ad215452fd604430a2b7e84`.

That changed arm A's shared registry identity and consequently all 32 arm-A
unit-binding digests.  A bounded single-organism reproduction found zero value
differences, zero dictionary-order differences, exact continuation equality,
and 69 reference-alias differences.  The differences are pickle memo sharing
of equal dictionary-key strings, principally repeated `config` keys.  Candidate
population, experimental identity, source binding, source snapshot, graph,
topology, arm/seed/organism, row, tape, run, package, and zero-outcome identities
were exact.

The machine-readable localization is
`reports/autogrowth/native_authority/v2_process_readiness_repair/unit_binding_admission_diagnostic.json`
(SHA-256
`61ede2efa636456ee330d25e00f85b50c870e47a4b7ec5d42767f8d7cbf15400`).

## Narrow repair exercised

The existing `RepairExposureUnitJournal` admission comparison was changed in
place.  It now constructs an explicit portable semantic projection and excludes
only the three proven transport-derived fields:

- `payload_sha256`;
- `registry_identity`;
- `unit_binding_digest`.

Historical values remain in the unchanged journal and remain bound by the
original record chain and completion marker.  The portable projection binds the
complete remaining unit binding plus explicit source raw/compressed and semantic
snapshot identities, source-binding projection, candidate population,
experimental identity, graph continuation, arm/seed/organism identity, row
order and definitions, tape, run, package, and zero-outcome state.

Focused checks passed 25/25.  The full current and adjacent admission suites
passed 94/94.  They demonstrate that representation-only change passes while
candidate, continuation, topology, arm, seed, row, tape, package, outcome state,
journal chain, stored binding, committed result, and reconstructed artifact
changes still fail.

## Replacement-run result

The first complete restore passed and was durably checkpointed:

- 96/96 portable unit-binding comparisons;
- 96 committed units;
- zero transport mismatches;
- exact exposure and execution reconstruction;
- protected files byte-identical;
- science paths absent;
- outcome access exactly zero.

Its checkpoint SHA-256 is
`3ca3e3ac5e33eebf31b7f140b31eed23ba4de005c9798ec099899abfd5f8a9d8`.

The decisive second restore advanced beyond all portable unit-binding checks
and entered exact artifact reconstruction.  Reconstruction then stopped in
`V2LaboratoryRegistry.adjudicate_cohort()` with:

```text
ProspectiveV2IntegrityError: foreign registry scan result
```

The committed scan wrappers still contain the historical registry identity,
whereas the freshly reconstructed registry contains the raw-pickle-derived
second-restore identity.  The unit-binding comparison was therefore not the
only place where the same transport identity enters admission.  No in-package
repair or further run was attempted.

The preserved failure SHA-256 is
`a0b2d7af92b31e478671e9c1a8f900ac7ff7d98e8328b5e2cab04100d7c90cf1`.

## Preservation and interpretation

All 195 protected exposure, execution, completion, and journal files remain
byte-identical.  Their set digest before and after the attempt is
`9082cf52f505d924590458c4dd2a7f365bbdec3494cdbbc3d974726e97cb4239`.
No science-start marker, outcome journal, carrier, canonical result, or outcome
environment was created.  Outcome access remains exactly zero.

The bounded conclusion is narrower than a completed admission repair:

> Portable semantic unit-binding comparison is sound at the tested boundary,
> but completed-exposure reconstruction has a second raw-transport dependency
> in registry-owned scan-wrapper identity.

External review should decide whether the next bounded closure may compare
stored scan wrappers to a registry-owned portable organism identity while
retaining their exact historical bytes and chain bindings.  Outcomes remain
unopened.
