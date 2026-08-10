from app.batch.runner import run_batch


def test_batch_uses_reproducible_consecutive_seeds() -> None:
    runs = run_batch(lambda seed: seed * 2, repetitions=3, initial_seed=10)
    assert [(run.seed, run.result) for run in runs] == [(10, 20), (11, 22), (12, 24)]
