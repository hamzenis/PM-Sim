from fastapi import APIRouter

from app.scenarios.models import ScenarioDefinition

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("/validate", response_model=ScenarioDefinition)
def validate_scenario(scenario: ScenarioDefinition) -> ScenarioDefinition:
    """Validate and normalize a scenario without persisting it."""
    return scenario
