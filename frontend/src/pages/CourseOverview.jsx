import { Alert, AlertIcon, Container, Heading, SimpleGrid, Text } from '@chakra-ui/react';
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
		loadClasses().catch((requestError) => setError(requestError.message));
		listOwnedScenarios()
			.then((scenarios) => Promise.all(scenarios.map((scenario) => listScenarioRevisions(scenario.id))))
			.then((groups) => setPublishedRevisions(groups.flat().filter((item) => item.status === 'published')))
			.catch((requestError) => setError(requestError.message));
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

			<SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
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
				<ScenarioPanel
					selectedId={selectedId}
					revisions={publishedRevisions}
					assignments={assignments}
					onAssign={(revisionId) =>
						runAction(() => assignScenario(selectedId, revisionId), 'Scenario assigned.')
					}
					onUnassign={(assignment) =>
						askForConfirmation(
							'Unassign scenario',
							`Unassign revision ${assignment.revision_number} from this class?`,
							'Unassign',
							() => unassignScenario(selectedId, assignment.id),
							'Scenario unassigned.'
						)
					}
				/>
			</SimpleGrid>

			<StudentPanel
				className={selectedClass?.name}
				selectedId={selectedId}
				students={students}
				isBusy={isBusy}
				onCreate={(username, password) =>
					runAction(
						() => importStudents(selectedId, [{ username, password }]),
						'Student created and added to the class.'
					)
				}
				onAdd={(username) => runAction(() => addStudent(selectedId, username), 'Existing student added.')}
				onReset={setResetStudent}
				onRemove={(student) =>
					askForConfirmation(
						'Remove student',
						`Remove ${student.username} from this class?`,
						'Remove',
						() => removeStudent(selectedId, student.id),
						'Student removed.'
					)
				}
			/>

			<ResultsPanel classId={selectedId} results={results} />

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
