import {
	Alert,
	AlertIcon,
	Box,
	Button,
	Container,
	Flex,
	Heading,
	Spinner,
	Table,
	Tbody,
	Td,
	Th,
	Thead,
	Tr,
	Text,
} from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import { listAuditEntries } from '../api/audit';
import { formatDateTime, plainLanguageLabel } from '../utils/resultPresentation';

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
			<Text mb={6}>Professor activity history. Support identifiers and raw records are available in each row’s technical details.</Text>
			{error && (
				<Alert status="error" mb={4}>
					<AlertIcon />
					{error}
				</Alert>
			)}
			{isLoading ? (
				<Spinner />
			) : (
				<Table bg="white">
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
									<Box as="details" mt={1}><Box as="summary" cursor="pointer" fontWeight="semibold">Technical details</Box><Text>Target UUID: {entry.target_id}</Text><Box as="pre" overflowX="auto" fontSize="xs">{JSON.stringify(entry.details, null, 2)}</Box></Box>
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
