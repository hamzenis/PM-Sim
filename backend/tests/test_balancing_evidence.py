from scenario_examples.balancing.datawarehouse_migration_kt_1571220 import generate_evidence


def test_evidence_summary_schema_and_seed_range_are_stable(monkeypatch) -> None:
    monkeypatch.setattr(generate_evidence, "REPETITIONS", 2)

    summary, rows = generate_evidence.generate_evidence()

    assert list(summary) == [
        "scenario",
        "scenario_sha256",
        "engine_entry_point",
        "initial_seed",
        "repetitions_per_strategy",
        "seed_range",
        "strategies",
        "modes",
    ]
    assert summary["seed_range"] == [1_571_220, 1_571_221]
    assert set(summary["modes"]) == {"none", "semi"}
    strategy_summary = summary["modes"]["semi"]["low-cost-staffing"]
    assert list(strategy_summary["score_distribution"]) == [
        "mean",
        "min",
        "p10",
        "median",
        "p90",
        "max",
    ]
    assert {row["seed"] for row in rows} == {1_571_220, 1_571_221}
