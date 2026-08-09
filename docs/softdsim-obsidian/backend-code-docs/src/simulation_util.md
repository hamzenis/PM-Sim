# simulation_util.py

This module provides advanced utilities for managing simulation fragments, scenario components, and team adjustments during simulation.

## Classes

### EventEffectDTO
A data transfer object for event effects, including value and task counts.

### WorkpackStatus
Tracks meetings per day and remaining trainings for a workpack. Calculates meeting distribution across days.

## Functions

### find_next_scenario_component(session: CachedScenario)
Finds the next scenario component (question collection, simulation fragment, or model selection) based on the current counter. Recursively skips simulation fragments if the scenario is ended.
- **Connections:** Uses models for scenario components and the `end_of_simulation` function.

### end_of_fragment(session: CachedScenario) -> bool
Determines if the end condition of a simulation fragment is reached, based on type and limit.

### end_of_simulation(session: CachedScenario) -> bool
Checks if the scenario is ended or if there are no remaining tasks.

### adjust_team_stress(session, event_effect)
Adjusts the stress level of all team members based on an event effect.

### adjust_team_motivation(session, event_effect)
Adjusts the motivation level of all team members based on an event effect.

### adjust_team_familiarity(session, event_effect)
Adjusts the familiarity level of all team members based on an event effect.

### adjust_budget(session, event_effect)
Adjusts the scenario's budget based on an event effect.


### [[add_tasks]](session, event_effect)


## Notes
- Used by simulation logic to manage scenario progression and team state.
- Integrates with models for scenario, team, and tasks.
