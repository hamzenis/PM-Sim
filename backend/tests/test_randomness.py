import pytest

from app.simulation.randomness import RecordedRandomSource, SeededRandomSource


def test_recorded_probability_values_make_outcomes_replayable() -> None:
    random = RecordedRandomSource(probabilities=[0.1, 0.9])
    assert random.probability(0.5) is True
    assert random.probability(0.5) is False


def test_recorded_poisson_values_are_returned_in_order() -> None:
    random = RecordedRandomSource(poisson_values=[3, 8])
    assert random.poisson(4.5) == 3
    assert random.poisson(4.5) == 8


def test_exhausted_recording_fails_instead_of_hiding_randomness() -> None:
    with pytest.raises(RuntimeError, match="no recorded probability value remains"):
        RecordedRandomSource().probability(0.5)


def test_same_seed_replays_the_same_mixed_random_sequence() -> None:
    first = SeededRandomSource(42)
    second = SeededRandomSource(42)
    first_values = [first.probability(0.4), first.poisson(5), first.probability(0.8)]
    second_values = [second.probability(0.4), second.poisson(5), second.probability(0.8)]
    assert first_values == second_values


def test_different_seeds_produce_different_sequences() -> None:
    first = SeededRandomSource(1)
    second = SeededRandomSource(2)
    assert [first.poisson(20) for _ in range(5)] != [second.poisson(20) for _ in range(5)]
