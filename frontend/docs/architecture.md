# Frontend architecture

`src/Routing.jsx` owns route registration and role gates. Route-level screens live in `src/pages/`,
reusable UI in `src/components/`, server adapters and response mapping in `src/api/`, and shared
presentation formatters in `src/utils/`. `src/App.jsx` installs the Chakra theme from `src/theme.js`.

The student simulation is assembled by `pages/SimulationV2.jsx` from focused components under
`components/SimulationV2/`. Professor class-management panels live under
`components/ClassManagement/`. Keep network shapes out of page components by mapping them in the
API adapter layer.

## Related documentation

- [Routing and role gates](routing.md)
- [API integration](api-integration.md)
- [UI conventions](ui-conventions.md)
