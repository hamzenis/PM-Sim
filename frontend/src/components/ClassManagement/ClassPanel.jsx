import { Box, Button, FormControl, FormLabel, Heading, Input, Select, Stack, Text } from '@chakra-ui/react';
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
		<Box bg="white" p={{ base: 4, md: 6 }} borderRadius="xl" borderWidth="1px">
			<Heading size="md" mb={4}>
				Choose a class
			</Heading>
			<Text color="gray.600" mb={4}>Select the class you want to work with, or create a new one.</Text>
			<Stack spacing={4}>
				<FormControl>
					<FormLabel htmlFor="current-class">Current class</FormLabel>
					<Select
						id="current-class"
						placeholder="Select a class"
						value={selectedId}
						onChange={(event) => onSelect(event.target.value)}
					>
						{classes.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
					</Select>
				</FormControl>
				<Heading size="sm">Create a class</Heading>
				<Input
					aria-label="New class name"
					placeholder="New class name"
					value={newName}
					onChange={(event) => setNewName(event.target.value)}
				/>
				<Button colorScheme="blue" isDisabled={!newName.trim()} isLoading={isBusy} onClick={create}>
					Create class
				</Button>
				{selectedClass && (
					<>
						<Heading size="sm" pt={2}>Manage {selectedClass.name}</Heading>
						<Input
							aria-label="Class name"
							value={editedName}
							onChange={(event) => setEditedName(event.target.value)}
						/>
						<Button
							variant="outline"
							isLoading={isBusy}
							isDisabled={!editedName.trim() || editedName.trim() === selectedClass.name}
							onClick={() => onRename(editedName)}
						>
							Rename class
						</Button>
						<Button colorScheme="red" variant="outline" isDisabled={isBusy} onClick={onArchive}>
							Archive class
						</Button>
					</>
				)}
			</Stack>
		</Box>
	);
};

export default ClassPanel;
