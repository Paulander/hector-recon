# Native mature-cell falsification: instrument-repair addendum

Status: engineering-only repair frozen after the first canonical attempt.

The first attempt is preserved byte-for-byte as
`native_mature_cell_falsification_instrument_abort.json` together with all 96
serialized arm organisms. It correctly reported
`stage=implementation_instrument_abort` because its restore gate failed in all
96 arms.

Localization found no persistent-state or inference mismatch. The runner had
defined restore identity as equality between the original pickle bytes and a
second pickle produced after loading. Pickle memo and alias ordering are not a
canonical state representation. On the preserved artifacts, the complete
canonical envelope manifest and correction audit survive exactly. The existing
V3B persistence contract likewise compares `to_manifest()` before and after
restore.

The sole repair changes that gate to equality of the complete canonical
manifest, which contains configuration, every cell and its evidence/lifecycle
state, evidence keys, lifecycle and correction audits, and the graph snapshot.
The source and restored manifest SHA-256 values are persisted independently.
Artifact pickle bytes retain their own SHA-256 but are not treated as a
canonical state digest.

No organism mechanism, arm, outcome, row order, control permutation, threshold,
cell transition, metric, or scientific gate changes. The original control
manifest remains immutable. A separate cryptographic repair manifest must be
generated from the pushed repair commit and pushed before the same package is
repeated. It freezes the repair files and hashes the preserved abort result and
all 96 abort organisms.
