#!/bin/bash

#
# train LM using srilm
#

lmdir=data/local/lm
lang=data/lang_test

if [ -f path.sh ]; then
      . path.sh; else
         echo "missing path.sh"; exit 1;
fi

export LC_ALL=C
. ./path.sh || exit 1; # for KALDI_ROOT
export PATH=$KALDI_ROOT/tools/srilm/bin:$KALDI_ROOT/tools/srilm/bin/i686-m64:$PATH
export LD_LIBRARY_PATH="$KALDI_ROOT/tools/liblbfgs-1.10/lib/.libs:$LD_LIBRARY_PATH"

rm -rf data/lang_test
cp -r data/lang data/lang_test

echo
echo "create train_all.txt"

cat $lmdir/train_nounk.txt ../sentences.txt > $lmdir/train_all.txt

echo
echo "ngram-count..."

ngram-count -text $lmdir/train_all.txt -order 3 \
                -wbdiscount -interpolate -lm $lmdir/lm.arpa

echo
echo "creating G.fst..."

cat $lmdir/lm.arpa | utils/find_arpa_oovs.pl $lang/words.txt  > $lmdir/oovs_lm.txt

echo 2

cat $lmdir/lm.arpa  | \
    grep -v '<s> <s>' | \
    grep -v '</s> <s>' | \
    grep -v '</s> </s>' | \
    arpa2fst - | fstprint | \
    utils/remove_oovs.pl $lmdir/oovs_lm.txt | \
    utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=$lang/words.txt \
      --osymbols=$lang/words.txt  --keep_isymbols=false --keep_osymbols=false | \
     fstrmepsilon > $lang/G.fst

