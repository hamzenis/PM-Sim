import {
	Alert,
	AlertIcon,
	Box,
	Code,
	Heading,
	ListItem,
	OrderedList,
	SimpleGrid,
	Stack,
	Text,
	UnorderedList,
} from '@chakra-ui/react';
import React from 'react';

const FlowStep = ({ children, tone = 'blue' }) => (
	<Box borderWidth="1px" borderColor={`${tone}.200`} bg={`${tone}.50`} borderRadius="lg" px={3} py={2} textAlign="center" fontWeight="semibold">
		{children}
	</Box>
);

const TaskFlow = () => (
	<Stack direction={{ base: 'column', md: 'row' }} align="center" spacing={2} aria-label="Task lifecycle diagram">
		<FlowStep>Backlog</FlowStep><Text aria-hidden>→</Text>
		<FlowStep>Completed</FlowStep><Text aria-hidden>→</Text>
		<FlowStep>Unit tested</FlowStep><Text aria-hidden>→</Text>
		<FlowStep tone="green">Integration tested</FlowStep>
	</Stack>
);

export const HelpSection = ({ title, children }) => (
	<Box as="section" bg="white" borderRadius="xl" p={{ base: 5, md: 6 }}>
		<Heading size="md" mb={4}>{title}</Heading>
		<Stack spacing={3}>{children}</Stack>
	</Box>
);

/** The v2 simulation guide is shared by the full Help page and in-run Help drawer. */
export const SimulationHelpSections = () => (
	<Stack spacing={6}>
		<HelpSection title="Dashboard at a glance">
			<SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
				<Box><Text fontWeight="bold">Working days remaining</Text><Text>The scenario deadline minus elapsed working days. A final week can be shorter than five days.</Text></Box>
				<Box><Text fontWeight="bold">Cumulative expenses</Text><Text>Initial budget minus remaining budget. Its weekly delta is the latest salary charge.</Text></Box>
				<Box><Text fontWeight="bold">Remaining tasks</Text><Text>All easy, medium, and hard tasks currently in the backlog. This can rise when integration testing returns work.</Text></Box>
				<Box><Text fontWeight="bold">Budget remaining</Text><Text>Initial budget minus staff costs charged so far. A negative red value means the project is over budget.</Text></Box>
			</SimpleGrid>
			<Text color="gray.600">“Since last week” compares the current state with the preceding saved week; green means the movement is favorable.</Text>
		</HelpSection>

		<HelpSection title="Task lifecycle and task-progress metrics">
			<TaskFlow />
			<Text><strong>Development</strong> moves tasks from Backlog to Completed. <strong>Unit testing</strong> moves eligible completed tasks into Unit tested and reveals defects. <strong>Bug fixing</strong> removes known bugs. <strong>Integration testing</strong> accepts clean unit-tested work.</Text>
			<UnorderedList spacing={2} pl={5}>
				<ListItem><strong>Completed</strong>, <strong>Unit tested</strong>, and <strong>Integration tested</strong> are cumulative pools, not mutually exclusive buckets: an integrated task is also completed and unit tested.</ListItem>
				<ListItem><strong>Known bugs</strong> counts visible defects on unit-tested, not-yet-integrated work.</ListItem>
				<ListItem>Work is automatically spread across easy, medium, and hard tasks in proportion to the eligible pool.</ListItem>
			</UnorderedList>
		</HelpSection>

		<HelpSection title="Visible and undiscovered bugs">
			<Alert status="info"><AlertIcon /><Text>The dashboard never exposes hidden defects. A zero Known bugs value means “none discovered,” not necessarily “none exist.”</Text></Alert>
			<Text>Development can create undiscovered bugs. Unit testing samples eligible completed work, moves any defects it finds into Known bugs, and makes those bugs available for fixing. Bug-fixing capacity can only act on known bugs.</Text>
			<Text>Example: development completes 6 tasks and 2 secretly contain bugs. Before unit testing, Known bugs is 0. If testing samples one defective task, Known bugs becomes 1; the other defect remains invisible.</Text>
		</HelpSection>

		<HelpSection title="Integration-test returns">
			<Stack direction={{ base: 'column', md: 'row' }} align="center" spacing={2} aria-label="Integration return diagram">
				<FlowStep>Clean unit-tested work</FlowStep><Text aria-hidden>→</Text><FlowStep>Integration test</FlowStep><Text aria-hidden>→</Text><FlowStep tone="green">Accepted</FlowStep>
				<Text aria-hidden>or</Text><FlowStep tone="orange">Returned to backlog</FlowStep>
			</Stack>
			<Text>Integration testing only selects unit-tested work without known bugs. A task with an incorrect specification is returned to the backlog: it is removed from Completed and Unit tested and must repeat the lifecycle. A passing task joins Integration tested.</Text>
			<Text>Example: test 4 eligible tasks; if 1 has a specification failure, 3 become integration tested and 1 returns to Remaining tasks. This is why backlog and progress lines can move in unexpected directions in the same week.</Text>
		</HelpSection>

		<HelpSection title="Employee status and throughput">
			<UnorderedList spacing={2} pl={5}>
				<ListItem><strong>Motivation, stress, and familiarity</strong> are shown as current team averages; the population is recalculated after hires and dismissals.</ListItem>
				<ListItem><strong>Experience</strong> is displayed on each roster card and multiplies that employee’s output. It is not plotted in the team-average chart.</ListItem>
				<ListItem>Overtime adds capacity but raises stress and lowers motivation. A week without overtime reduces stress; a solo employee receives an additional stress increase.</ListItem>
				<ListItem>Meetings consume capacity and increase familiarity. Training consumes capacity; employees below the team’s effective-throughput average can gain experience and motivation.</ListItem>
			</UnorderedList>
			<Text>An employee type’s throughput is tasks per eight productive hours for each difficulty. Actual expected output also reflects the task mix, personal efficiency (familiarity, motivation, and closeness to the ideal stress level), experience, and team communication overhead. Depending on scenario randomness, the final whole-task result is rounded or sampled and cannot exceed eligible work.</Text>
		</HelpSection>

		<HelpSection title="Budget burn">
			<Text><Code>cumulative cost = initial budget − remaining budget</Code></Text>
			<Text>Each completed week charges every employee then on the team their employee type’s daily cost times that week’s working days. Overtime, meetings, and training change capacity or status but do not add a separate charge.</Text>
			<Text>The gray planned line burns the initial budget evenly across scheduled working days. <strong>Variance from plan</strong> is actual cumulative cost minus planned cumulative cost, so a positive number is unfavorable. <strong>Spend during latest week</strong> is the change between the two latest snapshots.</Text>
		</HelpSection>

		<HelpSection title="Weekly decisions and processing order">
			<OrderedList spacing={2} pl={5}>
				<ListItem>Choose hires and dismissals; they take effect before capacity and this week’s salary are calculated.</ListItem>
				<ListItem>Allocate exactly 100% among development, unit testing, bug fixing, and integration testing.</ListItem>
				<ListItem>Add non-negative overtime, meeting, and training hours per employee. Meetings and training reserve hours before percentages are applied to the remaining capacity.</ListItem>
				<ListItem>Complete the week. The engine processes unit testing, bug fixing, development, then integration testing; updates employee status; charges staff cost; and advances time.</ListItem>
			</OrderedList>
			<Text>Because testing and fixing happen before development, work developed this week cannot be unit tested until a later week. Integration runs after development, but still requires work that was already unit tested and clean.</Text>
		</HelpSection>

		<HelpSection title="Submission, outcomes, and accepted work">
			<Text>Submission readiness is <Code>integration-tested tasks ÷ total project tasks</Code>. The 80% marker is guidance only: you may submit below it, but submission is final and only integration-tested tasks are accepted.</Text>
			<UnorderedList spacing={2} pl={5}>
				<ListItem><strong>Completed:</strong> every project task has passed integration testing.</ListItem>
				<ListItem><strong>Submitted:</strong> you ended an active run with Submit project.</ListItem>
				<ListItem><strong>Deadline reached:</strong> no working days remain before every task is accepted.</ListItem>
			</UnorderedList>
			<Text>Rejected tasks are all project tasks not integration tested at the end—including backlog work, incomplete testing, known or hidden defects, and returned specification failures.</Text>
		</HelpSection>

		<HelpSection title="How scoring works">
			<Text>Every scenario supplies quality, time, and budget point limits and exponents. Quality is based on the accepted-task ratio. Time and budget receive their full component points while at or below their scheduled-days or initial-budget targets; exceeding a target reduces that component according to its scenario exponent, down to zero.</Text>
			<Text><Code>total score = round((quality + time + budget points) ÷ available component points × 100)</Code></Text>
			<Text>Example with equal 100-point limits and exponent 1: accepting 80% gives 80 quality points. Finishing within schedule gives 100 time points. Spending 10% over budget leaves 90 budget points. The total is <Code>round(270 ÷ 300 × 100) = 90</Code>. Scenario limits or exponents can make your result differ.</Text>
		</HelpSection>
	</Stack>
);

const HelpContent = ({ showIntroduction = true }) => (
	<>
		{showIntroduction && (
			<Box mb={6}>
				<Heading mb={2}>Simulation v2 help</Heading>
				<Text color="gray.600">Use this guide to interpret the live dashboard and make weekly project decisions.</Text>
			</Box>
		)}
		<SimulationHelpSections />
	</>
);

export default HelpContent;
