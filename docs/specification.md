# 現行仕様の見取り図

ローカルの特許データを明示した条件で集計し、結果と根拠を確認するための仕様索引です。契約の適用範囲、共通処理、例外を示します。

## 読む資料と正本

| 確認したいこと | 参照先 | 役割 |
| --- | --- | --- |
| 導入・最初の実行 | [README](../README.md) | 利用手順 |
| 利用可能な分析・mark・schema・上限 | `capabilities --json`、[分析カタログ](analysis-catalog.md) | インストールした配布物の機械可読な能力と選択ガイド |
| 入出力・公開API・エラー・互換性 | [contracts](contracts.md)、`schema <filename> --json` | 共通契約と公開Schema。意味検証はSchemaに加えて実装が行う |
| 処理境界・責務 | [architecture](architecture.md) | API、分析コア、描画、adapterの関係 |
| Ranking固有の集計 | [ranking-analysis-v1](ranking-analysis-v1.md) | 旧Ranking契約に適用。共通母集団を使う[Ranking v2](input-preflight-and-ranking-v2.md)も提供 |
| 応用分析の数え方 | [advanced-json-slices](advanced-json-slices.md) | 応用分析の計算・欠損・分母・上限 |
| フィルターと代表1行選択 | [contracts](contracts.md)、[family-population](family-population.md) | 既存v2分析の母集団 |
| 共発明クラスタの年次追跡 | [inventor-tracking](inventor-tracking.md) | 旧来の追跡分析。新しい人物ID分析群とは別 |
| 人物ID・単位・引用・関係変化の根拠 | [inventor-analysis](inventor-analysis.md) | 専用の発明者分析群 |
| CSV・テキスト表 / SVG | [table-export](table-export.md)、[advanced-rendering](advanced-rendering.md) | 表現・表示予算・省略の意味 |
| local stdio MCP | [mcp](mcp.md)、[contracts](contracts.md#local-stdio-mcp-adapter) | 起動、ツール引数、handleと情報開示 |
| 安全性 / 性能 / 配布物の検証 | [SECURITY](../SECURITY.md)、[performance](performance.md)、[release](release.md) | 信頼境界、過去の計測、受入手順 |

公開契約は対象のpackage・Schema・registry・実装・契約テストに基づきます。

## 提供範囲

Python API・CLI・local stdio MCPが同じ計算コアを使います。公開対象は<!--var:analysis_count-->29<!--/var-->分析、MCPは<!--var:mcp_tool_count-->6<!--/var-->ツールです。JSON、CSV・テキスト表、対応する固定markのSVGを出力します。

入力は利用者が用意したローカルCSVまたはJSONです。列対応、正規化、分析条件をSpecへ明示します。外部特許DB取得、自然言語からのSpec生成、任意SQL・コードの実行、GUI、remote MCPは提供範囲に含みません。

`OperationPlan`は説明・検証用の契約であり、登録済みoperationを実行する計画エンジンではありません。実行入口は`analyze --spec`と、その共有APIである`run_analysis`です。

## 混同しやすい契約の区分

| 区分 | 入力Spec / 集計本体 | 母集団・識別の規則 |
| --- | --- | --- |
| `ranking.v1` | version fieldのない旧Spec / `result` | 元レコードを集計。`multi_value_mode`を指定。v2のfilters・family選択は使わない |
| 共通母集団v2の<!--var:population_analysis_count-->18<!--/var-->分析（`ranking.v2`・`inventor-tracking.v1`を含む） | `analysis_contract_version: "2.0.0"`と`analysis_id` / `data` | 共通の列対応・正規化・filters・selection_sets、`family_mode: records`または`earliest` |
| 新しい発明者<!--var:inventor_analysis_count-->10<!--/var-->分析 | 同じv2 envelope / `data.statistics`、`data.input_coverage`等 | 専用のraw ID入力。共通`family_mode`は`records`のみ。最初の7分析は別の`parameters.unit`で計算単位を指定 |

新しい発明者分析には`inventor` extraが必要です。`inventor-tracking.v1`はこのextraの対象ではありません。発明者の氏名、人物ID、企業のID、ファミリーIDを同じ正規化規則で扱いません。

## 入力と処理順

```text
local CSV / JSON + AnalysisSpec
  -> allowed-root / file / size checks
  -> spec dispatch + dataset loading
     +-> legacy Ranking -> result + receipt
     +-> existing v2
     |    -> bindings + normalization
     |    -> filters + selection_sets
     |    -> records / earliest representative
     |    -> analysis-specific aggregation -> data + receipt
     +-> native inventor
          -> raw IDs + optional auxiliary evidence
          -> filters + witnessed units / observations
          -> statistics + coverage + evidence + provenance
  -> JSON / CSV table / text table
  -> optional fixed chart model -> trusted local Node -> SVG + receipt
```

図は論理上の境界を表します。個々のAPIでの検査順やエラー優先順位は、その実装と契約テストに従います。

| 項目 | 現行契約 |
| --- | --- |
| CSV | comma区切り。UTF-8、UTF-8 BOM、UTF-16 LE/BE BOM。300 MiBまで |
| JSON dataset | `.json`拡張子。UTF-8、先頭BOM 1個を許容。単一objectまたは空でないobject配列。32 MiBまで |
| 共通の入力上限 | 100,000行、1,000列、headerを含む2,000,000セル、1セル1,000,000文字。分析固有の上限でさらに狭まる |
| JSONの列化 | 入れ子objectをドット区切り列へ展開。scalar配列は`\|`区切りへ変換。欠けた列は空文字 |
| 拒否するJSON | 重複キー、非有限数、object/配列を含む配列、列名衝突、不正encoding等。詳細は[入力契約](contracts.md#json-input) |
| 新しい発明者IDのセル | 既定はJSON文字列配列を表す文字列セル。`parameters.id_array_format: "native"`で明示bindingしたID列のJSON配列も受理。[詳細](input-preflight-and-ranking-v2.md) |
| `inspect` | メタデータだけ。セル値・サンプル行を公開しない |
| `validate-spec` | `--dataset`省略時はSpecの構造・実装済み条件を検査。`--dataset`指定時は列対応・欠損・共通母集団の事前診断。分析固有の適格性・集計は`analyze`、描画は`render`で確認 |

`earliest`はフィルター通過後の同一IDから代表1行を選びます。ID空欄は個別に残し、代表以外の人物・出願人・分類を合算しません。両候補の日付が有効な場合だけ早い日を選び、同日や不正・欠損日付の比較は入力順で決めます。

発明者分析の`unit: family`は、人物の観測根拠を保持して単位をまとめる別の契約です。`family_mode: earliest`による代表選択へ置き換えられません。`inventor-tracking`の年内連結成分と、`inventor-network`等のコミュニティも別の定義です。

## 出力と利用境界

| 出力・入口 | 固定する条件 |
| --- | --- |
| JSON | 旧`ranking.v1`は`result`、`ranking.v2`を含むv2は`data`。元の行数、選択後の行数、複数値の所属数、ペア数、構成比の分母を区別する |
| CSV / text | 全分析に対応。完成出力16 MiBまで。`--include-context`でSpecと分析文書全体を添付。CSVは数式開始文字をescapeする |
| SVG | <!--var:mark_count-->28<!--/var-->固定mark。任意ECharts option不可。`inventor-mobility-evidence.v1`にはmarkなし。複数分析で共用するmarkもあるため、分析とmarkは1対1ではない |
| SVG保存 | 出力先は既存ディレクトリ。同一bytesは`reused`、異なる既存artifactは上書きしない |
| MCP analyze | core receipt・安定hashを公開応答から除外。対応markがある分析だけ、同じprocess内で使うランダムな`render_handle`を返す |
| MCP render | 最大4件のFIFO handleから検証済み分析を参照。5件目のhandle発行や再起動で古いhandleが無効になる。markのない分析はhandleを発行せず、既存handleも退去させない |

SVG対応はWindows x64とmacOS arm64/x86_64、Node.js 24.22.1 exactです。Linuxでは分析・JSON・表を利用でき、公開SVG経路は非対応です。Pythonは3.14系です。現在の依存指定は[pyproject.toml](../pyproject.toml)、描画条件は[contracts](contracts.md)を参照します。

CLIのファイル入力は`PATENT_ANALYSIS_ALLOWED_ROOT`、Python APIは`allowed_root`、MCPは起動時のinput/output rootを使います。CLI/APIの描画先は既存ディレクトリを渡します。MCPは既存のoutput root内に、指定した相対`output_path`の不足ディレクトリを作成できます。入力元を変更せず、描画先への書込みを別に扱います。これらは信頼するローカル実行環境の境界であり、任意shellを実行できる相手へのsandboxではありません。

分析結果やSVGには入力由来のラベルが残ります。MCPでも匿名化を保証しません。共発明や出願人との共記載、関係先の変化候補を、雇用・所属部署・転職・因果関係の証明へ読み替えません。未観測、欠損、既知のゼロ、未提供の根拠を区別します。

## 実装と受入確認の対応

| 仕様境界 | 実装の入口 | 主な既存検証 |
| --- | --- | --- |
| 公開能力・Spec振分け | [api.py](../src/patent_analysis/api.py)、[analysis_dispatch.py](../src/patent_analysis/analysis_dispatch.py)、[analysis_registry.py](../src/patent_analysis/analysis_registry.py) | `tests/test_public_api.py`、`tests/test_spec_cli.py`、`tests/test_doc_vars.py` |
| CSV / JSON入力 | [dataset_v2.py](../src/patent_analysis/dataset_v2.py)、[data.py](../src/patent_analysis/data.py) | `tests/test_json_dataset_input.py`、`tests/test_dataset_v2.py` |
| 母集団・代表選択 | [population.py](../src/patent_analysis/population.py)、[normalization/family.py](../src/patent_analysis/normalization/family.py) | `tests/test_family_population.py` |
| 人物ID・単位・根拠 | [inventor_inputs.py](../src/patent_analysis/inventor_inputs.py)、[inventor_units.py](../src/patent_analysis/inventor_units.py)、[inventor_sidecars.py](../src/patent_analysis/inventor_sidecars.py) | `tests/test_inventor_examples.py`、`tests/test_inventor_foundation_inputs.py`、`tests/test_inventor_foundation_units.py` |
| 表出力 | [analysis_tables.py](../src/patent_analysis/analysis_tables.py)、[analyses/_inventor_common.py](../src/patent_analysis/analyses/_inventor_common.py) | `tests/test_table_export.py`、`tests/test_inventor_public_cli.py` |
| 描画・MCP・配布物 | [local_renderer.py](../src/patent_analysis/local_renderer.py)、[tool_handlers.py](../src/patent_analysis_mcp/tool_handlers.py) | [release](release.md)の独立したwheel受入確認とOS別CI |

## 残る確認と変更判断

- 実データでの列対応、人物識別、欠損・重複の品質、使用するSpecでの性能は、合成例の成功だけでは確定しません。
- Schemaに適合するだけで分析が成功するとは限りません。集計時の適格性、byte予算、描画資産とruntimeの条件も確認します。
