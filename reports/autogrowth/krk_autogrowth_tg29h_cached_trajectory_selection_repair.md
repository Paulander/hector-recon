# TG29h Cached Trajectory Selection Repair

- checkpoint_pass: `True`
- interpretation: `cached_wider_audit_found_trajectory_candidate_but_repair_not_causal`
- selected repair arm: `combined_trajectory_selection_repair`
- repair_applied: `False`
- cache entries / hits / live rollouts: `60` / `16` / `16`
- audited candidates: `16`
- trajectory-positive candidates/lost: `2` / `2`
- contrast rows: `2`
- better trajectory selections after repair: `1`
- bounded episode success: `0` / `2`
- average seconds per candidate: `104.046456`

Interpretation: cache entries are memoized frozen graph responses. They are not runtime move providers.
