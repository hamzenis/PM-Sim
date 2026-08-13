import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Navbar from './components/Navbar';
import { Box, Flex } from '@chakra-ui/react';
import Footer from './components/Footer';
import Routing from './Routing';
import { AuthProvider } from './context/AuthProvider';
import ScrollToTop from './components/ScrollToTop';
import LogoutTimer from './components/LogoutTimer';

function App() {
	return (
		<Flex minH="100vh" flexDir="column">
			<Box
				as="a"
				href="#main-content"
				position="fixed"
				top="2"
				left="2"
				zIndex="skipLink"
				px="4"
				py="3"
				bg="white"
				transform="translateY(-150%)"
				_focus={{ transform: 'translateY(0)' }}
			>
				Skip to main content
			</Box>
			<BrowserRouter>
				<AuthProvider>
					<ScrollToTop>
						<Navbar />
						<Box as="main" id="main-content" flex="1" display="flex" flexDirection="column">
							<Routing />
						</Box>
						<Footer />
						<LogoutTimer />
					</ScrollToTop>
				</AuthProvider>
			</BrowserRouter>
		</Flex>
	);
}

export default App;
