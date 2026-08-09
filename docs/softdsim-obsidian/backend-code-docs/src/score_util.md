# score_util.py

This module provides functions for calculating various scores in a user scenario, including quality, time, budget, and question scores.

## Functions

### [[calc_scores]](scenario: UserScenario, tasks: CachedTasks) -> dict
Calculates and returns a dictionary of scores for quality, time, budget, and questions. Also computes a total score based on all components.
- **Connections:** Uses `ScoreCard`, `ManagementGoal`, `Answer`, and scenario/task models.

### [[calc_time_score]](actual_time, scheduled_time, limit, p) -> int
Calculates the time score based on actual vs. scheduled time, applying a penalty if exceeded.

### [[calc_budget_score]](cost, budget, limit, p) -> int
Calculates the budget score based on actual cost vs. budget, applying a penalty if exceeded.

### [[calc_quality_score]](tasks, err, limit, k) -> int
Calculates the quality score based on the number of tasks and errors.

## Notes
- Used to evaluate scenario performance and provide feedback to users.
- Integrates with models for score cards, management goals, and answers.
