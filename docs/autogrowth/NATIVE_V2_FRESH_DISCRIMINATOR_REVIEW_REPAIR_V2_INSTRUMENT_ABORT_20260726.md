# V2 fresh discriminator review repair V2 — instrument abort

Date: 2026-07-26

## Verdict

The frozen package stopped before exposure and before any environment outcome
was opened. It is an instrument abort, not a positive, negative, non-engaged,
or exposure-starved scientific result.

The discovery prefix and exact-once arm construction completed. The global
preflight restored and semantically verified all 96 A/B/C organisms and issued
a complete zero-outcome receipt. The immediately following
prefix-to-snapshot reconstruction stopped at:

```text
FreshScientificIntegrityError: snapshot candidate contract mismatch:0
```

The failure occurred inside `_verify_prefix_snapshot_metadata` for seed ordinal
0. Per the frozen rule, the command was not repaired, repeated, or advanced.
No exposure artifact, execution manifest, science journal, carrier, or
canonical result exists.

## Frozen identities

- authorized starting HEAD:
  `3b5968725d3cae2092bfcd7a81060558e768b820`;
- source freeze:
  `29329b5906dbe41640fb9b94b7df5d4f971be693`;
- outer manifest SHA-256:
  `de8ff271ba49451e372814aa843956b85f22d557f52ecb7cad1b1d2a0cb2db60`;
- outer canonical digest:
  `93228166bdb2bee000511882b1ec05d72e46df58563e7adc57fc32ab15565b95`;
- discovery artifact commit:
  `ca9c45803b84794ce693884f434a7a24ea5208d9`;
- discovery manifest SHA-256:
  `b927528e1566f7c057cd5bedbf48d69b449633330c9a010c2667e29d22c0c542`;
- discovery manifest canonical digest:
  `9397f9734d42dbcfd0d614d5c30accd5253a73020b6c260f1a095db585bc642e`.

All protected V2.1 hashes and frozen source identities were exact immediately
before the failed stage.

## Admission and stop boundary

| Measurement | Result |
|---|---:|
| fixed seeds retained | 32/32 |
| planted target present | 32/32 |
| frozen selected spurious target present | 30/32 |
| both exact targets present | 30/32 |
| exact A/B/C snapshots constructed | 96/96 |
| globally restored and semantically verified | 96/96 |
| preflight outcome reads | 0 |
| exposure rows evaluated | 0 |
| outcome rows evaluated | 0 |

The global receipt has:

- manifest canonical digest
  `9415a2cf6527de69e8048b6b0b33e46be92180992fcac8931dfaafa95f67eb68`;
- receipt SHA-256
  `a20aec5ac0263deb6780c7426a5d2c3c02e92e0279f121735b2c1c3ca33afb92`;
- receipt canonical digest
  `bfd01aa67abbbb18849f5e15f2a8b05901fdd5ad158095612f1fda8b8033ec2e`;
- coverage: 32 seeds, 3 arms, 96 artifacts, complete;
- outcome access: count 0, empty event list.

Because the stop preceded exposure, A/B/C visible-signal parity, targeted
exposure, engagement, C contradiction dose, graph clearing consistency,
`D_safe`, `D_signal`, favorable-seed counts, pooled totals, effective sample
sizes, and raw/Holm-adjusted probabilities are all **not evaluated**. The
frozen exposure-starvation stop label was never reached and is unchanged.

No science journal was created, so journal restarts and completed-row replays
are both exactly zero. There are no wins, losses, or ties because no outcome
was opened.

## Artifact preservation

The exact raw arm manifest remains locally preserved at its canonical path:

- raw size: `1129782531` bytes;
- raw SHA-256:
  `ccb91d226c61b3354cb1c89cc939123c01a24723a0868ac5da36bf9b14a0b2e4`.

Because GitHub does not accept a single 1.13 GB ordinary Git blob and this
checkout has no large-file extension configured, an exact deterministic
`gzip -n -9` transport is committed alongside all 96 original snapshot files:

- compressed size: `65766696` bytes;
- compressed SHA-256:
  `92b8e7aa1b437281e346ddc57b1f4cb5c139ef68190c57f1699e6acd86f8d43f`.

`arm_snapshot_manifest_transport.json` binds both representations. Decompressing
the tracked transport must reproduce the recorded raw size and SHA-256 before
any future audit use. This packaging occurred only after the frozen stop and
does not alter experiment state.

## Runtime and interpretation

- discovery: `1284.49` seconds;
- exact-once A/B/C construction: `1466.33` seconds;
- joint preflight plus failed pre-exposure reconstruction: `849.06` seconds;
- total frozen computation before stop: `3599.88` seconds (59m59.88s).

The only supported interpretation is that snapshot transport and restored
semantic identity passed for the complete cohort, while the stronger
prefix/candidate identity contract did not reconstruct for seed 0. The frozen
science therefore supplied no evidence about prospective versus same-ledger
authority.

The planned scope was one frozen synthetic ecology and 32 genome seeds. Even a
completed result would have been conditional on those limits; this abort is
narrower because it never reached exposure or outcomes. KRK R1, retired-65,
historical regression, and every other learning package remain untouched.

No source, test, preregistration, threshold, seed, ecology, target rule, arm,
endpoint, statistic, or stop rule was changed, and no follow-up mechanism was
started.
