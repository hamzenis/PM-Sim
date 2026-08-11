import { apiRequest } from './client';
import { assignScenario, createClass, importStudents, listClasses, removeStudent } from './classes';

jest.mock('./client', () => ({ apiRequest: jest.fn() }));

beforeEach(() => apiRequest.mockReset());

test('maps common class management operations', async () => {
	apiRequest.mockResolvedValue({});

	await listClasses();
	await createClass('Software Engineering');
	await importStudents('class-1', [{ username: 'student', password: 'long-password' }]);
	await assignScenario('class-1', 'revision-1');
	await removeStudent('class-1', 'student-1');

	expect(apiRequest.mock.calls).toEqual([
		['/api/classes'],
		['/api/classes', { method: 'POST', body: JSON.stringify({ name: 'Software Engineering' }) }],
		[
			'/api/classes/class-1/students/import',
			{
				method: 'POST',
				body: JSON.stringify({ students: [{ username: 'student', password: 'long-password' }] }),
			},
		],
		[
			'/api/classes/class-1/scenarios',
			{ method: 'POST', body: JSON.stringify({ scenario_revision_id: 'revision-1' }) },
		],
		['/api/classes/class-1/students/student-1', { method: 'DELETE' }],
	]);
});
