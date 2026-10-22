# ファミリー代表単位の集計

`family_mode: "earliest"`は、CSVに明示された同じファミリーIDから代表1行を選びます。
ファミリーを推定する機能でも、全構成員の出願人・分類・引用数を合算する機能でもありません。
<!--var:population_analysis_count-->17<!--/var-->種類のnative v2分析で共通の母集団処理を使います。凍結済みの旧`ranking.v1`は対象外です。
local MCPでは既に公開対象のv2分析だけを利用でき、公開分析の一覧自体は増やしません。

## 選択のルール

処理順は、列対応・既存の正規化 → 指定フィルター → ファミリー代表選択 → 分析固有の適格性判定・集計です。
フィルターに適合するメンバーの中から代表を選びます。選択した代表の分析対象列が空欄でも、
後のメンバーに差し替えて結果を補完しません。

ファミリーIDは元CSVの1セルを文字列として扱い、前後の空白だけを取り除きます。
区切り記号で分割せず、大文字小文字も同一視しません。ID空欄の行はそれぞれ独立して残します。
フィルターや分析に同じ列を使った場合の値の扱いは、従来の正規化規則のままです。

`family_role`は必須で、列対応が解決できなければエラーです。`date_role`は省略できます。
指定日付は元CSVの`YYYY-MM-DD`または`YYYY/MM/DD`を実在する暦日として比較します。
元の行順に走査し、現在の代表と候補の両日付が有効な場合だけ早い日付を選びます。
同日、どちらかの日付が不正・欠損、または`date_role`省略時は元の行順で決定します。
したがって最初のメンバーの日付が不明なら、後の有効日付のメンバーで置換しません。
出力のファミリー順は初出順を維持します。日付列を年別分析にも指定しても、代表選択では
月日を失わず、既存の年正規化は変更しません。

## 実行例

リポジトリのルートで、許可ルートを`examples/family`の絶対パスに設定します。

```powershell
$env:PATENT_ANALYSIS_ALLOWED_ROOT = (Resolve-Path examples/family).Path
patent-analysis analyze patents.csv --spec composition.json --json
```

同梱CSVの5行から4代表行を選択し、出願人件数はA=1、B=1、C=2になります。
`population.family_mode`を`records`にして`family_role`と`date_role`を削除すると、従来どおり
5行を集計し、A=2、B=1、C=2になります。既存records結果には新しいフィールドを付加しません。

ファミリー結果の`family_selection`には、選択方式・役割名と次の件数を記録します。

- `matched_rows`: フィルター通過行数。
- `representative_rows`: ID空欄の独立行も含む代表選択後の行数。
- `collapsed_rows`: 同じIDにより除いた行数。matched = representative + collapsed。
- `unidentified_rows`: 代表選択後に残るID空欄行数。

外側の`population`は従来の入力・分析・除外件数を維持します。したがって除外件数には
フィルター、重複メンバー、分析対象列の欠損などが含まれます。代表選択の記録にはファミリーIDや元の行を
含めません。API・CLI・MCPは同じ実装を使い、入力CSVを変更しません。
SVGは従来のWindows x64 / exact Node 22.23.4の制約を維持し、新しい描画形式は追加しません。
