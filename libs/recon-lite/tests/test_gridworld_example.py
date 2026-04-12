from recon_lite import ActivationMode
from recon_lite.examples.gridworld import main, run_simulation


def test_gridworld_runs_discrete_and_continuous():
    discrete = run_simulation(mode=ActivationMode.DISCRETE, steps=10)
    continuous = run_simulation(mode=ActivationMode.CONTINUOUS, steps=10, microticks=3)

    assert discrete[-1].endswith("bindings=1")
    assert "agent=(4, 4)" in discrete[-1]
    assert "mode=continuous" in continuous[0]


def test_gridworld_cli_smoke(capsys):
    assert main(["--mode", "discrete", "--steps", "2"]) == 0
    captured = capsys.readouterr()
    assert "mode=discrete" in captured.out
