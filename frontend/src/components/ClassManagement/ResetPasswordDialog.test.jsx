import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import ResetPasswordDialog from './ResetPasswordDialog';

test('requires a matching password with at least ten characters', () => {
	const onSave = jest.fn();
	render(
		<ResetPasswordDialog
			student={{ username: 'student' }}
			isOpen
			isBusy={false}
			onCancel={jest.fn()}
			onSave={onSave}
		/>
	);

	const saveButton = screen.getByRole('button', { name: 'Reset password' });
	fireEvent.change(screen.getByLabelText('New temporary password'), { target: { value: 'new-password' } });
	fireEvent.change(screen.getByLabelText('Repeat password'), { target: { value: 'different-password' } });
	expect(saveButton).toBeDisabled();

	fireEvent.change(screen.getByLabelText('Repeat password'), { target: { value: 'new-password' } });
	fireEvent.click(saveButton);
	expect(onSave).toHaveBeenCalledWith('new-password');
});
