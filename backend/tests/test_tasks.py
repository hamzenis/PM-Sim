import pytest

from app.simulation.models import TaskPool
from app.simulation.tasks import distribute_tasks


def test_default_distribution_is_25_50_25() -> None:
    assert distribute_tasks(400) == TaskPool(easy=100, medium=200, hard=100)


def test_rounding_preserves_total_deterministically() -> None:
    assert distribute_tasks(3) == TaskPool(easy=1, medium=1, hard=1)


def test_invalid_weights_are_rejected() -> None:
    with pytest.raises(ValueError, match="total 1.0"):
        distribute_tasks(10, easy=0.5, medium=0.5, hard=0.5)
