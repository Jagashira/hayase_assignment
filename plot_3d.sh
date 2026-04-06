#!/bin/bash

if [ $# -lt 1 ]; then
  echo "使い方: $0 gray.dat"
  exit 1
fi

gnuplot -e "ARG1='$1'" plot_3d.plt