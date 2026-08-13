# Backend documentation

This index is the source of truth for documentation about the FastAPI service, persistence, and
simulation engine. Begin with the [backend orientation and quick start](../README.md).

| Topic | Guide | Audience |
| --- | --- | --- |
| Setup and development | [Development and local operation](development.md) | Contributors and backend developers |
| Architecture | [Backend architecture](architecture.md) | Backend developers |
| API | [HTTP API](api.md) | API consumers and frontend developers |
| Simulation engine | [Simulation engine](simulation-engine.md) | Backend developers and scenario authors |
| Scenario authoring | [Scenario authoring and validation](scenario-authoring.md) | Scenario authors and professors |
| Authored-content architecture | [Authored scenario content](authored-content.md) | Backend developers |
| Data model | [Data model](data-model.md) | Backend developers and operators |
| Operations | [SQLite classroom operations](sqlite-operations.md) | Operators |
| Deployment | [Backend deployment](deployment.md) | Operators and maintainers |
| Testing | [Backend testing](testing.md) | Contributors and backend developers |
| Decisions | [Architecture decision records](adr/README.md) | Maintainers |

## Documentation conventions

- Use sentence-case headings and fenced `bash` blocks for commands.
- Use repository-relative Markdown links and PM-Sim's terms: **scenario**, **class**, **simulation
  run**, **weekly turn**, **professor**, and **student**.
- Write lifecycle statuses as code values (for example, `draft` or `submitted`) and pair them with
  their human-readable UI label when one exists.
- End a topic guide with **Related documentation** when another component must change with it.

## Related documentation

- [Frontend documentation](../../frontend/docs/README.md)
- [Repository documentation map](../../README.md#documentation-map)
