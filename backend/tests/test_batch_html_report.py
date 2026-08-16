from dataclasses import replace
from pathlib import Path

from app.batch.html_report import render_html_report, write_html_report
from app.batch.service import BatchExecutionConfig, execute_batch
from app.batch.strategies import TeamMemberCount


def _result(tmp_path):
    scenario = tmp_path / "scenario.json"
    source = Path(__file__).parent / "fixtures" / "batch_scenario.json"
    scenario.write_bytes(source.read_bytes())
    return execute_batch(
        BatchExecutionConfig(
            scenario_path=scenario,
            team_composition=(TeamMemberCount("developer", 2),),
            strategy_names=("balanced", "quality-first"),
            repetitions=3,
            initial_seed=10,
        )
    )


def test_html_chart_values_are_deterministic_and_include_context(tmp_path) -> None:
    result = _result(tmp_path)

    first = render_html_report(result)
    second = render_html_report(result)
    normalized = " ".join(first.split())

    assert first == second
    assert f'data-value="{result.reports[0].summary.score_distribution.median}"' in first
    assert f'data-value="{result.reports[0].summary.total_cost_distribution.p90}"' in first
    assert "Seed range</dt><dd>10–12" in normalized
    assert "pm-sim-backend" in first
    assert "developer</code>: 2" in first


def test_html_escapes_scenario_and_strategy_text_and_writes_file(tmp_path) -> None:
    result = _result(tmp_path)
    unsafe = '<script>alert("unsafe")</script>'
    report = replace(result.reports[0], strategy=unsafe)
    strategy = replace(result.metadata.strategies[0], name=unsafe)
    result = replace(
        result,
        reports=(report, *result.reports[1:]),
        metadata=replace(
            result.metadata,
            scenario_name="Scenario <unsafe> & friends",
            strategies=(strategy, *result.metadata.strategies[1:]),
        ),
    )

    destination = tmp_path / "output" / "report.html"
    write_html_report(result, destination, create_parents=True)
    html = destination.read_text(encoding="utf-8")

    assert "Scenario &lt;unsafe&gt; &amp; friends" in html
    assert "&lt;script&gt;alert(&quot;unsafe&quot;)&lt;/script&gt;" in html
    assert unsafe not in html
