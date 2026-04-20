set terminal pngcairo size 1800,1200 enhanced font "Helvetica,14" background rgb "#f2f2f2"
set output OUTPUT

unset key
unset colorbox
set multiplot layout 2,3 rowsfirst title "Luminance comparison and helper maps"
set view map
set xrange [*:*]
set yrange [*:*] reverse
set offsets 0,0,0,0
set border linecolor rgb "#666666"
unset xtics
unset ytics
unset lmargin
unset rmargin
unset tmargin
unset bmargin

gray(v) = int(v) * 65536 + int(v) * 256 + int(v)
diverging(v) = (v < 128 ? int(2*v) * 256 + 255 : 255 * 65536 + int(2*(255-v)) * 256)

set title "Fair compare: R+G+B"
plot SUM_FILE using 1:2:(gray($3)) with rgbimage

set title "Fair compare: 0.299R+0.587G+0.114B"
plot WEIGHTED_FILE using 1:2:(gray($3)) with rgbimage

set title "Signed diff: Lsum - Lweighted"
plot DIFF_FILE using 1:2:(diverging($3)) with rgbimage

set title "Weighted only: min-max"
plot WEIGHTED_MINMAX_FILE using 1:2:(gray($3)) with rgbimage

set title "Weighted only: 1%-99%"
plot WEIGHTED_PERCENTILE_FILE using 1:2:(gray($3)) with rgbimage

set title "Weighted only: percentile + gamma 2.2"
plot WEIGHTED_GAMMA_FILE using 1:2:(gray($3)) with rgbimage

unset multiplot
unset output
