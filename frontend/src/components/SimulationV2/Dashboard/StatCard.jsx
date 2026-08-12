import { Box, Stat, StatHelpText, StatLabel, StatNumber } from '@chakra-ui/react';
import React from 'react';

const StatCard = ({ label, value, helper, delta, deltaIsFavorable, isUnfavorable = false }) => (
	<Box bg="white" borderRadius="xl" p={5}>
		<Stat>
			<StatLabel>{label}</StatLabel>
			<StatNumber color={isUnfavorable ? 'red.600' : undefined}>
				{value ?? '—'}
			</StatNumber>
			{helper && <StatHelpText color="gray.600" mb={delta ? 1 : 0}>{helper}</StatHelpText>}
			{delta && (
				<StatHelpText color={deltaIsFavorable ? 'green.600' : 'red.600'} mb={0}>
					{delta} since last week
				</StatHelpText>
			)}
		</Stat>
	</Box>
);

export default StatCard;
