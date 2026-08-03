# Native V2 systemd outer schema reclosure result

## Verdict

The bounded admission-only schema reclosure passed. Three independently
identified child processes reproduced the same 96-unit portable cohort and the
same historical exposure/execution artifacts. The frozen aggregate verifier
accepted all three attempts. Graph/candidate mutation and outcome access were
both zero.

This closes the outer result-schema mismatch reported at `81f70c4`. It is
admission and historical-reconstruction evidence only. It is not an exposure
rerun, an outcome-stage result, a mechanism result, a learning result, or KRK
R1 evidence.

## Frozen identity

- Frozen child HEAD: `8479cbdd22ed06d09eea3bd051a2e0e8344063ec`
- Preparation commit: `6290caca9c01952e019cfdb62af8af14c3be3db0`
- Recovery series: `schema-reclosure-00079210ade5457dab063a8ce990a4a2`
- Outer manifest SHA-256:
  `643443467633a67943546c5d89a68f3948a6781324467ca0225ba87857ab4aea`
- Protected-file count/digest: `195` /
  `9082cf52f505d924590458c4dd2a7f365bbdec3494cdbbc3d974726e97cb4239`
- Portable cohort digest:
  `5f6de9695ee0da4a74d01b2f27d2f5b0e9abb2845e304f31d230c67b5477327b`

## Execution

Slot 01 was not rerun. Its immutable four-file result from `81f70c4` was
verified in place. Slots 02 and 03 each ran once, followed by their frozen
read-only verifier. The aggregate verifier then ran once.

| Slot | Child PID | Child seconds | Result SHA-256 | Result digest |
|---|---:|---:|---|---|
| 01, carried | 282158 | 33090.447 | `f3fa534f84eb6221b93146cac03d446bede447dfb91529e1553e63297a3bd3d6` | `2165afec220b8c0cbd6867689c54c7ff9ed2166432c8a6d4d45df6647dd1c124` |
| 02 | 771465 | 34162.529 | `7b7f7b0aec56489c9f1d6c3fa5a632054bf45699051d1243854d08305124dfaf` | `eb6750ef73e2070c74f30c6b9cb65dccf31cc18ea7577d973e6de310c46f56ab` |
| 03 | 824722 | 31027.032 | `62084c4ecd71781e48157d186e9ab81f1513b8ab4f19b154aa350fd33a17fbf9` | `a5540e02df73b3dc478d059dfb94b194f7038814d9f2b00560737649f28c9fdb` |

The successor service ran for `62325.712` seconds (17 h 18 m 45.712 s).
Every child reported:

- 96/96 complete semantic identities;
- 96/96 portable bindings;
- 96/96 portable unit results;
- the same 192-record, 96-unit historical journal with zero recomputation;
- the same A/B/C historical registry identities;
- zero graph/candidate mutation;
- zero outcome events and absent science paths.

The aggregate result retained the exact historical artifacts:

- exposure SHA-256:
  `6a0d086599c44f035d07a07fa389d680019e7e7fdeaace75e978640e587ad2a7`;
- execution-manifest SHA-256:
  `8fa649f4587099f5f1eae54468736bfd410b3d12d46576393916021a4a128216`;
- exposure-completion SHA-256:
  `c92a51b13c16be884ae168cece22b16501ab9006086ba1fea16b7658fd2c0ec7`.

## Terminal records

- Aggregate digest:
  `a7bf36df7309f67da8d6c42ae700dd032413dcfa70390d47fba7e40c35eae733`
- Aggregate stdout SHA-256:
  `041f25d1d18808f073f4ebb5db73e27aab192436dc4670e4a4a106f20797aeb4`
- Series-terminal digest:
  `def1470f6a2618e3738f20ee3fc65b2862f22394b51797a1738a3d93f5e7d75f`
- Series-terminal SHA-256:
  `1d43bf5363971bd20fae6c4755ee3416a7e19079e22ff609e422a9b44204c6e3`
- Finalization digest:
  `f5ff79a020d7ad247c29284b7d5aae84105cb87bb57bcca4cdd09fbd26f500dc`
- Finalization SHA-256:
  `ab32f8d1ea7d3991aac0bcb431a392c28d5c45704840edca65b7b382c99bb109`

All child and verifier processes exited zero without a signal and with empty
stderr. Finalization observed the service inactive, absent after cleanup, and
successful. Outcome access remained exactly `{"count": 0, "event_ids": []}`.

## Bound conclusion

The carried-slot schema correction is valid and the complete frozen cohort is
portable across three independent processes. Exact historical exposure and
execution reconstruction is stable at this boundary. The package stops here as
required. It does not authorize exposure, outcome execution, KRK R1, or a new
learning mechanism.
