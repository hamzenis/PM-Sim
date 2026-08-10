from app.simulation.models import TaskPool


def distribute_tasks(
    total: int,
    *,
    easy: float = 0.25,
    medium: float = 0.50,
    hard: float = 0.25,
) -> TaskPool:
    """Distribute anonymous tasks deterministically with largest remainders."""
    if total < 0:
        raise ValueError("total tasks cannot be negative")
    weights = (easy, medium, hard)
    if min(weights) < 0 or abs(sum(weights) - 1.0) > 1e-9:
        raise ValueError("difficulty weights must be non-negative and total 1.0")

    exact = [total * weight for weight in weights]
    counts = [int(value) for value in exact]
    remaining = total - sum(counts)
    order = sorted(range(3), key=lambda index: (-(exact[index] - counts[index]), index))
    for index in order[:remaining]:
        counts[index] += 1

    return TaskPool(easy=counts[0], medium=counts[1], hard=counts[2])
