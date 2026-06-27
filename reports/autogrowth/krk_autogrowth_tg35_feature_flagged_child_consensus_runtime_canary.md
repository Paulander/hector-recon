# TG35 Feature-Flagged Child Consensus Runtime Canary

- checkpoint_pass: `True`
- interpretation: `feature_flagged_canary_ready`
- default runtime policy: `parent_only`
- canary runtime policy: `child_consensus_canary_balanced`
- total / paired episodes: `100000` / `20000`
- parent / canary success: `5678` / `7581`
- paired help / hurt / net: `1903` / `0` / `1903`
- parity selected/outcome/gate mismatches: `0` / `0` / `0`
- decoy / hard-decoy false handoff: `0` / `0`
- live/cache samples and mismatches: `5000` / `0`
- artifact hygiene: `gzip_jsonl_by_default_full_logs_opt_in`

Interpretation: TG35 installs a default-off experimental runtime policy. It does not adopt the child into default/main runtime.
