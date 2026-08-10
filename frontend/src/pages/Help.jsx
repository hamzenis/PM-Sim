import { Box, Container, Heading, ListItem, OrderedList, SimpleGrid, Text, UnorderedList } from '@chakra-ui/react';
import React from 'react';

const Help = () => (
	<Container maxW="6xl" py={8} flexGrow={1}>
		<Heading mb={2}>Help</Heading>
		<Text color="gray.600" mb={6}>
			PM-Sim teaches project-management decision making by balancing scope, time, quality, and budget.
		</Text>
		<SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
			<HelpSection title="Student workflow">
				<OrderedList spacing={2}>
					<ListItem>Open Scenarios and choose the assignment for your class.</ListItem>
					<ListItem>Start a run or resume your existing run.</ListItem>
					<ListItem>Allocate 100% of team capacity across the four activities.</ListItem>
					<ListItem>Choose hiring, dismissals, overtime, meetings, and training.</ListItem>
					<ListItem>Complete weeks until you are ready to submit the project.</ListItem>
				</OrderedList>
			</HelpSection>
			<HelpSection title="Professor workflow">
				<OrderedList spacing={2}>
					<ListItem>Import, validate, and publish a scenario from the Scenarios page.</ListItem>
					<ListItem>Create a class and add student accounts.</ListItem>
					<ListItem>Assign a published scenario revision to the class.</ListItem>
					<ListItem>Review result details and the administrative audit.</ListItem>
				</OrderedList>
			</HelpSection>
			<HelpSection title="Weekly activities">
				<UnorderedList spacing={2}>
					<ListItem>Development completes new tasks.</ListItem>
					<ListItem>Unit testing discovers defects in completed work.</ListItem>
					<ListItem>Bug fixing addresses known defects.</ListItem>
					<ListItem>Integration testing prepares tested work for acceptance.</ListItem>
				</UnorderedList>
			</HelpSection>
			<HelpSection title="Concurrent sessions">
				<Text>
					A run has a version number. If another browser tab completes the same week first, PM-Sim reloads the
					run and asks you to review the updated state before submitting again.
				</Text>
			</HelpSection>
		</SimpleGrid>
	</Container>
);

const HelpSection = ({ title, children }) => (
	<Box bg="white" borderRadius="xl" p={6}>
		<Heading size="md" mb={4}>
			{title}
		</Heading>
		{children}
	</Box>
);

export default Help;
