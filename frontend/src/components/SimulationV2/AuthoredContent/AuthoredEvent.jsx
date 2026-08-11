import { Heading, Text } from '@chakra-ui/react';
import React from 'react';
import ContentFeedback from './ContentFeedback';

const AuthoredEvent = ({ entry }) => (
	<>
		{entry.title && <Heading size="sm" mb={2}>{entry.title}</Heading>}
		{entry.body && <Text whiteSpace="pre-wrap">{entry.body}</Text>}
		<ContentFeedback feedback={entry.feedback} />
	</>
);

export default AuthoredEvent;
