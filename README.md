# hayase_assignment

課題の作業用リポジトリです。

今入っているものは大きく 2 つです。

- `csharp/Kadai3ScottPlot`
  Windows Forms と ScottPlot を使った課題3用の表示プログラム
- `digital`
  NEF からメタデータや輝度を取り出して、CSV やグラフを作るためのツール群

## 課題3のプログラム

場所:

- [csharp/Kadai3ScottPlot](/Users/jagashira/work/github.com/Jagashira/hayase_assignment/csharp/Kadai3ScottPlot)

Windows の Visual Studio で次を開けばそのまま実行できます。

- [csharp/Kadai3ScottPlot/Kadai3ScottPlot.sln](/Users/jagashira/work/github.com/Jagashira/hayase_assignment/csharp/Kadai3ScottPlot/Kadai3ScottPlot.sln)

内容はこんな感じです。

- `sin / cos / tan / exp` などの関数を切り替えて表示できる
- タイマーで時間を進める
- 速度をボタンで変えられる
- `tan` は漸近線のところで線が変につながらないようにしてある

詳しいメモは下の README に置いてあります。

- [csharp/Kadai3ScottPlot/README.md](/Users/jagashira/work/github.com/Jagashira/hayase_assignment/csharp/Kadai3ScottPlot/README.md)

## NEF まわり

NEF から CSV を作るときは `Makefile` のコマンドを使います。

よく使うもの:

- `make dcraw`
- `make metadata-csv`
- `make shutter-csv`
- `make iso100-csv`
- `make iso100-plot`
- `make iso100-theory-plot`

出力先:

- `output/csv`
- `output/images`

## 例

```bash
make shutter-csv
make iso100-csv
make iso100-plot
```

## 補足

NEF を PowerPoint に貼りたいだけなら、現像して色を合わせるより、まず埋め込み JPEG を抜くほうが早いです。

```bash
./bin/dcraw -e ./public/nef/100-1000-1.8.NEF
```

TIFF にしたい場合はこんな形です。

```bash
./bin/dcraw -T -w -o 1 -6 ./public/nef/100-1000-1.8.NEF
```
