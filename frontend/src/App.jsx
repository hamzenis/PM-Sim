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
