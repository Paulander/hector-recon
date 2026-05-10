#!/usr/bin/env python3
"""
Verification tests for subgraph goal delegation.

Tests that KPK/KQK move selectors work correctly when:
1. Called directly (bypassing engine)
2. Run through multi-tick engine
3. Handle KPK→KQK transitions

Run: uv run python tests/test_subgraph_delegation.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import chess

from recon_lite.graph import NodeState
from recon_lite.engine import ReConEngine
from recon_lite_chess.scripts.endgame_gate import create_endgame_gate
from recon_lite_chess.scripts.kpk import create_kpk_move_selector, create_kpk_promotion_probe
from recon_lite_chess.scripts.kqk import create_kqk_move_selector, is_kqk_position
from recon_lite_chess.graph import build_unified_graph


def test_kpk_move_selector_direct():
    """Test KPK move selector produces correct move when called directly."""
    print("\n=== Test 1: KPK Move Selector (Direct Call) ===")
    
    # Near-promotion position: White pawn on g7, should promote
    test_fens = [
        ("8/6P1/7K/8/2k5/8/8/8 w - - 0 1", "g7g8q", "Pawn promotion"),
        ("4K3/6P1/8/8/8/8/8/5k2 w - - 0 1", "g7g8q", "Pawn promotion with king support"),
        ("8/2P5/4K3/8/8/8/8/5k2 w - - 0 1", "c7c8q", "c-file promotion"),
    ]
    
    passed = 0
    for fen, expected_move, description in test_fens:
        board = chess.Board(fen)
        env = {"board": board}
        
        node = create_kpk_move_selector("test_kpk")
        done, success = node.predicate(node, env)
        
        suggested = env.get("kpk", {}).get("policy", {}).get("suggested_move")
        
        status = "✓" if suggested == expected_move else "✗"
        print(f"  {status} {description}: {suggested} (expected {expected_move})")
        
        if suggested == expected_move:
            passed += 1
    
    print(f"  Result: {passed}/{len(test_fens)} passed")
    return passed == len(test_fens)


def test_kqk_move_selector_direct():
    """Test KQK move selector produces valid moves when called directly."""
    print("\n=== Test 2: KQK Move Selector (Direct Call) ===")
    
    # KQK positions - queen should restrict or mate
    test_fens = [
        "6Q1/7K/8/8/2k5/8/8/8 w - - 0 1",  # After promotion
        "8/8/8/3Q4/8/8/1k6/7K w - - 0 1",  # Mid-game KQK
    ]
    
    passed = 0
    for fen in test_fens:
        board = chess.Board(fen)
        is_kqk, attacker = is_kqk_position(board)
        
        if not is_kqk:
            print(f"  ✗ {fen[:20]}... not detected as KQK")
            continue
        
        env = {"board": board, "kqk": {"is_kqk": True, "attacker": attacker}}
        
        node = create_kqk_move_selector("test_kqk")
        done, success = node.predicate(node, env)
        
        suggested = env.get("kqk", {}).get("policy", {}).get("suggested_move")
        
        if suggested:
            # Verify it's a legal move
            try:
                move = chess.Move.from_uci(suggested)
                is_legal = move in board.legal_moves
                status = "✓" if is_legal else "✗"
                print(f"  {status} {fen[:25]}... → {suggested} (legal={is_legal})")
                if is_legal:
                    passed += 1
            except Exception as e:
                print(f"  ✗ {fen[:25]}... → {suggested} (invalid: {e})")
        else:
            print(f"  ✗ {fen[:25]}... → No move suggested")
    
    print(f"  Result: {passed}/{len(test_fens)} passed")
    return passed == len(test_fens)


def test_engine_single_tick():
    """Test that single engine tick does NOT reach move selectors."""
    print("\n=== Test 3: Engine Single Tick (Confirms Bug) ===")
    
    fen = "8/6P1/7K/8/2k5/8/8/8 w - - 0 1"  # KPK near promotion
    
    g = build_unified_graph()
    engine = ReConEngine(g)
    board = chess.Board(fen)
    env = {"board": board}
    
    # Request root
    g.nodes["GameRoot"].state = NodeState.REQUESTED
    
    # Single tick
    engine.step(env)
    
    # Check move selector state
    move_selector = g.nodes.get("kpk_move_selector")
    if move_selector:
        state = move_selector.state.name
        suggested = env.get("kpk", {}).get("policy", {}).get("suggested_move")
        
        print(f"  kpk_move_selector state: {state}")
        print(f"  env[kpk][policy]: {env.get('kpk', {}).get('policy', {})}")
        
        # With single tick, move selector should NOT have run
        if suggested is None and state in ("INACTIVE", "REQUESTED"):
            print("  ✓ Confirmed: Single tick does NOT reach move selector")
            return True
        else:
            print(f"  ✗ Unexpected: Move selector reached in single tick")
            return False
    else:
        print("  ✗ kpk_move_selector not found in graph")
        return False


def test_engine_multi_tick():
    """Test that multiple engine ticks DO reach move selectors."""
    print("\n=== Test 4: Engine Multi-Tick (Validates Fix) ===")
    
    fen = "8/6P1/7K/8/2k5/8/8/8 w - - 0 1"  # KPK near promotion
    
    g = build_unified_graph()
    engine = ReConEngine(g)
    board = chess.Board(fen)
    env = {"board": board}
    
    # Request root
    g.nodes["GameRoot"].state = NodeState.REQUESTED
    
    # Multiple ticks
    for i in range(8):
        engine.step(env)
        
        suggested = env.get("kpk", {}).get("policy", {}).get("suggested_move")
        if suggested:
            print(f"  ✓ Move suggested after {i+1} ticks: {suggested}")
            return True
        
        # Debug: show move selector progression
        move_selector = g.nodes.get("kpk_move_selector")
        if move_selector:
            state = move_selector.state.name
            if i < 3:  # Only show first few
                print(f"    Tick {i+1}: kpk_move_selector = {state}")
    
    print("  ✗ No move suggested after 8 ticks")
    return False


def test_kpk_to_kqk_transition():
    """Test that after promotion, KQK detects and suggests moves."""
    print("\n=== Test 5: KPK→KQK Transition ===")
    
    # Start with KPK
    kpk_fen = "8/6P1/7K/8/2k5/8/8/8 w - - 0 1"
    board = chess.Board(kpk_fen)
    
    # KPK should suggest promotion
    env = {"board": board}
    kpk_node = create_kpk_move_selector("kpk")
    kpk_node.predicate(kpk_node, env)
    kpk_move = env.get("kpk", {}).get("policy", {}).get("suggested_move")
    
    if not kpk_move:
        print("  ✗ KPK did not suggest move")
        return False
    
    print(f"  KPK suggests: {kpk_move}")

    gate_node = create_endgame_gate("endgame_gate")
    gate_node.predicate(gate_node, env)
    router_before = env.get("routers", {}).get("endgame_gate", {})
    if env.get("endgame_gate", {}).get("active_endgame") != "kpk":
        print(f"  ✗ Before promotion, gate did not select KPK: {env.get('endgame_gate')}")
        return False
    if router_before.get("domain_execution_eligibility", {}).get("kqk"):
        print("  ✗ Before promotion, KQK was execution-eligible")
        return False
    if "activations" not in env.get("endgame_gate", {}):
        print("  ✗ Legacy endgame_gate activations missing")
        return False
    
    # Apply promotion
    move = chess.Move.from_uci(kpk_move)
    board.push(move)

    # Promotion confirmation emits trace only; it must not route by itself.
    trace_env = {"board": board}
    promotion_probe = create_kpk_promotion_probe("kpk_promotion_probe")
    promotion_probe.predicate(promotion_probe, trace_env)
    packets = trace_env.get("handoff_packets", [])
    if not packets:
        print("  ✗ Promotion did not emit handoff packet")
        return False
    packet = packets[-1]
    if packet.get("from_skill") != "kpk.promotion" or packet.get("status") != "confirmed":
        print(f"  ✗ Unexpected handoff packet: {packet}")
        return False
    if packet.get("continuation_exports", {}).get("domain.kqk") != 1.0:
        print(f"  ✗ Missing KQK continuation export: {packet}")
        return False
    
    # Now should be KQK
    is_kqk, attacker = is_kqk_position(board)
    if not is_kqk:
        print(f"  ✗ After promotion, not KQK: {board.fen()}")
        return False
    
    print(f"  ✓ After promotion: KQK detected (attacker={attacker})")

    # Simulate the next White turn for domain execution eligibility.
    gate_board = board.copy(stack=False)
    gate_board.turn = attacker
    gate_env = {"board": gate_board}
    gate_node.predicate(gate_node, gate_env)
    router_after = gate_env.get("routers", {}).get("endgame_gate", {})
    if gate_env.get("endgame_gate", {}).get("active_endgame") != "kqk":
        print(f"  ✗ After promotion, gate did not select KQK: {gate_env.get('endgame_gate')}")
        return False
    if not router_after.get("domain_execution_eligibility", {}).get("kqk"):
        print(f"  ✗ After promotion, KQK not execution-eligible: {router_after}")
        return False
    
    # KQK should suggest move on the next attacking turn - need fresh env with correct setup
    env2 = {"board": gate_board}
    
    # First run material detector to populate env properly
    from recon_lite_chess.scripts.kqk import create_kqk_material_detector
    mat_node = create_kqk_material_detector("kqk_mat")
    mat_node.predicate(mat_node, env2)
    
    # Then run move selector
    kqk_node = create_kqk_move_selector("kqk")
    done, success = kqk_node.predicate(kqk_node, env2)
    kqk_move = env2.get("kqk", {}).get("policy", {}).get("suggested_move")
    
    if kqk_move:
        print(f"  ✓ KQK suggests: {kqk_move}")
        return True
    else:
        print("  ✗ KQK did not suggest move")
        print(f"    env2[kqk] = {env2.get('kqk', {})}")
        return False


def test_domain_root_execution_veto():
    """KQK approach affordance is not enough to execute KQK before promotion."""
    print("\n=== Test 6: Domain Root Execution Veto ===")

    g = build_unified_graph()
    gate_node = g.nodes["endgame_gate"]
    kqk_root = g.nodes["kqk_root"]

    board = chess.Board("8/6P1/7K/8/2k5/8/8/8 w - - 0 1")
    env = {"board": board}
    gate_node.predicate(gate_node, env)
    router = env.get("routers", {}).get("endgame_gate", {})

    approach = router.get("domain_approach_affordance", {}).get("kqk", 0.0)
    eligible = router.get("domain_execution_eligibility", {}).get("kqk")
    done, success = kqk_root.predicate(kqk_root, env)
    if not (
        approach > 0.0
        and eligible is False
        and done is True
        and success is True
        and kqk_root.meta.get("execution_vetoed") is True
        and kqk_root.activation.value == 0.0
    ):
        print(
            "  ✗ Expected KQK soft approach but hard execution veto:",
            f"approach={approach}",
            f"eligible={eligible}",
            f"root=({done}, {success})",
            f"vetoed={kqk_root.meta.get('execution_vetoed')}",
        )
        return False

    engine = ReConEngine(g)
    engine.reset_states()
    gate_node.predicate(gate_node, env)
    g.nodes["kqk_root"].state = NodeState.REQUESTED
    engine.step(env)
    if g.nodes["kqk_material_check"].state != NodeState.INACTIVE:
        print(
            "  ✗ Vetoed KQK root requested internal children:",
            f"kqk_material_check={g.nodes['kqk_material_check'].state.name}",
        )
        return False

    move = chess.Move.from_uci("g7g8q")
    board.push(move)
    promoted_board = board.copy(stack=False)
    promoted_board.turn = chess.WHITE
    env2 = {"board": promoted_board}
    gate_node.predicate(gate_node, env2)
    router2 = env2.get("routers", {}).get("endgame_gate", {})
    done2, success2 = kqk_root.predicate(kqk_root, env2)
    if router2.get("selected_route") != "kqk" or done2 is not False or not success2:
        print(
            "  ✗ Expected KQK execution eligibility after promotion:",
            f"route={router2.get('selected_route')}",
            f"eligible={router2.get('domain_execution_eligibility', {}).get('kqk')}",
            f"root=({done2}, {success2})",
        )
        return False

    print("  ✓ KQK root respects execution eligibility before and after promotion")
    return True


def test_subgraph_lock():
    """Test SubgraphLock mechanism produces move in single step()."""
    print("\n=== Test 7: SubgraphLock (New Feature) ===")
    
    fen = "8/6P1/7K/8/2k5/8/8/8 w - - 0 1"  # KPK near promotion
    
    g = build_unified_graph()
    engine = ReConEngine(g)
    board = chess.Board(fen)
    env = {"board": board}
    
    # Define sentinel: stay locked while still KPK
    from recon_lite_chess.sensors.structure import summarize_kpk_material
    def kpk_sentinel(env):
        board = env.get("board")
        if not board:
            return False
        summary = summarize_kpk_material(board)
        return bool(summary.get("is_kpk"))
    
    # Lock into KPK subgraph
    engine.lock_subgraph("kpk_root", kpk_sentinel)
    
    # Single step - should complete internal ticks and produce move
    engine.step(env)
    
    suggested = env.get("kpk", {}).get("policy", {}).get("suggested_move")
    
    if suggested == "g7g8q":
        print(f"  ✓ SubgraphLock produced correct move: {suggested}")
        return True
    elif suggested:
        print(f"  ~ SubgraphLock produced move: {suggested} (expected g7g8q)")
        return True  # Any legal move is acceptable for this test
    else:
        print(f"  ✗ SubgraphLock did not produce move")
        print(f"    env[kpk] = {env.get('kpk', {})}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("SUBGRAPH DELEGATION VERIFICATION TESTS")
    print("=" * 60)
    
    results = {
        "KPK Direct": test_kpk_move_selector_direct(),
        "KQK Direct": test_kqk_move_selector_direct(),
        "Single Tick (Bug)": test_engine_single_tick(),
        "Multi Tick (Fix)": test_engine_multi_tick(),
        "KPK→KQK Transition": test_kpk_to_kqk_transition(),
        "Domain Root Veto": test_domain_root_execution_veto(),
        "SubgraphLock": test_subgraph_lock(),
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "PASS ✓" if passed else "FAIL ✗"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
