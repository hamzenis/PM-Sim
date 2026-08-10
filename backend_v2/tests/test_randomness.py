import pytest

from app.simulation.randomness import RecordedRandomSource


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
