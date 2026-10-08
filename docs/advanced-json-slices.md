# Advanced analysis JSON

Python API・CLI・local stdio MCPで利用できる10分析の計算仕様です。SVGの形式は[描画仕様](advanced-rendering.md)を参照してください。

## Included analyses and exact semantics

| Analysis | Calculation |
| --- | --- |
| growth-quadrant.v1 | Each explicit long/short span is split at floor midpoint; rate is (recent-previous)/previous*100. Overlapping spans count each record once in the union total. A zero denominator with positive recent count returns null/new, not an invented plotting value. |
| entry-exit.v1 | First and last observed years and total records per category. Recent activity is last_year >= maximum_eligible_year-2, using the complete eligible input before top-N. This does not establish a real-world market exit. |
| citation.v1 | Top individual records by citation count, then year and label. Repeated labels remain separate records. This is not aggregation of an applicant's total citations. |
| matrix-composition.v1 | Category membership counts for one explicit x/y cell. Shares use all category memberships in that cell before top-N; one multi-valued row can contribute to several categories. |
| new-entrants.v1 | First observed applicant year is computed over the whole supplied population. Qualifying applicants are ranked before classification filtering; within-applicant shares include all classifications before display truncation. |
| compara.v1 | A minus B count matrix on explicitly named groups. A record belonging to both contributes once to each. Same-group comparison is rejected; all zero cells are retained. |
| cooccurrence.v1 | Each unordered pair of distinct labels is counted once per record. Matrix is symmetric with zero diagonal; singleton occurrences still affect label selection. |
| collaboration-network.v1 | Only multi-member records contribute to node weights and unordered links. Select the global top pairs, then filter by top 50 nodes; expose only linked nodes. |
| uniqueness.v1 | Build item ownership across all eligible groups before top-N. Count an item as exclusive only when exactly one group owns it. Repeated records do not create extra distinct items. |
| shared-involvement.v1 | Shared means at least min_groups distinct owners. Involvement counts each qualifying record once per group, not once per shared item. |

The ten kernels consume internal normalized role-token mappings. Their CSV
wrappers reuse `prepare_records_population`, `NormalizedRow`, and the existing
population rules. CLI and API call the same registered functions.
No second CSV reader, user expression language, provider mode, or external
runtime dependency is introduced.

## Calculation rules

- Canonical role tokens, per-row deduplication and code-point tie ordering are used. Blank roles are excluded, not named
  '(blank)'. The original CSV remains unchanged.
- Citation parser accepts bounded nonnegative finite decimals up to 10^12,
  including supported English/Japanese prefixes. Negative values and ambiguous
  multi-valued citation/label roles are excluded, not summed or silently selected.
  Its parser accepts thousands commas; CSV normalization follows the role pipeline.
- New-entrant matrix uses only valid-dated records for classification counts.
  Eligibility is relative to the supplied, possibly filtered dataset, not universal novelty.
- Odd-length quadrant spans use unequal halves. Rates are count
  changes, not annualized rates, and use percentages rather than Growth's ratio.
- Compara is count-only; general numeric measures and inferred group
  selection are not implemented or advertised.
- Unique/shared item lists show at most 20 sorted items with `items_truncated`.
  Their counts and rates always use the complete underlying sets.
- No recent-publication-lag correction, prediction, or market-status verdict is
  inferred from labels or years.

## Bounds and tests

All ten reject unknown parameters, boolean integers, invalid role collisions,
non-finite JSON, and oversized labels even when those labels fall outside top-N.
Limits: 100,000 normalized records, 2,000,000 normalized role tokens,
100 values per role per row, 4096 canonical-JSON UTF-8 bytes per label,
1,000,000 expanded contributions, 100,000 tracked keys, 96 KiB result JSON.
Most output axes/groups are limited to 20; network has up to 80 pairs and 50 nodes.
Pair and Cartesian expansions are checked before their quadratic loops.

## Run from a full checkout

Use the project's existing Python environment and dependency installation.
From the repository root, set the trusted input root to an absolute path:

```powershell
$env:PATENT_ANALYSIS_ALLOWED_ROOT = (Resolve-Path examples/advanced).Path
python -m patent_analysis analyze patents.csv --spec entry-exit.json --json
python -m patent_analysis analyze patents.csv --spec growth-quadrant.json --json
python -m patent_analysis analyze patents.csv --spec uniqueness.json --json
python -m pytest tests/test_advanced_json_logic.py tests/test_advanced_json_entrypoints.py -q -p no:cacheprovider
```

All ten complete specs and a repository-owned ten-record CSV are in
`examples/advanced/`. Substitute another spec filename for another analysis.
No input data, model or network access is performed by the analysis package.
