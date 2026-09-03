from recon_lite import AnonymousChoiceGenome, AnonymousChoiceOption
import pytest


def test_anonymous_choice_genome_emits_graph_winner() -> None:
    result = AnonymousChoiceGenome().emit((
        AnonymousChoiceOption("alpha", "actuator:a", 0.1),
        AnonymousChoiceOption("beta", "actuator:b", 0.9),
        AnonymousChoiceOption("gamma", "actuator:c", 0.4),
    ))
    assert result.actuator_identity == "actuator:b"
    assert result.option_identity == "beta"
    assert result.activation == 0.9


def test_evidence_terminal_breaks_equal_upside_independently_of_option_order():
    known = AnonymousChoiceOption("known", "experienced", 1.0, tie_break_measurements=(1.0, 3.0))
    novel = AnonymousChoiceOption("novel", "untried", 1.0, tie_break_measurements=(1.0, 0.0))
    for options in ((known, novel), (novel, known)):
        assert AnonymousChoiceGenome().emit(options).actuator_identity == "experienced"
    weaker = AnonymousChoiceOption("weaker", "old", 0.9, tie_break_measurements=(1.0, 1000.0))
    assert AnonymousChoiceGenome().emit((weaker, novel)).actuator_identity == "untried"
    contradicted = AnonymousChoiceOption("contradicted", "old", 1.0,
        tie_break_measurements=(0.9, 1000.0))
    assert AnonymousChoiceGenome().emit((contradicted, novel)).actuator_identity == "untried"


@pytest.mark.parametrize("evidence", [float("nan"), float("inf"), float("-inf")])
def test_bad_internal_evidence_is_rejected(evidence):
    with pytest.raises(ValueError):
        AnonymousChoiceGenome().emit((AnonymousChoiceOption("a", "a", 1.0,
            tie_break_measurements=(evidence,)),))
