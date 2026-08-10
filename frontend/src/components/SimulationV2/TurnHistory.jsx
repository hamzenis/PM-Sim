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
				{turns.map((turn) => (
					<Box key={turn.week_number} borderWidth="1px" borderRadius="md" p={4}>
						<Heading size="sm" mb={2}>
							Week {turn.week_number}
						</Heading>
						{turn.events.length === 0 ? (
							<Text>No visible events.</Text>
						) : (
							turn.events.map((event, index) => (
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
