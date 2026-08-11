import { Container } from '@chakra-ui/react';
import React from 'react';
import HelpContent from '../components/HelpContent';

const Help = () => (
	<Container maxW="6xl" py={8} flexGrow={1}>
		<HelpContent />
	</Container>
);

export default Help;
