import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import ClassPanel from './ClassPanel';

test('renames the selected class', () => {
	const onRename = vi.fn();
	render(
		<ClassPanel
			classes={[{ id: 'class-1', name: 'Old name' }]}
			selectedId="class-1"
			selectedClass={{ id: 'class-1', name: 'Old name' }}
			isBusy={false}
			onSelect={vi.fn()}
			onCreate={vi.fn()}
			onRename={onRename}
			onArchive={vi.fn()}
		/>
	);

	fireEvent.change(screen.getByLabelText('Class name'), { target: { value: 'New name' } });
	fireEvent.click(screen.getByRole('button', { name: 'Rename class' }));

	expect(onRename).toHaveBeenCalledWith('New name');
});
