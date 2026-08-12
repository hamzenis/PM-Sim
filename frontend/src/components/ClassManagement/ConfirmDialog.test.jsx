import { ChakraProvider } from '@chakra-ui/react';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';
import ConfirmDialog from './ConfirmDialog';

test('focuses the cancel button when the confirmation dialog opens', async () => {
	render(
		<ChakraProvider>
			<ConfirmDialog
				isOpen
				title="Delete class"
				message="This action cannot be undone."
				onCancel={vi.fn()}
				onConfirm={vi.fn()}
			/>
		</ChakraProvider>
	);

	await waitFor(() => expect(screen.getByRole('button', { name: 'Cancel' })).toHaveFocus());
});
