# Advanced SVG presentations — packaged resources and acceptance

## Scope and current boundary

The eleven advanced analyses share one fixed advanced renderer family.
The calculation kernels, public API/CLI/MCP routes and supplied-result relationship
checks are connected. The package includes the verified gzip bundle, bootstrap,
manifest and candidate pins, plus the generated `ADVANCED_BUILD` activation record.
All eleven fixed advanced marks are enabled. The public renderer supports Windows x64
and macOS arm64/x86_64 with exact Node.js 24.22.1 for the matching architecture.
Linux aggregation and JSON remain supported, while the public SVG route remains unsupported.

Packaged resources and activation remain separate concepts. `--stage-only`
regenerates resources without changing the activation module; the candidate pin
file is not runtime activation authority. Resource, raw-bundle and schema hashes
are verified before use. Missing or altered resources fail closed. There is no
runtime download, compilation or fallback to another renderer.

## Fixed presentations

| Analysis | Fixed mark | Meaning |
| --- | --- | --- |
| growth-quadrant.v1 | growth-quadrant-svg.v1 | Long/short rates; undefined rates remain unplottable. |
| entry-exit.v1 | entry-exit-svg.v1 | First/last observed year and recent activity, not inferred market exit. |
| citation.v1 | citation-svg.v1 | Record-level year/citations; repeated display labels remain separate points. |
| matrix-composition.v1 | matrix-composition-svg.v1 | Selected-cell composition with the full membership denominator. |
| new-entrants.v1 | new-entrants-svg.v1 | New-to-population applicants and classification counts. |
| compara.v1 | compara-svg.v1 | Signed A-minus-B record counts, with every axis pair represented. |
| cooccurrence.v1 | cooccurrence-svg.v1 | Symmetric zero-diagonal matrix checked against pair and label counts. |
| collaboration-network.v1 | collaboration-network-svg.v1 | Joint counts with deterministic circle positions. |
| uniqueness.v1 | uniqueness-svg.v1 | Exclusive items using full-population ownership. |
| shared-involvement.v1 | shared-involvement-svg.v1 | Shared items and once-per-record involvement. |
| inventor-tracking.v1 | inventor-tracking-svg.v1 | Annual inventor lanes; year-local clusters, applicant changes and observation gaps. |

Selected-cell bars show one cell only; the all-cell pie is `matrix.v1` with `pie_role`,
drawn by `matrix-bubble-svg.v1`. Compara remains
count-only. No arbitrary chart options, executable input or adapter-specific aggregation are
introduced.

## Resource staging

The complete four-resource set is tracked alongside its generated activation
module. An explicit build reproduces those committed bytes.

Use the renderer workspace's declared dependencies and exact Node.js 24.22.1 for the
matching architecture.
From `renderer/`, run:

```text
npm ci
node scripts/build-advanced-bundle.mjs --stage-only
```

Staging creates the gzip bundle, fixed bootstrap, manifest and candidate pin JSON
under `src/patent_analysis/renderer/`. Repeating the staging build must reproduce
identical bytes and digests. The existing activation file and legacy renderer
assets must remain unchanged. Unknown command-line arguments are errors, not
requests to perform an activation build.

After generating the assets, the wheel includes them through the existing `renderer/*.js`,
`renderer/*.json` and `renderer/*.gz` package-data rules. Verification must inspect
the built wheel and execute the generated self-contained bundle through its fixed
bootstrap; source-only ECharts tests do not prove packaged-resource behavior.

From the repository root, the optional build-workspace tests verify staged
resource hashes and reject invalid frames, altered bundles and incompatible specs.
They do not change activation or the public platform guard. Successful rendering
of every presentation is covered by renderer tests and native Windows/macOS E2E below:

```text
python -m pytest -q -rs -p no:cacheprovider tests/test_advanced_asset_staging.py tests/test_advanced_staged_protocol.py
```

These artifact-dependent tests skip on a checkout without the complete staged
resource set. Their successful collection or skip is not evidence that the
generated resources were verified. In the explicit build verification, all
artifact-dependent cases must execute.

## Windows/macOS acceptance, not merely a successful build

An explicit build without `--stage-only` retains the existing activation behavior.
Use that mode only in an isolated acceptance checkout before running the Windows/macOS
public-entrypoint tests. Do not interpret local generated pins as permission to
merge or release an unverified renderer.

On Windows x64 or macOS arm64/x86_64 with exact Node.js 24.22.1 for the matching
architecture and Python >=3.14,<3.15, run the normal suite from the repository root.
It already includes the native SVG cases:

```text
python -m pytest -q -rs -p no:cacheprovider
```

For a focused rendering change, run only the existing E2E file instead of
repeating the whole suite:

```text
python -m pytest -q -rs -p no:cacheprovider tests/test_advanced_svg_end_to_end.py
```

CI runs the full Python suite once on each OS, including `macos-15` (arm64) and
`macos-15-intel`. On Windows, it checks that the suite executed tests and contains
no skipped cases, using that same run's JUnit report. macOS permits skips only for
Windows-specific tests in `tests/test_access.py`; all native SVG tests execute.
The exact checkout, resource verification,
regenerated-byte equality and wheel-content checks remain in CI.

The native Windows/macOS suite compares API/CLI
SVGs for all eleven analyses using both explicit and omitted CLI marks, and compares
MCP-handler output with the public API. It checks created/reused receipts, exact
SVG bytes and artifact identity, absence of extra artifacts, and unchanged input
CSV/specification bytes. The MCP cases exercise the real handlers and renderer,
not the full SDK/stdio transport.

**Skipped tests are not acceptance.** Confirm the host, the selected Node version
and architecture, and that the isolated build produced activation pins before
running. The acceptance record must report actual executions and skips. Linux
bootstrap tests do not bypass the public Windows/macOS guard and are not native
Windows/macOS E2E.

## Preserved implementation constraints

The family uses exact ECharts 6.1.0, the existing framed trusted-local launcher,
SVG allow-list and content-addressed no-overwrite/reuse publication. The build
starts from the hash-verified points bootstrap; it does not modify legacy assets.
Public rendering supports Windows x64 and macOS arm64/x86_64 with matching exact
Node.js 24.22.1; Linux public SVG remains unsupported.

Compressed and raw bundle hashes are verified. Expansion is bounded to 4 MiB;
trailing/concatenated streams and invalid UTF-8 are rejected. Other existing limits
include a 256 KiB model, 16 KiB spec/schema, 64 KiB bootstrap and 8 MiB SVG. Runtime
and canonical-wire checks, safe errors, fixed input/output roots and MCP handle
limits remain in force. Input contradictions are rejected, not silently corrected;
top subsets do not acquire a new denominator.
