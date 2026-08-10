import React, { useContext } from 'react';
import { AuthContext } from './context/AuthProvider';
import { Navigate, Route, Routes } from 'react-router-dom';
import Landing from './pages/Landing';
import ScenarioOverview from './pages/ScenarioOverview';
import UserOverview from './pages/UserOverview';
import Simulation from './pages/Simulation';
import Login from './pages/Login';
import ResetPassword from './pages/ResetPassword';
import Help from './pages/Help';
import GDPR from './pages/GDPR';
import Imprint from './pages/Imprint';
import NotFoundPage from './components/NotFoundPage';
import ScenarioStudio from './pages/ScenarioStudio';
import AddMultipleUsers from './pages/AddMultipleUsers';
import SkillTypesOverview from './pages/SkillTypesOverview';
import ScenarioConfigOverview from './pages/ScenarioConfigOverview';
import CourseOverview from './pages/CourseOverview';
import ScenarioManagement from './pages/ScenarioManagement';

const Routing = () => {
	const { currentUser, isAuthenticating } = useContext(AuthContext);

	return (
		<Routes>
			<>
				{/* routes which are accessible for every user */}
				<Route path="/gdpr" element={<GDPR />} />
				<Route path="/imprint" element={<Imprint />} />
			</>

			{currentUser ? (
				<>
					{/* routes which are accessible for every logged-in user */}
					<Route path="/" element={<Navigate to="/scenarios" replace />} />
					<Route path="/scenarios" element={<ScenarioOverview />} />
					<Route path="/scenarios/:scn_id" element={<Simulation />} />
					<Route path="/help" element={<Help />} />
					<Route path="/login" element={<Navigate to="/" replace />} />
					<Route path="*" element={<NotFoundPage />} />
				</>
			) : (
				<>
					{/* routes which are accessible for only not logged-in users */}
					{!isAuthenticating && (
						<>
							<Route path="/" element={<Landing />} />
							<Route path="/login" element={<Login />} />
							<Route path="/reset-password" element={<ResetPassword />} />
							<Route path="*" element={<Navigate to="/login" replace />} />
						</>
					)}
				</>
			)}
			{currentUser?.role === 'professor' && (
				<>
					{/* adding routes which are accessible for every logged-in user with role creator */}
					<Route path="/scenario-studio" element={<ScenarioStudio />} />
					<Route path="/skill-types" element={<SkillTypesOverview />} />
					<Route path="/scenario-config" element={<ScenarioConfigOverview />} />
					<Route path="/scenariomanagement" element={<ScenarioManagement />} />
				</>
			)}
			{currentUser?.role === 'professor' && (
				<>
					{/* adding routes which are accessible for every logged-in user with role staff */}
					<Route path="/users" element={<UserOverview />} />
					<Route path="/addusers" element={<AddMultipleUsers />} />
					<Route path="/courses" element={<CourseOverview />} />
				</>
			)}
		</Routes>
	);
};

export default Routing;
