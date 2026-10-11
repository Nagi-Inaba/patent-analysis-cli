from copy import deepcopy

from patent_analysis_mcp.tool_handlers import ToolHandlers


def test_sidecar_provenance_is_removed_inside_nested_list_containers():
    synthetic = {
        'data': {
            'provenance': {'sidecars': [[{'source_sha256': 'a' * 64,
                                          'format': 'json', 'receipt': {'private': True}}]]},
            'candidate_id': 'synthetic-public-candidate',
        },
    }
    before = deepcopy(synthetic)
    projected = ToolHandlers._without_linkable_provenance(synthetic)
    assert projected == {
        'data': {
            'provenance': {'sidecars': [[{'format': 'json'}]]},
            'candidate_id': 'synthetic-public-candidate',
        },
    }
    assert synthetic == before
