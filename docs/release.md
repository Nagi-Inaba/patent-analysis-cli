# リリース手順

この文書は、source distributionとwheelを作成し、同じ成果物を検証して公開するための手順です。

## 前提

- release対象commitのCIが成功している
- `CHANGELOG.md`、version、利用者向け文書が一致している
- Python 3.14、Node.js 22.19.0、npmを使用する
- working treeがcleanである
- Apache-2.0本体ライセンスと第三者通知が配布物へ含まれる
- 公開repositoryではGitHub Private Vulnerability Reportingが有効である

## Build

project専用venvへhash固定したMCP依存と開発依存を導入し、testとlintを実行します。このlockはsource testの再現性を保証します。

```text
python -m pip install --require-hashes -r requirements/mcp-2.2.0.lock
python -m pip install -e '.[dev,inventor]' build
python -m pytest -q -p no:cacheprovider
python -m ruff check --no-cache src tests scripts
python -m build
```

rendererを変更した場合は、`renderer/package-lock.json`から`npm ci`を実行し、typecheck、lint、test、全bundleの再生成一致を確認します。Node.jsは22.19.0を使用します。

## 配布物の検証

CIは既存のWindowsとLinuxに加えて`macos-15`（arm64）と`macos-15-intel`でwheelとsdistを作成し、test、lint、renderer build、dependency auditを実行したうえで、次を確認します。Windowsはskip 0件、macOSはWindows固有の`tests/test_access.py`に限ってskipを許可し、native SVG testsはすべて実行します。

1. wheel内のPython source、Schema、renderer資産、Apache-2.0ライセンス、第三者通知がrelease対象commitと一致する。
2. sdistにbuildへ必要なPython／renderer source、lock、test fixture、文書、例が含まれる。
3. system site-packagesを継承しない新しいvenvへwheelを非editable installする。この検証では公開metadataのversion範囲から現在の依存を新規解決し、lock環境とは別に互換性を確認する。
   依存のwheelは`pip wheel`で準備する。Intel macOSなどで安全な版の完成済みwheelがない場合は、ソースからwheelを作成してからoffline installを検証する。binary-only制限を満たすために古い版へ戻さない。
4. coreだけの環境でconsole entrypoint、<!--var:catalog_case_count-->18<!--/var-->分析、Windows x64またはmacOS arm64/x86_64の対応SVGと再利用を検証する。
5. 同じwheelへ`[mcp]` extraを導入し、実stdio経由の<!--var:catalog_case_count-->18<!--/var-->分析、未知分析の拒否、Windows x64またはmacOS arm64/x86_64の対応SVGと再利用を検証する。
6. 別の新しいvenvへ同じwheelの`[inventor]`、続いて`[inventor,mcp]` extraを導入し、発明者分析10種類のPython API・console entrypoint・実stdio MCPを比較する。Windows x64またはmacOS arm64/x86_64では発明者SVG9種類と再利用も確認し、Linuxでは公開SVG経路を迂回しない。
7. 検証前後で入力CSV・JSONとspecが変化していないことを確認する。

`scripts/verify_installed_release.py`と発明者用の`scripts/verify_installed_inventor_release.py`はsource tree外から`-I`付きで実行し、検証結果をJSON reportへ保存します。

## 依存・secret検査

hash固定した`requirements/mcp-2.2.0.lock`と、配布wheelから新規解決した実際の依存を`pip-audit==2.10.1`で検査します。renderer lockは`npm audit --json`で検査します。lockはsource testの再現性、新規解決は公開時点のinstall互換性をそれぞれ確認するもので、両方に既知脆弱性がないことを要求します。

Gitleaks 8.30.1でrelease対象commitまでのGit履歴と、wheel・sdistを含む`dist`を検査します。配布物は3階層まで展開し、reportはredactします。

```text
pip-audit --no-deps --disable-pip -r dist/verification/dependencies.txt --format json
npm --prefix renderer audit --json
gitleaks git . --log-opts=HEAD --redact --no-banner
gitleaks dir dist --max-archive-depth=3 --redact --no-banner
```

監査結果は候補ごとに保存し、別commitの結果を流用しません。依存更新は影響範囲を確認して個別に行い、強制的な一括更新は避けます。

## 公開

公開するwheel、sdist、GitHub Release、tagは同じcommitを指す必要があります。次を記録します。

- commit ID
- Python、Node.js、npmのversion
- wheel、sdist、依存wheelのSHA-256
- clean-install report
- Python／npm dependency audit
- Git履歴／配布物のsecret scan

GitHub Releaseには変更履歴、対応platform、Python要件、renderer要件を記載します。PyPIへ公開する場合は、検証済みwheelとsdistだけをアップロードし、公開後にhashとinstall手順を再確認します。

## 第三者通知

`src/patent_analysis/renderer/THIRD_PARTY_NOTICES.txt`をwheelとsdistへ含めます。このファイルには固定npm版のECharts、zrender、xmldom、tslib、生成コードに関係するAjv・Rolldown等の通知があります。

本体の利用条件はrepository rootの`LICENSE`（Apache License 2.0）が定めます。第三者コンポーネントには、それぞれの通知とライセンスが適用されます。
