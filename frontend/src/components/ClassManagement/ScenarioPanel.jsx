import { Box, Button, Flex, Heading, Select, Stack, Text } from '@chakra-ui/react';
import React, { useState } from 'react';

const ScenarioPanel = ({ selectedId, revisions, assignments, onAssign, onUnassign }) => {
	const [revisionId, setRevisionId] = useState('');
	return (
		<Box bg="white" p={6} borderRadius="xl">
			<Heading size="md" mb={4}>
				Assigned scenarios
			</Heading>
			<Stack direction={{ base: 'column', md: 'row' }} mb={4}>
				<Select
					aria-label="Published revision"
					placeholder="Published revision"
					value={revisionId}
					onChange={(event) => setRevisionId(event.target.value)}
				>
					{revisions.map((revision) => (
						<option key={revision.id} value={revision.id}>
							{revision.definition.name} (revision {revision.revision_number})
						</option>
					))}
				</Select>
				<Button colorScheme="blue" isDisabled={!selectedId || !revisionId} onClick={() => onAssign(revisionId)}>
					Assign
				</Button>
			</Stack>
			{assignments.length === 0 ? (
				<Text>No scenarios assigned.</Text>
			) : (
				assignments.map((item) => (
					<Flex key={item.id} justify="space-between" align="center" py={2}>
						<Text>
							Revision {item.revision_number} ({item.status})
						</Text>
						<Button size="sm" colorScheme="red" variant="outline" onClick={() => onUnassign(item)}>
							Unassign
						</Button>
					</Flex>
				))
			)}
		</Box>
	);
};

export default ScenarioPanel;
