# Native V2 Execution Launch Amendment — Cleanup Addendum

Date: 2026-07-28

The first detached canary completed its 1,085-second child interval with exit
status 0, exact recorded launch identity, and zero stderr. Finalization stopped
because the cleanup gate required both `systemctl stop` and
`systemctl reset-failed` to return zero.

The recorded sequence established:

- `stop` returned zero and unloaded the transient retained unit;
- `reset-failed`, called afterward, returned one with the exact diagnostic that
  the same unit was not loaded;
- an independent status read reported `LoadState=not-found`,
  `ActiveState=inactive`, `SubState=dead`, and `ExecMainPID=0`.

This is a cleanup-adjudication defect, not a child-runtime failure. The failed
finalization attempt, its original source/binding/launch-readiness artifacts,
and its exact external records remain preserved.

The bounded correction retains both cleanup commands and requires:

1. exact success from `stop`;
2. either exact success from `reset-failed`, or its exact same-unit
   already-unloaded response after the successful stop;
3. an independent final observation that the unit is
   `not-found/inactive/dead` with no process.

Any different command failure, diagnostic text, loaded state, active state, or
remaining process still fails. No learner, graph, registry, laboratory,
cohort, ecology, threshold, journal, statistic, exposure, or outcome behavior
changes.
