"""
Helper functions and classes for scripts/fastsim.py
"""

from random import randint, random
from statistics import mean
from typing import List, Tuple
import numpy as np
from pandas import DataFrame
from app.models.scenario import ScenarioConfig
from app.models.task import Task
from app.models.team import Member, SkillType, Team
from app.models.user_scenario import ScenarioState, UserScenario
from app.src.simulation import simulate
from app.dto.request import SimulationRequest, Workpack
from fast_simulation_framework.wrappers import FastScenario, FastTasks


def init_scenario() -> Tuple[UserScenario, ScenarioState, Team]:
    """
    Create and persist a new UserScenario and its related ScenarioState and Team.

    Returns:
        Tuple[UserScenario, ScenarioState, Team] -- (user_scenario, scenario_state, team)

    Notes:
        - All objects are created and saved to the database.
        - ScenarioState and Team are linked to the created UserScenario via the user_scenario FK.
        - Caller is responsible for cleanup (deleting these objects) if needed.

    Example:
        us, state, team = init_scenario()
    """
    us = UserScenario.objects.create()
    state = ScenarioState.objects.create(user_scenario=us)
    team = Team.objects.create(user_scenario=us)
    return us, state, team


def init_config(is_fixed_mode: bool = False) -> ScenarioConfig:
    """
    Initialize Scenario Configuration with default parameters.
    When is_fixed_mode is False, random parameters are used.

    Args:
        is_fixed_mode (bool, optional): When true, use fixed parameters and no randomization. Defaults to False.

    Returns:
        ScenarioConfig: The created ScenarioConfig object.
    """
    try:
        ScenarioConfig.objects.get(name="fast_sim_config").delete()
    except ScenarioConfig.DoesNotExist:
        pass

    if is_fixed_mode:
        return ScenarioConfig.objects.create(
            name="fast_sim_config",
            stress_weekend_reduction=0.2,
            stress_overtime_increase=0.04,
            stress_error_increase=0.02,
            train_skill_increase_rate=0.1,
            done_tasks_per_meeting=50,
            randomness="full",
        )
    else:
        return ScenarioConfig.objects.create(
            name="fast_sim_config",
            stress_weekend_reduction=round(random() * 0.8, 2),
            stress_overtime_increase=round(random() * 0.25, 2),
            stress_error_increase=round(random() * 0.33, 2),
            train_skill_increase_rate=round(random() * 0.5, 2),
            done_tasks_per_meeting=randint(0, 5) * 20,
            randomness="full",
        )


def init_skill_types(is_fixed_mode: bool = False):
    """
    Initialize Team Members (Skill Types) with default parameters.
    If is_fixed_mode is True, use fixed parameters otherwise, use random parameters.
    """

    try:
        SkillType.objects.get(name="s1 Junior Backend Developer").delete()
        SkillType.objects.get(name="s2 Senior Backend Developer").delete()
        SkillType.objects.get(name="s3 Junior Frontend Developer").delete()
        SkillType.objects.get(name="s4 Senior Frontend Developer").delete()
        SkillType.objects.get(name="s5 Junior Consultant").delete()
        SkillType.objects.get(name="s6 Senior Consultant").delete()
    except Exception:
        pass

    if is_fixed_mode:
        s1 = SkillType.objects.create(
            name="s1 Junior Backend Developer",
            cost_per_day=171.15,
            throughput=2,
            error_rate=0.06,
            development_quality=35,
            management_quality=30,
        )
        s2 = SkillType.objects.create(
            name="s2 Senior Backend Developer",
            cost_per_day=250,
            throughput=3,
            error_rate=0.03,
            development_quality=70,
            management_quality=40,
        )
        s3 = SkillType.objects.create(
            name="s3 Junior Frontend Developer",
            cost_per_day=164.6,
            throughput=2,
            error_rate=0.05,
            development_quality=25,
            management_quality=30,
        )
        s4 = SkillType.objects.create(
            name="s4 Senior Frontend Developer",
            cost_per_day=216.09,
            throughput=3,
            error_rate=0.03,
            development_quality=60,
            management_quality=40,
        )
        s5 = SkillType.objects.create(
            name="s5 Junior Consultant",
            cost_per_day=182.69,
            throughput=2,
            error_rate=0.06,
            development_quality=20,
            management_quality=55,
        )
        s6 = SkillType.objects.create(
            name="s6 Senior Consultant",
            cost_per_day=230.77,
            throughput=4,
            error_rate=0.03,
            development_quality=20,
            management_quality=90,
        )
        return [s1, s2, s3, s4, s5, s6]
    else:
        s1 = SkillType.objects.create(
            name="s1 Junior Backend Developer",
            cost_per_day=200,
            throughput=randint(1, 5),
            error_rate=round(random() * 0.23 + 0.1, 2),
        )
        s2 = SkillType.objects.create(
            name="s2 Senior Backend Developer",
            cost_per_day=350,
            throughput=randint(3, 8),
            error_rate=round(random() * 0.3 + 0.03, 2),
        )
        s3 = SkillType.objects.create(
            name="s3 Junior Frontend Developer",
            cost_per_day=500,
            throughput=randint(5, 10),
            error_rate=round(random() * 0.25, 2),
        )
        s4 = SkillType.objects.create(
            name="s4 Senior Frontend Developer",
            cost_per_day=400,
            throughput=randint(2, 6),
            error_rate=round(random() * 0.2 + 0.05, 2),
        )
        s5 = SkillType.objects.create(
            name="s5 Junior Consultant",
            cost_per_day=250,
            throughput=randint(1, 4),
            error_rate=round(random() * 0.22 + 0.08, 2),
        )
        s6 = SkillType.objects.create(
            name="s6 Senior Consultant",
            cost_per_day=300,
            throughput=randint(4, 9),
            error_rate=round(random() * 0.28 + 0.04, 2),
        )

    return [s1, s2, s3, s4, s5, s6]


def init_members(skill_types: List[SkillType]) -> List[Member]:
    """
    Creates Member objects for each skill type.

    Args:
        skill_types (List[SkillType]): List of SkillType objects.

    Returns:
        List[Member]: List of created Member objects.
    """
    members = []
    for sk in skill_types:
        members.append(Member.objects.create(skill_type=sk, team_id=1))
    return members


def run_simulation(
    scenario: UserScenario,
    config: ScenarioConfig,
    members: List[Member],
    tasks: FastTasks,
    skill_types: List[SkillType],
    rec: "NpRecord",
    UP: Workpack,
    UP_n: int,
):
    """
    Run a single simulation with given parameters.
    Results are not returned but recorded in the provided NpRecord instance.

    Args:
        scenario (UserScenario): Scenario to simulate.
        config (ScenarioConfig): Configuration for the simulation.
        members (List[Member]): List of members involved in the simulation.
        tasks (FastTasks): Tasks to be processed in the simulation.
        skill_types (List[SkillType]): Skill types available in the simulation.
        rec (NpRecord): Record to store simulation results.
        UP (Workpack): Workpack containing actions for the simulation.
        UP_n (int): Identifier or count related to the workpack.
    """
    scenario.config = config
    s = FastScenario(scenario, members, tasks, 1, 1)
    r = SimulationRequest(scenario_id=0, type="SIMULATION", actions=UP)
    simulate(r, s)
    rec.add(s, config, skill_types, UP, UP_n)


def run_continuous_simulation(
    scenario: UserScenario,
    config: ScenarioConfig,
    members: List[Member],
    tasks: FastTasks,
    skill_types: List[SkillType],
    rec: "NpRecord",
    UP: Workpack,
    UP_n: int,
) -> FastScenario:
    """
    Run a continuous simulation with given parameters.
    On the first run, initializes a new FastSecenario.
    On subsequent runs, continues the simulation with the existing scenario.
    Results are recorded in the provided NpRecord instance.

    Args:
        scenario (UserScenario): Scenario to simulate.
        config (ScenarioConfig): Configuration for the simulation.
        members (List[Member]): List of members involved in the simulation.
        tasks (FastTasks): Tasks to be processed in the simulation.
        skill_types (List[SkillType]): Skill types available in the simulation.
        rec (NpRecord): Record to store simulation results.
        UP (Workpack): Workpack containing actions for the simulation.
        UP_n (int): Identifier or count related to the workpack.

    Returns:
        FastSecenario: The updated or newly created FastSecenario instance.
    """
    if UP_n == 0:
        # First run of continuous simulation
        scenario.config = config
        s = FastScenario(scenario, members, tasks, 1, 1)
        r = SimulationRequest(scenario_id=0, type="SIMULATION", actions=UP)
        simulate(r, s)
        rec.add(s, config, skill_types, UP, UP_n)
        return s
    else:
        r = SimulationRequest(scenario_id=0, type="SIMULATION", actions=UP)
        simulate(r, scenario)
        rec.add(scenario, config, skill_types, UP, UP_n)
        return scenario


def set_tasks_random(us: UserScenario) -> FastTasks:
    """
    Creates tasks with random difficulties for the given user scenario.
    25% tasks of difficulty 1, 50% of difficulty 2, 25% of difficulty 3.

    Args:
        us (UserScenario): The user scenario to associate tasks with.

    Returns:
        FastTasks: A collection of tasks with random difficulties associated with the given user scenario.
    """

    TOTAL = 200
    tasks = set()
    for _ in range(int(TOTAL * 0.25)):
        tasks.add(Task(id=randint(0, 9999999999), difficulty=1, user_scenario=us))
    for _ in range(int(TOTAL * 0.5)):
        tasks.add(Task(id=randint(0, 9999999999), difficulty=2, user_scenario=us))
    for _ in range(int(TOTAL * 0.25)):
        tasks.add(Task(id=randint(0, 9999999999), difficulty=3, user_scenario=us))
    return FastTasks(tasks)


def set_tasks_fixed(us: UserScenario) -> FastTasks:
    """
    Creates a fixed set of tasks for the given user scenario.
    125 tasks of difficulty 1, 250 tasks of difficulty 2, 155 tasks of difficulty 3.

    Args:
        us (UserScenario): The user scenario to associate tasks with.

    Returns:
        FastTasks: A collection of tasks with fixed difficulties associated with the given user scenario.
    """
    tasks = set()
    for _ in range(125):
        tasks.add(Task(id=randint(0, 9999999999), difficulty=1, user_scenario=us))
    for _ in range(250):
        tasks.add(Task(id=randint(0, 9999999999), difficulty=2, user_scenario=us))
    for _ in range(155):
        tasks.add(Task(id=randint(0, 9999999999), difficulty=3, user_scenario=us))
    return FastTasks(tasks)


def set_members(members: List[Member]) -> List[Member]:
    """
    Sets members' attributes to initial values.

    Args:
        members (List[Member]): List of members to set attributes for.

    Returns:
        List[Member]: List of members with attributes set to initial values.
    """
    for member in members:
        member.familiar_tasks = 0
        member.familiarity = 0
        member.motivation = 0.75
        member.stress = 0.15
        member.xp = 0

    return members


def set_scenario_state(state: ScenarioState) -> ScenarioState:
    """
    Sets parameters for the scenario state object to initial values.

    Args:
        state (ScenarioState): The scenario state to set parameters for.

    Returns:
        ScenarioState: The updated scenario state with parameters set.
    """

    state.cost = 0
    state.day = 0
    return state


def np_record(
    s: FastScenario,
    config: ScenarioConfig,
    skill_types: List[SkillType],
    workpack: Workpack,
    UP_n: int,
) -> np.array:
    """
    Create a numpy array record of the simulation state and parameters.

    Args:
        s (FastSecenario): Current simulation scenario.
        config (ScenarioConfig): Current scenario configuration.
        skill_types (List[SkillType]): List of skill types in the simulation.
        workpack (Workpack): Current workpack being processed.
        UP_n (int): Index or identifier for the user parameters.
    Returns:
        np.array: Numpy array representing the simulation record.
    """

    return np.array(
        [
            config.stress_weekend_reduction,
            config.stress_overtime_increase,
            config.stress_error_increase,
            config.done_tasks_per_meeting,
            config.train_skill_increase_rate,
            skill_types[0].throughput,
            skill_types[0].error_rate,
            skill_types[1].throughput,
            skill_types[1].error_rate,
            skill_types[2].throughput,
            skill_types[2].error_rate,
            skill_types[3].throughput,
            skill_types[3].error_rate,
            skill_types[4].throughput,
            skill_types[4].error_rate,
            skill_types[5].throughput,
            skill_types[5].error_rate,
            UP_n,
            workpack.days,
            workpack.bugfix,
            workpack.unittest,
            workpack.integrationtest,
            workpack.meetings,
            workpack.training,
            workpack.teamevent,
            workpack.overtime,
            s.scenario.state.cost,
            s.scenario.state.day,
            mean([m.efficiency for m in s.members]),
            mean([m.familiarity for m in s.members]),
            mean([m.stress for m in s.members]),
            mean([m.xp for m in s.members]),
            mean([m.motivation for m in s.members]),
            len(s.tasks.accepted()),
            len(s.tasks.rejected()),
            s.tasks.len_tasks(),
            s.tasks.len_tasks_worked_on(),
        ]
    )


class NpRecord:
    """
    Class to store and manage numpy array records of simulation data.
    """

    def __init__(self):
        self.data = None

    def add(self, s: FastScenario, *args):
        if self.data is None:
            self.data = np.array([np_record(s, *args)])
        else:
            self.data = np.vstack((self.data, np.array([np_record(s, *args)])))

    def clear(self):
        self.data = None

    def df(self):
        return DataFrame(
            self.data,
            columns=[
                "c_swr",
                "c_soi",
                "c_sei",
                "c_dtm",
                "c_tsi",
                "s1_thr",
                "s1_err",
                "s2_thr",
                "s2_err",
                "s3_thr",
                "s3_err",
                "s4_thr",
                "s4_err",
                "s5_thr",
                "s5_err",
                "s6_thr",
                "s6_err",
                "UP",
                "days",
                "bugfix",
                "unittest",
                "integrationtest",
                "meetings",
                "training",
                "teamevent",
                "overtime",
                "Cost",
                "Day",
                "Eff",
                "Fam",
                "Str",
                "XP",
                "Mot",
                "Acc",
                "Rej",
                "total_tasks",
                "worked_on_tasks",
            ],
        )
