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
import { EmptyState } from '../FeedbackStates';

const StudentPanel = ({ className, selectedId, students, isBusy, onCreate, onAdd, onReset, onRemove }) => {
	const [username, setUsername] = useState('');
	const [password, setPassword] = useState('');

	const create = async () => {
		await onCreate(username, password);
		setUsername('');
		setPassword('');
	};

	return (
		<Box
			as="section"
			aria-labelledby="roster-heading"
			bg="white"
			p={{ base: 4, md: 6 }}
			borderRadius="xl"
			borderWidth="1px"
		>
			<Heading size="md" mb={4}>
				<span id="roster-heading">Student roster</span>
			</Heading>
			<Text color="gray.600" mb={5}>
				Create student accounts or add an existing student to {className || 'the selected class'}.
			</Text>
			<Stack direction={{ base: 'column', md: 'row' }} mb={6} align="end">
				<FormControl>
					<FormLabel htmlFor="student-username">Username</FormLabel>
					<Input id="student-username" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} />
				</FormControl>
				<FormControl>
					<FormLabel htmlFor="student-temporary-password">Temporary password</FormLabel>
					<Input id="student-temporary-password" autoComplete="new-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
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
				<Button
					minW="160px"
					isLoading={isBusy}
					isDisabled={!selectedId || !username.trim()}
					onClick={() => onAdd(username)}
				>
					Add existing
				</Button>
			</Stack>
			{students.length === 0 ? (
				<EmptyState
					title="No students in this class"
					description={`No students have joined ${className || 'this class'} yet. Create a student account above or add an existing student by username.`}
				/>
			) : (
				<Box overflowX="auto">
					<Table>
						<caption className="chakra-visually-hidden">Students in the selected class</caption>
						<Thead>
							<Tr>
								<Th scope="col">Username</Th>
								<Th scope="col">Actions</Th>
							</Tr>
						</Thead>
						<Tbody>
							{students.map((student) => (
								<Tr key={student.id}>
									<Td>{student.username}</Td>
									<Td>
										<Flex gap={2} wrap="wrap">
											<Button size="sm" isDisabled={isBusy} onClick={() => onReset(student)}>
												Reset password
											</Button>
											<Button
												size="sm"
												colorScheme="red"
												variant="outline"
												isDisabled={isBusy}
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
				</Box>
			)}
		</Box>
	);
};

export default StudentPanel;
