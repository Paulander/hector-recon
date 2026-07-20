from __future__ import annotations

from recon_lite_chess.autogrowth.native_terminal_trace_historical_regression import (
    ARM_NAMES,
    build_predata_manifest,
    exact_sign_test,
    holm_two,
    organism_metrics,
)


def _row(outcome: bool, state: str) -> dict[str, object]:
    return {
        "actual_completion": outcome,
        "classification": {"state": state},
    }


def test_metrics_are_deployable_only_when_false_positive_free() -> None:
    safe = organism_metrics([
        *[_row(True, "available") for _ in range(3)],
        *[_row(False, "unknown") for _ in range(2)],
    ])
    unsafe = organism_metrics([
        _row(True, "available"),
        _row(False, "available"),
    ])
    assert safe["tp"] == 3 and safe["fp"] == 0 and safe["deployable_tp"] == 3
    assert unsafe["tp"] == 1 and unsafe["fp"] == 1
    assert unsafe["deployable_tp"] == 0


def test_exact_paired_sign_and_holm_are_frozen() -> None:
    left = [2] * 28 + [0] * 4
    right = [0] * 32
    first = {"control": ARM_NAMES[1], **exact_sign_test(left, right)}
    second = {"control": ARM_NAMES[2], **exact_sign_test(left, right)}
    rows = holm_two(first, second)
    assert first["wins"] == 28 and first["losses"] == 0 and first["ties"] == 4
    assert all(row["holm_pass_0_05"] for row in rows)


def test_predata_manifest_does_not_open_regression(monkeypatch, tmp_path) -> None:
    import recon_lite_chess.autogrowth.native_terminal_trace_historical_regression as module

    monkeypatch.setattr(
        module,
        "_load_and_verify_pool_source",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("pre-data freeze opened regression")
        ),
    )
    monkeypatch.setattr(module, "FREEZE_MANIFEST", str(tmp_path / "freeze.json"))
    manifest = build_predata_manifest()
    assert manifest["regression_opened"] is False
    assert len(manifest["organisms"]) == 96
    assert manifest["regression_commitments"]["row_order"] == (
        "24899b4a004cf68d5e4a4105ea479496d26fea884d447a105e339cf783bffee4"
    )
