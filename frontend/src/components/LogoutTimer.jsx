import { useContext, useEffect } from 'react';
import { AuthContext } from '../context/AuthProvider';

const INACTIVITY_TIMEOUT_MS = 60 * 60 * 1000;
const ACTIVITY_EVENTS = ['mousemove', 'keydown', 'click', 'scroll'];

const LogoutTimer = () => {
	const { currentUser, logout } = useContext(AuthContext);

	useEffect(() => {
		if (!currentUser) return undefined;

		let timeoutId;
		const expireSession = async () => {
			try {
				await logout();
			} catch (error) {
				console.error('Automatic logout failed', error);
			}
			window.alert('You have been logged off due to inactivity.');
		};
		const resetTimer = () => {
			window.clearTimeout(timeoutId);
			timeoutId = window.setTimeout(expireSession, INACTIVITY_TIMEOUT_MS);
		};

		resetTimer();
		ACTIVITY_EVENTS.forEach((eventName) => document.addEventListener(eventName, resetTimer));
		return () => {
			window.clearTimeout(timeoutId);
			ACTIVITY_EVENTS.forEach((eventName) => document.removeEventListener(eventName, resetTimer));
		};
	}, [currentUser, logout]);

	return null;
};

export default LogoutTimer;
