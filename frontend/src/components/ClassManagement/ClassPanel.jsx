import { Box, Button, Heading, Input, Select, Stack } from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';

const ClassPanel = ({ classes, selectedId, selectedClass, isBusy, onSelect, onCreate, onRename, onArchive }) => {
	const [newName, setNewName] = useState('');
	const [editedName, setEditedName] = useState('');

	useEffect(() => setEditedName(selectedClass?.name || ''), [selectedClass]);

	const create = async () => {
		await onCreate(newName);
		setNewName('');
	};

	return (
		<Box bg="white" p={6} borderRadius="xl">
			<Heading size="md" mb={4}>
				Classes
			</Heading>
			<Stack>
				<Input
					aria-label="New class name"
					placeholder="New class name"
					value={newName}
					onChange={(event) => setNewName(event.target.value)}
				/>
				<Button colorScheme="blue" isDisabled={!newName.trim()} isLoading={isBusy} onClick={create}>
					Create class
				</Button>
				<Select
					aria-label="Select a class"
					placeholder="Select a class"
					value={selectedId}
					onChange={(event) => onSelect(event.target.value)}
				>
					{classes.map((item) => (
						<option key={item.id} value={item.id}>
							{item.name}
						</option>
					))}
				</Select>
				{selectedClass && (
					<>
						<Input
							aria-label="Class name"
							value={editedName}
							onChange={(event) => setEditedName(event.target.value)}
						/>
						<Button
							variant="outline"
							isDisabled={!editedName.trim() || editedName.trim() === selectedClass.name}
							onClick={() => onRename(editedName)}
						>
							Rename class
						</Button>
						<Button colorScheme="red" variant="outline" onClick={onArchive}>
							Archive class
						</Button>
					</>
				)}
			</Stack>
		</Box>
	);
};

export default ClassPanel;
