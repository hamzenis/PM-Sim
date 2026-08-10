import { scenarioAssignmentKey } from './ScenarioOverview';

test('uses both class and revision IDs for scenario assignments', () => {
	expect(scenarioAssignmentKey('class-1', 'revision-1')).toBe('class-1:revision-1');
	expect(scenarioAssignmentKey('class-2', 'revision-1')).not.toBe(scenarioAssignmentKey('class-1', 'revision-1'));
});
