import { Box, Heading, HStack, Text, VisuallyHidden, Wrap, WrapItem } from '@chakra-ui/react';
import React from 'react';

export const CHART = { left: 14, right: 96, top: 8, bottom: 84 };

export const ChartCard = ({ title, description, children }) => (
	<Box bg="surface.bg" borderRadius="2xl" p={{ base: 4, md: 7 }} mb={8}>
		<Heading size="md">{title}</Heading>
		<Text color="text.muted" fontSize="sm" mt={2} mb={5}>{description}</Text>
		{children}
	</Box>
);

export const ChartGrid = ({ ticks, getYPosition, formatTick, xLabel, yLabel, chart = CHART, yLabelX = 3.5 }) => (
	<g aria-hidden="true">
		{ticks.map((tick) => (
			<g key={tick}>
				<line x1={chart.left} y1={getYPosition(tick)} x2={chart.right} y2={getYPosition(tick)} stroke="var(--chakra-colors-chart-grid)" strokeWidth="0.5" />
				<text x={chart.left - 2} y={getYPosition(tick) + 1.5} fontSize="3.3" textAnchor="end" fill="var(--chakra-colors-chart-axis)">{formatTick(tick)}</text>
			</g>
		))}
		<line x1={chart.left} y1={chart.top} x2={chart.left} y2={chart.bottom} stroke="var(--chakra-colors-chart-axis)" strokeWidth="0.6" />
		<line x1={chart.left} y1={chart.bottom} x2={chart.right} y2={chart.bottom} stroke="var(--chakra-colors-chart-axis)" strokeWidth="0.6" />
		<text x={(chart.left + chart.right) / 2} y="99" fontSize="3.5" textAnchor="middle" fill="var(--chakra-colors-chart-axis)">{xLabel}</text>
		<text x={yLabelX} y="46" fontSize="3.5" textAnchor="middle" transform={`rotate(-90 ${yLabelX} 46)`} fill="var(--chakra-colors-chart-axis)">{yLabel}</text>
	</g>
);

export const ChartLegend = ({ items }) => (
	<Wrap spacingX={5} spacingY={2} mt={3} aria-label="Chart legend">
		{items.map(({ key, label, color, dashed, marker = 'circle' }) => (
			<WrapItem key={key}>
				<HStack spacing={2} fontSize="sm">
					<Box as="svg" viewBox="0 0 24 12" width="24px" height="12px" aria-hidden="true">
						<line x1="1" y1="6" x2="23" y2="6" stroke={color} strokeWidth="2" strokeDasharray={dashed ? '4 3' : undefined} />
						{!dashed && (marker === 'square' ? <rect x="9" y="3" width="6" height="6" fill={color} /> : <circle cx="12" cy="6" r="3" fill={color} />)}
					</Box>
					<Text>{label}</Text>
				</HStack>
			</WrapItem>
		))}
	</Wrap>
);

export const ChartDataTable = ({ caption, columns, rows }) => (
	<VisuallyHidden>
		<table>
			<caption>{caption}</caption>
			<thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
			<tbody>{rows.map((row, index) => <tr key={index}>{row.map((value, cellIndex) => <td key={cellIndex}>{value}</td>)}</tr>)}</tbody>
		</table>
	</VisuallyHidden>
);

export const EmptyChart = ({ children = 'No chart data is available yet.' }) => (
	<Box minH={{ base: '180px', md: '240px' }} display="grid" placeItems="center" borderWidth="1px" borderStyle="dashed" borderColor="border.default" borderRadius="lg">
		<Text color="text.muted" fontWeight="semibold" textAlign="center">{children}</Text>
	</Box>
);
