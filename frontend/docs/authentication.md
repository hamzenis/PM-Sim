# Authentication

Authentication uses an HTTP-only session cookie. JavaScript cannot and must not read it; the shared
API client sends credentials with requests. Never store session tokens or passwords in local storage,
session storage, application state, logs, or rendered error details.

Role gates distinguish public, authenticated, and professor-only routes. Treat a rejected session as
an authentication transition: clear user presentation state and return to the login workflow. In
production, use HTTPS and compatible frontend/API origins so cookie and CORS policies permit
credentialed requests.

## Related documentation

- [Backend HTTP API: authentication](../../backend/docs/api.md#authentication-cookies-and-cors)
- [API integration](api-integration.md)
- [Routing and role gates](routing.md)
