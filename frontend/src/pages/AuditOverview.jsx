import { Box, Button, Container, Flex, Heading, Table, Tbody, Td, Th, Thead, Tr, Text } from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import { listAuditEntries } from '../api/audit';
import { formatDateTime, plainLanguageLabel } from '../utils/resultPresentation';
import { EmptyState, PageLoadingState, RequestError } from '../components/FeedbackStates';

const PAGE_SIZE = 50;

const AuditOverview = () => {
	const [entries, setEntries] = useState([]);
	const [offset, setOffset] = useState(0);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState('');

	useEffect(() => {
		setIsLoading(true);
		setError('');
		listAuditEntries(PAGE_SIZE, offset)
			.then(setEntries)
			.catch((requestError) => setError(requestError.message))
			.finally(() => setIsLoading(false));
	}, [offset]);

	return (
		<Container maxW="7xl" py={8} flexGrow={1}>
			<Heading mb={2}>Administrative audit</Heading>
			<Text mb={6}>
				Professor activity history. Support identifiers and raw records are available in each row’s technical
				details.
			</Text>
			{error && <RequestError title="Couldn’t load audit activity" message={error} mb={4} />}
			{isLoading ? (
				<PageLoadingState label="Loading audit activity…" />
			) : entries.length === 0 ? (
				<EmptyState
					title="No audit activity on this page"
					description={
						offset === 0
							? 'No professor actions have been recorded yet. Activity will appear here after professors manage classes or scenarios.'
							: 'There are no more recorded actions. Return to the previous page to review earlier activity.'
					}
				/>
			) : (
				<Table bg="white">
								<caption className="chakra-visually-hidden">Administrative audit events</caption>
					<Thead>
						<Tr>
							<Th>Time</Th>
							<Th>Action</Th>
							<Th>Target</Th>
						</Tr>
					</Thead>
					<Tbody>
						{entries.map((entry) => (
							<Tr key={entry.id}>
								<Td>{formatDateTime(entry.created_at)}</Td>
								<Td>{plainLanguageLabel(entry.action)}</Td>
								<Td>
									{plainLanguageLabel(entry.target_type)}
									<Box as="details" mt={1}>
										<Box as="summary" cursor="pointer" fontWeight="semibold">
											Technical details
										</Box>
										<Box as="pre" overflowX="auto" fontSize="xs">
											{JSON.stringify(entry.details, null, 2)}
										</Box>
									</Box>
								</Td>
							</Tr>
						))}
					</Tbody>
				</Table>
			)}
			<Flex mt={4} justify="space-between">
				<Button isDisabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>
					Previous
				</Button>
				<Button isDisabled={entries.length < PAGE_SIZE} onClick={() => setOffset(offset + PAGE_SIZE)}>
					Next
				</Button>
			</Flex>
		</Container>
	);
};

export default AuditOverview;
