# user_scenario_util.py

This module provides utility functions for managing and updating the state of user scenarios.

## Functions

### get_scenario_state_dto(scenario: UserScenario) -> ScenarioStateDTO
Serializes the scenario state and returns a DTO for further processing.
- **Connections:** Uses `ScenarioStateSerializer` and `ScenarioStateDTO`.

### increase_scenario_component_counter(scenario, increase_by=1)
Increments the `component_counter` in the scenario state and saves the state.
- **Connections:** Directly modifies the scenario's state.

### increase_scenario_step_counter(scenario, increase_by=1)
Increments the `step_counter` in the scenario state and saves the state.
- **Connections:** Directly modifies the scenario's state.

## Notes
- All functions operate on the scenario's state and persist changes.
- Used by simulation logic to track scenario progress.
