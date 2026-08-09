insert into
    sim.app_eventeffect (
        id,
        type,
        value,
        easy_tasks,
        medium_tasks,
        hard_tasks,
        event_id
    )
values
    (1, 'budget', 0, 0, 0, 0, 1),
    (2, 'duration', 0, 0, 0, 0, 1),
    (3, 'stress', 0.3, 0, 0, 0, 1),
    (4, 'motivation', -0.2, 0, 0, 0, 1),
    (5, 'familiarity', -0.15, 0, 0, 0, 1),
    (6, 'tasks', 0, 0, 25, 20, 1),
    (7, 'budget', -44000, 0, 0, 0, 2),
    (8, 'duration', 0, 0, 0, 0, 2),
    (9, 'stress', 0.35, 0, 0, 0, 2),
    (10, 'motivation', -0.25, 0, 0, 0, 2),
    (11, 'familiarity', -0.2, 0, 0, 0, 2),
    (12, 'tasks', 0, 10, 18, 12, 2),
    (13, 'budget', -32500, 0, 0, 0, 3),
    (14, 'duration', 0, 0, 0, 0, 3),
    (15, 'stress', 0.4, 0, 0, 0, 3),
    (16, 'motivation', -0.2, 0, 0, 0, 3),
    (17, 'familiarity', -0.1, 0, 0, 0, 3),
    (18, 'tasks', 0, 11, 22, 14, 3);