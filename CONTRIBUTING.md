# Contributing

`patent-analysis-cli`への改善提案を歓迎します。

## Issueとセキュリティ報告

不具合報告や機能提案はGitHub Issueを利用してください。再現手順、期待した結果、実際の結果、OS、Pythonバージョンを記載すると調査しやすくなります。

脆弱性の可能性がある内容は公開Issueへ投稿せず、[GitHub Private Vulnerability Reporting](https://github.com/Nagi-Inaba/patent-analysis-cli/security/advisories/new)から報告してください。詳細は[SECURITY.md](SECURITY.md)を参照してください。

## 開発環境

Python 3.14系（3.14以上・3.15未満）が必要です。Windowsでは署名済みPython 3.14を使用し、依存はproject専用の`.venv`へ導入します。

```powershell
$basePythonExe = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'
if ((Get-AuthenticodeSignature -LiteralPath $basePythonExe).Status -ne 'Valid') {
    throw 'Python signature verification failed'
}
uv venv --python $basePythonExe .venv
$pythonExe = (Resolve-Path .venv\Scripts\python.exe).Path
uv pip install --python $pythonExe --require-hashes -r requirements/mcp-2.0.0.lock
uv pip install --python $pythonExe -e ".[dev]" build
& $pythonExe -m pytest -q -p no:cacheprovider
& $pythonExe -m ruff check --no-cache src tests scripts
```

LinuxでもPython 3.14のvenvを作成し、同じextrasと検証コマンドを使用できます。SVG rendererの開発には`renderer/package-lock.json`に従うNode.js 22.19.0環境が必要です。

## 変更方針

- 公開API、Schema、CLI command、error codeを変更するときは、先に失敗する契約テストを追加してください。
- valid/invalidの双方を確認し、既存の数値回帰とcanonical bytesを維持してください。
- 分析ロジックはPython coreへ置き、CLIとMCPは公開Python APIを利用してください。
- 任意code、SQL、shell、network fetchを実行する機能は追加しないでください。
- 入力データ、絶対path、秘密情報をerrorやログへ含めないでください。
- renderer依存を変更した場合はlock、SBOM、第三者通知、生成bundleを同期してください。
- 文書は利用方法、仕様、開発・リリース手順に必要な内容へ限定してください。

## Pull Request

Pull Requestには変更理由、利用者への影響、実行した検証を記載してください。変更範囲は1つの目的に絞り、生成物や依存更新を含む場合はその根拠を説明してください。

提出されたcontributionは、このrepositoryの[Apache License 2.0](LICENSE)の条件で提供されます。
