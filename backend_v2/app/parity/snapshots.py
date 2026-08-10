from dataclasses import asdict

from app.simulation.models import SimulationState, WeeklyDecision
from app.simulation.state_codec import state_to_dict
from app.simulation.turn import TurnResult


def turn_snapshot(
    *,
    initial_state: SimulationState,
    decision: WeeklyDecision,
    result: TurnResult,
) -> dict[str, object]:
    """Create the stable JSON-like contract used by whole-turn golden tests."""
    snapshot = {
        "initial_state": state_to_dict(initial_state),
        "decision": asdict(decision),
        "result": {
            "state": state_to_dict(result.state),
            "activity_hours": asdict(result.activity_hours),
            "meeting_hours": result.meeting_hours,
            "training_hours": result.training_hours,
            "events": [asdict(event) for event in result.events],
        },
    }
    return _json_value(snapshot)


def _json_value(value: object) -> object:
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_value(item) for item in value]
    return value
