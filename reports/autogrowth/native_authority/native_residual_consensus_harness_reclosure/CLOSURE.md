# Residual-consensus harness reclosure

Engineering validation stopped before science. The frame-neutral comparator and
its binding tests passed 7/7, and the residual/adjacent layer passed 46/46. The
preserved instrument-stop artifacts remain byte-identical, legacy V1 escrow
serialization remains unversioned, and all 32 frozen continuation digests load
exactly.

The prospective/nomination-escrow layer reproducibly failed three atomic
mutation tests. The residual-consensus extension's `NominationEscrow.__setstate__`
calls `__post_init__` during `deepcopy`, so a deliberately mutated escrow raises
`ValueError: nomination escrow digest mismatch` before V2 can perform its own
atomic integrity classification. Repairing that production compatibility defect
would exceed this comparator-only reclosure.

Stage-0 admission remains the preserved 32/32 pair-or-triple and 32/32 direct-
triple result. The complete repository suite was not run because the focused
gate failed. No residual-consensus scientific process was launched and no
scientific conclusion was reached.
