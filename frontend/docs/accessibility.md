# Accessibility

Accessibility is part of the definition of done, not a final audit. Follow these requirements for
new UI and preserve them when changing existing workflows.

## Structure, names, and instructions

- Use semantic landmarks (`header`, `nav`, `main`, and `footer`) and native controls before ARIA.
- Give each route one descriptive `h1`. Nest section headings in order (`h2`, then `h3`) without
  skipping levels or using heading markup only for styling.
- Give every control an accessible name. Associate visible labels with inputs and connect help text,
  format requirements, and inline errors with `aria-describedby` when needed. A placeholder is not a
  label; required fields and constraints must be explained before submission.
- Write links and buttons that make sense out of context. Include status text and error meaning rather
  than communicating through position, shape, or color alone.

## Focus and keyboard interaction

All functionality must work with Tab, Shift+Tab, Enter, Space, Escape, and relevant arrow keys using
the native interaction model. Do not attach click behavior to a non-interactive `div`. Keep the theme's
visible focus indicator and ensure focused content is not hidden behind a sticky region.

On route changes, place focus at the start of the new page when the router does not do so naturally.
When opening a dialog, move focus inside, contain it while open, allow a safe Escape action, and
restore it to the invoking control on close. After deletion, move focus to a sensible surviving
heading, row, or status message. Loading and completion updates that occur without navigation should
be announced without repeatedly interrupting the user.

## Destructive confirmations

Use `ConfirmDialog` for destructive actions. The title and destructive button must name the action
and affected object, while the body explains irreversible consequences. Put initial focus on
**Cancel**, keep actions in a safe order, and restore focus after cancellation. Never rely on color,
an icon, or a generic **OK** label to convey risk.

## Touch, contrast, and motion

Interactive targets must be at least 44 by 44 CSS pixels or have equivalent spacing, including icon
buttons and chart points. Verify text, icons, focus rings, borders needed to identify controls, and
chart series meet appropriate contrast against every background. Theme tokens are preferred, but
using a token does not remove the need to check contrast. Statuses and chart series need a text,
shape, marker, or line-style cue in addition to color.

Respect `prefers-reduced-motion`: remove non-essential animation, avoid parallax and flashing, and do
not make motion the only indication of state. Functional transitions should be short and should not
block interaction. Playwright requests reduced motion, but the product must also honor the user's
browser setting outside tests.

## Charts and data alternatives

Provide a captioned HTML data table containing every value represented by a chart, with clear row and
column headers and the same units and formatting as the visual. Place it adjacent to the chart or
behind a clearly labeled disclosure—not in inaccessible SVG-only text. Give the chart a concise
summary, visible legend, non-color series cues, and keyboard-operable points when points are
interactive. Do not duplicate a long table as an equally long accessible name.

## Automated and manual checks

Automated checks catch only part of the problem. Run `npm test` for Testing Library and the
representative axe audit in `src/accessibility.test.jsx`; extend that audit for materially different
page structures. Run Playwright coverage for real-browser routes and responsive layouts. Treat an axe
pass as a starting point, not certification.

Manually test the changed workflow:

1. Navigate in both directions using only the keyboard and activate every control.
2. Check focus visibility, logical order, dialog containment/restoration, and focus after errors or
   deletion.
3. Inspect the accessibility tree or use a screen reader to confirm landmarks, heading order, names,
   descriptions, status announcements, and table headers.
4. Zoom to 200%, test a narrow mobile viewport, and check reflow, 44px targets, and no two-dimensional
   scrolling for ordinary content.
5. Test high contrast where available, a color-insensitive view, and reduced-motion preferences.

Record manual findings in the pull request when the change includes a new workflow, dialog, chart,
or unusual interaction.

## Related documentation

- [UI guidelines](ui-guidelines.md)
- [Frontend testing](testing.md)
