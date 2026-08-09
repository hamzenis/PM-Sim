# Overview of the `src` Folder

The `src` folder is the core of the [[backend]] simulation logic for this project. It contains modules and utilities that drive the main features and algorithms of the simulation system.

## Structure and Purpose

- [**simulation.py**](backend-code-docs/src/simulation.md): Implements the main simulation engine, orchestrating scenario progression, team actions, and event handling.
- [**util/**](backend-code-docs/src/util.md): Contains utility modules for specific tasks, such as:
  - [`user_scenario_util.py`](backend-code-docs/src/user_scenario_util): Manages scenario state and progression.
  - [`question_util.py`](backend-code-docs/src/question_util.md): Handles question collections and answer processing.
  - [`score_util.py`](backend-code-docs/src/score_util.md): Calculates scenario scores (quality, time, budget, etc.).
  - [`task_util.py`](backend-code-docs/src/task_util.md): Summarizes and manages task statuses.
  - [`scenario_util.py`](backend-code-docs/src/scenario_util.md): Processes scenario requests and extracts actions/effects.
  - [`simulation_util.py`](backend-code-docs/src/simulation_util.md): Advanced helpers for simulation fragments and team adjustments.
  - [`member_util.py`](member_util.md): 

## Key Responsibilities
- Running and managing project management simulations.
- Processing user actions, scenario events, and team changes.
- Calculating scores and outcomes based on scenario data.
- Providing helper functions for tasks, questions, and scenario state.

## Connections
- Integrates with models, serializers, and DTOs from other parts of the backend.
- Used by higher-level application logic to execute and manage simulations.

---
This folder is essential for the backend's simulation features and contains the main logic for scenario execution and analysis.
