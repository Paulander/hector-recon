# TG29n S1 Full-Reply Handoff Validation

- checkpoint_pass: `True`
- interpretation: `s1_full_reply_validation_pass`
- selected arm: `strict_all_reply_priority`
- S1 slices train/heldout/near_miss: `4` / `4` / `4`
- heldout selected all-reply: `1` / `4`
- selected one-reply false positives: `0`
- all/partial/one-reply positives: `2` / `15` / `2`
- one-reply later failed: `15`
- max2 success: `2` / `2`
- max3 success: `2` / `2`
- safety rook/illegal/stalemate: `0` / `0` / `0`
- ablation causal: `True`

Interpretation: TG29n validates post-trajectory S1 second-move evidence. It does not broaden KRK or add a new learner mechanism.
