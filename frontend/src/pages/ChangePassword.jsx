import {
	Alert,
	AlertIcon,
	Box,
	Button,
	Container,
	FormControl,
	FormLabel,
	Heading,
	Input,
	Stack,
	Text,
} from '@chakra-ui/react';
import React, { useContext, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { changePassword } from '../api/auth';
import { AuthContext } from '../context/AuthProvider';

const ChangePassword = () => {
	const navigate = useNavigate();
	const { setCurrentUser } = useContext(AuthContext);
	const [currentPassword, setCurrentPassword] = useState('');
	const [newPassword, setNewPassword] = useState('');
	const [confirmation, setConfirmation] = useState('');
	const [error, setError] = useState('');
	const [isSaving, setIsSaving] = useState(false);
	const saveInProgress = useRef(false);
	const errorRef = useRef(null);
	const isValid = currentPassword !== '' && newPassword.length >= 10 && confirmation !== '';

	useEffect(() => {
		if (error) errorRef.current?.focus();
	}, [error]);

	const submit = async (event) => {
		event.preventDefault();
		if (!isValid || saveInProgress.current) return;
		if (newPassword !== confirmation) {
			setError('The new passwords do not match.');
			return;
		}
		saveInProgress.current = true;
		setIsSaving(true);
		setError('');
		try {
			await changePassword(currentPassword, newPassword);
			setCurrentUser(null);
			navigate('/login');
		} catch (requestError) {
			setError(requestError.message || 'Could not change the password.');
		} finally {
			saveInProgress.current = false;
			setIsSaving(false);
		}
	};

	return (
		<Container maxW="lg" py={12} flexGrow={1}>
			<Box as="form" onSubmit={submit} bg="white" borderRadius="xl" p={8}>
				<Heading size="lg" mb={2}>
					Change password
				</Heading>
				<Text color="gray.600" mb={6}>
					You will need to sign in again after changing your password.
				</Text>
				{error && (
					<Alert ref={errorRef} status="error" role="alert" tabIndex={-1} mb={4}>
						<AlertIcon />
						{error}
					</Alert>
				)}
				<Stack spacing={4}>
					<FormControl isRequired>
						<FormLabel htmlFor="current-password">Current password</FormLabel>
						<Input
							id="current-password"
							name="currentPassword"
							type="password"
							autoComplete="current-password"
							value={currentPassword}
							onChange={(event) => setCurrentPassword(event.target.value)}
						/>
					</FormControl>
					<FormControl isRequired>
						<FormLabel htmlFor="new-password">New password</FormLabel>
						<Input
							id="new-password"
							name="newPassword"
							type="password"
							autoComplete="new-password"
							value={newPassword}
							onChange={(event) => setNewPassword(event.target.value)}
						/>
					</FormControl>
					<FormControl isRequired>
						<FormLabel htmlFor="confirm-password">Repeat new password</FormLabel>
						<Input
							id="confirm-password"
							name="confirmPassword"
							type="password"
							autoComplete="new-password"
							value={confirmation}
							onChange={(event) => setConfirmation(event.target.value)}
						/>
					</FormControl>
					<Button
						type="submit"
						colorScheme="blue"
						isLoading={isSaving}
						loadingText="Changing password"
						isDisabled={!isValid || isSaving}
					>
						Change password
					</Button>
				</Stack>
			</Box>
		</Container>
	);
};

export default ChangePassword;
