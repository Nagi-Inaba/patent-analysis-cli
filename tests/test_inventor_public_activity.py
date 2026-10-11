import json

from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis


def test_activity_observation_dates_and_absence_are_not_zero(tmp_path):
    write_patents(tmp_path)
    result = run_analysis(
        "patents.json", json.dumps(spec("inventor-activity.v1")).encode(), allowed_root=tmp_path
    )
    stats = result["data"]["statistics"]
    assert stats["calendar"] == [
        dict(year=2023, observed=True, record_count=1, unit_count=1),
        dict(year=2024, observed=True, record_count=1, unit_count=1),
    ]
    a = [r for r in stats["observations"] if r["person_token"] == '["id","A"]']
    assert a[-1]["activity"] is None and not a[-1]["observed"]
    assert stats["missing_date_record_ids"] == ["r3"]
