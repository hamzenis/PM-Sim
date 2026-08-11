from types import SimpleNamespace
import pytest

from app.src.util import score_util
from app.src.util.score_util import calc_scores


class DummyState:
    def __init__(self, day, cost):
        self.day = day
        self.cost = cost


class DummyTasks:
    def __init__(self, tasks, rejected):
        self.tasks = tasks
        self._rejected = rejected

    def rejected(self):
        return self._rejected


class DummyScoreCard:
    def __init__(
        self,
        quality_limit=100,
        time_limit=100,
        budget_limit=100,
        quality_k=1.0,
        time_p=1.0,
        budget_p=1.0,
    ):
        self.quality_limit = quality_limit
        self.time_limit = time_limit
        self.budget_limit = budget_limit
        self.quality_k = quality_k
        self.time_p = time_p
        self.budget_p = budget_p


class DummyManagementGoal:
    def __init__(self, duration, budget):
        self.duration = duration
        self.budget = budget


class DummyQuestionCollection:
    def __init__(self, questions):
        # questions: list of DummyQuestion
        self.questions = SimpleNamespace(all=lambda: questions)


class DummyTemplate:
    def __init__(self, score_card, management_goal, question_collections=None):
        self.score_card = score_card
        self.management_goal = management_goal
        # question_collections should expose .all()
        if question_collections is None:
            self.question_collections = SimpleNamespace(all=lambda: [])
        else:
            self.question_collections = SimpleNamespace(all=lambda: question_collections)


class DummyScenario:
    def __init__(self, template, state, question_points=0):
        self.template = template
        self.state = state
        self.question_points = question_points


def _patch_answer_objects_with(monkeypatch, points_list):
    """
    Patch score_util.Answer so that Answer.objects.filter(question) returns a list
    of objects with .points attributes whose values are from points_list.
    """
    class Manager:
        def __init__(self, ret):
            self._ret = ret

        def filter(self, question):
            return self._ret

    answers = [SimpleNamespace(points=p) for p in points_list]
    fake_answer = SimpleNamespace(objects=Manager(answers))
    monkeypatch.setattr(score_util, "Answer", fake_answer, raising=False)


def test_calc_scores_simple(monkeypatch):
    # Setup score card and goal with defaults
    score_card = DummyScoreCard(
        quality_limit=100, time_limit=100, budget_limit=100, quality_k=1.0, time_p=1.0, budget_p=1.0
    )
    goal = DummyManagementGoal(duration=5, budget=1000)

    # No question collections
    template = DummyTemplate(score_card=score_card, management_goal=goal, question_collections=None)

    # scenario: 10 tasks with 2 rejected -> quality = int((1 - 2/10)^1 * 100) = 80
    tasks = DummyTasks(tasks=list(range(10)), rejected=[1, 2])
    state = DummyState(day=5, cost=500)  # time <= scheduled -> full time score, cost <= budget -> full budget score
    scenario = DummyScenario(template=template, state=state, question_points=0)

    # Ensure no positive answers
    _patch_answer_objects_with(monkeypatch, [])

    res = calc_scores(scenario, tasks)

    assert res["quality_score"] == 80
    assert res["time_score"] == 100
    assert res["budget_score"] == 100
    # raw_total = 80 + 100 + 100 + 0 = 280; denom = 300 -> 93.333 -> rounded 93
    assert res["total_score"] == 93
    assert res["question_score"] == 0


def test_calc_scores_with_question_points_and_positive_answers(monkeypatch):
    # Use smaller limits
    score_card = DummyScoreCard(
        quality_limit=50, time_limit=50, budget_limit=50, quality_k=1.0, time_p=1.0, budget_p=1.0
    )
    goal = DummyManagementGoal(duration=10, budget=100)

    # Create one question collection with one question (question object is irrelevant for our fake)
    q1 = SimpleNamespace()
    qc = DummyQuestionCollection([q1])
    template = DummyTemplate(score_card=score_card, management_goal=goal, question_collections=[qc])

    # tasks: 10 tasks, 1 rejected -> quality = int((1 - 1/10) * 50) = int(0.9 * 50) = 45
    tasks = DummyTasks(tasks=list(range(10)), rejected=[0])
    state = DummyState(day=8, cost=80)  # before/within -> full time and budget
    scenario = DummyScenario(template=template, state=state, question_points=10)

    # Patch Answer to return a positive points list that sums to 20
    _patch_answer_objects_with(monkeypatch, [5, 15])  # total_positive_points = 20

    res = calc_scores(scenario, tasks)

    assert res["quality_score"] == 45
    assert res["time_score"] == 50
    assert res["budget_score"] == 50
    # raw_total = 45 + 50 + 50 + 10 = 155
    total_limits = 50 + 50 + 50  # 150
    denom = total_limits + 20  # 170
    expected_percentage = (155 / denom) * 100
    expected_rounded = int(round(expected_percentage))
    assert res["total_score"] == expected_rounded
    assert res["question_score"] == 10