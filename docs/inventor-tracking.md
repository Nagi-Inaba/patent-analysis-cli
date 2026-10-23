# 発明者・共発明クラスタの年次追跡

`inventor-tracking.v1`は、CSVに記録された発明者・出願人・日付から、年ごとの共発明クラスタと出願人との関係の変化を集計します。Python API・CLI・local stdio MCPから利用でき、JSON、CSV／テキスト表、`inventor-tracking-svg.v1`のSVGを出力します。

## 入力と識別

[合成CSV](../examples/inventor-tracking/patents.csv)と[Spec](../examples/inventor-tracking/spec.json)を用意しています。Specの必須パラメータは`date_role`、`inventor_role`、`applicant_role`で、`resolution.bindings`でそれぞれ実際の列に対応させます。

- 日付には`year`、`filing_date`など共通正規化で日付を扱うroleを指定します。年は1800〜2199。日付は暦年へ正規化し、発明者または有効年のない行を除外します。複数の有効年を持つ行はエラーにします。
- 発明者欄の`|`や`;`等は複数値の区切りです。同じ行内の同じ値は1回だけ数えます。`identity_kind: "name"`では追跡集計時に氏名へNFKCと前後の空白除去を適用し、全角・半角等の互換文字を統一します。同姓同名の分離や、これを超える曖昧な名寄せは行いません。
- 信頼できる発明者IDがある場合は、その列を`inventor_role`のbinding先にし、`identity_kind: "id"`を指定します。既定値は`"name"`です。IDには追跡側のNFKCを適用せず、共通の値分割・前後空白除去後の値を保持します。IDと氏名の並び順による対応付けは行わず、IDを図の行ラベルにも使います。IDの一意性と区切り文字を含まないことは入力側で管理します。
- `applicant`などのroleでは共通の出願人名正規化を適用します。複数発明者・複数出願人の行は、その全組み合わせを同じ特許での共記載として数えます。個々の発明者の勤務先を割り当てる処理ではありません。

フィルターと`selection_sets`、`family_mode: "records" | "earliest"`は共通仕様です。フィルター・代表選択の後に追跡します。氏名のNFKC統一もこの段階なので、発明者列で絞り込む場合は共通の値分割後の表記を指定します。`earliest`では代表以外の行の人物や出願人を合算しないため、全出願の活動履歴を見たい場合は`records`を使います。

## クラスタと変化の定義

同一年の同一レコードに現れる発明者の各ペアを共発明関係とします。そのグラフの**連結成分**がクラスタです。A–BとB–CがあればA・B・Cは同じクラスタになり、単独の発明者も1つのクラスタになります。コミュニティ検出の最適化や技術分類による類似度は使いません。

クラスタIDは`年:年内の番号`です。年内で発明者の値を辞書順に並べて番号を決めます。入力行を並べ替えても結果は変わりません。同じ番号でも別の年のクラスタは別物です。

隣接する暦年のクラスタ間で、両年に観測された発明者の共通集合を`cluster_links`として出力します。1つのクラスタから複数へつながると`split: true`、複数から1つへつながると`merge: true`です。リンクの件数は共通する発明者数です。未観測年を飛び越すクラスタリンクは作りません。

出願人の変化は、発明者ごとの連続する**観測年**の出願人集合を比較します。新たに現れた出願人を`added_applicants`、観測されなくなった出願人を`removed_applicants`へ出します。空白年の数は`gap_years`に残します。これは観測間の差分で、異動が起きた日付や雇用・転職の認定ではありません。

比較するどちらかの年に出願人欄が空のレコードが1行でもある場合、`status: "unknown"`とし、追加・消失の配列は空にします。他の行に出願人が記載されていても、欠損を消失とはみなしません。欠損がなければ`changed`または`unchanged`です。

## 出力

| JSON／表の名前 | 内容 |
| --- | --- |
| `inventors` | 発明者別件数と初回・最終観測年 |
| `observations` | 発明者×年の件数、クラスタ、出願人集合、出願人欠損行数 |
| `co_inventions` | 年別の共発明ペアと共同レコード数 |
| `affiliations` | 発明者×年×出願人の共記載件数 |
| `clusters` | 年別クラスタと全メンバー |
| `cluster_links` | 隣接年の共通メンバー、分裂・合流フラグ |
| `affiliation_changes` | 観測年の間の出願人集合の変化と未観測年数 |

`contributions`は発明者所属件数＋共発明ペア件数＋出願人共記載件数です。レコード件数とは異なります。集計の固定期待値は[expected-aggregates.json](../examples/expected-aggregates.json)の`inventor-tracking.v1`にあります。

SVGの横軸は暦年、縦軸は発明者です。色とC番号は**同一年内**のクラスタを表し、菱形は出願人の変化、白抜きは比較不明、破線は未観測年を含む同一発明者の観測間リンクです。空白年にも横軸の位置を残します。長いラベルは図上で省略し、JSON・表には全値を保持します。分裂・合流の全メンバーは`cluster_links`で確認できます。

```powershell
$env:PATENT_ANALYSIS_ALLOWED_ROOT = (Resolve-Path examples).Path
& $pythonExe -m patent_analysis analyze inventor-tracking/patents.csv --spec inventor-tracking/spec.json --format text --include-context
$result = & $pythonExe -m patent_analysis analyze inventor-tracking/patents.csv --spec inventor-tracking/spec.json --json
if ($LASTEXITCODE -ne 0) { throw "Analysis failed" }
# $outputは既存ディレクトリの絶対パス。$nodeExeは信頼するNode 24.22.1 x64。
$result | & $pythonExe -m patent_analysis render --analysis - --mark inventor-tracking-svg.v1 --output $output --node $nodeExe --json
```

## 上限

1回の追跡は、フィルター後の有効行に現れる発明者20件まで、最初から最後まで12暦年以内です。クラスタを壊す上位件数の切り捨ては行いません。超える場合は対象期間・対象レコードを絞って再実行してください。特定人物を含む行を選ぶ場合も、その行の共発明者は残ります。

共通の100,000行、roleごと100値／行、正規化値2,000,000、展開寄与1,000,000、追跡キー100,000の上限も適用します。この分析の集計本体は192 KiBまでです。上限超過は`input.invalid`で終了し、部分的な図は作りません。SVGには既存の文字数・サイズ上限も適用します。SVG生成はWindows x64・固定Node版のtrusted-local環境が必要です。
