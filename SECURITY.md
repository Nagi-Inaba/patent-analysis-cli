# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 0.2.x | Yes |
| 0.1.x and earlier | No |

分析契約は旧Rankingの`1.0.0`と登録済みv2分析の`2.0.0`を提供する。利用可能な分析・上限・描画形式は`capabilities`と[分析カタログ](docs/analysis-catalog.md)で確認する。

## Contract And Execution Boundary

OperationPlanはversion付きの説明・検証契約であり、本packageは登録済みoperationを実行しない。`analyze` は `AnalysisSpec` に基づく閉じたregistryの分析だけを実行する。旧Rankingとv2分析は同じ公開Python APIを通じてCLI・local stdio MCPから利用でき、任意code・SQL・shellを受け付けない。

OperationPlanは登録済み操作とstrict schemaだけを受け付け、operation paramsでは追加属性を許可しない。`intent` は非信頼の表示・監査用文字列として扱い、実行、shell展開、SQL組立、モデル転送には利用しない。

## Local Input Boundary

CLIの `inspect` / `analyze` / `render` とfile-backed `validate-plan` / `validate-spec` は、trusted launcherが絶対pathの既存ローカルdirectoryとして設定した `PATENT_ANALYSIS_ALLOWED_ROOT` とverified root/pathを必須とする。相対dataset（CSV・JSON）/spec/plan/analysis/overlay pathはこのrootを基準に解決し、root配下のregular fileだけを受け付ける。`--spec -`、`validate-plan -`、`validate-spec -`、`render --analysis -`、`render --overlay -`のbounded stdinだけがfile-backed入力の例外であり、analysisとoverlayを同時にstdinから読まない。rootまたはpathが未設定・拒否された場合は `input.invalid`、exit code 3となる。

optionalなlocal stdio MCPは起動時に入力・出力rootを検証し、重複・包含しないrootとして固定する。ツールはこのroot内の相対pathだけを扱い、CLI subprocessを起動せず公開Python APIを直接利用する。`inspect`はセル値を返さない。分析応答は入力由来labelと集計値を含む一方、coreのreceipt・安定hash・絶対pathを除く。描画用のfull documentは同じprocess内に最大4件保持し、opaque handleだけを返す。transport・引数・応答の固定byte上限と6ツールのclosed引数契約は[docs/contracts.md](docs/contracts.md)を参照する。remote transportは提供しない。

OperationPlanの `contract` と `validate-plan -` はこのrootを要求しないが、file-backed `validate-plan <file>` は要求する。OperationPlanとAnalysisSpecのJSON入力は最大2 MiB、render analysisは最大16 MiB、render overlayは最大4 MiBである。render JSONはobject construction前にdepth 64、token/node 250,000、numeric lexeme 128 bytes、decoded string合計2,000,000 code pointsを検査する。違反、duplicate key、NUL、NaN/Infinity、invalid UTF-8、non-objectは`input.invalid` / exit code 3となる。

WindowsではUNC/device/NT namespace/ADS、remoteまたはmapped drive、SUBST、symlink/junction/mount/reparse component、identity/final-handle escapeを拒否する。component swap、hard-link、host privilegeによる残余境界は残る。このcontrolはsandboxではなく、modelがenvironment variableを変更できる、またはarbitrary shellを実行できる運用ではroot境界を迂回できる。

## Privacy And Result Disclosure

package自身はmodel、network、cloud、外部API、外部の特許DB・特許データAPI、インターネット検索を呼ばない。`inspect` はcell valueを含まないbounded manifest metadataだけを返す。`analyze` はデータ由来のdimension label、集計値、count、shareを返し、unique labelがsource cell文字列と一致する場合もある。結果を外部AIやserviceへ送るかどうかはcaller policyであり、本packageの責務外である。

`LabelOverlayPack`、表示用label、`AnalysisResult`のlabelとその他のresult fieldsはcaller-controlled sensitive output（callerが管理する機微な出力）であり、package自身が外部へ送信することはない。package自身はnetwork、cloud、外部APIを呼ばない。`build_ranking_chart_model`と`build_ranking_render_spec`はローカルの契約検証・生成だけを行う。

trusted-local rendererはpackaged bootstrap/bundleだけを使い、Node/ECharts runtime、SVG artifact、relative receipt、公開Python API、公開`render` CLIを提供する。

## Trusted-local Renderer Security Boundary

trusted-local v1はWindows x64-onlyで、Node 22.19.0 exactとpackaged ECharts 6.1.0から固定profileのSVGを生成する。選択したNode executableはcallerが完全に信頼するlocal softwareであり、malicious executableはuser authorityで動作できる。このprofileはsandboxを主張しない。

analysis/overlayはbounded UTF-8 JSON objectとしてparseし、duplicate keyとNaN/Infinityを拒否する。semantic contractを先に構築し、成功後だけplatform、output、Nodeの順に検証する。file-backed inputは`PATENT_ANALYSIS_ALLOWED_ROOT`配下、outputとNodeはabsolute local non-reparse pathに限定する。childは固定argv、固定最小environment、10秒timeout、bounded concurrent stdout/stderr drainで起動する。

10秒はcooperativeなchildに対するwall timeoutであり、malicious Nodeやstdio handleを保持するdescendantへのcontainmentではない。parent APIはdaemon worker、best-effort kill、全pipe close、bounded follow-up wait/joinによって復帰時間をboundedに保つが、trusted executableやdescendantの終了は保証しない。

runtimeはverified self-contained bundleと固定bootstrapだけを使い、npm、`node_modules`、CDN、network、path import、caller option、theme、formatter、JavaScriptを受け付けない。package自身はanalysis、overlay、receipt、artifact、label、pathをAI/service/networkへ送らない。

Node runtime自体は`npm audit`の対象外であるため、release時に固定versionへ影響するNode security advisoryを別途確認する。[2026-01-13のNode 22.x advisory](https://nodejs.org/en/blog/vulnerability/december-2025-security-releases)のうち、固定bootstrapは`node:vm`を利用するが、allocation問題のtriggerとなるVM timeoutは指定しない。permission modelはdefense in depthとして有効にするが、固定実行経路はfilesystem・UDS・networkのallow-listを受け取らず、それらへアクセスしないため、symlink／`fs.futimes` bypassとHTTP/2・TLS・UDS問題の前提を満たさない。`async_hooks`も利用しない。

[2026-03-24のadvisory](https://nodejs.org/en/blog/vulnerability/march-2026-security-releases)にあるCVE-2026-21717は22.19.0に影響し、caller由来文字列を含むpayloadの`JSON.parse()`は実行経路にある。入力bytes・depth・node・文字列長をPython側で制限し、renderごとに独立childを起動して10秒後にbest-effort killし、parent APIがboundedに復帰する設計である。ただし、制限内でのHashDoSや反復呼び出しによる可用性低下を否定するものではないため、rendererをuntrusted multi-tenant serviceへ公開しない。

[2026-06-18](https://nodejs.org/en/blog/vulnerability/june-2026-security-releases)および[2026-07-29](https://nodejs.org/en/blog/vulnerability/july-2026-security-releases)の22.x advisoryも確認している。固定実行経路はWebCrypto encryption、HTTP/HTTP2、TLS、proxy、DNS、SQLite、zlib、`process.report`、trace events、filesystem、UDSを使用せず、filesystem・networkのallow-listも与えない。permission path over-grant、report／trace write、network parser・client、zlib等の問題はその前提を満たさない。将来のadvisoryがこの固定経路から到達でき、process分離と上限で緩和できない場合は、profileのNode versionを更新するまでreleaseを停止する。これらの評価はNode executableをsandboxにするものではなく、callerが完全に信頼するという前提を変更しない。

artifactはsame-directory own tempをfsync/closeし、Windows `os.rename`をno-replace commit pointとして公開する。完全一致する既存fileだけを`reused`とし、異なる既存fileを削除・repair・上書きしない。receiptのpath情報はrelative filenameだけであり、再利用確認用の決定論的hashも返す。

SVGは固定allow-listで正規化後、Pythonでtext-onlyの`title`・`desc`と固定ARIA参照を加える。文字列はXML escapeし、制御文字を可視化する。`xml:space="preserve"`はtext/tspanだけに許可する。公開receiptのhashはmetadataを含む最終bytesを対象とする。集計表は`--include-context`でSpec・分析文書全体を添付できる。trusted-local v1は支援技術全般の動作、WCAG適合、advanced Python SVG policy全体の再検証を主張しない。

## Public Error And Resource Boundary

`DatasetInputError` と `RenderError` の公開属性・`as_dict()`・通常の `str` / `repr`・標準形式のtracebackにはraw valueを出さない。`RenderError`は5組の固定code/message、`retryable = false`、空detailsだけを公開し、cause/contextを保持しない。

内部例外`RenderContractError`と公開例外はいずれも、Python tracebackのframe localsにcallerの入力値や中間のraw/text/rowsを保持し得る。`RenderContractError`はpackage rootの公開APIではない。cause/contextの抑止や固定safe messageはframe localsを消去しないため、logging、telemetry、AI、外部serviceではtraceback localsの収集を無効化し、無効化できない場合は外部送信前にcaller dataをredactする。

CSVの公開上限はfile size 300 MiB、columns 1,000、rows 100,000、cells 2,000,000、cell length 1,000,000文字である。dataset JSONはwhole-document parseのためfile sizeを32 MiB、object depthを64に制限し、展開後のcolumns・rows・cells・cell lengthにはCSVと同じ上限を適用する。duplicate key、NaN/Infinity、不正UTF-8、objectを含む配列、展開後の列名衝突も拒否する。ranking analysisには、`all` の1セルあたり空でないraw token 1,000個（dedup前）、post-dedup expanded contribution 500,000、distinct bucket 100,000の追加budgetがある。`first` は最初の空でないtokenで停止し、analysis budget違反は `input.invalid` / exit code 3となる。`inspect` はanalysis budgetの影響を受けない。root/path拒否、OperationPlan/AnalysisSpec JSONのUTF-8 decode・parse失敗または2 MiB超過、datasetのencoding/構造/公開上限違反も `input.invalid` / exit code 3である。

300 MiBはCSV入力サイズの上限であり、loaderはverified raw bytesとrow structuresを保持し、文字列を段階的にdecodeする。dataset JSONはverified raw bytesから全体をstrict parseしてから`DatasetV2`へ変換する。上限付近の合成データを使うCSV実測と再実行方法は[docs/performance.md](docs/performance.md)を参照する。実データ・分析条件ごとの必要メモリ量は保証しないため、near-limit operationの前に代表データでbenchmarkする。

## Reporting a Vulnerability

脆弱性の可能性がある内容は公開Issueへ投稿せず、[GitHub Private Vulnerability Reporting](https://github.com/Nagi-Inaba/patent-analysis-cli/security/advisories/new)から報告してください。

報告には、影響するversion、再現条件、想定される影響、可能であれば最小の再現手順を含めてください。特許データ、秘密情報、認証情報は添付せず、合成データで再現してください。受領後はGitHub Security Advisory上で確認と対応状況を連絡します。
