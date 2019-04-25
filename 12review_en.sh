#!/bin/bash

#
# Model adaptation:
#

# ./speech_sentences.py -l en -p voxforge_en
# cut -f 1 -d ' ' data/models/kaldi-generic-en-tdnn_f-latest/data/local/dict/lexicon.txt >vocab.txt
# lmplz -o 4 --prune 0 1 2 3 --limit_vocab_file vocab.txt --interpolate_unigrams 0 <data/dst/text-corpora/voxforge_en.txt >lm.arpa
# lmplz -o 6 --prune 0 0 0 0 1 --limit_vocab_file vocab.txt --interpolate_unigrams 0 <data/dst/text-corpora/voxforge_en.txt >lm.arpa

# ./speech_kaldi_adapt.py data/models/kaldi-generic-en-tdnn_f-latest dict-en.ipa lm.arpa voxforge_en
# pushd data/dst/asr-models/kaldi/voxforge_en
# bash run-adaptation.sh
# popd

# ./speech_dist.sh voxforge_en kaldi adapt


MODEL='kaldi-voxforge_en-adapt-r20190425'

./auto_review.py -m ${MODEL} -l en -s 12 -o 0  -R tmp/res00.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 1  -R tmp/res01.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 2  -R tmp/res02.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 3  -R tmp/res03.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 4  -R tmp/res04.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 5  -R tmp/res05.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 6  -R tmp/res06.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 7  -R tmp/res07.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 8  -R tmp/res08.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 9  -R tmp/res09.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 10 -R tmp/res10.csv voxforge_en &
./auto_review.py -m ${MODEL} -l en -s 12 -o 11 -R tmp/res11.csv voxforge_en &

wait

echo "to apply the review result, run:"
echo "./apply_review.py -l en voxforge_en tmp/*.csv"


