import { Alert, AlertIcon, Badge, Box, Code, Heading, HStack, Text, VStack } from '@chakra-ui/react';
import React from 'react';
import { formatDateTime, formatTeachingValue, plainLanguageLabel, readableStatus, statusColor } from '../utils/resultPresentation';

const ProfessorAuthoredTimeline = ({ audit }) => {
	if (!audit) return null;
	return <Box mt={8} aria-labelledby="authored-timeline-heading">
		<Heading id="authored-timeline-heading" size="md" mb={3}>Teaching-content timeline</Heading>
		{audit.digestStatus !== 'verified' && <Alert status="error" mb={4}><AlertIcon />Integrity verification failed. Technical audit data may not match the stored teaching record.</Alert>}
		{audit.divergences.length > 0 && <Alert status="error" mb={4}><AlertIcon />Replay divergence detected. Stored authored facts do not match replay.</Alert>}
		<VStack align="stretch" spacing={4}>{audit.deliveries.map((delivery) => <Box key={delivery.id} bg="white" p={5} borderRadius="xl" borderWidth="1px">
			<HStack wrap="wrap" mb={2}><Heading size="sm">{delivery.definition.title || delivery.definition.prompt || 'Teaching content'}</Heading><Badge colorScheme={statusColor(delivery.status)}>{readableStatus(delivery.status)}</Badge>{delivery.hiddenFromStudents && <Badge colorScheme="purple">Professor only</Badge>}{delivery.turnWeekNumber != null && <Badge colorScheme="blue">Week {delivery.turnWeekNumber}</Badge>}</HStack>
			<Text>{plainLanguageLabel(delivery.checkpoint)}</Text><Text color="gray.600" fontSize="sm">Delivered {formatDateTime(delivery.deliveredAt)}</Text>
			{delivery.responses.map((response) => <Box key={response.id} mt={3} pl={3} borderLeftWidth="3px"><Text fontWeight="bold">{response.kind === 'answer' ? 'Student response' : 'Learning acknowledgement'}</Text><Text>{formatTeachingValue('answer', response.answer)}</Text></Box>)}
			{delivery.effects.map((effect) => <Box key={effect.id} mt={3}><Text fontWeight="bold">Teaching outcome {effect.effectIndex + 1}</Text><Text>{formatTeachingValue('outcome', effect.payload)}</Text></Box>)}
		</Box>)}</VStack>
		<Box as="details" mt={4} bg="gray.50" p={4} borderRadius="md"><Box as="summary" cursor="pointer" fontWeight="bold">Technical details</Box>
			<Text mt={2}>Digest status: <Badge>{readableStatus(audit.digestStatus)}</Badge></Text>
			{audit.deliveries.map((delivery) => <Box key={delivery.id} mt={3}><Text>Delivery UUID: <Code>{delivery.id}</Code></Text><Text>Definition digest: <Code>{delivery.definitionDigest}</Code></Text></Box>)}
			{audit.effects.map((effect) => <Text key={effect.id}>Projection digests: <Code>{effect.beforeProjectionDigest}</Code> → <Code>{effect.afterProjectionDigest}</Code></Text>)}
			{audit.divergences.map((item, index) => <Text key={`${item.category}-${index}`}>Divergence {item.category} ({item.record}): expected {JSON.stringify(item.expected)}, actual {JSON.stringify(item.actual)}</Text>)}
			<Heading size="xs" mt={3}>Raw audit payload</Heading><Box as="pre" overflowX="auto" fontSize="xs">{JSON.stringify(audit, null, 2)}</Box>
		</Box>
	</Box>;
};
export default ProfessorAuthoredTimeline;
