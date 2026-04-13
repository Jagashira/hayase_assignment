# 課題3 ScottPlot サンプル

`Visual Studio` と `Visual C#`、`System.Windows.Forms.Timer`、`ScottPlot` を使って、
動画 `課題3の霊.mp4` のように定期的に増加するデータを表示するサンプルです。

## 内容

- `x` を 0.1 秒刻みで増加
- `sin(x)` と `cos(x)` を定期更新
- 現在位置を縦線で表示
- 右下に現在の `x` 値を表示
- `開始 / 停止 / リセット` ボタン付き

## 開き方

1. Windows の Visual Studio で [Kadai3ScottPlot.sln](/Users/jagashira/work/github.com/Jagashira/hayase_assignment/csharp/Kadai3ScottPlot/Kadai3ScottPlot.sln) を開く
2. NuGet 復元を行う
3. 実行する

## 主要ファイル

- [Program.cs](/Users/jagashira/work/github.com/Jagashira/hayase_assignment/csharp/Kadai3ScottPlot/Program.cs)
- [MainForm.cs](/Users/jagashira/work/github.com/Jagashira/hayase_assignment/csharp/Kadai3ScottPlot/MainForm.cs)
- [Kadai3ScottPlot.csproj](/Users/jagashira/work/github.com/Jagashira/hayase_assignment/csharp/Kadai3ScottPlot/Kadai3ScottPlot.csproj)
