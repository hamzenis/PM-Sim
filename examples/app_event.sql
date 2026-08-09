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