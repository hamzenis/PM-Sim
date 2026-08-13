import { Box, Button, Flex, Heading, Stack, Text } from '@chakra-ui/react';
import React from 'react';
import { Link } from 'react-router-dom';
import landingBg from '../images/landing_bg.svg';

const Landing = () => (
	<Flex
		as="main"
		align="center"
		justify="center"
		flexGrow="1"
		px={{ base: 4, md: 8 }}
		py={{ base: 10, md: 16 }}
		backgroundImage={landingBg}
		backgroundPosition="center"
		backgroundSize="cover"
		backgroundRepeat="no-repeat"
	>
		<Box bg="white" borderRadius="2xl" boxShadow="xl" w="full" maxW="720px" p={{ base: 7, md: 12 }}>
			<Stack spacing={6} align="center" textAlign="center">
				<Text color="blue.600" fontWeight="bold" letterSpacing="wide" textTransform="uppercase">
					Project management, made practical
				</Text>
				<Heading as="h1" size={{ base: 'xl', md: '2xl' }}>
					Learn by leading a project
				</Heading>
				<Text color="gray.600" fontSize={{ base: 'md', md: 'lg' }} maxW="560px">
					PM-Sim is an interactive project simulation where your decisions about people, time, and
					priorities shape the outcome.
				</Text>
				<Button as={Link} to="/login" colorScheme="blue" size="lg" w={{ base: 'full', sm: 'auto' }} px={12}>
					Log in to PM-Sim
				</Button>
			</Stack>
		</Box>
	</Flex>
);

export default Landing;
