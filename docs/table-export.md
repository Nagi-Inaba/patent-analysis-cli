# 集計表の出力

`analyze <dataset> --spec <spec.json|-> --format csv|text`は、同じ公開分析APIからCSVまたはJSON入力の集計表を作る。元datasetを変更せず、分析は1回だけ行う。Pythonでは`patent_analysis.api.run_analysis_table(source, spec_bytes, allowed_root=..., table_format="csv")`が同じ文字列を返す。互換名`run_analysis_csv()`と`analyze --json`も維持する。MCPは従来どおりJSON結果を返す。

## 表の構成

| 分析 | table / 内容 |
| --- | --- |
| Ranking | rows：項目、値、件数、比率、row_kind |
| Matrix | cells：軸index・ラベル、値、row_count |
| Timeline / Growth / Concentration | series：系列×年ごとに値とrow_count。Growthはgrowth_rate/state、Concentrationはclassification/contribution_countも含む |
| Composition / Matrix Composition | items：項目別の件数・比率 |
| Lifecycle / Growth Quadrant / Entry Exit / Citation | points：各点の集計値。入れ子の指標は`long.rate_percent`のような列名にする |
| New Entrants | applicants / cells：新規出願人と分類別集計 |
| Compara | cells：A/B件数と差分 |
| Cooccurrence | label_counts / pairs / cells：項目件数、ペア、対称行列 |
| Collaboration Network | nodes / edges：ノードと接続の件数 |
| Uniqueness / Shared Involvement | groups：指標、item一覧、items_truncated |

CSVは1つの矩形表で、先頭列は`analysis_id,table`。複数tableの列を結合し、そのtableに存在しない列を空欄にする。ヘッダーは空母集団でも同じ。結果に含まれる順序と数値を維持し、top-N外や空の行列セルを勝手に補完しない。系列だけは既存の年配列に従って行へ展開する。

既定の出力は集計値だけを含む。条件や由来も保存する場合は`--include-context`を付ける。Python APIでは`include_context=True`を指定する。`items_truncated`がtrueの一覧は元の分析結果と同じく省略を含む。

## 条件・警告を含める

```powershell
patent-analysis analyze advanced/patents.csv --spec basic/composition.json --format csv --include-context
patent-analysis analyze advanced/patents.csv --spec basic/composition.json --format text --include-context
```

この指定では、検証済みSpec全体と同じ1回の計算から得た分析文書全体を末尾に添付する。フィルター、選択集合、集計期間、母集団、警告、receipt、hashを含み、元CSVの行は添付しない。source由来のラベルや列名は含まれるため、共有範囲はcallerが管理する。

CSVには`context_path,context_value`列と`table=context`行を追加する。`context_path`はJSON PointerをJSON文字列として符号化したセル、`context_value`はJSON値である。各セルを`json.loads()`して復元する。空のPointerは`{"spec": ..., "analysis": ...}`のrootを表し、objectとarrayは空のcontainer行の後に子を順番に出力する。Pointerの`~0`と`~1`はそれぞれ`~`と`/`を表す。この構造は空container、null、boolean、数値、文字列の型を維持する。集計行のcontext列とcontext行の集計列は空欄になる。

textには`[context]`節を追加し、PointerとJSON値を1行ずつ表示する。JSON値の日本語はそのまま読める形にし、制御文字・書式制御文字・Unicode行区切りはescapeする。値中の`|`は`\u007c`にして表の区切りと区別するため、値は引き続き`json.loads()`で復元できる。CSVのcontext値とPointerは従来どおりASCII escapeしたJSONで、数式を始める文字や制御文字がそのまま文字列セルの先頭に出ない。contextにも完成出力16 MiBの上限を適用し、超過時は部分出力しない。`--include-context`は`--format csv|text`との併用が必要である。

## 文字・数値と上限

- stdoutはUTF-8、CSV行末はLF。CSVのカンマ・引用符・改行は標準の引用規則で出力する。表計算ソフトへ読み込む際もUTF-8を指定する。
- CSVの文字列が空白を除いた先頭で`= + - @`（全角も含む）から始まる場合、または先頭がtab/CR/LFの場合は、数式として解釈されないよう先頭へ`'`を付ける。この接頭辞は集計値を変えず、CSVの文字列表現だけに適用する。数値の負数には付けない。元の文字列が必要な機械処理にはJSONを使う。
- 配列はセル内のコンパクトJSON。CSV・textとも配列内の制御文字・書式制御文字・Unicode行区切りをescapeし、textでは`|`を`\u007c`にする。日本語を読める形で保持し、`json.loads()`で元の配列を復元できる。booleanは`true/false`。定義されない数値はCSVで空欄、textで`null`。ゼロへ置き換えない。
- tab/CR/LF以外の制御文字とUnicode書式制御文字は、端末で実行されないよう`\u001b`等の表記へ変換する。
- textは`[table]`見出しと` | `区切り。引用符・バックスラッシュ・制御文字をJSON風に、区切り文字を`\|`へエスケープする。文字列セルとcontextのPointerでもUnicode行区切りをescapeして1行表示を保つ。空表は`(no rows)`。元の正規化が改行を複数値へ分割する場合、その既存挙動を維持する。
- 完成出力はUTF-8で16 MiBまで。超過は`analysis.invalid`／終了コード2とし、途中までの表をstdoutへ出さない。既存の入力・分析上限も適用する。CLIの表モードの診断はstderrへ出し、`--json`との併用は引数エラーとする。

`inventor-tracking.v1`は`inventors`、`observations`、`co_inventions`、`affiliations`、`clusters`、`cluster_links`、`affiliation_changes`の7表を出力する。配列のメンバー・出願人をJSONセルとして保持し、意味と列は[発明者追跡](inventor-tracking.md)を参照する。

## 新しい発明者分析の表

人物IDを扱う<!--var:inventor_analysis_count-->10<!--/var-->分析もCSV・textに対応する。各分析の`data.statistics`から次の固定表を出力し、全分析に`identity_evidence`を付加する。`inventor-impact.v1`には`citation_evidence`も付加する。意味と入力条件は[発明者分析](inventor-analysis.md)を参照する。

| 分析ID | table |
| --- | --- |
| `inventor-network.v1` | `nodes`、`edges`、`unplottable` |
| `inventor-ego-network.v1` | `nodes`、`edges`、`unplottable`、`hop_membership`、`partners` |
| `inventor-technology.v1` | `profiles`、`cells`、`classifications` |
| `inventor-activity.v1` | `people`、`calendar`、`observations` |
| `inventor-cluster-flow.v1` | `nodes`、`links`、`unplottable` |
| `inventor-similarity.v1` | `features`、`similarities`、`co_inventor_edges` |
| `inventor-impact.v1` | `people`、`units`、`cohorts` |
| `inventor-mobility.v1` / `inventor-mobility-evidence.v1` | `candidates`、`associations`、`episodes`、`unbound_reviews`、`corporate_changes` |
| `inventor-mobility-flow.v1` | 上記の関係変化5表と`flows`、`unallocated` |

固定列は[実装の表定義](../src/patent_analysis/analyses/_inventor_common.py)で管理する。ここでも`--include-context`で分析文書全体を添付できる。既定の表は統計・根拠の選択した項目を表すため、分析文書の全fieldが自動で列になるわけではない。
