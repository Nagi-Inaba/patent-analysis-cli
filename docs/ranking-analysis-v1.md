# Ranking Analysis v1

## 目的

この仕様は、特許CSVのランキング集計を決定論的なPython APIとCLIから実行する最初の分析スライスを定義する。利用者は任意のローカルAIに自然言語で依頼し、AIはCSVのbounded manifestを確認して`AnalysisSpec`を作り、CLIを呼び出せる。package自身はmodel、network、cloud、外部APIを呼ばない。`inspect`はcell valueを含まないmetadataだけを返し、`analyze`はデータ由来のdimension label、集計値、count、shareを返すため、unique labelがsource cell文字列と一致する場合もある。結果を外部AIやserviceへ送るかどうかはcaller policyであり、本packageの責務外である。

## 製品境界

`patent_analysis`はCSV読込、入力上限、ranking集計、中立な`AnalysisResult`、`ExecutionReceipt`を所有する。CLIは公開Python APIを呼ぶだけのadapterとする。

OperationPlanはversion付きの説明・検証契約であり、本packageは登録済みoperationを実行しない。`analyze` が実行する契約はAnalysisSpecであり、現行の実行対象は`ranking.v1`である。package自身はmodel、network、cloud、外部APIを呼ばない。

次は実装しない。

- UI、FastAPI、ECharts、MCP、Agent Gateway。
- 自然言語から`AnalysisSpec`を生成するmodel呼出し。
- 外部特許DB、外部API、インターネット検索。
- 任意Python、任意SQL、任意shell。
- filter、SelectionSet、family単位集計、breakdown、render設定。
- timeline、matrix、composition等のranking以外の分析。

## 公開契約

package versionは`0.2.0`、分析契約versionは`1.0.0`、algorithm IDは`ranking.v1`である。

分析契約versionは`1.0.0`とし、OperationPlan契約versionとは分ける。

rankingの分析結果とhashの挙動は変わらない。`AnalysisResult`の集計値、行順、`row_kind`、`ExecutionReceipt`、`input_sha256`、`spec_sha256`、`result_sha256`は既存の契約どおりであり、overlayは表示用の別入力として扱う。

公開Python APIは次を追加する。

```python
ANALYSIS_CONTRACT_VERSION: str

def get_analysis_spec_schema() -> dict[str, object]: ...
def validate_analysis_spec(spec: object) -> dict[str, object]: ...
def get_analysis_result_schema() -> dict[str, object]: ...
def validate_analysis_result(result: object) -> dict[str, object]: ...
def inspect_csv(source: str | Path, *, allowed_root: str | Path) -> dict[str, object]: ...
def analyze_csv(source: str | Path, spec: object, *, allowed_root: str | Path) -> dict[str, object]: ...
```

`validate_analysis_spec`は検証済みのspecを返す。失敗時は`AnalysisContractError`を送出する。公開するmessage/detailsは`code`、`safe_message`、`retryable`、boundedな`details`に限定し、入力値、セル値、prompt、絶対pathを入れない。tracebackのframe localsは別の開示境界として扱う。

`inspect_csv`と`analyze_csv`の`allowed_root`はkeyword-onlyで必須であり、trusted launcherが用意した絶対pathの既存local directoryを受け取る。OperationPlanの`contract`と`validate-plan -`はこのrootを要求しないが、file-backed `validate-plan <file>`は要求する。OperationPlanとAnalysisSpecのJSON入力はfileまたはstdinのいずれもUTF-8 bytesで最大2 MiBであり、超過は`input.invalid`/exit code 3となる。

## AnalysisSpec

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

- `analysis_type`は`ranking`。
- `dimension`は空白以外の列名。
- `measure.mode`は`count`、`sum`、`average`、`max`、`min`。
- `count`では`measure.column`を`null`にする。
- `count`以外では`measure.column`を空白以外の列名にする。
- `top_n`は1以上100以下の整数。
- `include_other`はboolean。
- `multi_value_mode`は`all`または`first`。
- すべてのobjectは`additionalProperties: false`。

## Dataset入力

v1はcomma区切りCSVまたは`.json` datasetを読み取る。CSV encodingはBOMを優先して`UTF-8`、`UTF-8 with BOM`、`UTF-16 LE/BE with BOM`を受け付け、BOMのない入力はUTF-8として読む。JSONの構造と射影規則は[contracts](contracts.md#json-input)に従う。元datasetは変更しない。

入力の上限は次のとおりとする。

- file size: CSVは300 MiB、JSONは32 MiB。
- columns: 1,000。
- rows: 100,000。
- cells: 2,000,000。
- cell length: 1,000,000文字。

空のheader、重複header、CSV行ごとの列数不一致、および公開されたfile size・columns・rows・cells・cell length上限の違反は`input.invalid`として拒否する。`inspect_dataset`は列名、行数、列数、byte数、encoding等のmetadataだけを返し、file name、絶対path、sample value、cell valueを返さない。

CLIの`inspect`/`analyze`とfile-backed `validate-plan`は、trusted launcherが絶対pathの既存ローカルdirectoryとして設定した`PATENT_ANALYSIS_ALLOWED_ROOT`とverified root/pathを必須とする。相対dataset/spec/plan pathはこのrootを基準に解決し、dataset・spec・planはroot配下のregular fileだけを受け付ける。`--spec -`と`validate-plan -`のbounded stdinだけがfile-backed入力の例外である。rootまたはpathが未設定・拒否された場合は`input.invalid`、exit code 3となる。CLIにもAnalysisSpecにもrootを変更するfieldやoptionはない。OperationPlanとAnalysisSpecのJSON入力はfileまたはstdinのいずれもUTF-8 bytesで最大2 MiBであり、超過は`input.invalid`/exit code 3となる。

WindowsではUNC/device/NT namespace/ADS、remoteまたはmapped drive、SUBST、symlink/junction/mount/reparse component、identity/final-handle escapeを拒否する。component swap、hard-link、host privilegeによる残余境界は残る。このcontrolはsandboxではなく、modelがenvironment variableを変更できる、またはarbitrary shellを実行できる運用ではroot境界を迂回できる。

`multi_value_mode = all`は1セルあたり空でないraw tokenを1,000個までdedup前に扱う。`first`は最初の空でないtokenで停止する。post-dedup expanded contributionは500,000、distinct bucketは100,000までで、違反は`input.invalid`/exit code 3となる。これらのanalysis-only budgetは`inspect`には適用しない。

300 MiBはCSV、32 MiBはJSONの入力サイズ上限である。現行CSV loaderはraw bytes・decoded text・row structuresを保持し、JSON loaderはwhole documentをparseしてから同じrow structuresへ射影する。上限近くのpeak RSSは未benchmarkで、memory-safety recommendationではない。near-limit operationの前に代表データでbenchmarkする。

## Multi-value処理

`multi_value_mode = all`ではdimension cellを分割し、同一セル内の重複値を除いた各値へ行を展開する。`first`では最初の値だけを使う。空値は`(空白)`として集計する。

`DatasetInputError`の公開属性・`as_dict()`・通常の`str`/`repr`・標準形式のtracebackにはraw valueを出さない。`code`は`input.invalid`、`retryable`は`false`、`details`は`{}`、`safe_message`は固定allow-listの文言となり、cause/contextは抑止される。ただしPython tracebackのframe localsには引数や中間のraw/text/rowsが残り得るため、locals付きtracebackをAI、logging、telemetry、外部serviceへ送らない。

通常列の区切り文字は`|`、`;`、`；`、`、`、`，`、改行とする。列名がIC、IPC、CPC、FI、FTM、F-term、Fターム、サブクラス、メイングループを示す場合はcommaも区切り文字に加える。

## 数値処理

`count`は展開後の行数を数える。その他のmeasureでは、commaを除いた有限の10進数を使う。次のprefix付き引用数も数値として受け付ける。

- `被引用`、`被引用件数`、`被引用数`、`被引用回数`。
- `引用`、`引用件数`、`引用数`、`引用回数`。
- `cited by`、`citation count`、`citation`、`citations`、`forward citation`、`forward citations`。

数値でないセルはmeasure計算から除外する。bucket内に有効な数値がなければvalueは0とする。

## Ranking結果

bucketはvalue降順、count降順、label昇順で並べる。v1のlabel tie-breakはPythonのUnicode code point順とする。

各rowは次を持つ。

```json
{
  "row_kind": "dimension_value",
  "label": "A社",
  "value": 3,
  "count": 3,
  "share": 0.5
}
```

`row_kind = "dimension_value"`は実際のdimension bucket、`row_kind = "remainder"`は任意で追加される合成の最後の`その他`を示す。実データのlabel `その他`はdimension valueとしてremainderと共存できる。remainderは高々1つで最後に置き、`(row_kind, label)`の組は一意である。

shareは`top_n`適用前の全bucketを基準に計算し、丸めない。`count`は`total_count > 0`なら`count / total_count`、それ以外は0とする。`sum`は`total_value > 0`なら`value / total_value`とし、`total_value <= 0`の場合は`total_count > 0`なら`count / total_count`、それ以外は0とする。`average`、`max`、`min`は`total_count > 0`なら`count / total_count`、それ以外は0とする。`その他`にも同じ分母と計算basisを適用する。fallbackはshareの計算basisだけを変更し、valueとランキング順には影響しない。

`include_other = true`かつbucket数が`top_n`を超える場合、`その他`はtop_n外の残りの展開後ラベル寄与から再計算する。average、max、minでもbucket valueの平均や合計ではなく、必要なmeasureを元行へ再適用して残りの寄与を求める。

## AnalysisResult schema

schema fileは`analysis-result.schema.json`、IDは`urn:patent-analysis:analysis-result:1.0.0`である。`get_analysis_result_schema()`がschemaを返し、`validate_analysis_result()`が検証済み結果のdefensive copyを返す。結果はstrictな有限値だけを受け付け、dimensionとlabelはblankでない文字列、countは1以上でなければならない。semantic validationはrow_kindのenum、remainderの高々1つ・最後配置・label `その他`・dimension valueの先行、`(row_kind, label)`の一意性を検証する。

## AnalysisResultとExecutionReceipt

`analyze_csv`は次のenvelopeを返す。

```json
{
  "analysis_contract_version": "1.0.0",
  "ok": true,
  "result": {
    "analysis_type": "ranking",
    "dimension": "出願人",
    "measure": {"mode": "count", "column": null},
    "population": {"input_rows": 4, "analyzed_rows": 4},
    "rows": [],
    "warnings": []
  },
  "receipt": {
    "algorithm_id": "ranking.v1",
    "package_version": "0.2.0",
    "input_sha256": "...",
    "spec_sha256": "...",
    "result_sha256": "..."
  }
}
```

hashはUTF-8、`ensure_ascii = false`、key sort、余分な空白なしのcanonical JSONから計算する。receiptへ時刻、file name、pathを入れない。同じpackage version、同じ入力bytes、同じspecから同じresultとreceiptを返す。

`analyze_csv`の成功envelopeのトップレベルfieldは`analysis_contract_version`、`ok`、`result`、`receipt`の4つであり、`ok`は`true`である。

## CLI

次のcommandを追加する。

```powershell
patent-analysis inspect <dataset.csv|dataset.json> --json
patent-analysis analyze <dataset.csv|dataset.json> --spec <spec.json|-> --json
```

`inspect`/`analyze`とfile-backed `validate-plan`の前に、trusted launcherが絶対pathの既存local directoryを`PATENT_ANALYSIS_ALLOWED_ROOT`へ設定する。`contract`と`validate-plan -`はrootを要求しない。CLIにもspecにもrootを変更するfieldやoptionはない。root/path拒否とOperationPlan/AnalysisSpec JSON（file/stdin）の2 MiB超過は`input.invalid`/exit code 3である。

JSON modeのstdoutにはJSON以外を出さない。human modeは短い要約をstdoutへ出し、診断をstderrへ出す。

exit codeは既存の意味を維持する。

- `0`: 成功。
- `2`: AnalysisSpecまたは分析契約違反。
- `3`: CSV、spec、encoding、JSONの読込・UTF-8 decode・parse失敗または2 MiB超過、root/path拒否、CSV構造違反、公開入力上限違反、ranking analysis-only budget違反。
- `4`: CLI引数不備。

分析のerror codeは`analysis.invalid`、入力のerror codeは既存の`input.invalid`、CLI利用方法は既存の`usage.invalid`とする。

## Golden comparison

最初のgolden fixtureは、count、average、空白bucket、multi-value expansion、top N、その他再計算を、手計算したliteral expected valueで検証する。valueまたはcountを一意にし、未解決の日本語collation差をfixtureへ混ぜない。


## 表示契約

既存の`analyze_csv`成功envelopeから表示用中間契約を作る正本のflowは次のとおりである。

```text
analyze success envelope
  -> optional complete provider-neutral LabelOverlayPack
  -> build_ranking_chart_model()
  -> ChartModel + ChartModelBuildReceipt
```

package rootに追加された公開builderは`build_ranking_chart_model(analyze_success_envelope, *, overlay=None)`と`build_ranking_render_spec(*, row_count)`だけである。前者は`ChartModel`と`ChartModelBuildReceipt`を返し、後者は後続renderer向けの固定`RenderSpec`契約データを返す。`LabelOverlayPack`は全visible rowを覆う完全なprovider-neutral入力として検証される。


## 将来拡張

2本目以降の分析は`AnalysisSpec.analysis_type`のvariantと専用result fieldsを追加する。CLI commandを分析ごとに増やさず、`analyze --spec`を共通入口として維持する。
