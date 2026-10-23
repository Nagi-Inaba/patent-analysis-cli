# 分析カタログ

## 選び方

入力は利用者が用意するローカルCSVまたはJSONです。全分析をPython API・CLIで利用でき、MCP対応は下表のとおりです。利用可能なmarkと上限の機械可読な正本は`patent-analysis capabilities --json`です。

| 分析ID | 調べたいこと | spec（examples/からの相対パス） | local MCP |
| --- | --- | --- | --- |
| `ranking.v1` | 項目別の件数・数値の順位 | `basic/ranking.json` | 対応 |
| `matrix.v1` | 2軸の組み合わせ件数（`pie_role`でバブル内に構成比） | `basic/matrix.json`、円グラフ入りは`basic/matrix-pie.json` | 対応 |
| `timeline.v1` | 年ごとの系列推移 | `basic/timeline.json` | 対応 |
| `composition.v1` | 項目別の構成比 | `basic/composition.json` | 対応 |
| `growth.v1` | 指定した2年の増減 | `basic/growth.json` | 対応 |
| `concentration.v1` | 年別の集中度（HHI） | `basic/concentration.json` | 対応 |
| `lifecycle.v1` | ピーク年・固定5年窓の成長指標 | `basic/lifecycle.json` | 対応 |
| `growth-quadrant.v1` | 長期・短期の成長の組み合わせ | `advanced/growth-quadrant.json` | 対応 |
| `entry-exit.v1` | 項目の出現・活動・退出状態 | `advanced/entry-exit.json` | 対応 |
| `citation.v1` | レコードに記載された被引用数 | `advanced/citation.json` | 対応 |
| `matrix-composition.v1` | 選択した1セル内の構成比 | `advanced/matrix-composition.json` | 対応 |
| `new-entrants.v1` | 基準年以降の新規出願人と分類 | `advanced/new-entrants.json` | 対応 |
| `compara.v1` | 2グループのセル件数差 | `advanced/compara.json` | 対応 |
| `cooccurrence.v1` | 同じレコードに現れる項目の組 | `advanced/cooccurrence.json` | 対応 |
| `collaboration-network.v1` | 同じレコードに現れる主体の関係 | `advanced/collaboration-network.json` | 対応 |
| `uniqueness.v1` | グループ固有の項目 | `advanced/uniqueness.json` | 対応 |
| `shared-involvement.v1` | グループ間で共有される項目への関与 | `advanced/shared-involvement.json` | 対応 |
| `inventor-tracking.v1` | 共発明クラスタと出願人の年次変化 | `inventor-tracking/spec.json` | 対応 |

既存<!--var:shared_example_count-->17<!--/var-->例は同じ10行の`examples/advanced/patents.csv`を利用します。発明者追跡は専用の12行の`examples/inventor-tracking/patents.csv`を使います。実データや外部DBへの接続は不要です。[analysis-catalog.json](../examples/analysis-catalog.json)にはCSV・spec・mark・MCP対応・入力hash、[expected-aggregates.json](../examples/expected-aggregates.json)には期待する集計JSON本体があります。

```bash
# リポジトリルート。利用するvenvを有効化済みの場合。
export PATENT_ANALYSIS_ALLOWED_ROOT="$(pwd)/examples"
patent-analysis analyze advanced/patents.csv --spec basic/timeline.json --json
```

MCPの呼び出しには[共通手順](mcp.md)で該当specのJSONオブジェクトを渡します。

## 人物ID・根拠を保持する発明者分析

次の<!--var:inventor_analysis_count-->10<!--/var-->分析は`inventor` extraが必要です。全件local MCPに対応し、[専用の入力条件・解釈・合成例](inventor-analysis.md)があります。各Specは`examples/`からの相対パスです。

| 分析ID | 調べたいこと | spec |
| --- | --- | --- |
| `inventor-network.v1` | 共発明の全体グラフと中心性 | `inventor-analysis/inventor-network.v1.json` |
| `inventor-ego-network.v1` | 指定人物の周囲の関係 | `inventor-analysis/inventor-ego-network.v1.json` |
| `inventor-technology.v1` | 発明者別技術分類と構成 | `inventor-analysis/inventor-technology.v1.json` |
| `inventor-activity.v1` | 年次活動と未観測・日付欠損 | `inventor-analysis/inventor-activity.v1.json` |
| `inventor-cluster-flow.v1` | 協働グループの年次変化 | `inventor-analysis/inventor-cluster-flow.v1.json` |
| `inventor-similarity.v1` | 技術構成の類似度 | `inventor-analysis/inventor-similarity.v1.json` |
| `inventor-impact.v1` | 活動量と提供された引用データ | `inventor-analysis/inventor-impact.v1.json` |
| `inventor-mobility.v1` | 出願人との関係変化と企業イベント | `inventor-analysis/inventor-mobility.v1.json` |
| `inventor-mobility-flow.v1` | 法人・当時のグループ間フロー | `inventor-analysis/inventor-mobility-flow.v1.json` |
| `inventor-mobility-evidence.v1` | 変化候補の根拠・review履歴 | `inventor-analysis/inventor-mobility-evidence.v1.json` |

入力は`inventor-analysis/patents.json`です。この分析群の本体は`data.statistics`、入力充足率は`data.input_coverage`です。共通母集団の`family_mode`は`records`だけを受け付け、最初の7分析の計算単位は別途`parameters.unit`で指定します。旧来の代表1行選択と混同しないでください。根拠一覧にはSVGがなく、残る9分析も同梱の対応資産が有効な場合だけmarkを公開します。

## 結果を読むときの注意

Rankingは契約v1、その他はv2です。前者の集計本体は応答の`result`、後者は`data`です。既存<!--var:population_analysis_count-->17<!--/var-->種類のv2分析の外側の`population`は元入力の件数、`data.population`はフィルター・代表選択後の母集団を表すため、同じ意味の件数とは限りません。新しい発明者分析は上記の専用出力契約を使います。

複数値の項目は1レコードから複数の所属・組み合わせを生む場合があります。レコード数、所属件数、ペア件数、構成比の分母を混同しないでください。成長の基準年や窓はspecで明示します。ゼロ分母・欠損・上位外の扱いは各閉じた分析仕様に従います。

### マトリクスのバブルの中に円グラフを描く

`matrix.v1`の`parameters`に`pie_role`（バブルを分ける項目）を指定すると、各セルに`slices`（円グラフの区分と件数）が付き、結果の`pie`に凡例の区分が入ります。`matrix-bubble-svg.v1`ではバブルの中がその構成比になり、右に凡例が並びます。ヒートマップは円グラフを描きません。

| parameter | 意味 |
| --- | --- |
| `pie_role` | バブルを分ける項目。指定しなければ従来どおりで、結果も変わりません |
| `pie_limit` | 区分として残す上位件数。2〜8、既定5。残りは1つの「その他（上位外）」にまとめます |
| `pie_classification_level` | 分類項目を丸める粒度（`x_classification_level`と同じ値） |

- 区分は、いずれかのセルに入った行全体での出現数の順（同数は文字コード順）に決め、全セルで同じ凡例・順序・色を使います。軸と同じ順位づけです。
- 値が空の行は「(空白)」の区分になります。
- 1行が複数の値を持つとき、値ごとに数えます。区分の合計がセルの`row_count`を超えることがあります。バブルの大きさは`row_count`です。
- 円の中の順序は12時の位置から時計回りで、凡例と同じ順です。モノクロ配色では、区分を明るさの段階で区別します。

`year_range`フィルターは正規化後の値を比較します。4桁の十進数字を年として扱い、上付き数字・空欄・年として読めない値は範囲に一致しません。`effect: "exclude"`では、範囲に一致する値を持たない行が残ります。

Matrix Compositionは**選択1セル**の内訳です。全セルの構成比を一度に見るには、`matrix.v1`の`pie_role`を使います。Comparaは**count-only**です。被引用数は外部サービスから取得せず、CSVに記録された値だけを使います。

既存v2の<!--var:population_analysis_count-->17<!--/var-->分析は[ファミリー代表単位](family-population.md)を選べます。代表以外の出願人・分類・引用数を合算しないため、「ファミリー全構成員の属性集合」とは別の結果です。Rankingは従来のレコード単位を維持します。

## SVG

Windows x64 / Node 24.22.1 x64で、各分析の`render_marks`から選択します。複数markを持つのはMatrix、Timeline、Compositionです。異なる分析のmarkや任意のECharts設定は渡せません。生成結果の相対receiptとSVGのSHA-256は、配布確認artifactの`core.json`・`mcp.json`にも記録します。そこで確認する代表経路と全体CIの検証は[配布手順](release.md)で区別しています。

発明者追跡のクラスタは年内の共発明グラフの連結成分です。出願人の変化は同一人物の観測間の集合差であり、雇用・転職を判定しません。識別・欠損・上限・図の読み方は[発明者追跡](inventor-tracking.md)を参照してください。
