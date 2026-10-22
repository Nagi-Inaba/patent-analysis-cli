# Changelog

このprojectの主な変更を記録します。

## Unreleased

### Added

- `matrix.v1`に任意の`pie_role`（`pie_limit`、`pie_classification_level`）を追加。`matrix-bubble-svg.v1`のバブルの中を、その項目の構成比の円グラフにして、右に凡例を表示する。指定しない場合は結果もSVGも変わらない。例は`examples/basic/matrix-pie.json`。
- 全markで選べる配色パレット`palette`（`standard`／`colorblind`／`monochrome`／`high-contrast`）を追加。CLIは`render --palette`、MCPのrenderは`palette`。既定の`standard`は出力が変わらない。
- CSVに加え、UTF-8（先頭のUTF-8 BOM 1個は許容）の特許JSONをdataset入力として追加。単一objectとobject配列、入れ子objectのドット区切り列、scalar配列のmulti-value cell変換に対応。
- Python API、CLI、local stdio MCPから利用できる既存18種類の分析に、発明者向け10種類の分析を追加。CSV・text・JSONの集計出力に対応。
- `records`と`earliest`による明示的なファミリー代表選択。
- Matrix、Timeline、Composition、Network、Inventor Trackingなど従来の19種類の固定SVG表現に、発明者分析の9種類のマップを追加。
- `inventor-tracking.v1`による年別共発明クラスタ、分裂・合流、出願人記載の変化、未観測期間の集計。
- 発明者の共発明・人物中心の関係・技術構成・活動履歴・協働グループ変遷・技術類似・引用・関係先変化を分析。移動候補の根拠一覧はJSON／表で確認でき、出願人変更だけで転職とは断定しない。
- `selection_sets`による値・年範囲フィルターと、分析前のSpec検証。
- Apache License 2.0、公開用security reporting、再現可能な配布検証手順。
- macOS（Apple Silicon／Intel）でのCLI・MCP・SVG生成と、両アーキテクチャのCI検証を追加。

### Changed

- MCP SDKと`mcp-types`を2.2.0へ更新し、CVE-2026-59951を解消。ハッシュ付き依存ロックとCI・導入手順を同期。
- MCPの`cryptography`を検証済みの50.0.1以上へ制限。Intel Macでも安全な版のwheelを必要に応じてビルドし、binary-only解決による旧版の選択を防止。
- 形式中立の`run_analysis()`を公開し、`run_analysis_csv()`は互換APIとして維持。
- CSV decodeとcanonical hash処理を改善し、大きな入力でのピークメモリを削減。
- CLIとMCPを共通Python APIへ統一。
- renderer依存、lock、SBOM、第三者通知を同期。
- macOSのSVG公開を、同一ディレクトリで`os.link(..., follow_symlinks=False)`を使うhard-link no-overwrite方式に対応し、既存artifactを置き換えずに公開。
- 集計表のcontext出力とUnicode escapeを改善。
- バブルのSVG（`matrix-bubble-svg.v1`、`points-bubble-svg.v1`）から格子線を除去。ライフサイクル図は年をカンマなしで表示し、ステージの凡例を追加。
- `matrix-bubble-svg.v1`の件数ラベルを、既定で非表示にし、`value_labels="shown"`（CLIは`--value-labels shown`、MCPのrenderは`value_labels`）で表示できるように変更。従来はラベルを有効にしても文字が描画されなかった。
- ライフサイクル図のy軸名を軸の左側へ移し、左上の点のラベルとの重なりを解消。
- `inventor-cluster-flow-svg.v1`の年の見出し（2023など）を太字にしない。図中の数値は太字にせず、タイトルと凡例の見出しだけを太字とする。
- ヒートマップ（`cooccurrence-svg.v1`、`compara-svg.v1`、`new-entrants-svg.v1`、`inventor-technology-svg.v1`）の件数の文字色を、セルの色に合わせて暗色と白から選ぶように変更。標準配色の濃いセルで暗い文字が読めず、中間色のセルで白い文字が読めなかった。
- 散布・バブル図（`points-bubble-svg.v1`、`entry-exit-svg.v1`、`citation-svg.v1`、`growth-quadrant-svg.v1`）の点のラベルが、同じ座標の点のラベル、隣の点、軸名と重ならないように、右・下・左・上へ積む位置へ自動で移す。重ならない図の出力は変わらない。
- 散布図の年軸（`citation-svg.v1`、`entry-exit-svg.v1`）の目盛りを、桁区切りなしの整数（2018、2024など）で表示する。
- 四象限図（`growth-quadrant-svg.v1`）で値が0以下のみの場合に、軸線と軸名がゼロの位置（上・右）へ移動していた問題を解消。軸線を常に左・下へ描画し、他の散布図と同じ位置に揃える。
- ヒートマップ（`compara-svg.v1`、`cooccurrence-svg.v1`、`new-entrants-svg.v1`）のx軸カテゴリラベルは、長い項目（表示上7文字以上）がある場合のみ傾け、短いラベルは水平のまま表示する。1文字のラベルが傾いていた。
- 横棒図（`matrix-composition-svg.v1`、`uniqueness-svg.v1`、`shared-involvement-svg.v1`）の件数軸の目盛りを整数にする。件数が少ない図で「0.5件」のような半端な目盛りが出ていた。
- 発明者の活動履歴（`inventor-activity-svg.v1`、`inventor-mobility-svg.v1`）のノードラベルを、接続線がラベル文字を貫通して見えないよう、白背景の上に描画する。

### Fixed

- dataset JSON、AnalysisSpec、OperationPlanの先頭UTF-8 BOM 1個をencoding signatureとして許容する。BOM付きJSONは`input.invalid`となっていた。
- `render --help`はテキストヘルプを表示し、exit code 0とする。従来は常に`usage.invalid`だった。`--json`との併用時は従来どおり`usage.invalid`、exit code 4とする。
- トップレベル`--help`のコマンド一覧に`capabilities`を表示する。従来は実行できたがヘルプに載っていなかった。
- 発明者分析の按分値の変換を、呼び出し元のDecimal設定から独立させた。丸めモードによる結果の変化や、例外trap・指数範囲の設定による未処理例外を防ぎ、小数12桁のhalf-even丸めを維持する。

### Security

- MCPの通信JSON全体をSDKの解釈前に検証し、重複キー、過剰な入れ子、不正な数値・Unicodeを拒否。request IDをUTF-8で1,024 bytesまでに制限し、JSON-RPC envelope込みの最終応答へ256 KiB上限を適用。protocol errorから要求文字列と内部error dataを除去。

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
