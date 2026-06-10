from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_historical_report_tree_is_archived() -> None:
    archive = ROOT / "archive" / "pre_autogrowth_2026_06_10"

    assert (archive / "reports" / "strategy_arbitration").is_dir()
    assert (archive / "reports" / "structural_candidates").is_dir()
    assert (archive / "legacy_report_tests").is_dir()

    assert not (ROOT / "reports" / "strategy_arbitration").exists()
    assert not (ROOT / "reports" / "structural_candidates").exists()


def test_active_agent_instructions_prioritize_autogrowth() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "KRK Autogrowth v0" in text
    assert "Do not recreate the old report-gate loop" in text
    assert "stage labels may still be used after the fact" in text.lower()


def test_active_brief_points_to_learning_loop() -> None:
    text = (ROOT / "docs" / "autogrowth" / "ACTIVE_BRIEF.md").read_text(
        encoding="utf-8"
    )

    assert "trace-derived topology-growth loop" in text
    assert "More readiness packets" in text
    assert "Stage7" in text
