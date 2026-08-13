import {
	Button,
	FormControl,
	FormErrorMessage,
	FormLabel,
	Input,
	Modal,
	ModalBody,
	ModalCloseButton,
	ModalContent,
	ModalFooter,
	ModalHeader,
	ModalOverlay,
} from '@chakra-ui/react';
import React, { useEffect, useState } from 'react';

const ResetPasswordDialog = ({ student, isOpen, isBusy, onCancel, onSave }) => {
	const [password, setPassword] = useState('');
	const [confirmation, setConfirmation] = useState('');

	useEffect(() => {
		if (isOpen) {
			setPassword('');
			setConfirmation('');
		}
	}, [isOpen]);

	const isTooShort = password.length > 0 && password.length < 10;
	const doesNotMatch = confirmation.length > 0 && password !== confirmation;
	const isValid = password.length >= 10 && password === confirmation;

	return (
		<Modal isOpen={isOpen} onClose={onCancel}>
			<ModalOverlay />
			<ModalContent>
				<ModalHeader>Reset password for {student?.username}</ModalHeader>
				<ModalCloseButton />
				<ModalBody>
					<FormControl isInvalid={isTooShort} mb={4}>
						<FormLabel htmlFor="reset-password">New temporary password</FormLabel>
						<Input id="reset-password" autoComplete="new-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
						<FormErrorMessage>The password must contain at least 10 characters.</FormErrorMessage>
					</FormControl>
					<FormControl isInvalid={doesNotMatch}>
						<FormLabel htmlFor="reset-password-confirmation">Repeat password</FormLabel>
						<Input
							id="reset-password-confirmation"
							autoComplete="new-password"
							type="password"
							value={confirmation}
							onChange={(event) => setConfirmation(event.target.value)}
						/>
						<FormErrorMessage>The passwords do not match.</FormErrorMessage>
					</FormControl>
				</ModalBody>
				<ModalFooter>
					<Button variant="ghost" onClick={onCancel}>
						Cancel
					</Button>
					<Button
						colorScheme="blue"
						ml={3}
						isDisabled={!isValid}
						isLoading={isBusy}
						onClick={() => onSave(password)}
					>
						Reset password
					</Button>
				</ModalFooter>
			</ModalContent>
		</Modal>
	);
};

export default ResetPasswordDialog;
