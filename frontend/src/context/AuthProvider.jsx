import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { ApiError } from '../api/client';
import { getCurrentUser, login as loginRequest, logout as logoutRequest } from '../api/auth';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
	const [currentUser, setCurrentUser] = useState(null);
	const [isAuthenticating, setIsAuthenticating] = useState(true);

	useEffect(() => {
		let active = true;
		getCurrentUser()
			.then((user) => active && setCurrentUser(user))
			.catch((error) => {
				if (!(error instanceof ApiError && error.status === 401)) {
					console.error('Could not restore the session', error);
				}
				if (active) setCurrentUser(null);
			})
			.finally(() => active && setIsAuthenticating(false));
		return () => {
			active = false;
		};
	}, []);

	const login = useCallback(async (username, password) => {
		const user = await loginRequest(username, password);
		setCurrentUser(user);
		return user;
	}, []);

	const logout = useCallback(async () => {
		try {
			await logoutRequest();
		} finally {
			setCurrentUser(null);
		}
	}, []);

	const value = useMemo(
		() => ({ currentUser, isAuthenticating, login, logout, setCurrentUser }),
		[currentUser, isAuthenticating, login, logout]
	);

	return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
