import { Badge, Box, Checkbox, FormControl, FormLabel, Grid, Heading, Input, Progress, SimpleGrid, Stack, Text } from '@chakra-ui/react';
import React from 'react';

const ACTIVITY_LABELS = {
	development: 'Development',
	unit_testing: 'Unit testing',
	bug_fixing: 'Bug fixing',
	integration_testing: 'Integration testing',
};

const percentage = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;
const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });

export const deriveEmployeeDisplayModels = (employees, employeeTypes) => {
	const namesByCode = Object.fromEntries(employeeTypes.map(({ code, name }) => [code, name]));
	return employees.map((employee, index) => ({
		employee,
		label: `Employee ${index + 1}`,
		typeLabel: namesByCode[employee.employee_type_code] || employee.employee_type_code,
	}));
};

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
	const displayEmployees = deriveEmployeeDisplayModels(employees, employeeTypes);

	if (employees.length === 0) return <Text>No current employees.</Text>;

	return (
		<SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
			{displayEmployees.map(({ employee, label, typeLabel }) => {
				const isSelected = dismissalIds.includes(employee.id);
				return (
				<Box key={employee.id} borderWidth="1px" borderRadius="lg" p={5} bg={isSelected ? 'orange.50' : 'white'}>
					<Heading as="h4" size="sm">{label}</Heading>
					<Text color="gray.600" fontSize="sm" mb={4}>Employee type: {typeLabel}</Text>
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
						{isSelected ? 'Keep employee' : 'Select for dismissal'}
					</Checkbox>
				</Box>
				);
			})}
		</SimpleGrid>
	);
};

const WeeklyDecisionForm = ({ decision, employees, employeeTypes, isDisabled = false, onChange }) => {
	const allocationTotal = Object.values(decision.allocation).reduce((total, value) => total + Number(value), 0);
	const employeeDisplays = deriveEmployeeDisplayModels(employees, employeeTypes);
	const selectedEmployeeLabels = employeeDisplays
		.filter(({ employee }) => decision.dismiss_employee_ids.includes(employee.id))
		.map(({ label }) => label);
	const typeNamesByCode = Object.fromEntries(employeeTypes.map(({ code, name }) => [code, name]));

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
		<Stack spacing={8}>
			<Box as="section">
				<Heading size="md" mb={5}>Work plan</Heading>
				<Heading size="sm" mb={2}>
					Activity allocation
				</Heading>
				<Text color={allocationTotal === 100 ? 'green.600' : 'red.600'} mb={4}>
					Allocated: {allocationTotal}% of team capacity
				</Text>
				<Grid templateColumns={{ base: '1fr', md: 'repeat(4, 1fr)' }} gap={5}>
					{Object.entries(decision.allocation).map(([name, value]) => (
						<FormControl key={name}>
							<FormLabel>{ACTIVITY_LABELS[name]} (%)</FormLabel>
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

			<Box as="section">
				<Heading size="sm" mb={4}>
					Team activities per employee
				</Heading>
				<SimpleGrid columns={{ base: 1, md: 3 }} spacing={5}>
					<HoursInput
						isDisabled={isDisabled}
						label="Overtime"
						name="overtime_hours_per_employee"
						value={decision.overtime_hours_per_employee}
						onChange={setHours}
					/>
					<HoursInput
						isDisabled={isDisabled}
						label="Meetings"
						name="meeting_hours_per_employee"
						value={decision.meeting_hours_per_employee}
						onChange={setHours}
					/>
					<HoursInput
						isDisabled={isDisabled}
						label="Training"
						name="training_hours_per_employee"
						value={decision.training_hours_per_employee}
						onChange={setHours}
					/>
				</SimpleGrid>
			</Box>

			<Box as="section" borderTopWidth="1px" pt={7}>
				<Heading size="md" mb={2}>
					Hiring
				</Heading>
				<Text color="gray.600" fontSize="sm" mb={4}>
					Choose how many employees to add. Costs are shown in US dollars per employee per day. Throughput is the number of tasks completed per eight productive hours.
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

			<Box as="section" borderTopWidth="1px" pt={7}>
				<Heading size="md" mb={2}>
					Team decisions
				</Heading>
				<Text color="gray.600" fontSize="sm" mb={4}>
					Review each employee’s status. Dismissal selections only apply when you submit the week.
				</Text>
				<TeamRoster
					employees={employees}
					employeeTypes={employeeTypes}
					dismissalIds={decision.dismiss_employee_ids}
					isDisabled={isDisabled}
					onToggleDismissal={toggleDismissal}
				/>
			</Box>

			<Box as="section" borderWidth="1px" borderRadius="lg" p={5} bg="gray.50">
				<Heading size="md" mb={4}>Decision summary</Heading>
				<SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
					<Box>
						<Text fontWeight="semibold">Work allocation</Text>
						<Text>{allocationTotal}% allocated</Text>
					</Box>
					<Box>
						<Text fontWeight="semibold">Hours per employee</Text>
						<Text>Overtime: {decision.overtime_hours_per_employee} hours · Meetings: {decision.meeting_hours_per_employee} hours · Training: {decision.training_hours_per_employee} hours</Text>
					</Box>
					<Box>
						<Text fontWeight="semibold">Hiring</Text>
						<Text>{decision.hires.length === 0 ? 'No new hires' : decision.hires.map((hire) => `${hire.count} ${typeNamesByCode[hire.employee_type_code] || hire.employee_type_code}`).join(', ')}</Text>
					</Box>
					<Box>
						<Text fontWeight="semibold">Dismissals</Text>
						<Text>{selectedEmployeeLabels.length === 0 ? 'No employees selected' : selectedEmployeeLabels.join(', ')}</Text>
					</Box>
				</SimpleGrid>
				<Badge mt={4} colorScheme={allocationTotal === 100 ? 'green' : 'red'}>{allocationTotal === 100 ? 'Ready to submit' : 'Needs attention'}</Badge>
			</Box>
		</Stack>
	);
};

const HoursInput = ({ label, name, value, isDisabled, onChange }) => (
	<FormControl>
		<FormLabel>{label} (hours)</FormLabel>
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
