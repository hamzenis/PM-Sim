/** Total a simulation task pool while tolerating an absent pool. */
export const taskPoolTotal = (pool = {}) =>
	['easy', 'medium', 'hard'].reduce((total, difficulty) => total + Number(pool?.[difficulty] || 0), 0);
