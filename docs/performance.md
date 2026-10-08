# CSVの性能測定

CSVの公表上限は300 MiB、100,000行、1,000列、2,000,000セルである。セル数にはheaderも含む。これらは入力の拒否境界であり、すべての分析条件に対する推奨サイズや必要メモリ量ではない。

## 測定方法

`scripts/benchmark_csv.py`は新しいローカルdirectoryに合成CSVを作り、`api.inspect_dataset()`、legacy Ranking、v2 Compositionをそれぞれ新しいPython processで実行する。行数・列数または固定の集計値を検証し、全実行後に元CSVのSHA-256一致も検査する。package外部の開発用scriptであり、特許データやネットワークを使わない。

- `rows`: 100,000行、2列、900,015 bytes。
- `cells`: 99,999行、20列、header込み2,000,000セル。
- `wide`: 1,999行、1,000列、header込み2,000,000セル。
- `bytes`: 100,000行、2列、ASCII本文、ちょうど300 MiB。
- `unicode`: 100,000行、2列、UTF-8の日本語本文、ちょうど300 MiB。

合成CSVは`group`がすべてAで、分析しない本文列を含む。実データの多数ラベル・多値展開・多条件・family処理を網羅する測定ではない。実運用では同じ機械で代表データと使用するSpecも測定する。

## Windowsでの実測

2026-09-26、Windows 11 10.0.26200、Intel Core i7-9700、32 GiB RAM、CPython 3.14.3。各条件1回の観測値で、中央値や保証値ではない。時間はAPI呼出し、ピークメモリはimportを含むprocess全体のWindows PeakWorkingSetSizeをMiBに換算した値である。

| 入力 | 処理 | 変更前 秒 | 変更後 秒 | 変更前 MiB | 変更後 MiB |
| --- | --- | ---: | ---: | ---: | ---: |
| rows | inspect | 0.27 | 0.21 | 331.8 | 52.8 |
| rows | Ranking | 0.39 | 0.32 | 331.6 | 57.1 |
| rows | Composition | 5.41 | 3.38 | 331.8 | 95.4 |
| cells | inspect | 0.65 | 0.56 | 331.8 | 161.1 |
| cells | Ranking | 0.90 | 0.85 | 331.7 | 178.5 |
| cells | Composition | 9.95 | 6.41 | 331.8 | 206.0 |
| wide | inspect | 0.42 | 0.35 | 331.6 | 153.1 |
| wide | Ranking | 0.62 | 0.52 | 331.7 | 186.7 |
| wide | Composition | 5.36 | 3.57 | 331.8 | 156.5 |
| bytes | inspect | 3.83 | 3.30 | 2160.4 | 661.9 |
| bytes | Ranking | 3.89 | 3.37 | 2165.4 | 665.5 |
| bytes | Composition | 87.59 | 9.87 | 2160.9 | 661.9 |
| unicode | inspect | 2.30 | 2.14 | 1161.4 | 559.7 |
| unicode | Ranking | 2.42 | 2.30 | 1165.4 | 563.5 |
| unicode | Composition | 51.34 | 7.08 | 1161.4 | 560.7 |

丸め前の値、生成データのhash、比較対象のreader/serializerのsource hashは[performance-sample.json](performance-sample.json)にある。変更前は全文decodeとStringIOを併用し、変更後はverified byte snapshotを段階的にdecodeする。小さいファイルでは公表最大サイズを先に確保せず、実際のfile sizeに応じて読む。JCS文字列はサロゲート検査を維持して標準JSON encoderでescapeし、全Unicode scalarの固定hash、既存の数値・key順・不正文字の回帰で出力互換性を検査する。

## 再実行

READMEの開発環境を用意し、署名を確認したPythonで実行する。`--workspace`には未作成のdirectoryを指定する。既存directoryを上書きせず、生成CSVは比較用に残す。全5条件で約640 MiBの空きdiskを使う。

```powershell
$pythonExe = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'
if ((Get-AuthenticodeSignature -LiteralPath $pythonExe).Status -ne 'Valid') { throw 'Invalid Python signature' }
if ((Get-AuthenticodeSignature -LiteralPath .\.venv\Scripts\python.exe).Status -ne 'Valid') { throw 'Invalid venv signature' }
New-Item -ItemType Directory -Force .benchmark-work | Out-Null
$env:PYTHONUTF8 = '1'
& .\.venv\Scripts\python.exe scripts/benchmark_csv.py --workspace .benchmark-work/csv-run --repeat 1
```

`--cases rows bytes`のように対象を限定できる。`--repeat 3`は各条件を独立processで3回実行する。stdoutは環境1行と測定結果のJSON Lines。各実行は600秒上限で、集計の不一致やprocessの失敗は非ゼロ終了する。Linuxでは`ru_maxrss`をbytesに換算するが、上表はWindowsの実測のみである。
