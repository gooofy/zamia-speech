#!/bin/bash

./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 0  -R tmp/res00.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 1  -R tmp/res01.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 2  -R tmp/res02.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 3  -R tmp/res03.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 4  -R tmp/res04.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 5  -R tmp/res05.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 6  -R tmp/res06.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 7  -R tmp/res07.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 8  -R tmp/res08.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 9  -R tmp/res09.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 10 -R tmp/res10.csv gspv2 &
./auto_review.py -m kaldi-generic-de-tdnn_f-latest -s 12 -o 11 -R tmp/res11.csv gspv2 &

wait

