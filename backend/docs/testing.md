# Backend testing

Run the backend checks from `backend/`:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

Put tests in `tests/` near the domain named by the production module. Prefer focused unit tests for
engine rules and service tests for transactions. API tests should exercise authentication, role
checks, response status, and error shape. Simulation tests must use fixed seeds and assert replay
determinism rather than relying on incidental random output.

When changing migrations, test both a new database and an upgrade of representative existing data.
When changing example scenarios or authored content, load the example and run representative batch
seeds as well as the focused test suite.

## Related documentation

- [Development and local operation](development.md)
- [Simulation engine](simulation-engine.md)
- [Frontend testing](../../frontend/docs/testing.md)
