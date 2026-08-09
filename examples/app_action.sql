insert into
    sim.app_action (
        id,
        title,
        lower_limit,
        upper_limit,
        simulation_fragment_id
    )
values
    (1, 'bugfix', null, null, 1),
    (2, 'unittest', null, null, 1),
    (3, 'integrationtest', null, null, 1),
    (4, 'meetings', 0, 5, 1),
    (5, 'teamevent', null, null, 1),
    (6, 'training', 0, 3, 1),
    (7, 'overtime', null, null, 1);