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
import React, { useContext, useState } from 'react';
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

	const submit = async () => {
		if (newPassword !== confirmation) {
			setError('The new passwords do not match.');
			return;
		}
		setIsSaving(true);
		setError('');
		try {
			await changePassword(currentPassword, newPassword);
			setCurrentUser(null);
			navigate('/login');
		} catch (requestError) {
			setError(requestError.message || 'Could not change the password.');
		} finally {
			setIsSaving(false);
		}
	};

	return (
		<Container maxW="lg" py={12} flexGrow={1}>
			<Box bg="white" borderRadius="xl" p={8}>
				<Heading size="lg" mb={2}>
					Change password
				</Heading>
				<Text color="gray.600" mb={6}>
					You will need to sign in again after changing your password.
				</Text>
				{error && (
					<Alert status="error" mb={4}>
						<AlertIcon />
						{error}
					</Alert>
				)}
				<Stack spacing={4}>
					<FormControl>
						<FormLabel>Current password</FormLabel>
						<Input
							type="password"
							value={currentPassword}
							onChange={(event) => setCurrentPassword(event.target.value)}
						/>
					</FormControl>
					<FormControl>
						<FormLabel>New password</FormLabel>
						<Input
							type="password"
							value={newPassword}
							onChange={(event) => setNewPassword(event.target.value)}
						/>
					</FormControl>
					<FormControl>
						<FormLabel>Repeat new password</FormLabel>
						<Input
							type="password"
							value={confirmation}
							onChange={(event) => setConfirmation(event.target.value)}
						/>
					</FormControl>
					<Button
						colorScheme="blue"
						isLoading={isSaving}
						isDisabled={!currentPassword || newPassword.length < 10 || !confirmation}
						onClick={submit}
					>
						Change password
					</Button>
				</Stack>
			</Box>
		</Container>
	);
};

export default ChangePassword;
