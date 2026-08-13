import {
	AlertDialog,
	AlertDialogBody,
	AlertDialogContent,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogOverlay,
	Button,
} from '@chakra-ui/react';
import React, { useRef } from 'react';

const ConfirmDialog = ({ isOpen, title, message, confirmLabel = 'Confirm', onCancel, onConfirm, isBusy }) => {
	const cancelRef = useRef();

	return (
		<AlertDialog isOpen={isOpen} leastDestructiveRef={cancelRef} onClose={isBusy ? undefined : onCancel}>
			<AlertDialogOverlay>
				<AlertDialogContent>
					<AlertDialogHeader>{title}</AlertDialogHeader>
					<AlertDialogBody>{message}</AlertDialogBody>
					<AlertDialogFooter>
						<Button ref={cancelRef} isDisabled={isBusy} onClick={onCancel}>
							Cancel
						</Button>
						<Button
							colorScheme="red"
							ml={3}
							isLoading={isBusy}
							loadingText={confirmLabel}
							isDisabled={isBusy}
							onClick={onConfirm}
						>
							{confirmLabel}
						</Button>
					</AlertDialogFooter>
				</AlertDialogContent>
			</AlertDialogOverlay>
		</AlertDialog>
	);
};

export default ConfirmDialog;
