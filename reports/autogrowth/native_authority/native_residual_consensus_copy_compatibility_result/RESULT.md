# Residual-consensus copy-compatibility result

## Compatibility and differential validation

The copy-only compatibility repair is frozen at commit
`aea0fd24330b62957492672d5aa9639228a9d5f2`. It changed no learning rule,
manifest, or continuation digest and retained strict deserialization validation.
Current locks passed 2/2, prospective/escrow tests 31/31, comparator tests 7/7,
and residual/adjacent tests 53/53. The complete suite's 44 failures are the
recorded baseline historical replay incompatibilities; 1,364 tests passed, two
skipped, and the repair demonstrated no new failure.

## Retained Stage-0 admission

Stage 0 was not rerun. Its frozen opportunity result remains 32/32 seeds with a
legal direct pair or triple and 32/32 with a legal direct triple, bound by
`e31445a8564462d005fa815adab1077d1386de2fee5fab4aa3ef7445af5c7efd`.

## Scientific result

The one authorized 32-seed, three-arm execution completed and failed its
preregistered gates with terminal conclusion
`residual_consensus_engagement_or_evidence_starvation`. The true and deranged
arms each nominated direct pair/triple candidates in every seed, but none had
four later activation opportunities; both certified zero direct pair/triples,
engaged 0/32 seeds, and abstained on all 2,048 evaluations. The hash arm engaged
26/32 seeds, produced 234 TP and 16 FP, and still reached zero safe-narrow seeds.
The true arm had zero wins against either control.

R0 action retention was 3,072/3,072, serialization/VIRTUAL parity was 96/96,
virtual learning and host candidate selection were zero, and the zero mixed-
trace groups are recorded as not exercised with zero violations. Two independent
preregistered gates also failed: persistent R0 state was not exact in any of 96
organisms, and complete primary search-budget equality held for only 20/32
seeds. No repair, rerun, Mate-in-2, retired-65, fresh data, alternative seed, or
follow-up was started.

The frozen execution and exact adjudication are in `execution_freeze.json` and
`execution_closure.json`; the complete generated result remains in the parent
report directory.
