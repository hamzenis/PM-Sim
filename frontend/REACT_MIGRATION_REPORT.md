# React migration verification report

## Scope and registry snapshot

This verification was performed from `frontend/` on 2026-08-11 immediately
before any implementation. The npm registry was queried with `npm view`; the
stable `latest` distribution tag was selected in every case. Prerelease,
`beta`, `next`, `canary`, `experimental`, and release-candidate tags were not
eligible. A `backport` tag was also not treated as the current stable release.

| Package | Selected stable tag | Exact version | Registry release date (UTC) | Declared Node.js requirement | Declared peer dependencies |
| --- | --- | --- | --- | --- | --- |
| `react` | `latest` | `19.2.8` | `2026-07-21T15:41:28.716Z` | `>=0.10.0` | None |
| `react-dom` | `latest` | `19.2.8` | `2026-07-21T15:41:41.267Z` | None declared | `react: ^19.2.8` |
| `@types/react` | `latest` | `19.2.18` | `2026-07-30T21:54:03.456Z` | None declared | None |
| `@types/react-dom` | `latest` | `19.2.4` | `2026-07-30T21:53:05.684Z` | None declared | `@types/react: ^19.2.0` |

The individual registry reads completed between `2026-08-11T23:31:27.983Z`
and `2026-08-11T23:31:39.154Z`. React and React DOM are intentionally pinned
to exactly the same selected version, `19.2.8`; implementation must preserve
that equality rather than use independent ranges.

## Build and test compatibility

The verification environment uses Node.js `20.20.2`.

| Tool | Version checked | Node.js requirement | Relevant peer dependencies | Result with selected React |
| --- | --- | --- | --- | --- |
| `react-scripts` | `5.0.1` (current and registry `latest`) | `>=14.0.0` | `react: >=16`; `typescript: ^3.2.1 || ^4` | Declared Node and React constraints pass. |
| `@testing-library/react` | `13.1.1` (current) | `>=12` | `react: ^18.0.0`; `react-dom: ^18.0.0` | **Fails**: its React peers exclude React 19. |
| `@testing-library/react` | `16.3.2` (registry `latest` checked for the migration) | `>=18` | `react` and `react-dom`: `^18.0.0 || ^19.0.0`; optional type peers of the same majors; `@testing-library/dom: ^10.0.0` | Passes on Node 20 and React 19, provided `@testing-library/dom` is installed/resolved at `^10`. |
| `typescript` | `4.5.4` (current) | `>=4.2.0` | None | Passes Node, and satisfies CRA 5, but the registry routes TypeScript 4.5 consumers to React 18-era typings rather than the selected `latest` React 19 typings. |

The selected React runtime therefore must not be installed while retaining
`@testing-library/react@13.1.1`. The implementation should upgrade the React
Testing Library to `16.3.2` together with its declared DOM peer, then validate
the CRA build and Jest suite. CRA 5's published constraints permit the selected
runtime, but that metadata is not a substitute for the build and test run.

## Typings cleanup decision

This is a JavaScript application: the source inventory contains JavaScript and
JSX but no TypeScript or TSX, there is no `tsconfig.json`, and the React type
packages and TypeScript are referenced only by `package.json`. CRA does not
require them for JavaScript builds. Consequently, implementation should remove
`@types/react`, `@types/react-dom`, and `typescript` as a separately reviewed
dependency cleanup instead of installing the registry's React 19 typings.
Editor inference for JavaScript remains available from the runtime packages;
if the project later adopts checked TypeScript, typings compatible with that
chosen compiler should be reintroduced then.

This removal also avoids a tooling mismatch: CRA 5 declares only TypeScript 3
and 4 support, while the current `latest` React type tags target newer compiler
tracks (the registry's TypeScript-specific tag for 4.5 remains on React 18).

## Verification boundary and rollback

No application source, package declaration, or lockfile was changed during
this verification. Implementation is intentionally deferred. The rollback
position is the current `frontend/package.json` and
`frontend/package-lock.json`: retain both unchanged if the migration is not
implemented or if its build/test validation fails.
