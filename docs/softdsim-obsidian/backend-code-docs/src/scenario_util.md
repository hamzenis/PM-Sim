# scenario_util.py

This module provides utilities for handling scenario requests, validating indexes, and extracting actions/effects from scenario components.

## Functions

### check_indexes(data) -> bool
Checks if the indexes of template scenario components are correct and sequential.

### create_correct_request_model(request) -> ScenarioRequest
Creates the correct request model object based on the request type.

### handle_model_request(req, session: CachedScenario)
Updates the scenario's model based on the request.

### handle_start_request(req, session: CachedScenario)
Placeholder for handling start requests.

### handle_end_request(req, session: CachedScenario)
Marks the scenario as ended.

### handle_event_request(req, session: CachedScenario)
Placeholder for handling event requests.

### get_actions_from_fragment(next_component) -> List[ActionDTO]
Extracts actions from a scenario component and returns them as a list of DTOs.

### request_type_matches_previous_response_type(scenario, req) -> bool
Checks if the request type matches the previous response type in scenario history.

### get_effects_from_event(event)
Extracts effects from an event and returns them as a list of DTOs.

## Notes
- Used throughout simulation logic to process and validate scenario requests and actions.
- Connects with models and DTOs for scenario management.
