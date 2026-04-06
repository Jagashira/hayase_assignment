#!/bin/bash

if [ $# -lt 2 ]; then
  echo "使い方: $0 [2d|3d] datafile"
  exit 1
fi

MODE="$1"
FILE="$2"

if [ "$MODE" = "2d" ]; then
gnuplot -persist <<EOF
set terminal wxt
unset key
set size ratio -1
set view map
set yrange [*:*] reverse
plot "$FILE" using 1:2:3 with image
EOF

elif [ "$MODE" = "3d" ]; then
gnuplot -persist <<EOF
set terminal wxt
unset key
set view 65,35
set hidden3d
splot "$FILE" using 1:2:3 with lines
EOF

else
  echo "mode は 2d または 3d"
  exit 1
fi