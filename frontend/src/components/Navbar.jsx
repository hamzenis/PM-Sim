import {
	Box,
	Button,
	Flex,
	HStack,
	Image,
	Menu,
	Text,
	MenuButton,
	MenuGroup,
	MenuItem,
	MenuList,
} from '@chakra-ui/react';
import Logo from '../images/logo-simplify.png';
import { HiKey, HiMenu, HiOutlineLogout, HiUserCircle } from 'react-icons/hi';
import { useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../context/AuthProvider';

const Navbar = () => {
	const { currentUser, logout } = useContext(AuthContext);

	const handleClick = () => {
		if (window.value >= 20) {
			const confirmLeave = window.confirm('Are you sure you want to leave this page?');
			if (!confirmLeave) {
				return; // Abbruch, wenn der Benutzer "Abbrechen" geklickt hat
			}
		}
	};

	async function handleLogout() {
		try {
			await logout();
		} catch (err) {
			console.error('Logout failed', err);
		}
	}

	return (
		<Flex w="full" px={16} py={4} borderBottom="1px solid #E2E8F0">
			<Box as={Link} to={'/'} onClick={handleClick}>
				<Image src={Logo} alt="logo" w={14} objectFit="contain" />
			</Box>

			{currentUser && (
				<HStack ml={4} spacing={2} alignItems="center">
					<HiUserCircle size={20} />
					<Text fontWeight="bold">{currentUser.username}</Text>
				</HStack>
			)}

			<HStack w="100%" justifyContent="center" gap={14}>
				<Button variant="link" as={Link} to="/scenarios" onClick={handleClick}>
					Scenarios
				</Button>

				<Button variant="link" as={Link} to="/help" onClick={handleClick}>
					Help
				</Button>

				{currentUser?.role === 'professor' && (
					<>
						<Button variant="link" as={Link} to="/classes" onClick={handleClick}>
							Classes
						</Button>
						<Button variant="link" as={Link} to="/audit" onClick={handleClick}>
							Audit
						</Button>
					</>
				)}
			</HStack>

			<HStack justifyContent="flex-end">
				<HStack borderRadius="full" backgroundColor="white" p={3} boxShadow="xl">
					<Menu>
						<MenuButton
							size="sm"
							cursor="pointer"
							display="flex"
							alignItems="center"
							justifyContent="center"
							aria-label="Account menu"
						>
							<Box as="span" display="flex" alignItems="center" justifyContent="center" w="full">
								<HiMenu />
							</Box>
						</MenuButton>
						<MenuList mt={2}>
							<MenuGroup>
								<MenuItem as={Link} to="/change-password" icon={<HiKey />}>
									Change password
								</MenuItem>
								<MenuItem icon={<HiOutlineLogout />} color="red" onClick={handleLogout}>
									Logout
								</MenuItem>
							</MenuGroup>
						</MenuList>
					</Menu>
				</HStack>
			</HStack>
		</Flex>
	);
};

export default Navbar;
