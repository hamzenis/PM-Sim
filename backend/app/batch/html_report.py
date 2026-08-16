"""Dependency-free, self-contained HTML reports for batch experiment results."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import TYPE_CHECKING

from app.batch.export import export_text
from app.batch.runner import DistributionSummary, SimulationBatchReport
from app.simulation.results import SimulationOutcome

if TYPE_CHECKING:
    from app.batch.service import BatchExecutionResult


def render_html_report(result: BatchExecutionResult) -> str:
    """Render a deterministic report body (apart from supplied envelope metadata)."""
    metadata = result.metadata
    team = "".join(
        f"<li><code>{escape(member.employee_type_code)}</code>: {member.count}</li>"
        for member in result.provenance.team_composition
    )
    strategies = ", ".join(
        f"<code>{escape(strategy.name)}</code>" for strategy in metadata.strategies
    )
    score_charts = "".join(_distribution_chart(report, "score") for report in result.reports)
    cost_charts = "".join(_distribution_chart(report, "total_cost") for report in result.reports)
    completion_chart = _completion_chart(result.reports)
    comparison_chart = _comparison_chart(result.reports)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Batch report — {escape(metadata.scenario_name)}</title>
<style>
:root {{ color-scheme: light; font-family: system-ui, sans-serif; color: #172033; }}
body {{ max-width: 1100px; margin: auto; padding: 2rem; background: #f6f8fb; }}
header, section {{ background: white; padding: 1.25rem; margin-bottom: 1rem; border-radius:
.5rem; }}
h1, h2 {{ color: #173b67; }} .charts {{ display: grid; grid-template-columns:
repeat(auto-fit,minmax(300px,1fr)); gap: 1rem; }}
figure {{ margin: 0; padding: 1rem; border: 1px solid #d8dfeb; }} svg {{ width: 100%; height:
auto; }}
.bar {{ fill: #3478b8; }} .complete {{ fill: #23845a; }} .incomplete {{ fill: #c8654a; }}
.label {{ font-size: 12px; fill: #172033; }} .value {{ font-size: 11px; fill: #172033; }}
code {{ overflow-wrap: anywhere; }} table {{ border-collapse: collapse; width: 100%; }} th,td
{{ padding:.4rem; text-align:left; border-bottom:1px solid #ddd; }}
</style></head><body>
<header><h1>Batch experiment report</h1>
<dl><dt>Scenario</dt><dd>{escape(metadata.scenario_name)}</dd><dt>Scenario
SHA-256</dt><dd><code>{escape(metadata.scenario_sha256)}</code></dd>
<dt>Package</dt><dd>{escape(metadata.pm_sim_package)} {escape(metadata.pm_sim_version)}</dd>
<dt>Report schema</dt><dd>{metadata.schema_version}</dd><dt>Seed
range</dt><dd>{metadata.initial_seed}–{metadata.final_seed}</dd>
<dt>Repetitions per
strategy</dt><dd>{metadata.repetitions}</dd><dt>Strategies</dt><dd>{strategies}</dd></dl>
<h2>Team composition</h2><ul>{team}</ul></header>
<section><h2>Score distribution by strategy</h2><p>Each range shows the 10th, median, and 90th
percentile score. It makes typical results and spread easier to compare without hiding
variation behind one average.</p><div class="charts">{score_charts}</div></section>
<section><h2>Completion versus non-completion</h2><p>Counts show how many runs completed the
project and how many ended for another reason.</p>{completion_chart}</section>
<section><h2>Total-cost distribution</h2><p>Each range shows the 10th, median, and 90th
percentile total cost, revealing both a typical cost and the spread between lower- and
higher-cost runs.</p><div class="charts">{cost_charts}</div></section>
<section><h2>Average score, completion, and budget exhaustion</h2><p>Bars compare average
score, completion rate, and budget-exhaustion rate on a common 0–100 scale. Rates are displayed
as percentages.</p>{comparison_chart}</section>
<section><h2>How to use this report</h2><p>These deliberately simple strategy baselines are
balancing aids, not predictions of student behavior. Review the retained per-run CSV alongside
these summaries before drawing conclusions.</p></section>
</body></html>\n"""


def write_html_report(
    result: BatchExecutionResult,
    destination: Path | str,
    *,
    create_parents: bool = False,
    force: bool = False,
) -> None:
    """Atomically write a self-contained HTML report."""
    export_text(render_html_report(result), destination, create_parents=create_parents, force=force)


def _format_number(value: float) -> str:
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _distribution_chart(report: SimulationBatchReport, metric: str) -> str:
    summary: DistributionSummary = getattr(report.summary, f"{metric}_distribution")
    maximum = max(summary.max, 1)
    points = (("p10", summary.p10), ("median", summary.median), ("p90", summary.p90))
    bars = "".join(
        f'<text class="label" x="0" y="{25 + index * 38}">{label}</text>'
        f'<rect class="bar" data-value="{value}" x="65" y="{10 + index * 38}" '
        f'width="{value / maximum * 210:.3f}" height="20"/>'
        f'<text class="value" x="280" y="{25 + index * 38}">{_format_number(value)}</text>'
        for index, (label, value) in enumerate(points)
    )
    label = f"{escape(report.strategy)} {metric.replace('_', ' ')} percentiles"
    return (
        f"<figure><figcaption>{escape(report.strategy)}</figcaption>"
        f'<svg viewBox="0 0 350 125" role="img" aria-label="{label}">{bars}</svg></figure>'
    )


def _completion_chart(reports: tuple[SimulationBatchReport, ...]) -> str:
    rows = []
    for report in reports:
        completed = sum(run.result.outcome == SimulationOutcome.COMPLETED for run in report.runs)
        incomplete = len(report.runs) - completed
        rows.append(
            f'<tr><th>{escape(report.strategy)}</th><td data-value="{completed}">{completed}</td>'
            f'<td data-value="{incomplete}">{incomplete}</td></tr>'
        )
    return (
        "<table><thead><tr><th>Strategy</th><th>Completed</th>"
        "<th>Not completed</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _comparison_chart(reports: tuple[SimulationBatchReport, ...]) -> str:
    rows = []
    for report in reports:
        values = (
            ("Average score", report.summary.average_score),
            ("Completion", report.summary.completion_rate * 100),
            ("Budget exhaustion", report.summary.budget_exhaustion_rate * 100),
        )
        bars = "".join(
            f'<text class="label" x="0" y="{25 + index * 34}">{label}</text>'
            f'<rect class="bar" data-value="{value}" x="125" y="{10 + index * 34}" '
            f'width="{max(0, min(value, 100)) * 2:.3f}" height="20"/>'
            f'<text class="value" x="330" y="{25 + index * 34}">{_format_number(value)}</text>'
            for index, (label, value) in enumerate(values)
        )
        rows.append(
            f"<figure><figcaption>{escape(report.strategy)}</figcaption>"
            f'<svg viewBox="0 0 390 112" role="img" '
            f'aria-label="{escape(report.strategy)} averages">{bars}</svg></figure>'
        )
    return '<div class="charts">' + "".join(rows) + "</div>"
