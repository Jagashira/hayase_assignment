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

`latte_falsecolor.plt` では、左に元画像、右に gnuplot の式で偽カラー化した画像を並べています。
