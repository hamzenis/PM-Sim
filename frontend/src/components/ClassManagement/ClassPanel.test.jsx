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

test('selects and creates classes by their human-readable names', () => {
	const onSelect = vi.fn();
	const onCreate = vi.fn();
	render(<ClassPanel classes={[{ id: 'class-2', name: 'Fall studio' }]} selectedId="" isBusy={false} onSelect={onSelect} onCreate={onCreate} onRename={vi.fn()} onArchive={vi.fn()} />);
	fireEvent.change(screen.getByLabelText('Current class'), { target: { value: 'class-2' } });
	expect(onSelect).toHaveBeenCalledWith('class-2');
	fireEvent.change(screen.getByLabelText('New class name'), { target: { value: 'Spring studio' } });
	fireEvent.click(screen.getByRole('button', { name: 'Create class' }));
	expect(onCreate).toHaveBeenCalledWith('Spring studio');
});
