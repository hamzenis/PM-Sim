import {
	Alert,
	AlertIcon,
	Box,
	Button,
	Checkbox,
	FormControl,
	FormLabel,
	Heading,
	IconButton,
	Input,
	InputGroup,
	InputRightElement,
	Stack,
	Text,
} from '@chakra-ui/react';
import { HiOutlineEye, HiOutlineEyeOff, HiOutlineLogin } from 'react-icons/hi';
import React, { useContext, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiError } from '../api/client';
import { AuthContext } from '../context/AuthProvider';
import landingBg from '../images/landing_bg.svg';

const Login = () => {
	const { login } = useContext(AuthContext);
	const [username, setUsername] = useState('');
	const [password, setPassword] = useState('');
	const [privacyPolicyAccepted, setPrivacyPolicyAccepted] = useState(false);
	const [showPassword, setShowPassword] = useState(false);
	const [error, setError] = useState('');
	const [isSubmitting, setIsSubmitting] = useState(false);
	const submissionInProgress = useRef(false);
	const errorRef = useRef(null);
	const isValid = username.trim() !== '' && password !== '' && privacyPolicyAccepted;

	useEffect(() => {
		if (error) errorRef.current?.focus();
	}, [error]);

	const handleSubmit = async (event) => {
		event.preventDefault();
		if (!isValid || submissionInProgress.current) return;
		submissionInProgress.current = true;
		setIsSubmitting(true);
		setError('');
		try {
			await login(username, password);
		} catch (requestError) {
			if (requestError instanceof ApiError && requestError.status === 401) {
				setError('The username or password is incorrect.');
			} else {
				console.error('Login failed', requestError);
				setError('We could not reach Simplify. Check your connection and try again.');
			}
		} finally {
			submissionInProgress.current = false;
			setIsSubmitting(false);
		}
	};

	return (
		<Box
			as="main"
			display="flex"
			alignItems="center"
			justifyContent="center"
			flexGrow="1"
			px={4}
			py={{ base: 8, md: 12 }}
			backgroundImage={landingBg}
			backgroundPosition="center"
			backgroundSize="cover"
		>
			<Box as="form" onSubmit={handleSubmit} bg="white" borderRadius="2xl" boxShadow="xl" w="full" maxW="440px" p={{ base: 6, md: 10 }} noValidate>
				<Stack spacing={5}>
					<Box textAlign="center">
						<Heading as="h1" size="xl">Welcome back</Heading>
						<Text color="gray.600" mt={2}>Log in to continue your simulation.</Text>
					</Box>
					{error && (
						<Alert ref={errorRef} status="error" role="alert" tabIndex={-1} borderRadius="md">
							<AlertIcon />{error}
						</Alert>
					)}
					<FormControl isRequired>
						<FormLabel htmlFor="username">Username</FormLabel>
						<Input id="username" name="username" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" size="lg" bg="gray.50" />
					</FormControl>
					<FormControl isRequired>
						<FormLabel htmlFor="password">Password</FormLabel>
						<InputGroup size="lg">
							<Input id="password" name="password" type={showPassword ? 'text' : 'password'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" bg="gray.50" pr="3rem" />
							<InputRightElement>
								<IconButton type="button" variant="ghost" aria-label={showPassword ? 'Hide password' : 'Show password'} icon={showPassword ? <HiOutlineEyeOff /> : <HiOutlineEye />} onClick={() => setShowPassword((visible) => !visible)} />
							</InputRightElement>
						</InputGroup>
					</FormControl>
					<Checkbox isChecked={privacyPolicyAccepted} onChange={(event) => setPrivacyPolicyAccepted(event.target.checked)}>
						I accept the <Link to="/gdpr"><Text as="span" color="blue.600" textDecoration="underline">Privacy Policy</Text></Link>
					</Checkbox>
					<Button type="submit" rightIcon={<HiOutlineLogin />} isLoading={isSubmitting} loadingText="Logging in" colorScheme="blue" size="lg" isDisabled={!isValid || isSubmitting}>
						Log in
					</Button>
				</Stack>
			</Box>
		</Box>
	);
};

export default Login;
