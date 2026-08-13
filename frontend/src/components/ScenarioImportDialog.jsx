import {
	Button,
	FormControl,
	FormErrorMessage,
	FormLabel,
	Modal,
	ModalBody,
	ModalCloseButton,
	ModalContent,
	ModalFooter,
	ModalHeader,
	ModalOverlay,
	Textarea,
} from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';

const ScenarioImportDialog = ({ isOpen, isBusy, onCancel, onImport }) => {
	const [source, setSource] = useState('');
	const [parseError, setParseError] = useState('');

	useEffect(() => {
		if (isOpen) {
			setSource('');
			setParseError('');
		}
	}, [isOpen]);

	const submit = () => {
		try {
			const definition = JSON.parse(source);
			setParseError('');
			onImport(definition);
		} catch (_error) {
			setParseError('Enter a valid JSON scenario definition.');
		}
	};

	return (
		<Modal isOpen={isOpen} onClose={onCancel} size="3xl">
			<ModalOverlay />
			<ModalContent>
				<ModalHeader>Import scenario JSON</ModalHeader>
				<ModalCloseButton />
				<ModalBody>
					<FormControl isInvalid={Boolean(parseError)}>
						<FormLabel htmlFor="scenario-definition">Scenario definition</FormLabel>
						<Textarea
							id="scenario-definition"
							minH="360px"
							fontFamily="mono"
							value={source}
							onChange={(event) => setSource(event.target.value)}
						/>
						<FormErrorMessage>{parseError}</FormErrorMessage>
					</FormControl>
				</ModalBody>
				<ModalFooter>
					<Button variant="ghost" onClick={onCancel}>
						Cancel
					</Button>
					<Button colorScheme="blue" ml={3} isDisabled={!source.trim()} isLoading={isBusy} onClick={submit}>
						Validate and import
					</Button>
				</ModalFooter>
			</ModalContent>
		</Modal>
	);
};

export default ScenarioImportDialog;
