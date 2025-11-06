import json
import os

from autorl.pbt import mutate


def test_pbt_mutation_bounds():
    space = {"eps_greedy": (0.0, 0.5), "lr": (0.01, 0.5)}
    params = {"eps_greedy": 0.2, "lr": 0.1}
    out = mutate(params, space, __import__("random").Random(0), scale=0.5)
    assert 0.0 <= out["eps_greedy"] <= 0.5
    assert 0.01 <= out["lr"] <= 0.5


def test_runner_produces_artifact(tmp_path, monkeypatch):
    # Run the runner main in-process with small budget and temp CWD
    from autorl import runner
    monkeypatch.chdir(tmp_path)
    os.makedirs(tmp_path / "reports" / "autorl_runs", exist_ok=True)
    # Simulate CLI args
    import sys
    argv_bak = sys.argv[:]
    sys.argv = ["runner.py", "--population", "4", "--generations", "2", "--train-steps", "50", "--eval-steps", "50", "--seed", "7", "--min-delta", "0.0"]
    try:
        runner.main()
    finally:
        sys.argv = argv_bak
    # Verify artifact exists
    out_dir = tmp_path / "reports" / "autorl_runs"
    files = list(out_dir.glob("run_*.json"))
    assert files, "runner should produce at least one run_*.json"
    # Validate JSON structure
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert "best" in data and "gate_decision" in data
