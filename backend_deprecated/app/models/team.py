from __future__ import annotations
from statistics import mean
import numpy as np
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
)
from django.db import models
from app.dto.request import Workpack
from app.dto.response import TeamStatsDTO
from app.models.task import Task
from app.models.user_scenario import UserScenario
from app.src.util.util import probability

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.cache.scenario import CachedScenario

# Debug mode flag
from softDsim.settings import DEBUG_MODE, DEBUG_DIRECTORY

if DEBUG_MODE:
    import csv
    import os
    import datetime


class Team(models.Model):
    """
    Represents a team within the simulated project environment.

    The Team class models key team characteristics, behaviors, and management operations within a project scenario.
    It maintains team-level statistics such as efficiency, communication channels, and management skill.
    The class also orchestrates workflows simulating meetings, training sessions, and collaborative work,
    acting as a central unit for resource and performance calculations.

    Attributes:
        name (CharField): The team name.
        userscenario (OneToOneField): The user scenario this team is linked to.

    Methods:
        num_communication_channels(teamsize):
            Returns the number of unique communication channels in a team of given size.

        efficiency(session):
            Computes team efficiency based on the number of communication channels.

        management_skill(session):
            Calculates the team's effective management skill as a probability value.

        motivation(members):
            Returns the team's average motivation level.

        familiarity(members):
            Returns the average project familiarity across team members.

        stress(members):
            Returns the average stress level among members.

        stats(members):
            Aggregates and returns all team statistics as a DTO object.

        meetingsession(session, workhours):
            Simulates a meeting, improving familiarity and consuming work hours.

        training(session, workhours, mean_real_throughput):
            Simulates training to improve members' experience and motivation.

        work(session, workpack, workpackstatus, currentday):
            Simulates a complete workday, including meetings, training, and task work.

        apply_weekend_stress_reduction(session):
            Reduces member stress at specified intervals.

        conduct_meetings(session, workpackstatus, currentday, remainingworkhours):
            Schedules meetings for the workday.

        conduct_training(session, workpackstatus, remainingworkhours):
            Manages training sessions within time constraints.

        apply_overtime_stress(session, workpack):
            Increases members' stress due to overtime.

        task_work(session, hours, workpack):
            Orchestrates task assignment and completion for all team members.

    Raises:
        TypeError: If required attributes are missing.
        ValueError: For invalid input values or configuration.

    """

    name = models.CharField(max_length=32, default="team")

    user_scenario = models.OneToOneField(
        UserScenario,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="team",
    )

    @staticmethod
    def num_communication_channels(team_size: int) -> int:
        """
        Returns the number of communication channels in a team.

        In a team of n people, each person can communicate with n-1 others.
        The total number of unique communication channels is n(n-1)/2.

        Args:
            team_size: The number of team members

        Returns:
            The number of unique communication channels

        Raises:
            ValueError: If n is negative
        """
        if team_size < 0:
            raise ValueError("Number of team members cannot be negative")

        return int((team_size * (team_size - 1)) // 2)

    def efficiency(self, session) -> float:
        """
        Returns the team's efficiency based on communication channels.

        Efficiency decreases as the number of communication channels increases,
        following the principle that more communication paths increase complexity
        and reduce overall team efficiency.

        Args:
            session: The session containing team members

        Returns:
            float: Efficiency value between 0 and 1, where higher values
                indicate better efficiency

        Raises:
            TypeError: If session or session.members is None
        """

        if session is None or not hasattr(session, "members"):
            raise TypeError("Session with members attribute is required.")

        # Constants that determine the efficiency curve
        # Controls how quickly efficiency drops with more channels
        CHANNEL_SCALING_FACTOR = 20.0
        # Small positive offset to prevent division by zero
        EFFICIENCY_OFFSET = 0.05

        # Calculate communication channels
        num_members = len(session.members)
        channels = self.num_communication_channels(num_members)

        # Calculate efficiency using the inverse relationship with communication channels
        return 1 / (1 + (channels / CHANNEL_SCALING_FACTOR - EFFICIENCY_OFFSET))

    def management_skill(self, session: CachedScenario) -> float:
        """
        Returns the team's management skill as a probability value.

        This value represents the likelihood of producing correct task specifications.
        It's calculated based on the management_quality of team members' skill types,
        weighted by their experience level and current motivation.

        Returns:
            float: A value between 0.0 and 1.0 representing management skill
        """

        # TODO: reenable checks, because in intial start there are no members yet
        # api endpoint /sim/next is used before members are created
        # and this causes errors. Needs to be fixed properly.

        # if not hasattr(self, "members") or not session.members.exists():
        #     return 0.0  # No members, no management skill

        # members = session.members.all()

        # Support both Django QuerySet (has exists()/all()) and plain lists/iterables.
        if session is None or not hasattr(session, "members"):
            return 0.0

        members_attr = session.members

        # If it's a QuerySet-like object, use exists()/all()
        if hasattr(members_attr, "exists"):
            try:
                if not members_attr.exists():
                    return 0.0
            except Exception:
                # Fall back to treating as iterable below
                pass

            try:
                members = list(members_attr.all())
            except Exception:
                # If .all() is not available or fails, coerce to list
                members = list(members_attr)
        else:
            # Assume it's an iterable (like a list)
            members = list(members_attr)

        if len(members) == 0:
            return 0.0  # No members, no management skill

        # Calculate weighted management quality based on each member's skill type,
        # experience level and motivation
        weighted_quality_sum = 0
        total_weight = 0

        for member in members:
            if member.skill_type:
                # Higher weight for members with greater experience and motivation
                weight = 1.0 + member.xp + (member.motivation / 2)

                # Convert management_quality (0-100) to a 0-1 scale
                quality = member.skill_type.management_quality / 100

                weighted_quality_sum += weight * quality
                total_weight += weight

        if total_weight == 0:
            return 0.0  # No members, no management skill

        # Return normalized management skill between 0.0 and 1.0
        return_value = min(1.0, max(0.0, weighted_quality_sum / total_weight))
        return return_value

    @staticmethod
    def motivation(members) -> float:
        """
        Calculate the team's average motivation level.

        Args:
            members: Collection of team members

        Returns:
            float: Average motivation value between 0.0 and 1.0

        Raises:
            TypeError: If members parameter is None
        """

        if members is None:
            raise TypeError("Attribute members is required")
        if len(members) == 0:
            return 0

        return mean([member.motivation for member in members])

    @staticmethod
    def familiarity(members) -> float:
        """
        Calculate the team's average familiarity level.

        This metric represents how familiar team members are with the project's tasks.
        Higher values indicate better team knowledge of the codebase and requirements.

        Args:
            members: Collection of team members

        Returns:
            float: Average familiarity value between 0.0 and 1.0

        Raises:
            TypeError: If members parameter is None
        """

        if members is None:
            raise TypeError("Attribute members is required")
        if len(members) == 0:
            return 0

        return mean([member.familiarity for member in members])

    @staticmethod
    def stress(members) -> float:
        """
        Calculate the team's average stress level.

        This metric represents how stressed team members are with the project's tasks.
        Higher values indicate higher team stress level.

        Args:
            members: Collection of team members

        Returns:
            float: Average stress level value between 0.0 and 1.0

        Raises:
            TypeError: If members parameter is None
        """
        if members is None:
            raise TypeError("Attribute members is required")
        if len(members) == 0:
            return 0

        return mean([m.stress for m in members])

    def stats(self, members) -> TeamStatsDTO:
        """
        Return all team statistics as a data transfer object.

        Aggregates motivation, familiarity, and stress metrics into a single DTO
        for convenient access and transmission.

        Args:
            members: Collection of team members

        Returns:
            TeamStatsDTO: Object containing all team statistics

        Raises:
            TypeError: If members parameter is None
            ValueError: If members parameter is empty
        """
        # TODO: reenable checks, because in intial start there are no members yet
        # api endpoint /sim/next is used before members are created
        # and this causes errors. Needs to be fixed properly.

        # if members is None:
        #     raise TypeError("Attribute members is required")
        # if not members:
        #     raise ValueError("Attribute members cannot be empty")

        return TeamStatsDTO(
            motivation=self.motivation(members),
            familiarity=self.familiarity(members),
            stress=self.stress(members),
        )

    @staticmethod
    def meeting(session: CachedScenario, work_hours: int) -> int:
        """
        Simulate a team meeting that increases members' familiarity with solved tasks.

        During a meeting, team members become familiar with additional tasks based on
        the configured number of tasks that can be discussed per meeting.

        Args:
            session: The cached scenario containing tasks and team members
            work_hours: Available work hours before the meeting

        Returns:
            int: Remaining work hours after the meeting (1 hour consumed)

        Raises:
            ValueError: If work_hours is less than 1
            TypeError: If session is None or lacks required attributes
        """

        if session is None:
            raise TypeError("Session parameter is required")
        if not hasattr(session, "tasks") or not hasattr(session, "members"):
            raise TypeError("Session must have 'tasks' and 'members' attributes")
        if work_hours < 1:
            raise ValueError("Work hours must be at least 1")

        # Get configuration and solved tasks once to avoid repeated calls
        solved_tasks = session.tasks.solved()
        solved_tasks_count = len(solved_tasks)
        tasks_per_meeting = session.scenario.config.done_tasks_per_meeting

        # Update each member's familiarity
        for member in session.members:
            # Increase familiar tasks up to the maximum number of solved tasks

            member.familiar_tasks = min(
                member.familiar_tasks + tasks_per_meeting, solved_tasks_count
            )

            # Update the familiarity percentage
            member.calculate_familiarity(solved_tasks_count)

        # Return remaining work hours
        return work_hours - 1

    @staticmethod
    def training(
        session: CachedScenario, work_hours: int, mean_real_throughput: float
    ) -> int:
        """
        Simulate team training that increases member experience and motivation.

        Training helps members with lower throughput catch up to the team's average.
        Members whose throughput is already above average do not gain additional experience.

        Args:
            session: The cached scenario containing team members
            work_hours: Available work hours before training
            mean_real_throughput: The team's average throughput

        Returns:
            int: Remaining work hours after the training (1 hour consumed)

        Raises:
            ValueError: If work_hours is less than 1
            TypeError: If session is None or lacks required attributes
        """

        if session is None:
            raise TypeError("Session parameter is required")
        if not hasattr(session, "members") or not hasattr(session, "scenario"):
            raise TypeError("Session must have members and scenario attributes")
        if work_hours < 1:
            raise ValueError("Not enough work hours available for training")

        train_skill_increase_rate = session.scenario.config.train_skill_increase_rate

        MOTIVATION_BOOST = 0.1

        for member in session.members:
            # Calculate the difference between team average and member's throughput
            members_throughput = member.skill_type.throughput * (1 + member.xp)
            delta = mean_real_throughput - members_throughput

            # Only improve members who are below the team average
            if delta > 0:
                # Experience gain is inversely proportional to current experience level
                xp_gain = (delta * train_skill_increase_rate) / (1 + member.xp) ** 2
                member.xp += xp_gain

                # Boost motivation for successful training
                member.motivation = min(1.0, member.motivation + MOTIVATION_BOOST)

        # Return remaining work hours
        return work_hours - 1

    def work(
        self,
        session: CachedScenario,
        workpack: Workpack,
        workpack_status,
        current_day: int,
    ) -> None:
        """
        Simulate a complete workday for the team with meetings, training, and task work.

        This method orchestrates all team activities during a workday:
        1. Calculates staff costs
        2. Reduces stress on weekends (every 5th day)
        3. Conducts scheduled meetings
        4. Performs training sessions if scheduled
        5. Applies overtime stress to team members
        6. Applies solo worker stress penalty (if only one team member)
        7. Allocates remaining time to task work

        Args:
            session: The cached scenario containing team members and tasks
            workpack: Configuration for the current work period
            workpack_status: Status tracking for workpack activities
            current_day: Current day index in the simulation

        Returns:
            None
        """

        NORMAL_WORK_HOUR_DAY: int = 8

        # Calculate total work hours including overtime
        remaining_work_hours = NORMAL_WORK_HOUR_DAY + workpack.overtime

        # Calculate and apply staff costs
        staff_cost = sum(member.skill_type.cost_per_day for member in session.members)
        session.scenario.state.cost += staff_cost

        # Every 5th day, the stress is reduced by stress_weekend_reduction
        if session.scenario.state.day % 5 == 0:
            self._apply_weekend_stress_reduction(session)

        # 1. Conduct scheduled meetings
        remaining_work_hours = self._conduct_meetings(
            session, workpack_status, current_day, remaining_work_hours
        )

        # 2. Conduct training sessions if scheduled
        remaining_work_hours = self._conduct_training(
            session, workpack_status, remaining_work_hours
        )

        # Apply overtime stress to team members
        self._apply_overtime_stress(session, workpack)

        # Apply solo worker stress penalty (working alone increases stress)
        self._apply_solo_worker_stress(session)

        # 3. Allocate remaining time to task work
        self.task_work(session, remaining_work_hours, workpack)

    @staticmethod
    def _apply_weekend_stress_reduction(session: CachedScenario) -> None:
        """Apply weekend stress reduction to all team members."""
        for member in session.members:
            member.stress = max(
                0, member.stress - session.scenario.config.stress_weekend_reduction
            )

    def _conduct_meetings(
        self,
        session: CachedScenario,
        workpack_status,
        current_day: int,
        remaining_work_hours: int,
    ) -> int:
        """Conduct scheduled meetings and return remaining work hours."""
        for _ in range(workpack_status.meetings_per_day[current_day]):
            if remaining_work_hours >= 1:
                remaining_work_hours = self.meeting(session, remaining_work_hours)

        return remaining_work_hours

    def _conduct_training(
        self, session: CachedScenario, workpack_status, remaining_work_hours: int
    ) -> int:
        """Conduct training sessions and return remaining work hours."""
        remaining_trainings_today = workpack_status.remaining_trainings

        if remaining_trainings_today <= 0:
            return remaining_work_hours

        # Adjust training sessions based on available hours
        if remaining_trainings_today > remaining_work_hours:
            workpack_status.remaining_trainings = (
                remaining_trainings_today - remaining_work_hours
            )
            remaining_trainings_today = remaining_work_hours
        else:
            workpack_status.remaining_trainings = 0

        # Calculate team's average throughput
        mean_real_throughput_of_team = mean(
            [
                member.skill_type.throughput * (1 + member.xp)
                for member in session.members
            ]
        )

        # Conduct training sessions
        for _ in range(remaining_trainings_today):
            if remaining_work_hours >= 1:
                remaining_work_hours = self.training(
                    session, remaining_work_hours, mean_real_throughput_of_team
                )

        return remaining_work_hours

    @staticmethod
    def _apply_overtime_stress(session: CachedScenario, workpack: Workpack) -> None:
        """
        Apply stress increase to team members due to overtime work.
        Possible values from workpack.overtime are
        -1 (Leave early)
        0 (No overtime)
        1 (Encourage Overtime)
        2 (Enforce Overtime)

        Args:
            session (CachedScenario): The current cached scenario containing team members.
            workpack (Workpack): The workpack containing overtime information.
        """
        for member in session.members:
            stress_increase = (
                workpack.overtime * session.scenario.config.stress_overtime_increase
            )
            member.stress = max(0, min(1, member.stress + stress_increase))

    @staticmethod
    def _apply_solo_worker_stress(session: CachedScenario) -> None:
        """
        Apply additional stress for members working alone (no team support).
        Working alone without team support increases stress faster, which
        negatively affects efficiency. This penalty applies when there is
        only one team member.

        Args:
            session (CachedScenario): The current cached scenario containing team members.
        """
        # Solo worker stress penalty factor
        SOLO_STRESS_INCREASE = 0.05

        if len(session.members) == 1:
            for member in session.members:
                member.stress = min(1.0, member.stress + SOLO_STRESS_INCREASE)

    def task_work(self, session: CachedScenario, hours: int, workpack: Workpack):
        """
        Handles task work for all team members during a work day.

        This method:
        1. Processes unit tests if enabled in workpack
        2. Fixes bugs if enabled in workpack
        3. Completes new tasks based on each member's capacity

        Args:
            session: The cached scenario containing tasks and team members
            hours: Available work hours for task work
            workpack: Configuration for the current work period
        """
        if hours <= 0:
            return  # No time left for task work

        if DEBUG_MODE:
            """
            ----------------- Debug Logging Setup -----------------
            Log task work actions to CSV for analysis
            """

            # Prepare CSV output directory and file
            output_dir = DEBUG_DIRECTORY
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Failed to create output directory {output_dir}: {e}")

            local_filename = output_dir / "task_work_log.csv"
            write_header = not os.path.exists(local_filename)

            # Ensure header is written only once (best-effort)
            if write_header:
                try:
                    with open(local_filename, "a", newline="") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(
                            [
                                "timestamp",
                                "day",
                                "member_id",
                                "member_repr",
                                "skill_type",
                                "action",
                                "task_id",
                                "task_difficulty",
                                "task_bug",
                                "task_correct_specification",
                                "task_unit_tested",
                                "task_integration_tested",
                                "calc_management_skill",
                            ]
                        )
                except Exception:
                    print("Could not write header to task work log.")
                    pass
                write_header = False

            def _log_task_action(member, task, action):
                """Append a single action row to the task work CSV (best-effort)."""
                try:
                    with open(local_filename, "a", newline="") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(
                            [
                                datetime.datetime.utcnow().isoformat(),
                                getattr(session.scenario.state, "day", ""),
                                getattr(member, "id", ""),
                                str(member),
                                (
                                    getattr(member.skill_type, "name", "")
                                    if member.skill_type
                                    else ""
                                ),
                                action,
                                getattr(task, "id", ""),
                                getattr(task, "difficulty", ""),
                                getattr(task, "bug", ""),
                                getattr(task, "correct_specification", ""),
                                getattr(task, "unit_tested", ""),
                                getattr(task, "integration_tested", ""),
                                self.management_skill(session),
                            ]
                        )
                except Exception:
                    print("Could not write task action to log.")
                    pass

        tasks = session.tasks
        tasks_processed = {member.id: 0 for member in session.members}

        for member in session.members:
            # Calculate the number of tasks that the member can do in the given hours
            capacity, poisson_value = member.calculate_number_of_tasks(hours, session)

            # Track Poisson distribution statistics
            session.scenario.state.poisson_sum += poisson_value
            session.scenario.state.poison_counter += 1

            # Process unit tests
            if workpack.unittest and capacity > 0:
                tasks_to_test = tasks.done()
                tests_performed = min(capacity, len(tasks_to_test))

                for _ in range(tests_performed):
                    if not tasks_to_test:
                        break

                    task = tasks_to_test.pop()
                    task.unit_tested = True
                    tasks_processed[member.id] += 1
                    capacity -= 1

                    # Increase stress if member introduced a bug
                    if task.bug:
                        stress_increase = session.scenario.config.stress_error_increase
                        member.stress = min(
                            1.0,
                            member.stress + stress_increase,
                        )

                    if DEBUG_MODE:
                        _log_task_action(member, task, "unit_test")

            # Fix bugs
            if workpack.bugfix and capacity > 0:
                tasks_to_fix = tasks.bug()
                bugs_fixed = min(capacity, len(tasks_to_fix))

                for _ in range(bugs_fixed):
                    if not tasks_to_fix:
                        break

                    task = tasks_to_fix.pop()
                    task.bug = False
                    tasks_processed[member.id] += 1
                    capacity -= 1

                    if DEBUG_MODE:
                        _log_task_action(member, task, "bug_fix")

            # Work on new tasks with remaining capacity
            if capacity > 0:
                tasks_to_do = tasks.todo()
                tasks_completed = min(capacity, len(tasks_to_do))

                for _ in range(tasks_completed):
                    if not tasks_to_do:
                        break

                    task = tasks_to_do.pop()
                    task.done = True

                    # Calculate error rate reduction based on member's skill
                    error_increase = member.solve_task(task)

                    # Determine if task has a bug based on member's error rate
                    bug_probability = (
                        member.skill_type.error_rate + member.stress - error_increase
                    ) / 3
                    task.bug = probability(bug_probability)

                    # Set other task attributes
                    task.correct_specification = probability(
                        self.management_skill(session)
                    )
                    task.unit_tested = False
                    task.integration_tested = False

                    # Update member stats
                    member.familiar_tasks += 1
                    tasks_processed[member.id] += 1

                    if DEBUG_MODE:
                        _log_task_action(member, task, "done")

                    capacity -= 1

            # Update member familiarity after completing tasks
            member.calculate_familiarity(len(tasks.solved()))


class SkillType(models.Model):
    """
    Represents a specific skill type or role within a team.

    Contains core attributes that define performance characteristics,
    quality metrics, and associated costs.
    """

    name = models.CharField(
        max_length=32,
        unique=True,
        help_text="Name of the skill type (e.g., 'Junior Developer')",
    )

    cost_per_day = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=100,
        help_text="Daily cost for this skill type",
    )

    error_rate = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        default=0.05,
        help_text="Probability of introducing errors (0.0 to 1.0)",
    )

    throughput = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=1,
        help_text="Base productivity multiplier",
    )

    management_quality = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        help_text="Management skill quality (0-100)",
    )

    development_quality = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=100,
        help_text="Development skill quality (0-100)",
    )

    signing_bonus = models.FloatField(
        validators=[MinValueValidator(0.0)],
        default=0,
        help_text="One-time bonus paid when hiring",
    )

    class Meta:
        verbose_name = "Skill Type"
        verbose_name_plural = "Skill Types"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def calculate_effective_throughput(self, experience: float = 0.0) -> float:
        """
        Calculate effective throughput considering experience.

        Args:
            experience: Experience multiplier (default: 0.0)

        Returns:
            float: The effective throughput value
        """
        return self.throughput * (1 + experience)

    def calculate_total_cost(self, days: int) -> float:
        """
        Calculate the total cost for this skill type over a period.

        Args:
            days: Number of days to calculate cost for

        Returns:
            float: Total cost including daily rate and signing bonus
        """
        return (self.cost_per_day * days) + self.signing_bonus

    @property
    def has_additional_info(self) -> bool:
        """Check if this skill type has additional information."""
        return self.extra_info is not None

    @property
    def quality_rating(self) -> float:
        """
        Calculate an overall quality rating based on development and management quality.

        Returns:
            float: Quality rating between 0.0 and 1.0
        """
        return (self.development_quality + self.management_quality) / 200.0


class Member(models.Model):
    """
    Represents a team member with skills, attributes, and performance metrics.

    Members have various characteristics that affect their performance including
    experience level, motivation, familiarity with tasks, and stress level.
    Each member belongs to a team and has a specific skill type.
    """

    # Experience points - affects productivity and error rates
    xp = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Experience level of the member (0.0+)",
    )

    # Motivation level - affects productivity and quality
    motivation = models.FloatField(
        default=0.75,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Motivation level of the member (0.0-1.0)",
    )

    # Number of tasks the member is familiar with
    familiar_tasks = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of tasks the member is familiar with",
    )

    # Familiarity ratio (familiar_tasks / total_tasks)
    familiarity = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Ratio of familiar tasks to total tasks (0.0-1.0)",
    )

    # Stress level - affects error rates and efficiency
    stress = models.FloatField(
        default=0.1,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Current stress level of the member (0.0-1.0)",
    )

    # Relationships
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="members",
        help_text="The team this member belongs to",
    )

    skill_type = models.ForeignKey(
        SkillType,
        on_delete=models.CASCADE,
        related_name="members",
        blank=True,
        null=True,
        help_text="The skill type of this member",
    )

    # Constants
    IDEAL_STRESS_LEVEL = 0.2
    MOTIVATION_ADJUSTMENT_FACTOR = 0.01
    TASK_SCALING_FACTOR = 0.2

    class Meta:
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
        ordering = ["team", "skill_type__name"]
        indexes = [
            models.Index(fields=["team"]),
            models.Index(fields=["skill_type"]),
        ]

    def __str__(self):
        skill_name = "Unassigned" if self.skill_type is None else self.skill_type.name
        return f"{skill_name} Member"

    def clean(self):
        """Validate the model before saving."""
        super().clean()
        if self.familiar_tasks < 0:
            raise ValidationError({"familiar_tasks": "Cannot be negative"})

    @property
    def efficiency(self) -> float:
        """
        Calculate the efficiency of the member based on their attributes

        The efficiency is calculated from:
        - Familiarity with tasks
        - Current motivation level
        - Stress level (with 0.2 being the optimal stress level)

        Returns:
            float: Efficiency value between 0.0 and 1.0
        """

        # Calculate optimal stress contribution
        optimal_stress_contribution = 1 - abs(self.stress - self.IDEAL_STRESS_LEVEL)

        # Calculate base efficiency from member attributes
        base_efficiency = (
            self.familiarity + self.motivation + optimal_stress_contribution
        ) / 3

        return base_efficiency

    def calculate_familiarity(self, solved_tasks: int) -> float:
        """
        Calculate the familiarity ratio based on known tasks versus total solved tasks.

        Familiarity represents the proportion of tasks a team member is familiar with
        compared to the total number of tasks they've solved. This metric indicates
        how comfortable or experienced the member is with the current work.

        Args:
            solved_tasks (int): The total number of tasks solved by the team member.

        Returns:
            float: The calculated familiarity value, normalized to range [0.0, 1.0].
                - 0.0 indicates no familiarity (when no tasks are solved or known)
                - 1.0 indicates complete familiarity (all solved tasks are familiar)
        """

        if solved_tasks > 0:
            self.familiarity = self.familiar_tasks / solved_tasks
        else:
            self.familiarity = 0.0

        self.familiarity = min(max(self.familiarity, 0.0), 1.0)

        if DEBUG_MODE:
            """
            ----------------------------- Debug Logging -----------------------------
            Log to CSV for analysis of familiarity calculation statistics
            """
            output_dir = DEBUG_DIRECTORY

            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Failed to create output directory {output_dir}: {e}")

            local_filename = output_dir / "familiarity_calc_stats.csv"
            write_header = not os.path.exists(local_filename)
            with open(local_filename, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                if write_header:
                    writer.writerow(
                        [
                            "timestamp",
                            "member_id",
                            "member_name",
                            "familiar_tasks",
                            "solved_tasks",
                            "calculated_familiarity",
                        ]
                    )
                writer.writerow(
                    [
                        datetime.datetime.utcnow().isoformat(),
                        getattr(self, "id", ""),
                        str(self),
                        self.familiar_tasks,
                        solved_tasks,
                        self.familiarity,
                    ]
                )

        return self.familiarity

    def calculate_number_of_tasks(self, hours: int, session) -> tuple[int, int]:
        """
        Calculate the number of tasks the member can complete in the given hours.

        Uses a Poisson distribution to model task completion with randomness
        based on the scenario configuration.

        Args:
            hours (int): Available work hours
            session: The cached scenario with configuration settings

        Returns:
            tuple[int, int]: (Number of tasks, Poisson random value used)
        """

        if not self.skill_type:
            return 0, 0

        # Calculate the expected number of tasks (mu parameter for Poisson)
        member_efficiency = self.efficiency
        team_efficiency = self.team.efficiency(session)

        # Average the member and team efficiency
        combined_efficiency = (member_efficiency + team_efficiency) / 2

        # Calculate base throughput from skill type and experience
        base_throughput = self.skill_type.throughput + self.xp

        # Calculate the expected number of tasks
        mu = hours * combined_efficiency * base_throughput

        # Handle different randomness settings
        randomness = session.scenario.config.randomness

        return_value = (0, 0)

        if randomness == "none":  # Deterministic mode - no randomness
            calc_capacity_rounded = round(mu * self.TASK_SCALING_FACTOR)
            return_value = int(calc_capacity_rounded), 0
            return return_value

        # Generate a random value from Poisson distribution
        poisson_value = np.random.poisson(mu)

        if (
            randomness == "semi"
        ):  # Semi-random mode - average of random and deterministic
            avg_value = np.mean([poisson_value, mu])
            calc_capacity_rounded = round(avg_value * self.TASK_SCALING_FACTOR)
            return_value = int(calc_capacity_rounded), poisson_value
            return return_value

        # Fully random mode
        calc_capacity_rounded = round(poisson_value * self.TASK_SCALING_FACTOR)
        return_value = int(calc_capacity_rounded), poisson_value

        if DEBUG_MODE:
            """
            ----------------------------- Debug Logging -----------------------------
            Log to CSV for analysis of capacity distribution statistics
            """

            output_dir = DEBUG_DIRECTORY

            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Failed to create output directory {output_dir}: {e}")

            local_filename = output_dir / "capacity_calc_stats.csv"
            write_header = not os.path.exists(local_filename)

            # Compute the next row counter by counting existing lines (header included).
            # Could be a bottle neck, maybe rewrite that in future with a better method.
            if os.path.exists(local_filename):
                try:
                    with open(local_filename, "r", newline="") as rf:
                        existing_lines = sum(1 for _ in rf)
                    # existing_lines includes the header line, so the next data row index equals existing_lines
                    row_counter = existing_lines
                except Exception:
                    row_counter = 1
            else:
                row_counter = 1

            with open(local_filename, "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                if write_header:
                    writer.writerow(
                        [
                            "",
                            "timestamp",
                            "hours",
                            "mu",
                            "poisson_value",
                            "fixed_return_value",
                            "loss",
                            "old_return_value",
                            "exact_return_value",
                        ]
                    )
                writer.writerow(
                    [
                        row_counter,
                        datetime.datetime.utcnow().isoformat(),
                        hours,
                        float(mu),
                        int(poisson_value),
                        int(return_value[0]),
                        float(
                            (poisson_value * self.TASK_SCALING_FACTOR) - return_value[0]
                        ),
                        int(poisson_value * self.TASK_SCALING_FACTOR),
                        float(poisson_value * self.TASK_SCALING_FACTOR),
                    ]
                )

        return return_value

    def solve_task(self, task: Task) -> float:
        """
        Solve a task and adjust member's motivation based on the task difficulty.

        Calculates how well the member's skills match the task difficulty and
        adjusts their motivation accordingly. Well-matched tasks increase motivation,
        while mismatched tasks (too easy or too hard) decrease it.

        Args:
            task (Task): The task being solved

        Returns:
            float: Error rate reduction factor (negative values indicate increased risk)
        """

        if not self.skill_type:
            raise ValueError("Member must have a skill type assigned to solve tasks")

        # Calculate the skill-difficulty match (0-100 scale)
        # Convert task difficulty (1-3) to percentage (33-100)
        difficulty_percent = (task.difficulty / 3) * 100
        skill_match = self.skill_type.development_quality - difficulty_percent

        # Calculate motivation adjustment
        # - Perfect match: positive adjustment
        # - Poor match: negative adjustment
        base_adjustment = 0.005
        difficulty_adjustment = (
            abs(skill_match) / 100
        ) * self.MOTIVATION_ADJUSTMENT_FACTOR
        motivation_change = round(base_adjustment - difficulty_adjustment, 4)

        # Apply motivation change with the upper limit of 1.0
        self.motivation = min(self.motivation + motivation_change, 1.0)

        # Return error rate adjustment factor
        # Negative values indicate increased risk of bugs
        return min(0, skill_match / 100)
