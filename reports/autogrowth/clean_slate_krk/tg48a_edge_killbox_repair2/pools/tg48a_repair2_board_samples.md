# TG48a Repair Board Samples

Human-readable samples from TG48a repair evaluation traces. Family/substage fields are trainer-side diagnostics only.

## M3 failures

### TG48a_M3_trial_only index 0

- FEN: `8/6R1/2K5/k7/8/8/8/8 w - - 0 1`
- Pieces: `ka5, Kc6, Rg7`
- Family: `edge_killbox_mixed`
- Selected move: `g7b7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . R .
. . K . . . . .
k . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 1

- FEN: `8/8/8/7K/8/7k/8/5R2 w - - 0 1`
- Pieces: `Rf1, kh3, Kh5`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `h5g6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . R . .
```

### TG48a_M3_trial_only index 2

- FEN: `1k6/3K4/4R3/8/8/8/8/8 w - - 0 1`
- Pieces: `Re6, Kd7, kb8`
- Family: `edge_killbox_opposed_side`
- Selected move: `e6e8`
- Success: `False`
- Failure buckets: `confinement_regression, graph_positive_false_basin, partial_only_near_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=True, rook_blunder=False, stalemate=False, confinement_regression=True`

```text
. k . . . . . .
. . . K . . . .
. . . . R . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 3

- FEN: `2k5/4K3/8/R7/8/8/8/8 w - - 0 1`
- Pieces: `Ra5, Ke7, kc8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `a5a7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . k . . . . .
. . . . K . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 4

- FEN: `1k6/3R4/K7/8/8/8/8/8 w - - 0 1`
- Pieces: `Ka6, Rd7, kb8`
- Family: `edge_killbox_mixed`
- Selected move: `d7c7`
- Success: `False`
- Failure buckets: `rook_blunder, graph_positive_false_basin, partial_only_near_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=True, rook_blunder=True, stalemate=False, confinement_regression=False`

```text
. k . . . . . .
. . . R . . . .
K . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 5

- FEN: `8/8/k7/8/1K6/8/3R4/8 w - - 0 1`
- Pieces: `Rd2, Kb4, ka6`
- Family: `edge_killbox_opposed_side`
- Selected move: `b4c3`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
. K . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 6

- FEN: `k7/2K5/1R6/8/8/8/8/8 w - - 0 1`
- Pieces: `Rb6, Kc7, ka8`
- Family: `edge_killbox_mixed`
- Selected move: `b6b7`
- Success: `False`
- Failure buckets: `stalemate`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=False, partial_only_near_basin=False, rook_blunder=False, stalemate=True, confinement_regression=False`

```text
k . . . . . . .
. . K . . . . .
. R . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 7

- FEN: `8/8/1R6/8/K7/8/k7/8 w - - 0 1`
- Pieces: `ka2, Ka4, Rb6`
- Family: `edge_killbox_opposed_side`
- Selected move: `a4b4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. R . . . . . .
. . . . . . . .
K . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 8

- FEN: `2K1k3/8/8/8/8/6R1/8/8 w - - 0 1`
- Pieces: `Rg3, Kc8, ke8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `c8b7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . K . k . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . R .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 9

- FEN: `2R5/8/8/8/6K1/8/7k/8 w - - 0 1`
- Pieces: `kh2, Kg4, Rc8`
- Family: `edge_killbox_opposed_side`
- Selected move: `g4f5`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . R . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . K .
. . . . . . . .
. . . . . . . k
. . . . . . . .
```

### TG48a_M3_trial_only index 10

- FEN: `4K1k1/8/5R2/8/8/8/8/8 w - - 0 1`
- Pieces: `Rf6, Ke8, kg8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `f6f7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . K . k .
. . . . . . . .
. . . . . R . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 11

- FEN: `2K1k3/8/8/8/8/R7/8/8 w - - 0 1`
- Pieces: `Ra3, Kc8, ke8`
- Family: `edge_killbox_mixed`
- Selected move: `c8b7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . K . k . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 12

- FEN: `1k1K4/8/4R3/8/8/8/8/8 w - - 0 1`
- Pieces: `Re6, kb8, Kd8`
- Family: `edge_killbox_opposed_side`
- Selected move: `d8e7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. k . K . . . .
. . . . . . . .
. . . . R . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 13

- FEN: `5R2/7K/8/7k/8/8/8/8 w - - 0 1`
- Pieces: `kh5, Kh7, Rf8`
- Family: `edge_killbox_opposed_side`
- Selected move: `h7g8`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . R . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 14

- FEN: `8/8/8/8/K7/8/k7/3R4 w - - 0 1`
- Pieces: `Rd1, ka2, Ka4`
- Family: `edge_killbox_mixed`
- Selected move: `d1a1`
- Success: `False`
- Failure buckets: `rook_blunder, confinement_regression, graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=True, stalemate=False, confinement_regression=True`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
K . . . . . . .
. . . . . . . .
k . . . . . . .
. . . R . . . .
```

### TG48a_M3_trial_only index 15

- FEN: `k7/2K5/8/8/8/8/3R4/8 w - - 0 1`
- Pieces: `Rd2, Kc7, ka8`
- Family: `edge_killbox_opposed_side`
- Selected move: `c7d6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
k . . . . . . .
. . K . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 16

- FEN: `8/8/8/8/8/R7/4K3/2k5 w - - 0 1`
- Pieces: `kc1, Ke2, Ra3`
- Family: `edge_killbox_mixed`
- Selected move: `e2f3`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . K . . .
. . k . . . . .
```

### TG48a_M3_trial_only index 17

- FEN: `8/8/2K5/k7/3R4/8/8/8 w - - 0 1`
- Pieces: `Rd4, ka5, Kc6`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `d4b4`
- Success: `False`
- Failure buckets: `rook_blunder, graph_positive_false_basin, partial_only_near_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=True, rook_blunder=True, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . K . . . . .
k . . . . . . .
. . . R . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 18

- FEN: `8/8/8/8/R7/8/1K6/3k4 w - - 0 1`
- Pieces: `kd1, Kb2, Ra4`
- Family: `edge_killbox_opposed_side`
- Selected move: `a4e4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. K . . . . . .
. . . k . . . .
```

### TG48a_M3_trial_only index 19

- FEN: `8/6K1/3R4/7k/8/8/8/8 w - - 0 1`
- Pieces: `kh5, Rd6, Kg7`
- Family: `edge_killbox_mixed`
- Selected move: `d6d4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . K .
. . . R . . . .
. . . . . . . k
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

## M4 failures

### TG48a_M4_consolidated_only index 0

- FEN: `8/6R1/2K5/k7/8/8/8/8 w - - 0 1`
- Pieces: `ka5, Kc6, Rg7`
- Family: `edge_killbox_mixed`
- Selected move: `g7b7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . R .
. . K . . . . .
k . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 1

- FEN: `8/8/8/7K/8/7k/8/5R2 w - - 0 1`
- Pieces: `Rf1, kh3, Kh5`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `f1g1`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . R . .
```

### TG48a_M4_consolidated_only index 2

- FEN: `1k6/3K4/4R3/8/8/8/8/8 w - - 0 1`
- Pieces: `Re6, Kd7, kb8`
- Family: `edge_killbox_opposed_side`
- Selected move: `e6e7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. k . . . . . .
. . . K . . . .
. . . . R . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 3

- FEN: `2k5/4K3/8/R7/8/8/8/8 w - - 0 1`
- Pieces: `Ra5, Ke7, kc8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `a5b5`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . k . . . . .
. . . . K . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 4

- FEN: `1k6/3R4/K7/8/8/8/8/8 w - - 0 1`
- Pieces: `Ka6, Rd7, kb8`
- Family: `edge_killbox_mixed`
- Selected move: `a6b5`
- Success: `False`
- Failure buckets: `graph_positive_false_basin, partial_only_near_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=True, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. k . . . . . .
. . . R . . . .
K . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 5

- FEN: `8/8/k7/8/1K6/8/3R4/8 w - - 0 1`
- Pieces: `Rd2, Kb4, ka6`
- Family: `edge_killbox_opposed_side`
- Selected move: `d2d7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
. K . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 6

- FEN: `k7/2K5/1R6/8/8/8/8/8 w - - 0 1`
- Pieces: `Rb6, Kc7, ka8`
- Family: `edge_killbox_mixed`
- Selected move: `c7d6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
k . . . . . . .
. . K . . . . .
. R . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 7

- FEN: `8/8/1R6/8/K7/8/k7/8 w - - 0 1`
- Pieces: `ka2, Ka4, Rb6`
- Family: `edge_killbox_opposed_side`
- Selected move: `b6b3`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. R . . . . . .
. . . . . . . .
K . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 8

- FEN: `2K1k3/8/8/8/8/6R1/8/8 w - - 0 1`
- Pieces: `Rg3, Kc8, ke8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `g3g7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . K . k . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . R .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 9

- FEN: `2R5/8/8/8/6K1/8/7k/8 w - - 0 1`
- Pieces: `kh2, Kg4, Rc8`
- Family: `edge_killbox_opposed_side`
- Selected move: `c8f8`
- Success: `False`
- Failure buckets: `graph_positive_false_basin, partial_only_near_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=True, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . R . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . K .
. . . . . . . .
. . . . . . . k
. . . . . . . .
```

### TG48a_M4_consolidated_only index 10

- FEN: `4K1k1/8/5R2/8/8/8/8/8 w - - 0 1`
- Pieces: `Rf6, Ke8, kg8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `f6f7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . K . k .
. . . . . . . .
. . . . . R . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 11

- FEN: `2K1k3/8/8/8/8/R7/8/8 w - - 0 1`
- Pieces: `Ra3, Kc8, ke8`
- Family: `edge_killbox_mixed`
- Selected move: `a3a7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . K . k . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 12

- FEN: `1k1K4/8/4R3/8/8/8/8/8 w - - 0 1`
- Pieces: `Re6, kb8, Kd8`
- Family: `edge_killbox_opposed_side`
- Selected move: `e6e7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. k . K . . . .
. . . . . . . .
. . . . R . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 13

- FEN: `5R2/7K/8/7k/8/8/8/8 w - - 0 1`
- Pieces: `kh5, Kh7, Rf8`
- Family: `edge_killbox_opposed_side`
- Selected move: `f8g8`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . R . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 14

- FEN: `8/8/8/8/K7/8/k7/3R4 w - - 0 1`
- Pieces: `Rd1, ka2, Ka4`
- Family: `edge_killbox_mixed`
- Selected move: `a4b4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
K . . . . . . .
. . . . . . . .
k . . . . . . .
. . . R . . . .
```

### TG48a_M4_consolidated_only index 16

- FEN: `8/8/8/8/8/R7/4K3/2k5 w - - 0 1`
- Pieces: `kc1, Ke2, Ra3`
- Family: `edge_killbox_mixed`
- Selected move: `a3b3`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . K . . .
. . k . . . . .
```

### TG48a_M4_consolidated_only index 17

- FEN: `8/8/2K5/k7/3R4/8/8/8 w - - 0 1`
- Pieces: `Rd4, ka5, Kc6`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `c6b7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . K . . . . .
k . . . . . . .
. . . R . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 18

- FEN: `8/8/8/8/R7/8/1K6/3k4 w - - 0 1`
- Pieces: `kd1, Kb2, Ra4`
- Family: `edge_killbox_opposed_side`
- Selected move: `a4e4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. K . . . . . .
. . . k . . . .
```

### TG48a_M4_consolidated_only index 19

- FEN: `8/6K1/3R4/7k/8/8/8/8 w - - 0 1`
- Pieces: `kh5, Rd6, Kg7`
- Family: `edge_killbox_mixed`
- Selected move: `d6g6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . K .
. . . R . . . .
. . . . . . . k
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M4_consolidated_only index 20

- FEN: `1k6/3K4/7R/8/8/8/8/8 w - - 0 1`
- Pieces: `Rh6, Kd7, kb8`
- Family: `edge_killbox_opposed_side`
- Selected move: `h6a6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. k . . . . . .
. . . K . . . .
. . . . . . . R
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

## Hard-decoy false handoffs

No rows in this category.

## Graph-positive false basins

### parent_TG46d_only index 1

- FEN: `8/8/8/7K/8/7k/8/5R2 w - - 0 1`
- Pieces: `Rf1, kh3, Kh5`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `f1f2`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . R . .
```

### parent_TG46d_only index 2

- FEN: `1k6/3K4/4R3/8/8/8/8/8 w - - 0 1`
- Pieces: `Re6, Kd7, kb8`
- Family: `edge_killbox_opposed_side`
- Selected move: `e6a6`
- Success: `False`
- Failure buckets: `confinement_regression, graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=True`

```text
. k . . . . . .
. . . K . . . .
. . . . R . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 3

- FEN: `2k5/4K3/8/R7/8/8/8/8 w - - 0 1`
- Pieces: `Ra5, Ke7, kc8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `a5a7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . k . . . . .
. . . . K . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 4

- FEN: `1k6/3R4/K7/8/8/8/8/8 w - - 0 1`
- Pieces: `Ka6, Rd7, kb8`
- Family: `edge_killbox_mixed`
- Selected move: `d7a7`
- Success: `False`
- Failure buckets: `confinement_regression, graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=True`

```text
. k . . . . . .
. . . R . . . .
K . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 5

- FEN: `8/8/k7/8/1K6/8/3R4/8 w - - 0 1`
- Pieces: `Rd2, Kb4, ka6`
- Family: `edge_killbox_opposed_side`
- Selected move: `d2d7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
. K . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
```

### parent_TG46d_only index 7

- FEN: `8/8/1R6/8/K7/8/k7/8 w - - 0 1`
- Pieces: `ka2, Ka4, Rb6`
- Family: `edge_killbox_opposed_side`
- Selected move: `b6b3`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. R . . . . . .
. . . . . . . .
K . . . . . . .
. . . . . . . .
k . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 8

- FEN: `2K1k3/8/8/8/8/6R1/8/8 w - - 0 1`
- Pieces: `Rg3, Kc8, ke8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `g3g7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . K . k . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . R .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 9

- FEN: `2R5/8/8/8/6K1/8/7k/8 w - - 0 1`
- Pieces: `kh2, Kg4, Rc8`
- Family: `edge_killbox_opposed_side`
- Selected move: `c8c1`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . R . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . K .
. . . . . . . .
. . . . . . . k
. . . . . . . .
```

### parent_TG46d_only index 10

- FEN: `4K1k1/8/5R2/8/8/8/8/8 w - - 0 1`
- Pieces: `Rf6, Ke8, kg8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `f6h6`
- Success: `False`
- Failure buckets: `confinement_regression, graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=True`

```text
. . . . K . k .
. . . . . . . .
. . . . . R . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 11

- FEN: `2K1k3/8/8/8/8/R7/8/8 w - - 0 1`
- Pieces: `Ra3, Kc8, ke8`
- Family: `edge_killbox_mixed`
- Selected move: `a3a7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . K . k . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 12

- FEN: `1k1K4/8/4R3/8/8/8/8/8 w - - 0 1`
- Pieces: `Re6, kb8, Kd8`
- Family: `edge_killbox_opposed_side`
- Selected move: `e6a6`
- Success: `False`
- Failure buckets: `confinement_regression, graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=True`

```text
. k . K . . . .
. . . . . . . .
. . . . R . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 13

- FEN: `5R2/7K/8/7k/8/8/8/8 w - - 0 1`
- Pieces: `kh5, Kh7, Rf8`
- Family: `edge_killbox_opposed_side`
- Selected move: `f8f4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . R . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 14

- FEN: `8/8/8/8/K7/8/k7/3R4 w - - 0 1`
- Pieces: `Rd1, ka2, Ka4`
- Family: `edge_killbox_mixed`
- Selected move: `a4b4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
K . . . . . . .
. . . . . . . .
k . . . . . . .
. . . R . . . .
```

### parent_TG46d_only index 16

- FEN: `8/8/8/8/8/R7/4K3/2k5 w - - 0 1`
- Pieces: `kc1, Ke2, Ra3`
- Family: `edge_killbox_mixed`
- Selected move: `a3b3`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . K . . .
. . k . . . . .
```

### parent_TG46d_only index 18

- FEN: `8/8/8/8/R7/8/1K6/3k4 w - - 0 1`
- Pieces: `kd1, Kb2, Ra4`
- Family: `edge_killbox_opposed_side`
- Selected move: `a4e4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
R . . . . . . .
. . . . . . . .
. K . . . . . .
. . . k . . . .
```

### parent_TG46d_only index 19

- FEN: `8/6K1/3R4/7k/8/8/8/8 w - - 0 1`
- Pieces: `kh5, Rd6, Kg7`
- Family: `edge_killbox_mixed`
- Selected move: `d6g6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . K .
. . . R . . . .
. . . . . . . k
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 20

- FEN: `1k6/3K4/7R/8/8/8/8/8 w - - 0 1`
- Pieces: `Rh6, Kd7, kb8`
- Family: `edge_killbox_opposed_side`
- Selected move: `h6a6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. k . . . . . .
. . . K . . . .
. . . . . . . R
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### parent_TG46d_only index 21

- FEN: `4R3/7k/8/7K/8/8/8/8 w - - 0 1`
- Pieces: `Kh5, kh7, Re8`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `h5g5`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . R . . .
. . . . . . . k
. . . . . . . .
. . . . . . . K
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 0

- FEN: `8/6R1/2K5/k7/8/8/8/8 w - - 0 1`
- Pieces: `ka5, Kc6, Rg7`
- Family: `edge_killbox_mixed`
- Selected move: `g7b7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . R .
. . K . . . . .
k . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 1

- FEN: `8/8/8/7K/8/7k/8/5R2 w - - 0 1`
- Pieces: `Rf1, kh3, Kh5`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `h5g6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . K
. . . . . . . .
. . . . . . . k
. . . . . . . .
. . . . . R . .
```

## Parent succeeds but M3 worsens

### TG48a_M3_trial_only index 0

- FEN: `8/6R1/2K5/k7/8/8/8/8 w - - 0 1`
- Pieces: `ka5, Kc6, Rg7`
- Family: `edge_killbox_mixed`
- Selected move: `g7b7`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=True, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . R .
. . K . . . . .
k . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 15

- FEN: `k7/2K5/8/8/8/8/3R4/8 w - - 0 1`
- Pieces: `Rd2, Kc7, ka8`
- Family: `edge_killbox_opposed_side`
- Selected move: `c7d6`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
k . . . . . . .
. . K . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 17

- FEN: `8/8/2K5/k7/3R4/8/8/8 w - - 0 1`
- Pieces: `Rd4, ka5, Kc6`
- Family: `edge_killbox_same_side_rook_danger`
- Selected move: `d4b4`
- Success: `False`
- Failure buckets: `rook_blunder, graph_positive_false_basin, partial_only_near_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=True, rook_blunder=True, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . K . . . . .
k . . . . . . .
. . . R . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
```

### TG48a_M3_trial_only index 23

- FEN: `8/8/3R4/8/8/6K1/8/7k w - - 0 1`
- Pieces: `kh1, Kg3, Rd6`
- Family: `edge_killbox_opposed_side`
- Selected move: `g3f4`
- Success: `False`
- Failure buckets: `graph_positive_false_basin`
- Metrics: `validated_entry=False, validated_mate1_entry=False, validated_mate2_entry=False, mate_conversion_within_horizon=False, graded_positive_progress=False, graph_positive_false_basin=True, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
. . . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
. . . . . . . .
. . . . . . K .
. . . . . . . .
. . . . . . . k
```

## M4 succeeds with active veto terminal

### TG48a_M4_consolidated_only index 15

- FEN: `k7/2K5/8/8/8/8/3R4/8 w - - 0 1`
- Pieces: `Rd2, Kc7, ka8`
- Family: `edge_killbox_opposed_side`
- Selected move: `d2d5`
- Success: `True`
- Failure buckets: `none`
- Metrics: `validated_entry=True, validated_mate1_entry=True, validated_mate2_entry=True, mate_conversion_within_horizon=True, graded_positive_progress=True, graph_positive_false_basin=False, partial_only_near_basin=False, rook_blunder=False, stalemate=False, confinement_regression=False`

```text
k . . . . . . .
. . K . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . R . . . .
. . . . . . . .
```
