import { Alert, AlertIcon, Box, Heading, Spinner, Text } from '@chakra-ui/react';
import React from 'react';
import { HiOutlineInbox } from 'react-icons/hi';

export const PageLoadingState = ({ label }) => (
	<Box py={12} textAlign="center" role="status" aria-live="polite">
		<Spinner size="xl" color="blue.500" mb={4} />
		<Text color="gray.600" fontWeight="medium">
			{label}
		</Text>
	</Box>
);

export const EmptyState = ({ title, description, action }) => (
	<Box py={10} px={5} textAlign="center" borderWidth="1px" borderStyle="dashed" borderRadius="xl" bg="gray.50">
		<Box as={HiOutlineInbox} aria-hidden="true" mx="auto" mb={3} boxSize={8} color="gray.400" />
		<Heading as="h2" size="md" mb={2}>
			{title}
		</Heading>
		<Text color="gray.600" maxW="xl" mx="auto">
			{description}
		</Text>
		{action && <Box mt={4}>{action}</Box>}
	</Box>
);

export const RequestError = ({ message, title = 'Something went wrong', ...props }) => (
	<Alert status="error" role="alert" alignItems="flex-start" {...props}>
		<AlertIcon mt={1} />
		<Box>
			<Text fontWeight="bold">{title}</Text>
			<Text>{message}</Text>
		</Box>
	</Alert>
);
