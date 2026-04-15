# RGB 課題メモ

`rgb.c` は GTK/GdkPixbuf で画像を読み込み、各画素について次の 6 列を標準出力へ出します。

`y x r g b r+g+b`

- `y`: 行番号
- `x`: 列番号
- `r g b`: 各画素の RGB 値
- `r+g+b`: 明るさの簡易指標

この macOS 環境には GTK が入っていないため、元の C 版はそのままではビルドできません。
その代わりに `extract_rgb.py` を追加し、`rgb.c` と同じ列構成のデータを出せるようにしています。

## 実行

```sh
cd rgb
make plot_latte
```

生成物:

- `latte_rgb.dat`: `latte.jpg` から抜き出した RGB テーブル
- `latte_falsecolor.png`: `gnuplot` が色変換して描いた図

`latte_falsecolor.plt` では条件に応じて対象色を強調した画像を出力します。

輝度比較は `LUMINANCE_SOURCE` を 1 か所変えるだけで切り替えられます。

```sh
cd rgb
make plot_luminance_compare
```

必要なら実行時に上書きもできます。

```sh
make plot_luminance_compare LUMINANCE_SOURCE=../public/rgb/redBrick.JPG
```

輝度比較では次の 6 図をまとめて出力します。

- `L_sum = R + G + B` の公平比較用マップ
- `L_weighted = 0.299R + 0.587G + 0.114B` の公平比較用マップ
- `L_sum - L_weighted` の符号付き差分マップ
- `L_weighted` の単独 min-max 正規化版
- `L_weighted` の 1%-99% パーセンタイル正規化版
- パーセンタイル正規化にガンマ 2.2 をかけた版

公平比較用の 2 枚は、両者それぞれを別々に正規化せず、共通の `global_min` と `global_max` を使って表示スケールをそろえています。
