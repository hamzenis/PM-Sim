import {
	Alert,
	AlertIcon,
	Box,
	Button,
	Container,
	Flex,
	FormControl,
	FormLabel,
	Heading,
	Input,
	Select,
	SimpleGrid,
	Stack,
	Table,
	Tbody,
	Td,
	Text,
	Th,
	Thead,
	Tr,
} from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';
import {
	addStudent,
	archiveClass,
	assignScenario,
	createClass,
	importStudents,
	listAssignedScenarios,
	listClasses,
	listClassResults,
	listStudents,
	removeStudent,
	resetStudentPassword,
	unassignScenario,
} from '../api/classes';
import { listOwnedScenarios, listScenarioRevisions } from '../api/scenarios';

const CourseOverview = () => {
	const [classes, setClasses] = useState([]);
	const [selectedId, setSelectedId] = useState('');
	const [students, setStudents] = useState([]);
	const [assignments, setAssignments] = useState([]);
	const [results, setResults] = useState([]);
	const [publishedRevisions, setPublishedRevisions] = useState([]);
	const [newClassName, setNewClassName] = useState('');
	const [username, setUsername] = useState('');
	const [password, setPassword] = useState('');
	const [revisionId, setRevisionId] = useState('');
	const [error, setError] = useState('');
	const [message, setMessage] = useState('');
	const [isBusy, setIsBusy] = useState(false);

	const selectedClass = classes.find((item) => item.id === selectedId);

	const loadClasses = async () => {
		const loaded = await listClasses();
		setClasses(loaded);
		setSelectedId((current) => current || loaded[0]?.id || '');
	};

	useEffect(() => {
		loadClasses().catch((requestError) => setError(requestError.message));
		listOwnedScenarios()
			.then((scenarios) => Promise.all(scenarios.map((scenario) => listScenarioRevisions(scenario.id))))
			.then((revisionGroups) =>
				setPublishedRevisions(revisionGroups.flat().filter((item) => item.status === 'published'))
			)
			.catch((requestError) => setError(requestError.message));
	}, []);

	useEffect(() => {
		if (!selectedId) {
			setStudents([]);
			setAssignments([]);
			setResults([]);
			return;
		}
		Promise.all([listStudents(selectedId), listAssignedScenarios(selectedId), listClassResults(selectedId)])
			.then(([loadedStudents, loadedAssignments, loadedResults]) => {
				setStudents(loadedStudents);
				setAssignments(loadedAssignments);
				setResults(loadedResults);
			})
			.catch((requestError) => setError(requestError.message));
	}, [selectedId]);

	const runAction = async (action, successMessage) => {
		setIsBusy(true);
		setError('');
		setMessage('');
		try {
			await action();
			setMessage(successMessage);
			if (selectedId) {
				const [loadedStudents, loadedAssignments, loadedResults] = await Promise.all([
					listStudents(selectedId),
					listAssignedScenarios(selectedId),
					listClassResults(selectedId),
				]);
				setStudents(loadedStudents);
				setAssignments(loadedAssignments);
				setResults(loadedResults);
			}
		} catch (requestError) {
			setError(requestError.message || 'The request failed.');
		} finally {
			setIsBusy(false);
		}
	};

	const handleCreateClass = () =>
		runAction(async () => {
			const created = await createClass(newClassName);
			setNewClassName('');
			await loadClasses();
			setSelectedId(created.id);
		}, 'Class created.');

	const handleCreateStudent = () =>
		runAction(async () => {
			await importStudents(selectedId, [{ username, password }]);
			setUsername('');
			setPassword('');
		}, 'Student created and added to the class.');

	return (
		<Container maxW="7xl" py={8} flexGrow={1}>
			<Heading mb={2}>Class management</Heading>
			<Text color="gray.600" mb={6}>
				Create classes, manage students, and assign published scenarios.
			</Text>
			{error && (
				<Alert status="error" mb={4}>
					<AlertIcon />
					{error}
				</Alert>
			)}
			{message && (
				<Alert status="success" mb={4}>
					<AlertIcon />
					{message}
				</Alert>
			)}

			<SimpleGrid columns={{ base: 1, lg: 3 }} spacing={6}>
				<Box bg="white" p={6} borderRadius="xl">
					<Heading size="md" mb={4}>
						Classes
					</Heading>
					<Stack>
						<Input
							placeholder="New class name"
							value={newClassName}
							onChange={(event) => setNewClassName(event.target.value)}
						/>
						<Button
							colorScheme="blue"
							isDisabled={!newClassName.trim()}
							isLoading={isBusy}
							onClick={handleCreateClass}
						>
							Create class
						</Button>
						<Select
							placeholder="Select a class"
							value={selectedId}
							onChange={(event) => setSelectedId(event.target.value)}
						>
							{classes.map((item) => (
								<option key={item.id} value={item.id}>
									{item.name}
								</option>
							))}
						</Select>
						{selectedClass && (
							<Button
								colorScheme="red"
								variant="outline"
								onClick={() =>
									runAction(async () => {
										await archiveClass(selectedId);
										setSelectedId('');
										await loadClasses();
									}, 'Class archived.')
								}
							>
								Archive class
							</Button>
						)}
					</Stack>
				</Box>

				<Box bg="white" p={6} borderRadius="xl">
					<Heading size="md" mb={4}>
						Add a student
					</Heading>
					<Stack>
						<FormControl>
							<FormLabel>Username</FormLabel>
							<Input value={username} onChange={(event) => setUsername(event.target.value)} />
						</FormControl>
						<FormControl>
							<FormLabel>Temporary password</FormLabel>
							<Input
								type="password"
								value={password}
								onChange={(event) => setPassword(event.target.value)}
							/>
						</FormControl>
						<Button
							colorScheme="blue"
							isDisabled={!selectedId || !username.trim() || password.length < 10}
							isLoading={isBusy}
							onClick={handleCreateStudent}
						>
							Create student
						</Button>
						<Button
							variant="outline"
							isDisabled={!selectedId || !username.trim()}
							onClick={() => runAction(() => addStudent(selectedId, username), 'Existing student added.')}
						>
							Add existing student
						</Button>
					</Stack>
				</Box>

				<Box bg="white" p={6} borderRadius="xl">
					<Heading size="md" mb={4}>
						Assign a scenario
					</Heading>
					<Stack>
						<Select
							placeholder="Published revision"
							value={revisionId}
							onChange={(event) => setRevisionId(event.target.value)}
						>
							{publishedRevisions.map((revision) => (
								<option key={revision.id} value={revision.id}>
									{revision.definition.name} (revision {revision.revision_number})
								</option>
							))}
						</Select>
						<Button
							colorScheme="blue"
							isDisabled={!selectedId || !revisionId}
							onClick={() =>
								runAction(() => assignScenario(selectedId, revisionId), 'Scenario assigned.')
							}
						>
							Assign
						</Button>
					</Stack>
				</Box>
			</SimpleGrid>

			<Box bg="white" p={6} borderRadius="xl" mt={6}>
				<Heading size="md" mb={4}>
					Students in {selectedClass?.name || 'the selected class'}
				</Heading>
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
											<Button
												size="sm"
												onClick={() => {
													const value = window.prompt(`New password for ${student.username}`);
													if (value)
														runAction(
															() => resetStudentPassword(selectedId, student.id, value),
															'Password reset.'
														);
												}}
											>
												Reset password
											</Button>
											<Button
												size="sm"
												colorScheme="red"
												variant="outline"
												onClick={() =>
													runAction(
														() => removeStudent(selectedId, student.id),
														'Student removed.'
													)
												}
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

			<SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6} mt={6}>
				<Box bg="white" p={6} borderRadius="xl">
					<Heading size="md" mb={4}>
						Assigned scenarios
					</Heading>
					{assignments.length === 0 ? (
						<Text>No scenarios assigned.</Text>
					) : (
						assignments.map((item) => (
							<Flex key={item.id} justify="space-between" align="center" py={2}>
								<Text>
									Revision {item.revision_number} ({item.status})
								</Text>
								<Button
									size="sm"
									onClick={() =>
										runAction(() => unassignScenario(selectedId, item.id), 'Scenario unassigned.')
									}
								>
									Unassign
								</Button>
							</Flex>
						))
					)}
				</Box>
				<Box bg="white" p={6} borderRadius="xl">
					<Heading size="md" mb={4}>
						Simulation results
					</Heading>
					{results.length === 0 ? (
						<Text>No simulation results yet.</Text>
					) : (
						results.map((result) => (
							<Flex key={result.run_id} justify="space-between" py={2}>
								<Text>{result.student_username}</Text>
								<Text>
									{result.status}, week {result.current_week}
								</Text>
							</Flex>
						))
					)}
				</Box>
			</SimpleGrid>
		</Container>
	);
};

export default CourseOverview;
