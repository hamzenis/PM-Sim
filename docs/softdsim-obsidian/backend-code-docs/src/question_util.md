# question_util.py

This module provides utilities for handling question collections and processing question answers within a scenario.

## Functions

### get_question_collection(scenario)
Fetches the relevant `QuestionCollection` for the scenario and sorts its questions by index. Returns a `QuestionCollectionDTO`.
- **Connections:** Uses `QuestionCollection`, `QuestionCollectionSerializer`, and `QuestionCollectionDTO`.

### handle_question_answers(req, session: CachedScenario)
Processes answers to questions, updating the scenario's question points. Ensures points do not go below zero.
- **Connections:** Uses `Answer` model and updates `session.scenario.question_points`.

## Notes
- Used in simulation to process user answers and update scenario scoring.
- Handles exceptions and logs warnings for errors during answer processing.
