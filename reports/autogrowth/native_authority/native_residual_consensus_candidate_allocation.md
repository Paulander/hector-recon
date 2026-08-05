# Residual-consensus candidate allocation

Terminal conclusion: `execution_failure_preserved`; no scientific gate or
positive/negative mechanism conclusion was reached.

Stage 0 passed: all 32/32 retained seeds had a legal direct pair/triple
opportunity and all 32/32 had a direct-triple opportunity. The source/config
freeze is commit `3f812b2e4c99fdd6a43b5b893a3563becf8332e9`; the external manifest SHA-256 is
`26bbb740fd7903db272a4ab8334a9924c537c3c42c2cfea3e2e4a57a36a76ab7`.

The one frozen service run stopped before cohort assembly at the prospective
trace-parity check. The runner compared `GraphSignalTrace.digest()`, which
contains frame identity, against reference digests minted with different frame
identities. That check is therefore structurally unequal even if actuation,
ordered signal identities and typed terminal signals agree. Exit status was 1;
the service used 539.181266 CPU seconds and peaked at 1,005,162,496 bytes. No
repair or replacement run was made, and partial worker outputs were not
interpreted.

Focused and directly affected adjacent tests passed 25/25. The required single
full-suite invocation reached about 20%, emitted five failure markers, then made
no observable progress for an extended bounded interval and was interrupted.
Pytest retained one named failure,
`test_discovery_epoch_atomic_native_escrow_and_closure`; no full-suite rerun was
performed.
