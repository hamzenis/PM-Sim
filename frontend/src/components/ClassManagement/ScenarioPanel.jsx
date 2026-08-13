import { Badge, Box, Button, Flex, Heading, Select, Stack, Text } from '@chakra-ui/react';
import React, { useState } from 'react';

const ScenarioPanel = ({ selectedId, revisions, assignments, isBusy, onAssign, onUnassign }) => {
	const [revisionId, setRevisionId] = useState('');
	return (
		<Box as="section" aria-labelledby="assignments-heading" bg="white" p={{ base: 4, md: 6 }} borderRadius="xl" borderWidth="1px">
			<Heading size="md" mb={4}>
				<span id="assignments-heading">Scenario assignments</span>
			</Heading>
			<Text color="gray.600" mb={4}>Choose from your published scenario revisions.</Text>
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
				<Button colorScheme="blue" isLoading={isBusy} isDisabled={!selectedId || !revisionId} onClick={() => onAssign(revisionId)}>
					Assign
				</Button>
			</Stack>
			{assignments.length === 0 ? (
				<Text>No scenarios assigned.</Text>
			) : (
				assignments.map((item) => (
					<Flex key={item.id} justify="space-between" align={{ base: 'start', sm: 'center' }} direction={{ base: 'column', sm: 'row' }} gap={3} py={3} borderBottomWidth="1px">
						<Box><Text fontWeight="semibold">{item.scenario_name}</Text><Text fontSize="sm" color="gray.600">Revision {item.revision_number} <Badge ml={2} colorScheme="green">{item.status}</Badge></Text></Box>
						<Button size="sm" colorScheme="red" variant="outline" isDisabled={isBusy} onClick={() => onUnassign(item)}>
							Unassign
						</Button>
					</Flex>
				))
			)}
		</Box>
	);
};

export default ScenarioPanel;
