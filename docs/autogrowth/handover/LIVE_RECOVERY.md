# Recovery complete: final durable record

Completed2026-09-15. All nine arms reached1,920 actions. No worker, pending unit
or failed unit remains. All270 blocks and279 checkpoints verify, including all
4,464 frozen reproductions. Do not resume this closed cohort or run verification
again. See ../OWNER_TRIAL_LEARNING_RESULTS.md for interpretation and exact tables.

| Seed | Current | Original trial | Learning-trial |
| --- | --- | --- | --- |
| 21 | 16/16 | 11/16 | 14/16 |
| 22 | 12/16 | 12/16 | 12/16 |
| 23 | 12/16 | 10/16 | 12/16 |
| Total | 40/48 | 33/48 | 38/48 |

Handover publication preceded retry implementation/play:
remote48e184e33df7307b5abc9926636b93b8456a75d1.
Retry source remotecebb51bd4e5682ce2f4a6b2e875b1628b3bdd63e,
localaa6ef44711ba00876dc99b92807ac4c12812299c,
common tree1051d2273833040eb417204f1baadc1085f2cc34.
All86 original runtime files remain unchanged; all88 retry source hashes match.

## Counts and caveats

The logical study has17,280 training,4,464 scheduled evaluation and4,464 frozen
reproduction actions. Reused:5,376 training/1,392 evaluation. Newly executed in
retry:11,904 training/3,072 evaluation/4,464 frozen. All39 known uncheckpointed
original actions were reexecuted in the environment and matched exactly; they
were never replayed as logged feedback or double-credited to the learner.
Known recorded physical work across both attempts is26,247 actions, including
those39 repetitions. Original unrecorded in-flight work remains unknown.

Independent no-play audits pass: all actual credits, measurement flags, assignment
RNG, owner/trial histories and4,464 arithmetic choices. Eight exact endpoint
capacity contradictions and one rational witness; no fitted weights installed.
All revised endpoints lack16 capacity. Five revised trials accepted, four pending,
no second review completed; seed23 accepted a noise-bit partition. Current stays
the reference. No learner retuning or main merge occurred.

## Final archive

- Name: HECTOR_OWNER_TRIAL_RETRY_20260915.zip
- Library identity: libfile_594e815364a881918743618e665c0e4e
- Final version:3; file ID:file_0000000040b08210900c4d7ad39828be
- Size:36,276,210 bytes;36,641 members;36,640 checked payload hashes
- SHA256:b1c09311fc891c8f0a5b898b924f4b9cf4871d7f52a9e09e51d5d1878de339ec
- Coverage: complete raw run, final result, all frozen verification receipts,
  source hashes, reused provenance, environment, unit receipts and recovery JUnit
- Local path:/workspace/scratch/2d2531e3ef96/HECTOR_OWNER_TRIAL_RETRY_20260915.zip

Versions0/1/2 were intermediate durable checkpoints. Restore version3 for completed
evidence. Verify SHA256SUMS.json and source pins. Original interrupted archive
libfile_1f179c97dea081918faac4def83827cb remains separate and unchanged. Git-backed
source/docs/reports are omitted from raw ZIP and live in private Paulander/hector-recon,
branch codex/context-owned-decisions. Main remains
2aa1ce47a6a93e2571aaa0b02101e9543fe94955. The final report publication is discoverable
from branch history; its containing commit identifies the final handover version.

For a new instance: restore source/docs, read START_HERE.md and final results,
fetch/verify this archive, then inspect existing reports. There is no authorized
additional cohort or learner change hidden in the recovery commands.
