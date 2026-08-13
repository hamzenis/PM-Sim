// jest-dom adds custom Vitest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom/vitest';


// axe-core probes canvas text metrics when checking icon fonts; jsdom has no canvas renderer.
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
	measureText: () => ({ width: 0 }),
	fillText: vi.fn(),
}));
