export const orderedContentEntries = (deliveries = []) =>
	[...deliveries].filter((entry) => entry.visible !== false).sort((left, right) => left.sequence_ordinal - right.sequence_ordinal);

export const selectEarliestActionableRequiredEntry = (deliveries = []) =>
	orderedContentEntries(deliveries).find((entry) => entry.required && entry.status === 'actionable') || null;

export const selectRequiredContentBlocking = (deliveries = []) =>
	Boolean(selectEarliestActionableRequiredEntry(deliveries));

export const selectContentFeedback = (entry) => entry?.feedback || null;

export const selectContentState = (deliveries = []) => ({
	entries: orderedContentEntries(deliveries),
	earliestActionableRequiredEntry: selectEarliestActionableRequiredEntry(deliveries),
	isBlocking: selectRequiredContentBlocking(deliveries),
});

// Short aliases keep consumers readable while the longer names document intent.
export const sortContentEntries = orderedContentEntries;
export const earliestActionableRequiredEntry = selectEarliestActionableRequiredEntry;
export const isRequiredContentBlocking = selectRequiredContentBlocking;
