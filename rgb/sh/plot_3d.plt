set terminal wxt
unset key
set view 65,35
set hidden3d
splot ARG1 using 1:2:3 with lines
pause -1