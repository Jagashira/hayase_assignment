# COMSOL export plotting

`plot_comsol.py` reads COMSOL text exports whose metadata/header lines start with `%`,
writes cleaned plot data, generates a gnuplot script, and creates a PNG.

Basic single-file plot:

```sh
python3 gnuplot/plot_comsol.py gnuplot/data/work3-10.00.dat \
  --x y --y p \
  --output gnuplot/output/comsol/work3_10_p.png \
  --key off
```

Compare multiple files:

```sh
python3 gnuplot/plot_comsol.py \
  gnuplot/data/work3-9.98r.txt \
  gnuplot/data/work3-9.99r.txt \
  gnuplot/data/work3-10.00r.txt \
  gnuplot/data/work3-10.01r.txt \
  gnuplot/data/work3-10.02r.txt \
  --x y --y p \
  --labels "z = 9.98 mm" "z = 9.99 mm" "z = 10.00 mm" "z = 10.01 mm" "z = 10.02 mm" \
  --xlabel "y (mm)" \
  --ylabel "p (Pa)" \
  --vline -0.2 --vline 0.2 \
  --key "bottom left" \
  --output gnuplot/output/comsol/work3_r_compare.png
```

Convert COMSOL SI units to mm/mm/s and center the horizontal axis:

```sh
python3 gnuplot/plot_comsol.py \
  gnuplot/data/work4-rectangle-middleA.dat \
  gnuplot/data/work4-rectangle-middleB.dat \
  --x 1 --y 4 \
  --x-scale 1000 --y-scale 1000 --center-x \
  --labels middleA middleB \
  --xlabel "Centered position (mm)" \
  --ylabel "Velocity magnitude (mm/s)" \
  --key "bottom right" \
  --output gnuplot/output/comsol/work4_compare.png
```

Useful options:

- `--x`, `--y`: column name or 1-based column number.
- `--x-scale`, `--y-scale`: unit conversion multipliers.
- `--x-offset`, `--y-offset`: subtract fixed offsets after scaling.
- `--center-x`, `--center-y`: center each series around its data midpoint.
- `--xrange`, `--yrange`: pass ranges such as `-0.2:0.2` or `0:30`.
- `--dry-run`: only write the `.dat` and `.gp` files.
