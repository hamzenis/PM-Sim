const LABEL_OVERRIDES = {
	bug_fixing: 'Bug fixing',
	integration_testing: 'Integration testing',
	unit_testing: 'Unit testing',
	tasks_completed: 'Tasks completed',
	tasks_returned_to_backlog: 'Tasks returned to backlog',
	tasks_integration_tested: 'Tasks integration tested',
};

export const plainLanguageLabel = (key = '') =>
	LABEL_OVERRIDES[key] || key.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());

export const readableStatus = (status = '') => plainLanguageLabel(status).replace('Deadline Reached', 'Deadline reached');

export const statusColor = (status) => ({ completed: 'green', submitted: 'blue', deadline_reached: 'orange' })[status] || 'gray';

export const formatDateTime = (value) => value ? new Intl.DateTimeFormat(undefined, {
	dateStyle: 'medium', timeStyle: 'short',
}).format(new Date(value)) : 'Not completed';

export const formatMoney = (value) => new Intl.NumberFormat(undefined, {
	style: 'currency', currency: 'USD', maximumFractionDigits: 0,
}).format(value);

export const formatPercent = (value) => new Intl.NumberFormat(undefined, {
	style: 'percent', maximumFractionDigits: 1,
}).format(value > 1 ? value / 100 : value);

export const formatTeachingValue = (key, value) => {
	if (value == null) return '—';
	if (Array.isArray(value)) return value.length ? value.map((item) => formatTeachingValue(key, item)).join('; ') : 'None';
	if (typeof value === 'object') return Object.entries(value).map(([childKey, childValue]) => {
		const formatted = /allocation|percent|rate/.test(key) && typeof childValue === 'number'
			? formatPercent(childValue)
			: formatTeachingValue(childKey, childValue);
		return `${plainLanguageLabel(childKey)}: ${formatted}`;
	}).join(', ');
	if (/budget|cost|salary/.test(key) && typeof value === 'number') return formatMoney(value);
	if (/percent|rate|allocation/.test(key) && typeof value === 'number') return formatPercent(value);
	if (typeof value === 'boolean') return value ? 'Yes' : 'No';
	return String(value);
};
