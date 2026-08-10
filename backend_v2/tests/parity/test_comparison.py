from app.parity.comparison import ParityDifference, compare_snapshots


def test_snapshot_comparison_reports_precise_paths_and_tolerates_float_noise() -> None:
    legacy = {"budget": 100.0, "tasks": {"done": 4}, "events": ["hired"]}
    rewritten = {"budget": 100.0000000001, "tasks": {"done": 3}, "events": ["hired", "paid"]}
    assert compare_snapshots(legacy, rewritten) == [
        ParityDifference("$.events.length", 1, 2),
        ParityDifference("$.tasks.done", 4, 3),
    ]


def test_snapshot_comparison_can_ignore_approved_differences() -> None:
    assert (
        compare_snapshots(
            {"state": {"id": "legacy", "week": 1}},
            {"state": {"id": "new", "week": 1}},
            ignored_paths=frozenset({"$.state.id"}),
        )
        == []
    )


def test_snapshot_comparison_does_not_treat_booleans_as_integers() -> None:
    assert compare_snapshots({"finished": True}, {"finished": 1}) == [
        ParityDifference("$.finished", True, 1)
    ]
