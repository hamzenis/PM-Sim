# simulation.py

This module orchestrates the simulation of scenario fragments in the backend. It integrates with many utility modules and models, handling requests, team member changes, workpack processing, and simulation events.

## Functions

### simulate(req, session: CachedScenario)
Simulates a scenario fragment based on the request and session state. Handles member changes, workpack actions, team events, and integration tests. Raises exceptions for invalid actions or member changes.
- **Connections:** Uses `WorkpackStatus` from `simulation_util`, member management from `member_util`, and scenario state from `user_scenario_util`.

### continue_simulation(session: CachedScenario, req)
Processes a simulation request and returns a `ScenarioResponse`. Maps request types to handler functions:
- `SIMULATION`: `simulate`
- `QUESTION`: `handle_question_answers` (from `question_util`)
- `MODEL`: `handle_model_request` (from `scenario_util`)
- `START`: `handle_start_request` (from `scenario_util`)
- `EVENT`: `handle_event_request` (from `scenario_util`)
- `END`: `handle_end_request` (from `scenario_util`)

## Connections
- Imports and uses functions from `question_util`, `scenario_util`, `task_util`, `member_util`, `user_scenario_util`, and `simulation_util`.
- Relies on models such as `Event`, `QuestionCollection`, `SimulationFragment`, `ModelSelection`, `SkillType`, and `Member`.
- Handles exceptions from `exceptions.py`.
- Integrates with Django ORM for member and scenario management.

## Notes
- The file is central to simulation logic and acts as a hub for connecting various utility modules and models.
- Exception handling is robust, ensuring simulation integrity.
