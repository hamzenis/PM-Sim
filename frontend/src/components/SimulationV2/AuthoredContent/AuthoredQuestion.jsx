import { Button, Checkbox, FormControl, FormLabel, Radio, RadioGroup, Stack, Text, Textarea } from '@chakra-ui/react';
import React, { useState } from 'react';
import ContentFeedback from './ContentFeedback';

const persistedAnswer = (entry) => entry.latest_response?.value?.answer;

const AnswerReview = ({ entry }) => {
	const answer = persistedAnswer(entry);
	const options = entry.question?.options || [];
	const labels = Array.isArray(answer) ? answer.map((id) => options.find((option) => option.id === id)?.label || id) : [];
	let value = answer;
	if (entry.question?.answer_schema === 'single_choice') value = options.find((option) => option.id === answer)?.label || answer;
	if (entry.question?.answer_schema === 'multiple_choice') value = labels.join(', ');
	if (typeof value === 'boolean') value = value ? 'True' : 'False';
	return <Text mt={3}><Text as="span" fontWeight="semibold">Your answer: </Text>{String(value ?? '')}</Text>;
};

const AuthoredQuestion = ({ entry, isSubmitting, onAnswer }) => {
	const schema = entry.question?.answer_schema;
	const options = entry.question?.options || [];
	const maximum = entry.question?.short_text_max_length || 500;
	const initial = schema === 'multiple_choice' ? [] : schema === 'short_text' ? '' : null;
	const [answer, setAnswer] = useState(initial);
	const completed = entry.status === 'completed';
	const valid = schema === 'multiple_choice' || schema === 'short_text' ? !entry.required || answer.length > 0 : answer !== null;

	if (completed) return <><Text fontWeight="semibold">{entry.prompt}</Text><AnswerReview entry={entry} /><ContentFeedback feedback={entry.feedback} /></>;

	return (
		<FormControl as="fieldset" isRequired={entry.required}>
			<FormLabel as="legend" htmlFor={schema === 'short_text' ? `${entry.sequence_entry_id}-answer` : undefined}>{entry.prompt}</FormLabel>
			{schema === 'single_choice' && (
				<RadioGroup value={answer || ''} onChange={setAnswer}><Stack>{options.map((option) => <Radio key={option.id} value={option.id}>{option.label}</Radio>)}</Stack></RadioGroup>
			)}
			{schema === 'multiple_choice' && <Stack>{options.map((option) => (
				<Checkbox key={option.id} isChecked={answer.includes(option.id)} onChange={(event) => setAnswer(event.target.checked ? [...answer, option.id] : answer.filter((id) => id !== option.id))}>{option.label}</Checkbox>
			))}</Stack>}
			{schema === 'boolean' && <RadioGroup value={answer === null ? '' : String(answer)} onChange={(value) => setAnswer(value === 'true')}><Stack direction="row"><Radio value="true">True</Radio><Radio value="false">False</Radio></Stack></RadioGroup>}
			{schema === 'short_text' && <><Textarea id={`${entry.sequence_entry_id}-answer`} value={answer} maxLength={maximum} onChange={(event) => setAnswer(event.target.value)} aria-describedby={`${entry.sequence_entry_id}-remaining`} /><Text id={`${entry.sequence_entry_id}-remaining`} fontSize="sm" color="gray.600">{maximum - answer.length} characters remaining</Text></>}
			<Button mt={4} colorScheme="blue" size="sm" isLoading={isSubmitting} isDisabled={!valid} onClick={() => onAnswer(answer)}>Submit answer</Button>
			<ContentFeedback feedback={entry.feedback} />
		</FormControl>
	);
};

export default AuthoredQuestion;
