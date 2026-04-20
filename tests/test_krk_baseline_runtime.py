import chess

from recon_lite_chess.krk_baseline_nodes import create_actuator_terminal


def test_actuator_runtime_penalizes_stalemate_even_when_delta_matches():
    node = create_actuator_terminal("actuator_stalemate_trap")
    node.meta.update(
        {
            "targets": ["sensor_0"],
            "goal_delta": {"sensor_0": 1.0},
            "stage": 4,
            "curriculum_label": "edge_trap_wrong_tempo",
        }
    )
    env = {
        "board": chess.Board("7k/5KR1/8/8/8/8/8/8 w - - 0 1"),
        "blackboard": {
            "feature_set": "krk_rich_v1",
            "sensor_outputs": {"sensor_0": 0.0},
            "sensor_specs": {
                "sensor_0": {
                    "feature_mask_keys": ["feature_1"],
                    "readout_type": "identity",
                    "readout_params": {},
                }
            },
        },
    }

    done, success = node.predicate(node, env)

    assert done is True
    assert success is True
    assert env["suggested_move"] != "f7f8"
    board_after = chess.Board("7k/5KR1/8/8/8/8/8/8 w - - 0 1")
    board_after.push(chess.Move.from_uci(env["suggested_move"]))
    assert not board_after.is_stalemate()
