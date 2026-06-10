# KRK Strategy Arbiter Out-of-Sample Control Labels v0

This is a bounded offline non-causal label run. It did not implement a selector, change runtime defaults, promote Stage 7, train Stage 8, or mutate topology.

## Summary

- Label count: `12`
- Wall time sec: `125.858986`
- Selected result counts: `{'mate': 11, 'max_plies': 1}`
- Forced selected-provider result counts: `{'mate': 11, 'max_plies': 1}`
- Selected result counts by stage: `{'stage5:mate': 4, 'stage6:mate': 4, 'stage4:max_plies': 1, 'stage4:mate': 3}`
- Stage 7 training rows: `0`

## Labels

- `state.3dca34326fca` stage=`stage5` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.69711173114a` stage=`stage6` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.ea634c29ece7` stage=`stage4` selected_provider=`krk.stage0_basin` selected=`max_plies` forced_selected=`max_plies`
- `state.2f5f57c82e5b` stage=`stage4` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.6ed5d7581360` stage=`stage4` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.e99b2e731810` stage=`stage4` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.7cab65617cd8` stage=`stage5` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.7b116c49a009` stage=`stage5` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.388d05197dd9` stage=`stage5` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.e65bbd1e9f0c` stage=`stage6` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.cb9f8eea01fd` stage=`stage6` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`
- `state.df10abc0731f` stage=`stage6` selected_provider=`krk.stage0_basin` selected=`mate` forced_selected=`mate`

## Recommended Next Step

`probe_out_of_sample_control_labels_before_any_selector_sandbox`
