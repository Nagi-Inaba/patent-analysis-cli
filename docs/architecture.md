# Architecture

## Product Boundary

`patent-analysis-cli` は、移植可能なOperationPlan・AnalysisSpec契約、ローカルCSV・JSON入力、<!--var:analysis_count-->28<!--/var-->分析、Python API、CLI adapter、およびoptionalなlocal stdio MCP adapterを所有する。

Python API・CLI・local stdio MCPは同じ計算コアを利用する。`.json`入力は単一objectまたはobject配列を決定論的に文字列行へ射影し、CSVと同じimmutable `DatasetV2`、列対応、正規化、母集団処理、分析コアへ渡す。静的SVG rendererは固定bundleを信頼したローカルNode processで実行する。

## Local stdio MCP

local stdio MCPの統合済み実装は、MCP 2.0のoptional dependencyを使う薄いlocal stdio adapterである。入力rootと出力rootは起動時に承認し、互いにdisjointなrootとして固定する。adapterは分析・描画の意味処理を所有せず、公開Python APIへ渡す。

```text
MCP 2.0 stdio
  -> bounded transport
  -> pure handlers
  -> public patent_analysis.api
  -> existing core
```

MCP adapterは `patent_analysis` の公開APIを直接呼び、CLIを呼ばず、CLI subprocessも起動しない。remote transport、network、hosted executionはこのadapterの範囲外である。<!--var:mcp_tool_count-->6<!--/var-->つのclosed toolの引数、公開analysis、rootおよびbyte境界は [contracts](contracts.md) に定める。

`analyze`は公開coreのfull documentをprocess memoryへ最大4件保持する一方、分析responseではreceiptと安定SHA-256を除外し、ランダムな`render_handle`だけを付加する。`render`はこのhandleで同一process内の検証済みdocumentを参照する。描画responseには相対filenameと、artifact再利用を確認するための決定論的な`artifact_id`、`svg_sha256`、`renderer_build_digest`が含まれる。

## 構成

現在の実装は、OperationPlan契約、boundedなローカルCSV・JSON検査、<!--var:analysis_count-->28<!--/var-->分析、<!--var:population_analysis_count-->17<!--/var--> native v2分析のファミリー代表選択、および<!--var:mark_count-->28<!--/var-->固定renderer markを含む。以下の構成図は旧Ranking経路の代表例であり、全module一覧ではない。OperationPlanはversion付きの説明・検証契約であり、本packageは登録済み<!--var:operation_count-->15<!--/var--> operationを実行しない。`analyze` が実行する契約はAnalysisSpecである。

```text
src/patent_analysis/
  __init__.py
  contracts.py             # OperationPlan契約
  analysis_contracts.py    # AnalysisSpec契約
  access.py                # allowed_rootとWindows path access control
  errors.py                # sanitized DatasetInputError
  data.py                  # CSV読込、上限、inspect_csv
  dataset_v2.py            # CSV・JSONからimmutable DatasetV2への変換
  analysis.py              # ranking集計、AnalysisResult、ExecutionReceipt
  cli.py                   # contract/validate-plan/inspect/analyzeのadapter
  _render_canonical.py     # canonical JSON bytesとhash
  _render_text.py          # 固定grapheme/text処理
  _render_contracts.py     # 内部schema/semantic validator
  chart_model.py           # 2つの公開builder
  render_errors.py         # 固定safe RenderError
  local_renderer.py        # trusted-local Node subprocess launcher
  rendering.py             # bounded parse、既存builder、SVG publication
  schemas/
    label-overlay-pack.schema.json
    chart-model.schema.json
    chart-model-build-receipt.schema.json
    render-spec.schema.json
    render-contract-cases.json
```

`data.py` はBOM優先のCSV読込と入力上限を提供し、`dataset_v2.py`はCSVまたはUTF-8 JSON（先頭のUTF-8 BOM 1個は許容）をbounded manifestとimmutable rowsへ変換する。`access.py` はtrusted `allowed_root`、regular file、opened-handle identityを検証する。`analysis.py` はrankingの中立な結果を返し、ECharts optionは返さない。CLIは公開Python APIを呼ぶだけで、分析ロジックを持たない。

処理の境界は次のとおりである。

1. `inspect_dataset` が列名、行数、列数、byte数、encoding等のmetadataだけを返す。
2. ローカルAIまたは人間がbounded manifestから `AnalysisSpec` を作り、`validate_analysis_spec` で検証する。自然言語からspecを作るmodel呼出しは本packageの責務ではない。
3. `run_analysis` がローカルCSV・JSONへ選択された分析を適用し、決定論的な結果とreceiptを返す。

`OperationPlan` はversion付きの説明・検証契約であり、本packageは登録済みoperationを実行しない。`AnalysisSpec` が `analyze` で実行される分析契約である。

### 有効化済みの表示・render契約境界

render処理は、検証済みの分析結果をclosed chart modelへ変換し、固定表示契約とpackaged rendererからSVGを作る。provider-neutral `LabelOverlayPack`はrankingだけが任意で受け付ける。

```text
validated analysis result
  -> ranking / matrix / categorical / points / advanced chart-model builder
  -> ChartModel + ChartModelBuildReceipt
  -> fixed RenderSpec + PARSVG01 frame
  -> trusted local Node 22.23.4 + packaged ECharts 6.1.0
  -> normalized SVG + fixed text-only accessibility metadata
  -> final SVG + relative receipt
```

package rootは既存builderに加え、`render_ranking_svg(...)`、`render_analysis_svg(...)`、`RenderError`を公開する。Matrix、Series、Compositionはcanonical bytes、renderer resources、frame/response protocolを再利用し、analysisの意味を複製しない。

`render`はWindows x64またはmacOS arm64/x86_64で、対応アーキテクチャのNode.js 22.23.4 exactを使う。Linuxでは集計・JSONを利用できるが、公開SVG経路は提供しない。analysis 16 MiB、overlay 4 MiB、stdout 12 MiB、stderr 64 KiB、cooperative childのwall 10秒を上限とする。Node path、output directory、file-backed inputsは既存local/non-reparse boundaryを通す。artifactは同一directoryのown tempをflush/fsync/closeし、Windowsでは`os.rename`をno-replace commit pointとして維持する。macOSでは同一directory内で`os.link(..., follow_symlinks=False)`を使って完全なbytesを既存のwinnerを置き換えずにatomically公開し、その後に自分のtemporary nameをunlinkする。同一bytesだけを`reused`とし、異なる既存fileとのconflictでは既存fileを保持して上書きしない。10秒timeoutはmalicious Node/descendantへのcontainmentではない。parent APIはbest-effort kill、pipe close、bounded wait/joinで復帰するが、trusted executableとdescendantの終了は保証しない。

## Trusted-local Renderer Boundary

CLI rendererは固定ChartModelとRenderSpecだけを入力とし、HTML、対話機能、caller指定のECharts option、theme、formatter、JavaScriptを受け取らない。

```text
optional package-external AI or human
  -> AnalysisSpec
  -> trusted local launcher
  -> analyze
  -> optional provider-neutral overlay（省略可能）
  -> render_analysis_svg()
  -> trusted local Node/ECharts SSR
  -> same-directory no-overwrite SVG publication
  -> relative RenderReceipt
```

自然言語からAnalysisSpecを作る処理はoptionalなpackage外部AIまたは人間が所有する。trusted local launcherだけがanalyze/renderを実行し、trusted rootと相対receiptを結合する。本packageは自然言語を解釈せず、model、network、cloud、外部APIを呼ばず、analysis、overlay、receipt、artifact、label、pathをAI/serviceへ送らない。

public Python APIは `render_ranking_svg(analysis_document: bytes, *, overlay_document: bytes | None = None, output_directory: str | Path, node_executable: str | Path | None = None) -> dict[str, object]` と公開 `RenderError` である。CLIは`--analysis`、任意の`--overlay`、`--output`、任意の`--node`、必須`--json`を受け付ける。

runtime dependencyはwheel内のverified self-contained bundleと固定bootstrapだけである。ECharts 6.1.0を含むexact dependencyを許可するのはrenderer build workspaceだけとし、Python core/public adapterはEChartsをimportしない。runtimeはnpm、`node_modules`、CDN、network、path importを使わない。

trusted-local v1はWindows x64またはmacOS arm64/x86_64で、対応アーキテクチャのNode.js 22.23.4 exactを使う。選択したNode executableはcallerが完全に信頼するsoftwareであり、sandbox、Authenticode pinning、AppContainer、Job Object、private namespace、handle-relative publicationを保証しない。

Pythonは正規化済みSVGへ固定ARIA参照とtext-onlyのtitle/descを加え、その最終bytesからhashとrelative receiptを作る。titleは検証済みchart modelに従い、descは入力行数・分析対象件数・警告件数と集計表への案内を含む。table APIの`include_context=True`はSpec・分析文書全体をJSON Pointer/value行で添付する。trusted-local v1はWCAG適合やadvanced Python SVG policy全体の再検証を主張しない。

## Access Control

CLIの `inspect` / `analyze` / `render` とfile-backed `validate-plan` は、trusted launcherが絶対pathの既存ローカルdirectoryとして設定した `PATENT_ANALYSIS_ALLOWED_ROOT` とverified root/pathを必須とする。相対dataset/spec/plan/analysis/overlay pathはこのrootを基準に解決する。`--spec -`、`validate-plan -`、`render --analysis -`だけがfile-backed入力の例外である。

Python APIの `inspect_dataset(source, *, allowed_root)` と `run_analysis(source, spec_bytes, *, allowed_root)` も、絶対pathの既存local directoryをkeyword-onlyで受け取る。互換APIの`inspect_csv`、`analyze_csv`、`run_analysis_csv`は維持する。OperationPlanの `contract` と `validate-plan -` はこのrootを要求しないが、file-backed `validate-plan <file>` は要求する。OperationPlanとAnalysisSpecのJSON入力はfileまたはstdinのいずれもUTF-8 bytes（先頭のUTF-8 BOM 1個は許容）で最大2 MiBであり、超過は `input.invalid` / exit code 3となる。

WindowsではUNC/device/NT namespace/ADS、remoteまたはmapped drive、SUBST、symlink/junction/mount/reparse component、identity/final-handle escapeを拒否する。component swap、hard-link、host privilegeによる残余境界は残る。このcontrolはsandboxではなく、modelがenvironment variableを変更できる、またはarbitrary shellを実行できる運用ではroot境界を迂回できる。

`DatasetInputError` は公開属性・`as_dict()`・通常の `str` / `repr`・標準形式のtracebackにraw valueを出さない。`code` は `input.invalid`、`retryable` は `false`、`details` は `{}`、`safe_message` は固定allow-listの文言となり、cause/contextは抑止される。ただしPython tracebackのframe localsには引数や中間のraw/text/rowsが残り得るため、locals付きtracebackをAI、logging、telemetry、外部serviceへ送らない。

## Limits And Locality

comma区切りCSVは`UTF-8`、`UTF-8 with BOM`、`UTF-16 LE/BE with BOM`を受け付け、file size上限は300 MiBである。`.json`はUTF-8（先頭のUTF-8 BOM 1個は許容）の単一objectまたはobject配列を受け付け、file size上限は32 MiBである。両形式ともcolumns 1,000、rows 100,000、cells 2,000,000、cell length 1,000,000文字を上限とする。JSONの具体的な射影規則は[contracts](contracts.md#json-input)に定める。

元datasetはread-onlyで扱う。`inspect_dataset` はsample value、cell value、file name、絶対pathを返さず、package自身はmodel、network、cloud、外部APIを呼ばない。`run_analysis` はデータ由来のdimension label、集計値、count、shareを返し、unique labelがsource cell文字列と一致する場合もある。結果を外部AIやserviceへ送るかどうかはcaller policyであり、本packageの責務外である。

`all` のanalysis-only budgetは1セルあたり空でないraw token 1,000個（dedup前）、post-dedup expanded contribution 500,000、distinct bucket 100,000である。`first` は最初の空でないtokenで停止する。違反は `input.invalid` / exit code 3で、`inspect` には適用しない。

300 MiBはCSV入力サイズの上限であり、loaderはverified raw bytesとrow structuresを保持し、文字列を段階的にdecodeする。JSONは32 MiB以内のverified raw bytesを全体parseしてから行へ射影する。上限付近の合成CSVを使う実測と再実行方法は[performance.md](performance.md)を参照する。実データ・分析条件ごとの必要メモリ量は保証しないため、near-limit operationの前に代表データでbenchmarkする。

## 提供範囲

現在は<!--var:analysis_count-->28<!--/var-->分析、v2の<!--var:population_analysis_count-->17<!--/var-->分析に対する明示的ファミリー代表選択、<!--var:mcp_analysis_count-->28<!--/var-->分析のlocal MCP、<!--var:mark_count-->28<!--/var-->固定SVG markを提供する。列対応・正規化 → フィルター → 任意の代表選択 → 集計という共通経路をAPI/CLI/MCPで使う。`verify`、`report`という新しい公開コマンド、remote MCP、遠隔実行は追加しない。CLIは`analyze --spec`を共通入口として維持する。

分析と対応範囲は[分析カタログ](analysis-catalog.md)、母集団は[ファミリー仕様](family-population.md)、配布されたwheelの境界確認は[配布手順](release.md)を参照する。

各分析は保存済みの期待結果と比較して検証する。未実装機能の利用可能性や提供時期はこの文書では約束しない。
