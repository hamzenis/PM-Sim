import { apiRequest } from './client';

export const listAuditEntries = (limit = 50, offset = 0) => apiRequest(`/api/audit?limit=${limit}&offset=${offset}`);

const byOrdinal = (left, right) => left.sequenceOrdinal - right.sequenceOrdinal;

export const mapProfessorContentAudit = (audit = {}) => {
	const responses = (audit.responses || []).map((response) => ({
		id: response.id,
		sequenceEntryId: response.sequence_entry_id,
		responseVersion: response.response_version,
		kind: response.command_kind,
		answer: response.normalized_answer,
		answeredAt: response.answered_at,
		requestDigest: response.request_digest,
		idempotencyKeyDigest: response.idempotency_key_digest,
	}));
	const effects = (audit.effects || []).map((effect) => ({
		id: effect.id,
		sequenceEntryId: effect.sequence_entry_id,
		effectIndex: effect.effect_index,
		payload: effect.effect_payload,
		beforeProjectionDigest: effect.before_projection_digest,
		afterProjectionDigest: effect.after_projection_digest,
		appliedAt: effect.applied_at,
		turnId: effect.turn_id,
		turnWeekNumber: effect.turn_week_number,
	}));
	const deliveries = (audit.deliveries || []).map((delivery) => ({
		id: delivery.id,
		sequenceEntryId: delivery.sequence_entry_id,
		sequenceOrdinal: delivery.sequence_ordinal,
		checkpoint: delivery.checkpoint,
		visibility: delivery.visibility,
		hiddenFromStudents: delivery.hidden_from_students,
		definitionDigest: delivery.definition_digest,
		definition: delivery.definition_snapshot,
		status: delivery.status,
		deliveredAt: delivery.delivered_at,
		completedAt: delivery.completed_at,
		turnId: delivery.turn_id,
		turnWeekNumber: delivery.turn_week_number,
		responses: responses.filter((response) => response.sequenceEntryId === delivery.sequence_entry_id),
		effects: effects.filter((effect) => effect.sequenceEntryId === delivery.sequence_entry_id),
	})).sort(byOrdinal);

	return {
		deliveries,
		responses,
		effects,
		digestStatus: audit.digest_status || 'unknown',
		divergences: (audit.divergences || []).map((divergence) => ({
			category: divergence.category,
			record: divergence.record,
			expected: divergence.expected,
			actual: divergence.actual,
		})),
	};
};

export const mapRunAudit = (result) => ({
	...result,
	contentAudit: mapProfessorContentAudit(result.content_audit),
});
