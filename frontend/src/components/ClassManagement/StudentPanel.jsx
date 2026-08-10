import {
	Box,
	Button,
	Flex,
	FormControl,
	FormLabel,
	Heading,
	Input,
	Stack,
	Table,
	Tbody,
	Td,
	Text,
	Th,
	Thead,
	Tr,
} from '@chakra-ui/react';
import React, { useState } from 'react';

const StudentPanel = ({ className, selectedId, students, isBusy, onCreate, onAdd, onReset, onRemove }) => {
	const [username, setUsername] = useState('');
	const [password, setPassword] = useState('');

	const create = async () => {
		await onCreate(username, password);
		setUsername('');
		setPassword('');
	};

	return (
		<Box bg="white" p={6} borderRadius="xl" mt={6}>
			<Heading size="md" mb={4}>
				Students in {className || 'the selected class'}
			</Heading>
			<Stack direction={{ base: 'column', md: 'row' }} mb={6} align="end">
				<FormControl>
					<FormLabel>Username</FormLabel>
					<Input value={username} onChange={(event) => setUsername(event.target.value)} />
				</FormControl>
				<FormControl>
					<FormLabel>Temporary password</FormLabel>
					<Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
				</FormControl>
				<Button
					colorScheme="blue"
					minW="140px"
					isDisabled={!selectedId || !username.trim() || password.length < 10}
					isLoading={isBusy}
					onClick={create}
				>
					Create student
				</Button>
				<Button minW="160px" isDisabled={!selectedId || !username.trim()} onClick={() => onAdd(username)}>
					Add existing
				</Button>
			</Stack>
			{students.length === 0 ? (
				<Text>No students in this class.</Text>
			) : (
				<Table>
					<Thead>
						<Tr>
							<Th>Username</Th>
							<Th>Actions</Th>
						</Tr>
					</Thead>
					<Tbody>
						{students.map((student) => (
							<Tr key={student.id}>
								<Td>{student.username}</Td>
								<Td>
									<Flex gap={2}>
										<Button size="sm" onClick={() => onReset(student)}>
											Reset password
										</Button>
										<Button
											size="sm"
											colorScheme="red"
											variant="outline"
											onClick={() => onRemove(student)}
										>
											Remove
										</Button>
									</Flex>
								</Td>
							</Tr>
						))}
					</Tbody>
				</Table>
			)}
		</Box>
	);
};

export default StudentPanel;
