# Existing frontend migration guide

## Goal

Keep the existing frontend usable while replacing its legacy-backend integration incrementally.
Do not begin with a visual rewrite. First introduce a stable API boundary, then migrate one
workflow at a time and retain existing components wherever their presentation still works.

The backend contract is documented in [`api.md`](api.md). During development, use the generated
OpenAPI document at `http://127.0.0.1:8000/openapi.json` to confirm exact schemas.

## Recommended migration sequence

1. **Inventory the current frontend.** Record routes, stores, API calls, legacy response shapes,
   role checks, and screens that directly depend on legacy simulation fields.
2. **Add one API client module.** All HTTP traffic should pass through this module; components
   should not call `fetch` or Axios directly.
3. **Migrate session restoration and login.** Make `/api/auth/me` the initial session check and
   add the login/logout/password flows.
4. **Migrate professor scenario management.** Adapt the existing editor to validate, create
   revisions, publish, and archive through the new endpoints.
5. **Migrate classes and students.** Reuse existing screens while replacing their data loaders
   and mutations.
6. **Migrate the student dashboard.** Load assigned revisions and existing runs.
7. **Migrate weekly simulation play.** Introduce the new percentage allocation decision model,
   run versions, and idempotent submissions.
8. **Migrate professor results and audit views.** Keep full run audit data out of student stores.
9. **Remove legacy adapters only after every route uses the new API client.**

## API client requirements

The client should provide a small typed method for each backend operation and share one request
function with these behaviors:

- resolve URLs relative to a configurable API base URL;
- send `Accept: application/json`;
- set `Content-Type: application/json` only when a JSON body exists;
- use `credentials: "include"` so the HTTP-only session cookie is sent;
- parse `{"detail":"..."}` errors into one frontend error type;
- treat a `204` response as `undefined` rather than attempting JSON parsing;
- redirect to or display login after `401`;
- show a role/access message for `403` instead of treating it as logout;
- expose `409` distinctly for stale simulation state;
- preserve field-level `422` validation details for forms.

Example transport shape in TypeScript:

```ts
export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
```

This is an integration example, not a requirement to change the frontend's existing framework
or state library.

## Session and role state

On application startup:

1. call `GET /api/auth/me`;
2. store only the returned `id`, `username`, and `role`;
3. render professor or student routes from `role`;
4. treat `401` as an anonymous session;
5. never store the cookie, a token, or a password in browser storage.

After login, use the returned user object immediately. After logout or password change, clear
all user-specific cached data. A password change revokes sessions, so the frontend must return
to login.

## Professor workflow mapping

| Frontend capability | Backend operation |
| --- | --- |
| List scenarios | `GET /api/scenarios` |
| Validate editor form | `POST /api/scenarios/validate` |
| Save new scenario | `POST /api/scenarios` |
| Save changes | `POST /api/scenarios/{id}/revisions` |
| Publish | `POST /api/scenarios/{id}/revisions/{number}/publish` |
| Archive | `POST /api/scenarios/{id}/archive` |
| List/create/rename/archive classes | `/api/classes` operations |
| Manage students | `/api/classes/{id}/students` operations |
| Assign scenarios | `/api/classes/{id}/scenarios` operations |
| Review outcomes | `/api/classes/{id}/results` |
| Review administrative history | `GET /api/audit` |

Published scenario revisions are immutable. The editor should create a new revision rather than
trying to update a published object in place. Use IDs as keys; do not identify resources by
array position or display name.

## Student workflow mapping

1. Load `GET /api/classes/available-scenarios`.
2. Load `GET /api/simulations` and show resumable runs.
3. Start a run with the selected revision ID, class ID, and a seed.
4. Render the returned `state`; do not invent or request hidden quality fields.
5. Build the weekly decision from student-controlled percentages and staffing choices.
6. Submit with the cached version and a stable idempotency key.
7. Replace cached state and version from the response.
8. Load `/turns` for visible history when required.
9. Submit the run with its current version and render `final_result`.

The student now decides the percentage allocation between development, unit testing, bug fixing,
and integration testing. This is an approved rewrite behavior and should replace legacy boolean
activity controls rather than be emulated behind the old UI.

## Optimistic concurrency and retries

The run `version` protects against two tabs completing the same week. Store it with the run, not
as an independent counter. A turn submission must use the latest returned version.

For each user submission:

1. generate a UUID or equivalently unique idempotency key;
2. disable duplicate clicks while the request is pending;
3. reuse that key when retrying a timeout or connection failure;
4. replace the run with the successful response;
5. on `409`, fetch the run again and require review before resubmitting with a new key.

Do not optimistically advance the displayed week before the server responds.

## Development connectivity

The simplest initial setup is to serve the existing frontend through its development server and
proxy `/api`, `/health`, `/docs`, and `/openapi.json` to `http://127.0.0.1:8000`. A same-origin
proxy avoids introducing CORS and cross-site cookie behavior during the first migration stage.

If the frontend must call the backend from a different origin directly, CORS support must be
implemented and explicitly configured in the backend before that deployment is supported.

## Definition of done for each migrated screen

- No direct request to a legacy endpoint remains in the screen or its store.
- Requests go through the shared API client.
- Loading, empty, validation, authorization, conflict, and unexpected-error states are visible.
- Tests cover the adapted response mapping and the primary user action.
- IDs, timestamps, enums, and optional values are handled without implicit coercion.
- Student screens cannot render professor-only audit data or hidden simulation state.
- Refreshing the browser restores the workflow from backend state.

## Legacy removal checkpoint

Keep a temporary endpoint-usage checklist during migration. Remove the legacy client and backend
startup dependency only when searches show no legacy URL, no legacy response type, and no legacy
simulation decision model in reachable frontend code.
