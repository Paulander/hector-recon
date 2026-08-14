# Deferred-specialization initialization reclosure

Status: **INITIALIZATION RECLOSED — SCIENTIFIC ATTEMPT NOT EXECUTED**

This additive package starts from preserved commit
`c1476253252248bfd981e6a66fb84f5671894cc3`. The historical discriminator,
performance reclosure, failed attempt, terminal record, and verified cache were
not changed. The only corrected ordering is:

`open -> grow -> V2 wrap once -> wrapper close once -> clone arms`

## Exact diagnosis

Both historical runners close `organism` nomination before calling
`NativeProspectiveAuthorityV2.from_organism()`. Immediately before that call,
the source epoch is therefore closed. `from_organism()` imports a wrapper with
`experimental_identity=None`; its invariant check recomputes the identity
required by the closed epoch and raises `experimental initialization identity
mismatch`.

The production-path canary reproduced this on all 32 frozen genome seeds. The
actual identity was null in every case. For seed
`907644595097955793`, the failed-path expected identity digest was
`66397a1d5637aba35ce90f71f40c7c64fe06c79474002b3fc59d6dd548c80bbb`.
The canary JSON records the corresponding digest for every seed. The error is
inside `from_organism() -> _verify_invariants`, before any parent-prospective
event.

The corrected path passes an open epoch into the wrapper and closes it through
`wrapper.close_nomination()`. For the example seed, the freshly recomputed and
installed corrected identity digest was
`80042acfa302305bffa8046239af87cc460b5651f37e20dc8b4233332657b155`.
It intentionally differs from the failed-path expected digest because only the
wrapper-owned close records `NATIVE_NOMINATION_CLOSED`; the underlying candidate
population remains identical.

## Semantic parity and boundary canary

The canary used only the 64 already-consumed `parent_discovery` rows. Their
ordered row-ID digest is
`03f0ac2e85d31e6848a76e863923f475bb119fd6b2238ab18a948ee7829c85e7`.
Results:

- 32/32 discovery-growth and corrected-wrapper initializations passed;
- 32/32 wrapper-owned closes installed the freshly recomputed identity;
- 96/96 candidate-identical arms passed the future Stage-A invariant check;
- every seed had an eligible mixed-outcome shadow parent (167–179 per seed);
- candidate populations contained 168–181 cells per seed;
- parent-prospective events, exposure scans, Stage-B events, and new-outcome
  accesses were all exactly zero;
- the stop was immediately before the first parent-prospective row.

For every seed, the reference organism-only close and corrected wrapper close
were exactly equal for candidate IDs/counts, members, fixed polarities,
dormant-shadow states/origins, nomination escrows and categorized read sets,
lineage/depth, selected parent identity/manifest, frozen candidate manifest and
digest, receipt/evidence ledgers, R0 topology/weights/credit/lifecycle digests,
R0 emitted action/trace/successor behavior, and source organism/state
identities. Before specialization mode was assigned, all three arm
hypothesis/escrow/candidate/topology manifests had one identical digest per
seed. After assignment, their executed decision-topology digests remained
identical.

Fields that cannot be byte-identical are wrapper-owned metadata, not semantic
waivers: immutable hypothesis digests on wrapper base cells, V2 state and
structural-invariant records, the wrapper close event, experimental identity,
generation boundaries, and the deliberately different specialization mode
after arm parity is recorded. No candidate, escrow, evidence, R0, or executed
topology difference was waived.

The engineering artifact is
`reports/autogrowth/native_authority/native_deferred_specialization_initialization_canary.json`.
It makes no engagement or performance claim.

## Preserved identities and stopping point

- Historical discriminator SHA-256:
  `35d83440b6060ef56f9908dc5b2fc82cb93e2241f364c40f97fea7f2f20ac9c3`
- Historical performance reclosure SHA-256:
  `fe8fdc182b501aedb0fc7341335b960b84a8746a3f1f618f4f23dde6765c44f2`
- Failed `attempt.json` SHA-256:
  `01e241771e47c1094f81c30eca7007fbb820f0a269e8851c05feebea0ee02ccc`
- Verified cache SHA-256:
  `2d364c274fab22863082daa09fc51d4e402df41c44ebb0d692539f0967c5403f`
- Terminal failure record SHA-256:
  `a2d790634f0523438edf23a1dc25e3de308942639e4fb9eddb22beaf5dc84b25`

No scientific attempt was started. The future command is preserved in the
source manifest but is **NOT AUTHORIZED**.
