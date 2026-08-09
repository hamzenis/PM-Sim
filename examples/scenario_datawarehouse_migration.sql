insert into
    sim.app_templatescenario (id, name, story, studio_template_id)
values
    (
        1,
        'Datawarehouse Migration KT 1571220',
        '# Scenario Description
Our client, Monday Natural Products GmbH & Co. KG, is a long-established company specializing in the production and distribution of high-quality dietary supplements. In recent years, the company has gained recognition for developing innovative products and establishing strong industry partnerships. To further promote growth and optimize operations, the company has decided to invest in a new Data Warehouse System, which our team has been commissioned to develop. The Data Warehouse System is expected to accelerate data processing, automate data preparation, improve reporting, and support management in strategic decision-making. Our client places great emphasis on continuing to develop and maintain a high-quality IT infrastructure after we deliver the new Data Warehouse System. The final product is thus expected to meet their expectations and be completed with sufficient testing.
The client has prioritized the budgetary aspect to ensure the financial viability and success of the project. It is important to understand that delivering within the budget not only meets our client''s expectations but also fosters a potential long-term partnership based on trust and reliability. At the same time, our client needs the Data Warehouse implemented as soon as possible to continue using and developing their own IT systems that will be connected to the Data Warehouse. Until then, they will maintain their business operations with their current fully functional setup.',
        '6694f7f429fcd937523817da'
    );

insert into
    sim.app_skilltype (
        id,
        name,
        cost_per_day,
        error_rate,
        throughput,
        development_quality,
        management_quality,
        signing_bonus
    )
values
    (
        1,
        'Back-End-Developer Junior',
        171.15,
        0.06,
        2,
        35,
        30,
        0
    ),
    (
        2,
        'Back-End-Developer Senior',
        250.00,
        0.03,
        3,
        70,
        40,
        0
    ),
    (
        3,
        'Front-End-Developer Junior',
        164.60,
        0.05,
        2,
        25,
        30,
        0
    ),
    (
        4,
        'Front-End-Developer Senior',
        216.09,
        0.03,
        3,
        60,
        40,
        0
    ),
    (
        5,
        'Junior Consultant',
        182.69,
        0.06,
        2,
        20,
        55,
        0
    ),
    (
        6,
        'Senior Consultant',
        230.77,
        0.03,
        4,
        35,
        90,
        0
    );

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

insert into
    sim.app_event (
        id,
        text,
        trigger_type,
        trigger_value,
        trigger_comparator,
        template_scenario_id
    )
values
    (
        1,
        '# Budget Overrun
During the development of the data warehouse system, the project team receives an urgent notification from the database vendor about significant updates and changes to the licensing terms. The new license fees are nearly double the original cost, and the updates necessitate additional hardware to support the enhanced functionality. These unforeseen expenses threaten to exceed the budget. Despite extensive negotiations with stakeholders for additional funding, the project does not receive extra financial support. Under pressure, the team rallies together and revises its strategy to stay on track amidst the changed conditions.

This event has an impact on the following attributes:
+30% stress
-20% motivation
-15% familiarity
+45 new tasks',
        'time',
        15,
        'ge',
        1
    ),
    (
        2,
        '# Data Integration Issues
As the development of the Datawarehouse System progresses, the team encounters significant data integration issues during testing. Key datasets from the existing systems do not align correctly with the new warehouse, leading to data inconsistencies and errors.

A crisis meeting is convened immediately, and the team is tasked with identifying the root cause and finding solutions. The integration specialists work around the clock, reconfiguring data mappings and conducting extensive tests. Due to the specialized technical knowledge and novel solution approaches required for these data integration problems, the team faces tasks beyond their prior experience. This necessitates additional training and the assistance of experts.

After intensive efforts, the team succeeds in resolving the issues and ensuring a seamless data flow. 

This event has an impact on the following attributes:
-44.000,00 € budget
+35% stress
-25% motivation
-20% familiarity 
+40 new tasks
',
        'time',
        30,
        'ge',
        1
    ),
    (
        3,
        '# Performance Issues
As the Datawarehouse System neared completion, the team discovered significant performance issues during final testing. The system struggled to handle the real-world data load, causing severe slowdowns and errors. This setback was traced back to the earlier integration problems with the database provider''s updates and the new hardware that had been hastily implemented. The team worked tirelessly to optimize the system’s performance. After extensive reconfigurations and additional testing, they finally resolved the issues, ensuring the system could handle the demands of the daily operations.

This event has an impact on the following attributes:
-32.500,00 € budget
+40% stress
-20% motivation
-10% familiarity 
+47 new tasks

',
        'time',
        45,
        'ge',
        1
    );

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

insert into
    sim.app_managementgoal (
        id,
        budget,
        duration,
        easy_tasks,
        medium_tasks,
        hard_tasks,
        tasks_predecessor_p,
        template_scenario_id
    )
values
    (1, 250000, 60, 125, 250, 155, 0.3, 1);

insert into
    sim.app_scorecard (
        id,
        budget_limit,
        time_limit,
        quality_limit,
        budget_p,
        time_p,
        quality_k,
        template_scenario_id
    )
values
    (1, 100, 100, 100, 1, 1, 1, 1);

insert into
    sim.app_simulationfragment (id, `index`, text, last, template_scenario_id)
values
    (
        1,
        0,
        '# Project Information
Project Duration: 60 Days
Project Costs: 250.000,00 €

Quantity and difficulty of tasks:
* Easy Tasks: 125
* Medium Tasks: 250
* Hard Tasks: 155

# Please note 
## A) Procedure
The following simplified sequence according to software engineering and project management principles for handling tasks should be followed to ensure that the software is developed, tested, and integrated correctly:

1. Task Implementation:
Developers implement and process assigned tasks. During this development phase, testing the software is not possible, meaning bugs will not be found, nor will the software be integrated into the overall system. This can result in reduced quality.

2. Unit Testing:
Create and execute unit tests to ensure that individual components function correctly. While this may reduce task throughput (it is possible that your team is not able to work on any planned tasks at all), it can increase quality, depending on the team''s motivation and stress levels.

3. Bug Fixing:
Fix bugs found during implementation or unit testing. Addressing these issues requires the team to take on additional, unplanned tasks, which can improve quality, again depending on motivation and stress levels.

4. Integration and Testing:
Integrate the developed components into the overall system and conduct integration tests to ensure that individual components work together correctly. This integration testing will occupy an entire day, reducing task throughput but ultimately improving the software''s quality.

Be aware that tasks can fail during integration testing, resulting in them being listed as “remaining tasks” again. They will have to be redone and go through the development and testing process again.

The number of successfully integrated tasks, the duration, and the amount of money spent directly impact the final score. Attributes such as motivation, stress, and familiarity only contribute indirectly by influencing the efficiency of your employees. Here, "familiarity" refers to how well the developers or workers understand and are acquainted with the tasks.


## B) Factors
Motivation, stress, and familiarity with tasks are critical factors that significantly influence the throughput of potentially processable tasks in software development. Maintaining high motivation, managing stress effectively, and ensuring familiarity with tasks are essential for maximizing the throughput of processable tasks. Balancing these factors can lead to a more productive and efficient development process, ultimately contributing to the successful completion of projects.

### Motivation:
High Motivation:
When team members are highly motivated, they tend to work more efficiently and with greater enthusiasm. This leads to higher productivity and an increased throughput of tasks. Motivated individuals are more likely to take initiative, solve problems quickly, and maintain a high level of focus, all of which contribute to a smoother workflow and faster task completion.

Low Motivation:
Conversely, low motivation can result in decreased productivity and a lower throughput of tasks. Team members may lack the drive to tackle challenges, leading to procrastination, errors, and a slower pace of work.

Influencing Factors:
Meetings and training can increase motivation by providing clear goals, feedback, and learning opportunities.

### Stress:
High Stress:
High stress levels can severely impact task throughput. Stress can lead to mental fatigue, decreased concentration, and a higher incidence of mistakes. As stress increases, the ability to manage tasks efficiently diminishes, resulting in slower progress and a reduction in overall task throughput.

Low Stress:
When stress levels are low, team members can concentrate better and make more rational decisions. This conducive environment helps maintain a steady workflow, allowing for consistent progress and a higher throughput of tasks. Low stress also reduces the likelihood of burnout, enabling sustained productivity over time.

Influencing Factors:
Team events can significantly reduce stress, fostering a relaxed and supportive environment.

### Familiarity with Tasks:
High Familiarity:
When team members are familiar with the tasks at hand, they can execute them more quickly and with greater confidence. Familiarity reduces the time spent on learning and understanding requirements, allowing for a more streamlined workflow and higher throughput. Experienced team members are also better at anticipating and mitigating potential issues, further enhancing productivity.

Low Familiarity:
Low familiarity with tasks can slow down the process significantly. Team members may need additional time to understand the requirements, learn new tools or technologies, and develop suitable solutions. This learning curve can result in a lower throughput of tasks as more time is devoted to gaining the necessary knowledge and skills.

Influencing Factors:
Meetings and training enhance familiarity by improving knowledge and skills, facilitating a smoother workflow.



---
If you have any other questions, such as about the functionalities and features of the Simulation, or if you want to reread the scenario description and project information, you can use the “Open Story” and “Help” buttons in the upper left corner.

',
        1,
        1
    );

insert into
    sim.app_simulationend (
        id,
        `limit`,
        `type`,
        `limit_type`,
        `simulation_fragment_id`
    )
values
    (1, '60', 'duration', 'ge', 1);

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