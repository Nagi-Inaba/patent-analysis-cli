# Local stdio MCP

## インストールと起動

MCPはoptional extraです。通常の集計だけなら不要です。リポジトリからは`python -m pip install ".[mcp]"`、wheelからは`python -m pip install "./patent_analysis_cli-0.2.0-py3-none-any.whl[mcp]"`を使います。

新しい発明者<!--var:inventor_analysis_count-->10<!--/var-->分析も使う場合は、リポジトリでは`python -m pip install ".[mcp,inventor]"`、wheelでは`python -m pip install "./patent_analysis_cli-0.2.0-py3-none-any.whl[mcp,inventor]"`を指定します。`inventor-tracking.v1`はこの追加extraの対象外です。詳細は[発明者分析](inventor-analysis.md)を参照してください。

例では既存`examples`を入力root、新しい別ディレクトリを出力rootにします。PowerShellで、READMEのvenvを使用します。

```powershell
$pythonExe = (Resolve-Path .venv\Scripts\python.exe).Path
$inputRoot = (Resolve-Path examples).Path
$outputRoot = Join-Path $env:TEMP ("patent-mcp-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $outputRoot | Out-Null
& $pythonExe -m patent_analysis_mcp.server --input-root "input=$inputRoot" --output-root "output=$outputRoot"
```

stdio対応クライアントには、上記のPython絶対パスを`command`、`-m`以降を個別の`args`として設定します。単独起動後に通常のプロンプトが返らないのは、MCPメッセージをstdinで受け取るサーバーだからです。HTTPサーバーやremote MCPではありません。

入力・出力は既存のローカルディレクトリで、IDも実パスも重複・包含させません。ツールへ渡す`path`・`output_path`は対応rootからの相対パスです。CLIの`PATENT_ANALYSIS_ALLOWED_ROOT`は、この起動設定の代わりにはなりません。SVGにはWindows x64またはmacOS arm64/x86_64と、対応アーキテクチャのNode.js 24.22.1 exactが必要です。Linuxでは集計・JSONを利用できますが、公開SVG経路は非対応です。信頼するNode絶対パスを`--node`で指定することもできます。

## 発見 → 検証 → 分析 → 描画

公開ツールは次の<!--var:mcp_tool_count-->6<!--/var-->件です。

| ツール | 役割 |
| --- | --- |
| `patent_analysis.capabilities` | 利用できる<!--var:mcp_analysis_count-->29<!--/var-->分析・mark・schema名 |
| `patent_analysis.schema` | 許可されたschema名からJSON Schemaを取得 |
| `patent_analysis.inspect` | CSV・JSONのメタデータ検査。サンプル行は返さない |
| `patent_analysis.validate_spec` | JSONオブジェクトとして渡したspecを検証 |
| `patent_analysis.analyze` | 同じ公開Python APIで集計 |
| `patent_analysis.render` | 同じセッションのhandleからローカルSVGを出力 |

まず`capabilities`を`{}`で呼び、返されたschema名を`schema`へ渡します。下は`tools/call`の`params`であり、JSON-RPC全体ではありません。

```json
{
  "name": "patent_analysis.analyze",
  "arguments": {
    "input_root_id": "input",
    "path": "advanced/patents.csv",
    "spec": {
      "analysis_contract_version": "2.0.0",
      "analysis_id": "collaboration-network.v1",
      "resolution": {"bindings": {"group": "group"}},
      "normalization": {"profiles": []},
      "population": {"filters": [], "selection_sets": [], "family_mode": "records"},
      "parameters": {"category_role": "group"}
    }
  }
}
```

`validate_spec`には同じ`spec`を`{"spec": ...}`として渡します。`spec`のファイル名文字列や`$ref`ではなく、ファイルを読んだJSONオブジェクトが必要です。

[例の一覧](../examples/analysis-catalog.json)で`mcp: true`の18例は、この呼び出しの`path`と`spec`を該当CSV・JSONへ置き換えて実行できます。[期待集計](../examples/expected-aggregates.json)を同じ分析IDで確認してください。Matrix・Timeline・Compositionも、同じ公開API経由で分析・描画できます。

対応markがある分析の成功応答には`structured_content.content.render_handle`が含まれ、同じサーバープロセス内で使用できます。`inventor-mobility-evidence.v1`など、対応markのない分析はhandleを発行しません。クライアントのSDKによってフィールド名の表記は異なるため、wireでは返されたstructured contentを参照してください。

```json
{
  "name": "patent_analysis.render",
  "arguments": {
    "output_root_id": "output",
    "output_path": "network",
    "analysis_handle": "<直前の成功応答のrender_handle>",
    "mark": "collaboration-network-svg.v1"
  }
}
```

承認するoutput root自体は既存ディレクトリでなければなりません。その配下の`output_path`（例では`network`）が存在しなければ、MCP adapterが安全性を確認して作成します。receiptの`svg`はこの出力先からの相対名です。同一入力・出力先の再実行は`reused`になり、異なる内容を上書きしません。handleは最大4件のFIFOで、5件目のhandle発行時に最古のものが失効し、再起動後は全件無効になります。markのない分析はhandleを発行せず、既存handleも退去させません。分析の直後に描画するか、失効後は分析をやり直してください。

## 外部AIへ渡す情報

元CSV・JSONや任意ファイルを転送するツールではありません。`.json`は単一特許objectまたはobject配列を受け付け、変換規則と上限は[入力契約](contracts.md#json-input)に従います。ただし分析応答に出願人・分類等の入力由来ラベルは含まれます。機密情報を含む結果をAI・ログ・外部サービスへ渡すかどうかは呼び出し側の責任です。`analyze`応答はcoreのreceipt・安定SHA-256・絶対パスを除き、対応markがある場合だけランダムな`render_handle`を返します。`render`応答は指定した`output_path` directoryからの相対filenameに加え、再利用確認用の決定論的な`artifact_id`、`svg_sha256`、`renderer_build_digest`を返します。

入力不備や非公開分析の拒否は、安全なerrorとして返ります。`is_error` / `ok`を確認し、失敗応答からhandleを取り出そうとしないでください。任意式、SQL、shell、HTTP transportは追加していません。

## 入力と描画環境の事前診断

`validate_spec`のデータ照合、発明者ID配列、`ranking.v2`、描画runtime診断の契約と例は[入力診断とRanking v2](input-preflight-and-ranking-v2.md)を参照してください。
