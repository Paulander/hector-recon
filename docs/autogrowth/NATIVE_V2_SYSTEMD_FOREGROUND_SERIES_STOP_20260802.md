# Native V2 systemd foreground series stop

## Verdict

The service transport worked, and the first portable-admission child completed
successfully. The outer coordinator then stopped on an exact JSON-shape check
before launching the first verifier. This is a **terminal outer-contract stop
after child success**, not an admission-cohort replication, exposure, outcome,
mechanism, learning, or KRK result.

The series is closed under its frozen no-retry rule. Slots 02 and 03, all three
individual verifiers, and the aggregate verifier were not started.

## Execution result

The service started from clean exact child commit
`8479cbdd22ed06d09eea3bd051a2e0e8344063ec` with outer manifest SHA-256
`2f9895f3a9a7c7b6aae99615b5739a2eb4fdab8efc7244a814e20e9d68aa0b28`.
It retained the coordinator as its foreground main process, used `Restart=no`
and an infinite runtime ceiling, and kept running for the complete child task.

Slot 01 (`portable-admission-01-e7dfd710b975`) ran for
`33090.446947380995` seconds and exited zero. Its preserved result reports:

- 96/96 complete semantic identities;
- 96/96 portable bindings;
- 96/96 portable unit results;
- zero candidate/graph mutations;
- 32/32 admitted historical registry organisms in each of A, B, and C;
- portable cohort digest
  `5f6de9695ee0da4a74d01b2f27d2f5b0e9abb2845e304f31d230c67b5477327b`;
- zero outcome events and absent science paths.

The child result is byte-identical to its captured stdout at SHA-256
`f3fa534f84eb6221b93146cac03d446bede447dfb91529e1553e63297a3bd3d6`.
Its internal record digest is
`2165afec220b8c0cbd6867689c54c7ff9ed2166432c8a6d4d45df6647dd1c124`.

## Exact stop

The child emitted:

```json
{"count": 0, "event_ids": [], "science_paths_absent": true}
```

The outer coordinator compared that complete object for equality with:

```json
{"count": 0, "event_ids": []}
```

The additional truthful `science_paths_absent` field made the equality false,
producing:

```text
RuntimeError: child outcome access changed:portable-admission-01-e7dfd710b975
```

No count or event identity changed. The error wording therefore describes the
failed equality gate, not an outcome read. The terminal record itself preserves
outcome count zero and an empty event list.

## Preservation and finalization

The coordinator stopped immediately, launched no later task, and did not retry.
Finalization recorded a terminal service with `MainPID=0`, `Restart=no`, and
zero outcome access. Its record digest is
`5b4bc3717389ef10706001b0a712d47422d5b49f882f7ea36554dddaecb08697`;
the file SHA-256 is
`a4c63c8f6476c87294efc576574e9eb79cc9fdd3d1a5b27e9f31705666ae4690`.

The complete child attempt, service records, empty service logs, canary records,
and concise machine-readable stop summary are committed unchanged. The series
must not be restarted or repurposed. Any successor requires a new externally
reviewed identity and must treat this completed slot as historical evidence,
not as a resumable task.
