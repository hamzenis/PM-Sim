import { Box, Checkbox, FormControl, FormLabel, Grid, Heading, Input, SimpleGrid, Stack, Text } from '@chakra-ui/react';
import React from 'react';

const ACTIVITY_LABELS = {
	development: 'Development',
	unit_testing: 'Unit testing',
	bug_fixing: 'Bug fixing',
	integration_testing: 'Integration testing',
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
				{employeeTypes.length === 0 ? (
					<Text>No employee types are available.</Text>
				) : (
					<SimpleGrid columns={{ base: 1, md: 3 }} spacing={5}>
						{employeeTypes.map((employeeType) => {
							const hire = decision.hires.find((item) => item.employee_type_code === employeeType.code);
							return (
								<FormControl key={employeeType.code}>
									<FormLabel>{employeeType.name}</FormLabel>
									<Input
										aria-label={`Hire ${employeeType.name}`}
										isDisabled={isDisabled}
										type="number"
										min={0}
										step={1}
										value={hire?.count || 0}
										onChange={(event) => setHireCount(employeeType.code, event.target.value)}
									/>
									<Text fontSize="sm" color="gray.600">
										{employeeType.cost_per_day} per day
									</Text>
								</FormControl>
							);
						})}
					</SimpleGrid>
				)}
			</Box>

			<Box>
				<Heading size="sm" mb={4}>
					Dismiss employees
				</Heading>
				{employees.length === 0 ? (
					<Text>No current employees.</Text>
				) : (
					<Stack>
						{employees.map((employee) => (
							<Checkbox
								key={employee.id}
								isDisabled={isDisabled}
								isChecked={decision.dismiss_employee_ids.includes(employee.id)}
								onChange={() => toggleDismissal(employee.id)}
							>
								{employee.id} ({employee.employee_type_code})
							</Checkbox>
						))}
					</Stack>
				)}
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
