import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import ScenarioImportDialog from './ScenarioImportDialog';

test('parses a JSON definition before importing it', () => {
	const onImport = jest.fn();
	render(<ScenarioImportDialog isOpen isBusy={false} onCancel={jest.fn()} onImport={onImport} />);
	fireEvent.change(screen.getByLabelText('Scenario definition'), {
		target: { value: '{"schema_version":1,"name":"Example","authored_content":{"fragments":[],"questions":[],"events":[],"sequence":[]}}' },
	});
	fireEvent.click(screen.getByRole('button', { name: 'Validate and import' }));
	expect(onImport).toHaveBeenCalledWith({
		schema_version: 1,
		name: 'Example',
		authored_content: { fragments: [], questions: [], events: [], sequence: [] },
	});
});
