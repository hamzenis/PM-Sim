# Frontend deployment

Create production assets from `frontend/`:

```bash
npm ci
npm run build
```

Publish `dist/` on a static host or web server. Configure an SPA fallback that rewrites unknown
non-file paths to `index.html`; otherwise refreshing a route such as `/simulations/example` returns
`404`.

For a separately hosted backend, set `VITE_API_BASE_URL` to its complete origin before building. Use
HTTPS, configure backend CORS for the exact frontend origin, and permit credentialed requests. Do not
embed secrets in `VITE_` variables because Vite includes them in browser assets.

## Related documentation

- [Authentication](authentication.md)
- [API integration](api-integration.md)
- [Backend operations](../../backend/docs/sqlite-operations.md)
