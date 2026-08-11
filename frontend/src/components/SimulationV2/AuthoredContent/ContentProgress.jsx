import { Text } from '@chakra-ui/react';
import React from 'react';

const ContentProgress = ({ entries = [] }) => {
	const completed = entries.filter((entry) => entry.status === 'completed').length;
	return <Text fontSize="sm" color="gray.600">Content progress: {completed} of {entries.length} complete</Text>;
};

export default ContentProgress;
