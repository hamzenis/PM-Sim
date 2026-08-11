/** Total a simulation task pool while tolerating an absent pool. */
export const totalTaskPool = (pool = {}) =>
	['easy', 'medium', 'hard'].reduce((total, difficulty) => total + Number(pool?.[difficulty] || 0), 0);
