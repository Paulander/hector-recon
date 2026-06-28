# Default-Off Child Consensus Canary Runtime

The default runtime policy remains `parent_only`.

Supported explicit policies:

- `parent_only`: parent foundation/runtime only.
- `child_shadow_only`: compute child evidence without allowing child influence.
- `child_consensus_canary_balanced`: default-off experimental canary branch.
- `child_consensus_canary_failclosed`: stricter canary that falls back on uncertainty.
- `no_child_canary_harness_control`: canary logging path with child influence disabled.

Example commands:

```bash
uv run python scripts/autogrowth/run_runtime_stage_gate_campaign.py --target-tier 1
uv run python scripts/autogrowth/run_default_off_canary_runtime_campaign.py --target-tier 1
```

Rollback/fail-closed rules:

- child cache unavailable falls back to parent-only behavior.
- actuator uncertainty blocks child influence.
- cache/live uncertainty blocks child influence.
- decoy and hard-decoy vetoes block child influence.
- child state and artifacts remain separate from the frozen parent.

This package is not main/default adoption.
