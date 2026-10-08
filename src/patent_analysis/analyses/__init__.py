"""Native, source-independent analysis implementations."""

from patent_analysis.analyses.matrix import (
    MatrixBudgetError,
    analyze_matrix,
    analyze_matrix_csv,
)

__all__ = (
    "MatrixBudgetError",
    "analyze_matrix",
    "analyze_matrix_csv",
)
