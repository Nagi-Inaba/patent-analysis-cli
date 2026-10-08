"""Public Python API for patent-analysis-cli."""

from patent_analysis._version import PACKAGE_VERSION
from patent_analysis.analysis import analyze_csv
from patent_analysis.analysis_contracts import (
    ANALYSIS_CONTRACT_VERSION,
    AnalysisContractError,
    get_analysis_result_schema,
    get_analysis_spec_schema,
    validate_analysis_result,
    validate_analysis_spec,
)
from patent_analysis.api import (
    describe_capabilities,
    get_public_schema,
    inspect_dataset,
    render_analysis_svg,
    run_analysis,
    run_analysis_csv,
    validate_analysis_spec_bytes,
)
from patent_analysis.chart_model import (
    build_ranking_chart_model,
    build_ranking_render_spec,
)
from patent_analysis.contracts import (
    CONTRACT_VERSION,
    OperationContractError,
    describe_contract,
    get_operation_plan_cases,
    get_operation_schema,
    list_operations,
    validate_operation_plan,
)
from patent_analysis.data import DatasetInputError, inspect_csv
from patent_analysis.render_errors import RenderError
from patent_analysis.rendering import render_ranking_svg

__all__ = [
    "CONTRACT_VERSION",
    "OperationContractError",
    "describe_contract",
    "get_operation_schema",
    "get_operation_plan_cases",
    "list_operations",
    "validate_operation_plan",
    "ANALYSIS_CONTRACT_VERSION",
    "AnalysisContractError",
    "get_analysis_result_schema",
    "get_analysis_spec_schema",
    "validate_analysis_result",
    "validate_analysis_spec",
    "DatasetInputError",
    "inspect_csv",
    "analyze_csv",
    "describe_capabilities",
    "inspect_dataset",
    "run_analysis",
    "run_analysis_csv",
    "render_analysis_svg",
    "get_public_schema",
    "validate_analysis_spec_bytes",
    "build_ranking_chart_model",
    "build_ranking_render_spec",
    "RenderError",
    "render_ranking_svg",
]

__version__ = PACKAGE_VERSION
