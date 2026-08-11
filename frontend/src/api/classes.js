import { apiRequest } from './client';
import { mapRunAudit } from './audit';

export const listClasses = () => apiRequest('/api/classes');

export const createClass = (name) =>
	apiRequest('/api/classes', {
		method: 'POST',
		body: JSON.stringify({ name }),
	});

export const renameClass = (classId, name) =>
	apiRequest(`/api/classes/${classId}`, {
		method: 'PATCH',
		body: JSON.stringify({ name }),
	});

export const archiveClass = (classId) => apiRequest(`/api/classes/${classId}/archive`, { method: 'POST' });

export const listStudents = (classId) => apiRequest(`/api/classes/${classId}/students`);

export const importStudents = (classId, students) =>
	apiRequest(`/api/classes/${classId}/students/import`, {
		method: 'POST',
		body: JSON.stringify({ students }),
	});

export const addStudent = (classId, username) =>
	apiRequest(`/api/classes/${classId}/students`, {
		method: 'POST',
		body: JSON.stringify({ username }),
	});

export const removeStudent = (classId, studentId) =>
	apiRequest(`/api/classes/${classId}/students/${studentId}`, { method: 'DELETE' });

export const resetStudentPassword = (classId, studentId, newPassword) =>
	apiRequest(`/api/classes/${classId}/students/${studentId}/password`, {
		method: 'PUT',
		body: JSON.stringify({ new_password: newPassword }),
	});

export const listAssignedScenarios = (classId) => apiRequest(`/api/classes/${classId}/scenarios`);

export const assignScenario = (classId, scenarioRevisionId) =>
	apiRequest(`/api/classes/${classId}/scenarios`, {
		method: 'POST',
		body: JSON.stringify({ scenario_revision_id: scenarioRevisionId }),
	});

export const unassignScenario = (classId, revisionId) =>
	apiRequest(`/api/classes/${classId}/scenarios/${revisionId}`, { method: 'DELETE' });

export const listClassResults = (classId) => apiRequest(`/api/classes/${classId}/results`);

export const getClassResult = (classId, runId) =>
	apiRequest(`/api/classes/${classId}/results/${runId}`).then(mapRunAudit);
