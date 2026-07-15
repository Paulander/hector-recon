from recon_lite import AnonymousChoiceGenome, AnonymousChoiceOption


def test_anonymous_choice_genome_emits_graph_winner() -> None:
    result = AnonymousChoiceGenome().emit((
        AnonymousChoiceOption("alpha", "actuator:a", 0.1),
        AnonymousChoiceOption("beta", "actuator:b", 0.9),
        AnonymousChoiceOption("gamma", "actuator:c", 0.4),
    ))
    assert result.actuator_identity == "actuator:b"
    assert result.option_identity == "beta"
    assert result.activation == 0.9
