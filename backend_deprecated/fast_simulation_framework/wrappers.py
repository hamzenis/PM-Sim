from __future__ import annotations
from typing import List, Set
from app.cache.scenario import CachedScenario
from app.models.task import CachedTasks, Task
from app.models.team import Member
from app.models.user_scenario import UserScenario

# This prevents circular imports, but allows type hinting.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.cache.scenario import CachedScenario


class FastTasks(CachedTasks):
    """
    A lightweight version of CachedTasks for fast simulations.
    """

    def __init__(self, tasks: Set[Task]):
        """
        Initialize FastTasks with a set of Task objects.

        Args:
            tasks (Set[Task]): A set of Task objects to initialize FastTasks with.
        """
        self.tasks = tasks


class FastScenario(CachedScenario):
    """
    A lightweight version of CachedScenario for fast simulations.
    """

    def __init__(
        self,
        scenario: UserScenario,
        members: List[Member],
        tasks: FastTasks,
        id: int,
        config: int,
    ) -> None:
        """
        Initialize FastScenario with given parameters.

        Args:
            scenario (UserScenario): UserScenario object.
            members (List[Member]): List of Member objects.
            tasks (FastTasks): FastTasks object.
            id (int): Identifier for the FastScenario.
            config (int): Configuration identifier for the FastScenario.
        """
        self.id = id
        self.scenario = scenario
        self.members = members
        self.tasks = tasks
        self.config = config
