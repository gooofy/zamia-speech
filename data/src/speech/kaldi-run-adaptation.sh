#!/bin/bash

# Copyright 2016, 2017, 2018 G. Bartsch
# Copyright 2015 Language Technology, Technische Universitaet Darmstadt (author: Benjamin Milde)
# Copyright 2014 QCRI (author: Ahmed Ali)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# adapted from kaldi-tuda-de run.sh
# adapted from wsj's run.sh

#
# adapt kaldi model to our current dict and srilm-generated LM
#

# now start preprocessing with KALDI scripts

if [ -f cmd.sh ]; then
      . cmd.sh; else
         echo "missing cmd.sh"; exit 1;
fi

#Path also sets LC_ALL=C for Kaldi, otherwise you will experience strange (and hard to debug!) bugs. It should be set here, after the python scripts and not at the beginning of this script
if [ -f path.sh ]; then
      . path.sh; else
         echo "missing path.sh"; exit 1;

fi

# echo "Runtime configuration is: nJobs $nJobs, nDecodeJobs $nDecodeJobs. If this is not what you want, edit cmd.sh"

#Make sure that LC_ALL is C for Kaldi, otherwise you will experience strange (and hard to debug!) bugs
export LC_ALL=C

# remove old lang dir if it exists
rm -rf data/lang
rm -rf data/local/lang

#Prepare phoneme data for Kaldi
utils/prepare_lang.sh data/local/dict "nspc" data/local/lang data/lang

lmdir=data/local/lm.adapt
lang=data/lang.adapt_test

rm -rf $lmdir
mkdir $lmdir
rm -rf $lang
cp -r data/lang $lang

echo
echo "creating G.fst..."

if [ -f lm.arpa ] ; then

    cat lm.arpa | utils/find_arpa_oovs.pl $lang/words.txt  > $lmdir/oovs_lm.txt

    cat lm.arpa | \
        grep -v '<s> <s>' | \
        grep -v '</s> <s>' | \
        grep -v '</s> </s>' | \
        arpa2fst - | fstprint | \
        utils/remove_oovs.pl $lmdir/oovs_lm.txt | \
        utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=$lang/words.txt \
          --osymbols=$lang/words.txt  --keep_isymbols=false --keep_osymbols=false | \
         fstrmepsilon > $lang/G.fst

fi

if [ -f G.src.fst ] ; then
    cat G.src.fst | fstcompile --isymbols=$lang/words.txt --osymbols=$lang/words.txt --keep_isymbols=false --keep_osymbols=false | fstrmepsilon > $lang/G.fst
    # fstdraw --isymbols="${MODEL}/words.txt" --osymbols="${MODEL}/words.txt" -portrait G.fst | dot -Tjpg >G.jpg
fi

if [ -f G.jsgf ] ; then
    sphinx_jsgf2fsg -jsgf G.jsgf -fsm G.fsm
    fstcompile --acceptor --isymbols=$lang/words.txt --osymbols=$lang/words.txt --keep_isymbols=false --keep_osymbols=false G.fsm | fstrmepsilon > $lang/G.fst
fi

#
# adapt our model
#

expdir=exp/adapt

utils/mkgraph.sh $lang $expdir $expdir/graph || exit 1;

