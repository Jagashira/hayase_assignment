set terminal pngcairo size 900,900 enhanced font "Helvetica,14"
set output OUTPUT

if (!exists("MODE")) MODE = 4

unset key
unset colorbox
title_text = (MODE == 1 ? "Condition 1: r > g > b" : \
             MODE == 2 ? "Condition 2: r > g > b + range filters" : \
             MODE == 3 ? "Condition 3: 5 brown points + 5 gray points" : \
                         "Condition 4: 15 brown points + 5 gray points")
# set title title_text

set size ratio -1
set view map
set xrange [*:*]
set yrange [*:*] reverse
set border linecolor rgb "#444444"

rgb(r,g,b) = int(r)*65536 + int(g)*256 + int(b)
clamp(v) = (v < 0 ? 0 : (v > 255 ? 255 : v))
dist2(r,g,b,rr,gg,bb) = (r-rr)**2 + (g-gg)**2 + (b-bb)**2
min2(a,b) = (a < b ? a : b)
min5(a,b,c,d,e) = min2(min2(a,b), min2(min2(c,d), e))
min10(a,b,c,d,e,f,g,h,i,j) = min2(min5(a,b,c,d,e), min5(f,g,h,i,j))
brown_d2_a(r,g,b) = min10( \
    dist2(r,g,b,106,86,51), \
    dist2(r,g,b,108,86,47), \
    dist2(r,g,b,110,88,47), \
    dist2(r,g,b,113,93,58), \
    dist2(r,g,b,119,99,64), \
    dist2(r,g,b,125,102,61), \
    dist2(r,g,b,138,115,73), \
    dist2(r,g,b,140,118,79), \
    dist2(r,g,b,144,123,80), \
    dist2(r,g,b,145,123,82))
brown_d2_b(r,g,b) = min5( \
    dist2(r,g,b,150,131,89), \
    dist2(r,g,b,153,135,99), \
    dist2(r,g,b,158,134,88), \
    dist2(r,g,b,179,152,107), \
    dist2(r,g,b,185,158,115))
brown_d2(r,g,b) = min2(brown_d2_a(r,g,b), brown_d2_b(r,g,b))
gray_d2(r,g,b) = min5( \
    dist2(r,g,b,179,178,176), \
    dist2(r,g,b,133,132,128), \
    dist2(r,g,b,140,135,129), \
    dist2(r,g,b,176,175,170), \
    dist2(r,g,b,177,173,170))
is_brown1(r,g,b) = (r > g && g > b)
is_brown2(r,g,b) = ( \
    r > 110 && g > 70 && b > 30 && \
    r > g && g > b && \
    (r-g) < 90 && (g-b) < 90 && \
    (r+g+b) < 560 )
is_brown3(r,g,b) = ( \
    r >= 118 && r <= 170 && \
    g >= 95  && g <= 145 && \
    b >= 55  && b <= 100 && \
    (r-g) >= 16 && (r-g) <= 32 && \
    (g-b) >= 28 && (g-b) <= 55 && \
    (r+g+b) >= 285 && (r+g+b) <= 410 && \
    brown_d2(r,g,b) <= 1400 && \
    gray_d2(r,g,b) > brown_d2(r,g,b) )
is_brown4(r,g,b) = ( \
    r >= 100 && r <= 195 && \
    g >= 80  && g <= 165 && \
    b >= 45  && b <= 120 && \
    (r-g) >= 14 && (r-g) <= 34 && \
    (g-b) >= 18 && (g-b) <= 52 && \
    (r+g+b) >= 240 && (r+g+b) <= 470 && \
    brown_d2(r,g,b) <= 900 && \
    gray_d2(r,g,b) > brown_d2(r,g,b) * 1.35 )
selected(r,g,b) = (MODE == 1 ? is_brown1(r,g,b) : \
                   MODE == 2 ? is_brown2(r,g,b) : \
                   MODE == 3 ? is_brown3(r,g,b) : \
                               is_brown4(r,g,b))
cyan = rgb(255, 0, 0)
plot INPUT using 2:1:(selected($3,$4,$5) ? cyan : rgb($3,$4,$5)) with rgbimage

unset output
