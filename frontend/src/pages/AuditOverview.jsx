import {
	Alert,
	AlertIcon,
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
} from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import { listAuditEntries } from '../api/audit';

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
			<Heading mb={6}>Administrative audit</Heading>
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
								<Td>{new Date(entry.created_at).toLocaleString()}</Td>
								<Td>{entry.action}</Td>
								<Td>
									{entry.target_type}: {entry.target_id}
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
