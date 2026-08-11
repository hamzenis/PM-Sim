from app.dto.request import Workpack


"""
User parameters for work packages where 12 Workpacks are used.
This user parameter set focuses on a realistic scenario where various factors such as
bug fixes, unit tests, integration tests, meetings, training and team events are used.
Trimmed to get the best outcome and a realistic simulation.

Based on this idea:

Week 1–2: Setup & core development
Week 3–6: Feature development with moderate QA
Week 7–9: Heavy testing, integration, stabilization
Week 10: Buffer, hardening, final fixes
Week 11: Release prep
Week 12: Cool-down, documentation, handover
"""
USERPARAMETERS_EXAMPLE = [
    Workpack(  # 0
        bugfix=False,
        unittest=False,
        integrationtest=False,
        meetings=4,
        training=2,
        teamevent=False,
        overtime=0,
    ),
    Workpack(  # 1
        bugfix=False,
        unittest=False,
        integrationtest=False,
        meetings=3,
        training=2,
        teamevent=False,
        overtime=0,
    ),
    Workpack(  # 2
        bugfix=False,
        unittest=True,
        integrationtest=False,
        meetings=2,
        training=2,
        teamevent=True,
        overtime=-1,
    ),
    Workpack(  # 3
        bugfix=False,
        unittest=True,
        integrationtest=False,
        meetings=2,
        training=2,
        teamevent=False,
        overtime=-1,
    ),
    Workpack(  # 4
        bugfix=True,
        unittest=True,
        integrationtest=False,
        meetings=3,
        training=2,
        teamevent=True,
        overtime=-1,
    ),
    Workpack(  # 5
        bugfix=True,
        unittest=True,
        integrationtest=False,
        meetings=2,
        training=2,
        teamevent=False,
        overtime=1,
    ),
    Workpack(  # 6
        bugfix=True,
        unittest=True,
        integrationtest=True,
        meetings=2,
        training=1,
        teamevent=True,
        overtime=0,
    ),
    Workpack(  # 7
        bugfix=True,
        unittest=True,
        integrationtest=True,
        meetings=3,
        training=2,
        teamevent=False,
        overtime=2,
    ),
    Workpack(  # 8
        bugfix=True,
        unittest=False,
        integrationtest=True,
        meetings=2,
        training=0,
        teamevent=True,
        overtime=2,
    ),
    Workpack(  # 9
        bugfix=True,
        unittest=True,
        integrationtest=False,
        meetings=2,
        training=0,
        teamevent=False,
        overtime=1,
    ),
    Workpack(  # 10
        bugfix=True,
        unittest=False,
        integrationtest=False,
        meetings=4,
        training=0,
        teamevent=True,
        overtime=1,
    ),
    Workpack(  # 11
        bugfix=False,
        unittest=False,
        integrationtest=False,
        meetings=2,
        training=0,
        teamevent=False,
        overtime=-1,
    ),
]
