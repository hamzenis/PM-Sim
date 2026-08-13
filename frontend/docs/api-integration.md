# API integration

All HTTP requests go through `src/api/client.js`. Domain adapters in `src/api/auth.js`,
`scenarios.js`, `classes.js`, `simulations.js`, and `audit.js` own endpoint paths and map transport
shapes into UI-friendly values. Components must not call `fetch` directly.

Relative `/api` requests use the Vite development proxy. For a separate API origin, set the complete
origin in `VITE_API_BASE_URL`; the backend must allow that origin and credentialed requests.

When an endpoint changes, update its domain adapter, adjacent adapter tests, affected loading/error
states, and the backend API guide together. Preserve server status values internally, but convert them
to consistent human-readable labels at the presentation boundary.

## Related documentation

- [Backend HTTP API](../../backend/docs/api.md)
- [Backend authored-content endpoints](../../backend/docs/api.md#answer-or-acknowledge-authored-content)
- [Authentication](authentication.md)
- [Frontend testing](testing.md)
