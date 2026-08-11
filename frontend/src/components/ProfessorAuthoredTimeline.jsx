import { Alert, AlertIcon, Badge, Box, Code, Heading, HStack, Text, VStack } from '@chakra-ui/react';
import React from 'react';

const printable = (value) => typeof value === 'string' ? value : JSON.stringify(value);

const ProfessorAuthoredTimeline = ({ audit }) => {
	if (!audit) return null;
	return (
		<Box mt={8} aria-labelledby="authored-timeline-heading">
			<Heading id="authored-timeline-heading" size="md" mb={3}>Authored-content timeline</Heading>
			<Alert status={audit.digestStatus === 'verified' ? 'success' : 'error'} mb={4}>
				<AlertIcon />Definition/projection digest status: {audit.digestStatus}
			</Alert>
			{audit.divergences.length > 0 && (
				<Alert status="error" mb={4}><AlertIcon />Replay divergence detected. Stored authored facts do not match replay.</Alert>
			)}
			<VStack align="stretch" spacing={4}>
				{audit.deliveries.map((delivery) => (
					<Box key={delivery.id} bg="white" p={5} borderRadius="xl" borderWidth="1px">
						<HStack wrap="wrap" mb={2}>
							<Heading size="sm">{delivery.definition.title || delivery.definition.prompt || delivery.sequenceEntryId}</Heading>
							<Badge>{delivery.status}</Badge>
							{delivery.hiddenFromStudents && <Badge colorScheme="purple">Professor only / hidden</Badge>}
							{delivery.turnWeekNumber != null && <Badge colorScheme="blue">Associated turn: week {delivery.turnWeekNumber}</Badge>}
						</HStack>
						<Text>Delivery checkpoint: {delivery.checkpoint}</Text>
						<Text fontSize="sm">Definition digest: <Code>{delivery.definitionDigest}</Code></Text>
						{delivery.responses.map((response) => (
							<Box key={response.id} mt={3} pl={3} borderLeftWidth="3px">
								<Text fontWeight="bold">{response.kind === 'answer' ? 'Authored response' : 'Learning interaction acknowledgement'}</Text>
								<Text>{printable(response.answer)}</Text>
							</Box>
						))}
						{delivery.effects.map((effect) => (
							<Box key={effect.id} mt={3}>
								<Text fontWeight="bold">Presentation effect {effect.effectIndex + 1}</Text>
								<Text>{printable(effect.payload)}</Text>
								<Text fontSize="sm">Projection digest: <Code>{effect.beforeProjectionDigest}</Code> → <Code>{effect.afterProjectionDigest}</Code></Text>
							</Box>
						))}
					</Box>
				))}
			</VStack>
			{audit.divergences.map((item, index) => (
				<Text key={`${item.category}-${item.record}-${index}`} mt={2}>Divergence {item.category} ({item.record}): expected {printable(item.expected)}, actual {printable(item.actual)}</Text>
			))}
		</Box>
	);
};

export default ProfessorAuthoredTimeline;
