# patent-analysis-cli

ローカルの特許CSVまたはJSONを、明示した列対応と条件で決定論的に集計し、JSON、CSV・テキストの集計表、固定形式のSVGとして出力するツールです。Python API・CLI・local stdio MCPは同じ計算コアを使います。自然言語の解釈や外部特許データの取得は行いません。

| 入口 | 現在の範囲 |
| --- | --- |
| Python API / CLI | 18分析。分析の選び方は[分析カタログ](docs/analysis-catalog.md) |
| local stdio MCP | 18分析・6ツール。[設定と呼び出し例](docs/mcp.md) |
| SVG | 19固定形式。Windows x64 / **Node.js 22.19.0 x64**のみ |
| 集計単位 | 17種類のv2分析で`records` / `earliest`。旧Rankingはレコード単位のみ |

Python 3.14で動作するローカル実行専用のパッケージです。入力・出力契約と安全性の境界は[SECURITY.md](SECURITY.md)、配布物の検証方法は[リリース手順](docs/release.md)を参照してください。

## インストール

**Python 3.14系（3.14以上・3.15未満）が必要**です。既存の文字処理はUnicode 16.0.0を要求するため、インストール条件も検証済みの3.14系に限定しています。SVGを使わなければNodeやnpmは不要です。依存の取得にはインストール時の通信が必要ですが、インストール後の分析処理は外部サービスを呼びません。

権限のある利用者が取得したリポジトリのルートで実行します。

### Windows / PowerShell

```powershell
py -3.14 -m venv .venv
$pythonExe = (Resolve-Path .venv\Scripts\python.exe).Path
& $pythonExe -m pip install .
& $pythonExe -m patent_analysis capabilities --json
```

### Linux

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m patent_analysis capabilities --json
```

通常利用に`[dev]`、editable install、rendererの`node_modules`は不要です。wheelからは`python -m pip install ./patent_analysis_cli-0.2.0-py3-none-any.whl`で導入できます。既存の同名versionを更新するときは、新しいvenvを使い、releaseのcommitとwheelのSHA-256を確認してください。

MCPを使う場合だけ`python -m pip install ".[mcp]"`を指定します。利用するクライアントには、そのvenvのPythonまたは`patent-analysis-mcp`の絶対パスを設定します。

## 最初の集計

すべて合成データです。既存17分析は`examples/advanced/patents.csv`を共用し、発明者追跡は専用の合成CSVを使います。[例の一覧](examples/analysis-catalog.json)がCSV・spec・期待結果との対応を管理します。

```powershell
$env:PATENT_ANALYSIS_ALLOWED_ROOT = (Resolve-Path examples).Path
& $pythonExe -m patent_analysis inspect advanced/patents.csv --json
& $pythonExe -m patent_analysis analyze advanced/patents.csv --spec basic/ranking.json --json
& $pythonExe -m patent_analysis analyze advanced/patents.csv --spec advanced/collaboration-network.json --json
```

Linuxでは`export PATENT_ANALYSIS_ALLOWED_ROOT="$(pwd)/examples"`と設定し、`$pythonExe`の代わりに`.venv/bin/python`を使います。

`inspect`は列名・件数等のメタデータだけを返し、セル値・サンプル行・絶対パスは返しません。`analyze`の結果には入力由来のラベルと集計値が含まれます。外部AIへ渡す範囲は利用者側で判断してください。元のCSV・JSONは変更しません。

### 特許JSONを入力する

拡張子`.json`のUTF-8ファイルは、提示された特許objectを1件として読みます。同じ形のobjectを配列にすると複数件を分析できます。

```json
[
  {
    "application_no": "JP2024-102312",
    "title": "潅水制御システム",
    "application_date": "2024-06-25",
    "publication_date": "2026-01-14",
    "applicants": ["株式会社クボタ"],
    "inventors": ["片桐  康之", "片岡  麻子"],
    "sections": {"abstract": "要約本文"}
  }
]
```

objectのキーが列名になります。入れ子objectは`sections.abstract`のようなドット区切り列へ展開し、`applicants`や`inventors`のscalar配列は`|`区切りのmulti-value cellとして既存の正規化へ渡します。複数objectで欠けた列は空文字になります。objectを含む配列、重複キー、NaN/Infinity、展開後に同名になるキーは拒否します。詳細な型変換と上限は[入力契約](docs/contracts.md#json-input)を参照してください。

CLIではCSVと同じコマンドを使います。

```powershell
& $pythonExe -m patent_analysis inspect patents.json --json
& $pythonExe -m patent_analysis analyze patents.json --spec basic/ranking.json --json
```

期待する集計本体は[expected-aggregates.json](examples/expected-aggregates.json)の各分析IDにあります。Rankingは応答の`result`、v2分析は`data`と比較します。同梱例の入力と条件に対応する固定結果です。

## 発明者のクラスタと出願人の変化を追う

`inventor-tracking.v1`で、年別の共発明クラスタ、クラスタの分裂・合流、発明者ごとの出願人の変化を追跡できます。名前または明示的な発明者IDを使い、未観測年と出願人欄の欠損を区別します。出願人は特許上の共記載であり、勤務先・転職を認定するものではありません。

```powershell
& $pythonExe -m patent_analysis analyze inventor-tracking/patents.csv --spec inventor-tracking/spec.json --format text
```

SVGには`inventor-tracking-svg.v1`を指定します。横軸は年、縦軸は発明者、色とC番号は同一年のクラスタです。菱形で出願人の変化、破線で未観測期間を示します。1回の追跡は20発明者・12暦年までで、上位だけに切り捨てる処理は行いません。[入力条件・集計の意味・実行例](docs/inventor-tracking.md)を参照してください。

![合成データの発明者追跡マップ。AとBのクラスタの分裂・合流、Cの出願人欠損、Dの未観測期間を表示](docs/images/inventor-tracking.svg)

## Specを事前検証する

分析前にSpecだけを検証する場合は、`validate-spec`を使います。CSVを読まず、Schemaと実装済み条件を検証します。列が実データに存在するか、実データが集計上限に収まるかは`analyze`で確認します。

```powershell
& $pythonExe -m patent_analysis validate-spec basic/growth.json --json
& $pythonExe -m patent_analysis schema growth-parameters-v1.schema.json --json
```

`validate-spec -`は標準入力に対応します。ファイル入力は`PATENT_ANALYSIS_ALLOWED_ROOT`配下が必要です。標準入力と`schema`にはroot設定は不要です。Schema名は`capabilities --json`にあるパスのファイル名を指定します。

## ファミリー代表単位で集計する

```powershell
& $pythonExe -m patent_analysis analyze family/patents.csv --spec family/composition.json --json
```

同梱の5行から4代表行を選び、出願人の所属件数はA=1、B=1、C=2になります。処理順は**フィルター → ファミリー代表選択 → 分析固有の集計**です。同じIDの属性を合算したり、IDを推定したりしません。空欄IDは個別に残します。

代表の日付を比較できる場合だけ最も早い暦日を使い、同日・不正または欠損日付の比較は元の行順で決めます。最初の日付が不明な代表を後の有効日付で置き換えません。詳細は[ファミリー仕様](docs/family-population.md)を参照してください。

## CSV・テキストの集計表を出力する

18分析すべてで`--format csv`または`--format text`を使えます。Nodeは不要です。

```powershell
& $pythonExe -m patent_analysis analyze advanced/patents.csv --spec basic/timeline.json --format csv
& $pythonExe -m patent_analysis analyze advanced/patents.csv --spec advanced/collaboration-network.json --format text
```

CSVはUTF-8でstdoutへ返し、`analysis_id`と`table`で分析・表種別を区別します。年別系列は年ごとに1行、Networkはnodesとedgesを出力します。`--json`とは併用できません。`--include-context`を付けると、Spec・母集団・警告・receiptを含む分析文書全体も添付できます。列一覧とエスケープ規則は[表出力](docs/table-export.md)を参照してください。

## WindowsでSVGを作る

信頼できるローカルのNode 22.19.0 x64と、既存の絶対パスの出力ディレクトリが必要です。同梱済みの描画資産を使うため、利用時にnpm installやビルドは行いません。

```powershell
$nodeExe = (Get-Command node.exe -ErrorAction Stop).Source
$output = Join-Path $env:TEMP ("patent-svg-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $output | Out-Null
$result = & $pythonExe -m patent_analysis analyze advanced/patents.csv --spec basic/ranking.json --json
if ($LASTEXITCODE -ne 0) { throw "Analysis failed; do not render the error response" }
$result | & $pythonExe -m patent_analysis render --analysis - --mark ranking-svg.v1 --output $output --node $nodeExe --json
```

同じ`$result`・mark・出力先で最後のコマンドを再実行すると、同一SVGを`reused`として返します。異なる内容で既存ファイルを上書きしません。成功応答の`svg`は出力先からの相対ファイル名です。

SVGは読み上げ用のタイトルと、入力行数・分析対象件数・警告件数を持ちます。数値と条件の詳細には`--include-context`付きの集計表を添えてください。すべての支援技術での操作やWCAG適合を保証するものではありません。

Linuxでは集計・JSONを利用できますが、公開SVG経路は非対応です。Nodeのバージョンやプラットフォーム検査を迂回しないでください。LifecycleのCLI描画も接続済みです。mark一覧は`capabilities --json`にあり、11分析の詳細は[SVG仕様](docs/advanced-rendering.md)にあります。

## Python API

```python
from pathlib import Path
from patent_analysis.api import run_analysis

root = Path("examples").resolve(strict=True)
result = run_analysis(
    "advanced/patents.csv",
    (root / "basic/composition.json").read_bytes(),
    allowed_root=root,
)
print(result["data"])
```

`run_analysis()`は`.csv`と`.json`を受け付けます。互換名`run_analysis_csv()`、旧Rankingの`analyze_csv()`、汎用描画入口`render_analysis_svg()`、`render_ranking_svg()`も保持しています。APIとCLIの契約・エラーは[contracts.md](docs/contracts.md)を参照してください。

## 構成と処理の流れ

アーキテクチャ図です。このリポジトリはローカルCSV・JSONの検査、集計、描画と各adapterを実装します。特許データの取得、自然言語からのSpec作成、GUI、結果の共有先の判断は利用側の役割です。

```mermaid
flowchart TB
    subgraph caller[利用側・リポジトリ外]
        collect[特許データの取得・CSVまたはJSONの準備]
        spec[人間または外部AIによるAnalysisSpec作成]
        client[ターミナル・Python利用者・MCPクライアント]
        use[SVG表示・結果の共有・業務判断]
    end
    subgraph product[patent-analysis-cli]
        adapters[CLI / optional local stdio MCP]
        api[共通Python API]
        validate[Spec検証・分析registry]
        input[許可root配下のCSV・JSON読込]
        population[列対応・正規化・フィルター・代表選択]
        analysis[分析コア：発明者追跡など18分析]
        result[JSON結果・receipt / CSV・テキスト表]
        model[固定ChartModel・内容整合性検証]
        runtime[固定Node・同梱ECharts bundle]
        svg[SVG検証・上書きしない保存・相対receipt]
    end
    collect --> input
    spec --> client
    client --> adapters --> api
    client --> api
    api --> validate --> input --> population --> analysis --> result
    result --> use
    result --> model --> runtime --> svg --> use
```

次はUMLシーケンス図です。分析結果を保存・再利用でき、SVG生成は必要なときだけ呼び出します。描画runtimeはWindows x64・Node 22.19.0に固定しています。

```mermaid
sequenceDiagram
    actor Caller as 利用者・CLI・MCP
    participant API as 公開Python API
    participant Runner as analysis_runner
    participant Input as CSV・JSON・母集団処理
    participant Kernel as 分析コア
    participant Render as ChartModel・renderer
    participant Node as 信頼済みローカルNode
    Caller->>API: run_analysis(dataset, AnalysisSpec, allowed_root)
    API->>Runner: Specを検証して分析を選択
    Runner->>Kernel: 登録済みdataset分析を呼び出す
    Kernel->>Input: 許可root内を読み、列対応・正規化・絞り込み
    Input-->>Kernel: 母集団と処理記録
    Kernel->>Kernel: 追跡・集計
    Kernel-->>Runner: 集計結果・警告
    Runner-->>API: 契約付き結果・receipt
    API-->>Caller: 分析結果JSON
    opt SVGが必要な場合
        Caller->>API: render_analysis_svg(結果, mark, output, node)
        API->>Render: Schema・集計値の整合性検証
        Render->>Node: 固定protocol・検証済みbundle
        Node-->>Render: SVG
        Render-->>API: SVG検証・安全な保存
        API-->>Caller: 相対ファイル名・hash・作成／再利用状態
    end
```

発明者追跡の論理ER図です。**入力dataset・集計JSONの関係を表すもので、永続DBやDBテーブルは実装していません。** 発明者と出願人の関係は同じ特許レコードへの記載から集計します。

```mermaid
erDiagram
    PATENT_RECORD ||--o{ INVENTOR_LISTING : lists
    INVENTOR ||--o{ INVENTOR_LISTING : appears_in
    PATENT_RECORD ||--o{ APPLICANT_LISTING : lists
    APPLICANT ||--o{ APPLICANT_LISTING : appears_in
    INVENTOR ||--o{ ANNUAL_OBSERVATION : observed_as
    ANNUAL_CLUSTER ||--|{ ANNUAL_OBSERVATION : contains
    ANNUAL_OBSERVATION ||--o{ APPLICANT_ASSOCIATION : aggregates
    APPLICANT ||--o{ APPLICANT_ASSOCIATION : co_listed_with
    ANNUAL_CLUSTER ||--o{ CLUSTER_LINK : source
    ANNUAL_CLUSTER ||--o{ CLUSTER_LINK : target
    INVENTOR ||--o{ AFFILIATION_CHANGE : compared_between_years
    PATENT_RECORD {
        int source_ordinal
        int observation_year
    }
    INVENTOR {
        string identity "名前または明示ID"
    }
    ANNUAL_OBSERVATION {
        int year
        string inventor
        string cluster_id
        int count
        int missing_applicant_rows
    }
    ANNUAL_CLUSTER {
        string cluster_id "年ごとに別のID"
        int year
        array members
    }
    APPLICANT_ASSOCIATION {
        int year
        string inventor
        string applicant
        int count
    }
    CLUSTER_LINK {
        string source
        string target
        int count "共通発明者数"
        boolean split
        boolean merge
    }
    AFFILIATION_CHANGE {
        int from_year
        int to_year
        int gap_years
        string status "changed / unchanged / unknown"
        array added_applicants
        array removed_applicants
    }
```

詳しい境界は[architecture.md](docs/architecture.md)、入力・出力の契約は[contracts.md](docs/contracts.md)を参照してください。

## 入力と安全な利用範囲

CLIのファイル入力は、信頼した起動側が指定する`PATENT_ANALYSIS_ALLOWED_ROOT`配下に限定します。dataset・specの相対パスは現在の作業ディレクトリではなく、このrootが基準です。MCPの承認済みrootは別設定で、入力・出力rootを互いに重ならない既存ディレクトリとして指定します。

CSVはカンマ区切りのUTF-8、UTF-8 BOM、UTF-16 LE/BE BOMに対応し、file size上限は300 MiBです。dataset JSONはstrict UTF-8に対応し、whole-document parseのためfile size上限は32 MiBです。両形式とも100,000行、1,000列、2,000,000セルが上限です。上限は推奨メモリ容量の保証ではありません。AnalysisSpecのJSONは最大2 MiBで、各分析に別の展開件数・文字列上限があります。

| CLI終了コード | 意味 |
| --- | --- |
| 0 | 成功 |
| 2 | 契約違反 |
| 3 | 入力・root・パス・読込エラー |
| 4 | 引数不備 |
| 5 | ローカル描画環境を利用できない |
| 6 | 出力先の競合 |

JSON出力はstdoutに1オブジェクトです。エラーを成功結果として後段へ渡さないでください。trusted-local描画はOSサンドボックスではありません。任意SQL・任意JavaScript・任意のECharts options、外部特許DB、remote MCPは提供しません。高度なWindows隔離は現在の保証に含めません。[SECURITY.md](SECURITY.md)が安全性と残余リスクの説明です。

## 開発・配布準備

```bash
python -m pip install --require-hashes -r requirements/mcp-2.0.0.lock
python -m pip install -e '.[dev]' build
python -m pytest -q -p no:cacheprovider
python -m ruff check --no-cache src tests scripts
python -m build
```

CIはWindowsとLinuxでtest、lint、renderer build、dependency auditを実行します。配布確認では別venvへwheelを非editable installし、source tree外からCLIとMCPを検証します。

## ライセンス

本体は[Apache License 2.0](LICENSE)で提供します。同梱rendererの第三者コンポーネントには、[THIRD_PARTY_NOTICES.txt](src/patent_analysis/renderer/THIRD_PARTY_NOTICES.txt)に記載した各ライセンスが適用されます。配布metadataの`License-Expression`は、本体と同梱コードを合わせた`Apache-2.0 AND MIT AND BSD-3-Clause AND 0BSD`です。

[リリース手順](docs/release.md) / [アーキテクチャ](docs/architecture.md) / [変更履歴](CHANGELOG.md) / [開発への参加](CONTRIBUTING.md)
