# UI guidelines

## Theme tokens

Use `src/theme.js` through Chakra props instead of introducing page-local approximations:

- `brand.50`, `brand.100`, `brand.500`, `brand.600`, `brand.700`, and `brand.900` form the product
  palette. Buttons default to the `brand` scheme, a semibold label, rounded corners, and 44px minimum
  height.
- `page.bg`, `surface.bg`, `text.default`, `text.muted`, `border.default`, and `focus.ring` are the
  semantic color tokens. They express purpose and should be preferred to raw hex values.
- `card` is the shared 12px radius; `card` and `header` are the shared shadows.
- Chart series use `chart.actual`, `planned`, `limit`, `stress`, `motivation`, `familiarity`,
  `completed`, `unitTested`, `integrationTested`, `bugs`, `grid`, and `axis`. Do not assign arbitrary
  series colors or depend on color alone.
- Body and heading fonts use the system stack. The global theme supplies a three-pixel visible focus
  ring to links and form controls.

## Responsive page structure and headings

Use the established centered page container and responsive Chakra values rather than fixed widths.
Pages must reflow without horizontal page scrolling at mobile widths. Each route has one descriptive
`h1`; sections descend to `h2` and `h3` without skipping levels. Do not choose heading levels for
visual size—use Chakra typography props.

Put the page's single primary action next to the heading on desktop and below it on mobile, usually
with a responsive `Flex` or `Stack`. Keep actions in a predictable order, use a verb plus object
(**Create class**, not **Submit**), and do not make several actions visually primary.

## Forms and dialogs

Give every input a persistent programmatic label and associate help, requirements, and validation
messages with it. Explain the expected format before submission, retain entered values after an
error, focus or summarize the first actionable error, and disable submission only when the reason is
clear. Use the correct input type and autocomplete value; placeholders are examples, not labels.

Use Chakra's dialog primitives with a visible title, initial focus on the safest useful control, a
logical tab order, Escape handling where safe, and focus restoration to the trigger. Confirm every
destructive action with `ConfirmDialog`; name the object and consequence, label the destructive
button precisely, and initially focus **Cancel**. Never use a browser `confirm()` dialog.

## Status, charts, and feedback states

Status badges always contain a human-readable label and must remain distinguishable without color.
Map API values such as `in_progress` to consistent plain-language text rather than printing raw
values. Use an icon only as reinforcement and give unfamiliar icons an accessible name.

Charts use the `chart.*` palette, a visible legend, readable axes/units, and text explaining the key
result. Make interactive points keyboard operable. Every chart must expose the same values in an
accessible table with a useful caption; shared chart presentation components already demonstrate
this pattern. Do not encode a series or outcome only by hue—also use labels, markers, or line styles.

Every request-driven region needs explicit states:

- **Loading:** retain useful layout where practical, announce meaningful asynchronous changes, and
  avoid a blank page or indefinite spinner.
- **Error:** state what failed in user terms and offer an appropriate retry or next step; preserve
  form data. Do not expose stack traces.
- **Empty:** explain why no items exist and offer the relevant primary action when the user can fix it.
- **Success:** confirm the completed action without unnecessarily stealing focus.

## Plain-language formatting and internal identities

Use the vocabulary visible in navigation and neighboring workflows. Prefer short sentences and
specific verbs, explain acronyms on first use, and avoid implementation terms. Use
`src/utils/resultPresentation.js` for locale-aware dates, currency, percentages, scores, and status
labels; never show raw timestamps or machine status strings.

IDs remain stable request, route, list, and form keys—not fallback copy. Show scenario and class
names, usernames, revision numbers, and employee-type names. If a professor genuinely needs an ID or
digest for diagnosis, put it in a closed **Technical details** disclosure. Never expose technical
details to students.

## Adding a page consistently

1. Add the route-level component under `src/pages/` and register it in `src/Routing.jsx` inside the
   correct public, authenticated, or professor-only gate.
2. Use the shared theme and responsive container, one descriptive `h1`, semantic landmarks, and the
   standard desktop/mobile primary-action placement.
3. Reuse navigation vocabulary, shared components, and presentation formatters. Keep IDs internal.
4. Provide loading, actionable error, useful empty, and success feedback. Use an accessible dialog
   for confirmation and `ConfirmDialog` for destructive work.
5. Check keyboard flow, focus, heading order, 44px targets, narrow-screen overflow, and text/contrast
   without color. Add the appropriate coverage described in the [testing guide](testing.md).

### Page consistency checklist

- The heading uniquely describes the task and actions have plain, specific labels.
- Labels, instructions, errors, dialog focus, and destructive confirmations are accessible.
- Dates, money, percentages, and statuses use shared formatting and plain-language labels.
- Loading, error, empty, and success paths communicate a next step where one exists.
- Charts include units, non-color cues, keyboard interaction, and an equivalent data table.
- Desktop and mobile layouts avoid page overflow and retain 44px pointer targets.
- UUIDs, internal run/class/revision/employee IDs, digests, and hashes are absent from ordinary copy.

## Related documentation

- [Accessibility](accessibility.md)
- [Frontend testing](testing.md)
- [Routing and role gates](routing.md)
