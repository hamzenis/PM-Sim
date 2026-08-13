import { Alert, AlertIcon, Box, Container, Heading, SimpleGrid, Stack, Text } from '@chakra-ui/react';
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
	renameClass,
	resetStudentPassword,
	unassignScenario,
} from '../api/classes';
import { listOwnedScenarios, listScenarioRevisions } from '../api/scenarios';
import ClassPanel from '../components/ClassManagement/ClassPanel';
import ConfirmDialog from '../components/ClassManagement/ConfirmDialog';
import ResetPasswordDialog from '../components/ClassManagement/ResetPasswordDialog';
import ResultsPanel from '../components/ClassManagement/ResultsPanel';
import ScenarioPanel from '../components/ClassManagement/ScenarioPanel';
import StudentPanel from '../components/ClassManagement/StudentPanel';
import { EmptyState, PageLoadingState, RequestError } from '../components/FeedbackStates';

const CourseOverview = () => {
	const [classes, setClasses] = useState([]);
	const [selectedId, setSelectedId] = useState('');
	const [students, setStudents] = useState([]);
	const [assignments, setAssignments] = useState([]);
	const [results, setResults] = useState([]);
	const [publishedRevisions, setPublishedRevisions] = useState([]);
	const [error, setError] = useState('');
	const [message, setMessage] = useState('');
	const [isBusy, setIsBusy] = useState(false);
	const [isLoading, setIsLoading] = useState(true);
	const [resetStudent, setResetStudent] = useState(null);
	const [confirmation, setConfirmation] = useState(null);

	const selectedClass = classes.find((item) => item.id === selectedId);

	const loadClasses = async () => {
		const loaded = await listClasses();
		setClasses(loaded);
		setSelectedId((current) => current || loaded[0]?.id || '');
	};

	const loadClassDetails = async (classId) => {
		if (!classId) {
			setStudents([]);
			setAssignments([]);
			setResults([]);
			return;
		}
		const [loadedStudents, loadedAssignments, loadedResults] = await Promise.all([
			listStudents(classId),
			listAssignedScenarios(classId),
			listClassResults(classId),
		]);
		setStudents(loadedStudents);
		setAssignments(loadedAssignments);
		setResults(loadedResults);
	};

	useEffect(() => {
		Promise.all([
			loadClasses(),
			listOwnedScenarios()
				.then((scenarios) => Promise.all(scenarios.map((scenario) => listScenarioRevisions(scenario.id))))
				.then((groups) => setPublishedRevisions(groups.flat().filter((item) => item.status === 'published'))),
		])
			.catch((requestError) => setError(requestError.message || 'Could not load the professor workspace.'))
			.finally(() => setIsLoading(false));
	}, []);

	useEffect(() => {
		let active = true;
		loadClassDetails(selectedId).catch((requestError) => {
			if (active) setError(requestError.message);
		});
		return () => {
			active = false;
		};
	}, [selectedId]);

	const runAction = async (action, successMessage, refreshDetails = true) => {
		if (isBusy) return false;
		setIsBusy(true);
		setError('');
		setMessage('');
		try {
			await action();
			setMessage(successMessage);
			if (refreshDetails) await loadClassDetails(selectedId);
			return true;
		} catch (requestError) {
			setError(requestError.message || 'The request failed.');
			return false;
		} finally {
			setIsBusy(false);
		}
	};

	const createNewClass = async (name) => {
		await runAction(
			async () => {
				const created = await createClass(name);
				await loadClasses();
				setSelectedId(created.id);
			},
			'Class created.',
			false
		);
	};

	const renameSelectedClass = async (name) => {
		await runAction(async () => {
			await renameClass(selectedId, name);
			await loadClasses();
		}, 'Class renamed.');
	};

	const askForConfirmation = (title, message, confirmLabel, action, successMessage, refreshDetails = true) => {
		setConfirmation({ title, message, confirmLabel, action, successMessage, refreshDetails });
	};

	const confirmAction = async () => {
		const completed = await runAction(
			confirmation.action,
			confirmation.successMessage,
			confirmation.refreshDetails
		);
		if (completed) setConfirmation(null);
	};

	const archiveSelectedClass = () => {
		askForConfirmation(
			'Archive class',
			`Archive ${selectedClass.name}? It will no longer appear in the active class list.`,
			'Archive',
			async () => {
				await archiveClass(selectedId);
				setSelectedId('');
				await loadClasses();
			},
			'Class archived.',
			false
		);
	};

	return (
		<Container maxW="7xl" py={{ base: 5, md: 8 }} flexGrow={1}>
			<Heading mb={2}>Professor workspace</Heading>
			<Text color="gray.600" mb={6}>
				Manage each class roster, scenario assignments, and simulation results in one place.
			</Text>
			{error && <RequestError title="Couldn’t complete the request" message={error} mb={4} />}
			{message && (
				<Alert status="success" mb={4}>
					<AlertIcon />
					{message}
				</Alert>
			)}

			{isLoading ? (
				<PageLoadingState label="Loading professor workspace…" />
			) : (
				<>
					{selectedClass && (
						<Box bg="blue.50" borderRadius="xl" p={{ base: 4, md: 6 }} mb={6}>
							<Text fontSize="sm" color="blue.700" fontWeight="bold" textTransform="uppercase">
								Selected class
							</Text>
							<Heading size="lg" mt={1}>
								{selectedClass.name}
							</Heading>
							<Text color="gray.600" mt={2}>
								Review your roster, assignments, and student progress below.
							</Text>
						</Box>
					)}

					<Box>
						<ClassPanel
							classes={classes}
							selectedId={selectedId}
							selectedClass={selectedClass}
							isBusy={isBusy}
							onSelect={setSelectedId}
							onCreate={createNewClass}
							onRename={renameSelectedClass}
							onArchive={archiveSelectedClass}
						/>
					</Box>

					{selectedClass ? (
						<Stack spacing={6} mt={6}>
							<SimpleGrid columns={{ base: 1, sm: 3 }} spacing={4}>
								{[
									['Students', students.length],
									['Assigned scenarios', assignments.length],
									['Results', results.length],
								].map(([label, count]) => (
									<Box key={label} bg="white" borderWidth="1px" borderRadius="lg" p={4}>
										<Text color="gray.600" fontSize="sm">
											{label}
										</Text>
										<Text fontSize="3xl" fontWeight="bold">
											{count}
										</Text>
									</Box>
								))}
							</SimpleGrid>
							<StudentPanel
								className={selectedClass.name}
								selectedId={selectedId}
								students={students}
								isBusy={isBusy}
								onCreate={(username, password) =>
									runAction(
										() => importStudents(selectedId, [{ username, password }]),
										`Student ${username} created and added.`
									)
								}
								onAdd={(username) =>
									runAction(() => addStudent(selectedId, username), `Student ${username} added.`)
								}
								onReset={setResetStudent}
								onRemove={(student) =>
									askForConfirmation(
										'Remove student',
										`Remove ${student.username} from ${selectedClass.name}?`,
										'Remove',
										() => removeStudent(selectedId, student.id),
										`${student.username} removed from the class.`
									)
								}
							/>
							<ScenarioPanel
								selectedId={selectedId}
								revisions={publishedRevisions}
								assignments={assignments}
								isBusy={isBusy}
								onAssign={(revisionId) =>
									runAction(() => assignScenario(selectedId, revisionId), 'Scenario assigned.')
								}
								onUnassign={(assignment) =>
									askForConfirmation(
										'Unassign scenario',
										`Unassign ${assignment.scenario_name}, revision ${assignment.revision_number}, from ${selectedClass.name}?`,
										'Unassign',
										() => unassignScenario(selectedId, assignment.id),
										'Scenario unassigned.'
									)
								}
							/>
							<ResultsPanel classId={selectedId} results={results} />
						</Stack>
					) : (
						<Box mt={6}>
							<EmptyState
								title="No classes yet"
								description="There are no active classes to select. Create a class above to start adding students and assigning scenarios."
							/>
						</Box>
					)}
				</>
			)}

			<ResetPasswordDialog
				student={resetStudent}
				isOpen={Boolean(resetStudent)}
				isBusy={isBusy}
				onCancel={() => setResetStudent(null)}
				onSave={async (password) => {
					const completed = await runAction(
						() => resetStudentPassword(selectedId, resetStudent.id, password),
						'Password reset.'
					);
					if (completed) setResetStudent(null);
				}}
			/>
			<ConfirmDialog
				isOpen={Boolean(confirmation)}
				title={confirmation?.title}
				message={confirmation?.message}
				confirmLabel={confirmation?.confirmLabel}
				isBusy={isBusy}
				onCancel={() => setConfirmation(null)}
				onConfirm={confirmAction}
			/>
		</Container>
	);
};

export default CourseOverview;
