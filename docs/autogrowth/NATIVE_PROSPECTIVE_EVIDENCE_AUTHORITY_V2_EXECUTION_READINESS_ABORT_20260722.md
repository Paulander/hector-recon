# Native prospective-evidence authority V2 execution-readiness abort

Date: 2026-07-22
Branch: `codex/native-krk-resume-composition`
Reviewed source: `cbf8b5167a80e9c03e9881b81a266dd73b32142d`
Pre-code contract: `8259273`

## Verdict

**Execution readiness failed at the binding behavior-preservation control.**

The current trigger-fixed nomination polarity changes ordinary native growth
behavior on the already-viewed engineering tape. The package instruction
required preserving this mismatch and stopping rather than tuning it away.
Accordingly, no registry canary, canonical runner, stream, preregistration,
fresh/unopened confirmation data, R1, or retired-65 data was accessed.

The incomplete implementation draft was discarded. The executable diagnostic
below runs against the reviewed `cbf8b51` mechanism itself.

## Control

Both arms began from the same trace-native R0 source and consumed the same four
already-viewed grounded negative receipts in the same order.

- Baseline: ordinary native growth with no prospective discovery epoch.
- Instrumented: the existing V2 wrapper opens the prospective epoch and native
  growth creates trigger-fixed nomination escrow.
- Genome, seed, proposal budget, lifecycle, thresholds, capacities, receipts,
  and request order were identical.
- Comparison excluded escrow-only metadata such as the numerical
  `availability_error`; it retained proposal round/order, members, seed,
  graph-request state, admission/reason, and cell identity.

The fixture reconstructs already-viewed retired training material and
validation-named development material. The correct statement is: **no fresh or
unopened confirmation data were accessed.**

## Exact mismatch

The first causal proposal divergence was proposal-row index 8:

| field | ordinary native baseline | escrow-instrumented |
|---|---|---|
| structural round | 2 | 2 |
| request ordinal | 0 | 0 |
| selected context | `context:competence_context_0001` | `context:v2_child` |
| selected base atom | `tg26s_shared_atom_b45e62de533291522a6d` | same |
| materialized cell ID | `competence_context_0007` | same |

An earlier numeric difference (`availability_error -0.5` versus `-1.0`) was
classified correctly as permitted instrumentation metadata. The round-2
context-parent change is not metadata: it changes the graph/genome input and
therefore fails exact behavioral parity.

## Interpretation

Baseline candidates begin polarity-free and acquire polarity from their
aggregate lifecycle evidence. Prospective candidates are constrained at birth
to the triggering outcome polarity. On this tape that changes which earlier
candidate is mature/eligible when round-2 context composition occurs. The
result is therefore evidence that the present fixed-polarity birth contract is
not behavior-neutral with respect to the native learner it is meant to
instrument.

This does not show that fixed polarity is scientifically wrong, nor does it
authorize weakening escrow. It shows that V2 cannot simultaneously claim
behavior-preserving instrumentation and the current trigger-fixed rule. That
architecture decision requires external adjudication before the remaining
readiness repairs or a scientific discriminator are opened.

## Reproduction

```bash
TMPDIR=/tmp uv run pytest -q tests/autogrowth/test_native_prospective_evidence_authority_v2.py -k trigger_fixed_polarity_behavior_gate_aborts_on_context_divergence
```

Result: **1 passed, 16 deselected in 277.73 s (4m37s)**. The passing diagnostic
asserts the exact abort mismatch; it is not a parity pass.

## Stopping boundary

Not run after the stop fired:

- the 32-organism registry-bound engineering canary;
- adjacent native/V1 suites;
- the full repository suite;
- any V2 scientific runner or canonical tape.

Integrity hashes, HMACs, and manifests remain tamper-evident mechanisms, not
proof against a caller able to execute repository code. Prefix-only global
closure remains an experimental isolation device, not final online ReCoN
doctrine.


## 2026-07-22 external adjudication addendum

The abort above remains preserved as an instrument-abort record, but its causal
attribution is withdrawn. Its fixture was not state-identical: it held eight
accepted receipts and zero envelope evidence records. Ordinary growth reviewed
only the four added negative records, while prospective wrapping silently
hydrated the eight historical receipts before reviewing those same four
negatives. The compared evidence ledgers were therefore 4 versus 12.

Prospective epoch opening now fails closed unless receipt IDs exactly equal
evidence IDs, every evidence record exactly equals the record derived from its
receipt (including ordered active signals, typed provenance, outcome, actuator,
completion terminal and policy response), and every cell evidence reference
belongs to that ledger. Opening is copy-on-write and never hydrates missing
evidence. The old 8/0 fixture is rejected without changing its continuation
digest.

On a coherent matched ledger, all 12 proposal rows match and both arms choose
`context:v2_child` at proposal row 8. Exact graph request/error values,
members, IDs, support, success/failure counts, lifecycle, maturation, pruning,
nesting, classifications, topology and graph actions match. Differences are
confined to escrow/provenance metadata and fixed polarity on final
non-authoritative PRUNED tombstones. The corrected 8+4 parity gate passed in
329.67 seconds. The exact frozen historical source was also verified at 96
receipts / 96 exact evidence records; its matched-ledger 96+4 parity smoke
passed in 152.78 seconds.

Therefore `de790fd` does **not** establish that fixed-at-nomination
polarity changes native growth. Fixed polarity remains part of the frozen V2
hypothesis, and the readiness package may proceed from the corrected canonical-
ledger boundary.
