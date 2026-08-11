from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class ScenarioConfig(models.Model):
    """
    Configuration for a simulation scenario.

    Encapsulates tunable parameters that influence agent behaviour, productivity,
    training progression, and event costs used by the simulation engine.

    Fields
    - name (str): Unique identifier for this configuration.
    - stress_weekend_reduction (float >= 0): Fractional reduction in stress on
        weekends (default 0.15).
    - stress_overtime_increase (float): Additional stress applied when working
        overtime (default 0.05).
    - stress_error_increase (float): Stress added per error occurrence
        (default 0.02).
    - done_tasks_per_meeting (int): Baseline tasks completed during a meeting
        (default 50).
    - train_skill_increase_rate (float): Skill increase rate from training per
        training unit (default 0.1).
    - cost_member_team_event (float): Monetary cost per member for team events
        (default 500.0).
    - randomness (str): Level of simulation stochasticity; expected values:
        'full', 'semi', 'none' (default 'full').
    """

    name = models.CharField(max_length=32, unique=True)
    stress_weekend_reduction = models.FloatField(
        default=0.15, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    stress_overtime_increase = models.FloatField(default=0.05)
    stress_error_increase = models.FloatField(default=0.02)
    done_tasks_per_meeting = models.IntegerField(default=50)
    train_skill_increase_rate = models.FloatField(default=0.1)
    cost_member_team_event = models.FloatField(default=500.0)
    randomness = models.TextField(default="full")  # 'full', 'semi', 'none'
