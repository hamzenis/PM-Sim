# task_util.py

This module provides utilities for retrieving and summarizing the status of tasks in a scenario.

## Functions

### get_tasks_status(session: CachedScenario) -> TasksStatusDTO
Returns a DTO summarizing the status of tasks for the current scenario, including counts for todo, done, unit tested, integration tested, and bugs.
- **Connections:** Uses `TasksStatusDTO` and session's cached tasks.

### get_tasks_status_detailed(scenario_id: int) -> Dict[str, int]
Returns a detailed dictionary of task statuses, including those not visible to the team/user.
- **Connections:** Uses `TaskStatus` model methods for various status counts.

### get_tasks_customer_view(scenario_id: int) -> Dict[str, int]
Returns a dictionary of task statuses as seen from the customer's perspective (accepted/rejected).
- **Connections:** Uses `TaskStatus` model methods for customer view.

## Notes
- Used to provide task status summaries for different user roles and views.
