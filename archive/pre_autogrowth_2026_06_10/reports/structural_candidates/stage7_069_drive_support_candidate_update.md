# Stage 7 069 Drive-Support Candidate Update

Keep the 069 drive-support adapter as a sandbox candidate. Do not promote Stage 7 yet; the remaining two families need capacity/horizon diagnosis or a narrow continuation overlay.

## Target Delta

Before: `{'mate': 16, 'max_plies': 9}`, shadows `27`
After: `{'mate': 19, 'max_plies': 6}`, shadows `21`

## Families

### state.069e81a609ed

FEN: `8/8/8/8/7R/2k5/4K3/8 w - - 2 2`
Status: `sandbox_validated_candidate`
Diagnosis: `narrow_visible_drive_support_fixes_family`
Next: `keep adapter opt-in; validate target/guardrails before promotion`
Controlled mates:
- `krk.drive_to_edge` h40 mate in 9 via `e2e3`
- `krk.drive_to_edge` h50 mate in 9 via `e2e3`

### state.2cc0b3e1033a

FEN: `8/8/R7/8/2k5/8/8/3K4 w - - 2 2`
Status: `capacity_or_horizon_gap_candidate`
Diagnosis: `no_existing_provider_or_legal_first_conversion_at_h50`
Next: `deeper horizon/tablebase-style diagnosis or narrow post-box continuation overlay; do not broad-patch`
- No controlled-provider mate at h40/h50.
- Legal-first h50: no conversion under current graph.

### state.bace6f82b671

FEN: `8/8/8/R7/4k3/8/3K4/8 w - - 2 2`
Status: `capacity_or_horizon_gap_candidate`
Diagnosis: `no_existing_provider_or_legal_first_conversion_at_h50`
Next: `deeper horizon/tablebase-style diagnosis or narrow post-box continuation overlay; do not broad-patch`
- No controlled-provider mate at h40/h50.
- Legal-first h50: no conversion under current graph.
