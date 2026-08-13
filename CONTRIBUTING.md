# Development Workflow

Create an issue for every planned feature, bug, and idea, and assign it directly to the project board. All open issues collectively form the backlog. Issues should be scoped narrowly enough to be completed within a short period (a few hours to no more than two days). Split larger tasks into multiple self-contained issues. Each issue should include a brief description, reproduction or implementation steps, acceptance criteria, and labels.

## Branches

Work on each feature in its own branch. Use the following naming convention:

```
type/issuenr-kurze-beschreibung
```

where ```issuenr``` is the issue number and ```type``` is one of ```feature``` (implementing a new feature), ```fix``` (fixing a bug or error), ```refactor``` (rewriting code without adding new functionality), or ```task``` (all other work). Example:

```
feature/127-Adding-api-delete-endpoint
task/123-Update-dependencies
refactor/45-Improve-code-structure
fix/78-Fix-login-bug
```

## Semantic Commit Messages


Commit messages should be clear and concise and follow this format:

Format: `<type>: #IssueNumber <subject>`

Optionally, add a longer explanation after a blank line.

The `#` symbol is important because it allows GitHub to associate the commit with the issue automatically. Example commit message:

### Example

```
feat: #73 add hat wobble
^--^  ^------------^
|     |
|     +-> Summary in present tense.
|
+-------> Type: chore, docs, feat, fix, refactor, style, or test.
```

### Type Categories:

- `feat`: (new feature for the user, not a new feature for build script)
- `fix`: (bug fix for the user, not a fix to a build script)
- `docs`: (changes to the documentation)
- `style`: (formatting, missing semi colons, etc; no production code change)
- `refactor`: (refactoring production code, eg. renaming a variable)
- `test`: (adding missing tests, refactoring tests; no production code change)
- `chore`: (updating grunt tasks etc; no production code change)


## Pull Requests

Once an issue has been resolved, create a pull request to merge the branch into the *develop* branch. The PR must receive at least one approval and pass all tests before it can be merged.

### Pull Request Documentation Checklist

Each PR must either list the updated documentation files in its description or explicitly explain
why no documentation changes are required. Before approval, the author confirms:

- [ ] **Change scope reviewed:** New or modified backend routes, request/response models,
  configuration values, CLI commands, database migrations, the scenario schema, simulation rules,
  frontend routes, API adapters, UI conventions, and deployment behavior are documented in the
  relevant references and workflows.
- [ ] **Examples executed:** Commands were run from the specified working directory; request,
  response, and configuration examples match the implementation and contain no secrets or personal
  data.
- [ ] **Repository check passed:** `uv run --project backend python scripts/check_docs.py` checks
  relative links, Markdown structure, unique heading anchors, code fences, backend and frontend
  routes, and the scenario examples.
- [ ] **Cross-references reviewed:** Backend, frontend, operations, and ADR documents link to one
  another when changes span multiple areas.
- [ ] **Generated reference handled:** No generated artifact was committed, or the intentionally
  versioned reference described below was updated reproducibly.

### Review Responsibilities

At least one person from the affected area must review the changes. Until GitHub teams are listed in
`CODEOWNERS`, the PR must explicitly name this role, and the repository team must assign a specific
person.

| Area | Required reviewer role | Additional review requirements |
| --- | --- | --- |
| `backend/app/api`, API contract, authentication | Backend/API owner | Requests/responses, commands, security and privacy guidance, links to frontend integration |
| Scenario schema, simulation, migrations, CLI | Domain/data owner | Validated examples, reproducibility, compatibility, and migration/rollback guidance |
| `frontend/src`, frontend documentation | Frontend/UI owner | Route matrix, API adapters, UI/accessibility conventions, screenshots where necessary |
| Deployment, configuration, CI | Operations/security owner | Executable commands, secrets/headers, upgrade/rollback, and operational cross-references |
| Documentation/ADR only | Owner of the documented area | Examples, security context, relative links, and current ADR references |

Reviewers must run the relevant commands themselves or inspect the CI output and explicitly confirm
**commands, examples, security guidance, and cross-references** in their review.

## Maintaining Documentation

- Cross-cutting guidance belongs in the root [`README.md`](README.md). Backend topics belong under
  [`backend/docs/`](backend/docs/README.md), and frontend topics under
  [`frontend/docs/`](frontend/docs/README.md). The respective `README.md` files should remain concise
  introduction and quick-start pages.
- Changes to behavior, API contracts, configuration, the data model, user workflows, or operations
  must update the affected guides in the same pull request. Related backend and frontend topics must
  link to each other under **Related documentation**.
- Commands and code examples must be run from the specified working directory or checked against
  the current interface. Example payloads must be validated, and relative links must be checked for
  reachable targets before review.

### Generated Documentation

Generated OpenAPI, schema, diagram, or report files must remain outside version control (temporarily
under `/tmp` or as CI artifacts) unless the project intentionally introduces a generated API
reference, including an owner and diff review process, in a dedicated PR. The current authoritative
API reference is the manually reviewed endpoint inventory in
[`backend/docs/api.md`](backend/docs/api.md). To compare it locally, regenerate the runtime
reference with:

```bash
cd backend
uv run uvicorn app.main:app
# in a second terminal:
curl -fsS http://127.0.0.1:8000/openapi.json > /tmp/pm-sim-openapi.json
```

If a generated reference is versioned in the future, its header must state this exact generation
command, including the tool version. Changes must be made only by rerunning this command, never by
editing the reference manually.

### Regular Documentation Audit

Create an audit issue once per quarter and before every major release using this checklist:

- [ ] compare documented runtime, package, and tool versions against lockfiles and CI;
- [ ] compare screenshots against the current UI, exclude sensitive test data, and replace or remove
  outdated images;
- [ ] mark historical migration, UX, and test reports as still relevant, or archive or remove them;
- [ ] compare behavior, transition paths, and compatibility guidance marked as deprecated against
  the code, and remove expired guidance;
- [ ] check the ADR index and all ADR links for reachable targets, current status, and superseding
  ADRs;
- [ ] run `uv run --project backend python scripts/check_docs.py` and record the findings in the
  audit issue.
