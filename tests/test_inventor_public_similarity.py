import json

from test_inventor_public import spec, write_patents

from patent_analysis.analysis_runner import run_analysis


def test_similarity_neutral_cosine_not_layout(tmp_path):
    write_patents(tmp_path)
    result = run_analysis(
        "patents.json",
        json.dumps(
            spec("inventor-similarity.v1", {"feature": "tfidf", "co_inventor_overlay": True})
        ).encode(),
        allowed_root=tmp_path,
    )
    stats = result["data"]["statistics"]
    assert len(stats["similarities"]) == 10
    assert stats["features"][-1]["undefined_reason"] == "zero_vector"
    assert stats["similarities"][-1]["cosine"] is None
    assert len(stats["co_inventor_edges"]) == 2
    assert "coordinates" not in stats
