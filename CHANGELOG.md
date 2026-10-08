# Changelog

このprojectの主な変更を記録します。

## Unreleased

### Added

- CSVに加え、strict UTF-8の特許JSONをdataset入力として追加。単一objectとobject配列、入れ子objectのドット区切り列、scalar配列のmulti-value cell変換に対応。
- Python API、CLI、local stdio MCPから利用できる18種類の分析と、CSV・text・JSONの集計出力。
- `records`と`earliest`による明示的なファミリー代表選択。
- Matrix、Timeline、Composition、Network、Inventor Trackingなど19種類の固定SVG表現。
- `inventor-tracking.v1`による年別共発明クラスタ、分裂・合流、出願人記載の変化、未観測期間の集計。
- `selection_sets`による値・年範囲フィルターと、分析前のSpec検証。
- Apache License 2.0、公開用security reporting、再現可能な配布検証手順。

### Changed

- 形式中立の`run_analysis()`を公開し、`run_analysis_csv()`は互換APIとして維持。
- CSV decodeとcanonical hash処理を改善し、大きな入力でのピークメモリを削減。
- CLIとMCPを共通Python APIへ統一。
- renderer依存、lock、SBOM、第三者通知を同期。
- 集計表のcontext出力とUnicode escapeを改善。

### Security

- file-backed入力を承認済みroot配下のverified regular fileへ制限。
- JSONのduplicate key、NaN／Infinity、不正UTF-8、過剰なdepth・node・string・file sizeを拒否。
- CLI、MCP、rendererの入力・応答・実行時間へ固定上限を適用。
- rendererを固定Node.js、固定bundle、固定argv・environment、SVG allow-listへ限定。
- error contractからcell value、絶対path、内部例外情報を除外。
- wheelのclean install、dependency audit、Git履歴・配布物のsecret scanをCIへ追加。

## 0.1.0

- version付きOperationPlan、AnalysisSpec、AnalysisResult、ExecutionReceiptの初期契約。
- boundedなローカルCSV inspectionと`ranking.v1`分析。
- Python APIと`patent-analysis` CLI。
