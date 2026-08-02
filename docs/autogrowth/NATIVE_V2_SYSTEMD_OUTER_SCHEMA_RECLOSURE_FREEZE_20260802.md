# Native V2 systemd outer schema reclosure freeze

## Scope and authorization

This is the bounded outer-only successor authorized after the terminal
`81f70c4` result. It does not modify the learner, portable-admission bridge,
historical launcher, child module, manifests, field classifications, comparison
allowlists, cohort, rows, thresholds, or statistics. It authorizes admission
verification only and stops after the frozen aggregate verifier. Exposure,
science, outcomes, KRK R1, and follow-up mechanisms remain prohibited.

## Exact correction

The coordinator now maintains two separate exact JSON contracts:

- persisted child `result.json` must contain exactly
  `{"count": 0, "event_ids": [], "science_paths_absent": true}`;
- verifier, aggregate, and outer transport records retain exactly
  `{"count": 0, "event_ids": []}`.

Canonical JSON equality rejects missing fields, unknown fields, false values,
nonzero counts, event identities, and JSON scalar-type substitutions. The
shared two-field transport constant was not changed.

## Carried slot 01

Slot `portable-admission-01-e7dfd710b975` is immutable carried input from
commit `81f70c4f90439d4c89d793ff6b8268d289b54d32`. Its four files are individually
bound both to materialized bytes and to the source commit. The coordinator also
binds the captured stdout, launch and terminal records, return code zero, empty
stderr, child PID `282158`, result SHA-256
`f3fa534f84eb6221b93146cac03d446bede447dfb91529e1553e63297a3bd3d6`,
and internal result digest
`2165afec220b8c0cbd6867689c54c7ff9ed2166432c8a6d4d45df6647dd1c124`.

The PID-uniqueness set is seeded with `282158`. The slot-01 child command is
absent from the successor task plan and cannot be rerun. Slots 02 and 03 must be
absent at preflight.

## Frozen successor

- Recovery series:
  `schema-reclosure-00079210ade5457dab063a8ce990a4a2`
- Carried outer execution:
  `outer-carried-f1853fbbad49424f880dc8dddb1bdfb5`
- Slot-02 outer execution:
  `outer-02-18398e6457964d6e9d1c3ef62cb00a6b`
- Slot-03 outer execution:
  `outer-03-65c3ced40f3b437e84b06645412896e4`
- Service:
  `hector-recon-v2-schema-6a8e100e71b846b98715e72fb378c75e.service`
- Frozen child HEAD:
  `8479cbdd22ed06d09eea3bd051a2e0e8344063ec`
- Outer manifest SHA-256:
  `643443467633a67943546c5d89a68f3948a6781324467ca0225ba87857ab4aea`
- Coordinator SHA-256:
  `f869e52e4505127d1e4a004d5f16d179196062725c24943acdafa17924c73c5f`
- Protected 195-file digest:
  `9082cf52f505d924590458c4dd2a7f365bbdec3494cdbbc3d974726e97cb4239`

The six-task plan is exactly:

1. slot-01 read-only verifier;
2. slot-02 child once;
3. slot-02 read-only verifier;
4. slot-03 child once;
5. slot-03 read-only verifier;
6. frozen aggregate verifier.

The service remains foreground and synchronous, with `Restart=no`, no runtime
ceiling, a new record namespace, and a terminal stop on the first failure.

## Pre-execution validation

Focused transport tests passed 12/12 in 4.809 seconds. They cover exact child
and transport schemas, all relevant malformed variants, actual carried-slot
commit/record binding, full child-directory gates, changed-hash rejection,
absence of the slot-01 child command, new unique identities, absent future
slots, frozen protected files, and absent science paths.

At this freeze point the successor record root does not exist, slots 02 and 03
have not run, and outcome access remains exactly zero. The literal start,
read-only status, and finalization commands are frozen in `COMMANDS.md`.
