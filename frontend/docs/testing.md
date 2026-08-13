# Frontend testing

Run checks from `frontend/`:

```bash
npm ci
npm ls --depth=0
npm run lint
npm test
npm run build
```

Place API mapping tests beside modules in `src/api/` and component tests beside their components.
Test loading, success, empty, error, keyboard, and role-dependent paths. The `npm test` command runs
Vitest once rather than starting watch mode.

## Visual regression review

Playwright covers high-value professor and student pages at desktop and mobile widths. Install its
pinned browser with `npx playwright install chromium`, then run `npm run test:visual`. Inspect every
diff before running `npm run test:visual:update`; review and commit intentional snapshots with the UI
change. Never replace snapshots merely to make CI pass.

## Related documentation

- [Accessibility](accessibility.md)
- [API integration](api-integration.md)
- [Backend testing](../../backend/docs/testing.md)
