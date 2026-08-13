import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import StudentPanel from './StudentPanel';

const props = { className: 'PM 2026', selectedId: 'class-id', isBusy: false, onCreate: vi.fn(), onAdd: vi.fn(), onReset: vi.fn(), onRemove: vi.fn() };

test('shows a clear empty roster state', () => {
	render(<StudentPanel {...props} students={[]} />);
	expect(screen.getByText('No students in this class.')).toBeInTheDocument();
});

test('shows responsive, named actions without exposing student identifiers', () => {
	const onRemove = vi.fn();
	render(<StudentPanel {...props} students={[{ id: 'a52c1e4e-659e-47d0-82cb-dfe42132ad8f', username: 'ada' }]} onRemove={onRemove} />);
	expect(screen.getByText('ada')).toBeInTheDocument();
	expect(screen.getByRole('button', { name: 'Reset password' })).toBeInTheDocument();
	fireEvent.click(screen.getByRole('button', { name: 'Remove' }));
	expect(onRemove).toHaveBeenCalledWith(expect.objectContaining({ username: 'ada' }));
	expect(screen.queryByText(/a52c1e4e/)).not.toBeInTheDocument();
});
