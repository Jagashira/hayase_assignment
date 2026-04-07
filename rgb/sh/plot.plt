set terminal wxt
unset key
set size ratio -1
set view map
set yrange [*:*] reverse
plot ARG1 using 1:2:3 with image
pause -1
