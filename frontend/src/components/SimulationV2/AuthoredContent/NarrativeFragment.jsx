import { Button, Heading, Text } from '@chakra-ui/react';
import React from 'react';
import ContentFeedback from './ContentFeedback';

const NarrativeFragment = ({ entry, isSubmitting, onAcknowledge }) => (
	<>
		{entry.title && <Heading size="sm" mb={2}>{entry.title}</Heading>}
		{entry.body && <Text whiteSpace="pre-wrap">{entry.body}</Text>}
		{entry.required && entry.status === 'actionable' && (
			<Button mt={4} colorScheme="blue" size="sm" isLoading={isSubmitting} onClick={onAcknowledge}>
				Acknowledge
			</Button>
		)}
		{entry.status === 'completed' && entry.latest_response?.command_kind === 'acknowledge' && (
			<Text mt={3} color="green.700" fontWeight="semibold">Acknowledged</Text>
		)}
		<ContentFeedback feedback={entry.feedback} />
	</>
);

export default NarrativeFragment;
