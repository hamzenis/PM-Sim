import { apiRequest } from './client';
import { listAuditEntries, mapProfessorContentAudit } from './audit';

vi.mock('./client', () => ({ apiRequest: vi.fn() }));

test('maps audit pagination to query parameters', async () => {
	apiRequest.mockResolvedValue([]);
	await listAuditEntries(25, 50);
	expect(apiRequest).toHaveBeenCalledWith('/api/audit?limit=25&offset=50');
});

test('maps and associates authored audit facts without treating answers as scores', () => {
	const result = mapProfessorContentAudit({
		deliveries: [{ id: 'd1', sequence_entry_id: 'entry', sequence_ordinal: 2, checkpoint: 'after_week:1', visibility: 'default', hidden_from_students: true, definition_digest: 'definition', definition_snapshot: { prompt: 'Reflect' }, status: 'completed', delivered_at: 'now', completed_at: 'later', turn_id: 't1', turn_week_number: 1 }],
		responses: [{ id: 'r1', sequence_entry_id: 'entry', response_version: 1, command_kind: 'answer', normalized_answer: { answer: 'Carefully' }, answered_at: 'later', request_digest: 'request', idempotency_key_digest: 'key' }],
		effects: [{ id: 'e1', sequence_entry_id: 'entry', effect_index: 0, effect_payload: { type: 'show_message' }, before_projection_digest: 'before', after_projection_digest: 'after', applied_at: 'later', turn_id: 't1', turn_week_number: 1 }],
		digest_status: 'verified',
		divergences: [{ category: 'response', record: 'r1', expected: 'a', actual: 'b' }],
	});
	expect(result.deliveries[0]).toMatchObject({ sequenceEntryId: 'entry', hiddenFromStudents: true, definitionDigest: 'definition', turnWeekNumber: 1 });
	expect(result.deliveries[0].responses[0].answer).toEqual({ answer: 'Carefully' });
	expect(result.deliveries[0].effects[0]).toMatchObject({ beforeProjectionDigest: 'before', afterProjectionDigest: 'after' });
	expect(result).toMatchObject({ digestStatus: 'verified' });
	expect(result.deliveries[0]).not.toHaveProperty('score');
});
