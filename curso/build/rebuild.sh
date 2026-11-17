#!/bin/bash
cd "$(dirname "$0")"
declare -A E=([1]=8,16 [2]=10,19 [3]=9,17 [4]=9,18 [5]=8,16 [6]=8,16)
for n in 1 2 3 4 5 6; do node render_slides.js $n && python3 make_video.py $n ${E[$n]}; done
echo TUDO-PRONTO
