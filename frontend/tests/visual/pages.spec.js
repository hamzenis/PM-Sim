import { expect, test } from '@playwright/test';

const student = { id: 'student-1', username: 'alex.student', role: 'student' };
const professor = { id: 'professor-1', username: 'prof.morgan', role: 'professor' };
const pool = (easy = 0, medium = 0, hard = 0) => ({ easy, medium, hard });

const activeRun = {
	id: 'run-1', class_id: 'class-1', scenario_revision_id: 'revision-1', version: 3,
	current_week: 2, status: 'active', scenario_title: 'Community Library Launch',
	scenario_briefing: 'Deliver a dependable library booking platform within six project weeks.', deliveries: [],
	employee_types: [{ code: 'developer', name: 'Software developer', cost_per_day: 640, throughput: { easy: 4, medium: 2, hard: 1 }, error_rate: 0.06, management_skill: 0.72 }],
	state: { week: 2, elapsed_working_days: 10, remaining_working_days: 20, initial_budget: 120000, remaining_budget: 94800,
		tasks_todo: pool(12, 7, 3), tasks_completed: pool(9, 4, 1), tasks_unit_tested: pool(8, 3, 1),
		tasks_integration_tested: pool(6, 2, 0), known_bugs: pool(1, 0, 0),
		employees: [{ id: 'employee-1', employee_type_code: 'developer', experience: 0.8, motivation: 0.74, stress: 0.31, familiarity: 0.68 }] },
};

const activeTurns = [{
	week_number: 1,
	decision: { allocation: { development: 55, unit_testing: 25, bug_fixing: 5, integration_testing: 15 }, hires: [], dismiss_employee_ids: [] },
	resulting_state: {
		...activeRun.state, week: 1, elapsed_working_days: 5, remaining_working_days: 25, remaining_budget: 107400,
		tasks_todo: pool(15, 8, 3), tasks_completed: pool(6, 3, 1), tasks_unit_tested: pool(4, 2, 0),
		tasks_integration_tested: pool(2, 1, 0), known_bugs: pool(1, 0, 0),
	},
	events: [{ kind: 'bugs_discovered', values: pool(1, 0, 0) }],
}];

const result = {
	run_id: 'run-1', student_id: 'student-1', scenario_revision_id: 'revision-1', student_username: 'alex.student',
	class_name: 'PM Fundamentals — Fall 2026', scenario_name: 'Community Library Launch', status: 'submitted', current_week: 5,
	finished_at: '2026-10-16T15:30:00Z', engine_version: '2.1', seed: 20261016,
	final_result: { outcome: 'success', score: { total: 91, quality: 92, time: 88, budget: 94 }, accepted_tasks: 31, rejected_tasks: 3 },
	current_state: activeRun.state,
	turns: [{ week_number: 1, submitted_at: '2026-09-18T14:00:00Z', decision: { allocation: { development: 60, unit_testing: 25, integration_testing: 15 } }, events: [{ kind: 'tasks_completed', easy: 6, medium: 2 }] }],
	content_audit: { digest_status: 'verified', divergences: [], deliveries: [], effects: [] },
};

async function installFixtures(page, role) {
	await page.route('**/api/**', async (route) => {
		const path = new URL(route.request().url()).pathname;
		if (!path.startsWith('/api/')) return route.continue();
		let body;
		if (path === '/api/auth/me') {
			if (!role) return route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'Not authenticated' }) });
			body = role === 'student' ? student : professor;
		} else if (path === '/api/classes/available-scenarios') body = [{ id: 'revision-1', class_id: 'class-1', class_name: 'PM Fundamentals — Fall 2026', revision_number: 4, definition: { name: 'Community Library Launch', description: 'Plan and deliver a public-service platform while balancing scope, team wellbeing, quality, and budget.' } }];
		else if (path === '/api/simulations') body = [activeRun];
		else if (path === '/api/simulations/run-1/turns') body = activeTurns;
		else if (path === '/api/simulations/run-1') body = activeRun;
		else if (path === '/api/classes') body = [{ id: 'class-1', name: 'PM Fundamentals — Fall 2026' }];
		else if (path === '/api/classes/class-1/students') body = [{ id: 'student-1', username: 'alex.student' }, { id: 'student-2', username: 'jamie.lee' }, { id: 'student-3', username: 'sam.rivera' }];
		else if (path === '/api/classes/class-1/scenarios') body = [{ id: 'assignment-1', scenario_revision_id: 'revision-1', scenario_name: 'Community Library Launch', revision_number: 4 }];
		else if (path === '/api/classes/class-1/results') body = [result];
		else if (path === '/api/classes/class-1/results/run-1') body = result;
		else if (path === '/api/scenarios') body = [{ id: 'scenario-1', name: 'Community Library Launch', latest_revision: 4, latest_status: 'published' }];
		else if (path === '/api/scenarios/scenario-1') body = [{ id: 'revision-1', scenario_id: 'scenario-1', scenario_name: 'Community Library Launch', revision_number: 4, status: 'published', definition: { name: 'Community Library Launch' } }];
		else body = [];
		await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });
	});
}

async function stableScreenshot(page, path, name, role, ready) {
	await installFixtures(page, role);
	const response = await page.goto(path);
	if (!response?.ok()) throw new Error(`Navigation failed: ${response?.status()} ${page.url()}`);
	await ready(page);
	await page.evaluate(() => document.fonts.ready);
	await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true, animations: 'disabled', caret: 'hide' });
}

test('login page', async ({ page }) => stableScreenshot(page, '/login', 'login', null, (p) => expect(p.getByRole('heading', { name: 'Welcome back' })).toBeVisible()));
test('student scenario dashboard', async ({ page }) => stableScreenshot(page, '/scenarios', 'student-scenarios', 'student', (p) => expect(p.getByRole('heading', { name: 'My scenarios' })).toBeVisible()));
test('active student weekly decision', async ({ page }) => stableScreenshot(page, '/simulations/run-1', 'student-weekly-decision', 'student', async (p) => {
	await expect(p.getByRole('dialog', { name: 'Scenario briefing' })).toBeVisible();
	await p.getByRole('button', { name: 'Start simulation' }).click();
	await expect(p.getByRole('heading', { name: 'Plan week 3' })).toBeVisible();
}));
test('professor class management', async ({ page }) => stableScreenshot(page, '/classes', 'professor-class-management', 'professor', (p) => expect(p.getByRole('heading', { name: 'Professor workspace' })).toBeVisible()));
test('professor result summary', async ({ page }) => stableScreenshot(page, '/classes/class-1/results/run-1', 'professor-result-summary', 'professor', (p) => expect(p.getByRole('heading', { name: 'Result for alex.student' })).toBeVisible()));
