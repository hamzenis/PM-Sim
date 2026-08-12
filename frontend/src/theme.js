import { extendTheme } from '@chakra-ui/react';

const theme = extendTheme({
	colors: {
		brand: {
			50: '#eef6ff',
			100: '#d9eaff',
			500: '#2563a8',
			600: '#1d4f88',
			700: '#173f6d',
			900: '#102a43',
		},
	},
	semanticTokens: {
		colors: {
			'page.bg': 'gray.50',
			'surface.bg': 'white',
			'text.default': 'gray.800',
			'text.muted': 'gray.600',
			'border.default': 'gray.200',
			'focus.ring': 'brand.500',
		},
	},
	fonts: {
		heading: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
		body: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
	},
	radii: { card: '12px' },
	shadows: {
		card: '0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04)',
		header: '0 1px 2px rgba(15, 23, 42, 0.06)',
	},
	styles: {
		global: {
			'html, body, #root': { minHeight: '100%' },
			body: { bg: 'page.bg', color: 'text.default' },
			'a, button, input, select, textarea': {
				_focusVisible: { outline: '3px solid', outlineColor: 'focus.ring', outlineOffset: '2px' },
			},
		},
	},
	components: {
		Button: {
			defaultProps: { colorScheme: 'brand' },
			baseStyle: { borderRadius: 'md', fontWeight: 'semibold' },
		},
	},
});

export default theme;
