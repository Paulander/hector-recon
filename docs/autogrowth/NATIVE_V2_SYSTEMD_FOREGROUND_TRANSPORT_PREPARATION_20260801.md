# Native V2 systemd foreground transport preparation

## Classification

This is **transport preparation only**. No portable-admission child, individual
verifier, aggregate verifier, exposure, science, outcome, learner, or KRK task
ran.

## Frozen identities

- Recovery series: `systemd-foreground-1107519c8a4448ed8e7bc134b8a68140`
- Outer execution 01: `outer-01-b7f1b46f135c4a66893f079e2c1a13c5`
- Outer execution 02: `outer-02-667cb406345d472c8ef878c975d9553a`
- Outer execution 03: `outer-03-df72c8c3c9204dd4af9616cf8adab5f3`
- Real unit:
  `hector-recon-v2-admission-e697c46cf43a4129a54d24341be70e29.service`
- Canary unit:
  `hector-recon-v2-canary-2ec72b8bab3d4965a987e8b7433e19cc.service`

The closed series `canonical-path-d79e26e2e483404289497ab764ec4b35`
and all of its outer identities remain permanently retired.

## Transport design

The external coordinator is the foreground `ExecStart` process owned directly
by the WSL systemd user service. It does not background another coordinator. It
performs the complete canonical preflight, synchronously launches and waits for
each child/verifier in the frozen order, requires distinct PIDs, and runs the
aggregate only after three passing individual verifiers. It records every
command, PID, start/end time, exit or signal, and stdout/stderr hash outside the
child directories. `Restart=no` and a terminal-on-interruption contract prevent
implicit retry or resume.

The harmless canary imports no ReCoN package, touches no experiment path, stays
foreground for 80 seconds, and records durable start and completion identities.

Frozen hashes:

- outer manifest:
  `2f9895f3a9a7c7b6aae99615b5739a2eb4fdab8efc7244a814e20e9d68aa0b28`
- foreground coordinator:
  `8d14ba9c67f3558e23143bde19a0aa070e3c1c1937ebad4b5d27f2dad94a963c`
- harmless canary:
  `46be6389c326ad00aa7ec11a85fe8d3d73bae68cf9fd2f9740d8a645a45b06a7`
- exact launch contract:
  `dbde8b5ad29ea546f82f78550f6859b89c3e8e5c2eb71ea81f015290154a0bd1`
- command document:
  `654b5274e8e757b0a3c7c41cc4026a3dd061c010710461ba1030f5e0aee225ed`
- preparation result:
  `d77e06a1661d7f91ac608f22bc2f9545142ce0c3762f7589d1000a2f74c417ba`

## Verification

Transport-only tests passed 10/10 in 7.362 seconds. They covered unique outer
identities, direct foreground service ownership, exact manifest/source binding,
read-only status/finalization, synthetic synchronous execution, exact
exit/log recording, terminal nonzero handling, atomic-record ambiguity, and a
canary with no ReCoN imports.

A read-only coordinator preflight from clean exact child HEAD
`8479cbdd22ed06d09eea3bd051a2e0e8344063ec` passed the canonical root,
interpreter, PYTHONPATH, module resolution, preservation refs, frozen hashes,
195-file protected set, absent attempt/science paths, and zero-outcome gates.
Its record SHA-256 is
`2b66a0b05f491f664655ae0084cee407c1bb2578d33bced72aefca733127c25c`.

The managed command environment could not access the WSL user bus, returning
`Failed to connect to bus: Operation not permitted`. Per instruction, no
substitute launcher and no canary were used. The exact normal-WSL canary,
status, verification, real-series, status, and finalization commands are frozen
in
`reports/autogrowth/native_authority/v2_systemd_foreground_transport_preparation/systemd-foreground-1107519c8a4448ed8e7bc134b8a68140/COMMANDS.md`.

## Preserved guarantees

- Commits `06707de`, `dec63b5`, `16b5350`, and frozen child `8479cbd` remain
  unchanged.
- All supplied prior record hashes matched.
- All 195 protected files remain exact at digest
  `9082cf52f505d924590458c4dd2a7f365bbdec3494cdbbc3d974726e97cb4239`.
- Outcome access remains exactly zero.
- No real service was launched.

## Subsequent execution closure

After independent authorization, the harmless canary passed and the real
service was launched once from exact child commit `8479cbdd`. The service
transport remained alive for the complete first child, which passed all 96
portable-admission units after approximately 9 hours 11 minutes. The outer
coordinator then stopped before verification because the child result's
zero-access object included the additional truthful field
`science_paths_absent: true`, while the coordinator required exact equality to
a two-field object.

Outcome access remained zero. No later child, verifier, aggregate, exposure, or
science step ran. The frozen no-retry series is terminal and preserved in
`NATIVE_V2_SYSTEMD_FOREGROUND_SERIES_STOP_20260802.md`.
