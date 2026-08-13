# Authored scenario content

Scenario authors can add staged events, questions, acknowledgements, and effects to a scenario
revision. Definitions live in the scenario payload; runtime resolution and persistence live under
`app/authored_content/`. Published revisions are immutable so an assigned simulation run retains the
content its professor reviewed.

## Authoring workflow

1. Start from a JSON file in `scenario_examples/` and preserve stable content identifiers.
2. Define visibility and trigger conditions using the supported schema.
3. Add answer choices or acknowledgement behaviour and any permitted effects.
4. Load the scenario as a draft, validate it, and test it over representative deterministic seeds.
5. Publish only after reviewing both professor and student presentations.

Authored content is presentation and decision context around the simulation. It must not bypass the
engine boundary or embed executable code. Use the comprehensive example for supported shapes and the
basic project for a minimal scenario.

## Related documentation

- [Simulation engine](simulation-engine.md)
- [HTTP API: authored content](api.md#simulation-runs-and-authored-content)
- [ADR 0001: authored scenario content](adr/0001-authored-scenario-content.md)
- [ADR 0002: content persistence and idempotency](adr/0002-content-persistence-idempotency.md)
- [Frontend API integration](../../frontend/docs/api-integration.md)
