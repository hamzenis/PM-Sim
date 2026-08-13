import { Box, Container, Text } from '@chakra-ui/react';

const Footer = () => (
	<Box as="footer" bg="surface.bg" borderTopWidth="1px" borderColor="border.default" mt="auto">
		<Container maxW="7xl" px={{ base: 4, md: 8 }} py={5}>
			<Text color="text.muted" fontSize="sm">© {new Date().getFullYear()} PM-Sim</Text>
		</Container>
	</Box>
);

export default Footer;
