# 入力の事前診断とRanking v2

## データとSpecを照合する

`validate-spec`に`--dataset`を追加すると、Specの検証に加え、列対応・欠損件数・日付の不正件数・発明者ID配列と、共通母集団の件数を確認します。

```powershell
& $pythonExe -m patent_analysis validate-spec basic/ranking-v2.json --dataset advanced/patents.csv --json
```

入力とSpecは`PATENT_ANALYSIS_ALLOWED_ROOT`配下に置きます。`--dataset`を省略した従来のSpec単体検証は変わりません。Pythonでは`api.preflight_analysis(source, spec_bytes, allowed_root=...)`、MCPでは`patent_analysis.validate_spec`に`input_root_id`と`path`を両方指定します。

応答の`population`は次の件数です。セル値、サンプル行、絶対パスは返しません。入力を書き換えず、一度読み込んだ特許データを使用します。

```text
input_rows -> matched_rows -> selected_rows
              filters        family representatives
filtered_rows = input_rows - matched_rows
collapsed_rows = matched_rows - selected_rows
```

`roles`に列対応の成否、欠損・不正件数、`issues`に固定エラーコードを返します。数値の検査対象は旧Rankingの数値列とv2の`measure_role`で、検査したロールには`numeric_checked: true`を返します。列の不足や発明者の入力不整合では`checks_passed: false`となり、CLIは終了コード3です。許容される欠損や年抽出の失敗は件数として報告します。入力形式・アクセス違反、Spec違反は従来のエラー契約で拒否します。

事前診断は分析固有の適格性判定・計算量上限・集計・描画を実行しません。`analysis_eligibility_checked: false`を返すため、`checks_passed: true`でも分析全体の成功を保証しません。新しい発明者分析では指定された補助データとID対応も検証します。

## JSONの発明者IDを配列で渡す

新しい10種類の発明者分析で`parameters.id_array_format: "native"`を指定すると、明示的にbindingした`inventor_ids`・`applicant_ids`・`source_ids`のJSON配列を受け取れます。

```json
{"record_id":"P1","inventors":["A|B"," A "],"applicants":["ORG-1"]}
```

上の`inventors`を`inventor_ids`へbindingした場合、`A|B`と` A `は2つの別IDです。IDを区切り記号で再分割せず、空白除去・文字種統一もしません。配列は最大64件の文字列のみで、数値・入れ子配列・objectは拒否します。従来のJSON配列を表す文字列セルも引き続き受け取れます。

既定値は`encoded`で、従来の入力契約を維持します。CSVは従来どおり文字列セルで渡します。指定したID列以外のJSON配列や`inventor-tracking.v1`は従来の処理のままです。

## 共通母集団を使って順位を付ける

`ranking.v2`はv2 Specを使い、列対応・正規化・filters・selection_sets・`family_mode`を他の分析と共有します。[サンプルSpec](../examples/basic/ranking-v2.json)を用意しています。

`parameters.role`に集計対象を指定します。`measure`は`count`（既定）・`sum`・`average`・`max`・`min`で、数値集計には`measure_role`が必要です。`top_n`は1〜100（既定10）、`include_other`は既定true、`multi_value_mode`は`all`（既定）または`first`です。

処理順は共通の正規化・絞り込み・代表選択の後に、ランキングの所属件数を展開します。構成比の分母は上位表示前の全体です。数値は他のv2分析と同じく、正規化された値のうち最初の有限数値を採用します。空白、データ由来の「その他」、表示外をまとめた「その他」を区別します。

外側の`population`は元入力・選択済み行・除外行、`data.population`は選択済み行と展開後の所属件数です。JSON・CSV／テキスト表・`ranking-svg.v1`のSVGに対応します。SVGの母集団表示は選択済み行と所属件数で、描画ハッシュは外側の母集団・ファミリー選択情報を含むv2結果全体に結び付きます。従来の`ranking.v1`のSpec・集計・ハッシュは変更しません。

## 描画環境を診断する

```powershell
& $pythonExe -m patent_analysis capabilities --check-runtime --node 'C:\Program Files\nodejs\node.exe' --json
```

`runtime`に対応OS、同梱描画資産5系統の整合性、選択されたNodeのバージョンとアーキテクチャを返します。Nodeは描画と同じ解決・起動経路を使い、24.22.1 exactを要求します。不適合では終了コード5です。`--node`は`--check-runtime`と併用します。通常の`capabilities`はプロセスを起動しません。

Pythonは`api.diagnose_renderer(node_executable=...)`、MCPは`patent_analysis.capabilities`の`check_runtime: true`を使います。MCPの結果キーは`renderer_runtime`で、サーバー設定のNodeを検査します。実行ファイルのパスや標準出力・標準エラーの内容は公開しません。

この診断はNodeの信頼性審査や実際のSVG生成の代替ではありません。`available: true`は環境と資産の検査通過を表します。別のNodeを自動インストールしたり、PATHを書き換えたりしません。

`node.version_mismatch`なら、信頼する対応版Nodeを`--node`で明示してください。診断通過後も対象データで実際のSVG生成を確認します。問題を共有する場合は固定コードと必要版・検出版で切り分け、生のstdout/stderrや実行ファイルの絶対パスを共有する必要はありません。
