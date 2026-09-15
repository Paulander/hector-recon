# Recovery progress and durable archive

This file supplements START_HERE.md. Check raw retry-control/status.json for
newer progress; this is a durable publication checkpoint, not a live heartbeat.

The handover was published before retry at48e184e33df7307b5abc9926636b93b8456a75d1.
The tested recovery wrapper/source is remotecebb51bd4e5682ce2f4a6b2e875b1628b3bdd63e,
localaa6ef44711ba00876dc99b92807ac4c12812299c, common tree
1051d2273833040eb417204f1baadc1085f2cc34. All86 original runtime files stayed
unchanged; the recovery snapshot additionally hashes the wrapper and retry protocol.

The retry initialized successfully, reusing84 verified sealed blocks and87
checkpoints. All39 original uncheckpointed actual executions were reexecuted
against the real environment and all complete records matched exactly.
Seed21 is now complete: current16/16, original trial11/16, revised14/16 at1920.
Seed22 current is also complete at12/16. Its two trial arms and seed23 were still
pending at this publication point. Frozen verification has not started yet.
Do not mistake these statements for final cohort results.

A verified archive containing all three completed seed21 trajectories was saved:

- Name: HECTOR_OWNER_TRIAL_RETRY_20260915.zip
- Library identity: libfile_594e815364a881918743618e665c0e4e
- File ID at version0: file_0000000079ec81f4a849c0bb53d681ef
- Version0 size:12,024,530 bytes;11,999 members;11,998 verified payloads
- Version0 SHA256:81d05130a545506f14074deabfb1d82f2eb910df8a1f6a51a13f14448535ff0a
- Coverage:5,760 sealed logical training actions; no frozen verification yet
- Local path:/workspace/scratch/2d2531e3ef96/HECTOR_OWNER_TRIAL_RETRY_20260915.zip

Later versions will use the same Library identity. Resolve its current version
before restoring; verify its own SHA256SUMS.json and source pins. The original
interrupted archive remains separate and unchanged. See OPERATIONS_AND_RECOVERY.md
for its identity and recovery protocol. Git-backed sources/docs/reports are omitted
from the raw archives and remain in the private repository.

Continue the already-authorized remaining units with the retry wrapper. Completed
worker receipts and sealed block manifests, not tool-session IDs, determine the
next action. All units have exited normally so far; there has been no score-driven
extension, learner retuning or main merge. Do not launch the original fresh runner
on an existing recovery directory or silently repeat an unfinished new unit.
