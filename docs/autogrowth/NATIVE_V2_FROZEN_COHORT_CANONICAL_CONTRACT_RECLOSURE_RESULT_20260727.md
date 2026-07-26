# V2 frozen-cohort canonical-contract reclosure — result

Date: 2026-07-27

## Verdict

The package stopped at an outer-runner instrument failure before the first
fresh-process cohort comparison. This is neither a canonical-contract mismatch
nor a pass. Exposure and outcomes remained unopened.

The failed child process was invoked with Python module name `__main__`.
Python therefore rejected the invocation before loading or comparing an
organism:

```text
Error while finding module specification for '__main__'
(ValueError: __main__.__spec__ is None)
```

The frozen package was not repaired or rerun. Its failure artifact records
ascending order, return code 1, zero completed orders, zero exposure rows and
zero outcome reads.

## Completed evidence

- Starting abort `a504ba919d92e7f1d1838a3ca318eac3d983811b` remains preserved.
- Source freeze:
  `0859a4a1db53eb6221e3ac48e19d156896aa56c6`.
- Manifest freeze:
  `7b41c9210aff57d0b8db2b5302754e68695836bb`.
- Source-manifest SHA-256:
  `4050a6598f54b50c05f7abe580cf122c27bcc56738e5bb9f515d858180730f62`.
- Source-manifest canonical digest:
  `30df57817025d4ecf615bae1b7da599771037f19093bf3d01bee91a706f8bc7a`.
- Artifact-binding SHA-256:
  `f6f60742ebd5341eaa37d9704e8595d0d712754429ae824e2e6434d436968869`.
- Artifact-binding canonical digest:
  `2e1e68a107ad6e28bf86764c89f206dccf438d376b83c965f5a862d0cb40462f`.
- Bound cohort: 32 prefix organisms, 96 A/B/C snapshots and 32 stored
  candidate contracts.
- Exact raw manifest reconstruction passed at 1,129,782,531 bytes and
  SHA-256
  `ccb91d226c61b3354cb1c89cc939123c01a24723a0868ac5da36bf9b14a0b2e4`.
- The seed-0 diagnosis reproduced the expected boundary:
  stored and restored digest
  `a5f275b7dc3d897f7870535d7e0f471969eb3ff8c9bec2452d77f8445c9d95aa`,
  equal canonical bytes, unequal raw dictionaries, and only tuple/list plus
  string-enum/string representation differences.
- Focused checks passed 15/15 in 68.09 seconds, including the real seed-0
  artifact.
- Manifest construction and input verification completed in 23.47 seconds.
- The stopped cohort command ran for 4.81 seconds and did not complete an
  order.

Failure artifact:

- SHA-256:
  `c345a35666a95d603472a01b935cd2ec4cedb8581996c8684568fb29ae0ff9c6`.
- Canonical failure digest:
  `e3c05cd49296381e0eb2508084a7d38e0ee6c0508a141f54f15fde2bdb0d8b9d`.

## Interpretation and boundary

The canonical comparison itself passed its focused and seed-0 checks, but the
preregistered all-32 gate was not evaluated. No claim is made about all 32
contracts, 96 snapshots, order invariance or fresh-process parity.

The fixed cohort remains previously observed at 32/32 planted targets and
30/32 selected comparison targets. The suffix is still unopened. The old
`a504ba9` result remains a valid instrument abort. A future attempt requires
independent review and a separately frozen outer-runner repair; it must not
silently continue this stopped package.
