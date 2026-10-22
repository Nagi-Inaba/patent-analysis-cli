# 発明者の協働・技術・活動・関係先を分析する

既存の `inventor-tracking.v1` とは別に、人物IDと観測根拠を保持する<!--var:inventor_analysis_count-->10<!--/var-->種類の分析を用意しています。すべて同じPython API・CLI・local stdio MCPで分析でき、JSONとCSV／テキスト表を出力します。描画可能なmarkは、インストールした配布物の `capabilities --json` で確認してください。宣言されたmarkがあるだけではSVGは有効になりません。

## 分析を選ぶ

| 分析ID | 内容 | SVG mark（対応資産が有効な場合） |
| --- | --- | --- |
| `inventor-network.v1` | 共発明グラフ、孤立人物、全体グラフの中心性・コミュニティ | `inventor-network-svg.v1` |
| `inventor-ego-network.v1` | 指定人物から1〜3段階の共発明関係。中心性は全体グラフの値を保持 | `inventor-ego-network-svg.v1` |
| `inventor-technology.v1` | 発明者×IPC/CPC、分類構成、集中度・多様性 | `inventor-technology-svg.v1` |
| `inventor-activity.v1` | 年ごとの活動、累積単位数、未観測年と日付欠損 | `inventor-activity-svg.v1` |
| `inventor-cluster-flow.v1` | 年別協働グループと隣接年の共通メンバー | `inventor-cluster-flow-svg.v1` |
| `inventor-similarity.v1` | 技術分類の構成・件数・TF-IDFによるコサイン類似度 | `inventor-similarity-svg.v1` |
| `inventor-impact.v1` | 活動量、提供された被引用データ、比較コホート、引用充足率 | `inventor-impact-svg.v1` |
| `inventor-mobility.v1` | 出願人との観測関係、変化候補、企業イベント・個人根拠 | `inventor-mobility-svg.v1` |
| `inventor-mobility-flow.v1` | 法人／当時の企業グループ間の有向フロー | `inventor-mobility-flow-svg.v1` |
| `inventor-mobility-evidence.v1` | 変化候補の根拠・解釈・review履歴の一覧 | なし（JSON／表） |

[合成データ](../examples/inventor-analysis/patents.json)と各ID名のSpecを `examples/inventor-analysis/` に用意しています。4レコードで、共発明・孤立人物・分類変化・出願人の共記載変化・日付欠損を確認できます。引用や雇用根拠は提供していないため、サンプルの被引用数や転職の確認結果を捏造しません。

## インストールと実行

分析にはPython 3.14と `inventor` extraが必要です。MCPも利用する場合は `.[inventor,mcp]` を指定します。SVGの利用条件は従来と同じWindows x64／信頼するNode 22.23.4 x64です。JSONと表の分析にはNodeは不要です。

```powershell
# リポジトリルート。$pythonExe は利用するPython 3.14 venvの絶対パス。
& $pythonExe -m pip install ".[inventor]"
$env:PATENT_ANALYSIS_ALLOWED_ROOT = (Resolve-Path examples).Path
& $pythonExe -m patent_analysis analyze inventor-analysis/patents.json --spec inventor-analysis/inventor-network.v1.json --json
& $pythonExe -m patent_analysis analyze inventor-analysis/patents.json --spec inventor-analysis/inventor-mobility-evidence.v1.json --format csv
```

LinuxではvenvのPythonと `export PATENT_ANALYSIS_ALLOWED_ROOT="$(pwd)/examples"` を使って分析できます。SVGのプラットフォーム検査は迂回しないでください。

全10例はSpecのファイル名を差し替えて実行できます。中心人物の例は `focus: ["id", "SAMPLE-B"]`、引用分析は明示的な `snapshot_date: "2025-01-01"` を使います。実行日を引用の基準日に補完しません。

```python
from pathlib import Path
from patent_analysis.api import run_analysis

root = Path("examples").resolve(strict=True)
result = run_analysis(
    "inventor-analysis/patents.json",
    (root / "inventor-analysis/inventor-technology.v1.json").read_bytes(),
    allowed_root=root,
)
print(result["data"]["statistics"])
```

## 入力と集計単位

Specの `resolution.bindings` で `record_id` と、`inventor_ids` または `inventor_names` のどちらか一方を指定します。IDと氏名の配列順から対応を推定しません。`date`、`classification`、`applicant_ids` 等の追加必須bindingは、分析のparameter schemaで確認できます。

この分析群は通常のmulti-value正規化とは異なるraw入力契約です。合成例の人物・法人列は `"[\"SAMPLE-A\",\"SAMPLE-B\"]"` のようにJSON文字列配列を表すセルです。この契約は`inventor_ids`／`applicant_ids`／`source_ids`に適用します。氏名だけの`inventor_names`は従来の氏名用区切り規則を使います。区切り文字を含むIDを勝手に分割せず、IDの空白除去・NFKC統一もしません。CSVでも同じセル内容を用い、CSVとして必要な引用符のエスケープをしてください。表示ラベルの短縮や表示用正規化は、元の人物識別子や統計を変更しません。

- 共通母集団は `family_mode: "records"` のみです。`earliest`／`workbench` は受け付けません。
- 最初の7分析では `parameters.unit` に `records`／`publication`／`application`／`family` を選べます。レコードを代表1行へ切り捨てるのではなく、本人が記載された観測根拠を保持して同じ単位をまとめます。records以外には対応する単位IDのbindingが必要です。
- 人物と分類の `full`／`fractional`、ペアの `joint_unit_count`／`unit_pair_fractional` は別の配分設定です。使える分析にだけ指定してください。
- 期間・人物等のfilterを明示できます。人物を含むレコードを選んでも、同じレコードの共発明者は残ります。
- 氏名だけの人物は暫定識別です。同姓同名を自動で分離したり、別名を根拠なく統合したりしません。曖昧性は出力に残します。

## 補助データと根拠

任意の `parameters.auxiliary` で、同じallowed root配下のJSON bundleまたは9つのCSVを指定します。pathの推測や外部DBへの問い合わせはしません。

```json
{"auxiliary": {"format": "json", "path": "evidence.json"}}
```

JSON bundleは `version: "1.0.0"` と `tables` を持ち、`sources`、`identities`、`entities`、`entity_aliases`、`groups`、`events`、`personal_evidence`、`reviews`、`citations` の全9配列が必要です。使わない表は空配列にします。列・enum・参照条件は公開 `inventor-sidecar-v1.schema.json` とloaderで検証されます。Schemaだけでは参照整合性や時点の意味は確認できません。

CSVの場合は `format: "csv"`、`version: "1.0.0"` と、9表すべての相対pathを `tables` に明示します。配列セルはJSON配列、nullableな欠損は空欄です。

JSONには入力のbyte hashと根拠IDを保持します。MCPの応答ではlinkable provenanceのhash等を除去しますが、観測や確認に使った意味のある根拠IDは残ります。企業イベント、個人根拠、reviewは別表であり、企業買収を個人の転職根拠へ置き換えません。

## 結果の解釈

- 共発明や同じ特許上の出願人との共記載は、部署・雇用関係の証明ではありません。コミュニティも実際の組織図とは異なります。
- 活動の未観測年・日付欠損・分類欠損・引用未提供を、退職や活動停止、分類0件、被引用0件へ変換しません。recent期間への所属を証明できない単位があれば、その人物のrecent合計は `null` です。
- 引用分析は明示snapshotの提供データだけを使います。既知0、未提供、明示unknownを区別し、年・分類コホートと充足率を併記します。ファミリー内の引用数を無条件に合算しません。
- 関係先の変化候補の時期は、前の観測と次の観測の間です。実際の転職日ではありません。社名変更、買収、事業移転、特許権移転、並行関係、未観測、原因不明を区別します。
- 企業グループの対応は当時の関係を使い、現在の親会社へ過去の全観測を置き換えません。
- `inventor-mobility-flow.v1` は `axis`、`mode`、`allocation` を明示できます。`allocation: "unique_inventors"` の重複除外人数と、`"fractional_flows"` の候補イベント按分重みは異なる指標です。按分はexact分数で保存し、配分不能分も `unallocated` に残します。
- `review_bindings` は候補IDにreview ID配列を明示します。reviewを含むauxiliaryを更新して再分析しても元の特許データは変更しません。利用者のaccepted判断だけではemployment confirmedに昇格しません。

統計本体は `data.statistics`、入力充足率は `data.input_coverage`、人物識別根拠は `data.identity_evidence` にあります。M07では `data.citation_evidence` も確認してください。表は分析ごとの固定列で、`analysis_id` と `table` を付けます。

## 上限と描画

分析の基本上限は5,000レコード・5,000単位・200人物・128分類です。年次／関係先分析は30暦年以内、統計は200 KiB、公開dataは256 KiBまでです。ペア・比較・辺・補助データにも別の上限があります。上限内の件数でも根拠やIDが長ければbyte上限で拒否されます。上位だけへ黙って切り捨てません。

SVGには別の表示予算があります。統計の中心性・分母・全件根拠を図の件数へ合わせて再計算せず、表示対象外や省略分を明示します。円の面積、色、線種等の意味は各図の凡例を確認してください。JSON／表を図と併用し、配置や技術類似の表示距離を因果関係の証明として扱わないでください。

SVGは分析結果JSONを保存して `render --analysis <相対JSONファイル> --mark <上表のmark> --output <既存の絶対ディレクトリ> --node <信頼するNodeの絶対パス> --json` で生成します。結果ファイルもallowed root配下に置きます。M10にはmarkがなく、根拠一覧はJSON／表として利用します。
