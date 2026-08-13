import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
	testDir: './tests/visual',
	snapshotDir: './tests/visual/__screenshots__',
	fullyParallel: true,
	forbidOnly: Boolean(process.env.CI),
	retries: process.env.CI ? 2 : 0,
	reporter: process.env.CI ? 'github' : 'list',
	use: {
		baseURL: 'http://127.0.0.1:4173',
		locale: 'en-US',
		timezoneId: 'UTC',
		colorScheme: 'light',
		reducedMotion: 'reduce',
		screenshot: 'only-on-failure',
	},
	projects: [
		{ name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
		{ name: 'mobile', use: { ...devices['Pixel 7'] } },
	],
	webServer: {
		command: 'npm run dev -- --host 127.0.0.1 --port 4173',
		url: 'http://127.0.0.1:4173',
		reuseExistingServer: !process.env.CI,
	},
});
