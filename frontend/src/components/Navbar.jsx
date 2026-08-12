import {
	Avatar,
	Box,
	Button,
	Container,
	Divider,
	Drawer,
	DrawerBody,
	DrawerCloseButton,
	DrawerContent,
	DrawerHeader,
	DrawerOverlay,
	Flex,
	HStack,
	IconButton,
	Image,
	Menu,
	MenuButton,
	MenuItem,
	MenuList,
	Stack,
	Text,
	useDisclosure,
} from '@chakra-ui/react';
import { HiKey, HiMenu, HiOutlineLogout, HiOutlineUser } from 'react-icons/hi';
import { useContext, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import Logo from '../images/logo-simplify.png';
import { AuthContext } from '../context/AuthProvider';

const linksFor = (user) => [
	{ label: 'Scenarios', to: '/scenarios' },
	{ label: 'Help', to: '/help' },
	...(user?.role === 'professor'
		? [
				{ label: 'Classes', to: '/classes' },
				{ label: 'Audit', to: '/audit' },
			]
		: []),
];

const Navbar = () => {
	const { currentUser, logout } = useContext(AuthContext);
	const location = useLocation();
	const mobileMenu = useDisclosure();
	const menuButtonRef = useRef();
	const links = linksFor(currentUser);
	const isActive = (to) => location.pathname === to || location.pathname.startsWith(`${to}/`);

	async function handleLogout() {
		try {
			await logout();
		} catch (err) {
			console.error('Logout failed', err);
		}
	}

	const NavLinks = ({ mobile = false }) => (
		<Stack direction={mobile ? 'column' : 'row'} spacing={mobile ? 2 : 1} align={mobile ? 'stretch' : 'center'}>
			{links.map(({ label, to }) => (
				<Button
					key={to}
					as={Link}
					to={to}
					onClick={mobile ? mobileMenu.onClose : undefined}
					variant={isActive(to) ? 'solid' : 'ghost'}
					colorScheme="brand"
					aria-current={isActive(to) ? 'page' : undefined}
					justifyContent={mobile ? 'flex-start' : 'center'}
				>
					{label}
				</Button>
			))}
		</Stack>
	);

	return (
		<Box as="header" bg="surface.bg" borderBottomWidth="1px" borderColor="border.default" boxShadow="header">
			<Container maxW="7xl" px={{ base: 3, sm: 5, lg: 8 }}>
				<Flex minH={{ base: 16, md: 20 }} align="center" gap={{ base: 2, md: 5 }}>
					<Flex as={Link} to={currentUser ? '/scenarios' : '/'} align="center" gap={2} flexShrink={0} aria-label="PM-Sim home">
						<Image src={Logo} alt="" w={{ base: 9, md: 11 }} objectFit="contain" />
						<Text fontSize={{ base: 'lg', md: 'xl' }} fontWeight="bold" color="brand.700" whiteSpace="nowrap">
							PM-Sim
						</Text>
					</Flex>

					{currentUser && (
						<>
							<Box as="nav" aria-label="Primary navigation" display={{ base: 'none', md: 'block' }} ml="auto">
								<NavLinks />
							</Box>
							<HStack ml={{ base: 'auto', md: 2 }} spacing={2}>
								<Menu placement="bottom-end">
									<MenuButton
										as={Button}
										variant="ghost"
										px={{ base: 2, lg: 3 }}
										aria-label={`Account menu for ${currentUser.username}`}
									>
										<HStack>
											<Avatar size="xs" name={currentUser.username} icon={<HiOutlineUser />} />
											<Text display={{ base: 'none', lg: 'block' }} maxW="10rem" noOfLines={1}>
												{currentUser.username}
											</Text>
										</HStack>
									</MenuButton>
									<MenuList>
										<Box px={3} py={2}>
											<Text fontWeight="semibold">{currentUser.username}</Text>
											<Text fontSize="sm" color="text.muted" textTransform="capitalize">{currentUser.role}</Text>
										</Box>
										<Divider />
										<MenuItem as={Link} to="/change-password" icon={<HiKey />}>Change password</MenuItem>
										<MenuItem icon={<HiOutlineLogout />} color="red.600" onClick={handleLogout}>Logout</MenuItem>
									</MenuList>
								</Menu>
								<IconButton
									ref={menuButtonRef}
									display={{ base: 'inline-flex', md: 'none' }}
									icon={<HiMenu />}
									aria-label="Open navigation menu"
									variant="outline"
									onClick={mobileMenu.onOpen}
								/>
							</HStack>
						</>
					)}
				</Flex>
			</Container>

			<Drawer isOpen={mobileMenu.isOpen} placement="right" onClose={mobileMenu.onClose} finalFocusRef={menuButtonRef}>
				<DrawerOverlay />
				<DrawerContent maxW="18rem">
					<DrawerCloseButton />
					<DrawerHeader>Navigation</DrawerHeader>
					<DrawerBody>
						<Box as="nav" aria-label="Mobile navigation"><NavLinks mobile /></Box>
					</DrawerBody>
				</DrawerContent>
			</Drawer>
		</Box>
	);
};

export default Navbar;
