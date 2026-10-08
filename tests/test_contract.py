import pytest

from patent_analysis.contracts import (
    CONTRACT_VERSION,
    OperationContractError,
    describe_contract,
    get_operation_plan_cases,
    validate_operation_plan,
)


def test_contract_description_exposes_version_and_registered_operations():
    contract = describe_contract()

    assert CONTRACT_VERSION == "1.0.0"
    assert contract["contract_version"] == CONTRACT_VERSION
    assert contract["schema_id"] == "urn:patent-analysis:operation-plan:1.0.0"
    assert contract["operations"] == sorted(
        [
            "add_analysis_note",
            "aggregate_dataset",
            "apply_selection_set",
            "clear_filter",
            "create_analysis",
            "create_selection_set",
            "draft_report_section",
            "drilldown_from_chart_element",
            "export_report_draft",
            "inspect_schema",
            "query_rows",
            "rerender_chart",
            "save_snapshot",
            "set_filter",
            "set_render_mode",
        ]
    )
    assert contract["commands"] == ["contract", "validate-plan"]


def test_plan_case_corpus_loads_and_covers_all_operations():
    cases = get_operation_plan_cases()

    assert cases["contract_version"] == CONTRACT_VERSION
    assert set(cases) >= {"valid", "invalid_schema", "invalid_semantic"}
    assert len(cases["valid"]) >= 15
    assert len(cases["invalid_schema"]) >= 4
    assert len(cases["invalid_semantic"]) >= 3

    seen = {
        case["plan"]["operations"][0]["type"]
        for case in cases["valid"]
    }
    assert seen == set(describe_contract()["operations"])


def test_plan_case_corpus_valid_cases_are_accepted():
    cases = get_operation_plan_cases()

    for case in cases["valid"]:
        validate_operation_plan(case["plan"])


def test_plan_case_corpus_invalid_cases_fail_as_expected():
    for case in [
        *get_operation_plan_cases()["invalid_schema"],
        *get_operation_plan_cases()["invalid_semantic"],
    ]:
        expected = case.get("error_code", "contract.invalid")
        with pytest.raises(OperationContractError) as caught:
            validate_operation_plan(case["plan"])
        assert caught.value.code == expected


def test_valid_matrix_heatmap_plan_passes_contract_validation():
    plan = {
        "intent": "IPC subclass by applicant matrix",
        "operations": [
            {
                "type": "create_analysis",
                "params": {
                    "analysis_type": "matrix",
                    "x": "ipc_subclass",
                    "y": "applicant",
                },
            },
            {"type": "set_render_mode", "params": {"mark": "heatmap"}},
        ],
    }

    validate_operation_plan(plan)


def test_contract_rejects_unknown_operations_and_schema_only_payload_keys():
    with pytest.raises(OperationContractError, match="unknown operation") as unknown_error:
        validate_operation_plan(
            {
                "intent": "run arbitrary code",
                "operations": [{"type": "run_anything", "params": {}}],
            }
        )
    assert unknown_error.value.code == "operation.unknown"
    assert unknown_error.value.retryable is False
    assert "path" not in unknown_error.value.details

    with pytest.raises(OperationContractError, match="operation plan violates the schema"):
        validate_operation_plan(
            {
                "intent": "extra sql key",
                "operations": [
                    {
                        "type": "query_rows",
                        "params": {
                            "dataset_id": "dataset-1",
                            "sql": "select * from patents",
                        },
                    }
                ],
            }
        )


def test_contract_accepts_untrusted_like_add_analysis_note_bodies():
    validate_operation_plan(
        {
            "intent": "note body should be accepted",
            "operations": [
                {
                    "type": "add_analysis_note",
                    "params": {
                        "body": "rm -rf / && powershell exec('whoami') // SELECT * FROM patents",
                        "snapshot_id": "snapshot-1",
                    },
                }
            ],
        }
    )


def test_contract_rejects_render_mark_incompatible_with_analysis():
    with pytest.raises(
        OperationContractError,
        match="scatter is not supported for ranking",
    ) as incompatible:
        validate_operation_plan(
            {
                "intent": "invalid ranking scatter",
                "operations": [
                    {
                        "type": "create_analysis",
                        "params": {"analysis_type": "ranking", "x": "applicant"},
                    },
                    {"type": "set_render_mode", "params": {"mark": "scatter"}},
                ],
            }
        )
    assert incompatible.value.code == "operation.incompatible_render"


@pytest.mark.parametrize(
    "plan",
    [
        [],
        {},
        {"intent": "", "operations": []},
        {"intent": "bounded", "operations": []},
        {
            "intent": "too many operations",
            "operations": [
                {"type": "inspect_schema", "params": {"dataset_id": "dataset-1"}}
            ]
            * 21,
        },
        {
            "intent": "unexpected top-level key",
            "operations": [
                {"type": "inspect_schema", "params": {"dataset_id": "dataset-1"}}
            ],
            "path": "secret.csv",
        },
    ],
)
def test_contract_rejects_invalid_plan_shapes_and_bounds(plan):
    with pytest.raises(OperationContractError):
        validate_operation_plan(plan)


def test_contract_rejects_whitespace_only_intent_like_workbench_registry():
    with pytest.raises(OperationContractError, match="operation plan intent is required"):
        validate_operation_plan(
            {
                "intent": "   ",
                "operations": [
                    {"type": "inspect_schema", "params": {"dataset_id": "dataset-1"}}
                ],
            }
        )


def test_contract_accepts_float_like_integers_for_integer_fields():
    validate_operation_plan(
        {
            "intent": "accept integer-like number",
            "operations": [
                {
                    "type": "query_rows",
                    "params": {"dataset_id": "dataset-1", "limit": 1.0},
                }
            ],
        }
    )


def test_contract_rejects_string_numbers_for_integer_fields():
    with pytest.raises(OperationContractError, match="operation plan violates the schema"):
        validate_operation_plan(
            {
                "intent": "integer string should fail",
                "operations": [
                    {
                        "type": "query_rows",
                        "params": {"dataset_id": "dataset-1", "limit": "1"},
                    }
                ],
            }
        )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_public_contract_rejects_non_finite_numbers(value):
    with pytest.raises(OperationContractError, match="non-finite"):
        validate_operation_plan(
            {
                "intent": "bounded numeric value",
                "operations": [
                    {
                        "type": "set_filter",
                        "params": {
                            "dimension": "score",
                            "operator": "equals",
                            "value": value,
                        },
                    }
                ],
            }
        )


def test_public_contract_rejects_excessive_nesting_without_node_limit_check():
    secret_key = r"C:\Users\Alice\secret.txt"
    nested = {}
    for _ in range(70):
        nested = {secret_key: nested}

    with pytest.raises(OperationContractError, match="nested too deeply") as caught:
        validate_operation_plan(
            {
                "intent": "nested",
                "operations": [
                    {
                        "type": "inspect_schema",
                        "params": {"dataset_id": "x"},
                    }
                ],
                "extra": nested,
            }
        )
    assert secret_key not in str(caught.value.as_dict())


def test_contract_accepts_large_plan_within_published_field_bounds():
    values = [f"value-{index}" for index in range(100)]
    filters = [
        {
            "dimension": f"dimension-{index}",
            "operator": "in",
            "values": values,
        }
        for index in range(20)
    ]
    validate_operation_plan(
        {
            "intent": "large plan within every published field bound",
            "operations": [
                {
                    "type": "query_rows",
                    "params": {"dataset_id": f"dataset-{index}", "filters": filters},
                }
                for index in range(6)
            ],
        }
    )


def test_contract_rejects_multiple_analysis_and_render_operations():
    with pytest.raises(OperationContractError, match="multiple create_analysis"):
        validate_operation_plan(
            {
                "intent": "ambiguous analysis",
                "operations": [
                    {
                        "type": "create_analysis",
                        "params": {"analysis_type": "ranking", "x": "applicant"},
                    },
                    {
                        "type": "create_analysis",
                        "params": {"analysis_type": "timeline", "x": "year"},
                    },
                ],
            }
        )

    with pytest.raises(OperationContractError, match="multiple set_render_mode"):
        validate_operation_plan(
            {
                "intent": "ambiguous rendering",
                "operations": [
                    {"type": "set_render_mode", "params": {"mark": "bar"}},
                    {"type": "set_render_mode", "params": {"mark": "line"}},
                ],
            }
        )


def test_contract_rejects_manual_selection_values_duplicate():
    with pytest.raises(OperationContractError):
        validate_operation_plan(
            {
                "intent": "duplicate manual selection",
                "operations": [
                    {
                        "type": "create_selection_set",
                        "params": {
                            "dimension": "publication_number",
                            "mode": "manual",
                            "values": ["JP-1", "JP-1"],
                        },
                    }
                ],
            }
        )


def test_contract_allows_null_values_for_non_manual_selection_set_modes():
    validate_operation_plan(
        {
            "intent": "selection set null fields accepted",
            "operations": [
                {
                    "type": "create_selection_set",
                    "params": {
                        "dimension": "publication_number",
                        "mode": "all",
                        "values": None,
                        "record_tokens": None,
                    },
                }
            ],
        }
    )


def test_contract_requires_manual_selection_set_to_have_one_non_null_source():
    with pytest.raises(OperationContractError, match="operation plan violates the schema"):
        validate_operation_plan(
            {
                "intent": "manual missing source",
                "operations": [
                    {
                        "type": "create_selection_set",
                        "params": {
                            "dimension": "publication_number",
                            "mode": "manual",
                        },
                    }
                ],
            }
        )


def test_contract_accepts_manual_record_tokens_with_explicit_null_values():
    validate_operation_plan(
        {
            "intent": "manual token source",
            "operations": [
                {
                    "type": "create_selection_set",
                    "params": {
                        "dimension": "publication_number",
                        "mode": "manual",
                        "values": None,
                        "record_tokens": ["record-1"],
                    },
                }
            ],
        }
    )
    with pytest.raises(OperationContractError, match="operation plan violates the schema"):
        validate_operation_plan(
            {
                "intent": "manual multiple sources",
                "operations": [
                    {
                        "type": "create_selection_set",
                        "params": {
                            "dimension": "publication_number",
                            "mode": "manual",
                            "values": ["JP-1"],
                            "record_tokens": ["token-1"],
                        },
                    }
                ],
            }
        )
