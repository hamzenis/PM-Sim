import { Box, Checkbox, FormControl, FormLabel, Grid, Heading, Input, Progress, SimpleGrid, Stack, Text } from '@chakra-ui/react';
import React from 'react';

const ACTIVITY_LABELS = {
	development: 'Development',
	unit_testing: 'Unit testing',
	bug_fixing: 'Bug fixing',
	integration_testing: 'Integration testing',
};

const percentage = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;
const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
const humanizeCode = (code) => String(code).replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase());

const Detail = ({ label, children }) => (
	<Box>
		<Text as="dt" color="gray.600" fontSize="sm">{label}</Text>
		<Text as="dd" fontWeight="semibold">{children}</Text>
	</Box>
);

export const EmployeeTypeCard = ({ employeeType, hireCount, isDisabled, onHireCountChange }) => (
	<Box borderWidth="1px" borderRadius="md" p={4}>
		<FormControl>
			<FormLabel fontWeight="bold">{employeeType.name}</FormLabel>
			<Input
				aria-label={`Hire ${employeeType.name}`}
				isDisabled={isDisabled}
				type="number"
				min={0}
				step={1}
				value={hireCount}
				onChange={(event) => onHireCountChange(employeeType.code, event.target.value)}
			/>
		</FormControl>
		<SimpleGrid as="dl" columns={{ base: 2, sm: 3 }} spacing={3} mt={4}>
			<Detail label="Cost per day">{currency.format(employeeType.cost_per_day)}</Detail>
			<Detail label="Easy throughput">{employeeType.throughput.easy}</Detail>
			<Detail label="Medium throughput">{employeeType.throughput.medium}</Detail>
			<Detail label="Hard throughput">{employeeType.throughput.hard}</Detail>
			<Detail label="Error rate">{percentage(employeeType.error_rate)}</Detail>
			<Detail label="Management skill">{percentage(employeeType.management_skill)}</Detail>
		</SimpleGrid>
	</Box>
);

const StatusIndicator = ({ label, value }) => {
	const percent = Number(value || 0) * 100;
	return (
		<Box>
			<Text fontSize="sm">{label}: {percent.toFixed(0)}%</Text>
			<Progress
				aria-label={`${label}: ${percent.toFixed(0)}%`}
				value={percent}
				min={0}
				max={100}
				size="sm"
			/>
		</Box>
	);
};

export const TeamRoster = ({ employees, employeeTypes, dismissalIds, isDisabled, onToggleDismissal }) => {
	const namesByCode = Object.fromEntries(employeeTypes.map(({ code, name }) => [code, name]));

	if (employees.length === 0) return <Text>No current employees.</Text>;

	return (
		<SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
			{employees.map((employee) => (
				<Box key={employee.id} borderWidth="1px" borderRadius="md" p={4}>
					<Text fontWeight="bold">{namesByCode[employee.employee_type_code] || humanizeCode(employee.employee_type_code)}</Text>
					<Text color="gray.600" fontSize="sm" mb={3}>{employee.id}</Text>
					<Stack spacing={3} mb={4}>
						<StatusIndicator label="Experience" value={employee.experience} />
						<StatusIndicator label="Motivation" value={employee.motivation} />
						<StatusIndicator label="Stress" value={employee.stress} />
						<StatusIndicator label="Familiarity" value={employee.familiarity} />
					</Stack>
					<Checkbox
						isDisabled={isDisabled}
						isChecked={dismissalIds.includes(employee.id)}
						onChange={() => onToggleDismissal(employee.id)}
					>
						Dismiss {employee.id}
					</Checkbox>
				</Box>
			))}
		</SimpleGrid>
	);
};

const WeeklyDecisionForm = ({ decision, employees, employeeTypes, isDisabled = false, onChange }) => {
	const allocationTotal = Object.values(decision.allocation).reduce((total, value) => total + Number(value), 0);

	const setAllocation = (name, value) => {
		onChange({ ...decision, allocation: { ...decision.allocation, [name]: Number(value) } });
	};

	const setHours = (name, value) => onChange({ ...decision, [name]: Number(value) });

	const setHireCount = (employeeTypeCode, value) => {
		const count = Number(value);
		const otherHires = decision.hires.filter((hire) => hire.employee_type_code !== employeeTypeCode);
		onChange({
			...decision,
			hires: count > 0 ? [...otherHires, { employee_type_code: employeeTypeCode, count }] : otherHires,
		});
	};

	const toggleDismissal = (employeeId) => {
		const isSelected = decision.dismiss_employee_ids.includes(employeeId);
		onChange({
			...decision,
			dismiss_employee_ids: isSelected
				? decision.dismiss_employee_ids.filter((id) => id !== employeeId)
				: [...decision.dismiss_employee_ids, employeeId],
		});
	};

	return (
		<Stack spacing={6}>
			<Box>
				<Heading size="sm" mb={2}>
					Activity allocation
				</Heading>
				<Text color={allocationTotal === 100 ? 'green.600' : 'red.600'} mb={4}>
					Allocated: {allocationTotal}% of team capacity
				</Text>
				<Grid templateColumns={{ base: '1fr', md: 'repeat(4, 1fr)' }} gap={5}>
					{Object.entries(decision.allocation).map(([name, value]) => (
						<FormControl key={name}>
							<FormLabel>{ACTIVITY_LABELS[name]}</FormLabel>
							<Input
								isDisabled={isDisabled}
								type="number"
								min={0}
								max={100}
								value={value}
								onChange={(event) => setAllocation(name, event.target.value)}
							/>
						</FormControl>
					))}
				</Grid>
			</Box>

			<Box>
				<Heading size="sm" mb={4}>
					Team activities per employee
				</Heading>
				<SimpleGrid columns={{ base: 1, md: 3 }} spacing={5}>
					<HoursInput
						isDisabled={isDisabled}
						label="Overtime hours"
						name="overtime_hours_per_employee"
						value={decision.overtime_hours_per_employee}
						onChange={setHours}
					/>
					<HoursInput
						isDisabled={isDisabled}
						label="Meeting hours"
						name="meeting_hours_per_employee"
						value={decision.meeting_hours_per_employee}
						onChange={setHours}
					/>
					<HoursInput
						isDisabled={isDisabled}
						label="Training hours"
						name="training_hours_per_employee"
						value={decision.training_hours_per_employee}
						onChange={setHours}
					/>
				</SimpleGrid>
			</Box>

			<Box>
				<Heading size="sm" mb={4}>
					Hire employees
				</Heading>
				<Text color="gray.600" fontSize="sm" mb={4}>
					Throughput is the number of tasks completed per eight productive hours.
				</Text>
				{employeeTypes.length === 0 ? (
					<Text>No employee types are available.</Text>
				) : (
					<SimpleGrid columns={{ base: 1, lg: 2 }} spacing={5}>
						{employeeTypes.map((employeeType) => {
							const hire = decision.hires.find((item) => item.employee_type_code === employeeType.code);
							return (
								<EmployeeTypeCard
									key={employeeType.code}
									employeeType={employeeType}
									hireCount={hire?.count || 0}
									isDisabled={isDisabled}
									onHireCountChange={setHireCount}
								/>
							);
						})}
					</SimpleGrid>
				)}
			</Box>

			<Box>
				<Heading size="sm" mb={4}>
					Team roster
				</Heading>
				<Text color="gray.600" fontSize="sm" mb={4}>
					These displayed status values affect employee efficiency.
				</Text>
				<TeamRoster
					employees={employees}
					employeeTypes={employeeTypes}
					dismissalIds={decision.dismiss_employee_ids}
					isDisabled={isDisabled}
					onToggleDismissal={toggleDismissal}
				/>
			</Box>
		</Stack>
	);
};

const HoursInput = ({ label, name, value, isDisabled, onChange }) => (
	<FormControl>
		<FormLabel>{label}</FormLabel>
		<Input
			isDisabled={isDisabled}
			type="number"
			min={0}
			value={value}
			onChange={(event) => onChange(name, event.target.value)}
		/>
	</FormControl>
);

export const decisionIsValid = (decision) => {
	const allocationTotal = Object.values(decision.allocation).reduce((total, value) => total + Number(value), 0);
	const hoursAreValid = [
		decision.overtime_hours_per_employee,
		decision.meeting_hours_per_employee,
		decision.training_hours_per_employee,
	].every((value) => Number(value) >= 0);
	return (
		allocationTotal === 100 &&
		hoursAreValid &&
		decision.hires.every((hire) => Number.isInteger(hire.count) && hire.count > 0)
	);
};

export default WeeklyDecisionForm;
