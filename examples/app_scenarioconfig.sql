insert into
    sim.app_scenarioconfig (
        id,
        name,
        stress_weekend_reduction,
        stress_overtime_increase,
        stress_error_increase,
        done_tasks_per_meeting,
        train_skill_increase_rate,
        cost_member_team_event,
        randomness
    )
values
    (
        1,
        'conf_low_stress',
        0.2,
        0.04,
        0.02,
        50,
        0.1,
        500,
        'full'
    );