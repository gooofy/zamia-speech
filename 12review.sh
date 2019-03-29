#!/bin/bash

#
# Model adaptation:
#

# ./speech_sentences.py -l de gspv2
# cut -f 1 -d ' ' data/models/kaldi-generic-de-tdnn_f-latest/data/local/dict/lexicon.txt >vocab.txt
# lmplz -o 4 --prune 0 1 2 3 --limit_vocab_file vocab.txt --interpolate_unigrams 0 <data/dst/text-corpora/gspv2.txt >lm.arpa

# ./speech_kaldi_adapt.py data/models/kaldi-generic-de-tdnn_f-latest dict-de.ipa lm.arpa gspv2
# pushd data/dst/asr-models/kaldi/gspv2
# bash run-adaptation.sh
# popd

# MODEL='kaldi-generic-de-tdnn_f-latest'
MODEL='kaldi-gspv2-adapt-r20190329'

./auto_review.py -m ${MODEL} -s 12 -o 0  -R tmp/res00.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 1  -R tmp/res01.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 2  -R tmp/res02.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 3  -R tmp/res03.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 4  -R tmp/res04.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 5  -R tmp/res05.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 6  -R tmp/res06.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 7  -R tmp/res07.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 8  -R tmp/res08.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 9  -R tmp/res09.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 10 -R tmp/res10.csv gspv2 &
./auto_review.py -m ${MODEL} -s 12 -o 11 -R tmp/res11.csv gspv2 &

wait

echo "to apply the review result, run:"
echo "./apply_review.py -l de gspv2 tmp/*.csv"
