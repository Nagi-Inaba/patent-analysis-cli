"""Canonical source-independent normalization public surface."""

from patent_analysis.normalization.applicant import applicant_key, normalize_applicant
from patent_analysis.normalization.classification import (
    CLASSIFICATION_LEVELS,
    derive_classification_values,
    format_classification,
)
from patent_analysis.normalization.multi_value import (
    MAX_NORMALIZED_VALUES_PER_CELL,
    split_patent_values,
    stable_dedupe,
)
from patent_analysis.normalization.pipeline import (
    MAX_NORMALIZATION_ROLES,
    MAX_NORMALIZED_CONTRIBUTIONS,
    NORMALIZATION_CONTRACT_VERSION,
    NormalizationConfig,
    NormalizationError,
    NormalizationReceipt,
    NormalizedDataset,
    NormalizedRow,
    normalize_dataset,
)
from patent_analysis.normalization.year import extract_year

__all__ = (
    "CLASSIFICATION_LEVELS",
    "MAX_NORMALIZATION_ROLES",
    "MAX_NORMALIZED_CONTRIBUTIONS",
    "MAX_NORMALIZED_VALUES_PER_CELL",
    "NORMALIZATION_CONTRACT_VERSION",
    "NormalizationConfig",
    "NormalizationError",
    "NormalizationReceipt",
    "NormalizedDataset",
    "NormalizedRow",
    "applicant_key",
    "derive_classification_values",
    "extract_year",
    "format_classification",
    "normalize_applicant",
    "normalize_dataset",
    "split_patent_values",
    "stable_dedupe",
)
