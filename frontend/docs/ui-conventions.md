# UI conventions

Use the Chakra theme and its brand colors, semantic tokens, defaults, radii, and shadows rather than
page-local substitutes. Each page has one descriptive `h1`; place its primary action beside the
heading on desktop and below it on mobile.

Use established navigation vocabulary and shared formatters for dates, money, percentages, and
statuses. API IDs remain request, list, form, and route keys—not fallback copy. If a professor needs
an identifier or digest for diagnosis, put it in a closed **Technical details** disclosure. Never show
technical details to students.

Provide explicit loading, actionable error, and useful empty states. Confirm destructive actions with
`ConfirmDialog`, with **Cancel** as the least-destructive initially focused action.

## Related documentation

- [Accessibility](accessibility.md)
- [Routing and role gates](routing.md)
- [Frontend testing](testing.md)
