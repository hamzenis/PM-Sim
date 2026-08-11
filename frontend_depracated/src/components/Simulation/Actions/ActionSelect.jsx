import { Select } from '@chakra-ui/react';

const ActionSelect = (props) => {
	function handleSelect(event) {
		const selectedAnswer = event.target.value;
		if (selectedAnswer === 'Leave early') {
			props.onActionSelect(-1);
		} else if (selectedAnswer === 'Normal hours') {
			props.onActionSelect(0);
		} else if (selectedAnswer === 'Encourage overtime') {
			props.onActionSelect(1);
		} else if (selectedAnswer === 'Enforce overtime') {
			props.onActionSelect(2);
		}
	}
	return (
		<Select pl={3} onChange={(event) => handleSelect(event)} defaultValue={props.selection[1]}>
			{props.selection.map((value, index) => {
				return (
					<option key={index} value={value}>
						{value}
					</option>
				);
			})}
		</Select>
	);
};

export default ActionSelect;
