# 分析カタログ

## 選び方

入力は利用者が用意するローカルCSVです。全分析をPython API・CLIで利用でき、MCP対応は下表のとおりです。利用可能なmarkと上限の機械可読な正本は`patent-analysis capabilities --json`です。

| 分析ID | 調べたいこと | spec（examples/からの相対パス） | local MCP |
| --- | --- | --- | --- |
| `ranking.v1` | 項目別の件数・数値の順位 | `basic/ranking.json` | 対応 |
| `matrix.v1` | 2軸の組み合わせ件数 | `basic/matrix.json` | 対応 |
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

既存17例は同じ10行の`examples/advanced/patents.csv`を利用します。発明者追跡は専用の12行の`examples/inventor-tracking/patents.csv`を使います。実データや外部DBへの接続は不要です。[analysis-catalog.json](../examples/analysis-catalog.json)にはCSV・spec・mark・MCP対応・入力hash、[expected-aggregates.json](../examples/expected-aggregates.json)には期待する集計JSON本体があります。

```bash
# リポジトリルート。利用するvenvを有効化済みの場合。
export PATENT_ANALYSIS_ALLOWED_ROOT="$(pwd)/examples"
patent-analysis analyze advanced/patents.csv --spec basic/timeline.json --json
```

MCPの呼び出しには[共通手順](mcp.md)で該当specのJSONオブジェクトを渡します。

## 結果を読むときの注意

Rankingは契約v1、その他17分析はv2です。前者の集計本体は応答の`result`、後者は`data`です。v2の外側の`population`は元入力の件数、`data.population`はフィルター・代表選択後の母集団を表すため、同じ意味の件数とは限りません。

複数値の項目は1レコードから複数の所属・組み合わせを生む場合があります。レコード数、所属件数、ペア件数、構成比の分母を混同しないでください。成長の基準年や窓はspecで明示します。ゼロ分母・欠損・上位外の扱いは各閉じた分析仕様に従います。

`year_range`フィルターは正規化後の値を比較します。4桁の十進数字を年として扱い、上付き数字・空欄・年として読めない値は範囲に一致しません。`effect: "exclude"`では、範囲に一致する値を持たない行が残ります。

Matrix Compositionは全セルに円グラフを並べる機能ではなく**選択1セル**です。Comparaは**count-only**です。被引用数は外部サービスから取得せず、CSVに記録された値だけを使います。

v2の17分析は[ファミリー代表単位](family-population.md)を選べます。代表以外の出願人・分類・引用数を合算しないため、「ファミリー全構成員の属性集合」とは別の結果です。Rankingは従来のレコード単位を維持します。

## SVG

Windows x64 / Node 22.19.0 x64で、各分析の`render_marks`から選択します。複数markを持つのはMatrix、Timeline、Compositionです。異なる分析のmarkや任意のECharts設定は渡せません。生成結果の相対receiptとSVGのSHA-256は、配布確認artifactの`core.json`・`mcp.json`にも記録します。そこで確認する代表経路と全体CIの検証は[配布手順](release.md)で区別しています。

発明者追跡のクラスタは年内の共発明グラフの連結成分です。出願人の変化は同一人物の観測間の集合差であり、雇用・転職を判定しません。識別・欠損・上限・図の読み方は[発明者追跡](inventor-tracking.md)を参照してください。
