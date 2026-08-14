import { Alert, AlertIcon, Badge, Box, Heading, Stack, Text } from '@chakra-ui/react';
import React, { useState } from 'react';
import { ApiError } from '../../../api/client';
import { acknowledgeContentEntry, answerContentEntry } from '../../../api/simulations';
import AuthoredEvent from './AuthoredEvent';
import AuthoredQuestion from './AuthoredQuestion';
import ContentProgress from './ContentProgress';
import NarrativeFragment from './NarrativeFragment';
import { selectContentState, selectPresentationMessages } from './selectors';

const ContentPanel = ({ runId, version, deliveries = [], presentation, onRunChange, onConflict }) => {
	const { entries } = selectContentState(deliveries);
	const messages = selectPresentationMessages(presentation);
	const [pending, setPending] = useState(null);
	const [error, setError] = useState(null);
	if (!entries.length && !messages.length) return null;

	const submit = async (entry, answer) => {
		const command = answer === undefined ? 'acknowledge' : 'answer';
		const current = pending?.entryId === entry.sequence_entry_id && pending.command === command
			? pending
			: { entryId: entry.sequence_entry_id, command, answer, key: window.crypto.randomUUID(), version };
		setPending(current);
		setError(null);
		try {
			const result = command === 'answer'
				? await answerContentEntry(runId, entry.sequence_entry_id, current.answer, current.version, current.key)
				: await acknowledgeContentEntry(runId, entry.sequence_entry_id, current.version, current.key);
			setPending(null);
			onRunChange?.(result);
		} catch (requestError) {
			if (requestError instanceof ApiError && requestError.status === 409) {
				setPending(null);
				setError('The content changed. Review the updated content state before trying again.');
				await onConflict?.();
			} else setError(`${requestError.message || 'Could not save this response'} You can retry the same request.`);
		}
	};

	return (
		<Box bg="blue.50" borderWidth="1px" borderColor="blue.200" borderRadius="2xl" p={{ base: 5, md: 7 }} mb={6} aria-labelledby="authored-content-heading">
			<Badge colorScheme="blue" mb={2}>Scenario update</Badge>
			<Heading id="authored-content-heading" size="md" mb={2}>Read and respond</Heading>
			<Text color="gray.700" mb={1}>These learning activities are separate from your weekly project plan.</Text>
			{entries.length > 0 && <ContentProgress entries={entries} />}
			{error && <Alert status="error" mt={4}><AlertIcon />{error}</Alert>}
			{messages.map((message) => (
				<Alert key={message} status="info" mt={4} variant="left-accent">
					<AlertIcon />
					<Text>{message}</Text>
				</Alert>
			))}
			<Stack spacing={4} mt={5}>
				{entries.map((entry) => (
					<Box key={entry.sequence_entry_id} id={`content-entry-${entry.sequence_entry_id}`} tabIndex={-1} bg="white" borderWidth={entry.required && entry.status === 'actionable' ? '2px' : '1px'} borderColor={entry.required && entry.status === 'actionable' ? 'blue.400' : 'gray.200'} borderRadius="lg" p={5}>
						{entry.required && entry.status === 'actionable' && <Badge colorScheme="blue" mb={3}>Required before continuing</Badge>}
						{!entry.required && entry.status === 'actionable' && ['question', 'fragment'].includes(entry.kind) && <Badge mb={3}>Optional</Badge>}
						{entry.kind === 'fragment' && <NarrativeFragment entry={entry} isSubmitting={pending?.entryId === entry.sequence_entry_id} onAcknowledge={() => submit(entry)} />}
						{entry.kind === 'question' && <AuthoredQuestion entry={entry} isSubmitting={pending?.entryId === entry.sequence_entry_id} onAnswer={(answer) => submit(entry, answer)} />}
						{entry.kind === 'event' && <AuthoredEvent entry={entry} />}
					</Box>
				))}
			</Stack>
		</Box>
	);
};

export default ContentPanel;
