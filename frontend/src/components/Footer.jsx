import { Box, Button, Container, Flex, Text } from '@chakra-ui/react';
import { Link } from 'react-router-dom';

const Footer = () => (
	<Box as="footer" bg="surface.bg" borderTopWidth="1px" borderColor="border.default" mt="auto">
		<Container maxW="7xl" px={{ base: 4, md: 8 }} py={5}>
			<Flex direction={{ base: 'column', sm: 'row' }} align={{ base: 'flex-start', sm: 'center' }} justify="space-between" gap={3}>
				<Text color="text.muted" fontSize="sm">© {new Date().getFullYear()} PM-Sim</Text>
				<Flex wrap="wrap" columnGap={4} rowGap={2}>
					<Button variant="link" as={Link} to="/imprint" size="sm">Imprint</Button>
					<Button variant="link" as={Link} to="/gdpr" size="sm">Privacy policy</Button>
				</Flex>
			</Flex>
		</Container>
	</Box>
);

export default Footer;
