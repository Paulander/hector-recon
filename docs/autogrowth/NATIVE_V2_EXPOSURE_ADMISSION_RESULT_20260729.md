# Native V2 Exposure Admission — Result

Date: 2026-07-29

Source commit:
`0bff5e622a9a28c75d13e421cff4faae33e55e5c`

Exposure attempt:
`20260728T212343341863Z-90c45431306648c5bee6604f9469832a`

## Verdict

**PASS — the frozen pre-outcome exposure stage is complete and admitted. Stop
before outcomes.**

The stored cohort provided the required recurring opportunities in 30 of 32
seeds, exceeding the frozen 24-of-32 admission requirement. The planted target
had eight distinct opportunities in every seed. The selected comparison target
had eight in 30 seeds and was absent in two. All 512 stored pre-outcome row
comparisons matched across arms A, B, and C.

This is exposure and admission evidence only. It shows that the frozen
experiment has enough matched opportunities to proceed to independent review.
It is not yet evidence that the proposed mechanism works, is not a learning
result, and is not a KRK result. The outcome stage was not started.

## Integrity review

- The journal contains exactly 96 `PREPARED` records and their 96 corresponding
  ordered `COMMITTED` records, covering units 0–95.
- Journal chain digest:
  `d827d8f1d45f4cebd8adb02ec895e4c3cd9d48249265572a64c81f568f6c3f75`.
- Exposure recomputation count: `0`.
- Exposure admission: `30/32`, against the frozen requirement of `24/32`.
- Stored row parity: `512/512`.
- Outcome access: `0`, with no event identities.
- The execution manifest is admitted and binds the stored exposure.
- The service exited `0`, received no signal, and produced empty stderr.
- Service cleanup was accepted; the retained unit is absent.
- Service-record SHA-256:
  `bd2f342c16e360f713209251e1e82f802291df182e2b89b8fe76f2e83503d12a`.
- Final service-record digest:
  `9fda978b1b9768c304dc16f1b91f3267aa11138a4a68925d921874d4ba042bf9`.

The repository was at the exact expected source commit before preservation.
Only the generated exposure, execution, completion, journal, and service-record
paths were untracked. No tracked source or frozen-package file differed from
`0bff5e622a9a28c75d13e421cff4faae33e55e5c`.

## Preserved artifact identities

- `preoutcome_exposure.json` SHA-256:
  `6a0d086599c44f035d07a07fa389d680019e7e7fdeaace75e978640e587ad2a7`
- Exposure canonical digest:
  `c95b60c670bb7b80a387f44da4c40e1790bc4100ff3f2a4f923b8a26ee5b7e3b`
- `execution_manifest.json` SHA-256:
  `8fa649f4587099f5f1eae54468736bfd410b3d12d46576393916021a4a128216`
- Execution canonical digest:
  `35587e65c9dc59a420af68c42868333f54af85d8b7f31b73c60d9eec948edb5d`
- `exposure_completion.json` SHA-256:
  `c92a51b13c16be884ae168cece22b16501ab9006086ba1fea16b7658fd2c0ec7`
- Completion canonical digest:
  `a63e0e073bbf77598a3fdd67192e83a0162b5b65475a88b05306cbd5c6b4a8a8`

No artifact was regenerated, no exposure row was replayed, and no outcome was
opened during this review.
