import { Box, Heading, Stack, Text } from '@chakra-ui/react';
import React from 'react';

const readableKind = (kind = '') => kind.replaceAll('_', ' ');

const TurnHistory = ({ turns }) => {
	if (turns.length === 0) return null;
	return (
		<Box bg="white" borderRadius="2xl" p={7} mt={6}>
			<Heading size="md" mb={4}>
				Turn history
			</Heading>
			<Stack spacing={4}>
				{turns.map(({ week_number: weekNumber, decision, events, resulting_state: resultingState }) => (
					<Box key={weekNumber} borderWidth="1px" borderRadius="md" p={4} data-state-week={resultingState?.week}>
						<Heading size="sm" mb={2}>
							Week {weekNumber}
						</Heading>
						<Text fontWeight="semibold">
							Allocation:{' '}
							{Object.entries(decision.allocation || {})
								.map(([name, value]) => `${readableKind(name)} ${value}%`)
								.join(', ')}
						</Text>
						<Text mb={2}>
							Hires: {decision.hires?.length || 0}; dismissals:{' '}
							{decision.dismiss_employee_ids?.length || 0}; overtime:{' '}
							{decision.overtime_hours_per_employee || 0} hours
						</Text>
						{events.length === 0 ? (
							<Text>No visible events.</Text>
						) : (
							events.map((event, index) => (
								<Text key={`${event.kind}-${index}`}>• {readableKind(event.kind)}</Text>
							))
						)}
					</Box>
				))}
			</Stack>
		</Box>
	);
};

export default TurnHistory;
