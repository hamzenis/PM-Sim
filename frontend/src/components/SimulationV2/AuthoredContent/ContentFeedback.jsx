import { Alert, AlertIcon } from '@chakra-ui/react';
import React from 'react';

const ContentFeedback = ({ feedback }) =>
	feedback ? (
		<Alert status="info" mt={4} aria-label="Feedback">
			<AlertIcon />
			{feedback}
		</Alert>
	) : null;

export default ContentFeedback;
