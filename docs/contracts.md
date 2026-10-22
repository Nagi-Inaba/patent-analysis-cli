# Contracts

## Version

package versionは `0.2.0`、OperationPlan契約versionは `1.0.0` である。AnalysisSpecは旧Rankingの `1.0.0` と、他の<!--var:v2_analysis_count-->27<!--/var-->分析の `2.0.0` を区別する。分析契約versionはOperationPlan契約versionとは別に管理する。OperationPlanはversion付きの説明・検証契約であり、本packageは登録済み<!--var:operation_count-->15<!--/var--> operationを実行しない。`analyze` が実行する契約はAnalysisSpecであり、現行の実行対象は<!--var:analysis_count-->28<!--/var-->分析である。

Schema IDは `urn:patent-analysis:operation-plan:1.0.0` とする。OperationPlan v1本体へversion fieldは追加しない。

既存のOperationPlan `additionalProperties: false` 契約と互換性の意味は維持する。

## Public Python API

OperationPlan API:

- `CONTRACT_VERSION`
- `describe_contract()`
- `get_operation_plan_cases()`
- `get_operation_schema()`
- `list_operations()`
- `validate_operation_plan(plan)`
- `OperationContractError`

Legacy Ranking analysis API（v1）:

- `ANALYSIS_CONTRACT_VERSION`
- `get_analysis_spec_schema()`
- `validate_analysis_spec(spec)`
- `validate_analysis_spec_bytes(spec_bytes)`
- `inspect_csv(source, *, allowed_root)`
- `analyze_csv(source, spec, *, allowed_root)`
- `AnalysisContractError`
- `DatasetInputError`
- `get_analysis_result_schema()`
- `validate_analysis_result(result)`

`inspect_csv` と `analyze_csv` の `allowed_root` はkeyword-onlyで必須である。trusted launcherが用意した絶対pathの既存local directoryを渡す。OperationPlanの `contract` と `validate-plan -` はこのrootを要求しないが、file-backed `validate-plan <file>` は要求する。

AnalysisSpecとOperationPlanのJSON読み込みはUTF-8で行い、先頭のUTF-8 BOM 1個はencoding signatureとして無視する（cell値など、埋め込まれた値の中のBOMは無視しない）。

`validate_analysis_spec` は検証済みのspecを返す。`AnalysisContractError` は `code`、`safe_message`、`retryable`、boundedな `details` を持つ。公開するmessage/detailsには入力値、CSVセル値、prompt、秘密情報、絶対pathを入れない。tracebackのframe localsは別の開示境界として扱う。

`inspect_csv` は列名、行数、列数、byte数、encoding、SHA-256だけを返す。`analyze_csv` の成功envelopeのトップレベルfieldは `analysis_contract_version`、`ok`、`result`、`receipt` の4つであり、`ok` は `true` である。

### 共通分析API（v1/v2の振り分け）

公開`patent_analysis.api`の`describe_capabilities()`、`get_public_schema(schema_name)`、
`validate_analysis_spec_bytes(spec_bytes)`、`inspect_dataset(source, *, allowed_root)`、
`run_analysis(source, spec_bytes, *, allowed_root)`を使用する。
`run_analysis`は`.csv` / `.json`とAnalysisSpecの版を判別し、legacy Rankingまたはnative v2 coreへ渡す。`run_analysis_csv`は後方互換名として残り、同じく両形式を受け付ける。
Rankingは成功envelopeの`result`、v2は中立な分析documentの`data`が集計本体である。
v2で指定した列が存在しない、または列対応が確定できない場合、`run_analysis`は
`DatasetInputError`を返す。CLIの`analyze --json`は既存の`input.invalid`と終了コード3を返す。
`inspect <dataset> --profile column-alias.v2 --json`で列名・候補を確認し、specの`resolution.bindings`を修正する。
`render_analysis_svg(analysis_document, *, mark, output_directory, node_executable=None, value_labels=None, palette=None)`は
対応する固定rendererへ振り分ける。各分析の専用schemaと上限はcapabilitiesを参照する。
`value_labels`（CLIでは`render --value-labels`）は`hidden`（既定）または`shown`で、`matrix-bubble-svg.v1`のバブルに件数を表示するかを選ぶ。他のmarkに指定すると`render.invalid`で拒否する。`hidden`はrender specに含めないため、既定の出力は変わらない。

図中の文字は、すべてのpaletteで次のように描く。

- ヒートマップの件数は、そのセルの色に対して読みやすい方（暗色または白）にする。中間の明るさのセルでは、どちらも約4.2:1が上限になる。
- 点のラベル（ライフサイクル、初回・最終観測年、被引用数、長期・短期成長四象限）は、既定で点の上に置く。他のラベル、他の点、軸名や目盛りと重なる場合だけ、右、下、左、または上へ積んだ位置に移す。重ならない図の出力は変わらない。座標が同じ点が多く、どの位置も埋まる場合は、最も重なりが少ない位置に置く。
- 図中の数値は太字にしない。太字はタイトルと凡例の見出しだけである。

### 配色パレット

`palette`（CLIでは`render --palette`、MCP renderの`palette`）は全markに共通で、次の4種から選ぶ。
未指定または`standard`は従来の配色で、render specに含めないため出力は変わらない。
`standard`以外は、`standard`と同じ図に色・線種・マーカーだけを変える。
色そのものはcallerが指定できず、固定の組だけを使う。

| palette | 用途 | 内容 |
| --- | --- | --- |
| `standard`（既定） | 通常の画面・資料 | 従来のteal基調 |
| `colorblind` | 色覚の多様性への配慮 | Okabe-Ito配色。値の大小は青の濃淡、正負は橙と青 |
| `monochrome` | 白黒印刷 | 黒から灰の4段階。折れ線は線種とマーカーで識別 |
| `high-contrast` | 低解像度・投影 | 全色が白に対して4.5:1以上。線を太くする |

`standard`以外では、折れ線を系列ごとに実線・破線・点線・一点鎖線とし、マーカーも円・四角・三角・菱形で変える。
色だけに頼らずに系列を識別するためである。
棒と円グラフの区画には不透明の輪郭を付ける。

色は白背景に対するWCAGのコントラスト比と、1型・2型・3型色覚の模擬での色差（CIEDE2000）で検証した。
`colorblind`は全8色の色差が10.9以上、`high-contrast`は全8色が4.5:1以上かつ色差9.1以上である。
`standard`は2型色覚で`#c2410c`と`#a16207`の色差が0.9しかなく、区別しにくい。

制約は次のとおり。

- `monochrome`で区別できるカテゴリは4つまでで、5つ目以降は同じ灰を繰り返す。凡例とラベルを併用する。
- advanced系の図は、色だけを一括で置き換える。形や線種は図ごとの既存の表現を使う。
- 丸いマーカー（バブル・散布図）は輪郭を付けない。拡大変換で描かれるため、輪郭の線幅がSVG規則の小数桁数を超える。
- 符号付きのヒートマップは、`monochrome`では色で正負を区別できない。数値ラベルの符号で読む。

## Local stdio MCP adapter

MCP adapterはoptionalな `mcp==2.2.0` dependencyとして提供する統合済み実装である。MCP 2.x stdioを使い、公開 `patent_analysis.api`（特にbyte-firstの `validate_analysis_spec_bytes()`、`inspect_dataset()`、`run_analysis_csv()`互換入口、`render_analysis_svg()`）を直接呼ぶ。dataset pathはCSV・JSONの両方を受け付ける。CLI subprocess、remote transport、network、hosted transfer、認証は使わない。

toolの引数objectはclosedで、`additionalProperties: false` とし、次のexact key setだけを受け付ける。文字列は空でない値で、`spec` はobjectである。renderはanalysis objectではなくhandleを受け取る。

| tool | exact argument shape |
| --- | --- |
| `patent_analysis.capabilities` | `{}` |
| `patent_analysis.schema` | `{"schema_name": string}` |
| `patent_analysis.inspect` | `{"input_root_id": string, "path": string}` |
| `patent_analysis.validate_spec` | `{"spec": object}` |
| `patent_analysis.analyze` | `{"input_root_id": string, "path": string, "spec": object}` |
| `patent_analysis.render` | `{"output_root_id": string, "output_path": string, "analysis_handle": string, "mark": string}`に加え、任意の`"value_labels": "hidden" \| "shown"`と`"palette": "standard" \| "colorblind" \| "monochrome" \| "high-contrast"` |

adapterのbyte境界は次のとおりである。

- stdio wire message: 最大2 MiB。
- canonical tool arguments: 最大1 MiB。
- serialized MCP final response: 最大256 KiB。

失敗はcaller-controlled textを含めない固定safe envelopeにする。公開されるcode/messageは次のallow-listに限定する。

| code | fixed message |
| --- | --- |
| `input.invalid` | `Tool input is invalid` |
| `input.too_large` | `Tool input is too large` |
| `schema.unknown` | `Public schema is unavailable` |
| `analysis.unknown` | `Analysis is unavailable` |
| `response.too_large` | `Tool response is too large` |
| `renderer.unavailable` | `Trusted local renderer is unavailable` |
| `output.conflict` | `Render output conflicts with an existing artifact` |
| `internal.failed` | `Internal MCP adapter failure` |

MCP公開対象はanalysis registryの `mcp_public=true` から導出し、現在は<!--var:mcp_analysis_count-->28<!--/var-->分析と対応する固定mark・公開schemaだけである。詳細な一覧は[分析カタログ](analysis-catalog.md)に記載する。非公開analysisは実行前に `analysis.unknown` として拒否する。

rootはserver起動時の `--input-root <root_id>=<absolute-local-directory>` と `--output-root <root_id>=<absolute-local-directory>` で承認する。各rootは既存のlocal directoryで、reparse componentを含まず、input/outputのroot IDは異なり、directoryは互いにdisjoint（同一・包含なし）でなければならない。toolの `path` / `output_path` は相対pathだけを受け付け、`..`、drive/UNC/device path、絶対path、reparse pathを拒否する。入力はroot配下のverified regular file、出力はroot配下のdirectoryに限定する。

`inspect` はraw rowやsampleを返さない。`analyze` はcore receiptと`*_sha256`を除いたaggregate結果に、process-localで推測困難な`render_handle`を付ける。serverはfull analysis documentを最大4件だけmemoryに保持し、5件目で最古のhandleを失効させる。`render`はcaller指定のanalysis objectを受け取らず、このhandleで同じprocess内の検証済みdocumentを参照する。handleは永続化せず、server再起動後は無効である。

`analyze` とrender関連の結果にはsource由来labelや集計値が含まれ得るため、外部AI、logging、telemetry、serviceへどの結果を渡すかはcallerが管理する。

### 表示builder、renderer、schema

package rootから公開する表示・render APIは次のとおりである。

- `build_ranking_chart_model(analyze_success_envelope, *, overlay=None)`：任意の完全なprovider-neutral `LabelOverlayPack`を検証し、`ChartModel`と`ChartModelBuildReceipt`を返す。
- `build_ranking_render_spec(*, row_count)`：固定`RenderSpec`契約データを返す。
- `render_ranking_svg(analysis_document, *, overlay_document=None, output_directory, node_executable=None)`：bounded JSON bytesを既存builderとpackaged rendererでSVGへ変換し、relative receiptを返す。
- `RenderError`：5組の固定code/messageだけを公開するfactory-only例外。

表示契約の4つのschema IDと役割は次のとおりである。

| 契約 | schema ID | 役割 |
| --- | --- | --- |
| `LabelOverlayPack` | `urn:patent-analysis:label-overlay-pack:1.0.0` | 分析結果へ結合する表示ラベルとprovenance |
| `ChartModel` | `urn:patent-analysis:chart-model:1.0.0` | renderer-neutralな表示モデル |
| `ChartModelBuildReceipt` | `urn:patent-analysis:chart-model-build-receipt:1.0.0` | canonical model bytesとhashの由来 |
| `RenderSpec` | `urn:patent-analysis:render-spec:1.0.0` | trusted-local rendererが使う固定描画条件 |

上記4契約のschema getter、validator、および`RenderContractError`は内部module interfaceであり、package rootの公開APIではない。`analyze`成功envelopeから`ChartModel`への正本のflowは次のとおりである。

```text
analyze success envelope
  -> optional complete provider-neutral LabelOverlayPack
  -> build_ranking_chart_model()
  -> ChartModel + ChartModelBuildReceipt
```

`ChartModel`と`RenderSpec`のgrapheme処理は`regex==2026.4.4`、Unicode data 16.0.0へ固定する。rendererはpackaged ECharts 6.1.0 bundleとNode 22.23.4 exactを使用する。

Rankingのrender success receiptは`render_contract_version`、`ok`、`status`、`artifact_id`、`svg`、`svg_sha256`、`renderer_build_digest`のexact 7 fieldsを持つ。`svg`は`ranking-svg-<artifact_id>.svg`というrelative filenameで、`status`は`created`または`reused`である。absolute path、username、environment、raw input、stderrは含めない。

## AnalysisSpec v1

v1はrankingだけを受け付ける。

```json
{
  "analysis_type": "ranking",
  "dimension": "出願人",
  "measure": {
    "mode": "count",
    "column": null
  },
  "top_n": 10,
  "include_other": true,
  "multi_value_mode": "all"
}
```

規則は次のとおり。

- `analysis_type` は `ranking`。
- `dimension` は空白以外の列名。
- `measure.mode` は `count`、`sum`、`average`、`max`、`min`。
- `count` では `measure.column` を `null` にする。
- `count` 以外では `measure.column` を空白以外の列名にする。
- `top_n` は1以上100以下の整数。
- `include_other` はboolean。
- `multi_value_mode` は `all` または `first`。
- すべてのobjectは `additionalProperties: false`。

`dimension` と、count以外の `measure.column` は、入力datasetの列名と完全一致する値を指定する。

`all` はdimension cellを分割し、同一セル内の重複値を除いて行を展開する。`first` は最初の値だけを使う。空値は `(空白)` として集計する。

## CSV Input

comma区切りCSVを読み取る。encodingはBOMを優先して `UTF-8`、`UTF-8 with BOM`、`UTF-16 LE/BE with BOM` を受け付ける。BOMのない入力はUTF-8として読む。元CSVは変更しない。

CSV入力の上限は次のとおりである。

- file size: 300 MiB
- columns: 1,000
- rows: 100,000
- cells: 2,000,000
- cell length: 1,000,000文字

空のheader、重複header、行ごとの列数不一致、および公開されたfile size・columns・rows・cells・cell length上限の違反は `input.invalid` として拒否する。`inspect_csv` はfile name、絶対path、sample value、cell valueを返さない。

## JSON Input

拡張子が大文字小文字を問わず`.json`の入力だけをdataset JSONとして扱う。UTF-8 JSONで、先頭のUTF-8 BOM 1個はencoding signatureとして無視する。top-levelは1件のobject、または1件以上のobjectからなる配列とする。元JSONは変更しない。

各objectを1行へ変換する規則は次のとおりである。

- top-level keyは列名とする。複数行の列は最初に出現した順のunionとし、欠けた列は空文字にする。
- 入れ子objectは`sections.abstract`のようなドット区切り列へ再帰的に展開する。空objectは`{}`というcellにする。
- stringはそのまま、`null`は空文字、booleanと有限numberはcanonical JSON表現の文字列にする。
- scalarだけの配列は各要素を上記規則で文字列化し、`|`で連結する。空配列は空文字にする。objectまたは配列を要素に持つ配列は拒否する。
- 展開後に列名が衝突するobject、空のtop-level object、duplicate key、NaN/Infinity、不正UTF-8、64階層超のobjectを拒否する。

JSON入力の上限はfile size 32 MiB、columns 1,000、rows 100,000、展開後の矩形cells 2,000,000、cell length 1,000,000文字である。JSONは全体をbounded bytesとして読み、strict parse後に既存のimmutable `DatasetV2`へ変換する。`inspect_dataset`は列名・件数等のmetadataだけを返し、raw rowやcell valueを返さない。

## Access Control

CLIの `inspect` / `analyze` / `render` とfile-backed `validate-plan` は、trusted launcherが設定した `PATENT_ANALYSIS_ALLOWED_ROOT` とverified root/pathを必須とする。renderのfile-backed analysis/overlayもroot配下のregular fileだけを受け付ける。analysisは16 MiB、overlayは4 MiBで、`--analysis -`のbounded stdinを使えるがoverlayと同時にstdinにはできない。outputとNodeはabsolute local non-reparse pathに限定する。

WindowsではUNC/device/NT namespace/ADS、remoteまたはmapped drive、SUBST、symlink/junction/mount/reparse component、identity/final-handle escapeを拒否する。component swap、hard-link、host privilegeによる残余境界は残る。このcontrolはsandboxではなく、modelがenvironment variableを変更できる、またはarbitrary shellを実行できる運用ではroot境界を迂回できる。

`DatasetInputError` の公開属性・`as_dict()`・通常の `str` / `repr`・標準形式のtracebackにはraw valueを出さない。`code` は `input.invalid`、`retryable` は `false`、`details` は `{}`、`safe_message` は固定allow-listの文言となり、cause/contextは抑止される。ただしPython tracebackのframe localsには引数や中間のraw/text/rowsが残り得るため、locals付きtracebackをAI、logging、telemetry、外部serviceへ送らない。

## Analysis-only Budgets And Memory Boundary

`multi_value_mode = all` は1セルあたり空でないraw tokenを1,000個までdedup前に扱う。`first` は最初の空でないtokenで停止する。post-dedup expanded contributionは500,000、distinct bucketは100,000までで、違反は `input.invalid` / exit code 3となる。これらのbudgetはranking analysisだけに適用し、`inspect` は影響を受けない。

300 MiBはCSV入力サイズの上限であり、loaderはverified raw bytesとrow structuresを保持し、文字列を段階的にdecodeする。上限付近の合成データを使う実測と再実行方法は[performance.md](performance.md)を参照する。実データ・分析条件ごとの必要メモリ量は保証しないため、near-limit operationの前に代表データでbenchmarkする。

## Ranking Result And Receipt

bucketはvalue降順、count降順、label昇順で並べる。labelのtie-breakはPythonのUnicode code point順とする。

各ranking rowは `row_kind`、`label`、`value`、`count`、`share` を持つ。`row_kind = "dimension_value"` は実際のdimension bucket、`row_kind = "remainder"` は任意で追加される合成の最後の `その他` を示す。実データのlabel `その他` はdimension valueとしてremainderと共存できる。remainderは高々1つで最後に置き、`(row_kind, label)` の組は一意である。

`share` は `top_n` 適用前の全bucketを基準に計算し、丸めない。計算basisは、`count` では `count / total_count`、`sum` では `total_value > 0` のときだけ `value / total_value`、それ以外は `count / total_count`、`average`・`max`・`min` では `count / total_count` である。`total_count` が0のときは0とし、`sum` の `total_value <= 0` fallbackも同じ規則に従う。`その他`にも同じ分母と計算basisを適用する。fallbackはshareの計算basisだけを変更し、valueとランキング順には影響しない。

`include_other = true` かつbucket数が `top_n` を超える場合、`その他` はtop_n外の残りの展開後ラベル寄与から再計算する。`average`、`max`、`min`でもbucket valueの平均や合計ではなく、必要なmeasureを元行へ再適用して残りの寄与を求める。

`count` は展開後の行数を数える。その他のmeasureではcommaを除いた有限の10進数を使い、数値でないセルは計算から除外する。measure計算に使える数値がbucket内にない場合、valueは0とする。

`analyze_csv` のreceiptには `algorithm_id: "ranking.v1"`、package version、入力・spec・resultのSHA-256を含める。hashはUTF-8、`ensure_ascii = false`、key sort、余分な空白なしのcanonical JSONから計算し、時刻、file name、pathを含めない。同じpackage version、同じ入力bytes、同じspecから同じresultとreceiptを返す。

## AnalysisResult Schema And Validation

schema fileは `analysis-result.schema.json`、IDは `urn:patent-analysis:analysis-result:1.0.0` である。`get_analysis_result_schema()` がschemaを返し、`validate_analysis_result()` が検証済み結果のdefensive copyを返す。

結果はstrictな有限値だけを受け付ける。dimensionとlabelはblankでない文字列、countは1以上でなければならない。semantic validationは、`row_kind` のenum、remainderの高々1つ・最後配置・label `その他`・dimension valueの先行、`(row_kind, label)` の一意性を検証する。

## Error Codes

| Code | 意味 |
| --- | --- |
| `contract.invalid` | OperationPlanのSchemaまたはplan横断制約への違反 |
| `operation.unknown` | 未登録operation |
| `operation.incompatible_render` | analysis typeとrender markの非互換 |
| `analysis.invalid` | AnalysisSpecまたは分析契約への違反 |
| `input.invalid` | root/path拒否、OperationPlanまたはAnalysisSpec JSON（file/stdin）の読込・UTF-8 decode・parse失敗または2 MiB超過、CSV encoding/構造/公開上限違反、ranking analysis-only budget違反 |
| `usage.invalid` | CLI引数の不備 |
| `render.invalid` | parsed analysis/overlay/model/spec契約またはrenderer schema違反 |
| `renderer.unavailable` | Node path/runtime、process、timeout、pipe、protocolの失敗 |
| `output.conflict` | output pathまたはno-overwrite publicationの失敗 |

## Exit Codes

| Exit code | 意味 |
| --- | --- |
| 0 | 成功 |
| 2 | AnalysisSpecまたは分析契約違反。既存のOperationPlan検証ではOperationPlan契約違反 |
| 3 | root/path拒否、OperationPlanまたはAnalysisSpec JSON（file/stdin）の読込・UTF-8 decode・parse失敗または2 MiB超過、CSV encoding/構造/公開上限違反、ranking analysis-only budget違反、または既存CLI入力の読込失敗 |
| 4 | CLI引数不備 |
| 5 | trusted local rendererを利用できない |
| 6 | render outputが既存artifactまたはpublication境界と競合 |

JSON modeのstdoutにはJSON以外を出力しない。human modeは短い要約をstdoutへ出し、診断をstderrへ出す。`--json` と `-h` / `--help` の併用も `usage.invalid`、exit code 4とする。`-h` / `--help` 単独ではコマンドのテキストヘルプを表示し、exit code 0とする（`render`も同じ）。

## Privacy And Non-goals

source CSVはローカルに留まり、read-onlyで扱う。package自身はmodel、network、cloud、外部特許DB、外部API、インターネット検索、任意Python、任意SQL、任意shellを呼ばない。`inspect` はcell valueを含まないmetadataだけを返す。`analyze` はデータ由来のdimension label、集計値、count、shareを返し、unique labelがsource cell文字列と一致する場合もある。結果を外部AIやserviceへ送るかどうかはcaller policyであり、本packageの責務外である。UI、remote MCP、遠隔実行はこのpackageの提供範囲外である。local stdio adapterはoptionalなthin adapterとしてこの契約に従う。

AnalysisSpec 1.0.0は旧Rankingを維持し、AnalysisSpec 2.0.0は他の<!--var:v2_analysis_count-->27<!--/var-->分析を提供する。利用可能なID・schema・markは`capabilities --json`と[分析カタログ](analysis-catalog.md)を参照する。

`validate-spec <file|-> --json`は公開Python APIの`validate_analysis_spec_bytes()`を使い、CSVを開かずにSchemaと実行条件を検証する。成功応答は`valid`、`analysis_id`、`spec_variant`を持つ。年範囲の逆転、必要な列割り当ての欠落・重複、同一roleを許さない分析パラメータを実行前に拒否する。Schemaの語彙だけでは実行可能性を保証しない。実データの列の存在・集計上限は`analyze`時に検査する。契約違反は`analysis.invalid`／終了コード2、読込・parse失敗は`input.invalid`／終了コード3。ファイル入力はtrusted root配下、標準入力はroot不要で、2 MiB上限は共通。

<!--var:population_analysis_count-->17<!--/var--> native v2分析の`population.filters`は`exact`、`one_of`、`year`、`year_range`、`outside_year_range`に対応する。年は1800〜2199の整数、範囲は両端を含む。正規化後の4桁の十進年を判定し、単年は同じ始年・終年の範囲と等価となる。`outside_year_range`は範囲内判定の否定なので、欠損年・無効年も含む。各filterの`effect: exclude`はその判定を反転する。

`selection_sets`は`dimension_role`の値が`values`のいずれかに一致する行を選ぶ。`source_date_role`・`start_year`・`end_year`を併記した場合は、その行の年範囲も満たす必要がある。これは行の条件であり、期間内に登場する主体の全期間の行を選ぶ指定ではない。`mode: exclude`は値と任意の年範囲を合わせた条件全体を反転する。値の集合内はOR、filtersとselection_setsの間はAND。同じdimensionの選択集合を重複させない。全条件で絞り込んだ後に`earliest`の代表行を選ぶ。

filtersとselection_setsの合計は64件以下、各値集合は空でない異なる文字列を1000件以下とする。分析・filter・選択dimension・選択日付で正規化する異なるroleの合計も64以下とする。選択用dimensionと日付のroleにも列割り当てが必要。列名は元CSVのheaderと一致させ、異なる必要roleに同じ列を割り当てない。各分析が使わない明示bindingsは無視する。これらの条件はCLI、公開Python API、local stdio MCPで共通となる。

例えば、`group`列のAを2021〜2022年の行だけに絞る指定は次のとおり。

```json
{"filters": [], "selection_sets": [{"dimension_role": "group", "mode": "include", "values": ["A"], "source_date_role": "year", "start_year": 2021, "end_year": 2022}], "family_mode": "records"}
```

`schema <filename> --json`は`get_public_schema()`の閉じた名前一覧から取得し、`schema_name`と`schema`を返す。root不要で、パスやURLは解決しない。不明な名前は`analysis.invalid`／終了コード2。成功時は`--json`を省略してもJSONを返す。

Matrix・Timeline・Composition・Growth・Concentration・Lifecycleの分析固有の上限超過は、内部例外を露出せず`analysis.invalid`／終了コード2を返す。CSV自体の入力上限と既存Rankingの上限は従来どおり`input.invalid`を返す。

v2の母集団は`family_mode=records|earliest`を選択できる。`earliest`は`family_role`が必須、`date_role`は任意。フィルター後の明示IDから代表を選び、family結果だけに`family_selection`を付加する。元入力件数と選択後件数を混同しない。詳細は[ファミリー仕様](family-population.md)に記載する。既存records結果にはこのフィールドを追加しない。

local MCPはregistryの公開対象<!--var:mcp_analysis_count-->28<!--/var-->分析を扱う。起動と呼び出し形式は[MCPガイド](mcp.md)を参照する。`verify`・`report`という新しい公開コマンドは追加しない。

trusted-local v1はWindows x64またはmacOS arm64/x86_64で、callerが選択した対応アーキテクチャのNode.js 22.23.4 exactを完全に信頼する。Linuxでは集計・JSONを利用できるが、公開SVG経路は提供しない。sandbox、Authenticode、AppContainer、Job Object、private namespace、WCAG適合、advanced Python SVG policy全体の再検証を主張しない。最終SVGは`role="img"`、`aria-labelledby`、`aria-describedby`と、検証済みmodelに由来するtext-onlyのtitle/descを持つ。表示用label、overlay、分析結果label、SVGはcaller-controlled sensitive outputであり、package自身は外部へ送信しない。`run_analysis_table(..., include_context=True)`と`analyze --format csv|text --include-context`はSpec・分析文書全体を添付する。詳細は[表出力](table-export.md)を参照する。

## Compatibility

patch releaseではaccepted payload、rejected payload、error codeを変えない。

minor releaseではoptional fieldまたはcapabilityで判別できるoperationを追加できる。AnalysisSpecのvariantを追加する場合も、OperationPlan契約versionの意味を変更しない。

必須field、既存型、既存operationの削除、既存error codeの変更はmajor releaseとする。
